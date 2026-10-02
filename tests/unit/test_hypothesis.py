"""
tests/unit/test_hypothesis.py — Unit tests for H3 testing, Wilcoxon, and FDR correction.
"""

import numpy as np
import pytest

from src.statistics.hypothesis import (
    benjamini_hochberg_correction,
    paired_wilcoxon_test,
    test_differential_degradation_h3,
)


def test_h3_steeper_degradation_supported():
    """Synthetic case where AD degrades much steeper than LE should support H3."""
    dt = np.array([0, 1, 5, 15, 60, 300])
    # Anomaly degradation steep slope: y = 2.0 * log1p(dt)
    ad_deg = 2.0 * np.log1p(dt)
    # Load degradation gentle slope: y = 0.5 * log1p(dt)
    le_deg = 0.5 * np.log1p(dt)

    res = test_differential_degradation_h3(
        predictor=dt,
        ad_normalized_degradation=ad_deg,
        le_normalized_degradation=le_deg,
        n_boot=300,
        seed=42,
    )

    assert res["conclusion"] == "SUPPORTED"
    assert res["delta_beta"] > 0
    assert res["ci_low"] > 0
    assert res["p_value_one_sided"] < 0.05


def test_h3_equal_slopes_not_supported():
    """Identical slopes must conclude NOT_SUPPORTED."""
    dt = np.array([0, 1, 5, 15, 60, 300])
    deg = 1.0 * np.log1p(dt)

    res = test_differential_degradation_h3(
        predictor=dt,
        ad_normalized_degradation=deg,
        le_normalized_degradation=deg,
        n_boot=300,
        seed=42,
    )
    assert res["conclusion"] == "NOT_SUPPORTED"
    assert np.isclose(res["delta_beta"], 0.0)


def test_paired_wilcoxon_test():
    """Wilcoxon test on strictly positive paired differences should reject null."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])

    res = paired_wilcoxon_test(x, y, alternative="greater")
    assert res["statistic"] > 0
    assert res["p_value"] < 0.05


def test_benjamini_hochberg_correction():
    """Verify Benjamini-Hochberg FDR adjustment on known p-values."""
    raw_p = [0.01, 0.04, 0.06, 0.20]
    # m = 4
    # rank 1: 0.01 * 4 / 1 = 0.04
    # rank 2: 0.04 * 4 / 2 = 0.08
    # rank 3: 0.06 * 4 / 3 = 0.08
    # rank 4: 0.20 * 4 / 4 = 0.20
    res = benjamini_hochberg_correction(raw_p, alpha=0.05)

    assert len(res["p_adjusted"]) == 4
    assert np.isclose(res["p_adjusted"][0], 0.04)
    assert np.isclose(res["p_adjusted"][1], 0.08)
    assert res["significant"][0] is True
    assert res["significant"][1] is False
