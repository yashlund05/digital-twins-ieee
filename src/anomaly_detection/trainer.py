"""
src/anomaly_detection/trainer.py — Unsupervised anomaly detection training coordinator.

Orchestrates unsupervised model training, validation score threshold calibration,
and unbiased test set evaluation across Isolation Forest and LSTM Autoencoder.
Enforces that no anomaly labels are seen during model fitting.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.anomaly_detection.detector import BaseAnomalyDetector
from src.anomaly_detection.isolation_forest import IsolationForestDetector
from src.anomaly_detection.lstm_autoencoder import LSTMAutoencoderDetector
from src.anomaly_detection.thresholds import get_threshold_selector
from src.evaluation.anomaly_metrics import compute_anomaly_metrics
from src.utils.config import AnomalyDetectionConfig, load_anomaly_detection_config
from src.utils.io import load_parquet
from src.utils.logging import get_logger
from src.utils.reproducibility import set_all_seeds

logger = get_logger("anomaly_detection.trainer")


@dataclass
class AnomalyEvaluationResult:
    """Stores evaluation metrics and predictions for an anomaly detector."""

    detector_name: str
    split_name: str
    input_representation: str
    threshold: float
    metrics: dict[str, float]
    scores: np.ndarray
    y_pred: np.ndarray
    y_true: np.ndarray


class AnomalyDetectionTrainer:
    """Coordinates unsupervised anomaly detector fitting, thresholding, and evaluation."""

    def __init__(
        self,
        config: AnomalyDetectionConfig | None = None,
        data_path: Path | str = "data/processed/load_profiles.parquet",
        labels_path: Path | str = "data/processed/anomaly_labels.parquet",
        splits_path: Path | str = "data/processed/splits.json",
        seed: int = 42,
    ) -> None:
        """Initialize anomaly detection trainer.

        Args:
            config: AnomalyDetectionConfig instance or None (loads from yaml).
            data_path: Path to processed load profiles parquet.
            labels_path: Path to anomaly labels parquet.
            splits_path: Path to splits.json.
            seed: Master random seed.
        """
        self.config = config or load_anomaly_detection_config()
        self.data_path = Path(data_path)
        self.labels_path = Path(labels_path)
        self.splits_path = Path(splits_path)
        self.seed = seed

        self.trained_detectors: dict[str, BaseAnomalyDetector] = {}
        self.evaluation_results: list[AnomalyEvaluationResult] = []

    def prepare_data(
        self,
        input_representation: str = "raw",
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], list[str]]:
        """Extract features and labels strictly aligned with dataset splits.

        Args:
            input_representation: 'raw' (load profiles) or 'residual'.

        Returns:
            Tuple of (features_dict, labels_dict, event_ids_dict, feature_names).
        """
        df_feats = load_parquet(self.data_path)
        df_labels = load_parquet(self.labels_path)

        with open(self.splits_path, encoding="utf-8") as f:
            splits = json.load(f)

        # Select continuous electrical telemetry features (32 P + 32 Q bus quantities)
        elec_cols = [
            c for c in df_feats.columns if c.startswith("bus_") and ("_p_kw" in c or "_q_kvar" in c)
        ]
        if not elec_cols:
            elec_cols = [c for c in df_feats.columns if c not in ["timestamp"]]

        X_all = df_feats[elec_cols].values.astype(np.float32)
        y_all = df_labels["is_anomaly"].values.astype(np.int32)
        events_all = df_labels["event_id"].values

        def _map_indices(idx_list: list[Any]) -> list[int]:
            if not idx_list:
                return []
            if isinstance(idx_list[0], int):
                return idx_list
            # Map timestamps to integer row indices
            ts_to_row = {ts: r for r, ts in enumerate(df_feats.index)}
            return [ts_to_row[ts] for ts in idx_list if ts in ts_to_row]

        train_rows = _map_indices(splits["train_indices"])
        val_rows = _map_indices(splits["validation_indices"])
        test_rows = _map_indices(splits["test_indices"])

        features = {
            "train": X_all[train_rows],
            "val": X_all[val_rows],
            "test": X_all[test_rows],
        }
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

        return features, labels, events, elec_cols

    def train_and_evaluate_all(
        self,
        detectors_to_run: list[str] | None = None,
        input_representation: str = "raw",
    ) -> tuple[dict[str, BaseAnomalyDetector], pd.DataFrame]:
        """Train detectors unsupervised, tune threshold on val, and evaluate on test."""
        set_all_seeds(self.seed)
        selected = detectors_to_run or self.config.detectors
        features, labels, events, feat_names = self.prepare_data(input_representation)

        # Threshold selector factory
        th_selector = get_threshold_selector(
            method=self.config.threshold.method,
            percentile=self.config.threshold.percentile,
        )

        for det_name in selected:
            logger.info(f"=== Training Detector: {det_name.upper()} (Unsupervised) ===")
            if det_name == "isolation_forest":
                detector = IsolationForestDetector(
                    config=self.config.isolation_forest,
                    random_state=self.seed,
                )
                # Fit strictly without labels
                detector.fit(features["train"], feature_names=feat_names)

                # Calibrate threshold on validation split scores (unsupervised)
                val_scores = detector.score_samples(features["val"])
                optimal_threshold = th_selector.fit(val_scores)
                detector.set_threshold(optimal_threshold)

                # Evaluate on Validation
                val_pred = detector.predict(features["val"])
                val_metrics = compute_anomaly_metrics(
                    y_true=labels["val"],
                    y_pred=val_pred,
                    scores=val_scores,
                    event_ids=events["val"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="val",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=val_metrics,
                        scores=val_scores,
                        y_pred=val_pred,
                        y_true=labels["val"],
                    )
                )

                # Evaluate on Test
                test_scores = detector.score_samples(features["test"])
                test_pred = detector.predict(features["test"])
                test_metrics = compute_anomaly_metrics(
                    y_true=labels["test"],
                    y_pred=test_pred,
                    scores=test_scores,
                    event_ids=events["test"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="test",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=test_metrics,
                        scores=test_scores,
                        y_pred=test_pred,
                        y_true=labels["test"],
                    )
                )
                self.trained_detectors[det_name] = detector

            elif det_name == "lstm_autoencoder":
                detector = LSTMAutoencoderDetector(
                    config=self.config.lstm_autoencoder,
                    seed=self.seed,
                )
                detector.fit(features["train"], X_val=features["val"], feature_names=feat_names)

                # Calibrate threshold on validation split scores
                val_scores = detector.score_samples(features["val"])
                optimal_threshold = th_selector.fit(val_scores)
                detector.set_threshold(optimal_threshold)

                val_pred = detector.predict(features["val"])
                val_metrics = compute_anomaly_metrics(
                    y_true=labels["val"],
                    y_pred=val_pred,
                    scores=val_scores,
                    event_ids=events["val"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="val",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=val_metrics,
                        scores=val_scores,
                        y_pred=val_pred,
                        y_true=labels["val"],
                    )
                )

                test_scores = detector.score_samples(features["test"])
                test_pred = detector.predict(features["test"])
                test_metrics = compute_anomaly_metrics(
                    y_true=labels["test"],
                    y_pred=test_pred,
                    scores=test_scores,
                    event_ids=events["test"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="test",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=test_metrics,
                        scores=test_scores,
                        y_pred=test_pred,
                        y_true=labels["test"],
                    )
                )
                self.trained_detectors[det_name] = detector

        comparison_df = self.get_comparison_dataframe()
        return self.trained_detectors, comparison_df

    def get_comparison_dataframe(self) -> pd.DataFrame:
        """Format evaluation results into a summary DataFrame."""
        rows = []
        for r in self.evaluation_results:
            rows.append(
                {
                    "detector": r.detector_name,
                    "split": r.split_name,
                    "input": r.input_representation,
                    "threshold": r.threshold,
                    "precision": r.metrics["precision"],
                    "recall": r.metrics["recall"],
                    "f1": r.metrics["f1"],
                    "pr_auc": r.metrics["pr_auc"],
                    "roc_auc": r.metrics["roc_auc"],
                    "fpr": r.metrics["false_positive_rate"],
                    "latency_steps": r.metrics["detection_latency"],
                }
            )
        return pd.DataFrame(rows)

    def save_detectors(self, output_dir: Path | str) -> None:
        """Save trained detector weights and thresholds."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, det in self.trained_detectors.items():
            det.save(out / name)
        logger.info(f"Saved {len(self.trained_detectors)} detectors to {out}")
