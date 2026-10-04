"""
src/anomaly_detection/thresholds.py — Unsupervised anomaly threshold selection.

Implements threshold selection strategies for converting continuous anomaly scores
into binary predictions without using ground-truth labels:
    - Percentile-based (e.g. 95th percentile, matching expected contamination)
    - Otsu's method (bimodal variance maximization)
    - Fixed threshold value
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from src.utils.logging import get_logger

logger = get_logger("anomaly_detection.thresholds")


class BaseThresholdSelector(ABC):
    """Abstract base class for threshold selection mechanisms."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.fitted_threshold: float | None = None

    @abstractmethod
    def fit(self, scores: np.ndarray) -> float:
        """Derive decision threshold from validation anomaly scores.

        Args:
            scores: Continuous anomaly scores (higher = more anomalous).

        Returns:
            Scalar threshold value.
        """
        ...

    def apply(self, scores: np.ndarray, threshold: float | None = None) -> np.ndarray:
        """Convert continuous anomaly scores to binary 0/1 predictions.

        Args:
            scores: Anomaly scores.
            threshold: Optional threshold override.

        Returns:
            Binary numpy int32 array (1 = anomaly, 0 = normal).
        """
        thresh = threshold if threshold is not None else self.fitted_threshold
        if thresh is None:
            raise RuntimeError("Threshold selector must be fitted before calling apply().")
        sc = np.asarray(scores, dtype=np.float64)
        return (sc >= thresh).astype(np.int32)


class PercentileThreshold(BaseThresholdSelector):
    """Selects threshold as a specific empirical percentile of the score distribution."""

    def __init__(self, percentile: float = 95.0) -> None:
        """Initialize percentile threshold selector.

        Args:
            percentile: Percentile cutoff in [0, 100] (default: 95.0).
        """
        super().__init__(name="percentile")
        if not (0.0 <= percentile <= 100.0):
            raise ValueError(f"Percentile must be in [0, 100], got {percentile}")
        self.percentile = percentile

    def fit(self, scores: np.ndarray) -> float:
        """Compute empirical percentile threshold."""
        sc = np.asarray(scores, dtype=np.float64)
        self.fitted_threshold = float(np.percentile(sc, self.percentile))
        logger.info(
            f"PercentileThreshold({self.percentile}%): selected threshold = {self.fitted_threshold:.6f}"
        )
        return self.fitted_threshold


class FixedThreshold(BaseThresholdSelector):
    """Uses a predefined static numerical cutoff."""

    def __init__(self, threshold: float = 0.5) -> None:
        super().__init__(name="fixed")
        self.threshold = threshold
        self.fitted_threshold = threshold

    def fit(self, scores: np.ndarray) -> float:
        self.fitted_threshold = self.threshold
        return self.fitted_threshold


class OtsuThreshold(BaseThresholdSelector):
    """Computes optimal threshold by maximizing inter-class variance (Otsu's method)."""

    def __init__(self, n_bins: int = 256) -> None:
        super().__init__(name="otsu")
        self.n_bins = n_bins

    def fit(self, scores: np.ndarray) -> float:
        """Find threshold maximizing between-class variance across score histogram."""
        sc = np.asarray(scores, dtype=np.float64)
        min_v, max_v = float(np.min(sc)), float(np.max(sc))
        if min_v == max_v:
            self.fitted_threshold = min_v
            return min_v

        counts, bin_edges = np.histogram(sc, bins=self.n_bins, range=(min_v, max_v))
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        total_count = len(sc)

        best_var = 0.0
        best_threshold = bin_centers[0]

        weight_0 = 0.0
        sum_0 = 0.0
        total_sum = float(np.sum(counts * bin_centers))

        for i in range(len(counts)):
            weight_0 += counts[i]
            if weight_0 == 0:
                continue
            weight_1 = total_count - weight_0
            if weight_1 == 0:
                break

            sum_0 += counts[i] * bin_centers[i]
            mean_0 = sum_0 / weight_0
            mean_1 = (total_sum - sum_0) / weight_1

            between_var = weight_0 * weight_1 * ((mean_0 - mean_1) ** 2)
            if between_var > best_var:
                best_var = between_var
                best_threshold = float(bin_centers[i])

        self.fitted_threshold = best_threshold
        logger.info(f"OtsuThreshold: selected threshold = {self.fitted_threshold:.6f}")
        return self.fitted_threshold


