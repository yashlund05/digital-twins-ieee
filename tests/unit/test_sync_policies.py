"""
tests/unit/test_sync_policies.py — Unit tests for missed-update policies.
"""

import pytest

from src.digital_twin.solver import DigitalTwinSolver
from src.synchronization.policies import (
    HoldLastStatePolicy,
    LinearExtrapolationPolicy,
    ZeroInputPolicy,
    get_policy,
)


@pytest.fixture(scope="module")
def base_state():
    """Create a baseline converged DigitalTwinState using standard benchmark loads."""
    solver = DigitalTwinSolver()
    return solver.solve_timestep_from_dict({}, timestamp="2018-01-01T00:00:00Z")


@pytest.fixture(scope="module")
def heavy_state():
    """Create a heavier load state for trend extrapolation tests."""
    solver = DigitalTwinSolver()
    # Scale active loads by 1.5
    heavy_loads = {f"P_bus_{b}": 150.0 for b in range(2, 34)}
    return solver.solve_timestep_from_dict(heavy_loads, timestamp="2018-01-01T00:15:00Z")


def test_hold_last_state_policy(base_state):
    """Verify HoldLastStatePolicy preserves the exact state values."""
    policy = HoldLastStatePolicy()
    assert policy.name == "hold_last_state"

    stale_state = policy.apply(last_known_state=base_state)
    assert stale_state.bus_voltages_pu == base_state.bus_voltages_pu
    assert stale_state.total_load_p_kw == base_state.total_load_p_kw
    assert stale_state.branch_currents_a == base_state.branch_currents_a

    # Verify deep copy (modifications to stale copy do not leak into original)
    stale_state.bus_voltages_pu[1] = 0.5
    assert base_state.bus_voltages_pu[1] != 0.5


def test_linear_extrapolation_policy_without_prior(base_state):
    """Verify LinearExtrapolationPolicy gracefully degrades to hold if no prior state."""
    policy = LinearExtrapolationPolicy()
    assert policy.name == "linear_extrapolation"

    extrapolated = policy.apply(last_known_state=base_state, previous_state=None)
    assert extrapolated.bus_voltages_pu == base_state.bus_voltages_pu
    assert extrapolated.total_load_p_kw == base_state.total_load_p_kw


def test_linear_extrapolation_policy_with_prior(base_state, heavy_state):
    """Verify LinearExtrapolationPolicy projects forward electrical quantities."""
    policy = LinearExtrapolationPolicy()

    # Previous was base_state (lighter load, higher voltage), Current is heavy_state (heavier load, lower voltage)
    extrapolated = policy.apply(last_known_state=heavy_state, previous_state=base_state)

    # Bus 18 is at the feeder end, voltage should drop further under increasing load
    v_prev = base_state.bus_voltages_pu[18]
    v_curr = heavy_state.bus_voltages_pu[18]
    assert v_curr < v_prev  # Precondition: heavy load causes lower voltage

    v_extrap = extrapolated.bus_voltages_pu[18]
    # Projected voltage should be even lower than heavy_state
    assert v_extrap < v_curr
    assert pytest.approx(v_extrap, rel=1e-3) == (2 * v_curr - v_prev)

    # Total load should be extrapolated upwards
    assert extrapolated.total_load_p_kw > heavy_state.total_load_p_kw


def test_zero_input_policy(base_state):
    """Verify ZeroInputPolicy zeros out loads and resets voltages to 1.0 pu."""
    policy = ZeroInputPolicy()
    assert policy.name == "zero_input"

    zeroed = policy.apply(last_known_state=base_state)
    assert zeroed.total_load_p_kw == 0.0
    assert zeroed.total_load_q_kvar == 0.0
    assert zeroed.total_generation_p_kw == 0.0
    assert zeroed.bus_voltages_pu[1] == 1.0
    assert zeroed.bus_voltages_pu[18] == 1.0
    assert zeroed.branch_currents_a["L1"] == 0.0


def test_policy_factory():
    """Verify get_policy factory returns corresponding policy objects."""
    p1 = get_policy("hold_last_state")
    assert isinstance(p1, HoldLastStatePolicy)

    p2 = get_policy("linear_extrapolation")
    assert isinstance(p2, LinearExtrapolationPolicy)

    p3 = get_policy("zero_input")
    assert isinstance(p3, ZeroInputPolicy)

    with pytest.raises(ValueError, match="Unknown missed update policy"):
        get_policy("non_existent_policy")
