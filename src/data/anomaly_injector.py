"""
src/data/anomaly_injector.py — Controlled synthetic anomaly injection.

Injects synthetic anomalies (load spikes, load drops, phase imbalances) into the
mapped bus load time series with reproducible random seeds.
Severity tiers are calibrated strictly in units of training split standard deviations (sigma).
Stores ground-truth labels and per-event telemetry separately to prevent data leakage.
"""

import uuid
from typing import Any

import numpy as np
import pandas as pd

from src.data.schema import AnomalyEvent
from src.utils.logging import get_logger

logger = get_logger("data.anomaly_injector")

# Severity Tier Multipliers (expressed as sigma multipliers on bus training residual/load std)
# Calibrated strictly on training/validation detectability characteristics.
SEVERITY_SIGMA_MULTIPLIERS: dict[str, dict[str, float]] = {
    "low": {
        "load_spike_sigma": 2.0,      # +2.0 sigma perturbation
        "load_drop_sigma": 1.5,       # -1.5 sigma perturbation
        "phase_imbalance_sigma": 2.0, # +2.0 sigma on primary bus, -1.0 sigma on others
    },
    "medium": {
        "load_spike_sigma": 3.5,      # +3.5 sigma perturbation
        "load_drop_sigma": 2.5,       # -2.5 sigma perturbation
        "phase_imbalance_sigma": 3.5, # +3.5 sigma on primary bus, -1.5 sigma on others
    },
    "high": {
        "load_spike_sigma": 5.0,      # +5.0 sigma perturbation
        "load_drop_sigma": 3.5,       # -3.5 sigma perturbation
        "phase_imbalance_sigma": 5.0, # +5.0 sigma on primary bus, -2.0 sigma on others
    },
}


