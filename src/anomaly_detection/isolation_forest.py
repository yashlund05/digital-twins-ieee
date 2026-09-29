"""
src/anomaly_detection/isolation_forest.py — Isolation Forest anomaly detector.

Implements the tree-based ensemble anomaly detector using scikit-learn IsolationForest.
Detects anomalous electrical states by isolating observations through recursive random partitioning.
Scores are normalized such that higher score = more anomalous.
"""

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from src.anomaly_detection.detector import BaseAnomalyDetector
from src.utils.config import IsolationForestConfig
from src.utils.logging import get_logger

logger = get_logger("anomaly_detection.isolation_forest")


class IsolationForestDetector(BaseAnomalyDetector):
    """Unsupervised Isolation Forest detector for tabular power grid telemetry."""

    def __init__(
        self,
        config: IsolationForestConfig | None = None,
        n_estimators: int = 100,
        contamination: float = 0.05,
        random_state: int = 42,
        n_jobs: int = -1,
        **kwargs: Any,
    ) -> None:
        """Initialize IsolationForestDetector.

        Args:
            config: Optional IsolationForestConfig instance.
            n_estimators: Number of isolation trees (default: 100).
            contamination: Expected anomaly proportion (default: 0.05).
            random_state: Seed for reproducibility.
            n_jobs: Number of CPU workers (-1 = all cores).
        """
        super().__init__(name="isolation_forest")
        cfg = config or IsolationForestConfig()

        self.n_estimators = kwargs.get("n_estimators", cfg.n_estimators if config else n_estimators)
        self.contamination = kwargs.get(
            "contamination", cfg.contamination if config else contamination
        )
        self.random_state = kwargs.get("random_state", cfg.random_state if config else random_state)
        self.n_jobs = kwargs.get("n_jobs", cfg.n_jobs if config else n_jobs)

        self.model: IsolationForest | None = None

    def fit(
        self,
        X_train: np.ndarray,
        X_val: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> "IsolationForestDetector":
        """Fit Isolation Forest on normal/unlabeled power flow data."""
        if feature_names is not None:
            self._feature_names = list(feature_names)

        logger.info(
            f"Fitting IsolationForest (n_trees={self.n_estimators}, contamination={self.contamination}) "
            f"on {len(X_train)} samples..."
        )

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )
        self.model.fit(X_train)
        self._is_fitted = True

        logger.info("IsolationForest fitting complete.")
        return self

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Compute anomaly scores. Higher score = more anomalous.

        In scikit-learn, score_samples returns negative anomaly score (lower is more anomalous).
        We negate it: score = -score_samples(X).
        """
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Detector must be fitted before score_samples() is called.")

        # Invert sklearn's score so higher = more abnormal
        raw_scores = self.model.score_samples(X)
        return -np.asarray(raw_scores, dtype=np.float64)

    def save(self, file_path: Path | str) -> None:
        """Save model weights and metadata."""
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Cannot save unfitted detector.")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        joblib_path = path.with_suffix(".joblib")
        joblib.dump(self.model, joblib_path)

        meta_path = path.with_suffix(".meta.json")
        meta = {
            "name": self.name,
            "n_estimators": self.n_estimators,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "n_jobs": self.n_jobs,
            "threshold": self._threshold,
            "feature_names": self._feature_names,
            "is_fitted": self._is_fitted,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Saved IsolationForest model to {joblib_path}")

    @classmethod
    def load(cls, file_path: Path | str) -> "IsolationForestDetector":
        """Restore detector from serialized files."""
        path = Path(file_path)
        meta_path = path.with_suffix(".meta.json")
        joblib_path = path.with_suffix(".joblib")

        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found at {meta_path}")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        instance = cls(
            n_estimators=meta.get("n_estimators", 100),
            contamination=meta.get("contamination", 0.05),
            random_state=meta.get("random_state", 42),
            n_jobs=meta.get("n_jobs", -1),
        )
        instance._threshold = meta.get("threshold")
        instance._feature_names = meta.get("feature_names", [])
        instance._is_fitted = meta.get("is_fitted", True)

        instance.model = joblib.load(joblib_path)
        return instance
