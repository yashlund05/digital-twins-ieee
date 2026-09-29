"""
src/forecasting/persistence.py — Zero-parameter Persistence baseline model.

Predicts the next load step as equal to the most recent known load observation:
    y_hat_{t+1} = y_t
Serves as the canonical lowest-complexity benchmark against which all ML models must compete.
"""

import json
from pathlib import Path

import numpy as np

from src.forecasting.base import BaseLoadForecaster
from src.utils.logging import get_logger

logger = get_logger("forecasting.persistence")


class PersistenceForecaster(BaseLoadForecaster):
    """Zero-parameter persistence forecaster (predicts lag-1)."""

    def __init__(self, lag_feature_name: str = "lag_1") -> None:
        """Initialize persistence model.

        Args:
            lag_feature_name: Name of the lag-1 column in tabular feature matrix.
        """
        super().__init__(name="persistence")
        self.lag_feature_name = lag_feature_name
        self._lag_idx: int = 0

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> "PersistenceForecaster":
        """Fit persistence forecaster (identifies lag-1 feature index)."""
        if feature_names is not None:
            self._feature_names = list(feature_names)
            if self.lag_feature_name in feature_names:
                self._lag_idx = feature_names.index(self.lag_feature_name)
            else:
                self._lag_idx = 0
        else:
            self._lag_idx = 0

        self._is_fitted = True
        logger.info(f"Persistence forecaster initialized (using column index {self._lag_idx})")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict next step using lag-1 value."""
        if not self._is_fitted:
            raise RuntimeError("Model must be fitted before calling predict().")

        arr = np.asarray(X)
        if arr.ndim == 1:
            return arr.copy()
        elif arr.ndim == 2:
            return arr[:, self._lag_idx].copy()
        elif arr.ndim == 3:
            # For 3D sequence tensors (N, seq_len, features), pick last timestep's lag feature
            return arr[:, -1, self._lag_idx].copy()
        else:
            raise ValueError(f"Unsupported input dimension for PersistenceForecaster: {arr.ndim}")

    def save(self, file_path: Path | str) -> None:
        """Serialize metadata to JSON."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {
            "name": self.name,
            "lag_feature_name": self.lag_feature_name,
            "lag_idx": self._lag_idx,
            "feature_names": self._feature_names,
            "is_fitted": self._is_fitted,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    @classmethod
    def load(cls, file_path: Path | str) -> "PersistenceForecaster":
        """Deserialize persistence model."""
        path = Path(file_path)
        with open(path, encoding="utf-8") as f:
            meta = json.load(f)
        model = cls(lag_feature_name=meta.get("lag_feature_name", "lag_1"))
        model._lag_idx = meta.get("lag_idx", 0)
        model._feature_names = meta.get("feature_names", [])
        model._is_fitted = meta.get("is_fitted", True)
        return model
