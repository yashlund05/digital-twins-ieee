"""
src/synchronization/engine.py — Core synchronization loop and engine.

Integrates the UpdateScheduler, AoITracker, StateDivergenceTracker, MissedUpdatePolicy,
and SyncEventLogger to control the experimental independent variable: synchronization staleness.
Guarantees that the Digital Twin always holds a well-defined state (fresh or stale)
and captures full audit logs for empirical staleness analysis.
"""

from pathlib import Path

import pandas as pd
from pydantic import BaseModel, Field

from src.digital_twin.state import DigitalTwinState
from src.synchronization.aoi import AoITracker
from src.synchronization.logger import SyncEventLogger, SyncLogRecord
from src.synchronization.policies import MissedUpdatePolicy, get_policy
from src.synchronization.scheduler import UpdateScheduler
from src.synchronization.state_tracker import DivergenceMetrics, StateDivergenceTracker
from src.utils.config import SynchronizationConfig
from src.utils.logging import get_logger

logger = get_logger("synchronization.engine")


class SynchronizationResult(BaseModel):
    """Encapsulates the output of a single synchronization engine step."""

    dt_state: DigitalTwinState = Field(
        ..., description="Active state maintained in the Digital Twin"
    )
    is_stale: bool = Field(
        ..., description="True if the state is held/extrapolated from an earlier timestamp"
    )
    sync_age_seconds: float = Field(
        ..., ge=0.0, description="Time elapsed since last successful physical update"
    )
    aoi_seconds: float = Field(..., ge=0.0, description="Age of Information in seconds")
    divergence: DivergenceMetrics = Field(
        ..., description="Divergence metrics between physical and DT state"
    )
    update_successful: bool = Field(
        ..., description="True if a fresh update was successfully received and applied"
    )
    policy_applied: str = Field(
        ..., description="Name of the missed-update policy applied ('none' if fresh)"
    )
    log_record: SyncLogRecord = Field(..., description="Structured audit log record for this event")


