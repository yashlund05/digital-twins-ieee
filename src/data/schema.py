"""
src/data/schema.py — Pydantic schemas for data pipeline validation.

Defines schemas for raw data ingestion, feeder bus mappings, temporal splits,
anomaly annotations, and overall data pipeline manifests.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BusMappingInfo(BaseModel):
    """Metadata describing the mapping of residential profiles to a single IEEE 33 bus."""

    bus_id: int = Field(..., ge=2, le=33, description="IEEE 33-bus load bus index (2 to 33)")
    nominal_p_kw: float = Field(
        ..., ge=0.0, description="Baran & Wu (1989) benchmark nominal active load (kW)"
    )
    nominal_q_kvar: float = Field(
        ..., ge=0.0, description="Baran & Wu (1989) benchmark nominal reactive load (kVAR)"
    )
    assigned_homes: list[int] = Field(
        ..., min_length=1, description="List of Pecan Street dataids assigned to this bus"
    )
    scaling_factor: float = Field(
        ..., gt=0.0, description="Scaling multiplier applied to aggregated home profile"
    )


class MappingConfigSummary(BaseModel):
    """Authoritative summary of the IEEE 33-bus mapping configuration."""

    topology: str = Field(default="ieee_33_bus", description="Network feeder topology identifier")
    num_load_buses: int = Field(default=32, ge=1, description="Number of active load buses")
    slack_bus_id: int = Field(default=1, description="Substation/slack bus identifier")
    total_nominal_p_kw: float = Field(
        default=3715.0, description="Total active load at nominal rating (kW)"
    )
    total_nominal_q_kvar: float = Field(
        default=2300.0, description="Total reactive load at nominal rating (kVAR)"
    )
    bus_mappings: dict[int, BusMappingInfo] = Field(..., description="Mapping for each load bus")
    random_seed: int = Field(..., description="Random seed used to generate deterministic mapping")


class AnomalyEvent(BaseModel):
    """Record describing a synthetically injected anomaly event."""

    event_id: str = Field(..., description="Unique anomaly event identifier")
    fault_type: str = Field(
        ..., description="Type of fault: voltage_sag, load_spike, phase_imbalance"
    )
    target_buses: list[int] = Field(..., min_length=1, description="Buses subjected to the anomaly")
    start_index: int = Field(..., ge=0, description="Integer timestep index start (inclusive)")
    end_index: int = Field(..., ge=0, description="Integer timestep index end (exclusive)")
    duration_timesteps: int = Field(..., gt=0, description="Duration in discrete timesteps")
    magnitude: float = Field(..., description="Relative multiplier or absolute perturbation value")
    start_timestamp: str = Field(..., description="ISO 8601 start timestamp in UTC")
    end_timestamp: str = Field(..., description="ISO 8601 end timestamp in UTC")

    @field_validator("end_index")
    @classmethod
    def validate_end_after_start(cls, v: int, info: Any) -> int:
        """Validate that end_index is strictly greater than start_index."""
        start = info.data.get("start_index")
        if start is not None and v <= start:
            raise ValueError(f"end_index ({v}) must be strictly greater than start_index ({start})")
        return v


class TemporalSplitIndices(BaseModel):
    """Strict temporal split indices preventing future leakage."""

    train_indices: list[int] = Field(
        ..., min_length=1, description="Chronological training indices"
    )
    validation_indices: list[int] = Field(
        ..., min_length=1, description="Chronological validation indices"
    )
    test_indices: list[int] = Field(..., min_length=1, description="Chronological testing indices")
    temporal: bool = Field(default=True, description="Strictly temporal (ordered) splitting")
    leak_free: bool = Field(
        default=True, description="True if train < val < test condition verified"
    )

    @field_validator("leak_free")
    @classmethod
    def verify_no_temporal_leakage(cls, v: bool, info: Any) -> bool:
        """Enforce that max(train) < min(val) and max(val) < min(test)."""
        train = info.data.get("train_indices")
        val = info.data.get("validation_indices")
        test = info.data.get("test_indices")
        if train and val and test:
            if max(train) >= min(val):
                raise ValueError(
                    "Temporal leakage detected: max(train_indices) >= min(validation_indices)"
                )
            if max(val) >= min(test):
                raise ValueError(
                    "Temporal leakage detected: max(validation_indices) >= min(test_indices)"
                )
        return True


class NormalizationParameters(BaseModel):
    """Per-bus normalization parameters computed strictly on the training partition."""

    method: str = Field(default="min_max", description="Normalization method: min_max or z_score")
    train_start_index: int = Field(..., ge=0)
    train_end_index: int = Field(..., ge=0)
    bus_params: dict[str, dict[str, float]] = Field(
        ...,
        description="Per-bus parameters (e.g. min, max, mean, std) computed strictly from training split",
    )


class DataPipelineManifest(BaseModel):
    """Complete manifest generated after running the Phase 2 data pipeline."""

    pipeline_version: str = Field(default="0.2.0")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    raw_source: str = Field(..., description="Path or description of raw source dataset")
    total_timesteps: int = Field(..., gt=0, description="Total number of 15-minute intervals")
    resolution_minutes: int = Field(default=15, description="Sampling interval in minutes")
    start_time: str = Field(..., description="ISO 8601 start timestamp in UTC")
    end_time: str = Field(..., description="ISO 8601 end timestamp in UTC")
    num_load_buses: int = Field(default=32)
    num_anomalies_injected: int = Field(..., ge=0)
    anomaly_rate: float = Field(..., ge=0.0, le=1.0)
    split_counts: dict[str, int] = Field(..., description="Number of timesteps per split")
    git_commit: str = Field(default="unknown")
    dataset_designation: str = Field(
        default="HYBRID_SIMULATION_DATASET",
        description="Explicit notice that this is a hybrid simulation, not IEEE field data",
    )
