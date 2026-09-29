"""
src/forecasting/features.py — Feature engineering and dataset preparation for forecasting.

Constructs strictly leak-free tabular feature matrices (for XGBoost / Persistence)
and 3D temporal tensors (for LSTM) from the processed load profiles.
Enforces that every prediction at timestep t only uses information available at <= t-1.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logging import get_logger

logger = get_logger("forecasting.features")


@dataclass
class ForecastingDataSplits:
    """Container holding partitioned train, validation, and test datasets."""

    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    feature_names: list[str]
    train_timestamps: pd.DatetimeIndex
    val_timestamps: pd.DatetimeIndex
    test_timestamps: pd.DatetimeIndex


def compute_target_series(df: pd.DataFrame, target_name: str = "total_load_p_kw") -> pd.Series:
    """Extract or compute the forecast target load series from the load profiles DataFrame.

    If target_name is 'total_load_p_kw', sums all 32 active power bus columns.
    Otherwise, extracts the specified column.

    Args:
        df: Processed load profiles DataFrame.
        target_name: Target identifier.

    Returns:
        1D pandas Series of load values.
    """
    if target_name == "total_load_p_kw":
        if "total_load_p_kw" in df.columns:
            return df["total_load_p_kw"].copy()
        p_cols = [
            c for c in df.columns if c.startswith("bus_") and c.endswith("_p_kw") and "lag" not in c
        ]
        if not p_cols:
            raise ValueError("No bus active power columns found to compute total_load_p_kw.")
        return df[p_cols].sum(axis=1).rename("total_load_p_kw")
    elif target_name in df.columns:
        return df[target_name].copy()
    else:
        raise KeyError(f"Target column '{target_name}' not found in DataFrame columns.")


def create_tabular_features(
    df: pd.DataFrame,
    target_series: pd.Series,
    lookback_steps: int = 24,
) -> tuple[pd.DataFrame, pd.Series]:
    """Generate tabular feature matrix X and target y for regression models (XGBoost, Persistence).

    Features generated:
    - Autoregressive lag values: lag_1 to lag_lookback
    - Rolling window statistics: rolling mean, rolling std over lookback window
    - Calendar/temporal features: hour, day_of_week, month, is_weekend, sin/cos cyclics
    - Lag-1 of aggregate system load

    Args:
        df: Input processed DataFrame containing calendar features.
        target_series: The target series y to be forecasted.
        lookback_steps: Number of prior steps to use as lags.

    Returns:
        Tuple of (feature_df, aligned_target_series) with NaNs trimmed from start.
    """
    feats = pd.DataFrame(index=df.index)

    # 1. Autoregressive lags (t-1, t-2, ..., t-lookback)
    for lag in range(1, lookback_steps + 1):
        feats[f"lag_{lag}"] = target_series.shift(lag)

    # 2. Rolling statistics (strictly over past values, shifted by 1 to prevent leakage)
    past_series = target_series.shift(1)
    feats["rolling_mean_6"] = past_series.rolling(min(6, lookback_steps)).mean()
    feats["rolling_mean_24"] = past_series.rolling(min(24, lookback_steps)).mean()
    feats["rolling_std_24"] = past_series.rolling(min(24, lookback_steps)).std().fillna(0.0)

    # 3. Calendar & cyclic features (available at inference time without lag)
    calendar_cols = [
        "hour",
        "day_of_week",
        "month",
        "is_weekend",
        "sin_hour",
        "cos_hour",
        "sin_day",
        "cos_day",
    ]
    for col in calendar_cols:
        if col in df.columns:
            feats[col] = df[col].astype(float)

    # Align and drop leading NaN rows due to lookback window
    valid_mask = ~feats.isna().any(axis=1) & ~target_series.isna()
    return feats[valid_mask], target_series[valid_mask]


def create_sequence_tensors(
    features_df: pd.DataFrame,
    target_series: pd.Series,
    lookback_steps: int = 24,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Create 3D sequence tensors (N, lookback_steps, features) for recurrent models (LSTM).

    Args:
        features_df: Tabular feature matrix.
        target_series: Target values.
        lookback_steps: Temporal window length per sample.

    Returns:
        Tuple of (X_sequences, y_targets, feature_names).
    """
    feat_names = list(features_df.columns)
    feat_mat = features_df.values
    targ_vec = target_series.values

    n_samples = len(features_df) - lookback_steps + 1
    if n_samples <= 0:
        raise ValueError(
            f"Not enough samples ({len(features_df)}) for lookback_steps ({lookback_steps})"
        )

    X_seq = np.empty((n_samples, lookback_steps, feat_mat.shape[1]), dtype=np.float32)
    y_seq = np.empty(n_samples, dtype=np.float32)

    for i in range(n_samples):
        X_seq[i] = feat_mat[i : i + lookback_steps]
        y_seq[i] = targ_vec[i + lookback_steps - 1]

    return X_seq, y_seq, feat_names


