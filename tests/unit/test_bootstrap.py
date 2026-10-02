"""
tests/unit/test_bootstrap.py — Unit tests for deterministic bootstrap resampling.
"""

import numpy as np

from src.statistics.bootstrap import (
    bootstrap_ci,
    bootstrap_difference_ci,
    bootstrap_slope_ci,
)


def test_bootstrap_seed_determinism():
    """Identical seeds must yield bitwise identical bootstrap confidence intervals."""
    data = np.array([1.2, 2.3, 1.8, 3.1, 2.5, 4.0, 2.9])
    res1 = bootstrap_ci(data, n_boot=200, seed=42)
    res2 = bootstrap_ci(data, n_boot=200, seed=42)

    assert res1["estimate"] == res2["estimate"]
    assert res1["ci_low"] == res2["ci_low"]
    assert res1["ci_high"] == res2["ci_high"]


def test_bootstrap_ci_coverage():
    """Bootstrap 95% CI on known mean should bracket true population parameter."""
    rng = np.random.default_rng(123)
    data = rng.normal(loc=10.0, scale=2.0, size=50)

    res = bootstrap_ci(data, stat_func=np.mean, n_boot=300, ci=0.95, seed=42)
    assert res["ci_low"] < 10.0 < res["ci_high"]


def test_bootstrap_difference_ci():
    """Paired difference bootstrap should correctly capture non-zero difference."""
    x = np.array([10.0, 12.0, 14.0, 16.0, 18.0])
    y = np.array([5.0, 6.0, 7.0, 8.0, 9.0])

    res = bootstrap_difference_ci(x, y, n_boot=200, paired=True, seed=42)
    assert res["diff_estimate"] > 0
    assert res["ci_low"] > 0
    assert res["p_value_two_sided"] < 0.05


def test_bootstrap_slope_ci():
    """Slope bootstrap should bracket true regression coefficient."""
    x = np.linspace(0, 10, 20)
    y = 3.0 * x + 1.0

    res = bootstrap_slope_ci(x, y, n_boot=200, ci=0.95, seed=42)
    assert np.isclose(res["slope"], 3.0)
    assert res["ci_low"] <= 3.0 <= res["ci_high"]
