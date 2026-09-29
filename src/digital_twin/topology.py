"""
src/digital_twin/topology.py — IEEE 33-bus distribution feeder topology definition.

Implements the standard Baran & Wu (1989) radial benchmark feeder:
- 33 buses (Bus 1 is the slack bus, Buses 2-33 are load buses)
- 32 branches with positive-sequence line impedances (R, X in Ohms)
- Nominal voltage: 12.66 kV line-to-line
- Total nominal active load: 3,715 kW; reactive load: 2,300 kVAR

Provides OpenDSS script generation and topology verification routines.
"""

from dataclasses import dataclass
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger("digital_twin.topology")

BASE_KV: float = 12.66

# Baran & Wu (1989) benchmark branch data: (from_bus, to_bus, R_ohms, X_ohms)
IEEE_33_BRANCHES: list[tuple[int, int, float, float]] = [
    (1, 2, 0.0922, 0.0470),
    (2, 3, 0.4930, 0.2511),
    (3, 4, 0.3660, 0.1864),
    (4, 5, 0.3811, 0.1941),
    (5, 6, 0.8190, 0.7070),
    (6, 7, 0.1872, 0.6188),
    (7, 8, 0.7114, 0.2351),
    (8, 9, 1.0300, 0.7400),
    (9, 10, 1.0440, 0.7400),
    (10, 11, 0.1966, 0.0650),
    (11, 12, 0.3744, 0.1238),
    (12, 13, 1.4680, 1.1550),
    (13, 14, 0.5416, 0.7129),
    (14, 15, 0.5910, 0.5260),
    (15, 16, 0.7463, 0.5450),
    (16, 17, 1.2890, 1.7210),
    (17, 18, 0.7320, 0.5740),
    (2, 19, 0.1640, 0.1565),
    (19, 20, 1.5042, 1.3554),
    (20, 21, 0.4095, 0.4784),
    (21, 22, 0.7089, 0.9373),
    (3, 23, 0.4512, 0.3083),
    (23, 24, 0.8980, 0.7091),
    (24, 25, 0.8960, 0.7011),
    (6, 26, 0.2030, 0.1034),
    (26, 27, 0.2842, 0.1447),
    (27, 28, 1.0590, 0.9337),
    (28, 29, 0.8042, 0.7006),
    (29, 30, 0.5075, 0.2585),
    (30, 31, 0.9744, 0.9630),
    (31, 32, 0.3105, 0.3619),
    (32, 33, 0.3410, 0.5302),
]

# Baran & Wu (1989) benchmark nominal bus loads: bus_id -> (P_nominal_kW, Q_nominal_kVAR)
IEEE_33_LOADS: dict[int, tuple[float, float]] = {
    2: (100.0, 60.0),
    3: (90.0, 40.0),
    4: (120.0, 80.0),
    5: (60.0, 30.0),
    6: (60.0, 20.0),
    7: (200.0, 100.0),
    8: (200.0, 100.0),
    9: (60.0, 20.0),
    10: (60.0, 20.0),
    11: (45.0, 30.0),
    12: (60.0, 35.0),
    13: (60.0, 35.0),
    14: (120.0, 80.0),
    15: (60.0, 10.0),
    16: (60.0, 20.0),
    17: (60.0, 20.0),
    18: (90.0, 40.0),
    19: (90.0, 40.0),
    20: (90.0, 40.0),
    21: (90.0, 40.0),
    22: (90.0, 40.0),
    23: (90.0, 50.0),
    24: (420.0, 200.0),
    25: (420.0, 200.0),
    26: (60.0, 25.0),
    27: (60.0, 25.0),
    28: (60.0, 20.0),
    29: (120.0, 70.0),
    30: (200.0, 600.0),
    31: (150.0, 70.0),
    32: (210.0, 100.0),
    33: (60.0, 40.0),
}


@dataclass(frozen=True)
class FeederTopology:
    """Immutable data structure defining the feeder topology."""

    name: str = "IEEE33Bus"
    base_kv: float = BASE_KV
    num_buses: int = 33
    num_branches: int = 32
    slack_bus: int = 1
    branches: tuple = tuple(IEEE_33_BRANCHES)
    nominal_loads: tuple = tuple(IEEE_33_LOADS.items())


def generate_dss_circuit_commands(
    load_multiplier: float = 1.0,
    custom_loads: dict[int, tuple[float, float]] | None = None,
    base_kv: float = BASE_KV,
) -> list[str]:
    """Generate the sequence of OpenDSS text commands to construct the IEEE 33-bus circuit.

    Args:
        load_multiplier: Uniform scaling multiplier for all loads (e.g., 0.5 for light, 1.5 for heavy).
        custom_loads: Optional dictionary overriding loads per bus: bus_id -> (kW, kVAR).
        base_kv: Feeder base line-to-line voltage in kV.

    Returns:
        List of OpenDSS script command strings.
    """
    commands: list[str] = [
        "Clear",
        f"New Circuit.IEEE33Bus basekv={base_kv} phases=3 pu=1.00 bus1=1",
    ]

    # Add all 32 distribution lines
    for i, (f_bus, t_bus, r, x) in enumerate(IEEE_33_BRANCHES, 1):
        commands.append(
            f"New Line.L{i} Phases=3 Bus1={f_bus} Bus2={t_bus} R1={r} X1={x} Length=1 Units=none"
        )

    # Determine loads
    loads_to_apply = custom_loads if custom_loads is not None else IEEE_33_LOADS

    # Add all loads at load buses
    for bus_id in range(2, 34):
        p_kw, q_kvar = loads_to_apply.get(bus_id, (0.0, 0.0))
        p_eff = p_kw * load_multiplier
        q_eff = q_kvar * load_multiplier
        commands.append(
            f"New Load.Load{bus_id} Bus1={bus_id} Phases=3 kV={base_kv} kW={p_eff:.4f} kvar={q_eff:.4f} Model=1 Vminpu=0.85"
        )

    # Setup voltage bases and solution parameters
    commands.extend(
        [
            f"Set VoltageBases=[{base_kv}]",
            "CalcVoltageBases",
            "Set Maxiterations=100",
            "Set Tolerance=0.0001",
        ]
    )

    return commands


def export_dss_file(
    output_path: Path | str,
    load_multiplier: float = 1.0,
    custom_loads: dict[int, tuple[float, float]] | None = None,
) -> Path:
    """Export the IEEE 33-bus circuit commands to a standalone OpenDSS (.dss) script file.

    Args:
        output_path: Destination path for the .dss file.
        load_multiplier: Load scaling multiplier.
        custom_loads: Optional custom bus loads.

    Returns:
        Path to the written file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    commands = generate_dss_circuit_commands(
        load_multiplier=load_multiplier, custom_loads=custom_loads
    )
    path.write_text("\n".join(commands) + "\n", encoding="utf-8")
    logger.info("Exported IEEE 33-bus OpenDSS model file", extra={"path": str(path)})
    return path
