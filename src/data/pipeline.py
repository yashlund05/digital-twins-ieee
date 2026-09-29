"""
src/data/pipeline.py — Master orchestrator for the Phase 2 Data Pipeline.

Executes the full data lifecycle:
1. Raw Pecan Street CSV ingestion (with benchmark generator fallback).
2. Cleaning, 15-minute resampling, and missing value imputation.
3. Feeder topology mapping to IEEE 33-bus load nodes (Baran & Wu 1989).
4. Feature engineering (temporal harmonics and autoregressive lags).
5. Controlled synthetic anomaly injection with isolated ground-truth labels.
6. Chronological 70/15/15 temporal splitting with zero future leakage.
7. Training-only normalization.
8. Persisting final Parquet datasets and JSON manifests.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.data.anomaly_injector import inject_synthetic_anomalies
from src.data.loader import generate_benchmark_residential_traces, load_pecan_street_csv
from src.data.mapper import map_homes_to_ieee33
from src.data.preprocessor import (
    clean_and_resample,
    extract_lag_features,
    extract_temporal_features,
    fit_and_apply_normalization,
)
from src.data.schema import DataPipelineManifest
from src.data.splitter import compute_temporal_splits, get_split_date_ranges
from src.utils.config import load_data_config
from src.utils.io import ensure_dir, save_json, save_parquet
from src.utils.logging import get_logger
from src.utils.reproducibility import get_git_commit, set_all_seeds

logger = get_logger("data.pipeline")


def run_pipeline(
    config_path: Path | str = "configs/data.yaml",
    raw_data_path: Path | str | None = None,
    output_dir: Path | str = "data/processed",
    interim_dir: Path | str = "data/interim",
    seed_override: int | None = None,
) -> dict[str, Any]:
    """Execute the end-to-end Phase 2 data pipeline.

    Args:
        config_path: Path to data configuration YAML.
        raw_data_path: Path to raw Pecan Street CSV. If None, checks default locations.
        output_dir: Directory where processed datasets and splits are saved.
        interim_dir: Directory where mapping and normalization configs are saved.
        seed_override: Optional seed overriding config settings.

    Returns:
        Dictionary containing manifest and status summary.
    """
    logger.info("Initializing Phase 2 Data Preparation Pipeline")

    # Load configuration
    cfg = load_data_config(config_path)
    seed = seed_override if seed_override is not None else cfg.anomaly_injection.seed
    set_all_seeds(seed)

    out_path = Path(output_dir)
    int_path = Path(interim_dir)
    ensure_dir(out_path)
    ensure_dir(int_path)

    # 1. Ingest raw data
    raw_candidate = (
        Path(raw_data_path) if raw_data_path else Path("data/raw/15minute_data_austin.csv")
    )
    if not raw_candidate.exists():
        # Check alternative common filename
        alt_candidate = Path("data/raw/pecan_street.csv")
        if alt_candidate.exists():
            raw_candidate = alt_candidate

    if raw_candidate.exists():
        logger.info("Found raw Pecan Street dataset on disk", extra={"path": str(raw_candidate)})
        start_date = cfg.source.pecan_street.date_range.start
        end_date = cfg.source.pecan_street.date_range.end
        date_tuple = (start_date, end_date) if (start_date or end_date) else None
        home_matrix = load_pecan_street_csv(
            filepath=raw_candidate,
            load_column="gross",
            date_range=date_tuple,
            home_ids=cfg.source.pecan_street.homes,
        )
        source_label = f"Pecan Street Austin CSV ({raw_candidate.name})"
    else:
        logger.warning(
            "Raw CSV not found in data/raw/. Generating synthetic benchmark residential traces matching Pecan Street statistics",
            extra={"path": str(raw_candidate)},
        )
        home_matrix = generate_benchmark_residential_traces(
            num_homes=25,
            num_days=365,
            resolution_minutes=cfg.source.pecan_street.resolution_minutes,
            seed=seed,
        )
        source_label = "Synthetic Benchmark Residential Traces (Pecan Street distribution matching)"

    # 2. Resample and clean
    cleaned_homes = clean_and_resample(
        home_matrix,
        resolution_minutes=cfg.source.pecan_street.resolution_minutes,
        max_gap_minutes=cfg.preprocessing.max_gap_minutes,
    )

    # 3. Feeder Mapping to IEEE 33-bus (ADR-0005: tracked assignment, re-anchored)
    active_df, reactive_df, mapping_summary = map_homes_to_ieee33(
        cleaned_homes,
        seed=seed,
        homes_per_bus=2,
        assignment_path=cfg.mapping.assignment_file,
        anchor=cfg.mapping.anchor,
        alpha=cfg.mapping.alpha,
        cap_multiple=cfg.mapping.cap_multiple,
    )
    save_json(mapping_summary.model_dump(), int_path / "mapping_config.json")

    # 4. Synthetic Anomaly Injection
    train_end_idx = int(cfg.splits.train_ratio * len(active_df))
    if cfg.anomaly_injection.enabled:
        inj_active_df, inj_reactive_df, labels_df, events = inject_synthetic_anomalies(
            active_power_df=active_df,
            reactive_power_df=reactive_df,
            anomaly_rate=cfg.anomaly_injection.anomaly_rate,
            fault_types=cfg.anomaly_injection.fault_types,
            duration_timesteps=cfg.anomaly_injection.duration_timesteps,
            train_end_idx=train_end_idx,
            seed=cfg.anomaly_injection.seed,
        )
    else:
        inj_active_df = active_df.copy()
        inj_reactive_df = reactive_df.copy()
        labels_df = pd.DataFrame(
            {
                "is_anomaly": 0,
                "anomaly_type": "none",
                "severity": "none",
                "target_buses": "none",
                "affected_buses": "none",
                "realized_ratio_kw": 1.0,
                "effect_size_sigma": 0.0,
                "event_id": "none",
            },
            index=active_df.index,
        )
        events = []

    # 5. Feature Engineering
    temporal_features = extract_temporal_features(active_df.index)
    lag_features = extract_lag_features(inj_active_df, lags=[1, 24, 96])

    # Combine into unified feature matrix
    # Bus active and reactive power columns
    power_features = pd.concat([inj_active_df, inj_reactive_df], axis=1)
    combined_features = pd.concat([power_features, temporal_features, lag_features], axis=1)

    # 6. Temporal Splitting (70% Train, 15% Validation, 15% Test)
    total_steps = len(combined_features)
    splits = compute_temporal_splits(
        total_timesteps=total_steps,
        train_ratio=cfg.splits.train_ratio,
        validation_ratio=cfg.splits.validation_ratio,
        test_ratio=cfg.splits.test_ratio,
    )
    date_ranges = get_split_date_ranges(active_df.index, splits)

    splits_data = {
        "train_indices": splits.train_indices,
        "validation_indices": splits.validation_indices,
        "test_indices": splits.test_indices,
        "date_ranges": date_ranges,
        "temporal": True,
        "leak_free": True,
        "ratios": {
            "train": cfg.splits.train_ratio,
            "validation": cfg.splits.validation_ratio,
            "test": cfg.splits.test_ratio,
        },
    }
    save_json(splits_data, out_path / "splits.json")

    # 7. Normalization (Strictly fit on unperturbed pre-injection training split)
    if cfg.preprocessing.normalize:
        # Construct pre-injection combined feature dataframe to fit scaler without synthetic contamination
        pre_inj_power = pd.concat([active_df, reactive_df], axis=1)
        pre_inj_lags = extract_lag_features(active_df, lags=[1, 24, 96])
        pre_inj_combined = pd.concat([pre_inj_power, temporal_features, pre_inj_lags], axis=1)

        norm_cols = list(power_features.columns) + list(lag_features.columns)
        normalized_df, norm_params = fit_and_apply_normalization(
            combined_features,
            feature_columns=norm_cols,
            train_indices=splits.train_indices,
            method=cfg.preprocessing.normalization_method,
            fit_df=pre_inj_combined,
        )
        save_json(norm_params.model_dump(), int_path / "normalization_params.json")
    else:
        normalized_df = combined_features.copy()

    # 8. Persist Processed Artifacts
    # Include physical unnormalized loads (bus_{id}_p_kw_phys, bus_{id}_q_kvar_phys)
    phys_features = power_features.copy()
    phys_features.columns = [f"{c}_phys" for c in phys_features.columns]
    full_output_df = pd.concat([normalized_df, phys_features], axis=1)

    # Save processed features matrix and separate anomaly labels
    save_parquet(full_output_df, out_path / "load_profiles.parquet")
    save_parquet(labels_df, out_path / "anomaly_labels.parquet")

    # 9. Pipeline Manifest
    commit_hash = get_git_commit() or "uncommitted"
    manifest = DataPipelineManifest(
        pipeline_version="0.2.0",
        raw_source=source_label,
        total_timesteps=total_steps,
        resolution_minutes=cfg.source.pecan_street.resolution_minutes,
        start_time=active_df.index.min().isoformat(),
        end_time=active_df.index.max().isoformat(),
        num_load_buses=cfg.network.num_load_buses,
        num_anomalies_injected=len(events),
        anomaly_rate=float(labels_df["is_anomaly"].mean()),
        split_counts={
            "train": len(splits.train_indices),
            "validation": len(splits.validation_indices),
            "test": len(splits.test_indices),
        },
        git_commit=commit_hash,
    )
    save_json(manifest.model_dump(), out_path / "manifest.json")

    logger.info(
        "Data Pipeline executed successfully",
        extra={"total_timesteps": total_steps, "output_dir": str(out_path)},
    )

    return {
        "status": "success",
        "manifest": manifest.model_dump(),
        "splits": date_ranges,
        "processed_files": [
            str(out_path / "load_profiles.parquet"),
            str(out_path / "anomaly_labels.parquet"),
            str(out_path / "splits.json"),
            str(out_path / "manifest.json"),
            str(int_path / "mapping_config.json"),
        ],
    }
