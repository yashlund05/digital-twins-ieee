"""
src/forecasting/base.py — Abstract base class for load estimation forecasters.

Defines the standard lifecycle interface (fit, predict, save, load) for all
load forecasting models (Persistence, XGBoost, LSTM).
"""

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class BaseLoadForecaster(ABC):
    """Abstract base class for all load estimation models."""

    def __init__(self, name: str) -> None:
        """Initialize base forecaster.

        Args:
            name: Identifier for the model instance.
        """
        self._name = name
        self._is_fitted = False
        self._feature_names: list[str] = []

    @property
    def name(self) -> str:
        """Return forecaster model name."""
        return self._name

    @property
    def is_fitted(self) -> bool:
        """Return whether model has been trained."""
        return self._is_fitted

    @property
    def feature_names(self) -> list[str]:
        """Return names of features used by the model."""
        return list(self._feature_names)

    @abstractmethod
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> "BaseLoadForecaster":
        """Train model parameters on the training split.

        Args:
            X_train: Input feature array of shape (N, features) or (N, lookback, features).
            y_train: Target array of shape (N,) or (N, targets).
            X_val: Optional validation features for early stopping.
            y_val: Optional validation targets for early stopping.
            feature_names: Optional list of feature column names.

        Returns:
            Self (fitted model).
        """
        ...

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate load forecasts for input features X.

        Args:
            X: Input feature array.

        Returns:
            1D or 2D numpy array of predicted load values.
        """
        ...

    @abstractmethod
    def save(self, file_path: Path | str) -> None:
        """Serialize model weights and metadata to disk.

        Args:
            file_path: Destination path on filesystem.
        """
        ...

    @classmethod
    @abstractmethod
    def load(cls, file_path: Path | str) -> "BaseLoadForecaster":
        """Deserialize and restore model from disk.

        Args:
            file_path: Source path on filesystem.

        Returns:
            Loaded forecaster instance.
        """
        ...