class SynchronizationEngine:
    """Core synchronization engine governing Digital Twin staleness."""

    def __init__(
        self,
        config: SynchronizationConfig,
        run_id: str = "dev_run",
        missed_update_rate: float = 0.0,
        seed: int = 42,
    ) -> None:
        """Initialize the SynchronizationEngine.

        Args:
            config: Validated SynchronizationConfig instance.
            run_id: Identifier for the current experiment run.
            missed_update_rate: Stochastic packet loss probability [0.0, 1.0].
            seed: Seed for stochastic drop reproducibility.
        """
        self.config = config
        self.run_id = run_id

        # Subcomponents
        self.scheduler = UpdateScheduler(
            interval_seconds=config.interval_seconds,
            missed_update_rate=missed_update_rate,
            seed=seed,
        )
        self.aoi_tracker = AoITracker(
            max_aoi_seconds=float(config.aoi.max_aoi_seconds)
            if config.aoi.max_aoi_seconds
            else None
        )
        self.policy: MissedUpdatePolicy = get_policy(config.missed_update_policy)
        self.divergence_tracker = StateDivergenceTracker()
        self.event_logger = SyncEventLogger(run_id=run_id, enabled=config.logging.enabled)

        # Internal state memory
        self._current_dt_state: DigitalTwinState | None = None
        self._previous_dt_state: DigitalTwinState | None = None
        self._last_successful_sync_time: float | None = None
        self._dt_timestamp: float | None = None
        self._missed_updates_count: int = 0
        self._step_counter: int = 0

    @property
    def current_aoi(self) -> float:
        """Current Age of Information in seconds."""
        return self.aoi_tracker.current_aoi

    @property
    def sync_age(self) -> float:
        """Time elapsed since last successful physical update in seconds."""
        return self.aoi_tracker.sync_age

    @property
    def peak_aoi(self) -> float:
        """Peak Age of Information observed so far in seconds."""
        return self.aoi_tracker.peak_aoi

    @property
    def average_aoi(self) -> float:
        """Time-average Age of Information in seconds."""
        return self.aoi_tracker.average_aoi

    @property
    def missed_updates_count(self) -> int:
        """Cumulative number of missed updates."""
        return self._missed_updates_count

    def step(
        self,
        physical_state: DigitalTwinState,
        current_time: float,
        generation_time: float | None = None,
        solver_time_ms: float = 0.0,
        inference_time_ms: float = 0.0,
    ) -> SynchronizationResult:
        """Process one synchronization step for the incoming physical state.

        Args:
            physical_state: Ground-truth physical grid state at current_time.
            current_time: Epoch or simulated wall-clock time in seconds.
            generation_time: Epoch time when measurement was generated at sensor (if None, current_time).
            solver_time_ms: Time spent running OpenDSS power flow for physical state in ms.
            inference_time_ms: Time spent running downstream inference in ms.

        Returns:
            SynchronizationResult containing active DT state, divergence, and staleness audit info.
        """
        is_due, is_successful = self.scheduler.check_update(
            current_time=current_time,
            last_sync_time=self._last_successful_sync_time,
        )

        gen_time = generation_time if generation_time is not None else current_time

        if is_successful:
            # Successful synchronization event: transfer physical state into DT
            self._previous_dt_state = self._current_dt_state
            self._current_dt_state = physical_state.model_copy(deep=True)
            self._last_successful_sync_time = current_time
            self._dt_timestamp = current_time
            self.aoi_tracker.record_update(current_time=current_time, generation_time=gen_time)

            is_stale = False
            policy_name = "none"
        else:
            # Synchronization missed or not scheduled
            self.aoi_tracker.evaluate_at(current_time=current_time)

            if is_due and not is_successful:
                self._missed_updates_count += 1

            # Apply missed update policy
            if self._current_dt_state is None:
                # Cold start fallback if first packet missed
                self._current_dt_state = physical_state.model_copy(deep=True)
                self._dt_timestamp = current_time
                policy_name = "none"
                is_stale = False
            else:
                elapsed_since_sync = (
                    current_time - self._last_successful_sync_time
                    if self._last_successful_sync_time is not None
                    else 0.0
                )
                self._current_dt_state = self.policy.apply(
                    last_known_state=self._current_dt_state,
                    previous_state=self._previous_dt_state,
                    dt_seconds=elapsed_since_sync,
                )
                policy_name = self.policy.name
                is_stale = True

        # Calculate divergence between ground truth physical state and virtual DT state
        divergence = self.divergence_tracker.compute_divergence(
            physical_state=physical_state,
            dt_state=self._current_dt_state,
        )

        # Build structured log record
        dt_ts = self._dt_timestamp if self._dt_timestamp is not None else current_time
        last_sync_ts = (
            self._last_successful_sync_time
            if self._last_successful_sync_time is not None
            else current_time
        )
        sync_age_val = max(0.0, current_time - last_sync_ts)

        log_record = SyncLogRecord(
            run_id=self.run_id,
            step_index=self._step_counter,
            physical_timestamp=current_time,
            dt_timestamp=dt_ts,
            last_sync_timestamp=last_sync_ts,
            sync_age_seconds=sync_age_val,
            aoi_seconds=self.aoi_tracker.current_aoi,
            update_interval_seconds=self.config.interval_seconds,
            update_successful=is_successful,
            is_stale=is_stale,
            missed_updates_count=self._missed_updates_count,
            solver_time_ms=solver_time_ms,
            inference_time_ms=inference_time_ms,
            residual_magnitude=divergence.l2_norm_divergence,
            policy_applied=policy_name,
        )

        self.event_logger.log_event(log_record)
        self._step_counter += 1

        return SynchronizationResult(
            dt_state=self._current_dt_state,
            is_stale=is_stale,
            sync_age_seconds=sync_age_val,
            aoi_seconds=self.aoi_tracker.current_aoi,
            divergence=divergence,
            update_successful=is_successful,
            policy_applied=policy_name,
            log_record=log_record,
        )

    def get_logs_dataframe(self) -> pd.DataFrame:
        """Export all logged events as a pandas DataFrame."""
        return self.event_logger.to_dataframe()

    def save_logs(self, file_path: Path | str) -> None:
        """Persist synchronization logs to JSONL or CSV file depending on extension.

        Args:
            file_path: Output file path (.jsonl or .csv).
        """
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            self.event_logger.save_csv(path)
        else:
            self.event_logger.save_jsonl(path)

    def reset(self, seed: int = 42) -> None:
        """Reset internal engine state and accumulators."""
        self._current_dt_state = None
        self._previous_dt_state = None
        self._last_successful_sync_time = None
        self._dt_timestamp = None
        self._missed_updates_count = 0
        self._step_counter = 0
        self.aoi_tracker.reset()
        self.scheduler.reset(seed=seed)
        self.divergence_tracker.reset()
        self.event_logger.clear()
