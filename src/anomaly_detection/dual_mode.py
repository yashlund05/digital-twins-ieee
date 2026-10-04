"""src/anomaly_detection/dual_mode.py — Dual-Mode Representation Switching Compensator.

Implements online representation switching between physics-derived state residuals
and direct raw load telemetry based on realized Age of Information (AoI).

Motivation:
    - At low staleness (AoI < 5.0s), physics-residual representation achieves near-perfect
      discrimination (F1 ~ 0.978 vs 0.539).
    - At high staleness (AoI >= 5.0s), virtual DT state drift contaminates residual space,
      inverting performance such that raw inputs outperform residual features.
    - DualModeInversionCompensator dynamically routes detection through the optimal
      representation, guaranteeing robust performance across all synchronization regimes.
"""

from typing import Any

import numpy as np

from src.evaluation.anomaly_metrics import compute_anomaly_metrics
from src.utils.logging import get_logger

logger = get_logger("anomaly_detection.dual_mode")


class DualModeInversionCompensator:
    """Dynamic representation switching detector based on Age of Information (AoI).

    Routes anomaly decision through physics-derived residuals when virtual state is fresh,
    and switches to raw telemetry when synchronization staleness exceeds the empirical
    inversion cliff (default: AoI* = 5.0s).
    """

    def __init__(
        self,
        aoi_inversion_threshold: float = 5.0,
        smooth_blending: bool = False,
        transition_width: float = 1.5,
    ) -> None:
        """Initialize dual-mode compensator.

        Args:
            aoi_inversion_threshold: Critical AoI in seconds at which representation
                inversion occurs (default: 5.0s based on Phase 11 change-point analysis).
            smooth_blending: Whether to use soft logistic weighting instead of hard switching.
            transition_width: Smoothing scale parameter beta for logistic transition.
        """
        if aoi_inversion_threshold < 0.0:
            raise ValueError(
                f"aoi_inversion_threshold must be non-negative, got {aoi_inversion_threshold}"
            )
        if transition_width <= 0.0:
            raise ValueError(f"transition_width must be positive, got {transition_width}")

        self.aoi_inversion_threshold = float(aoi_inversion_threshold)
        self.smooth_blending = bool(smooth_blending)
        self.transition_width = float(transition_width)

    def compute_routing_weights(self, aoi_seconds: np.ndarray) -> np.ndarray:
        """Compute raw-representation routing weight w_raw in [0, 1] for each sample.

        w_raw = 0 means 100% residual representation (fresh state).
        w_raw = 1 means 100% raw representation (stale state).

        Args:
            aoi_seconds: Array of realized AoI values.

        Returns:
            1D numpy float64 array of raw routing weights in [0, 1].
        """
        aoi = np.asarray(aoi_seconds, dtype=np.float64)
        if not self.smooth_blending:
            # Hard switching: 1 if AoI >= threshold else 0
            return (aoi >= self.aoi_inversion_threshold).astype(np.float64)

        # Soft logistic sigmoid transition
        z = (aoi - self.aoi_inversion_threshold) / self.transition_width
        # Clip z to avoid numerical overflow in exp
        z_clipped = np.clip(z, -20.0, 20.0)
        return 1.0 / (1.0 + np.exp(-z_clipped))

    def predict_hybrid(
        self,
        scores_residual: np.ndarray,
        scores_raw: np.ndarray,
        aoi_seconds: np.ndarray,
        threshold_residual: float,
        threshold_raw: float,
    ) -> dict[str, np.ndarray]:
        """Generate dual-mode hybrid predictions and routing metadata.

        Args:
            scores_residual: Continuous anomaly scores from residual detector.
            scores_raw: Continuous anomaly scores from raw detector.
            aoi_seconds: Realized Age of Information for each sample.
            threshold_residual: Pre-calibrated decision threshold for residual scores.
            threshold_raw: Pre-calibrated decision threshold for raw scores.

        Returns:
            Dictionary containing:
                - 'y_pred': Binary predictions (1 = anomaly, 0 = normal).
                - 'mode_selected': String representation mode per timestep ('residual' or 'raw').
                - 'w_raw': Array of raw routing weights.
                - 'fused_score': Continuous blended or selected score.
        """
        sc_res = np.asarray(scores_residual, dtype=np.float64)
        sc_raw = np.asarray(scores_raw, dtype=np.float64)
        aoi = np.asarray(aoi_seconds, dtype=np.float64)

        if len(sc_res) != len(sc_raw) or len(sc_res) != len(aoi):
            raise ValueError(
                f"Array length mismatch: scores_res={len(sc_res)}, scores_raw={len(sc_raw)}, aoi={len(aoi)}"
            )

        w_raw = self.compute_routing_weights(aoi)

        # Standard binary decisions in respective spaces
        pred_res = (sc_res >= threshold_residual).astype(np.int32)
        pred_raw = (sc_raw >= threshold_raw).astype(np.int32)

        if not self.smooth_blending:
            # Hard routing: pick detector based on AoI
            use_raw_mask = aoi >= self.aoi_inversion_threshold
            y_pred = np.where(use_raw_mask, pred_raw, pred_res)
            fused_score = np.where(use_raw_mask, sc_raw, sc_res)
            mode_selected = np.where(use_raw_mask, "raw", "residual")
        else:
            # Normalize scores relative to thresholds for continuous fusion
            norm_sc_res = sc_res / max(threshold_residual, 1e-8)
            norm_sc_raw = sc_raw / max(threshold_raw, 1e-8)
            fused_norm = (1.0 - w_raw) * norm_sc_res + w_raw * norm_sc_raw
            y_pred = (fused_norm >= 1.0).astype(np.int32)
            fused_score = fused_norm
            mode_selected = np.where(w_raw >= 0.5, "raw", "residual")

        return {
            "y_pred": y_pred,
            "mode_selected": mode_selected,
            "w_raw": w_raw,
            "fused_score": fused_score,
        }

    def evaluate_mitigation(
        self,
        y_true: np.ndarray,
        scores_residual: np.ndarray,
        scores_raw: np.ndarray,
        aoi_seconds: np.ndarray,
        threshold_residual: float,
        threshold_raw: float,
    ) -> dict[str, Any]:
        """Comprehensive comparative evaluation of Dual-Mode vs. uncompensated baselines.

        Args:
            y_true: Ground truth binary labels.
            scores_residual: Residual detector continuous anomaly scores.
            scores_raw: Raw detector continuous anomaly scores.
            aoi_seconds: Realized Age of Information in seconds.
            threshold_residual: Threshold for residual scores.
            threshold_raw: Threshold for raw scores.

        Returns:
            Dictionary with metrics for uncompensated residual, uncompensated raw,
            dual-mode hybrid, and absolute/relative improvement.
        """
        y_t = np.asarray(y_true, dtype=np.int32)
        sc_res = np.asarray(scores_residual, dtype=np.float64)
        sc_raw = np.asarray(scores_raw, dtype=np.float64)

        pred_res = (sc_res >= threshold_residual).astype(np.int32)
        pred_raw = (sc_raw >= threshold_raw).astype(np.int32)

        m_res = compute_anomaly_metrics(y_t, pred_res, sc_res)
        m_raw = compute_anomaly_metrics(y_t, pred_raw, sc_raw)

        hybrid_out = self.predict_hybrid(
            scores_residual=sc_res,
            scores_raw=sc_raw,
            aoi_seconds=aoi_seconds,
            threshold_residual=threshold_residual,
            threshold_raw=threshold_raw,
        )
        m_hybrid = compute_anomaly_metrics(y_t, hybrid_out["y_pred"], hybrid_out["fused_score"])

        delta_f1_vs_residual = float(m_hybrid["f1"] - m_res["f1"])
        delta_f1_vs_raw = float(m_hybrid["f1"] - m_raw["f1"])

        percent_switched_to_raw = float(np.mean(hybrid_out["w_raw"] >= 0.5) * 100.0)

        logger.info(
            f"Dual-Mode Evaluation: Uncompensated Residual F1={m_res['f1']:.4f}, "
            f"Uncompensated Raw F1={m_raw['f1']:.4f} -> Dual-Mode F1={m_hybrid['f1']:.4f} "
            f"(Delta vs Res = {delta_f1_vs_residual:+.4f}, Switched={percent_switched_to_raw:.1f}%)"
        )

        return {
            "uncompensated_residual": m_res,
            "uncompensated_raw": m_raw,
            "dual_mode_hybrid": m_hybrid,
            "delta_f1_vs_residual": delta_f1_vs_residual,
            "delta_f1_vs_raw": delta_f1_vs_raw,
            "percent_switched_to_raw": percent_switched_to_raw,
            "routing_metadata": hybrid_out,
        }
