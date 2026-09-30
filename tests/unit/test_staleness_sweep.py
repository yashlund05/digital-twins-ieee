"""tests/unit/test_staleness_sweep.py — Comprehensive unit tests for Experiment E5.

Tests:
1. Delta t = 0 baseline synchronization semantics (continuous updates, zero staleness).
2. Correct synchronization schedule for Delta t = 1.
3. Correct synchronization schedule for Delta t = 5.
4. Correct synchronization schedule for Delta t = 15.
5. Correct synchronization schedule for Delta t = 60.
6. Correct synchronization schedule for Delta t = 300.
7. Packet drop prevents update and increments missed count.
8. Hold-last-state is maintained across missed/dropped steps.
9. AoI calculation grows linearly between updates and resets upon arrival.
10. t_sync <= t and AoI >= 0 strictly holds for every timestep.
11. No future state access (leakage isolation).
12. Deterministic drop decisions under identical random seed.
13. Seed-dependent stochasticity across different seeds.
"""

import numpy as np
import pandas as pd
import pytest

from src.experiments.staleness_sweep import (
    StalenessCondition,
    simulate_synchronization_trace,
)
from src.synchronization.aoi import AoITracker
from src.synchronization.policies import HoldLastStatePolicy
from src.synchronization.scheduler import UpdateScheduler


@pytest.fixture
def mock_telemetry_1000():
    """Generate 1000 steps of mock synthetic telemetry with clear linear drift."""
    steps = 1000
    features = [f"bus_{b}_p_kw" for b in range(2, 34)]
    # Linear drift to easily verify hold_last_state
    vals = np.arange(steps, dtype=np.float64)[:, np.newaxis] + np.arange(len(features))
    return pd.DataFrame(vals, columns=features)


