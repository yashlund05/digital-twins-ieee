"""
src/synchronization/state_tracker.py — Physical vs. Digital Twin state divergence tracking.

Quantifies the degree to which the virtual Digital Twin state diverges from the true physical
grid state as a function of synchronization staleness:
    divergence = ||x_physical(t) - x_dt(t)||_2
Also tracks per-quantity deviations (voltage, current, power).
"""

import numpy as np
from pydantic import BaseModel, Field

from src.digital_twin.state import DigitalTwinState
from src.utils.logging import get_logger

logger = get_logger("synchronization.state_tracker")


class DivergenceMetrics(BaseModel):
    """Metrics quantifying divergence between physical state and Digital Twin state."""

    l2_norm_divergence: float = Field(
        ..., description="L2 norm difference of full 104-d state vectors"
    )
    relative_divergence_pct: float = Field(
        ..., description="Percentage L2 divergence relative to physical state norm"
    )
    max_voltage_error_pu: float = Field(
        ..., description="Maximum absolute voltage difference across all buses in pu"
    )
    mean_voltage_error_pu: float = Field(
        ..., description="Mean absolute voltage difference across all buses in pu"
    )
    max_current_error_a: float = Field(
        ..., description="Maximum absolute current difference across all branches in A"
    )
    mean_current_error_a: float = Field(
        ..., description="Mean absolute current difference across all branches in A"
    )
    active_power_error_kw: float = Field(
        ..., description="Absolute difference in total load active power in kW"
    )
    reactive_power_error_kvar: float = Field(
        ..., description="Absolute difference in total load reactive power in kVAR"
    )


class StateDivergenceTracker:
    """Computes and tracks state divergence between physical system and Digital Twin."""

    def __init__(self) -> None:
        """Initialize the divergence tracker."""
        self._last_metrics: DivergenceMetrics | None = None
        self._divergence_history: list[float] = []

    def compute_divergence(
        self,
        physical_state: DigitalTwinState,
        dt_state: DigitalTwinState,
    ) -> DivergenceMetrics:
        """Calculate divergence metrics between physical state and DT state.

        Args:
            physical_state: Current ground-truth physical grid state.
            dt_state: Current Digital Twin state (may be fresh or stale).

        Returns:
            DivergenceMetrics containing L2 norm and per-quantity error measures.
        """
        # 1. Full feature vector divergence
        vec_phys = physical_state.to_feature_vector()
        vec_dt = dt_state.to_feature_vector()
        diff = vec_phys - vec_dt
        l2_div = float(np.linalg.norm(diff))
        phys_norm = float(np.linalg.norm(vec_phys))
        rel_div_pct = float((l2_div / (phys_norm + 1e-7)) * 100.0)

        # 2. Bus voltage errors (pu)
        v_errors = [
            abs(physical_state.bus_voltages_pu[b] - dt_state.bus_voltages_pu[b])
            for b in physical_state.bus_voltages_pu
            if b in dt_state.bus_voltages_pu
        ]
        max_v_err = float(max(v_errors)) if v_errors else 0.0
        mean_v_err = float(np.mean(v_errors)) if v_errors else 0.0

        # 3. Branch current errors (A)
        i_errors = [
            abs(physical_state.branch_currents_a[line] - dt_state.branch_currents_a[line])
            for line in physical_state.branch_currents_a
            if line in dt_state.branch_currents_a
        ]
        max_i_err = float(max(i_errors)) if i_errors else 0.0
        mean_i_err = float(np.mean(i_errors)) if i_errors else 0.0

        # 4. Total power error (kW, kVAR)
        p_err = float(abs(physical_state.total_load_p_kw - dt_state.total_load_p_kw))
        q_err = float(abs(physical_state.total_load_q_kvar - dt_state.total_load_q_kvar))

        metrics = DivergenceMetrics(
            l2_norm_divergence=l2_div,
            relative_divergence_pct=rel_div_pct,
            max_voltage_error_pu=max_v_err,
            mean_voltage_error_pu=mean_v_err,
            max_current_error_a=max_i_err,
            mean_current_error_a=mean_i_err,
            active_power_error_kw=p_err,
            reactive_power_error_kvar=q_err,
        )

        self._last_metrics = metrics
        self._divergence_history.append(l2_div)

        return metrics

    @property
    def latest_divergence(self) -> DivergenceMetrics | None:
        """Return the most recently computed divergence metrics."""
        return self._last_metrics

    @property
    def mean_l2_divergence(self) -> float:
        """Mean L2 divergence over all tracked steps."""
        if not self._divergence_history:
            return 0.0
        return float(np.mean(self._divergence_history))

    def reset(self) -> None:
        """Reset history and cached metrics."""
        self._last_metrics = None
        self._divergence_history.clear()
