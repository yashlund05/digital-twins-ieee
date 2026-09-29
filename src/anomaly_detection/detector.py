"""
src/anomaly_detection/detector.py — Abstract base class for unsupervised anomaly detectors.

Defines the standard lifecycle interface (fit, score_samples, predict, save, load)
for all anomaly detection models (Isolation Forest, LSTM Autoencoder).
All models are strictly unsupervised: training uses only feature matrices X,
never anomaly labels y.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class BaseAnomalyDetector(ABC):
    """Abstract base class for all unsupervised anomaly detection models."""

    def __init__(self, name: str) -> None:
        """Initialize base anomaly detector.

        Args:
            name: Identifier for the model architecture.
        """
        self._name = name
        self._threshold: float | None = None
        self._is_fitted: bool = False
        self._feature_names: list[str] = []

    @property
    def name(self) -> str:
        """Detector model name."""
        return self._name

    @property
    def is_fitted(self) -> bool:
        """Whether the detector has been fitted."""
        return self._is_fitted

    @property
    def threshold(self) -> float | None:
        """Decision threshold for classifying samples as anomalous."""
        return self._threshold

    def set_threshold(self, threshold: float) -> None:
        """Set decision threshold.

        Args:
            threshold: Value above which samples are flagged as anomalous (1).
        """
        self._threshold = float(threshold)

    @abstractmethod
    def fit(
        self,
        X_train: np.ndarray,
        X_val: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> "BaseAnomalyDetector":
        """Fit detector on normal/unlabeled data (unsupervised).

        Args:
            X_train: Training feature array (no anomaly labels).
            X_val: Optional validation feature array.
            feature_names: Optional list of feature names.

        Returns:
            Self (fitted detector).
        """
        ...

    @abstractmethod
    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Calculate continuous anomaly score for each sample.

        Convention: Higher score = more anomalous.

        Args:
            X: Input feature array.

        Returns:
            1D array of float anomaly scores.
        """
        ...

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate binary anomaly predictions (1 = anomaly, 0 = normal).

        Args:
            X: Input feature array.

        Returns:
            1D array of int32 (0 or 1).
        """
        if not self._is_fitted:
            raise RuntimeError("Detector must be fitted before predict() is called.")
        if self._threshold is None:
            raise RuntimeError("Decision threshold must be set before predict() is called.")

        scores = self.score_samples(X)
        return (scores >= self._threshold).astype(np.int32)

    @abstractmethod
    def save(self, file_path: Path | str) -> None:
        """Serialize detector weights and metadata to disk."""
        ...

    @classmethod
    @abstractmethod
    def load(cls, file_path: Path | str) -> "BaseAnomalyDetector":
        """Deserialize and restore detector from disk."""
        ...
