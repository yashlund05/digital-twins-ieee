"""
src/residuals/experiment_e4.py — Execution script for Experiment E4: Raw vs. Residual Inputs.

Executes the 2x2 factorial design under ideal baseline synchronization (Delta t_sync = 0):
    Condition E4-1: Raw + Isolation Forest
    Condition E4-2: Residual + Isolation Forest
    Condition E4-3: Raw + LSTM Autoencoder
    Condition E4-4: Residual + LSTM Autoencoder

Enforces strict zero-leakage:
- Train-only residual normalization
- Unsupervised detector training (no labels seen during fit)
- 95th percentile validation threshold calibration (never test labels)
- Comprehensive reproducibility manifests and artifact preservation in experiments/runs/.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.anomaly_detection.isolation_forest import IsolationForestDetector
from src.anomaly_detection.lstm_autoencoder import LSTMAutoencoderDetector
from src.anomaly_detection.thresholds import get_threshold_selector
from src.data.loader import generate_benchmark_residential_traces, load_pecan_street_csv
from src.data.mapper import map_homes_to_ieee33
from src.data.schema import NormalizationParameters
from src.evaluation.anomaly_metrics import compute_anomaly_metrics
from src.residuals.calculator import calculate_residual
from src.residuals.features import ResidualFeatureConfig, ResidualFeatureExtractor
from src.residuals.normalizer import ResidualNormalizer
from src.utils.config import (
    AnomalyDetectionConfig,
    load_anomaly_detection_config,
    load_data_config,
)
from src.utils.io import ensure_dir, load_json, load_parquet, save_json, save_parquet
from src.utils.logging import get_logger
from src.utils.reproducibility import create_manifest, set_all_seeds

logger = get_logger("residuals.experiment_e4")


def get_baseline_dt_estimates(
    config_path: Path | str = "configs/data.yaml",
    norm_params_path: Path | str = "data/interim/normalization_params.json",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate the unperturbed Digital Twin nominal load estimates y_hat_DT,t.

    Under ideal baseline synchronization (Delta t = 0), the Digital Twin maintains
    the clean nominal feeder load profile before synthetic anomaly perturbation.

    Args:
        config_path: Path to data configuration YAML.
        norm_params_path: Path to fitted normalization parameters JSON.
        seed: Random seed matching the data generation process.

    Returns:
        DataFrame containing clean nominal electrical load profiles matching load_profiles.parquet.
    """
    cfg = load_data_config(config_path)

    # Ingest clean raw or benchmark data matching pipeline.py
    raw_candidate = Path("data/raw/15minute_data_austin.csv")
    if not raw_candidate.exists():
        alt_candidate = Path("data/raw/pecan_street.csv")
        if alt_candidate.exists():
            raw_candidate = alt_candidate

    if raw_candidate.exists():
        start_date = cfg.source.pecan_street.date_range.start
        end_date = cfg.source.pecan_street.date_range.end
        date_tuple = (start_date, end_date) if (start_date or end_date) else None
        home_matrix = load_pecan_street_csv(
            filepath=raw_candidate,
            load_column="grid",
            date_range=date_tuple,
            home_ids=cfg.source.pecan_street.homes,
        )
    else:
        home_matrix = generate_benchmark_residential_traces(
            num_homes=25,
            num_days=365,
            resolution_minutes=cfg.source.pecan_street.resolution_minutes,
            seed=seed,
        )

    # Clean unperturbed profiles mapped to IEEE 33-bus
    active_df, reactive_df, _ = map_homes_to_ieee33(home_matrix, seed=seed)
    clean_pwr = pd.concat([active_df, reactive_df], axis=1)

    # Normalize using the exact training parameters from Phase 2
    if Path(norm_params_path).exists():
        with open(norm_params_path, encoding="utf-8") as f:
            norm_dict = json.load(f)
        norm_params = NormalizationParameters.model_validate(norm_dict)

        clean_norm = clean_pwr.copy()
        for col in clean_pwr.columns:
            if col in norm_params.bus_params:
                p = norm_params.bus_params[col]
                # min_max normalization
                clean_norm[col] = (clean_norm[col] - p["min"]) / (p["max"] - p["min"] + 1e-8)
        return clean_norm

    return clean_pwr


