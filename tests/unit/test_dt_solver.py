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
