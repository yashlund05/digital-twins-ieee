"""
tests/unit/test_regression.py — Unit tests for linear and factorial regression models.
"""

import numpy as np
import pytest

from src.statistics.regression import (
    fit_linear_regression,
    fit_log_linear_regression,
    fit_two_way_factorial_regression,
)


def test_linear_regression_known_slope():
    """Verify exact recovery of slope and intercept on synthetic linear data."""
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    y = 2.5 * x + 4.0

    res = fit_linear_regression(x, y)
    assert np.isclose(res["slope"], 2.5)
    assert np.isclose(res["intercept"], 4.0)
    assert np.isclose(res["r_squared"], 1.0)
    assert res["p_value"] < 1e-4


def test_log_linear_regression():
    """Verify log1p-transformed regression fits correctly."""
    x = np.array([0.0, 1.0, 5.0, 15.0, 60.0, 300.0])
    y = 1.5 * np.log1p(x) + 0.5

    res = fit_log_linear_regression(x, y)
    assert np.isclose(res["slope"], 1.5)
    assert np.isclose(res["intercept"], 0.5)
    assert np.isclose(res["r_squared"], 1.0)
    assert res["transform"] == "log1p"


def test_regression_zero_variance():
    """Predictor with zero variance should return 0 slope without error."""
    x = np.array([5.0, 5.0, 5.0, 5.0])
    y = np.array([1.0, 2.0, 3.0, 4.0])

    res = fit_linear_regression(x, y)
    assert res["slope"] == 0.0
    assert np.isclose(res["intercept"], 2.5)
    assert res["r_squared"] == 0.0


def test_two_way_factorial_regression():
    """Verify two-way factorial model recovers main effects and interaction."""
    dt = np.array([0.0, 0.0, 10.0, 10.0, 20.0, 20.0])
    p_drop = np.array([0.0, 0.1, 0.0, 0.1, 0.0, 0.1])
    # y = 2.0 + 3.0 * dt + 4.0 * p_drop + 5.0 * (dt * p_drop)
    y = 2.0 + 3.0 * dt + 4.0 * p_drop + 5.0 * (dt * p_drop)

    res = fit_two_way_factorial_regression(dt, p_drop, y, use_log_dt=False)
    assert np.isclose(res["intercept"], 2.0)
    assert np.isclose(res["b_dt"], 3.0)
    assert np.isclose(res["b_pdrop"], 4.0)
    assert np.isclose(res["b_interaction"], 5.0)
    assert np.isclose(res["r_squared"], 1.0)


def test_invalid_regression_inputs():
    """Dimension mismatches or empty arrays must raise ValueError."""
    with pytest.raises(ValueError):
        fit_linear_regression([1.0], [1.0])
    with pytest.raises(ValueError):
        fit_linear_regression([1.0, 2.0], [1.0])
    with pytest.raises(ValueError):
        fit_log_linear_regression([-1.0, 2.0], [1.0, 2.0])
