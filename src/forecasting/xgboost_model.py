"""
src/forecasting/xgboost_model.py — XGBoost gradient-boosted decision tree load estimator.

Implements the non-linear machine learning baseline for short-term load estimation
using XGBoost with early stopping and configurable hyperparameters.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import xgboost as xgb

from src.forecasting.base import BaseLoadForecaster
from src.utils.config import XGBoostConfig
from src.utils.logging import get_logger

logger = get_logger("forecasting.xgboost")


class XGBoostForecaster(BaseLoadForecaster):
    """XGBoost regression model for tabular short-term load estimation."""

    def __init__(
        self,
        config: XGBoostConfig | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize XGBoost forecaster.

        Args:
            config: XGBoostConfig instance or None (uses defaults).
            **kwargs: Overrides for hyperparameters.
        """
        super().__init__(name="xgboost")
        cfg = config or XGBoostConfig()

        self.params: dict[str, Any] = {
            "n_estimators": kwargs.get("n_estimators", cfg.n_estimators),
            "max_depth": kwargs.get("max_depth", cfg.max_depth),
            "learning_rate": kwargs.get("learning_rate", cfg.learning_rate),
            "subsample": kwargs.get("subsample", cfg.subsample),
            "colsample_bytree": kwargs.get("colsample_bytree", cfg.colsample_bytree),
            "random_state": kwargs.get("random_state", cfg.random_state),
            "early_stopping_rounds": kwargs.get("early_stopping_rounds", cfg.early_stopping_rounds),
            "eval_metric": kwargs.get("eval_metric", cfg.eval_metric),
        }

        self.model: xgb.XGBRegressor | None = None

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> "XGBoostForecaster":
        """Train the XGBoost regressor with early stopping if validation set provided."""
        if feature_names is not None:
            self._feature_names = list(feature_names)

        eval_set = [(X_val, y_val)] if (X_val is not None and y_val is not None) else None

        # Build XGBRegressor
        model_kwargs = dict(self.params)
        # early_stopping_rounds requires eval_set
        if eval_set is None:
            model_kwargs.pop("early_stopping_rounds", None)
            model_kwargs.pop("eval_metric", None)

        self.model = xgb.XGBRegressor(
            **model_kwargs,
            objective="reg:squarederror",
            n_jobs=-1,
        )

        logger.info(f"Training XGBoost model on {len(X_train)} samples...")
        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            verbose=False,
        )

        self._is_fitted = True
        logger.info(
            f"XGBoost training complete. Best iteration: "
            f"{getattr(self.model, 'best_iteration', self.params['n_estimators'])}"
        )
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions using trained XGBoost model."""
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before predict() is called.")
        preds = self.model.predict(X)
        return np.asarray(preds, dtype=np.float64)

    def save(self, file_path: Path | str) -> None:
        """Save model JSON and metadata."""
        if not self._is_fitted or self.model is None:
            raise RuntimeError("Cannot save unfitted model.")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_json_path = path.with_suffix(".json")
        self.model.save_model(str(model_json_path))

        meta_path = path.with_suffix(".meta.json")
        meta = {
            "name": self.name,
            "params": self.params,
            "feature_names": self._feature_names,
            "is_fitted": self._is_fitted,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Saved XGBoost model to {model_json_path}")

    @classmethod
    def load(cls, file_path: Path | str) -> "XGBoostForecaster":
        """Load trained model and metadata."""
        path = Path(file_path)
        meta_path = path.with_suffix(".meta.json")
        model_json_path = path.with_suffix(".json")

        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found at {meta_path}")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        instance = cls(**meta.get("params", {}))
        instance._feature_names = meta.get("feature_names", [])
        instance._is_fitted = meta.get("is_fitted", True)

        instance.model = xgb.XGBRegressor()
        instance.model.load_model(str(model_json_path))
        return instance
