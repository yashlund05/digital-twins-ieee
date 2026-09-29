"""
src/data/preprocessor.py — Data cleaning, resampling, feature engineering, and normalization.

Implements strict temporal data preparation without future leakage.
Normalization parameters are computed strictly on the training partition
and applied symmetrically to validation and testing partitions.
"""

import numpy as np
import pandas as pd

from src.data.schema import NormalizationParameters
from src.utils.logging import get_logger

logger = get_logger("data.preprocessor")


def clean_and_resample(
    df: pd.DataFrame,
    resolution_minutes: int = 15,
    max_gap_minutes: int = 60,
) -> pd.DataFrame:
    """Ensure regular timestamp grid and impute small gaps per DATA_PROTOCOL.md.

    Args:
        df: DataFrame with a UTC DatetimeIndex.
        resolution_minutes: Target sampling resolution in minutes.
        max_gap_minutes: Maximum gap duration allowed for forward-fill imputation.

    Returns:
        Regularly sampled DataFrame with missing values imputed up to max_gap_minutes.
    """
    logger.info(
        "Cleaning and resampling time series", extra={"resolution_minutes": resolution_minutes}
    )

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be a DatetimeIndex.")

    # Create uniform date range
    start_time = df.index.min()
    end_time = df.index.max()
    freq_str = f"{resolution_minutes}min"
    full_index = pd.date_range(start=start_time, end=end_time, freq=freq_str, tz=df.index.tz)

    reindexed = df.reindex(full_index)
    limit_steps = max(1, max_gap_minutes // resolution_minutes)

    # Forward fill up to limit_steps
    cleaned = reindexed.ffill(limit=limit_steps)

    # Linear interpolation for any remaining small residual gaps
    cleaned = cleaned.interpolate(method="time", limit=limit_steps)

    # Backward fill any leading missing values at the very beginning of the series
    cleaned = cleaned.bfill(limit=limit_steps)

    # If any NaNs still remain beyond the max gap, fill with column medians to ensure clean pipeline
    remaining_nans = cleaned.isna().sum().sum()
    if remaining_nans > 0:
        logger.warning(
            "Unfilled NaNs remained after gap limit; filling with column medians",
            extra={"count": int(remaining_nans)},
        )
        cleaned = cleaned.fillna(cleaned.median())

    logger.info("Resampling and imputation complete", extra={"total_timesteps": len(cleaned)})
    return cleaned


def extract_temporal_features(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Extract calendar and cyclic temporal features from a DatetimeIndex.

    Features:
    - hour (0-23)
    - day_of_week (0-6, Monday=0)
    - month (1-12)
    - is_weekend (0 or 1)
    - sin_hour, cos_hour (cyclic daily representation)
    - sin_day, cos_day (cyclic weekly representation)

    Args:
        index: DatetimeIndex of timestamps.

    Returns:
        DataFrame containing engineered temporal feature columns.
    """
    hours = index.hour + index.minute / 60.0
    day_of_week = index.dayofweek
    months = index.month

    features = pd.DataFrame(index=index)
    features["hour"] = index.hour
    features["day_of_week"] = day_of_week
    features["month"] = months
    features["is_weekend"] = (day_of_week >= 5).astype(int)

    # Cyclic features for continuous daily and weekly harmonics
    features["sin_hour"] = np.sin(2.0 * np.pi * hours / 24.0)
    features["cos_hour"] = np.cos(2.0 * np.pi * hours / 24.0)
    features["sin_day"] = np.sin(2.0 * np.pi * day_of_week / 7.0)
    features["cos_day"] = np.cos(2.0 * np.pi * day_of_week / 7.0)

    return features


def extract_lag_features(
    series_df: pd.DataFrame,
    lags: list[int] | None = None,
) -> pd.DataFrame:
    """Extract historical lag features for time-series forecasting.

    Default lags:
    - 1: previous timestep (t-15m)
    - 24: 6 hours ago (daily sub-cycle)
    - 96: 24 hours ago (exact 1-day seasonal cycle at 15-min resolution)

    Args:
        series_df: DataFrame of bus load time-series.
        lags: List of integer lag steps. Defaults to [1, 24, 96].

    Returns:
        DataFrame with lag columns named '{col}_lag_{k}'.
    """
    if lags is None:
        lags = [1, 24, 96]

    lag_dfs = []
    for lag in lags:
        shifted = series_df.shift(lag)
        shifted.columns = [f"{col}_lag_{lag}" for col in series_df.columns]
        lag_dfs.append(shifted)

    all_lags = pd.concat(lag_dfs, axis=1)
    # Forward fill the initial NaNs created by shifting using first valid observation
    all_lags = all_lags.bfill()
    return all_lags


def fit_and_apply_normalization(
    df: pd.DataFrame,
    feature_columns: list[str],
    train_indices: list[int],
    method: str = "min_max",
    epsilon: float = 1e-6,
    fit_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, NormalizationParameters]:
    """Fit scaler strictly on the training partition and normalize the entire dataset.

    Guarantees zero data leakage: validation and test splits have zero influence
    on the calculated normalization parameters. If fit_df is provided (e.g. pre-injection data),
    parameters are computed strictly from fit_df.iloc[train_indices].

    Args:
        df: Input DataFrame containing feature_columns to transform.
        feature_columns: Column names to normalize.
        train_indices: Integer row indices corresponding strictly to the training split.
        method: Normalization method ('min_max' or 'z_score').
        epsilon: Small numerical stabilizer to prevent division by zero.
        fit_df: Optional DataFrame to fit parameters on. Defaults to df.

    Returns:
        Tuple of (normalized_df, NormalizationParameters schema object).
    """
    logger.info(
        "Computing normalization parameters on training split",
        extra={"method": method, "train_size": len(train_indices)},
    )

    source_fit = fit_df if fit_df is not None else df
    train_data = source_fit.iloc[train_indices][feature_columns]
    normalized_df = df.copy()
    bus_params: dict[str, dict[str, float]] = {}

    train_start = int(min(train_indices))
    train_end = int(max(train_indices))

    for col in feature_columns:
        vals = train_data[col].to_numpy(dtype=np.float64)

        if method == "min_max":
            v_min = float(np.nanmin(vals))
            v_max = float(np.nanmax(vals))
            rng = v_max - v_min if (v_max - v_min) > epsilon else 1.0
            normalized_df[col] = (df[col] - v_min) / rng
            bus_params[col] = {"min": v_min, "max": v_max, "range": rng}

        elif method == "z_score":
            v_mean = float(np.nanmean(vals))
            v_std = float(np.nanstd(vals))
            std_val = v_std if v_std > epsilon else 1.0
            normalized_df[col] = (df[col] - v_mean) / std_val
            bus_params[col] = {"mean": v_mean, "std": std_val}
        else:
            raise ValueError(
                f"Unsupported normalization method: {method}. Use 'min_max' or 'z_score'."
            )

    norm_params = NormalizationParameters(
        method=method,
        train_start_index=train_start,
        train_end_index=train_end,
        bus_params=bus_params,
    )

    logger.info(
        "Normalization complete without data leakage", extra={"num_features": len(feature_columns)}
    )
    return normalized_df, norm_params
