"""
tests/unit/test_degradation.py — Unit tests for degradation metrics and directions.
"""

import numpy as np
import pandas as pd
import pytest

from src.statistics.degradation import (
    METRIC_DIRECTION,
    build_degradation_dataframe,
    compute_absolute_degradation,
    compute_normalized_degradation,
    compute_relative_degradation,
    get_metric_direction,
)


def test_metric_direction_registry():
    """Verify registry correctly identifies directions for key metrics."""
    assert get_metric_direction("f1") == "higher_better"
    assert get_metric_direction("pr_auc") == "higher_better"
    assert get_metric_direction("roc_auc") == "higher_better"
    assert get_metric_direction("precision") == "higher_better"
    assert get_metric_direction("recall") == "higher_better"

    assert get_metric_direction("mae") == "lower_better"
    assert get_metric_direction("rmse") == "lower_better"
    assert get_metric_direction("mape") == "lower_better"
    assert get_metric_direction("fpr") == "lower_better"
    assert get_metric_direction("detection_latency") == "lower_better"

    with pytest.raises(ValueError):
        get_metric_direction("non_existent_metric")


def test_identical_performance_zero_degradation():
    """When observed equals baseline, degradation must be exactly zero."""
    for m in ["f1", "pr_auc", "mae", "rmse", "mape", "fpr"]:
        val = 0.85
        assert compute_absolute_degradation(val, val, m) == 0.0
        assert compute_relative_degradation(val, val, m) == 0.0
        assert compute_normalized_degradation(val, val, m) == 0.0


def test_higher_is_better_metric_degradation():
    """For higher-is-better metrics (e.g. F1), performance decrease is positive degradation."""
    baseline = 0.90
    observed = 0.45  # 50% drop
    abs_d = compute_absolute_degradation(observed, baseline, "f1")
    rel_d = compute_relative_degradation(observed, baseline, "f1")

    assert np.isclose(abs_d, 0.45)
    assert np.isclose(rel_d, 0.50)


def test_lower_is_better_metric_degradation():
    """For lower-is-better metrics (e.g. MAE), error increase is positive degradation."""
    baseline = 10.0
    observed = 25.0  # 150% increase
    abs_d = compute_absolute_degradation(observed, baseline, "mae")
    rel_d = compute_relative_degradation(observed, baseline, "mae")

    assert np.isclose(abs_d, 15.0)
    assert np.isclose(rel_d, 1.50)


def test_zero_baseline_protection():
    """Floor protection epsilon prevents division by zero without raising exception."""
    baseline = 0.0
    observed = 5.0
    rel_d = compute_relative_degradation(observed, baseline, "mae", epsilon=1e-6)
    assert np.isfinite(rel_d)
    assert rel_d > 0


def test_build_degradation_dataframe():
    """Verify conversion of comparison DataFrame into directional degradation table."""
    data = [
        {
            "condition_id": "C01",
            "staleness_seconds": 0,
            "packet_drop_rate": 0.0,
            "task": "anomaly_detection",
            "model": "lstm_autoencoder",
            "representation": "residual",
            "metric": "f1",
            "value": 0.90,
            "baseline_value": 0.90,
        },
        {
            "condition_id": "C02",
            "staleness_seconds": 60,
            "packet_drop_rate": 0.0,
            "task": "anomaly_detection",
            "model": "lstm_autoencoder",
            "representation": "residual",
            "metric": "f1",
            "value": 0.45,
            "baseline_value": 0.90,
        },
        {
            "condition_id": "C01",
            "staleness_seconds": 0,
            "packet_drop_rate": 0.0,
            "task": "load_estimation",
            "model": "lstm",
            "representation": "raw",
            "metric": "mape",
            "value": 10.0,
            "baseline_value": 10.0,
        },
        {
            "condition_id": "C02",
            "staleness_seconds": 60,
            "packet_drop_rate": 0.0,
            "task": "load_estimation",
            "model": "lstm",
            "representation": "raw",
            "metric": "mape",
            "value": 20.0,
            "baseline_value": 10.0,
        },
    ]
    df = pd.DataFrame(data)
    out_df = build_degradation_dataframe(df)

    assert "normalized_degradation" in out_df.columns
    assert "absolute_degradation" in out_df.columns
    assert "metric_direction" in out_df.columns

    # C01 should have 0 degradation
    assert out_df.iloc[0]["normalized_degradation"] == 0.0
    assert out_df.iloc[2]["normalized_degradation"] == 0.0

    # C02 AD: 0.90 -> 0.45 => norm deg = 0.5
    assert np.isclose(out_df.iloc[1]["normalized_degradation"], 0.5)
    # C02 LE: 10 -> 20 => norm deg = 1.0
    assert np.isclose(out_df.iloc[3]["normalized_degradation"], 1.0)
