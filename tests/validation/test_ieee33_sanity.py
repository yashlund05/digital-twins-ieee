"""
tests/validation/test_ieee33_sanity.py — Physical sanity validation of IEEE 33-bus Digital Twin.

Verifies:
1. Voltage profile limits: all 33 buses in [0.90, 1.10] pu under nominal conditions.
2. Radial feeder voltage drop profile (minimum voltage at Bus 18 per Baran & Wu 1989).
3. Active power loss magnitude matches benchmark (~202-210 kW).
4. Power balance conservation law: |P_gen - P_load - P_losses| < 0.5%.
5. Successful execution of Experiment E1 Baseline Validation suite.
"""

import pytest

from src.digital_twin.initializer import run_experiment_e1_validation
from src.digital_twin.solver import DigitalTwinSolver


@pytest.fixture(scope="module")
def nominal_state():
    """Solve nominal IEEE 33-bus power flow once for sanity verification."""
    solver = DigitalTwinSolver()
    return solver.solve()


def test_voltage_limits_pu(nominal_state):
    """Verify all 33 bus voltages remain strictly within standard [0.90, 1.10] pu range."""
    for bus_id, v_pu in nominal_state.bus_voltages_pu.items():
        assert 0.90 <= v_pu <= 1.10, (
            f"Bus {bus_id} voltage {v_pu:.4f} pu violates [0.90, 1.10] range"
        )


def test_minimum_voltage_bus18(nominal_state):
    """Verify the minimum voltage occurs at the distal branch termination (Bus 18)."""
    assert nominal_state.min_voltage_bus == 18
    # Baran & Wu (1989) reference voltage at bus 18 is ~0.913 pu
    assert nominal_state.min_voltage_pu == pytest.approx(0.9114, abs=0.01)


def test_system_losses_magnitude(nominal_state):
    """Verify active technical losses align with published benchmark (~200 kW)."""
    loss_p = nominal_state.total_losses_p_kw
    # Real losses should be between 180 kW and 230 kW
    assert 180.0 <= loss_p <= 230.0, f"Losses {loss_p:.2f} kW outside expected benchmark range"


def test_power_balance_conservation(nominal_state):
    """Verify first law of thermodynamics: P_gen = P_load + P_loss within 0.5% tolerance."""
    p_gen = nominal_state.total_generation_p_kw
    p_load = nominal_state.total_load_p_kw
    p_loss = nominal_state.total_losses_p_kw

    error_kw = abs(p_gen - (p_load + p_loss))
    error_pct = (error_kw / p_gen) * 100.0

    assert error_pct < 0.5, f"Power balance error {error_pct:.4f}% exceeds 0.5% threshold"
    assert nominal_state.power_balance_error_pct < 0.5


def test_experiment_e1_validation_execution(tmp_path):
    """Verify complete execution of Experiment E1 baseline validation."""
    result = run_experiment_e1_validation(output_root=tmp_path, seed=42)

    assert result["status"] == "success"
    assert result["all_passed"] is True
    assert (tmp_path / result["run_id"] / "manifest.json").exists()
    assert (tmp_path / result["run_id"] / "results" / "voltage_profile.csv").exists()
    assert (tmp_path / result["run_id"] / "results" / "power_flow.csv").exists()
    assert (tmp_path / result["run_id"] / "summary.md").exists()
