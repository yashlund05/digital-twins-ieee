"""src/publication/schemas.py — Schemas and data models for Phase 12 publication artifacts."""

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class SourceRunConfig(BaseModel):
    """Configuration definition for a single frozen source run."""

    path: str
    frozen: bool = True
    description: str = ""


class PublicationMetaConfig(BaseModel):
    """Publication target metadata."""

    target: str = "IEEE Transactions on Smart Grid"
    feeder: str = "IEEE 33-Bus Radial Benchmark Feeder"
    dataset: str = "Pecan Street Dataport"
    seeds: list[int] = Field(default_factory=lambda: [42, 123, 456, 789, 101112])
    staleness_seconds: list[int] = Field(default_factory=lambda: [0, 1, 5, 15, 60, 300])
    packet_drop_rates: list[float] = Field(default_factory=lambda: [0.00, 0.05, 0.10, 0.20])
    detectors: list[str] = Field(default_factory=lambda: ["isolation_forest", "lstm_autoencoder"])
    representations: list[str] = Field(default_factory=lambda: ["raw", "residual"])
    forecasters: list[str] = Field(default_factory=lambda: ["persistence", "xgboost", "lstm"])


class Phase12Config(BaseModel):
    """Master Phase 12 configuration model."""

    source_runs: dict[str, SourceRunConfig]
    publication: PublicationMetaConfig = Field(default_factory=PublicationMetaConfig)
    output: dict[str, str] = Field(
        default_factory=lambda: {"root": "experiments/runs/E12_PUBLICATION_ARTIFACTS_20261002"}
    )
    integrity: dict[str, Any] = Field(
        default_factory=lambda: {
            "verify_source_hashes": True,
            "fail_on_missing_source": True,
            "fail_on_schema_mismatch": True,
            "reproducibility_tolerance": 1.0e-5,
        }
    )


@dataclass
class FigureProvenanceRecord:
    """Provenance record tracking how a publication figure was derived."""

    figure_id: str
    figure_title: str
    source_runs: list[str]
    source_files: list[str]
    transformation_pipeline: list[str]
    random_seed: int | None
    generated_at: str
    png_path: str
    pdf_path: str
    source_csv_path: str
    source_hashes: dict[str, str] = field(default_factory=dict)
    output_hashes: dict[str, str] = field(default_factory=dict)


@dataclass
class TableProvenanceRecord:
    """Provenance record tracking how a publication table was derived."""

    table_id: str
    table_title: str
    source_runs: list[str]
    source_files: list[str]
    transformation_pipeline: list[str]
    row_count: int
    column_count: int
    generated_at: str
    csv_path: str
    tex_path: str
    source_hashes: dict[str, str] = field(default_factory=dict)
    output_hashes: dict[str, str] = field(default_factory=dict)
