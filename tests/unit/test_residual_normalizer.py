"""
tests/unit/test_residual_normalizer.py — Unit tests and leakage audit for ResidualNormalizer.
"""

import numpy as np
import pandas as pd
import pytest

from src.residuals.normalizer import ResidualNormalizer


def test_unfitted_transform_raises_error():
    """Calling transform before fit must raise RuntimeError."""
    norm = ResidualNormalizer(method="z_score")
    with pytest.raises(RuntimeError, match="must be fitted"):
        norm.transform(np.array([[1.0, 2.0]]))


def test_z_score_normalization():
    """z-score normalization achieves zero mean and unit variance."""
    X_train = np.array([[10.0, 100.0], [20.0, 200.0], [30.0, 300.0]], dtype=np.float64)
    norm = ResidualNormalizer(method="z_score")
    X_norm = norm.fit_transform(X_train)

    np.testing.assert_allclose(np.mean(X_norm, axis=0), 0.0, atol=1e-10)
    np.testing.assert_allclose(np.std(X_norm, axis=0), 1.0, atol=1e-10)

    # Inverse transform
    X_rev = norm.inverse_transform(X_norm)
    np.testing.assert_allclose(X_rev, X_train, atol=1e-10)


def test_min_max_normalization():
    """min_max scaling scales training data strictly to [0, 1]."""
    X_train = np.array([[10.0, -50.0], [30.0, 50.0]], dtype=np.float64)
    norm = ResidualNormalizer(method="min_max")
    X_norm = norm.fit_transform(X_train)

    np.testing.assert_allclose(X_norm[0], [0.0, 0.0])
    np.testing.assert_allclose(X_norm[1], [1.0, 1.0])


def test_robust_normalization():
    """robust scaling uses median and IQR."""
    X_train = np.array([[10.0], [20.0], [30.0], [40.0], [50.0]], dtype=np.float64)
    norm = ResidualNormalizer(method="robust")
    X_norm = norm.fit_transform(X_train)

    # Median is 30.0, should map to 0.0
    assert X_norm[2, 0] == 0.0


def test_dataframe_support():
    """ResidualNormalizer preserves DataFrame indices and column headers."""
    df = pd.DataFrame(
        {"bus_2": [10.0, 20.0, 30.0], "bus_3": [100.0, 200.0, 300.0]},
        index=pd.date_range("2018-01-01", periods=3, freq="15min"),
    )
    norm = ResidualNormalizer(method="z_score")
    norm_df = norm.fit_transform(df)

    assert isinstance(norm_df, pd.DataFrame)
    assert list(norm_df.columns) == ["bus_2", "bus_3"]
    assert norm_df.index.equals(df.index)


def test_serialization_roundtrip(tmp_path):
    """Fitted normalizer must serialize to JSON and restore numerically identical state."""
    X_train = np.array([[1.0, 10.0], [5.0, 50.0], [9.0, 90.0]])
    norm = ResidualNormalizer(method="z_score")
    norm.fit(X_train, feature_names=["feat_a", "feat_b"])

    file_path = tmp_path / "normalizer.json"
    norm.save(file_path)

    loaded_norm = ResidualNormalizer.load(file_path)
    assert loaded_norm.is_fitted is True
    assert loaded_norm.method == "z_score"
    assert loaded_norm.feature_names_ == ["feat_a", "feat_b"]
    np.testing.assert_allclose(loaded_norm.center_, norm.center_)
    np.testing.assert_allclose(loaded_norm.scale_, norm.scale_)

    X_test = np.array([[2.0, 20.0]])
    np.testing.assert_allclose(loaded_norm.transform(X_test), norm.transform(X_test))


def test_normalization_leakage_audit():
    """CRITICAL AUDIT: Test partition samples MUST NOT alter fitted training statistics."""
    # 1. Training set
    X_train = np.array([[10.0], [20.0], [30.0]], dtype=np.float64)

    # Fit strictly on train
    norm = ResidualNormalizer(method="z_score")
    norm.fit(X_train)

    train_mean_before = float(norm.center_[0])
    train_std_before = float(norm.scale_[0])

    # 2. Test set with extreme outlier (e.g. 1,000,000)
    X_test = np.array([[1000000.0]], dtype=np.float64)

    # Transform test set
    _ = norm.transform(X_test)

    # 3. Assert fitted parameters are COMPLETELY UNCHANGED
    assert norm.center_[0] == train_mean_before
    assert norm.scale_[0] == train_std_before
    assert norm.n_samples_seen_ == 3

    # If test had leaked into fit, mean would be 250,015 instead of 20
    assert norm.center_[0] == 20.0
