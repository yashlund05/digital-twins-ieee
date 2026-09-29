"""
tests/unit/test_sync_engine.py — Unit tests for the SynchronizationEngine.
"""

import pytest

from src.digital_twin.solver import DigitalTwinSolver
from src.synchronization.engine import SynchronizationEngine
from src.utils.config import SynchronizationConfig


@pytest.fixture(scope="module")
def states_sequence():
    """Generate a 4-step sequence of evolving physical states."""
    solver = DigitalTwinSolver()
    seq = []
    for step in range(4):
        # Vary load over time
        loads = {f"P_bus_{b}": 100.0 + step * 25.0 for b in range(2, 34)}
        state = solver.solve_timestep_from_dict(
            loads, timestamp=f"2018-01-01T00:{step * 15:02d}:00Z"
        )
        seq.append(state)
    return seq


def test_sync_engine_perfect_sync(states_sequence):
    """Verify Level 0 (interval=0s) provides continuous fresh synchronization."""
    config = SynchronizationConfig(interval_seconds=0, missed_update_policy="hold_last_state")
    engine = SynchronizationEngine(config=config, run_id="test_l0")

    for i, state in enumerate(states_sequence):
        t = i * 15.0  # steps every 15s
        res = engine.step(physical_state=state, current_time=t)

        assert res.is_stale is False
        assert res.update_successful is True
        assert res.sync_age_seconds == 0.0
        assert res.aoi_seconds == 0.0
        assert res.policy_applied == "none"
        assert res.divergence.l2_norm_divergence < 1e-4

    assert len(engine.event_logger) == 4
    assert engine.missed_updates_count == 0


def test_sync_engine_controlled_staleness(states_sequence):
    """Verify Level 3 (interval=60s) holds state between 15s steps."""
    config = SynchronizationConfig(interval_seconds=60, missed_update_policy="hold_last_state")
    engine = SynchronizationEngine(config=config, run_id="test_l3")

    # Step 0: t=0s -> Initial sync (fresh)
    res0 = engine.step(physical_state=states_sequence[0], current_time=0.0)
    assert res0.is_stale is False
    assert res0.sync_age_seconds == 0.0
    assert res0.aoi_seconds == 0.0

    # Step 1: t=15s -> Not due yet (stale, hold_last_state)
    res1 = engine.step(physical_state=states_sequence[1], current_time=15.0)
    assert res1.is_stale is True
    assert res1.sync_age_seconds == 15.0
    assert res1.aoi_seconds == 15.0
    assert res1.policy_applied == "hold_last_state"
    assert res1.divergence.l2_norm_divergence > 0.0  # Diverged because physical load increased

    # Step 2: t=30s -> Still not due (stale)
    res2 = engine.step(physical_state=states_sequence[2], current_time=30.0)
    assert res2.is_stale is True
    assert res2.sync_age_seconds == 30.0
    assert res2.aoi_seconds == 30.0

    # Step 3: t=60s -> Interval elapsed (fresh update applied)
    res3 = engine.step(physical_state=states_sequence[3], current_time=60.0)
    assert res3.is_stale is False
    assert res3.sync_age_seconds == 0.0
    assert res3.aoi_seconds == 0.0
    assert res3.update_successful is True
    assert res3.divergence.l2_norm_divergence < 1e-4


def test_sync_engine_stochastic_packet_drop(states_sequence):
    """Verify stochastic packet drop (Exp E7) increments missed updates and marks stale."""
    config = SynchronizationConfig(interval_seconds=15, missed_update_policy="hold_last_state")
    # 100% drop rate after first step to ensure drop behavior
    engine = SynchronizationEngine(
        config=config,
        run_id="test_drop",
        missed_update_rate=1.0,
    )

    # Step 0: t=0s -> first sync
    res0 = engine.step(physical_state=states_sequence[0], current_time=0.0)
    assert res0.update_successful is False  # Dropped due to 100% drop rate
    assert engine.missed_updates_count == 1

    # Step 1: t=15s
    res1 = engine.step(physical_state=states_sequence[1], current_time=15.0)
    assert res1.update_successful is False
    assert engine.missed_updates_count == 2
    assert res1.is_stale is True


def test_sync_engine_logging_and_export(states_sequence, tmp_path):
    """Verify log recording, DataFrame conversion, and file export."""
    config = SynchronizationConfig(interval_seconds=30)
    engine = SynchronizationEngine(config=config, run_id="test_export")

    for i, state in enumerate(states_sequence):
        engine.step(physical_state=state, current_time=float(i * 15))

    df = engine.get_logs_dataframe()
    assert len(df) == 4
    expected_cols = [
        "event_id",
        "run_id",
        "physical_timestamp",
        "dt_timestamp",
        "last_sync_timestamp",
        "sync_age_seconds",
        "aoi_seconds",
        "update_interval_seconds",
        "update_successful",
        "missed_updates_count",
        "residual_magnitude",
        "policy_applied",
    ]
    for col in expected_cols:
        assert col in df.columns

    # Test CSV and JSONL persistence
    csv_file = tmp_path / "sync_logs.csv"
    jsonl_file = tmp_path / "sync_logs.jsonl"
    engine.save_logs(csv_file)
    engine.save_logs(jsonl_file)

    assert csv_file.exists()
    assert jsonl_file.exists()
    assert csv_file.stat().st_size > 0
    assert jsonl_file.stat().st_size > 0

    # Summary statistics
    summary = engine.event_logger.get_summary_statistics()
    assert summary["total_events"] == 4.0
    assert summary["max_sync_age_seconds"] >= 15.0


def test_sync_engine_reset(states_sequence):
    """Verify engine reset restores clean state."""
    config = SynchronizationConfig(interval_seconds=60)
    engine = SynchronizationEngine(config=config)

    engine.step(physical_state=states_sequence[0], current_time=0.0)
    engine.step(physical_state=states_sequence[1], current_time=15.0)
    assert len(engine.event_logger) == 2

    engine.reset()
    assert len(engine.event_logger) == 0
    assert engine.current_aoi == 0.0
    assert engine.sync_age == 0.0
    assert engine.missed_updates_count == 0
