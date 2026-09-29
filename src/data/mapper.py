"""
src/data/mapper.py — Mapping Pecan Street residential load profiles to IEEE 33-bus topology.

Implements the hybrid simulation dataset protocol (DATA_PROTOCOL.md) and the
re-anchored mapping adopted by ADR-0005:

- Household-to-bus assignment is read from the tracked file
  ``configs/mapping_assignment.yaml`` (balanced, pair-unique) so the dataset
  construction never relies on RNG reproducibility.
- The feeder is anchored so that the p99.9 of the total unnormalized feeder
  power equals the Baran & Wu (1989) design peak (3,715 kW) instead of
  mean-matching each bus (legacy ``anchor="mean"`` remains available).
- A background cap limits every bus to ``cap_multiple`` x its nominal rating;
  injected anomalies are applied later (after anchoring) and may exceed the cap.
- Reactive power preserves each bus's benchmark power factor (Q/P ratio).
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.schema import BusMappingInfo, MappingConfigSummary
from src.utils.io import load_yaml_file
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

DEFAULT_ASSIGNMENT_PATH = "configs/mapping_assignment.yaml"

# Anchor name -> percentile of the unnormalized feeder total S(t) that is set to
# the design peak (3,715 kW). "mean" is the legacy per-bus mean-matching (s = 1).
ANCHOR_PERCENTILE: dict[str, float | None] = {
    "mean": None,
    "feeder_p99": 99.0,
    "feeder_p999": 99.9,
    "feeder_max": 100.0,
}


def load_assignment_file(path: Path | str = DEFAULT_ASSIGNMENT_PATH) -> dict[int, list[int]]:
    """Load the tracked household-to-bus assignment file.

    Args:
        path: Path to the assignment YAML (configs/mapping_assignment.yaml).

    Returns:
        Mapping of bus_id (2..33) to its list of assigned home ids.

    Raises:
        ValueError: If the file structure is not a valid 32-bus assignment.
    """
    data = load_yaml_file(path)
    bus_assignments = data.get("bus_assignments")
    if not isinstance(bus_assignments, dict):
        raise ValueError(f"Assignment file {path} has no 'bus_assignments' mapping.")
    assignment = {int(b): [int(h) for h in homes] for b, homes in bus_assignments.items()}
    if sorted(assignment) != list(range(2, 34)):
        raise ValueError(f"Assignment file {path} must cover buses 2..33 exactly once.")
    return assignment


def _validate_assignment(
    assignment: dict[int, list[int]], home_profiles: pd.DataFrame
) -> None:
    """Validate the structural contract of a household assignment.

    Raises:
        ValueError: If any bus is missing, has duplicate homes, or references
            households absent from ``home_profiles``; if two buses share the
            identical pair.
    """
    if sorted(assignment) != list(range(2, 34)):
        raise ValueError("Assignment must cover buses 2..33 exactly once.")
    available = set(home_profiles.columns)
    seen_pairs: set[frozenset] = set()
    for bus, homes in assignment.items():
        if len(homes) != 2:
            raise ValueError(f"Bus {bus}: ADR-0005 mapping requires exactly 2 homes per bus.")
        if len(set(homes)) != len(homes):
            raise ValueError(f"Bus {bus}: the same home may not be assigned twice to one bus.")
        for h in homes:
            if h not in available:
                raise ValueError(f"Bus {bus}: home {h} not present in home_profiles columns.")
        pair = frozenset(homes)
        if pair in seen_pairs:
            raise ValueError(f"Bus {bus}: duplicated household pair across buses.")
        seen_pairs.add(pair)


def _sha256_of_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def map_homes_to_ieee33(
    home_profiles: pd.DataFrame,
    seed: int = 42,
    homes_per_bus: int = 2,
    assignment: dict[int, list[int]] | None = None,
    assignment_path: Path | str | None = DEFAULT_ASSIGNMENT_PATH,
    anchor: str = "feeder_p999",
    alpha: float = 1.0,
    cap_multiple: float = 2.0,
) -> tuple[pd.DataFrame, pd.DataFrame, MappingConfigSummary]:
    """Map residential home profiles onto the 32 load buses of the IEEE 33-bus feeder.

    Per ADR-0005 (Option iv, re-anchor only):
    1. The household assignment comes from the tracked assignment file (or an
       explicit dict); legacy seeded sampling is used only if neither is given.
    2. Each bus's household-pair trace is normalized to a mean-1 shape; with
       ``alpha < 1`` the shape blends toward the all-home aggregate feeder shape.
    3. The feeder anchor scale ``s`` sets ``percentile(S, p) = 3,715 kW`` where
       ``S(t) = sum_b nom_b * shape_b(t)`` (``anchor="mean"`` restores s = 1).
    4. Active power is capped at ``cap_multiple`` x nominal (background cap);
       reactive power preserves each bus's benchmark Q/P ratio.

    Args:
        home_profiles: DataFrame of residential loads (columns = home IDs, index = timestamps).
        seed: Random seed (recorded; used only by the legacy sampling fallback).
        homes_per_bus: Households per bus (must be 2 for the tracked assignment).
        assignment: Explicit household assignment overriding the file, if given.
        assignment_path: Tracked assignment YAML; ignored when ``assignment`` is given.
        anchor: One of "mean", "feeder_p99", "feeder_p999", "feeder_max".
        alpha: Household-shape amplitude (1.0 = pure household shapes per ADR-0005).
        cap_multiple: Background cap in multiples of nominal (None disables).

    Returns:
        Tuple of (active power kW DataFrame, reactive power kVAR DataFrame,
        MappingConfigSummary with anchor metadata).

    Raises:
        ValueError: On invalid anchor/alpha/assignment or empty input.
    """
    if anchor not in ANCHOR_PERCENTILE:
        raise ValueError(f"Unknown anchor '{anchor}'. Valid: {sorted(ANCHOR_PERCENTILE)}")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(f"alpha must be within [0, 1], got {alpha}")
    if len(home_profiles.columns) == 0:
        raise ValueError("Cannot map empty home profiles DataFrame.")

    rng = np.random.default_rng(seed)
    timestamps = home_profiles.index
    all_home_matrix = home_profiles.to_numpy(dtype=np.float64)

    # --- resolve the household assignment ---
    assignment_file_used: str | None = None
    assignment_sha: str | None = None
    if assignment is None:
        if assignment_path is not None and Path(assignment_path).exists():
            assignment = load_assignment_file(assignment_path)
            assignment_file_used = str(assignment_path)
            assignment_sha = _sha256_of_file(assignment_path)
        else:
            logger.warning(
                "No assignment dict or assignment file found; falling back to legacy "
                "seeded sampling (not ADR-0005 compliant; for tests only).",
                extra={"seed": seed},
            )
            assignment = {}
            for bus_id in range(2, 34):
                idx = rng.choice(len(home_profiles.columns), size=homes_per_bus, replace=False)
                assignment[bus_id] = [int(home_profiles.columns[i]) for i in idx]
    _validate_assignment(assignment, home_profiles)

    # --- household shapes and feeder aggregate ---
    # F(t): aggregate shape over ALL available homes (the full inventory).
    feeder_agg = all_home_matrix.sum(axis=1)
    feeder_shape = feeder_agg / feeder_agg.mean()
    alpha = float(alpha)

    raw_sums: dict[int, np.ndarray] = {}
    mean_raw: dict[int, float] = {}
    shapes: dict[int, np.ndarray] = {}
    for bus_id in range(2, 34):
        rs = home_profiles[assignment[bus_id]].sum(axis=1).to_numpy(dtype=np.float64)
        raw_sums[bus_id] = rs
        mean_raw[bus_id] = float(rs.mean())
        if mean_raw[bus_id] <= 0.01:
            rs = rs - rs.min() + 0.5
            mean_raw[bus_id] = float(rs.mean())
            raw_sums[bus_id] = rs
        shapes[bus_id] = (1.0 - alpha) * feeder_shape + alpha * (rs / mean_raw[bus_id])

    # --- anchor scale ---
    unnorm_total = sum(IEEE_33_BENCHMARK_LOADS[b][0] * shapes[b] for b in range(2, 34))
    pct = ANCHOR_PERCENTILE[anchor]
    if pct is None:
        anchor_scale = 1.0
    else:
        anchor_scale = float(TOTAL_NOMINAL_P_KW / np.percentile(unnorm_total, pct))

    # --- scaled bus series with background cap ---
    active_data: dict[str, np.ndarray] = {}
    reactive_data: dict[str, np.ndarray] = {}
    bus_mappings: dict[int, BusMappingInfo] = {}
    for bus_id in range(2, 34):
        nom_p, nom_q = IEEE_33_BENCHMARK_LOADS[bus_id]
        uncapped = nom_p * anchor_scale * shapes[bus_id]
        capped = uncapped if cap_multiple is None else np.minimum(
            uncapped, cap_multiple * nom_p
        )
        capped_steps = int(np.sum(uncapped > cap_multiple * nom_p)) if cap_multiple else 0
        q_p_ratio = (nom_q / nom_p) if nom_p > 0 else 0.0

        active_data[f"bus_{bus_id}_p_kw"] = capped
        reactive_data[f"bus_{bus_id}_q_kvar"] = capped * q_p_ratio
        bus_mappings[bus_id] = BusMappingInfo(
            bus_id=bus_id,
            nominal_p_kw=nom_p,
            nominal_q_kvar=nom_q,
            assigned_homes=[int(h) for h in assignment[bus_id]],
            scaling_factor=float(nom_p * anchor_scale / mean_raw[bus_id]),
            mean_raw_kw=float(mean_raw[bus_id]),
            capped_steps=capped_steps,
        )

    active_df = pd.DataFrame(active_data, index=timestamps)
    reactive_df = pd.DataFrame(reactive_data, index=timestamps)

    home_use_counts: dict[str, int] = {}
    for homes in assignment.values():
        for h in homes:
            home_use_counts[str(h)] = home_use_counts.get(str(h), 0) + 1

    summary = MappingConfigSummary(
        topology="ieee_33_bus",
        num_load_buses=32,
        slack_bus_id=1,
        total_nominal_p_kw=TOTAL_NOMINAL_P_KW,
        total_nominal_q_kvar=TOTAL_NOMINAL_Q_KVAR,
        bus_mappings=bus_mappings,
        random_seed=seed,
        anchor=anchor,
        alpha=alpha,
        cap_multiple=float(cap_multiple) if cap_multiple is not None else None,
        anchor_scale=anchor_scale,
        assignment_file=assignment_file_used,
        assignment_sha256=assignment_sha,
        home_use_counts=home_use_counts,
    )

    logger.info(
        "Mapped 32 load buses (ADR-0005 re-anchored mapping)",
        extra={
            "anchor": anchor,
            "anchor_scale": round(anchor_scale, 6),
            "alpha": alpha,
            "cap_multiple": cap_multiple,
            "capped_steps_total": sum(m.capped_steps for m in bus_mappings.values()),
            "mean_total_p_kw": float(active_df.sum(axis=1).mean()),
        },
    )

    return active_df, reactive_df, summary
