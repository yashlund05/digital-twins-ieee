"""
src/synchronization/logger.py — Synchronization event logging and schema definition.

Provides structured logging for every synchronization event in accordance with
docs/architecture/SYNCHRONIZATION_ENGINE.md line 140. Enables downstream analysis of
synchronization staleness, Age of Information, and residual divergence.
"""

import json
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger("synchronization.logger")


class SyncLogRecord(BaseModel):
    """Schema for individual synchronization event logs."""

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique event UUID"
    )
    run_id: str = Field(default="dev_run", description="Experiment run identifier")
    step_index: int = Field(default=0, ge=0, description="Discrete simulation time step index")
    physical_timestamp: float = Field(
        ..., description="Wall-clock or epoch time of physical measurement"
    )
    dt_timestamp: float = Field(..., description="Timestamp of the state currently held in the DT")
    last_sync_timestamp: float = Field(
        ..., description="Timestamp of the last successful sync update"
    )
    sync_age_seconds: float = Field(
        ..., ge=0.0, description="Staleness age: physical_time - last_sync_time"
    )
    aoi_seconds: float = Field(
        ..., ge=0.0, description="Age of Information: physical_time - packet_generation_time"
    )
    update_interval_seconds: int = Field(
        ..., ge=0, description="Configured nominal sync interval (Delta t_sync)"
    )
    update_successful: bool = Field(..., description="Whether a fresh physical update was applied")
    is_stale: bool = Field(..., description="True if sync_age_seconds > 0 or update was missed")
    missed_updates_count: int = Field(
        default=0, ge=0, description="Cumulative count of missed updates"
    )
    solver_time_ms: float = Field(
        default=0.0, ge=0.0, description="OpenDSS solver runtime in milliseconds"
    )
    inference_time_ms: float = Field(default=0.0, ge=0.0, description="ML inference runtime in ms")
    residual_magnitude: float = Field(
        default=0.0, ge=0.0, description="L2 norm of physical-DT residual divergence"
    )
    policy_applied: str = Field(
        default="hold_last_state", description="Policy applied ('none', 'hold_last_state', etc.)"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert record to dictionary."""
        return self.model_dump()


class SyncEventLogger:
    """Manages the recording, in-memory buffering, and persistence of synchronization logs."""

    def __init__(self, run_id: str = "dev_run", enabled: bool = True) -> None:
        """Initialize the synchronization event logger.

        Args:
            run_id: Unique experiment run identifier.
            enabled: Whether event logging is active.
        """
        self.run_id = run_id
        self.enabled = enabled
        self._records: list[SyncLogRecord] = []

    def log_event(self, record: SyncLogRecord) -> None:
        """Record a synchronization event.

        Args:
            record: Validated SyncLogRecord instance.
        """
        if not self.enabled:
            return
        self._records.append(record)

    @property
    def records(self) -> list[SyncLogRecord]:
        """List of logged records."""
        return list(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all logged records to a pandas DataFrame."""
        if not self._records:
            return pd.DataFrame()
        return pd.DataFrame([r.to_dict() for r in self._records])

    def save_jsonl(self, file_path: Path | str) -> None:
        """Save logged events to a JSON Lines file.

        Args:
            file_path: Target path for the .jsonl file.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for record in self._records:
                f.write(json.dumps(record.to_dict()) + "\n")
        logger.info(f"Saved {len(self._records)} synchronization logs to {path}")

    def save_csv(self, file_path: Path | str) -> None:
        """Save logged events to a CSV file.

        Args:
            file_path: Target path for the .csv file.
        """
        df = self.to_dataframe()
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"Saved {len(df)} synchronization log rows to {path}")

    def get_summary_statistics(self) -> dict[str, float]:
        """Compute key summary statistics across all logged events.

        Returns:
            Dictionary with mean_aoi, max_aoi, mean_sync_age, max_sync_age,
            total_events, fresh_updates, stale_events, missed_updates.
        """
        if not self._records:
            return {}

        df = self.to_dataframe()
        return {
            "total_events": float(len(df)),
            "fresh_updates": float((df["update_successful"] & ~df["is_stale"]).sum()),
            "stale_events": float(df["is_stale"].sum()),
            "total_missed_updates": float(
                df["missed_updates_count"].iloc[-1] if not df.empty else 0
            ),
            "mean_aoi_seconds": float(df["aoi_seconds"].mean()),
            "max_aoi_seconds": float(df["aoi_seconds"].max()),
            "mean_sync_age_seconds": float(df["sync_age_seconds"].mean()),
            "max_sync_age_seconds": float(df["sync_age_seconds"].max()),
            "mean_residual_magnitude": float(df["residual_magnitude"].mean()),
            "max_residual_magnitude": float(df["residual_magnitude"].max()),
        }

    def clear(self) -> None:
        """Clear all logged events from memory."""
        self._records.clear()
