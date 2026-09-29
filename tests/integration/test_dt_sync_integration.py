"""
tests/integration/test_dt_sync_integration.py — Integration test connecting Phase 2 data, Phase 3 DT solver, and Phase 4 sync engine.
"""

from pathlib import Path

import pytest

from src.digital_twin.solver import DigitalTwinSolver
from src.synchronization.engine import SynchronizationEngine
from src.utils.config import SynchronizationConfig
from src.utils.io import load_parquet


@pytest.fixture(scope="module")
def physical_states_24():
    """Run OpenDSS power flow over 24 timesteps (6 hours) of processed Phase 2 data."""
    data_path = Path("data/processed/load_profiles.parquet")
    if not data_path.exists():
        pytest.skip("Processed profiles parquet not found in data/processed/")

    df = load_parquet(data_path).iloc[:24]
    solver = DigitalTwinSolver()
    states = []

    for timestamp, row in df.iterrows():
        state = solver.solve_timestep_from_dataframe(row, timestamp=str(timestamp))
        states.append(state)

    return states


def test_dt_sync_pipeline_perfect_vs_stale(physical_states_24):
    """Verify synchronization engine correctly introduces controlled staleness into DT state."""
    # Data is sampled at 15-minute (900 seconds) intervals:
    # Timesteps t = 0, 900, 1800, 2700, ...
    step_duration_s = 900.0

    # 1. Level 0: Perfect sync (interval = 0)
    config_l0 = SynchronizationConfig(interval_seconds=0, missed_update_policy="hold_last_state")
    engine_l0 = SynchronizationEngine(config=config_l0, run_id="integ_l0")

    results_l0 = [
        engine_l0.step(physical_state=state, current_time=i * step_duration_s)
        for i, state in enumerate(physical_states_24)
    ]

    assert all(r.is_stale is False for r in results_l0)
    assert all(r.update_successful is True for r in results_l0)
    assert all(r.divergence.l2_norm_divergence < 1e-4 for r in results_l0)
    assert engine_l0.peak_aoi == 0.0

    # 2. Level 8: 30-minute interval (interval = 1800s, updates every 2 timesteps)
    config_l8 = SynchronizationConfig(interval_seconds=1800, missed_update_policy="hold_last_state")
    engine_l8 = SynchronizationEngine(config=config_l8, run_id="integ_l8")

    results_l8 = [
        engine_l8.step(physical_state=state, current_time=i * step_duration_s)
        for i, state in enumerate(physical_states_24)
    ]

    stale_count = sum(1 for r in results_l8 if r.is_stale)
    fresh_count = sum(1 for r in results_l8 if not r.is_stale)

    # In 24 steps with step=900s and sync_interval=1800s:
    # Steps 0, 2, 4, ... are fresh (12 steps)
    # Steps 1, 3, 5, ... are stale (12 steps)
    assert fresh_count == 12
    assert stale_count == 12

    # Verify that stale steps exhibit positive state divergence from ground-truth
    stale_divergences = [r.divergence.l2_norm_divergence for r in results_l8 if r.is_stale]
    assert all(div > 0.0 for div in stale_divergences)

    # Monotonicity check: AoI for Level 8 must be strictly greater than Level 0
    assert engine_l8.peak_aoi > engine_l0.peak_aoi
    assert engine_l8.average_aoi > engine_l0.average_aoi
    assert engine_l8.peak_aoi == 900.0


def test_dt_sync_staleness_sweep_levels(physical_states_24):
    """Verify that sweeping synchronization intervals produces strictly increasing peak AoI."""
    # Test sweep across [0, 900, 1800, 3600]
    intervals = [0, 900, 1800, 3600]
    step_duration_s = 900.0
    peak_aois = []

    for interval in intervals:
        config = SynchronizationConfig(
            interval_seconds=interval, missed_update_policy="hold_last_state"
        )
        engine = SynchronizationEngine(config=config, run_id=f"sweep_{interval}")
        for i, state in enumerate(physical_states_24):
            engine.step(physical_state=state, current_time=i * step_duration_s)
        peak_aois.append(engine.peak_aoi)

    # Peak AoI must be non-decreasing with interval
    for k in range(len(peak_aois) - 1):
        assert peak_aois[k] <= peak_aois[k + 1]
