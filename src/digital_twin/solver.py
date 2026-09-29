"""
src/digital_twin/solver.py — OpenDSS power flow solver wrapper for the IEEE 33-bus feeder.

Encapsulates circuit initialization, dynamic load setting, AC power flow solving,
state telemetry extraction, and power balance validation.
"""

import numpy as np
import opendssdirect as dss
import pandas as pd

from src.digital_twin.state import DigitalTwinState
from src.digital_twin.topology import (
    BASE_KV,
    IEEE_33_LOADS,
    generate_dss_circuit_commands,
)
from src.utils.logging import get_logger

logger = get_logger("digital_twin.solver")


class DigitalTwinSolver:
    """OpenDSS-based Digital Twin solver for the IEEE 33-bus radial distribution network."""

    def __init__(
        self,
        base_kv: float = BASE_KV,
        max_iterations: int = 100,
        tolerance: float = 0.0001,
        custom_loads: dict[int, tuple[float, float]] | None = None,
    ) -> None:
        """Initialize the Digital Twin OpenDSS solver.

        Args:
            base_kv: Feeder base line-to-line voltage in kV.
            max_iterations: Maximum iterations for AC power flow solver.
            tolerance: Convergence tolerance.
            custom_loads: Optional custom bus loads dictionary.
        """
        self.base_kv = base_kv
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.custom_loads = custom_loads
        self._initialize_circuit()

    def _initialize_circuit(self, load_multiplier: float = 1.0) -> None:
        """Execute OpenDSS circuit initialization commands in memory."""
        commands = generate_dss_circuit_commands(
            load_multiplier=load_multiplier,
            custom_loads=self.custom_loads,
            base_kv=self.base_kv,
        )
        for cmd in commands:
            dss.Text.Command(cmd)

        dss.Text.Command(f"Set Maxiterations={self.max_iterations}")
        dss.Text.Command(f"Set Tolerance={self.tolerance}")
        logger.info("OpenDSS IEEE 33-bus circuit initialized", extra={"base_kv": self.base_kv})

    def set_load_multiplier(self, multiplier: float) -> None:
        """Scale all bus loads uniformly by a multiplier (e.g. 0.5 light, 1.5 heavy).

        Args:
            multiplier: Uniform scaling multiplier.
        """
        dss.Text.Command(f"Set LoadMult={multiplier:.4f}")

    def set_bus_load(self, bus_id: int, p_kw: float, q_kvar: float) -> None:
        """Update active and reactive load at a specific load bus.

        Args:
            bus_id: IEEE 33 bus number (2 to 33).
            p_kw: Active power demand in kW.
            q_kvar: Reactive power demand in kVAR.
        """
        if bus_id < 2 or bus_id > 33:
            raise ValueError(f"Invalid load bus ID: {bus_id}. Must be between 2 and 33.")

        dss.Loads.Name(f"Load{bus_id}")
        dss.Loads.kW(max(0.001, float(p_kw)))
        dss.Loads.kvar(float(q_kvar))

    def set_all_loads(self, loads_dict: dict[int, tuple[float, float]]) -> None:
        """Batch update active and reactive loads across all load buses.

        Args:
            loads_dict: Mapping bus_id -> (P_kW, Q_kVAR).
        """
        for bus_id, (p_kw, q_kvar) in loads_dict.items():
            self.set_bus_load(bus_id, p_kw, q_kvar)

    def solve(self, timestamp: str | None = None) -> DigitalTwinState:
        """Solve AC power flow and extract comprehensive feeder state telemetry.

        Args:
            timestamp: Optional ISO 8601 timestamp string for this state snapshot.

        Returns:
            DigitalTwinState schema containing complete physical telemetry.

        Raises:
            RuntimeError: If OpenDSS fails to solve power flow.
        """
        dss.Text.Command("Solve")
        converged = bool(dss.Solution.Converged())
        iterations = int(dss.Solution.Iterations())

        if not converged:
            logger.error("OpenDSS power flow failed to converge", extra={"iterations": iterations})
            raise RuntimeError(
                f"OpenDSS power flow did not converge after {iterations} iterations."
            )

        # Extract per-bus voltages and angles
        bus_voltages_pu: dict[int, float] = {}
        bus_voltages_kv: dict[int, float] = {}
        bus_voltage_angles_deg: dict[int, float] = {}

        for b_name in dss.Circuit.AllBusNames():
            b_id = int(b_name)
            dss.Circuit.SetActiveBus(b_name)
            v_mag_ang = dss.Bus.puVmagAngle()
            bus_voltages_pu[b_id] = float(v_mag_ang[0])
            bus_voltage_angles_deg[b_id] = float(v_mag_ang[1])
            # Line-to-line kV = line-to-neutral * sqrt(3)
            kv_ll = float(dss.Bus.VMagAngle()[0] / 1000.0 * np.sqrt(3))
            bus_voltages_kv[b_id] = kv_ll

        # Extract branch current magnitudes (A)
        branch_currents_a: dict[str, float] = {}
        has_line = dss.Lines.First()
        while has_line > 0:
            l_name = dss.Lines.Name().upper()
            currents = dss.CktElement.CurrentsMagAng()[:6:2]
            branch_currents_a[l_name] = float(currents[0])
            has_line = dss.Lines.Next()

        # Extract system power import and losses
        total_gen = dss.Circuit.TotalPower()
        gen_p = float(-total_gen[0])
        gen_q = float(-total_gen[1])

        losses = dss.Circuit.Losses()
        loss_p = float(losses[0] / 1000.0)
        loss_q = float(losses[1] / 1000.0)

        # Calculate actual consumed load power
        total_load_p = 0.0
        total_load_q = 0.0
        has_load = dss.Loads.First()
        while has_load > 0:
            powers = dss.CktElement.Powers()
            total_load_p += sum(powers[:6:2])
            total_load_q += sum(powers[1:6:2])
            has_load = dss.Loads.Next()

        # Compute power balance error
        balance_err_kw = abs(gen_p - (total_load_p + loss_p))
        balance_err_pct = (balance_err_kw / gen_p * 100.0) if gen_p > 0 else 0.0

        # Min and Max voltages
        v_items = [(b, v) for b, v in bus_voltages_pu.items()]
        min_b, min_v = min(v_items, key=lambda x: x[1])
        max_b, max_v = max(v_items, key=lambda x: x[1])

        state = DigitalTwinState(
            timestamp=timestamp,
            converged=converged,
            iterations=iterations,
            bus_voltages_pu=bus_voltages_pu,
            bus_voltages_kv=bus_voltages_kv,
            bus_voltage_angles_deg=bus_voltage_angles_deg,
            branch_currents_a=branch_currents_a,
            total_generation_p_kw=gen_p,
            total_generation_q_kvar=gen_q,
            total_load_p_kw=total_load_p,
            total_load_q_kvar=total_load_q,
            total_losses_p_kw=loss_p,
            total_losses_q_kvar=loss_q,
            power_balance_error_kw=balance_err_kw,
            power_balance_error_pct=balance_err_pct,
            min_voltage_pu=min_v,
            min_voltage_bus=min_b,
            max_voltage_pu=max_v,
            max_voltage_bus=max_b,
        )

        return state

    def solve_timestep_from_dataframe(
        self,
        row: pd.Series,
        timestamp: str | None = None,
    ) -> DigitalTwinState:
        """Solve power flow for a single row from the Phase 2 load_profiles DataFrame.

        Reads exclusively the physical columns ('bus_{id}_p_kw_phys' and 'bus_{id}_q_kvar_phys').
        Does NOT fall back to benchmark defaults; raises KeyError if physical columns are missing.

        Args:
            row: Pandas Series containing 'bus_{id}_p_kw_phys' and 'bus_{id}_q_kvar_phys' columns.
            timestamp: Timestamp identifier for state.

        Returns:
            DigitalTwinState telemetry snapshot.

        Raises:
            KeyError: If any required physical column is missing from row.
        """
        loads: dict[int, tuple[float, float]] = {}
        for bus_id in range(2, 34):
            p_col = f"bus_{bus_id}_p_kw_phys"
            q_col = f"bus_{bus_id}_q_kvar_phys"
            if p_col not in row or q_col not in row:
                raise KeyError(
                    f"Required physical load column '{p_col}' or '{q_col}' not found in telemetry row. "
                    "DigitalTwinSolver requires explicit unnormalized physical loads (*_phys)."
                )
            p_val = float(row[p_col])
            q_val = float(row[q_col])
            loads[bus_id] = (p_val, q_val)

        self.set_all_loads(loads)
        ts_str = timestamp or (str(row.name) if hasattr(row, "name") else None)
        return self.solve(timestamp=ts_str)

    def solve_timestep_from_dict(
        self,
        loads: dict[int, tuple[float, float]] | dict[str, float],
        timestamp: str | None = None,
    ) -> DigitalTwinState:
        """Solve power flow from a dictionary of bus loads.

        Args:
            loads: Mapping of either bus_id -> (P_kW, Q_kVAR) or 'P_bus_{id}' / 'bus_{id}_p_kw' -> float.
            timestamp: Timestamp identifier for state.

        Returns:
            DigitalTwinState telemetry snapshot.
        """
        parsed_loads: dict[int, tuple[float, float]] = {}
        for bus_id in range(2, 34):
            if bus_id in loads and isinstance(loads[bus_id], (tuple, list)):
                parsed_loads[bus_id] = (float(loads[bus_id][0]), float(loads[bus_id][1]))
            else:
                p_val = loads.get(
                    f"P_bus_{bus_id}", loads.get(f"bus_{bus_id}_p_kw", IEEE_33_LOADS[bus_id][0])
                )
                q_val = loads.get(
                    f"Q_bus_{bus_id}", loads.get(f"bus_{bus_id}_q_kvar", IEEE_33_LOADS[bus_id][1])
                )
                parsed_loads[bus_id] = (float(p_val), float(q_val))

        self.set_all_loads(parsed_loads)
        return self.solve(timestamp=timestamp)

    def reset(self) -> None:
        """Reset the solver circuit to default nominal baseline."""
        self._initialize_circuit()
