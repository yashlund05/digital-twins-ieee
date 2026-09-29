"""
src/data/anomaly_injector.py — Controlled synthetic anomaly injection.

Injects synthetic anomalies (load spikes, voltage sags, phase imbalances) into the
mapped bus load time series with reproducible random seeds.
Stores ground-truth labels separately to prevent data leakage during model training.
"""

import uuid

import numpy as np
import pandas as pd

from src.data.schema import AnomalyEvent
from src.utils.logging import get_logger

logger = get_logger("data.anomaly_injector")


def inject_synthetic_anomalies(
    active_power_df: pd.DataFrame,
    reactive_power_df: pd.DataFrame,
    anomaly_rate: float = 0.05,
    fault_types: list[str] | None = None,
    duration_timesteps: int = 4,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[AnomalyEvent]]:
    """Inject synthetic anomalies into active and reactive bus load profiles.

    Produces:
    1. Perturbed active power profiles.
    2. Perturbed reactive power profiles.
    3. Separate ground truth anomaly labels DataFrame (is_anomaly, anomaly_type, affected_buses).
    4. List of AnomalyEvent metadata records.

    Fault Types:
    - load_spike: sudden demand increase (2.5x - 4.0x) on target buses.
    - voltage_sag: severe load drop / fault sag (0.2x - 0.5x) on target buses.
    - phase_imbalance: asymmetric perturbation across a cluster of buses.

    Args:
        active_power_df: DataFrame of active power by bus.
        reactive_power_df: DataFrame of reactive power by bus.
        anomaly_rate: Fraction of timesteps that should be anomalous (e.g., 0.05 for 5%).
        fault_types: List of fault types to inject. Defaults to all 3 types.
        duration_timesteps: Duration of each anomaly event in discrete timesteps.
        seed: Random seed for deterministic reproducibility.

    Returns:
        Tuple of (injected_active_df, injected_reactive_df, anomaly_labels_df, event_list).
    """
    if fault_types is None:
        fault_types = ["voltage_sag", "load_spike", "phase_imbalance"]

    logger.info(
        "Injecting synthetic anomalies",
        extra={
            "rate": anomaly_rate,
            "fault_types": fault_types,
            "duration": duration_timesteps,
            "seed": seed,
        },
    )

    rng = np.random.default_rng(seed)
    n_timesteps = len(active_power_df)
    timestamps = active_power_df.index
    bus_cols_p = list(active_power_df.columns)
    bus_cols_q = list(reactive_power_df.columns)
    num_buses = len(bus_cols_p)

    injected_p = active_power_df.copy()
    injected_q = reactive_power_df.copy()

    # Labels arrays
    is_anomaly = np.zeros(n_timesteps, dtype=np.int32)
    label_types = ["none"] * n_timesteps
    affected_buses_str = ["none"] * n_timesteps
    event_ids = ["none"] * n_timesteps

    # Calculate target number of anomaly events
    target_anomalous_steps = int(n_timesteps * anomaly_rate)
    num_events = max(1, target_anomalous_steps // duration_timesteps)

    # Pick non-overlapping start indices with a safety buffer
    buffer_zone = duration_timesteps * 2
    available_indices = list(range(buffer_zone, n_timesteps - buffer_zone))
    rng.shuffle(available_indices)

    events: list[AnomalyEvent] = []
    occupied_indices: set[int] = set()

    for idx in available_indices:
        if len(events) >= num_events:
            break

        event_range = set(range(idx, idx + duration_timesteps))
        # Ensure no overlap with existing events
        if event_range.intersection(occupied_indices):
            continue

        # Choose fault type and target buses
        fault_type = str(rng.choice(fault_types))
        event_id = f"ANOM_{uuid.UUID(bytes=rng.bytes(16)).hex[:8]}"

        # Select 1 to 4 affected buses
        num_target_buses = rng.integers(1, min(5, num_buses + 1))
        target_indices = rng.choice(num_buses, size=num_target_buses, replace=False)
        target_buses_p = [bus_cols_p[b] for b in target_indices]
        target_buses_q = [bus_cols_q[b] for b in target_indices]
        bus_numbers = [int(b.split("_")[1]) for b in target_buses_p]

        end_idx = idx + duration_timesteps

        if fault_type == "load_spike":
            multiplier = float(rng.uniform(2.5, 4.0))
            for b_p, b_q in zip(target_buses_p, target_buses_q, strict=True):
                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] *= multiplier
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] *= multiplier

        elif fault_type == "voltage_sag":
            multiplier = float(rng.uniform(0.2, 0.5))
            for b_p, b_q in zip(target_buses_p, target_buses_q, strict=True):
                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] *= multiplier
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] *= multiplier

        elif fault_type == "phase_imbalance":
            multiplier = float(rng.uniform(2.0, 3.5))
            # Primary bus surges, others drop
            first_b_p, first_b_q = target_buses_p[0], target_buses_q[0]
            injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(first_b_p)] *= multiplier
            injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(first_b_q)] *= multiplier
            for b_p, b_q in zip(target_buses_p[1:], target_buses_q[1:], strict=True):
                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] *= 0.4
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] *= 0.4

        # Record labels
        for step in range(idx, end_idx):
            is_anomaly[step] = 1
            label_types[step] = fault_type
            affected_buses_str[step] = ",".join(map(str, bus_numbers))
            event_ids[step] = event_id

        occupied_indices.update(event_range)

        events.append(
            AnomalyEvent(
                event_id=event_id,
                fault_type=fault_type,
                target_buses=bus_numbers,
                start_index=idx,
                end_index=end_idx,
                duration_timesteps=duration_timesteps,
                magnitude=multiplier,
                start_timestamp=timestamps[idx].isoformat(),
                end_timestamp=timestamps[end_idx - 1].isoformat(),
            )
        )

    labels_df = pd.DataFrame(
        {
            "is_anomaly": is_anomaly,
            "anomaly_type": label_types,
            "affected_buses": affected_buses_str,
            "event_id": event_ids,
        },
        index=timestamps,
    )

    actual_rate = float(np.mean(is_anomaly))
    logger.info(
        "Anomaly injection complete",
        extra={
            "num_events": len(events),
            "anomalous_steps": int(np.sum(is_anomaly)),
            "actual_rate": round(actual_rate, 4),
        },
    )

    return injected_p, injected_q, labels_df, events
