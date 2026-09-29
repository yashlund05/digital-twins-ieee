"""
tests/unit/test_forecasting_metrics.py — Unit tests for load forecasting metrics.
"""

import numpy as np
import pytest

from src.evaluation.forecasting_metrics import (
    compute_forecasting_metrics,
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)


@pytest.fixture
def sample_regression_data():
    """Create simple synthetic targets and predictions for exact arithmetic checking."""
    y_true = np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float64)
    y_pred = np.array([12.0, 18.0, 33.0, 36.0], dtype=np.float64)
    # Errors: [+2, -2, +3, -4]
    # Abs errors: [2, 2, 3, 4] -> sum = 11 -> MAE = 11/4 = 2.75
    # Sq errors: [4, 4, 9, 16] -> sum = 33 -> MSE = 33/4 = 8.25 -> RMSE = sqrt(8.25) ≈ 2.87228
    # Pct errors: [2/10, 2/20, 3/30, 4/40] = [0.2, 0.1, 0.1, 0.1] -> sum = 0.5 -> MAPE = 0.5/4 * 100 = 12.5%
    return y_true, y_pred


def test_mean_absolute_error(sample_regression_data):
    """Verify MAE calculation."""
    y_true, y_pred = sample_regression_data
    mae = mean_absolute_error(y_true, y_pred)
    assert pytest.approx(mae, abs=1e-6) == 2.75


def test_root_mean_squared_error(sample_regression_data):
    """Verify RMSE calculation."""
    y_true, y_pred = sample_regression_data
    rmse = root_mean_squared_error(y_true, y_pred)
    assert pytest.approx(rmse, abs=1e-5) == np.sqrt(8.25)


def test_mean_absolute_percentage_error(sample_regression_data):
    """Verify MAPE calculation."""
    y_true, y_pred = sample_regression_data
    mape = mean_absolute_percentage_error(y_true, y_pred)
    assert pytest.approx(mape, abs=1e-4) == 12.5


def test_r2_score_perfect():
    """Verify R2 score is 1.0 for perfect predictions."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert pytest.approx(r2_score(y_true, y_true), abs=1e-6) == 1.0


def test_compute_forecasting_metrics_suite(sample_regression_data):
    """Verify combined dictionary metrics output."""
    y_true, y_pred = sample_regression_data
    res = compute_forecasting_metrics(y_true, y_pred)
    assert "mae" in res
    assert "rmse" in res
    assert "mape" in res
    assert "r2" in res
    assert res["mae"] == 2.75
    assert pytest.approx(res["mape"], abs=1e-4) == 12.5
