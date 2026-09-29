"""
tests/unit/test_preprocessor.py — Unit tests for data preprocessing and feature extraction.
"""

import numpy as np
import pandas as pd
import pytest

from src.data.preprocessor import (
    clean_and_resample,
    extract_lag_features,
    extract_temporal_features,
    fit_and_apply_normalization,
)


@pytest.fixture
def sample_timeseries():
    """Create a 100-step test time series with known timestamps and missing values."""
    timestamps = pd.date_range("2018-01-01 00:00:00", periods=100, freq="15min", tz="UTC")
    data = {
        "bus_2_p_kw": np.linspace(10, 50, 100),
        "bus_3_p_kw": np.sin(np.linspace(0, 10, 100)) * 20 + 30,
    }
    df = pd.DataFrame(data, index=timestamps)
    # Introduce small missing gap (2 steps)
    df.iloc[10:12, 0] = np.nan
    return df


def test_clean_and_resample(sample_timeseries):
    """Test regular grid verification and missing value imputation."""
    cleaned = clean_and_resample(sample_timeseries, resolution_minutes=15, max_gap_minutes=60)
    assert len(cleaned) == 100
    assert cleaned.isna().sum().sum() == 0
    # Imputed values should be within the linear range
    assert 10.0 <= cleaned.iloc[10, 0] <= 20.0


def test_extract_temporal_features(sample_timeseries):
    """Test calendar and cyclic temporal feature extraction."""
    features = extract_temporal_features(sample_timeseries.index)
    expected_cols = [
        "hour",
        "day_of_week",
        "month",
        "is_weekend",
        "sin_hour",
        "cos_hour",
        "sin_day",
        "cos_day",
    ]
    for col in expected_cols:
        assert col in features.columns

    # 2018-01-01 was a Monday (day_of_week = 0, is_weekend = 0)
    assert features["day_of_week"].iloc[0] == 0
    assert features["is_weekend"].iloc[0] == 0

    # Sine and cosine bounds
    assert np.all(features["sin_hour"] >= -1.0) and np.all(features["sin_hour"] <= 1.0)
    assert np.all(features["cos_hour"] >= -1.0) and np.all(features["cos_hour"] <= 1.0)


def test_extract_lag_features(sample_timeseries):
    """Test historical lag column extraction."""
    cleaned = sample_timeseries.bfill()
    lags = [1, 5]
    lagged = extract_lag_features(cleaned, lags=lags)

    assert "bus_2_p_kw_lag_1" in lagged.columns
    assert "bus_2_p_kw_lag_5" in lagged.columns
    # Check that lag 1 matches value from step t-1
    assert lagged["bus_2_p_kw_lag_1"].iloc[10] == cleaned["bus_2_p_kw"].iloc[9]
    assert lagged["bus_2_p_kw_lag_5"].iloc[10] == cleaned["bus_2_p_kw"].iloc[5]


def test_fit_and_apply_normalization_zero_leakage():
    """Verify normalization statistics are computed strictly on the training partition."""
    timestamps = pd.date_range("2018-01-01", periods=100, freq="15min", tz="UTC")
    # Training values: 0 to 50; Test values: 100 to 200
    vals = np.concatenate([np.linspace(0, 50, 70), np.linspace(100, 200, 30)])
    df = pd.DataFrame({"feat": vals}, index=timestamps)

    train_indices = list(range(0, 70))
    norm_df, norm_params = fit_and_apply_normalization(
        df,
        feature_columns=["feat"],
        train_indices=train_indices,
        method="min_max",
    )

    # Train min should be 0.0 and max should be 50.0 (ignoring test values 100-200)
    assert norm_params.bus_params["feat"]["min"] == pytest.approx(0.0)
    assert norm_params.bus_params["feat"]["max"] == pytest.approx(50.0)

    # In training partition, min is 0 and max is 1
    assert norm_df["feat"].iloc[0] == pytest.approx(0.0)
    assert norm_df["feat"].iloc[69] == pytest.approx(1.0)

    # In test partition, values exceed 1.0 because they are strictly normalized by train stats
    assert norm_df["feat"].iloc[70] > 1.0