def test_baseline_semantics_dt0(mock_telemetry_1000):
    """Test 1: Delta t = 0 produces continuous fresh synchronization at every step."""
    cond = StalenessCondition(staleness_seconds=0, packet_drop_rate=0.0, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    # Every update is scheduled and successful
    assert trace.aoi_statistics["scheduled_updates"] == 1000
    assert trace.aoi_statistics["successful_updates"] == 1000
    assert trace.aoi_statistics["dropped_updates"] == 0
    assert trace.aoi_statistics["mean_aoi"] == 0.0
    assert trace.aoi_statistics["max_aoi"] == 0.0
    # DT estimate exactly equals nominal telemetry
    np.testing.assert_allclose(trace.stale_estimate_df.values, mock_telemetry_1000.values)


def test_sync_schedule_dt1(mock_telemetry_1000):
    """Test 2: Delta t = 1 updates every single timestep."""
    cond = StalenessCondition(staleness_seconds=1, packet_drop_rate=0.0, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    assert trace.aoi_statistics["successful_updates"] == 1000
    assert trace.aoi_statistics["dropped_updates"] == 0
    assert trace.aoi_statistics["mean_aoi"] == 0.0


def test_sync_schedule_dt5(mock_telemetry_1000):
    """Test 3: Delta t = 5 updates every 5 timesteps."""
    cond = StalenessCondition(staleness_seconds=5, packet_drop_rate=0.0, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    # In 1000 steps (t=0 to 999), updates at 0, 5, 10, ..., 995 -> 200 updates
    assert trace.aoi_statistics["scheduled_updates"] == 200
    assert trace.aoi_statistics["successful_updates"] == 200
    assert trace.aoi_statistics["max_aoi"] == 4.0
    # Mean AoI for cycles (0, 1, 2, 3, 4) is exactly 2.0 s
    assert pytest.approx(trace.aoi_statistics["mean_aoi"], rel=1e-3) == 2.0


def test_sync_schedule_dt15(mock_telemetry_1000):
    """Test 4: Delta t = 15 updates every 15 timesteps."""
    cond = StalenessCondition(staleness_seconds=15, packet_drop_rate=0.0, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    # 1000 // 15 + 1 = 67 updates (t=0, 15, ..., 990)
    assert trace.aoi_statistics["scheduled_updates"] == 67
    assert trace.aoi_statistics["max_aoi"] == 14.0
    # Mean AoI is approx (14 * 15 / 2) / 15 = 7.0 s
    assert pytest.approx(trace.aoi_statistics["mean_aoi"], abs=0.2) == 7.0


def test_sync_schedule_dt60(mock_telemetry_1000):
    """Test 5: Delta t = 60 updates every 60 timesteps."""
    cond = StalenessCondition(staleness_seconds=60, packet_drop_rate=0.0, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    # 1000 // 60 + 1 = 17 updates (0, 60, 120, ..., 960)
    assert trace.aoi_statistics["scheduled_updates"] == 17
    assert trace.aoi_statistics["max_aoi"] == 59.0
    assert trace.aoi_statistics["mean_aoi"] > 25.0


def test_sync_schedule_dt300(mock_telemetry_1000):
    """Test 6: Delta t = 300 updates every 300 timesteps."""
    cond = StalenessCondition(staleness_seconds=300, packet_drop_rate=0.0, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    # updates at 0, 300, 600, 900 -> 4 updates
    assert trace.aoi_statistics["scheduled_updates"] == 4
    assert trace.aoi_statistics["max_aoi"] == 299.0
    assert trace.aoi_statistics["mean_aoi"] > 100.0


def test_packet_drop_prevents_update(mock_telemetry_1000):
    """Test 7: 100% packet drop rate prevents all scheduled updates after initial sync."""
    scheduler = UpdateScheduler(interval_seconds=15, missed_update_rate=1.0, seed=42)
    due_0, succ_0 = scheduler.check_update(current_time=0.0, last_sync_time=None)
    assert due_0 is True and succ_0 is False

    due_15, succ_15 = scheduler.check_update(current_time=15.0, last_sync_time=0.0)
    assert due_15 is True and succ_15 is False


def test_hold_last_state_maintained(mock_telemetry_1000):
    """Test 8: Verify DT retains last synchronized value across unupdated steps."""
    cond = StalenessCondition(staleness_seconds=10, packet_drop_rate=0.0, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    stale_vals = trace.stale_estimate_df.values
    # Step 0 synced: stale_vals[0] == mock[0]
    np.testing.assert_array_equal(stale_vals[0], mock_telemetry_1000.values[0])
    # Steps 1 to 9 must hold step 0
    for s in range(1, 10):
        np.testing.assert_array_equal(stale_vals[s], mock_telemetry_1000.values[0])
    # Step 10 updates
    np.testing.assert_array_equal(stale_vals[10], mock_telemetry_1000.values[10])


def test_aoi_monotonic_growth_between_updates():
    """Test 9: AoI increases linearly with slope 1 between updates and resets upon arrival."""
    aoi_tracker = AoITracker()
    aoi_0 = aoi_tracker.record_update(current_time=10.0, generation_time=10.0)
    assert aoi_0 == 0.0

    aoi_11 = aoi_tracker.evaluate_at(current_time=11.0)
    assert aoi_11 == 1.0

    aoi_15 = aoi_tracker.evaluate_at(current_time=15.0)
    assert aoi_15 == 5.0

    aoi_20 = aoi_tracker.record_update(current_time=20.0, generation_time=20.0)
    assert aoi_20 == 0.0


def test_tsync_le_t_and_aoi_nonnegative(mock_telemetry_1000):
    """Test 10: Strict invariant: t_sync <= t and AoI >= 0 across all conditions."""
    cond = StalenessCondition(staleness_seconds=60, packet_drop_rate=0.20, seed=42)
    trace = simulate_synchronization_trace(cond, mock_telemetry_1000)

    logs = trace.logs_df
    assert (logs["last_successful_sync"] <= logs["physical_timestamp"]).all()
    assert (logs["aoi_seconds"] >= 0.0).all()


def test_no_future_state_leakage(mock_telemetry_1000):
    """Test 11: Modifying future physical telemetry does not affect DT state at time t."""
    cond = StalenessCondition(staleness_seconds=15, packet_drop_rate=0.10, seed=42)

    df_original = mock_telemetry_1000.copy()
    trace_orig = simulate_synchronization_trace(cond, df_original)

    # Create mutated future copy starting at step 500
    df_mutated = mock_telemetry_1000.copy()
    df_mutated.iloc[500:] = df_mutated.iloc[500:] + 1e7
    trace_mut = simulate_synchronization_trace(cond, df_mutated)

    # For all steps t < 500, stale estimate and AoI must be bitwise identical
    np.testing.assert_array_equal(
        trace_orig.stale_estimate_df.values[:500],
        trace_mut.stale_estimate_df.values[:500],
    )
    np.testing.assert_array_equal(
        trace_orig.realized_aoi_array[:500],
        trace_mut.realized_aoi_array[:500],
    )


def test_deterministic_drop_sequence(mock_telemetry_1000):
    """Test 12: Same seed produces identical packet-drop decisions and AoI trace."""
    cond1 = StalenessCondition(staleness_seconds=15, packet_drop_rate=0.10, seed=42)
    cond2 = StalenessCondition(staleness_seconds=15, packet_drop_rate=0.10, seed=42)

    trace1 = simulate_synchronization_trace(cond1, mock_telemetry_1000)
    trace2 = simulate_synchronization_trace(cond2, mock_telemetry_1000)

    pd.testing.assert_frame_equal(trace1.logs_df, trace2.logs_df)
    np.testing.assert_array_equal(trace1.realized_aoi_array, trace2.realized_aoi_array)


def test_seed_dependent_stochasticity(mock_telemetry_1000):
    """Test 13: Different seeds expose distinct stochastic drop sequences."""
    cond1 = StalenessCondition(staleness_seconds=5, packet_drop_rate=0.20, seed=42)
    cond2 = StalenessCondition(staleness_seconds=5, packet_drop_rate=0.20, seed=999)

    trace1 = simulate_synchronization_trace(cond1, mock_telemetry_1000)
    trace2 = simulate_synchronization_trace(cond2, mock_telemetry_1000)

    # Realized drop decisions should differ between seed 42 and seed 999
    drops1 = trace1.logs_df["packet_dropped"].values
    drops2 = trace2.logs_df["packet_dropped"].values
    assert not np.array_equal(drops1, drops2)
