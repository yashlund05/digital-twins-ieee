"""tests/unit/test_aoi_adaptive_threshold.py — Unit tests for AoIAdaptiveThreshold."""

import numpy as np
import pytest

from src.anomaly_detection.thresholds import (
    AoIAdaptiveThreshold,
    get_threshold_selector,
)


def test_aoi_adaptive_threshold_initialization():
    """Verify initialization and validation of parameters."""
    selector = AoIAdaptiveThreshold(base_percentile=95.0, gamma=0.1, scaling_function="sqrt")
    assert selector.base_percentile == 95.0
    assert selector.gamma == 0.1
    assert selector.scaling_function == "sqrt"

    with pytest.raises(ValueError, match="base_percentile"):
        AoIAdaptiveThreshold(base_percentile=105.0)

    with pytest.raises(ValueError, match="gamma"):
        AoIAdaptiveThreshold(gamma=-0.5)

    with pytest.raises(ValueError, match="Unsupported scaling_function"):
        AoIAdaptiveThreshold(scaling_function="exponential")


def test_aoi_adaptive_threshold_fit_and_dynamic_computation():
    """Verify fit logic and dynamic threshold calculations across scaling functions."""
    np.random.seed(42)
    scores = np.random.normal(loc=0.0, scale=1.0, size=500)
    aoi = np.random.uniform(0.0, 100.0, size=500)

    # Test sqrt scaling
    selector_sqrt = AoIAdaptiveThreshold(base_percentile=95.0, gamma=0.2, scaling_function="sqrt")
    base_thresh = selector_sqrt.fit(scores, aoi)
    assert base_thresh > 0.0

    test_aoi = np.array([0.0, 1.0, 4.0, 16.0, 100.0])
    dyn_thresh_sqrt = selector_sqrt.compute_dynamic_threshold(test_aoi)

    # Monotonicity check
    assert np.all(np.diff(dyn_thresh_sqrt) > 0)
    # At AoI = 0, dynamic threshold should equal base_thresh
    assert np.isclose(dyn_thresh_sqrt[0], base_thresh)
    # At AoI = 16, sqrt is 4, so threshold should be base + 0.2 * 4 = base + 0.8
    assert np.isclose(dyn_thresh_sqrt[3], base_thresh + 0.8)

    # Test log scaling
    selector_log = AoIAdaptiveThreshold(base_percentile=95.0, gamma=0.5, scaling_function="log")
    selector_log.fit(scores)
    dyn_thresh_log = selector_log.compute_dynamic_threshold(test_aoi)
    assert np.isclose(dyn_thresh_log[0], selector_log.fitted_base_threshold)
    assert np.all(np.diff(dyn_thresh_log) > 0)

    # Test linear scaling
    selector_lin = AoIAdaptiveThreshold(base_percentile=95.0, gamma=0.01, scaling_function="linear")
    selector_lin.fit(scores)
    dyn_thresh_lin = selector_lin.compute_dynamic_threshold(test_aoi)
    assert np.isclose(dyn_thresh_lin[4], selector_lin.fitted_base_threshold + 1.0)


def test_aoi_adaptive_threshold_apply():
    """Verify application of adaptive threshold to generate binary classifications."""
    selector = AoIAdaptiveThreshold(base_percentile=90.0, gamma=1.0, scaling_function="linear")
    scores = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    selector.fit(scores)

    # Sample at high AoI should require much higher score to trigger anomaly
    aoi_fresh = np.zeros(len(scores))
    aoi_stale = np.full(len(scores), 10.0)

    pred_fresh = selector.apply_adaptive(scores, aoi_fresh)
    pred_stale = selector.apply_adaptive(scores, aoi_stale)

    # Stale condition raises threshold, so fewer false alarms
    assert np.sum(pred_stale) <= np.sum(pred_fresh)


def test_factory_registration():
    """Verify factory instantiation via get_threshold_selector."""
    sel = get_threshold_selector("aoi_adaptive", base_percentile=92.0, gamma=0.08)
    assert isinstance(sel, AoIAdaptiveThreshold)
    assert sel.base_percentile == 92.0
    assert sel.gamma == 0.08
