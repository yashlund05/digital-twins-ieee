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


def get_threshold_selector(
    method: str = "percentile",
    **kwargs: Any,
) -> BaseThresholdSelector:
    """Factory function for instantiating threshold selectors.

    Args:
        method: Name of strategy ('percentile', 'fixed', 'otsu').
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
    else:
        raise ValueError(
            f"Unknown threshold method: '{method}'. Valid options: ['percentile', 'fixed', 'otsu']"
        )
