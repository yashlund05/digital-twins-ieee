"""
tests/unit/test_splitter.py — Unit tests for temporal data splitting and leakage prevention.
"""

import pandas as pd
import pytest

from src.data.splitter import compute_temporal_splits, get_split_date_ranges


def test_compute_temporal_splits_ratios():
    """Verify split sizes match 70/15/15 configuration."""
    total_steps = 1000
    splits = compute_temporal_splits(
        total_timesteps=total_steps,
        train_ratio=0.70,
        validation_ratio=0.15,
        test_ratio=0.15,
    )

    assert len(splits.train_indices) == 700
    assert len(splits.validation_indices) == 150
    assert len(splits.test_indices) == 150
    assert (
        len(splits.train_indices) + len(splits.validation_indices) + len(splits.test_indices)
        == total_steps
    )


def test_zero_temporal_leakage():
    """Enforce non-negotiable temporal ordering: train < validation < test."""
    total_steps = 2000
    splits = compute_temporal_splits(total_steps)

    max_train = max(splits.train_indices)
    min_val = min(splits.validation_indices)
    max_val = max(splits.validation_indices)
    min_test = min(splits.test_indices)

    assert max_train < min_val, f"Leakage: max train ({max_train}) >= min val ({min_val})"
    assert max_val < min_test, f"Leakage: max val ({max_val}) >= min test ({min_test})"

    # Verify partitions are completely disjoint
    set_train = set(splits.train_indices)
    set_val = set(splits.validation_indices)
    set_test = set(splits.test_indices)

    assert len(set_train.intersection(set_val)) == 0
    assert len(set_val.intersection(set_test)) == 0
    assert len(set_train.intersection(set_test)) == 0


def test_invalid_ratios_raise_error():
    """Verify that split ratios not summing to 1.0 are rejected."""
    with pytest.raises(ValueError, match="must sum to 1.0"):
        compute_temporal_splits(100, train_ratio=0.6, validation_ratio=0.2, test_ratio=0.1)


def test_split_date_ranges():
    """Test date range extraction for each split."""
    timestamps = pd.date_range("2018-01-01", periods=100, freq="15min", tz="UTC")
    splits = compute_temporal_splits(100)
    ranges = get_split_date_ranges(timestamps, splits)

    assert "train" in ranges and "validation" in ranges and "test" in ranges
    assert pd.to_datetime(ranges["train"]["end"]) < pd.to_datetime(ranges["validation"]["start"])
    assert pd.to_datetime(ranges["validation"]["end"]) < pd.to_datetime(ranges["test"]["start"])
