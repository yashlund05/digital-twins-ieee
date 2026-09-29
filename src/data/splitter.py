"""
src/data/splitter.py — Strict temporal dataset splitting.

Partitions time-series data chronologically into training (70%), validation (15%),
and test (15%) splits without shuffling.
Enforces zero temporal leakage per DATA_PROTOCOL.md research integrity requirements.
"""

import pandas as pd

from src.data.schema import TemporalSplitIndices
from src.utils.logging import get_logger

logger = get_logger("data.splitter")


def compute_temporal_splits(
    total_timesteps: int,
    train_ratio: float = 0.70,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> TemporalSplitIndices:
    """Compute strictly chronological indices for train, validation, and test sets.

    Guarantees:
    - Zero future leakage: max(train) < min(val) and max(val) < min(test).
    - No random shuffling.
    - Continuous time blocks.

    Args:
        total_timesteps: Total number of observations in the time series.
        train_ratio: Fraction for training split (default: 0.70).
        validation_ratio: Fraction for validation split (default: 0.15).
        test_ratio: Fraction for testing split (default: 0.15).

    Returns:
        TemporalSplitIndices schema containing the verified split indices.

    Raises:
        ValueError: If ratios do not sum to 1.0 or if total_timesteps is insufficient.
    """
    total_ratio = train_ratio + validation_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-5:
        raise ValueError(f"Split ratios must sum to 1.0, got: {total_ratio:.4f}")

    if total_timesteps < 10:
        raise ValueError(
            f"Insufficient timesteps ({total_timesteps}) for three-way temporal split."
        )

    n_train = int(total_timesteps * train_ratio)
    n_val = int(total_timesteps * validation_ratio)
    n_test = total_timesteps - n_train - n_val

    if n_train <= 0 or n_val <= 0 or n_test <= 0:
        raise ValueError("Calculated split sizes must all be strictly positive.")

    train_indices = list(range(0, n_train))
    val_indices = list(range(n_train, n_train + n_val))
    test_indices = list(range(n_train + n_val, total_timesteps))

    splits = TemporalSplitIndices(
        train_indices=train_indices,
        validation_indices=val_indices,
        test_indices=test_indices,
        temporal=True,
        leak_free=True,
    )

    logger.info(
        "Computed temporal splits successfully",
        extra={
            "train_size": len(train_indices),
            "val_size": len(val_indices),
            "test_size": len(test_indices),
            "total": total_timesteps,
        },
    )

    return splits


def get_split_date_ranges(
    timestamps: pd.DatetimeIndex,
    splits: TemporalSplitIndices,
) -> dict[str, dict[str, str]]:
    """Return human-readable ISO date ranges for each temporal split partition.

    Args:
        timestamps: Full DatetimeIndex of the dataset.
        splits: Computed split indices.

    Returns:
        Dictionary mapping partition name to start and end ISO timestamp strings.
    """
    return {
        "train": {
            "start": timestamps[splits.train_indices[0]].isoformat(),
            "end": timestamps[splits.train_indices[-1]].isoformat(),
            "count": str(len(splits.train_indices)),
        },
        "validation": {
            "start": timestamps[splits.validation_indices[0]].isoformat(),
            "end": timestamps[splits.validation_indices[-1]].isoformat(),
            "count": str(len(splits.validation_indices)),
        },
        "test": {
            "start": timestamps[splits.test_indices[0]].isoformat(),
            "end": timestamps[splits.test_indices[-1]].isoformat(),
            "count": str(len(splits.test_indices)),
        },
    }
