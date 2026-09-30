"""
tests/unit/test_residual_features.py — Unit tests and causality audit for ResidualFeatureExtractor.
"""

import numpy as np
import pandas as pd
import pytest

from src.residuals.features import ResidualFeatureConfig, ResidualFeatureExtractor


def test_direct_raw_features():
    """Default configuration extracts direct raw residuals."""
    res = np.array([[1.0, -2.0], [3.0, -4.0]])
    extractor = ResidualFeatureExtractor()
    out = extractor.extract(res)

    np.testing.assert_allclose(out, res)


def test_nonlinear_and_spatial_features():
    """Test absolute, squared, L2 norm, mean absolute, and max absolute features."""
    res = np.array([[3.0, -4.0]])  # L2 norm is 5.0, mean is 3.5, max is 4.0
    cfg = ResidualFeatureConfig(
        include_raw=True,
        include_absolute=True,
        include_squared=True,
        include_l2_norm=True,
        include_mean_absolute=True,
        include_max_absolute=True,
    )
    extractor = ResidualFeatureExtractor(config=cfg)
    out = extractor.extract(res, feature_names=["f1", "f2"])

    # Columns: f1, f2, abs_f1, abs_f2, sq_f1, sq_f2, res_l2_norm, res_mean_abs, res_max_abs
    assert out.shape == (1, 9)
    np.testing.assert_allclose(out[0, 0:2], [3.0, -4.0])  # raw
    np.testing.assert_allclose(out[0, 2:4], [3.0, 4.0])  # abs
    np.testing.assert_allclose(out[0, 4:6], [9.0, 16.0])  # sq
    assert out[0, 6] == 5.0  # L2 norm
    assert out[0, 7] == 3.5  # Mean abs
    assert out[0, 8] == 4.0  # Max abs


def test_causal_lag_features():
    """Test lag feature shifts values backward causally."""
    res = np.array([[10.0], [20.0], [30.0], [40.0]])
    cfg = ResidualFeatureConfig(include_raw=True, lags=[1, 2])
    extractor = ResidualFeatureExtractor(config=cfg)
    out = extractor.extract(res)

    # Columns: raw, lag_1, lag_2
    assert out.shape == (4, 3)
    # Row 0: [10, 0, 0]
    np.testing.assert_allclose(out[0], [10.0, 0.0, 0.0])
    # Row 1: [20, 10, 0]
    np.testing.assert_allclose(out[1], [20.0, 10.0, 0.0])
    # Row 2: [30, 20, 10]
    np.testing.assert_allclose(out[2], [30.0, 20.0, 10.0])
    # Row 3: [40, 30, 20]
    np.testing.assert_allclose(out[3], [40.0, 30.0, 20.0])


def test_non_positive_lag_raises_error():
    """Lags <= 0 are non-causal and must be rejected."""
    with pytest.raises(ValueError, match="strictly positive"):
        ResidualFeatureExtractor(config={"lags": [0]})

    with pytest.raises(ValueError, match="strictly positive"):
        ResidualFeatureExtractor(config={"lags": [-1]})


def test_causality_and_future_leakage_audit():
    """CRITICAL AUDIT: Modifying future row r[t+1] MUST NOT alter features at row t."""
    # Sequence of 5 timesteps
    res_original = np.array(
        [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]], dtype=np.float64
    )

    cfg = ResidualFeatureConfig(
        include_raw=True,
        include_absolute=True,
        include_squared=True,
        include_l2_norm=True,
        include_mean_absolute=True,
        include_max_absolute=True,
        lags=[1, 2],
    )
    extractor = ResidualFeatureExtractor(config=cfg)
    feats_original = extractor.extract(res_original)

    # Inspect timestep t = 2
    t2_features_before = feats_original[2].copy()

    # Modify future timesteps t = 3 and t = 4 with extreme perturbations
    res_perturbed = res_original.copy()
    res_perturbed[3, :] = 999999.0
    res_perturbed[4, :] = -888888.0

    feats_perturbed = extractor.extract(res_perturbed)
    t2_features_after = feats_perturbed[2].copy()

    # Features at t=2 MUST be strictly identical
    np.testing.assert_allclose(t2_features_before, t2_features_after)


def test_dataframe_feature_names_and_indices():
    """DataFrame input preserves timestamp index and formats structured column names."""
    idx = pd.date_range("2018-01-01", periods=2, freq="15min")
    df = pd.DataFrame({"bus_2": [1.0, 2.0]}, index=idx)

    cfg = ResidualFeatureConfig(include_raw=True, include_absolute=True, lags=[1])
    extractor = ResidualFeatureExtractor(config=cfg)
    out_df = extractor.extract(df)

    assert isinstance(out_df, pd.DataFrame)
    assert out_df.index.equals(idx)
    assert list(out_df.columns) == ["bus_2", "abs_bus_2", "bus_2_lag_1"]
