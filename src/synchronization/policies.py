"""
src/synchronization/policies.py — Missed-update policies for the Digital Twin.

Defines strategies for updating or holding the Digital Twin state when a physical
measurement packet is delayed or missed due to synchronization staleness or communication failure.
Policies include:
    - hold_last_state: DT freezes the last successfully received physical state (default).
    - linear_extrapolation: DT estimates the next state via finite-difference extrapolation.
    - zero_input: DT resets load inputs to zero (stress-testing baseline).
"""

from abc import ABC, abstractmethod

import numpy as np

from src.digital_twin.state import DigitalTwinState
from src.utils.logging import get_logger

logger = get_logger("synchronization.policies")


class MissedUpdatePolicy(ABC):
    """Abstract base class for missed synchronization update policies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique identifier for this policy."""
        ...

    @abstractmethod
    def apply(
        self,
        last_known_state: DigitalTwinState,
        previous_state: DigitalTwinState | None = None,
        dt_seconds: float = 0.0,
    ) -> DigitalTwinState:
        """Produce a DigitalTwinState when a synchronization update is missed.

        Args:
            last_known_state: The most recent successfully synchronized state.
            previous_state: The state preceding last_known_state (used for rate-of-change).
            dt_seconds: Time elapsed since the last synchronization in seconds.

        Returns:
            The state to be maintained in the Digital Twin.
        """
        ...


class HoldLastStatePolicy(MissedUpdatePolicy):
    """Holds the last successfully synchronized state.

    This represents the standard zero-order hold (ZOH) behavior where the Digital
    Twin makes no assumptions about physical grid evolution between sync events.
    """

    @property
    def name(self) -> str:
        return "hold_last_state"

    def apply(
        self,
        last_known_state: DigitalTwinState,
        previous_state: DigitalTwinState | None = None,
        dt_seconds: float = 0.0,
    ) -> DigitalTwinState:
        """Return a copy of the last known state."""
        return last_known_state.model_copy(deep=True)


class LinearExtrapolationPolicy(MissedUpdatePolicy):
    """Linearly extrapolates electrical quantities from the previous two states.

    Computes finite-difference rate of change:
        x_extrapolated = x_{t-1} + (x_{t-1} - x_{t-2})
    Enforces physical feasibility clamping (voltages within [0.5, 1.5] pu, currents >= 0).
    Falls back to HoldLastStatePolicy if previous_state is not available.
    """

    @property
    def name(self) -> str:
        return "linear_extrapolation"

    def apply(
        self,
        last_known_state: DigitalTwinState,
        previous_state: DigitalTwinState | None = None,
        dt_seconds: float = 0.0,
    ) -> DigitalTwinState:
        """Apply first-order linear extrapolation to the Digital Twin state."""
        if previous_state is None:
            return last_known_state.model_copy(deep=True)

        extrapolated_dict = last_known_state.model_dump()

        # 1. Extrapolate bus voltages (pu)
        for bus_id in last_known_state.bus_voltages_pu:
            v_curr = last_known_state.bus_voltages_pu[bus_id]
            v_prev = previous_state.bus_voltages_pu.get(bus_id, v_curr)
            delta_v = v_curr - v_prev
            extrapolated_v = float(np.clip(v_curr + delta_v, 0.5, 1.5))
            extrapolated_dict["bus_voltages_pu"][bus_id] = extrapolated_v

            # Scale kV accordingly
            kv_curr = last_known_state.bus_voltages_kv[bus_id]
            if v_curr > 0:
                extrapolated_dict["bus_voltages_kv"][bus_id] = float(
                    kv_curr * (extrapolated_v / v_curr)
                )

        # 2. Extrapolate angles
        for bus_id in last_known_state.bus_voltage_angles_deg:
            ang_curr = last_known_state.bus_voltage_angles_deg[bus_id]
            ang_prev = previous_state.bus_voltage_angles_deg.get(bus_id, ang_curr)
            delta_ang = ang_curr - ang_prev
            extrapolated_dict["bus_voltage_angles_deg"][bus_id] = float(ang_curr + delta_ang)

        # 3. Extrapolate line currents
        for line_id in last_known_state.branch_currents_a:
            i_curr = last_known_state.branch_currents_a[line_id]
            i_prev = previous_state.branch_currents_a.get(line_id, i_curr)
            delta_i = i_curr - i_prev
            extrapolated_dict["branch_currents_a"][line_id] = float(max(0.0, i_curr + delta_i))

        # 4. Extrapolate system power totals
        p_load_curr = last_known_state.total_load_p_kw
        p_load_prev = previous_state.total_load_p_kw
        extrapolated_dict["total_load_p_kw"] = float(
            max(0.0, p_load_curr + (p_load_curr - p_load_prev))
        )

        q_load_curr = last_known_state.total_load_q_kvar
        q_load_prev = previous_state.total_load_q_kvar
        extrapolated_dict["total_load_q_kvar"] = float(q_load_curr + (q_load_curr - q_load_prev))

        # Recalculate summary metrics
        pu_vals = list(extrapolated_dict["bus_voltages_pu"].values())
        min_v = float(min(pu_vals))
        max_v = float(max(pu_vals))
        extrapolated_dict["min_voltage_pu"] = min_v
        extrapolated_dict["max_voltage_pu"] = max_v

        return DigitalTwinState(**extrapolated_dict)


class ZeroInputPolicy(MissedUpdatePolicy):
    """Sets active and reactive loads to zero, retaining nominal voltages.

    This policy models a severe dropout condition where unreceived input is assumed dead.
    """

    @property
    def name(self) -> str:
        return "zero_input"

    def apply(
        self,
        last_known_state: DigitalTwinState,
        previous_state: DigitalTwinState | None = None,
        dt_seconds: float = 0.0,
    ) -> DigitalTwinState:
        """Produce zero-input state."""
        state_dict = last_known_state.model_dump()
        state_dict["total_load_p_kw"] = 0.0
        state_dict["total_load_q_kvar"] = 0.0
        state_dict["total_losses_p_kw"] = 0.0
        state_dict["total_losses_q_kvar"] = 0.0
        state_dict["total_generation_p_kw"] = 0.0
        state_dict["total_generation_q_kvar"] = 0.0
        state_dict["power_balance_error_kw"] = 0.0
        state_dict["power_balance_error_pct"] = 0.0

        for bus_id in state_dict["bus_voltages_pu"]:
            state_dict["bus_voltages_pu"][bus_id] = 1.0
        for line_id in state_dict["branch_currents_a"]:
            state_dict["branch_currents_a"][line_id] = 0.0

        return DigitalTwinState(**state_dict)


def get_policy(policy_name: str) -> MissedUpdatePolicy:
    """Factory function to instantiate a missed update policy by name.

    Args:
        policy_name: Name of the policy ('hold_last_state', 'linear_extrapolation', 'zero_input').

    Returns:
        Instance of MissedUpdatePolicy.

    Raises:
        ValueError: If policy_name is unrecognized.
    """
    normalized = policy_name.lower().strip()
    if normalized == "hold_last_state":
        return HoldLastStatePolicy()
    elif normalized == "linear_extrapolation":
        return LinearExtrapolationPolicy()
    elif normalized == "zero_input":
        return ZeroInputPolicy()
    else:
        raise ValueError(
            f"Unknown missed update policy: '{policy_name}'. Valid options: "
            "['hold_last_state', 'linear_extrapolation', 'zero_input']"
        )
