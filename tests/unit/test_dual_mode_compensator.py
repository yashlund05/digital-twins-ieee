"""tests/unit/test_dual_mode_compensator.py — Unit tests for DualModeInversionCompensator."""

import numpy as np
import pytest

from src.anomaly_detection.dual_mode import DualModeInversionCompensator


def test_dual_mode_compensator_initialization():
    """Verify parameter initialization and validation."""
    comp = DualModeInversionCompensator(aoi_inversion_threshold=5.0, smooth_blending=False)
    assert comp.aoi_inversion_threshold == 5.0
    assert not comp.smooth_blending

    with pytest.raises(ValueError, match="non-negative"):
        DualModeInversionCompensator(aoi_inversion_threshold=-1.0)

    with pytest.raises(ValueError, match="positive"):
        DualModeInversionCompensator(transition_width=0.0)


def test_routing_weights():
    """Verify routing weight computation for hard and soft blending."""
    aoi = np.array([0.0, 2.0, 5.0, 10.0])

    # Hard switching
    comp_hard = DualModeInversionCompensator(aoi_inversion_threshold=5.0, smooth_blending=False)
    w_hard = comp_hard.compute_routing_weights(aoi)
    assert np.array_equal(w_hard, [0.0, 0.0, 1.0, 1.0])

    # Soft blending
    comp_soft = DualModeInversionCompensator(
        aoi_inversion_threshold=5.0, smooth_blending=True, transition_width=1.0
    )
    w_soft = comp_soft.compute_routing_weights(aoi)
    assert np.all(np.diff(w_soft) > 0)
    # Exactly at threshold, logistic should be 0.5
    assert np.isclose(w_soft[2], 0.5)


def test_predict_hybrid_hard():
    """Verify hard representation routing based on AoI threshold."""
    comp = DualModeInversionCompensator(aoi_inversion_threshold=5.0, smooth_blending=False)

    scores_res = np.array([0.8, 0.8, 0.8, 0.8])
    scores_raw = np.array([0.2, 0.2, 0.2, 0.2])
    aoi = np.array([0.0, 2.0, 5.0, 15.0])

    # Residual threshold 0.5, Raw threshold 0.5
    res = comp.predict_hybrid(
        scores_residual=scores_res,
        scores_raw=scores_raw,
        aoi_seconds=aoi,
        threshold_residual=0.5,
        threshold_raw=0.5,
    )

    # First two samples (AoI < 5) use residual (score 0.8 >= 0.5 -> 1)
    # Last two samples (AoI >= 5) use raw (score 0.2 < 0.5 -> 0)
    assert np.array_equal(res["y_pred"], [1, 1, 0, 0])
    assert np.array_equal(res["mode_selected"], ["residual", "residual", "raw", "raw"])


def test_evaluate_mitigation():
    """Verify comparative evaluation computation."""
    np.random.seed(42)
    n = 100
    y_true = np.zeros(n, dtype=int)
    y_true[::10] = 1  # 10 anomalies

    # Fresh samples: residual works well, raw works moderately
    # Stale samples: residual gives random scores (drifted), raw works moderately
    aoi = np.linspace(0, 50, n)
    scores_res = np.where(y_true == 1, 0.9, 0.1)
    # Add noise to residual as AoI grows
    scores_res += (aoi / 50.0) * 0.8

    scores_raw = np.where(y_true == 1, 0.7, 0.2)

    comp = DualModeInversionCompensator(aoi_inversion_threshold=5.0)
    eval_res = comp.evaluate_mitigation(
        y_true=y_true,
        scores_residual=scores_res,
        scores_raw=scores_raw,
        aoi_seconds=aoi,
        threshold_residual=0.5,
        threshold_raw=0.5,
    )

    assert "uncompensated_residual" in eval_res
    assert "uncompensated_raw" in eval_res
    assert "dual_mode_hybrid" in eval_res
    assert "delta_f1_vs_residual" in eval_res
    assert eval_res["percent_switched_to_raw"] > 0
