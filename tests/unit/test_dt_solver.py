"""
tests/unit/test_dt_solver.py — Unit tests for OpenDSS Digital Twin solver and state object.
"""

import json

import numpy as np
import pytest

from src.digital_twin.solver import DigitalTwinSolver
from src.digital_twin.state import DigitalTwinState


@pytest.fixture
def dt_solver():
    """Create a default DigitalTwinSolver instance."""
    return DigitalTwinSolver()


def test_dt_solver_initial_solve(dt_solver):
    """Test initial baseline power flow solution."""
    state = dt_solver.solve(timestamp="2018-01-01T00:00:00Z")

    assert isinstance(state, DigitalTwinState)
    assert state.converged is True
    assert state.timestamp == "2018-01-01T00:00:00Z"
    assert len(state.bus_voltages_pu) == 33
    assert len(state.bus_voltages_kv) == 33
    assert len(state.bus_voltage_angles_deg) == 33
    assert len(state.branch_currents_a) == 32


def test_dt_state_feature_vector_and_json(dt_solver):
    """Verify feature vector dimensions (104 elements) and JSON serialization."""
    state = dt_solver.solve()
    feat_vec = state.to_feature_vector()

    # 33 voltages + 33 angles + 32 currents + 6 system totals = 104
    assert isinstance(feat_vec, np.ndarray)
    assert feat_vec.shape == (104,)
    assert not np.isnan(feat_vec).any()

    # JSON serialization
    json_str = state.to_json()
    parsed = json.loads(json_str)
    assert parsed["converged"] is True
    assert "bus_voltages_pu" in parsed


def test_dt_solver_load_multiplier(dt_solver):
    """Test scaling solver load multiplier."""
    state_nom = dt_solver.solve()
    dt_solver.set_load_multiplier(0.5)
    state_light = dt_solver.solve()

    assert state_light.converged is True
    # In light loading, total load is roughly half and voltages are higher
    assert state_light.total_load_p_kw < state_nom.total_load_p_kw
    assert state_light.min_voltage_pu > state_nom.min_voltage_pu


def test_dt_solver_individual_bus_load_update(dt_solver):
    """Test modifying a single bus load."""
    dt_solver.reset()
    state_orig = dt_solver.solve()
    orig_v = state_orig.bus_voltages_pu[18]

    # Spike load at bus 18 (e.g. from 90 kW to 900 kW)
    dt_solver.set_bus_load(18, p_kw=900.0, q_kvar=400.0)
    state_spiked = dt_solver.solve()

    assert state_spiked.converged is True
    assert state_spiked.bus_voltages_pu[18] < orig_v


def test_dt_solver_determinism(dt_solver):
    """Verify solver produces identical numerical states for fixed inputs."""
    dt_solver.reset()
    state1 = dt_solver.solve()
    dt_solver.reset()
    state2 = dt_solver.solve()

    assert state1.total_generation_p_kw == pytest.approx(state2.total_generation_p_kw, abs=1e-8)
    assert state1.min_voltage_pu == pytest.approx(state2.min_voltage_pu, abs=1e-8)
    assert state1.to_feature_vector() == pytest.approx(state2.to_feature_vector(), abs=1e-8)


def test_physical_feeder_load_distribution():
    """Assert feeder total physical active load follows expected distribution on full horizon."""
    import pandas as pd
    from pathlib import Path

    parquet_path = Path("data/processed/load_profiles.parquet")
    assert parquet_path.exists(), "Processed load profiles parquet must exist."
    df = pd.read_parquet(parquet_path)
    phys_p_cols = [c for c in df.columns if c.endswith("_p_kw_phys")]
    assert len(phys_p_cols) == 32, "Must contain 32 physical load bus columns."

    total_phys_p = df[phys_p_cols].sum(axis=1)
    p_05 = float(total_phys_p.quantile(0.05))
    p_95 = float(total_phys_p.quantile(0.95))

    # Distributional bounds: 5th percentile > 1000 kW, 95th percentile < 10000 kW
    assert p_05 >= 1000.0, f"5th percentile {p_05:.2f} kW below 1,000 kW"
    assert p_95 <= 10000.0, f"95th percentile {p_95:.2f} kW above 10,000 kW"
    assert (total_phys_p >= 0.0).all(), "Feeder load must be non-negative everywhere"


def test_full_horizon_convergence(dt_solver):
    """Assert OpenDSS power flow converges across all timesteps in the dataset."""
    import pandas as pd
    from pathlib import Path

    parquet_path = Path("data/processed/load_profiles.parquet")
    df = pd.read_parquet(parquet_path)

    # Solve across all 35,040 rows or representative strided steps ensuring 100% convergence
    # Here test a dense sample of 500 timesteps including extreme peak to keep test suite fast
    peak_idx = df[[c for c in df.columns if c.endswith("_p_kw_phys")]].sum(axis=1).idxmax()
    sample_indices = list(range(0, len(df), 70))
    sample_df = df.iloc[sample_indices].copy()
    if peak_idx not in sample_df.index:
        sample_df.loc[peak_idx] = df.loc[peak_idx]

    for ts, row in sample_df.iterrows():
        state = dt_solver.solve_timestep_from_dataframe(row)
        assert state.converged is True, f"Power flow failed to converge at {ts}"



def test_dt_solver_raises_on_missing_phys_columns(dt_solver):
    """(ii) Assert solver raises KeyError if *_phys columns are missing from the telemetry row."""
    import pandas as pd

    # Row containing only normalized features (missing *_phys columns)
    incomplete_row = pd.Series(
        {f"bus_{b}_p_kw": 0.5 for b in range(2, 34)}
        | {f"bus_{b}_q_kvar": 0.3 for b in range(2, 34)}
    )

    with pytest.raises(KeyError, match="Required physical load column"):
        dt_solver.solve_timestep_from_dataframe(incomplete_row)


def test_solved_voltages_show_realistic_drop(dt_solver):
    """(iii) Assert solved bus voltages show realistic physical drop along radial feeder."""
    import pandas as pd
    from pathlib import Path

    parquet_path = Path("data/processed/load_profiles.parquet")
    df = pd.read_parquet(parquet_path)

    # Solve median physical load timestep
    phys_p_cols = [c for c in df.columns if c.endswith("_p_kw_phys")]
    total_phys = df[phys_p_cols].sum(axis=1)
    med_ts = (total_phys - total_phys.median()).abs().idxmin()
    row = df.loc[med_ts]

    state = dt_solver.solve_timestep_from_dataframe(row)
    assert state.converged is True

    # Feeder head (bus 1) is slack bus at 1.0 pu
    # End of main feeder lateral (e.g. bus 18) experiences realistic distribution voltage drop
    v_bus1 = state.bus_voltages_pu[1]
    v_bus18 = state.bus_voltages_pu[18]

    assert v_bus1 == pytest.approx(1.0, abs=2e-3)
    assert 0.90 <= state.min_voltage_pu <= 0.96, (
        f"Realistic distribution voltage drop expected in [0.90, 0.96] pu, got {state.min_voltage_pu:.4f} pu"
    )
    assert state.min_voltage_pu < v_bus1, (
        f"Feeder end voltage ({state.min_voltage_pu:.4f} pu) must be lower than substation ({v_bus1:.4f} pu)"
    )

