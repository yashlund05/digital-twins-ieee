"""
src/residuals/calculator.py — Pure physics-based Digital Twin residual calculator.

Computes the fundamental physical-virtual residual:
    r_t = y_t - y_hat_DT,t

Preserves raw residual immutability: no hidden clipping, smoothing, filtering,
denoising, or normalization is performed. Downstream scaling and feature extraction
are isolated in normalizer.py and features.py.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.digital_twin.state import DigitalTwinState
from src.utils.logging import get_logger

logger = get_logger("residuals.calculator")


@dataclass
class ResidualResult:
    """Encapsulates the raw residual calculation and associated synchronization metadata."""

    raw_residual: np.ndarray | pd.DataFrame
    feature_names: list[str]
    physical_timestamps: list[Any] | None = None
    dt_sync_timestamps: list[Any] | None = None
    aoi_seconds: float | np.ndarray | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def values(self) -> np.ndarray:
        """NumPy array representation of raw residual."""
        if isinstance(self.raw_residual, pd.DataFrame):
            return self.raw_residual.values
        return self.raw_residual

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the residual array."""
        return self.raw_residual.shape


@dataclass
class StateResidualResult:
    """Residual between two DigitalTwinState snapshots."""

    physical_timestamp: str | None
    dt_sync_timestamp: str | None
    full_state_residual: np.ndarray  # 104-d
    bus_voltage_residual_pu: dict[int, float]
    bus_voltage_residual_kv: dict[int, float]
    bus_angle_residual_deg: dict[int, float]
    branch_current_residual_a: dict[str, float]
    total_power_residual_kw: float
    total_power_residual_kvar: float
    l2_norm: float
    metadata: dict[str, Any] = field(default_factory=dict)


def calculate_residual(
    observed: np.ndarray | pd.DataFrame | pd.Series | list[Any],
    dt_estimate: np.ndarray | pd.DataFrame | pd.Series | list[Any],
    physical_timestamps: list[Any] | pd.Index | None = None,
    dt_sync_timestamps: list[Any] | pd.Index | None = None,
    aoi_seconds: float | np.ndarray | list[float] | None = None,
    feature_names: list[str] | None = None,
    validate: bool = True,
) -> ResidualResult:
    """Calculate the element-wise raw residual: r_t = y_t - y_hat_DT,t.

    Args:
        observed: Physical observations (y_t). Can be 1D or 2D array/DataFrame/Series.
        dt_estimate: Digital Twin estimates (y_hat_DT,t) matching observed shape.
        physical_timestamps: Optional timestamp list/index for observations.
        dt_sync_timestamps: Optional timestamp list/index for synchronized DT state.
        aoi_seconds: Age of Information in seconds (scalar or array).
        feature_names: Optional explicit feature/bus names.
        validate: If True, rigorously validates dimensions, shapes, NaNs, and Infs.

    Returns:
        ResidualResult containing the exact raw residual and metadata.

    Raises:
        ValueError: On shape mismatch, NaN/Inf values, empty input, or unaligned index.
    """
    # 1. Empty input validation
    if observed is None or dt_estimate is None:
        raise ValueError("Inputs 'observed' and 'dt_estimate' must not be None.")

    is_df = isinstance(observed, pd.DataFrame)
    is_series = isinstance(observed, pd.Series)

    # Extract feature names and timestamps if DataFrame or Series
    resolved_features = feature_names
    resolved_phys_ts = physical_timestamps

    if is_df:
        if resolved_features is None:
            resolved_features = list(observed.columns)
        if resolved_phys_ts is None:
            resolved_phys_ts = list(observed.index)
        obs_arr = observed.values
    elif is_series:
        if resolved_features is None:
            resolved_features = [str(observed.name or "feature_0")]
        if resolved_phys_ts is None:
            resolved_phys_ts = list(observed.index)
        obs_arr = observed.values
    else:
        obs_arr = np.asarray(observed)

    if isinstance(dt_estimate, (pd.DataFrame, pd.Series)):
        est_arr = dt_estimate.values
    else:
        est_arr = np.asarray(dt_estimate)

    if obs_arr.size == 0 or est_arr.size == 0:
        raise ValueError("Cannot calculate residual for empty inputs (size == 0).")

    # 2. Shape and dimension validation
    if obs_arr.shape != est_arr.shape:
        raise ValueError(
            f"Shape mismatch: observed shape {obs_arr.shape} does not match "
            f"dt_estimate shape {est_arr.shape}. Broadcasting is strictly disallowed."
        )

    # 3. Numeric validity (NaN / Inf)
    if validate:
        if not np.issubdtype(obs_arr.dtype, np.number) or not np.issubdtype(
            est_arr.dtype, np.number
        ):
            raise ValueError("All observed and dt_estimate values must be numeric.")

        if np.isnan(obs_arr).any() or np.isnan(est_arr).any():
            raise ValueError(
                "Input contains NaN values. Residual calculator requires clean, valid data."
            )

        if np.isinf(obs_arr).any() or np.isinf(est_arr).any():
            raise ValueError(
                "Input contains infinite values. Residual calculator requires finite data."
            )

        # Check timestamp alignment if both are pandas Series/DataFrames
        if isinstance(observed, (pd.DataFrame, pd.Series)) and isinstance(
            dt_estimate, (pd.DataFrame, pd.Series)
        ):
            if not observed.index.equals(dt_estimate.index):
                raise ValueError(
                    "Timestamp/index mismatch between observed and dt_estimate. "
                    "Indices must be identically ordered and aligned."
                )

    # 4. Pure raw residual calculation: r_t = y_t - y_hat_DT,t
    # Raw residual immutability: NO clipping, smoothing, or normalization.
    raw_res = obs_arr - est_arr

    # Format return array
    if is_df:
        raw_res_out: np.ndarray | pd.DataFrame = pd.DataFrame(
            raw_res,
            index=observed.index,
            columns=observed.columns,
        )
    elif is_series:
        raw_res_out = pd.Series(
            raw_res,
            index=observed.index,
            name=f"residual_{observed.name}",
        )
    else:
        raw_res_out = raw_res

    # Default feature names if still None
    if resolved_features is None:
        if raw_res.ndim == 1:
            resolved_features = ["feature_0"]
        else:
            resolved_features = [f"feature_{i}" for i in range(raw_res.shape[1])]

    meta = {
        "num_samples": int(obs_arr.shape[0]),
        "num_features": int(obs_arr.shape[1]) if obs_arr.ndim > 1 else 1,
        "is_exact_zero": bool(np.all(raw_res == 0.0)),
        "max_abs_residual": float(np.max(np.abs(raw_res))),
        "mean_abs_residual": float(np.mean(np.abs(raw_res))),
    }

    return ResidualResult(
        raw_residual=raw_res_out,
        feature_names=resolved_features,
        physical_timestamps=list(resolved_phys_ts) if resolved_phys_ts is not None else None,
        dt_sync_timestamps=list(dt_sync_timestamps) if dt_sync_timestamps is not None else None,
        aoi_seconds=aoi_seconds,
        metadata=meta,
    )


