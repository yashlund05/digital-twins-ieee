"""
src/residuals/features.py — Deterministic feature extraction on Digital Twin residuals.

Extracts direct, non-linear, spatial-aggregate, and causal temporal features
from raw or normalized residuals with strictly zero future leakage.
"""

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger("residuals.features")


class ResidualFeatureConfig(BaseModel):
    """Configuration options for residual feature engineering."""

    include_raw: bool = Field(default=True, description="Include direct raw residual r_t")
    include_absolute: bool = Field(
        default=False, description="Include absolute residual |r_t|"
    )
    include_squared: bool = Field(default=False, description="Include squared residual r_t^2")
    include_l2_norm: bool = Field(
        default=False, description="Include spatial L2 norm across all buses ||r_t||_2"
    )
    include_mean_absolute: bool = Field(
        default=False, description="Include mean absolute residual across buses"
    )
    include_max_absolute: bool = Field(
        default=False, description="Include maximum absolute residual across buses"
    )
    lags: list[int] = Field(
        default_factory=list,
        description="List of causal backward-looking lag steps (e.g. [1, 2, 4])",
    )


class ResidualFeatureExtractor:
    """Extracts configurable feature sets from Digital Twin residuals.

    Guarantees strict temporal causality: at time t, only past observations
    (t, t-1, t-2, ...) may be used. No centered rolling windows or future interpolation.
    """

    def __init__(self, config: ResidualFeatureConfig | dict[str, Any] | None = None) -> None:
        """Initialize the residual feature extractor.

        Args:
            config: ResidualFeatureConfig instance, dictionary, or None (defaults to raw only).
        """
        if config is None:
            self.config = ResidualFeatureConfig()
        elif isinstance(config, dict):
            self.config = ResidualFeatureConfig(**config)
        else:
            self.config = config

        # Validate lags are strictly positive integers (causal backward-looking)
        for k in self.config.lags:
            if not isinstance(k, int) or k <= 0:
                raise ValueError(
                    f"Lag step {k} is invalid. Lags must be strictly positive integers (k > 0) "
                    "to prevent temporal and future data leakage."
                )

    def extract(
        self,
        residuals: np.ndarray | pd.DataFrame,
        feature_names: list[str] | None = None,
    ) -> np.ndarray | pd.DataFrame:
        """Extract configured residual features from the input residual matrix.

        Args:
            residuals: Input residuals array or DataFrame of shape (n_samples, n_features).
            feature_names: Optional explicit names for input features.

        Returns:
            Engineered feature matrix matching input type (NumPy array or DataFrame).
        """
        is_df = isinstance(residuals, pd.DataFrame)

        if is_df:
            arr = residuals.values.astype(np.float64)
            base_names = list(residuals.columns)
            index = residuals.index
        else:
            arr = np.asarray(residuals, dtype=np.float64)
            if arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            base_names = feature_names or [f"res_{i}" for i in range(arr.shape[1])]
            index = None

        if arr.size == 0 or arr.shape[0] == 0:
            raise ValueError("Cannot extract features from empty residual matrix.")

        n_samples, n_features = arr.shape
        feature_blocks: list[np.ndarray] = []
        out_names: list[str] = []

        # 1. Direct residual: r_t
        if self.config.include_raw:
            feature_blocks.append(arr)
            out_names.extend(base_names)

        # 2. Absolute residual: |r_t|
        if self.config.include_absolute:
            abs_res = np.abs(arr)
            feature_blocks.append(abs_res)
            out_names.extend([f"abs_{name}" for name in base_names])

        # 3. Squared residual: r_t^2
        if self.config.include_squared:
            sq_res = np.square(arr)
            feature_blocks.append(sq_res)
            out_names.extend([f"sq_{name}" for name in base_names])

        # 4. Spatial aggregate: L2 norm across all buses ||r_t||_2
        if self.config.include_l2_norm:
            l2_norm = np.linalg.norm(arr, axis=1, keepdims=True)
            feature_blocks.append(l2_norm)
            out_names.append("res_l2_norm")

        # 5. Spatial aggregate: Mean absolute residual
        if self.config.include_mean_absolute:
            mean_abs = np.mean(np.abs(arr), axis=1, keepdims=True)
            feature_blocks.append(mean_abs)
            out_names.append("res_mean_absolute")

        # 6. Spatial aggregate: Maximum absolute residual
        if self.config.include_max_absolute:
            max_abs = np.max(np.abs(arr), axis=1, keepdims=True)
            feature_blocks.append(max_abs)
            out_names.append("res_max_absolute")

        # 7. Causal temporal lag features: r_{t-k}
        for k in self.config.lags:
            lag_arr = np.zeros_like(arr)
            if k < n_samples:
                # Shift backward: row t receives value from t-k
                lag_arr[k:] = arr[:-k]
            # Rows 0..k-1 retain 0.0 (unperturbed baseline prior to observation)
            feature_blocks.append(lag_arr)
            out_names.extend([f"{name}_lag_{k}" for name in base_names])

        if not feature_blocks:
            raise ValueError(
                "No residual features selected in ResidualFeatureConfig. "
                "At least one feature category must be enabled."
            )

        X_out = np.hstack(feature_blocks)

        if is_df:
            return pd.DataFrame(X_out, index=index, columns=out_names)
        return X_out
