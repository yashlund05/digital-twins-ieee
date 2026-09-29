"""
src/anomaly_detection/experiment_e3.py — Execution script for Experiment E3: Anomaly Detection Baselines.

Trains and validates unsupervised anomaly detectors (Isolation Forest, LSTM Autoencoder)
under ideal baseline conditions (perfect synchronization, Delta t_sync = 0).
Logs reproducibility manifests, metrics, predictions, and model artifacts to experiments/runs/.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.anomaly_detection.trainer import AnomalyDetectionTrainer
from src.utils.config import load_anomaly_detection_config
from src.utils.io import ensure_dir, save_json, save_parquet
from src.utils.logging import get_logger
from src.utils.reproducibility import create_manifest

logger = get_logger("experiments.e3")


def run_experiment_e3(
    seed: int = 42,
    output_base_dir: Path | str = "experiments/runs",
    detectors: list[str] | None = None,
    input_representation: str = "raw",
) -> Path:
    """Execute Experiment E3: Anomaly Detection Baselines under perfect synchronization.

    Args:
        seed: Random seed for reproducibility.
        output_base_dir: Base directory for run artifacts.
        detectors: Optional list of detectors to run.
        input_representation: 'raw' or 'residual'.

    Returns:
        Path to completed run directory.
    """
    date_str = datetime.now().strftime("%Y%m%d")
    run_id = f"E3_BASELINE_ANOMALY_DETECTION_SEED{seed}_{date_str}"
    run_dir = Path(output_base_dir) / run_id
    ensure_dir(run_dir)
    models_dir = run_dir / "models"
    ensure_dir(models_dir)

    logger.info(f"Starting Experiment E3: Anomaly Detection Baselines (Run ID: {run_id})...")
    config = load_anomaly_detection_config()

    trainer = AnomalyDetectionTrainer(config=config, seed=seed)
    trained_detectors, comparison_df = trainer.train_and_evaluate_all(
        detectors_to_run=detectors,
        input_representation=input_representation,
    )

    # 1. Save model weights
    trainer.save_detectors(models_dir)

    # 2. Extract and save test set predictions
    test_results = [r for r in trainer.evaluation_results if r.split_name == "test"]
    pred_dict: dict[str, Any] = {}
    if test_results:
        pred_dict["y_true"] = test_results[0].y_true
        for r in test_results:
            pred_dict[f"score_{r.detector_name}"] = list(r.scores)
            pred_dict[f"pred_{r.detector_name}"] = list(r.y_pred)

        pred_df = pd.DataFrame(pred_dict)
        save_parquet(pred_df, run_dir / "predictions.parquet")

    # 3. Save metrics JSON and CSV
    metrics_summary: dict[str, dict[str, Any]] = {}
    for r in trainer.evaluation_results:
        if r.detector_name not in metrics_summary:
            metrics_summary[r.detector_name] = {}
        metrics_summary[r.detector_name][r.split_name] = {
            "threshold": r.threshold,
            **r.metrics,
        }

    save_json(metrics_summary, run_dir / "metrics.json")
    comparison_df.to_csv(run_dir / "comparison.csv", index=False)

    # 4. Generate summary.md table
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
        "# Experiment E3: Anomaly Detection Baselines — Summary",
        "",
        f"- **Run ID:** `{run_id}`",
        f"- **Date:** {datetime.now().isoformat()}",
        f"- **Random Seed:** {seed}",
        f"- **Input Representation:** {input_representation}",
        "- **Training Mode:** Unsupervised (zero labels seen during training)",
        "- **Synchronization Interval:** 0 s (Level 0 — Perfect Synchronization)",
        f"- **Thresholding Strategy:** {config.threshold.method} ({config.threshold.percentile}th percentile)",
        "",
        "## Baseline Anomaly Detection Performance",
        "",
        table_md,
        "",
        "## Research Governance Notes",
        "- Detectors trained in strictly unsupervised fashion per research protocol.",
        "- Decision thresholds selected strictly on validation split scores (never test split).",
        "- All performance metrics reported without test-set tuning.",
    ]
    with open(run_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")

    # 5. Create reproducibility manifest
    manifest = create_manifest(
        experiment_id="E3",
        run_id=run_id,
        config_file="configs/anomaly_detection.yaml",
        config_version="1.0.0",
        random_seed=seed,
        synchronization_interval=0,
        missed_update_policy="hold_last_state",
        input_representation=input_representation,
        model_type="multi_detector_baseline",
        dataset_version="v1.0",
    )
    save_json(manifest, run_dir / "manifest.json")

    logger.info(f"Experiment E3 completed successfully! Artifacts written to {run_dir}")
    return run_dir


if __name__ == "__main__":
    run_experiment_e3()
