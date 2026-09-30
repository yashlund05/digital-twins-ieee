"""
src/residuals/normalizer.py — Physics-based residual normalization engine.

Provides zero-leakage normalization for raw Digital Twin residuals.
Fitted strictly on the training partition; test and validation partitions
never alter normalization statistics.
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.io import ensure_dir, load_json, save_json
from src.utils.logging import get_logger

logger = get_logger("residuals.normalizer")


class ResidualNormalizer:
    """Zero-leakage normalizer for Digital Twin residuals.

    Supported methods:
    - 'z_score': Standardization to zero mean and unit variance.
    - 'min_max': Scaling to [0, 1] range using training minimum and maximum.
    - 'robust': Median and Interquartile Range (IQR) scaling, robust to outliers.
    """

    SUPPORTED_METHODS = ("z_score", "min_max", "robust")

    def __init__(self, method: str = "z_score", epsilon: float = 1e-8) -> None:
        """Initialize the residual normalizer.

        Args:
            method: Normalization strategy ('z_score', 'min_max', 'robust').
            epsilon: Small numerical constant to prevent division by zero.
        """
        if method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported normalization method '{method}'. "
                f"Supported methods: {self.SUPPORTED_METHODS}"
            )
        self.method = method
        self.epsilon = float(epsilon)
        self.is_fitted = False

        # Fitted parameters
        self.feature_names_: list[str] | None = None
        self.n_features_in_: int | None = None
        self.n_samples_seen_: int | None = None

        # Statistics arrays (shape: (n_features,))
        self.center_: np.ndarray | None = None  # mean or min or median
        self.scale_: np.ndarray | None = None  # std or (max - min) or IQR
        self.raw_params_: dict[str, Any] = {}

    def fit(
        self,
        X: np.ndarray | pd.DataFrame | pd.Series,
        feature_names: list[str] | None = None,
    ) -> "ResidualNormalizer":
        """Fit normalization parameters strictly on the provided training partition.

        Args:
            X: Training residuals. Shape (n_samples, n_features) or (n_samples,).
            feature_names: Optional explicit list of feature names.

        Returns:
            Fitted instance of self.
        """
        if isinstance(X, pd.DataFrame):
            self.feature_names_ = list(X.columns)
            arr = X.values.astype(np.float64)
        elif isinstance(X, pd.Series):
            self.feature_names_ = [str(X.name or "feature_0")]
            arr = X.values.reshape(-1, 1).astype(np.float64)
        else:
            arr = np.asarray(X, dtype=np.float64)
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            self.feature_names_ = feature_names or [f"feature_{i}" for i in range(arr.shape[1])]

        if arr.size == 0 or arr.shape[0] == 0:
            raise ValueError("Cannot fit normalizer on empty array.")

        if np.isnan(arr).any() or np.isinf(arr).any():
            raise ValueError("Training data contains NaN or Inf values.")

        self.n_samples_seen_ = arr.shape[0]
        self.n_features_in_ = arr.shape[1]

        if self.method == "z_score":
            mean = np.mean(arr, axis=0)
            std = np.std(arr, axis=0, ddof=0)
            # Apply epsilon floor for zero-variance features
            scale = np.where(std < self.epsilon, 1.0, std)
            self.center_ = mean
            self.scale_ = scale
            self.raw_params_ = {
                "mean": mean.tolist(),
                "std": std.tolist(),
            }

        elif self.method == "min_max":
            min_val = np.min(arr, axis=0)
            max_val = np.max(arr, axis=0)
            diff = max_val - min_val
            scale = np.where(diff < self.epsilon, 1.0, diff)
            self.center_ = min_val
            self.scale_ = scale
            self.raw_params_ = {
                "min": min_val.tolist(),
                "max": max_val.tolist(),
            }

        elif self.method == "robust":
            median = np.median(arr, axis=0)
            q25 = np.percentile(arr, 25.0, axis=0)
            q75 = np.percentile(arr, 75.0, axis=0)
            iqr = q75 - q25
            scale = np.where(iqr < self.epsilon, 1.0, iqr)
            self.center_ = median
            self.scale_ = scale
            self.raw_params_ = {
                "median": median.tolist(),
                "iqr": iqr.tolist(),
                "q25": q25.tolist(),
                "q75": q75.tolist(),
            }

        self.is_fitted = True
        return self

    def transform(
        self,
        X: np.ndarray | pd.DataFrame | pd.Series,
    ) -> np.ndarray | pd.DataFrame:
        """Apply fitted normalization parameters to input residuals.

        Args:
            X: Input residuals to normalize.

        Returns:
            Normalized array or DataFrame matching input format.

        Raises:
            RuntimeError: If called before fit.
            ValueError: On dimension or feature mismatch.
        """
        if not self.is_fitted or self.center_ is None or self.scale_ is None:
            raise RuntimeError("ResidualNormalizer must be fitted before calling transform().")

        is_df = isinstance(X, pd.DataFrame)
        is_series = isinstance(X, pd.Series)

        if is_df:
            arr = X.values.astype(np.float64)
        elif is_series:
            arr = X.values.reshape(-1, 1).astype(np.float64)
        else:
            arr = np.asarray(X, dtype=np.float64)
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)

        if arr.shape[1] != self.n_features_in_:
            raise ValueError(
                f"Feature count mismatch: fitted on {self.n_features_in_} features, "
                f"got {arr.shape[1]} features."
            )

        if np.isnan(arr).any() or np.isinf(arr).any():
            raise ValueError("Input array contains NaN or Inf values.")

        # Element-wise scaling
        norm_arr = (arr - self.center_) / self.scale_

        if is_df:
            return pd.DataFrame(norm_arr, index=X.index, columns=X.columns)
        elif is_series:
            return pd.Series(norm_arr.flatten(), index=X.index, name=X.name)
        elif isinstance(X, np.ndarray) and X.ndim == 1:
            return norm_arr.flatten()
        return norm_arr

    def fit_transform(
        self,
        X: np.ndarray | pd.DataFrame | pd.Series,
        feature_names: list[str] | None = None,
    ) -> np.ndarray | pd.DataFrame:
        """Fit on X and immediately transform X.

        Args:
            X: Training residuals.
            feature_names: Optional feature names.

        Returns:
            Normalized training residuals.
        """
        return self.fit(X, feature_names=feature_names).transform(X)

    def inverse_transform(
        self,
        X: np.ndarray | pd.DataFrame | pd.Series,
    ) -> np.ndarray | pd.DataFrame:
        """Revert normalized residuals back to raw physical units.

        Args:
            X: Normalized residuals.

        Returns:
            Unnormalized residuals in original units.
        """
        if not self.is_fitted or self.center_ is None or self.scale_ is None:
            raise RuntimeError("ResidualNormalizer must be fitted before inverse_transform().")

        is_df = isinstance(X, pd.DataFrame)
        if is_df:
            arr = X.values.astype(np.float64)
        else:
            arr = np.asarray(X, dtype=np.float64)
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)

        raw_arr = (arr * self.scale_) + self.center_

        if is_df:
            return pd.DataFrame(raw_arr, index=X.index, columns=X.columns)
        elif isinstance(X, np.ndarray) and X.ndim == 1:
            return raw_arr.flatten()
        return raw_arr

    def to_dict(self) -> dict[str, Any]:
        """Serialize normalizer configuration and fitted parameters to a dictionary."""
        return {
            "method": self.method,
            "epsilon": self.epsilon,
            "is_fitted": self.is_fitted,
            "n_features_in": self.n_features_in_,
            "n_samples_seen": self.n_samples_seen_,
            "feature_names": self.feature_names_,
            "center": self.center_.tolist() if self.center_ is not None else None,
            "scale": self.scale_.tolist() if self.scale_ is not None else None,
            "raw_params": self.raw_params_,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResidualNormalizer":
        """Deserialize a normalizer from a dictionary."""
        instance = cls(method=data["method"], epsilon=data.get("epsilon", 1e-8))
        instance.is_fitted = data["is_fitted"]
        instance.n_features_in_ = data["n_features_in"]
        instance.n_samples_seen_ = data["n_samples_seen"]
        instance.feature_names_ = data.get("feature_names")
        if data.get("center") is not None:
            instance.center_ = np.array(data["center"], dtype=np.float64)
        if data.get("scale") is not None:
            instance.scale_ = np.array(data["scale"], dtype=np.float64)
        instance.raw_params_ = data.get("raw_params", {})
        return instance

    def save(self, file_path: Path | str) -> None:
        """Save fitted normalizer to a JSON file.

        Args:
            file_path: Destination path for JSON serialization.
        """
        path = Path(file_path)
        ensure_dir(path.parent)
        save_json(self.to_dict(), path)
        logger.info(f"Saved ResidualNormalizer to {path}")

    @classmethod
    def load(cls, file_path: Path | str) -> "ResidualNormalizer":
        """Load a fitted normalizer from a JSON file.

        Args:
            file_path: Path to serialized normalizer JSON.

        Returns:
            Restored ResidualNormalizer instance.
        """
        data = load_json(file_path)
        return cls.from_dict(data)
