"""
digital_twin — Digital Twin Engine.

Provides the OpenDSS-based Digital Twin implementation for the IEEE 33-bus
distribution feeder. Manages the virtual representation of the physical grid.

NOTE: This module contains NO synchronization logic. All synchronization is handled
by the synchronization module (src/synchronization/).
"""

from src.digital_twin.initializer import (
    initialize_digital_twin,
    run_experiment_e1_validation,
)
from src.digital_twin.solver import DigitalTwinSolver
from src.digital_twin.state import DigitalTwinState
from src.digital_twin.topology import (
    BASE_KV,
    IEEE_33_BRANCHES,
    IEEE_33_LOADS,
    FeederTopology,
    export_dss_file,
    generate_dss_circuit_commands,
)

__all__ = [
    "BASE_KV",
    "IEEE_33_BRANCHES",
    "IEEE_33_LOADS",
    "FeederTopology",
    "generate_dss_circuit_commands",
    "export_dss_file",
    "DigitalTwinState",
    "DigitalTwinSolver",
    "initialize_digital_twin",
    "run_experiment_e1_validation",
]