def calculate_state_residual(
    physical_state: DigitalTwinState,
    dt_state: DigitalTwinState,
) -> StateResidualResult:
    """Calculate the residual between two DigitalTwinState instances.

    Args:
        physical_state: Ground-truth physical state snapshot.
        dt_state: Digital Twin state snapshot (synchronized at dt_state.timestamp).

    Returns:
        StateResidualResult containing full 104-d vector residual and per-component residuals.
    """
    if not isinstance(physical_state, DigitalTwinState) or not isinstance(
        dt_state, DigitalTwinState
    ):
        raise TypeError("Both physical_state and dt_state must be DigitalTwinState instances.")

    vec_phys = physical_state.to_feature_vector()
    vec_dt = dt_state.to_feature_vector()

    if np.isnan(vec_phys).any() or np.isnan(vec_dt).any():
        raise ValueError("DigitalTwinState vector contains NaN values.")

    full_residual = vec_phys - vec_dt
    l2_res = float(np.linalg.norm(full_residual))

    # Per-bus voltage residuals (pu and kv)
    v_res_pu = {
        b: float(physical_state.bus_voltages_pu[b] - dt_state.bus_voltages_pu[b])
        for b in range(1, 34)
        if b in physical_state.bus_voltages_pu and b in dt_state.bus_voltages_pu
    }
    v_res_kv = {
        b: float(physical_state.bus_voltages_kv[b] - dt_state.bus_voltages_kv[b])
        for b in range(1, 34)
        if b in physical_state.bus_voltages_kv and b in dt_state.bus_voltages_kv
    }
    ang_res_deg = {
        b: float(physical_state.bus_voltage_angles_deg[b] - dt_state.bus_voltage_angles_deg[b])
        for b in range(1, 34)
        if b in physical_state.bus_voltage_angles_deg and b in dt_state.bus_voltage_angles_deg
    }
    curr_res_a = {
        line: float(physical_state.branch_currents_a[line] - dt_state.branch_currents_a[line])
        for line in physical_state.branch_currents_a
        if line in dt_state.branch_currents_a
    }

    p_res_kw = float(physical_state.total_load_p_kw - dt_state.total_load_p_kw)
    q_res_kvar = float(physical_state.total_load_q_kvar - dt_state.total_load_q_kvar)

    return StateResidualResult(
        physical_timestamp=physical_state.timestamp,
        dt_sync_timestamp=dt_state.timestamp,
        full_state_residual=full_residual,
        bus_voltage_residual_pu=v_res_pu,
        bus_voltage_residual_kv=v_res_kv,
        bus_angle_residual_deg=ang_res_deg,
        branch_current_residual_a=curr_res_a,
        total_power_residual_kw=p_res_kw,
        total_power_residual_kvar=q_res_kvar,
        l2_norm=l2_res,
        metadata={
            "max_voltage_error_pu": float(max(abs(v) for v in v_res_pu.values()))
            if v_res_pu
            else 0.0,
            "mean_voltage_error_pu": float(np.mean([abs(v) for v in v_res_pu.values()]))
            if v_res_pu
            else 0.0,
            "max_current_error_a": float(max(abs(i) for i in curr_res_a.values()))
            if curr_res_a
            else 0.0,
            "mean_current_error_a": float(np.mean([abs(i) for i in curr_res_a.values()]))
            if curr_res_a
            else 0.0,
        },
    )
