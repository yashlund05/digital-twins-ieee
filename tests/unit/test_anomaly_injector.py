"""
tests/unit/test_anomaly_injector.py — Unit tests for synthetic anomaly injection.
"""

import numpy as np
import pandas as pd
import pytest

from src.data.anomaly_injector import inject_synthetic_anomalies


@pytest.fixture
def mapped_load_data():
    """Create a 500-step test dataset for 4 buses."""
    timestamps = pd.date_range("2018-01-01", periods=500, freq="15min", tz="UTC")
    active = pd.DataFrame(
        {
            "bus_2_p_kw": np.full(500, 100.0),
            "bus_3_p_kw": np.full(500, 90.0),
            "bus_4_p_kw": np.full(500, 120.0),
            "bus_5_p_kw": np.full(500, 60.0),
        },
        index=timestamps,
    )
    reactive = active * 0.6
    reactive.columns = [col.replace("_p_kw", "_q_kvar") for col in active.columns]
    return active, reactive


def test_inject_synthetic_anomalies_rate_and_labels(mapped_load_data):
    """Test anomaly rate control and separate ground truth label creation."""
    active_df, reactive_df = mapped_load_data
    rate = 0.05
    duration = 4

    inj_p, inj_q, labels_df, events = inject_synthetic_anomalies(
        active_power_df=active_df,
        reactive_power_df=reactive_df,
        anomaly_rate=rate,
        duration_timesteps=duration,
        seed=42,
    )

    assert len(labels_df) == len(active_df)
    expected_cols = {
        "is_anomaly",
        "anomaly_type",
        "severity",
        "target_buses",
        "affected_buses",
        "realized_ratio_kw",
        "effect_size_sigma",
        "event_id",
    }
    assert expected_cols.issubset(set(labels_df.columns))

    actual_rate = float(labels_df["is_anomaly"].mean())
    # Should be close to 5%
    assert abs(actual_rate - rate) < 0.02
    assert len(events) > 0

    # Ensure anomalous steps have non-none labels and valid severity
    anom_rows = labels_df[labels_df["is_anomaly"] == 1]
    assert not (anom_rows["anomaly_type"] == "none").any()
    assert not (anom_rows["affected_buses"] == "none").any()
    assert set(anom_rows["severity"].unique()).issubset({"low", "medium", "high"})


def test_inject_synthetic_anomalies_fault_dynamics(mapped_load_data):
    """Test that load spikes increase power and load drops reduce power."""
    active_df, reactive_df = mapped_load_data

    # Test load spike
    inj_p_spike, _, _, events_spike = inject_synthetic_anomalies(
        active_power_df=active_df,
        reactive_power_df=reactive_df,
        anomaly_rate=0.08,
        fault_types=["load_spike"],
        seed=123,
    )

    for event in events_spike:
        assert event.fault_type == "load_spike"
        assert event.severity in ("low", "medium", "high")
        start, end = event.start_index, event.end_index
        for bus_id in event.target_buses:
            col = f"bus_{bus_id}_p_kw"
            baseline = active_df[col].iloc[start:end].to_numpy()
            spiked = inj_p_spike[col].iloc[start:end].to_numpy()
            assert np.all(spiked > baseline)

    # Test load drop
    inj_p_drop, _, _, events_drop = inject_synthetic_anomalies(
        active_power_df=active_df,
        reactive_power_df=reactive_df,
        anomaly_rate=0.08,
        fault_types=["load_drop"],
        seed=123,
    )

    for event in events_drop:
        assert event.fault_type == "load_drop"
        assert event.severity in ("low", "medium", "high")
        start, end = event.start_index, event.end_index
        for bus_id in event.target_buses:
            col = f"bus_{bus_id}_p_kw"
            baseline = active_df[col].iloc[start:end].to_numpy()
            dropped = inj_p_drop[col].iloc[start:end].to_numpy()
            assert np.all(dropped <= baseline)
            assert np.all(dropped >= 0.05)


def test_inject_synthetic_anomalies_reproducibility(mapped_load_data):
    """Test deterministic injection across runs with the same seed."""
    active_df, reactive_df = mapped_load_data

    p1, q1, l1, e1 = inject_synthetic_anomalies(active_df, reactive_df, seed=999)
    p2, q2, l2, e2 = inject_synthetic_anomalies(active_df, reactive_df, seed=999)

    pd.testing.assert_frame_equal(p1, p2)
    pd.testing.assert_frame_equal(q1, q2)
    pd.testing.assert_frame_equal(l1, l2)
    assert len(e1) == len(e2)