def prepare_forecasting_data(
    df: pd.DataFrame,
    splits: dict[str, Any],
    lookback_steps: int = 24,
    target_name: str = "total_load_p_kw",
    mode: str = "tabular",
) -> ForecastingDataSplits:
    """Prepare clean, strictly partitioned forecasting datasets according to splits.json.

    Args:
        df: Processed load profiles DataFrame.
        splits: Loaded dictionary from data/processed/splits.json.
        lookback_steps: Lookback context window.
        target_name: Target column name or 'total_load_p_kw'.
        mode: 'tabular' for 2D arrays (XGBoost, Persistence) or 'sequence' for 3D tensors (LSTM).

    Returns:
        ForecastingDataSplits object.
    """
    target = compute_target_series(df, target_name)
    feats, aligned_target = create_tabular_features(df, target, lookback_steps=lookback_steps)

    def _extract_split_index(raw_indices: list[Any]) -> list[Any]:
        if not raw_indices:
            return []
        first = raw_indices[0]
        if isinstance(first, (int, np.integer)):
            # Positional integer indices: map through df.index
            ts_list = [df.index[pos] for pos in raw_indices if pos < len(df)]
            return [ts for ts in ts_list if ts in feats.index]
        else:
            return [ts for ts in raw_indices if ts in feats.index]

    train_idx = _extract_split_index(splits["train_indices"])
    val_idx = _extract_split_index(splits["validation_indices"])
    test_idx = _extract_split_index(splits["test_indices"])

    if mode == "tabular":
        X_train = feats.loc[train_idx].values.astype(np.float32)
        y_train = aligned_target.loc[train_idx].values.astype(np.float32)

        X_val = feats.loc[val_idx].values.astype(np.float32)
        y_val = aligned_target.loc[val_idx].values.astype(np.float32)

        X_test = feats.loc[test_idx].values.astype(np.float32)
        y_test = aligned_target.loc[test_idx].values.astype(np.float32)
        feat_names = list(feats.columns)

    elif mode == "sequence":
        # For sequence mode, compute rolling slices within each partition to prevent cross-boundary leakage
        X_train, y_train, feat_names = create_sequence_tensors(
            feats.loc[train_idx], aligned_target.loc[train_idx], lookback_steps=lookback_steps
        )
        X_val, y_val, _ = create_sequence_tensors(
            feats.loc[val_idx], aligned_target.loc[val_idx], lookback_steps=lookback_steps
        )
        X_test, y_test, _ = create_sequence_tensors(
            feats.loc[test_idx], aligned_target.loc[test_idx], lookback_steps=lookback_steps
        )
        # Shift index to match valid output samples
        train_idx = train_idx[lookback_steps - 1 :]
        val_idx = val_idx[lookback_steps - 1 :]
        test_idx = test_idx[lookback_steps - 1 :]
    else:
        raise ValueError(f"Unknown dataset mode: '{mode}'. Expected 'tabular' or 'sequence'.")

    return ForecastingDataSplits(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        feature_names=feat_names,
        train_timestamps=pd.DatetimeIndex(train_idx),
        val_timestamps=pd.DatetimeIndex(val_idx),
        test_timestamps=pd.DatetimeIndex(test_idx),
    )
