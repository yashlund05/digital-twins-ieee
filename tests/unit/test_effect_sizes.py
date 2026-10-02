"""
tests/unit/test_effect_sizes.py — Unit tests for Cohen's d and Cliff's delta effect sizes.
"""

import numpy as np
import pytest

from src.statistics.effect_sizes import compute_cliffs_delta, compute_cohens_d


def test_cohens_d_known_values():
    """Verify independent and paired Cohen's d calculations."""
    x = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    y = np.array([8.0, 9.0, 10.0, 11.0, 12.0])

    # Paired: difference is constant 2.0 -> std of diff is 0 -> d = 0 or large depending on eps
    # Test slightly varying paired diff
    x_var = np.array([10.0, 12.0, 11.0, 15.0, 13.0])
    y_var = np.array([8.0, 9.0, 10.0, 11.0, 12.0])
    res_paired = compute_cohens_d(x_var, y_var, paired=True)
    assert res_paired["d"] > 0
    assert res_paired["paired"] is True

    # Independent
    res_ind = compute_cohens_d(x, y, paired=False)
    assert res_ind["d"] > 0
    assert res_ind["paired"] is False


def test_identical_distributions_zero_effect():
    """Identical distributions must have effect size of zero."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    res_d = compute_cohens_d(x, x, paired=True)
    assert res_d["d"] == 0.0
    assert res_d["interpretation"] == "negligible"

    res_delta = compute_cliffs_delta(x, x)
    assert res_delta["delta"] == 0.0
    assert res_delta["interpretation"] == "negligible"


def test_cliffs_delta_complete_separation():
    """Completely separated distributions should yield delta = 1.0."""
    x = np.array([10.0, 11.0, 12.0])
    y = np.array([1.0, 2.0, 3.0])

    res = compute_cliffs_delta(x, y)
    assert np.isclose(res["delta"], 1.0)
    assert res["interpretation"] == "large"

    # Reversed should yield -1.0
    res_rev = compute_cliffs_delta(y, x)
    assert np.isclose(res_rev["delta"], -1.0)
    assert res_rev["interpretation"] == "large"


def test_invalid_effect_size_inputs():
    """Empty arrays or mismatched paired inputs must raise ValueError."""
    with pytest.raises(ValueError):
        compute_cohens_d([1.0], [2.0])
    with pytest.raises(ValueError):
        compute_cohens_d([1.0, 2.0], [1.0], paired=True)
    with pytest.raises(ValueError):
        compute_cliffs_delta([], [1.0])