def inject_synthetic_anomalies(
    active_power_df: pd.DataFrame,
    reactive_power_df: pd.DataFrame,
    anomaly_rate: float = 0.05,
    fault_types: list[str] | None = None,
    duration_timesteps: int = 4,
    train_end_idx: int | None = None,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[AnomalyEvent]]:
    """Inject synthetic anomalies into active and reactive bus load profiles.

    Produces:
    1. Perturbed active power profiles (physical kW).
    2. Perturbed reactive power profiles (physical kVAR).
    3. Separate ground truth anomaly labels DataFrame with severity and per-bus annotations.
    4. List of AnomalyEvent metadata records.

    Fault Types:
    - load_spike: sudden physical demand increase (+sigma on target buses).
    - load_drop: sudden customer demand loss / curtailment (-sigma on target buses).
    - phase_imbalance: asymmetric perturbation across target buses.

    Severity Tiers:
    - low, medium, high (cycled deterministically or sampled uniformly).

    Args:
        active_power_df: DataFrame of unperturbed physical active power (kW) by bus.
        reactive_power_df: DataFrame of unperturbed physical reactive power (kVAR) by bus.
        anomaly_rate: Fraction of timesteps that should be anomalous (default: 0.05).
        fault_types: List of fault types to inject. Defaults to ['load_drop', 'load_spike', 'phase_imbalance'].
        duration_timesteps: Duration of each anomaly event in discrete timesteps.
        train_end_idx: Optional cutoff index defining the training split (for computing reference std).
        seed: Random seed for deterministic reproducibility.

    Returns:
        Tuple of (injected_active_df, injected_reactive_df, anomaly_labels_df, event_list).
    """
    if fault_types is None:
        fault_types = ["load_drop", "load_spike", "phase_imbalance"]

    # Remap deprecated 'voltage_sag' if encountered in legacy configs
    fault_types = [("load_drop" if ft == "voltage_sag" else ft) for ft in fault_types]

    logger.info(
        "Injecting synthetic anomalies with severity tiers",
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

    # Compute baseline reference standard deviations strictly from training partition
    train_limit = train_end_idx if (train_end_idx is not None and train_end_idx > 0) else int(0.70 * n_timesteps)
    train_active = active_power_df.iloc[:train_limit]
    bus_std_p: dict[str, float] = {}
    for col in bus_cols_p:
        std_val = float(train_active[col].std())
        bus_std_p[col] = max(1.0, std_val)

    injected_p = active_power_df.copy()
    injected_q = reactive_power_df.copy()

    # Labels arrays
    is_anomaly = np.zeros(n_timesteps, dtype=np.int32)
    label_types = ["none"] * n_timesteps
    affected_buses_str = ["none"] * n_timesteps
    event_ids = ["none"] * n_timesteps
    severity_labels = ["none"] * n_timesteps
    realized_ratios = np.ones(n_timesteps, dtype=np.float64)
    effect_sizes_sigma = np.zeros(n_timesteps, dtype=np.float64)

    # Calculate target number of anomaly events
    target_anomalous_steps = int(n_timesteps * anomaly_rate)
    num_events = max(1, target_anomalous_steps // duration_timesteps)

    # Pick non-overlapping start indices with a safety buffer
    buffer_zone = duration_timesteps * 2
    available_indices = list(range(buffer_zone, n_timesteps - buffer_zone))
    rng.shuffle(available_indices)

    events: list[AnomalyEvent] = []
    occupied_indices: set[int] = set()
    tier_names = ["low", "medium", "high"]

    for event_idx_count, idx in enumerate(available_indices):
        if len(events) >= num_events:
            break

        event_range = set(range(idx, idx + duration_timesteps))
        # Ensure no overlap with existing events
        if event_range.intersection(occupied_indices):
            continue

        # Choose fault type, severity tier, and event ID
        fault_type = str(rng.choice(fault_types))
        severity = str(tier_names[event_idx_count % len(tier_names)])
        event_id = f"ANOM_{uuid.UUID(bytes=rng.bytes(16)).hex[:8]}"

        # Select 1 to 4 affected buses
        num_target_buses = int(rng.integers(1, min(5, num_buses + 1)))
        target_indices = rng.choice(num_buses, size=num_target_buses, replace=False)
        target_buses_p = [bus_cols_p[b] for b in target_indices]
        target_buses_q = [bus_cols_q[b] for b in target_indices]
        bus_numbers = [int(b.split("_")[1]) for b in target_buses_p]

        end_idx = idx + duration_timesteps
        tier_cfg = SEVERITY_SIGMA_MULTIPLIERS[severity]

        event_ratios: list[float] = []
        event_sigmas: list[float] = []

        if fault_type == "load_spike":
            sigma_mult = tier_cfg["load_spike_sigma"]
            for b_p, b_q in zip(target_buses_p, target_buses_q, strict=True):
                base_p = injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)].to_numpy()
                std_ref = bus_std_p[b_p]
                delta_p = sigma_mult * std_ref
                new_p = base_p + delta_p
                # Preserve power factor
                q_p_ratio = (
                    injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)].to_numpy()
                    / np.maximum(0.01, base_p)
                )
                new_q = new_p * q_p_ratio

                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] = new_p
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] = new_q

                event_ratios.append(float(np.mean(new_p / np.maximum(0.01, base_p))))
                event_sigmas.append(sigma_mult)

        elif fault_type in ("load_drop", "voltage_sag"):
            fault_type = "load_drop"
            sigma_mult = tier_cfg["load_drop_sigma"]
            for b_p, b_q in zip(target_buses_p, target_buses_q, strict=True):
                base_p = injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)].to_numpy()
                std_ref = bus_std_p[b_p]
                delta_p = sigma_mult * std_ref
                # Drop load but enforce non-negative floor (>= 0.05 kW)
                new_p = np.maximum(0.05, base_p - delta_p)
                q_p_ratio = (
                    injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)].to_numpy()
                    / np.maximum(0.01, base_p)
                )
                new_q = np.maximum(0.01, new_p * q_p_ratio)

                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] = new_p
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] = new_q

                event_ratios.append(float(np.mean(new_p / np.maximum(0.01, base_p))))
                event_sigmas.append(sigma_mult)

        elif fault_type == "phase_imbalance":
            sigma_mult = tier_cfg["phase_imbalance_sigma"]
            # Primary bus surges (+sigma), secondary buses drop
            first_b_p, first_b_q = target_buses_p[0], target_buses_q[0]
            base_p0 = injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(first_b_p)].to_numpy()
            std_ref0 = bus_std_p[first_b_p]
            new_p0 = base_p0 + (sigma_mult * std_ref0)
            q_p_ratio0 = (
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(first_b_q)].to_numpy()
                / np.maximum(0.01, base_p0)
            )
            injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(first_b_p)] = new_p0
            injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(first_b_q)] = new_p0 * q_p_ratio0
            event_ratios.append(float(np.mean(new_p0 / np.maximum(0.01, base_p0))))
            event_sigmas.append(sigma_mult)

            # Secondary buses drop by half the sigma multiplier
            for b_p, b_q in zip(target_buses_p[1:], target_buses_q[1:], strict=True):
                base_pk = injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)].to_numpy()
                std_refk = bus_std_p[b_p]
                new_pk = np.maximum(0.05, base_pk - (0.5 * sigma_mult * std_refk))
                q_p_ratiok = (
                    injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)].to_numpy()
                    / np.maximum(0.01, base_pk)
                )
                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] = new_pk
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] = np.maximum(
                    0.01, new_pk * q_p_ratiok
                )
                event_ratios.append(float(np.mean(new_pk / np.maximum(0.01, base_pk))))
                event_sigmas.append(0.5 * sigma_mult)

        mean_realized_ratio = float(np.mean(event_ratios)) if event_ratios else 1.0
        mean_effect_sigma = float(np.mean(event_sigmas)) if event_sigmas else 0.0

        # Record labels
        for step in range(idx, end_idx):
            is_anomaly[step] = 1
            label_types[step] = fault_type
            affected_buses_str[step] = ",".join(map(str, bus_numbers))
            event_ids[step] = event_id
            severity_labels[step] = severity
            realized_ratios[step] = mean_realized_ratio
            effect_sizes_sigma[step] = mean_effect_sigma

        occupied_indices.update(event_range)

        events.append(
            AnomalyEvent(
                event_id=event_id,
                fault_type=fault_type,
                target_buses=bus_numbers,
                start_index=idx,
                end_index=end_idx,
                duration_timesteps=duration_timesteps,
                magnitude=mean_realized_ratio,
                severity=severity,
                realized_ratio_kw=mean_realized_ratio,
                effect_size_sigma=mean_effect_sigma,
                start_timestamp=timestamps[idx].isoformat(),
                end_timestamp=timestamps[end_idx - 1].isoformat(),
            )
        )

    labels_df = pd.DataFrame(
        {
            "is_anomaly": is_anomaly,
            "anomaly_type": label_types,
            "severity": severity_labels,
            "target_buses": affected_buses_str,
            "affected_buses": affected_buses_str,
            "realized_ratio_kw": realized_ratios,
            "effect_size_sigma": effect_sizes_sigma,
            "event_id": event_ids,
        },
        index=timestamps,
    )

    actual_rate = float(np.mean(is_anomaly))
    logger.info(
        "Anomaly injection complete with severity tiers",
        extra={
            "num_events": len(events),
            "anomalous_steps": int(np.sum(is_anomaly)),
            "actual_rate": round(actual_rate, 4),
        },
    )

    return injected_p, injected_q, labels_df, events
