"""
src/digital_twin/state.py — Digital Twin state representation.

Defines the state data structure representing the virtual physical state
of the IEEE 33-bus feeder at any discrete time instance.
Serializes to JSON and provides feature vector exports for downstream ML tasks.
"""

import json

import numpy as np
from pydantic import BaseModel, Field


class DigitalTwinState(BaseModel):
    """Complete snapshot of the IEEE 33-bus Digital Twin state."""

    timestamp: str | None = Field(default=None, description="ISO 8601 UTC timestamp")
    converged: bool = Field(..., description="Whether OpenDSS power flow converged")
    iterations: int = Field(default=1, ge=1, description="Number of solver iterations")

    # Nodal electrical quantities (buses 1 to 33)
    bus_voltages_pu: dict[int, float] = Field(
        ..., description="Positive-sequence voltage magnitude per bus in per-unit (pu)"
    )
    bus_voltages_kv: dict[int, float] = Field(
        ..., description="Voltage magnitude per bus in kV (line-to-neutral or line-to-line)"
    )
    bus_voltage_angles_deg: dict[int, float] = Field(
        ..., description="Voltage phase angle per bus in degrees"
    )

    # Branch electrical quantities (lines L1 to L32)
    branch_currents_a: dict[str, float] = Field(
        ..., description="Current magnitude per distribution line in Amperes"
    )

    # System-level power quantities (kW, kVAR)
    total_generation_p_kw: float = Field(
        ..., description="Total active power supplied by slack bus (kW)"
    )
    total_generation_q_kvar: float = Field(
        ..., description="Total reactive power supplied by slack bus (kVAR)"
    )
    total_load_p_kw: float = Field(
        ..., description="Total active load consumed across all load buses (kW)"
    )
    total_load_q_kvar: float = Field(
        ..., description="Total reactive load consumed across all load buses (kVAR)"
    )
    total_losses_p_kw: float = Field(..., description="Total technical active power losses (kW)")
    total_losses_q_kvar: float = Field(
        ..., description="Total technical reactive power losses (kVAR)"
    )

    # Physical validation metrics
    power_balance_error_kw: float = Field(..., description="|P_gen - P_load - P_loss| in kW")
    power_balance_error_pct: float = Field(
        ..., description="Power balance error as percentage of P_gen"
    )
    min_voltage_pu: float = Field(..., description="Minimum bus voltage magnitude in pu")
    min_voltage_bus: int = Field(..., description="Bus ID where minimum voltage occurs")
    max_voltage_pu: float = Field(..., description="Maximum bus voltage magnitude in pu")
    max_voltage_bus: int = Field(..., description="Bus ID where maximum voltage occurs")

    def to_feature_vector(self) -> np.ndarray:
        """Flatten state into a 1D numerical array for ML model inputs and residual calculation.

        Vector layout:
        - 33 bus voltages (pu): Bus 1..33
        - 33 bus voltage angles (deg): Bus 1..33
        - 32 branch currents (A): L1..L32
        - Total power and losses: [gen_p, gen_q, load_p, load_q, loss_p, loss_q]

        Returns:
            1D numpy float64 array of shape (104,).
        """
        voltages = [self.bus_voltages_pu[b] for b in range(1, 34)]
        angles = [self.bus_voltage_angles_deg[b] for b in range(1, 34)]
        currents = [self.branch_currents_a[f"L{i}"] for i in range(1, 33)]
        globals_vec = [
            self.total_generation_p_kw,
            self.total_generation_q_kvar,
            self.total_load_p_kw,
            self.total_load_q_kvar,
            self.total_losses_p_kw,
            self.total_losses_q_kvar,
        ]
        return np.array(voltages + angles + currents + globals_vec, dtype=np.float64)

    def to_json(self, indent: int | None = None) -> str:
        """Serialize state object to JSON string."""
        return json.dumps(self.model_dump(), indent=indent)