class AoIAdaptiveThreshold(BaseThresholdSelector):
    """Dynamically adjusts decision threshold as a function of realized Age of Information (AoI).

    Under synchronization staleness, virtual Digital Twin state drift inflates normal
    residual norms. A static threshold calibrated at fresh state (AoI = 0) experiences severe
    false alarm inflation. AoIAdaptiveThreshold dynamically scales the decision cutoff:

        tau(AoI_t) = tau_0 + gamma * f(AoI_t)

    where tau_0 is the nominal baseline threshold (e.g. 95th percentile under ideal synchronization),
    gamma is the expansion rate, and f(AoI) models physical error diffusion (e.g. sqrt(AoI)).
    """

    def __init__(
        self,
        base_percentile: float = 95.0,
        gamma: float = 0.05,
        scaling_function: str = "sqrt",
    ) -> None:
        """Initialize AoI-adaptive threshold selector.

        Args:
            base_percentile: Baseline percentile cutoff for fresh state (default: 95.0).
            gamma: Adaptation rate scaling factor (gamma >= 0).
            scaling_function: Functional growth form ('sqrt', 'log', 'linear').
        """
        super().__init__(name="aoi_adaptive")
        if not (0.0 <= base_percentile <= 100.0):
            raise ValueError(f"base_percentile must be in [0, 100], got {base_percentile}")
        if gamma < 0.0:
            raise ValueError(f"gamma must be non-negative, got {gamma}")
        if scaling_function not in ["sqrt", "log", "linear"]:
            raise ValueError(
                f"Unsupported scaling_function '{scaling_function}'. Choose from ['sqrt', 'log', 'linear']"
            )

        self.base_percentile = base_percentile
        self.gamma = gamma
        self.scaling_function = scaling_function
        self.fitted_base_threshold: float | None = None

    def fit(self, scores: np.ndarray, aoi_seconds: np.ndarray | None = None) -> float:
        """Derive base fresh-state threshold tau_0 and optionally fit gamma.

        Args:
            scores: Continuous anomaly scores on validation data.
            aoi_seconds: Optional realized AoI values. If provided and contains fresh states,
                tau_0 is calibrated on fresh samples (AoI <= 1.0s).

        Returns:
            Scalar baseline threshold tau_0.
        """
        sc = np.asarray(scores, dtype=np.float64)
        if aoi_seconds is not None:
            aoi = np.asarray(aoi_seconds, dtype=np.float64)
            fresh_mask = aoi <= 1.0
            if np.sum(fresh_mask) >= 10:
                sc_fresh = sc[fresh_mask]
            else:
                sc_fresh = sc
        else:
            sc_fresh = sc

        self.fitted_base_threshold = float(np.percentile(sc_fresh, self.base_percentile))
        self.fitted_threshold = self.fitted_base_threshold
        logger.info(
            f"AoIAdaptiveThreshold(base_pct={self.base_percentile}%, gamma={self.gamma}, fn={self.scaling_function}): "
            f"calibrated base threshold tau_0 = {self.fitted_base_threshold:.6f}"
        )
        return self.fitted_base_threshold

    def compute_dynamic_threshold(self, aoi_seconds: np.ndarray) -> np.ndarray:
        """Compute point-wise decision threshold array for given AoI sequence.

        Args:
            aoi_seconds: Array of realized AoI in seconds.

        Returns:
            Array of scalar thresholds tau(AoI_t).
        """
        if self.fitted_base_threshold is None:
            raise RuntimeError(
                "AoIAdaptiveThreshold must be fitted before computing dynamic threshold."
            )

        aoi = np.asarray(aoi_seconds, dtype=np.float64)
        aoi_clipped = np.maximum(aoi, 0.0)

        if self.scaling_function == "sqrt":
            drift_term = np.sqrt(aoi_clipped)
        elif self.scaling_function == "log":
            drift_term = np.log1p(aoi_clipped)
        else:  # linear
            drift_term = aoi_clipped

        return self.fitted_base_threshold + self.gamma * drift_term

    def apply_adaptive(self, scores: np.ndarray, aoi_seconds: np.ndarray) -> np.ndarray:
        """Convert anomaly scores to binary predictions using dynamic AoI thresholds.

        Args:
            scores: Continuous anomaly scores.
            aoi_seconds: Realized Age of Information for each sample.

        Returns:
            Binary numpy int32 array (1 = anomaly, 0 = normal).
        """
        sc = np.asarray(scores, dtype=np.float64)
        dynamic_thresh = self.compute_dynamic_threshold(aoi_seconds)
        return (sc >= dynamic_thresh).astype(np.int32)


def get_threshold_selector(
    method: str = "percentile",
    **kwargs: Any,
) -> BaseThresholdSelector:
    """Factory function for instantiating threshold selectors.

    Args:
        method: Name of strategy ('percentile', 'fixed', 'otsu', 'aoi_adaptive').
        **kwargs: Method-specific hyperparameters.

    Returns:
        BaseThresholdSelector instance.
    """
    m = method.lower().strip()
    if m == "percentile":
        pct = kwargs.get("percentile", 95.0)
        return PercentileThreshold(percentile=pct)
    elif m == "fixed":
        th = kwargs.get("threshold", 0.5)
        return FixedThreshold(threshold=th)
    elif m == "otsu":
        return OtsuThreshold(n_bins=kwargs.get("n_bins", 256))
    elif m in ["aoi_adaptive", "adaptive"]:
        pct = kwargs.get("base_percentile", kwargs.get("percentile", 95.0))
        gamma = kwargs.get("gamma", 0.05)
        fn = kwargs.get("scaling_function", "sqrt")
        return AoIAdaptiveThreshold(base_percentile=pct, gamma=gamma, scaling_function=fn)
    else:
        raise ValueError(
            f"Unknown threshold method: '{method}'. Valid options: ['percentile', 'fixed', 'otsu', 'aoi_adaptive']"
        )