def run_experiment_e4(
    seed: int = 42,
    output_base_dir: Path | str = "experiments/runs",
    data_path: Path | str = "data/processed/load_profiles.parquet",
    labels_path: Path | str = "data/processed/anomaly_labels.parquet",
    splits_path: Path | str = "data/processed/splits.json",
    detectors: list[str] | None = None,
    normalization_method: str = "z_score",
    feature_config: ResidualFeatureConfig | None = None,
) -> Path:
    """Execute Experiment E4: Raw vs. Residual Inputs (2x2 Factorial Design).

    Args:
        seed: Random seed for reproducibility.
        output_base_dir: Base directory for run artifacts.
        data_path: Path to processed load profiles parquet.
        labels_path: Path to anomaly labels parquet.
        splits_path: Path to temporal splits JSON.
        detectors: Optional list of detectors to run ('isolation_forest', 'lstm_autoencoder').
        normalization_method: Normalization strategy for residuals ('z_score', 'min_max', 'robust').
        feature_config: Optional ResidualFeatureConfig for residual feature extraction.

    Returns:
        Path to completed experiment run directory.
    """
    set_all_seeds(seed)
    date_str = datetime.now().strftime("%Y%m%d")
    run_id = f"E4_RAW_VS_RESIDUAL_SEED{seed}_{date_str}"
    run_dir = Path(output_base_dir) / run_id
    ensure_dir(run_dir)
    models_dir = run_dir / "models"
    ensure_dir(models_dir)

    logger.info(f"Starting Experiment E4: Raw vs. Residual Inputs (Run ID: {run_id})...")

    # 1. Load Configurations
    config: AnomalyDetectionConfig = load_anomaly_detection_config()
    selected_detectors = detectors or config.detectors

    # 2. Ingest Data and Split Partitions
    df_feats = load_parquet(data_path)
    df_labels = load_parquet(labels_path)
    splits = load_json(splits_path)

    train_rows = splits["train_indices"]
    val_rows = splits["validation_indices"]
    test_rows = splits["test_indices"]

    # Continuous electrical load telemetry columns (64 features: 32 P + 32 Q)
    elec_cols = [
        c
        for c in df_feats.columns
        if c.startswith("bus_") and (c.endswith("_p_kw") or c.endswith("_q_kvar"))
    ]
    if not elec_cols:
        elec_cols = [c for c in df_feats.columns if c not in ["timestamp"]]

    y_all = df_labels["is_anomaly"].values.astype(np.int32)
    events_all = df_labels["event_id"].values

    labels = {
        "train": y_all[train_rows],
        "val": y_all[val_rows],
        "test": y_all[test_rows],
    }
    events = {
        "train": events_all[train_rows],
        "val": events_all[val_rows],
        "test": events_all[test_rows],
    }

    # 3. Prepare Raw Representation (Phase 6 equivalent)
    X_raw_all = df_feats[elec_cols].values.astype(np.float32)
    raw_features = {
        "train": X_raw_all[train_rows],
        "val": X_raw_all[val_rows],
        "test": X_raw_all[test_rows],
    }

    # 4. Prepare Residual Representation (Physics-based r_t = y_t - y_hat_DT,t)
    logger.info("Computing physics-based Digital Twin residuals for E4...")
    df_dt_clean = get_baseline_dt_estimates(seed=seed)

    # Use pure residual calculator
    res_result = calculate_residual(
        observed=df_feats[elec_cols],
        dt_estimate=df_dt_clean[elec_cols],
        physical_timestamps=list(df_feats.index),
        dt_sync_timestamps=list(df_feats.index),
        aoi_seconds=0.0,
        feature_names=elec_cols,
    )
    raw_residuals_df = res_result.raw_residual
    save_parquet(raw_residuals_df, run_dir / "raw_residuals.parquet")

    # Train-only residual normalization (Zero Leakage)
    normalizer = ResidualNormalizer(method=normalization_method)
    train_res_raw = raw_residuals_df.iloc[train_rows].values
    normalizer.fit(train_res_raw, feature_names=elec_cols)
    normalizer.save(run_dir / "residual_normalizer.json")

    norm_res_train = normalizer.transform(raw_residuals_df.iloc[train_rows].values)
    norm_res_val = normalizer.transform(raw_residuals_df.iloc[val_rows].values)
    norm_res_test = normalizer.transform(raw_residuals_df.iloc[test_rows].values)

    # Feature extraction (default: direct normalized residuals)
    feat_cfg = feature_config or ResidualFeatureConfig(include_raw=True)
    extractor = ResidualFeatureExtractor(config=feat_cfg)

    residual_features = {
        "train": extractor.extract(norm_res_train).astype(np.float32),
        "val": extractor.extract(norm_res_val).astype(np.float32),
        "test": extractor.extract(norm_res_test).astype(np.float32),
    }

    # Save feature configuration
    save_json(feat_cfg.model_dump(), run_dir / "feature_config.json")

    # 5. Define 2x2 Factorial Conditions
    conditions = [
        ("E4-1", "isolation_forest", "raw"),
        ("E4-2", "isolation_forest", "residual"),
        ("E4-3", "lstm_autoencoder", "raw"),
        ("E4-4", "lstm_autoencoder", "residual"),
    ]

    # Filter to selected detectors
    conditions = [c for c in conditions if c[1] in selected_detectors]

    th_selector = get_threshold_selector(
        method=config.threshold.method,
        percentile=config.threshold.percentile,
    )

    comparison_rows = []
    metrics_summary: dict[str, dict[str, Any]] = {}
    predictions_dict: dict[str, Any] = {"y_true": labels["test"]}

    # 6. Execute Experimental Conditions
    for cond_id, det_name, rep_name in conditions:
        logger.info(f"=== Running Condition {cond_id}: {rep_name.upper()} + {det_name.upper()} ===")
        feats = raw_features if rep_name == "raw" else residual_features

        # Initialize detector
        if det_name == "isolation_forest":
            detector = IsolationForestDetector(
                config=config.isolation_forest,
                random_state=seed,
            )
            # Train unsupervised (strictly no labels)
            detector.fit(feats["train"], feature_names=elec_cols)

            # Threshold calibration on validation scores
            val_scores = detector.score_samples(feats["val"])
            threshold = th_selector.fit(val_scores)
            detector.set_threshold(threshold)

            # Test evaluation
            test_scores = detector.score_samples(feats["test"])
            test_pred = detector.predict(feats["test"])

        elif det_name == "lstm_autoencoder":
            detector = LSTMAutoencoderDetector(
                config=config.lstm_autoencoder,
                seed=seed,
            )
            # Train unsupervised on sequence reconstructions
            detector.fit(feats["train"], X_val=feats["val"], feature_names=elec_cols)

            val_scores = detector.score_samples(feats["val"])
            threshold = th_selector.fit(val_scores)
            detector.set_threshold(threshold)

            test_scores = detector.score_samples(feats["test"])
            test_pred = detector.predict(feats["test"])

        else:
            raise ValueError(f"Unknown detector '{det_name}'.")

        # Save trained detector weights and threshold
        detector.save(models_dir / f"{cond_id}_{det_name}_{rep_name}")

        # Compute evaluation metrics on validation and test
        val_pred = (val_scores >= threshold).astype(int)
        val_metrics = compute_anomaly_metrics(
            y_true=labels["val"],
            y_pred=val_pred,
            scores=val_scores,
            event_ids=events["val"],
        )
        test_metrics = compute_anomaly_metrics(
            y_true=labels["test"],
            y_pred=test_pred,
            scores=test_scores,
            event_ids=events["test"],
        )

        # Store test predictions
        predictions_dict[f"score_{cond_id}"] = list(test_scores)
        predictions_dict[f"pred_{cond_id}"] = list(test_pred)

        # Build comparison summary row
        comparison_rows.append(
            {
                "condition": cond_id,
                "detector": det_name,
                "representation": rep_name,
                "threshold": float(threshold),
                "precision": test_metrics["precision"],
                "recall": test_metrics["recall"],
                "f1": test_metrics["f1"],
                "pr_auc": test_metrics["pr_auc"],
                "roc_auc": test_metrics["roc_auc"],
                "fpr": test_metrics["false_positive_rate"],
                "latency_steps": test_metrics["detection_latency"],
                "test_samples": int(len(labels["test"])),
                "true_anomalies": int(np.sum(labels["test"])),
                "pred_anomalies": int(np.sum(test_pred)),
            }
        )

        metrics_summary[cond_id] = {
            "detector": det_name,
            "representation": rep_name,
            "threshold": float(threshold),
            "validation": val_metrics,
            "test": test_metrics,
        }

    # 7. Persist Artifacts
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(run_dir / "comparison.csv", index=False)
    save_json(metrics_summary, run_dir / "metrics.json")

    pred_df = pd.DataFrame(predictions_dict)
    save_parquet(pred_df, run_dir / "predictions.parquet")

    # 8. Create Human-Readable summary.md
    headers = list(comparison_df.columns)
    table_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in comparison_df.iterrows():
        vals = [f"{v:.4f}" if isinstance(v, float) else str(v) for v in row]
        table_lines.append("| " + " | ".join(vals) + " |")
    table_md = "\n".join(table_lines)

    summary_lines = [
        "# Experiment E4: Raw vs. Residual Inputs — Summary",
        "",
        f"- **Run ID:** `{run_id}`",
        f"- **Date:** {datetime.now().isoformat()}",
        f"- **Random Seed:** {seed}",
        "- **Synchronization Interval:** 0 s (Baseline Level 0 — Perfect Synchronization)",
        f"- **Residual Normalization:** {normalization_method}",
        f"- **Threshold Strategy:** {config.threshold.method} ({config.threshold.percentile}th percentile)",
        "- **Training Protocol:** Unsupervised (zero anomaly labels seen during fit)",
        "",
        "## 2x2 Factorial Baseline Results",
        "",
        table_md,
        "",
        "## Scientific Notes",
        "- All four conditions evaluated on identical test split partitions (Nov 7 - Dec 31, 2018).",
        "- Normalization parameters fitted strictly on training partition with zero future leakage.",
        "- Decision thresholds calibrated strictly on validation scores (never test split).",
        "- Raw residuals preserved in `raw_residuals.parquet` without hidden smoothing or filtering.",
    ]
    with open(run_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")

    # 9. Create Reproducibility Manifest
    manifest = create_manifest(
        experiment_id="E4",
        run_id=run_id,
        config_file="configs/anomaly_detection.yaml",
        config_version="1.0.0",
        random_seed=seed,
        synchronization_interval=0,
        missed_update_policy="hold_last_state",
        input_representation="raw_vs_residual_factorial",
        model_type="isolation_forest_and_lstm_autoencoder",
        dataset_version="v1.0",
    )
    # Add E4-specific metadata
    manifest["e4_metadata"] = {
        "conditions": [c[0] for c in conditions],
        "normalization_method": normalization_method,
        "feature_config": feat_cfg.model_dump(),
        "ideal_sync": True,
        "staleness_interval_seconds": 0,
    }
    save_json(manifest, run_dir / "manifest.json")

    logger.info(f"Experiment E4 completed successfully! All artifacts written to {run_dir}")
    return run_dir


if __name__ == "__main__":
    run_experiment_e4()
