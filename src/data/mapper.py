"""
src/data/mapper.py — Mapping Pecan Street residential load profiles to IEEE 33-bus topology.

Implements the hybrid simulation dataset protocol (DATA_PROTOCOL.md):
- Maps residential consumption traces onto the 32 load buses of the IEEE 33-bus benchmark.
- Applies bus-specific capacity scaling derived from Baran & Wu (1989) reference load data.
- Ensures load diversity across the feeder and preserves total system active load (3,715 kW nominal).
"""

import numpy as np
import pandas as pd

from src.data.schema import BusMappingInfo, MappingConfigSummary
from src.utils.logging import get_logger

logger = get_logger("data.mapper")

# Baran & Wu (1989) standard IEEE 33-bus benchmark nominal loads (kW, kVAR)
# Bus 1 is the slack bus (0 kW, 0 kVAR). Load buses are 2 through 33.
IEEE_33_BENCHMARK_LOADS: dict[int, tuple[float, float]] = {
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

TOTAL_NOMINAL_P_KW: float = sum(p for p, _ in IEEE_33_BENCHMARK_LOADS.values())  # 3715.0 kW
TOTAL_NOMINAL_Q_KVAR: float = sum(q for _, q in IEEE_33_BENCHMARK_LOADS.values())  # 2300.0 kVAR


def map_homes_to_ieee33(
    home_profiles: pd.DataFrame,
    seed: int = 42,
    homes_per_bus: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame, MappingConfigSummary]:
    """Map residential home profiles onto the 32 load buses of the IEEE 33-bus feeder.

    For each load bus (2 to 33):
    1. Deterministically selects a diverse combination of home profiles.
    2. Aggregates the selected homes into an unscaled bus load trace.
    3. Derives a bus-specific scaling factor such that the mean of the scaled active
       load equals the Baran & Wu (1989) benchmark nominal load for that bus.
    4. Calculates reactive power maintaining the benchmark power factor ratio (Q0 / P0).

    Args:
        home_profiles: DataFrame of residential loads (columns = home IDs, index = timestamps).
        seed: Random seed for deterministic reproducibility.
        homes_per_bus: Number of home profiles to aggregate per bus node.

    Returns:
        Tuple containing:
        - active_power_df: DataFrame of active power (kW) for buses 2 to 33.
        - reactive_power_df: DataFrame of reactive power (kVAR) for buses 2 to 33.
        - mapping_summary: MappingConfigSummary schema capturing assignment details.
    """
    logger.info(
        "Executing IEEE 33-bus mapping protocol",
        extra={"seed": seed, "homes_per_bus": homes_per_bus},
    )

    available_homes = list(home_profiles.columns)
    num_homes = len(available_homes)
    if num_homes == 0:
        raise ValueError("Cannot map empty home profiles DataFrame.")

    rng = np.random.default_rng(seed)
    timestamps = home_profiles.index

    active_data: dict[str, np.ndarray] = {}
    reactive_data: dict[str, np.ndarray] = {}
    bus_mappings: dict[int, BusMappingInfo] = {}

    for bus_id in range(2, 34):
        nom_p, nom_q = IEEE_33_BENCHMARK_LOADS[bus_id]

        # Deterministically sample homes for this bus with replacement across the network
        selected_home_indices = rng.choice(
            num_homes, size=homes_per_bus, replace=False if num_homes >= homes_per_bus else True
        )
        selected_homes = [int(available_homes[idx]) for idx in selected_home_indices]

        # Aggregate loads of selected homes
        raw_bus_load = home_profiles[selected_homes].sum(axis=1).to_numpy(dtype=np.float64)

        # Baseline mean check
        mean_raw = float(np.mean(raw_bus_load))
        if mean_raw <= 0.01:
            raw_bus_load = raw_bus_load - np.min(raw_bus_load) + 0.5
            mean_raw = float(np.mean(raw_bus_load))

        # Scaling factor: scales mean load to match benchmark nominal active power
        scaling_factor = nom_p / mean_raw
        scaled_p = raw_bus_load * scaling_factor

        # Reactive power: scaled to preserve benchmark power factor ratio
        q_p_ratio = (nom_q / nom_p) if nom_p > 0 else 0.0
        scaled_q = scaled_p * q_p_ratio

        # Store in columns
        col_p = f"bus_{bus_id}_p_kw"
        col_q = f"bus_{bus_id}_q_kvar"
        active_data[col_p] = scaled_p
        reactive_data[col_q] = scaled_q

        bus_mappings[bus_id] = BusMappingInfo(
            bus_id=bus_id,
            nominal_p_kw=nom_p,
            nominal_q_kvar=nom_q,
            assigned_homes=selected_homes,
            scaling_factor=float(scaling_factor),
        )

    active_df = pd.DataFrame(active_data, index=timestamps)
    reactive_df = pd.DataFrame(reactive_data, index=timestamps)

    summary = MappingConfigSummary(
        topology="ieee_33_bus",
        num_load_buses=32,
        slack_bus_id=1,
        total_nominal_p_kw=TOTAL_NOMINAL_P_KW,
        total_nominal_q_kvar=TOTAL_NOMINAL_Q_KVAR,
        bus_mappings=bus_mappings,
        random_seed=seed,
    )

    logger.info(
        "Mapped 32 load buses successfully",
        extra={
            "mean_total_p_kw": float(active_df.sum(axis=1).mean()),
            "nominal_total_p_kw": TOTAL_NOMINAL_P_KW,
        },
    )

    return active_df, reactive_df, summary
