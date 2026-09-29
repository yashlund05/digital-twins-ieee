"""
tests/integration/test_dt_pipeline.py — Integration test connecting Phase 2 data to Phase 3 DT.
"""

from pathlib import Path

import pytest

from src.digital_twin.solver import DigitalTwinSolver
from src.utils.io import load_parquet


@pytest.fixture(scope="module")
def processed_profiles():
    """Load sample of processed load profiles from Phase 2."""
    data_path = Path("data/processed/load_profiles.parquet")
    if not data_path.exists():
        pytest.skip("Processed profiles parquet not found in data/processed/")
    df = load_parquet(data_path)
    # Return first 24 timesteps (6 hours of 15-minute grid operation)
    return df.iloc[:24]


def test_dt_playback_with_processed_profiles(processed_profiles):
    """Verify OpenDSS solver stably executes playback on continuous Phase 2 load traces."""
    solver = DigitalTwinSolver()
    states = []

    for _idx, (timestamp, row) in enumerate(processed_profiles.iterrows()):
        state = solver.solve_timestep_from_dataframe(row, timestamp=str(timestamp))
        states.append(state)

        assert state.converged is True
        assert state.power_balance_error_pct < 0.5
        # Voltages should remain within safe distribution feeder bounds
        assert state.min_voltage_pu >= 0.88
        assert state.max_voltage_pu <= 1.05

    assert len(states) == 24
    # Ensure voltage trajectory varies with changing residential demand
    min_v_trajectory = [s.min_voltage_pu for s in states]
    assert len(set(min_v_trajectory)) > 1, "Voltage trajectory should vary with time-varying load"
