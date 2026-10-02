"""src/experiments/staleness_sweep.py — Primary execution engine for Experiment E5.

Systematically evaluates the effect of Digital Twin synchronization staleness (Delta t)
and stochastic packet loss (P_drop) on joint short-term load estimation and unsupervised
anomaly detection under the IEEE 33-bus benchmark feeder.

Governed by:
- 24-condition factorial matrix: Delta t in {0, 1, 5, 15, 60, 300} s x P_drop in {0.0, 0.05, 0.10, 0.20}
- Phase 4 SynchronizationEngine, UpdateScheduler, AoITracker, HoldLastStatePolicy
- Phase 5 Load Estimation models: Persistence, XGBoost, LSTM
- Phase 6 Anomaly Detectors: Isolation Forest, LSTM Autoencoder (Raw & Residual)
- Phase 7 Physics-based Residual Engine: r_t(Delta t) = y_t - y_hat_DT,t|t_sync
- Strict zero-leakage, temporal causality, and reproducibility manifests.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.anomaly_detection.isolation_forest import IsolationForestDetector
from src.anomaly_detection.lstm_autoencoder import LSTMAutoencoderDetector
from src.evaluation.anomaly_metrics import compute_anomaly_metrics
from src.evaluation.forecasting_metrics import compute_forecasting_metrics
from src.forecasting.features import prepare_forecasting_data
from src.forecasting.lstm_model import LSTMForecaster
from src.forecasting.persistence import PersistenceForecaster
from src.forecasting.xgboost_model import XGBoostForecaster
from src.residuals.calculator import calculate_residual
from src.residuals.experiment_e4 import get_baseline_dt_estimates
from src.residuals.features import ResidualFeatureConfig, ResidualFeatureExtractor
from src.residuals.normalizer import ResidualNormalizer
from src.synchronization.aoi import AoITracker
from src.synchronization.policies import HoldLastStatePolicy
from src.synchronization.scheduler import UpdateScheduler
from src.utils.config import E5ExperimentConfig, load_e5_config
from src.utils.io import ensure_dir, load_parquet, save_json, save_parquet
from src.utils.logging import get_logger
from src.utils.reproducibility import create_manifest, set_all_seeds

logger = get_logger("experiments.e5")


@dataclass(frozen=True)
class StalenessCondition:
    """Encapsulates a single experimental synchronization condition."""

    staleness_seconds: int
    packet_drop_rate: float
    seed: int = 42

    @property
    def condition_id(self) -> str:
        """Stable deterministic condition identifier."""
        p_drop_pct = int(round(self.packet_drop_rate * 100))
        return f"E5_DT{self.staleness_seconds}_PD{p_drop_pct:02d}_SEED{self.seed}"


@dataclass
class SynchronizationTrace:
    """Encapsulates the realized synchronization log and AoI statistics for a condition."""

    condition: StalenessCondition
    logs_df: pd.DataFrame
    aoi_statistics: dict[str, Any]
    stale_estimate_df: pd.DataFrame
    realized_aoi_array: np.ndarray


def simulate_synchronization_trace(
    condition: StalenessCondition,
    nominal_df: pd.DataFrame,
) -> SynchronizationTrace:
    """Generate the realized synchronization trace, AoI, and stale DT state under hold_last_state.

    For every simulation timestep t = 0, 1, ..., N-1:
    - Scheduler checks if an update is due and not dropped.
    - If successful, t_sync(t) = t and DT state is updated to nominal_df.iloc[t].
    - If dropped or not due, t_sync(t) = t_sync(t-1) and DT state is held from t_sync.
    - AoI(t) = t - t_sync(t) >= 0.

    Args:
        condition: StalenessCondition containing interval, drop rate, and seed.
        nominal_df: Clean nominal feeder telemetry DataFrame (35,040 timesteps).

    Returns:
        SynchronizationTrace with logs, AoI statistics, and stale estimates.
    """
    scheduler = UpdateScheduler(
        interval_seconds=condition.staleness_seconds,
        missed_update_rate=condition.packet_drop_rate,
        seed=condition.seed,
    )
    aoi_tracker = AoITracker()
    HoldLastStatePolicy()

    num_steps = len(nominal_df)
    stale_values = np.zeros_like(nominal_df.values)
    aoi_values = np.zeros(num_steps, dtype=np.float64)

    last_sync_time: float | None = None
    current_held_row: np.ndarray = nominal_df.values[0].copy()

    log_records: list[dict[str, Any]] = []
    scheduled_updates = 0
    successful_updates = 0
    dropped_updates = 0

    for step_idx in range(num_steps):
        t = float(step_idx)

        is_due, is_successful = scheduler.check_update(
            current_time=t,
            last_sync_time=last_sync_time,
        )

        if is_due:
            scheduled_updates += 1

        if is_successful:
            successful_updates += 1
            last_sync_time = t
            current_held_row = nominal_df.values[step_idx].copy()
            aoi_tracker.record_update(current_time=t, generation_time=t)
            packet_dropped = False
        else:
            if is_due:
                dropped_updates += 1
                packet_dropped = True
            else:
                packet_dropped = False

            aoi_tracker.evaluate_at(current_time=t)

        stale_values[step_idx] = current_held_row
        aoi_now = aoi_tracker.current_aoi
        aoi_values[step_idx] = aoi_now

        last_sync_ts = last_sync_time if last_sync_time is not None else 0.0

        log_records.append(
            {
                "condition_id": condition.condition_id,
                "step_index": step_idx,
                "physical_timestamp": t,
                "dt_timestamp": last_sync_ts,
                "last_successful_sync": last_sync_ts,
                "aoi_seconds": aoi_now,
                "scheduled_update": is_due,
                "successful_update": is_successful,
                "packet_dropped": packet_dropped,
                "staleness_seconds": condition.staleness_seconds,
                "packet_drop_rate": condition.packet_drop_rate,
                "seed": condition.seed,
            }
        )

    logs_df = pd.DataFrame(log_records)
    stale_df = pd.DataFrame(stale_values, index=nominal_df.index, columns=nominal_df.columns)

    # Realized AoI statistics
    actual_drop_rate = float(dropped_updates / scheduled_updates) if scheduled_updates > 0 else 0.0
    success_rate = float(successful_updates / scheduled_updates) if scheduled_updates > 0 else 1.0

    aoi_stats = {
        "condition_id": condition.condition_id,
        "staleness_seconds": condition.staleness_seconds,
        "packet_drop_rate": condition.packet_drop_rate,
        "mean_aoi": float(np.mean(aoi_values)),
        "median_aoi": float(np.median(aoi_values)),
        "std_aoi": float(np.std(aoi_values)),
        "min_aoi": float(np.min(aoi_values)),
        "max_aoi": float(np.max(aoi_values)),
        "p50_aoi": float(np.percentile(aoi_values, 50)),
        "p95_aoi": float(np.percentile(aoi_values, 95)),
        "p99_aoi": float(np.percentile(aoi_values, 99)),
        "scheduled_updates": scheduled_updates,
        "successful_updates": successful_updates,
        "dropped_updates": dropped_updates,
        "actual_drop_rate": actual_drop_rate,
        "update_success_rate": success_rate,
    }

    return SynchronizationTrace(
        condition=condition,
        logs_df=logs_df,
        aoi_statistics=aoi_stats,
        stale_estimate_df=stale_df,
        realized_aoi_array=aoi_values,
    )


class E5ExperimentCoordinator:
    """Coordinates offline baseline training and online stale execution across all 24 conditions."""

    def __init__(
        self,
        config: E5ExperimentConfig | None = None,
        config_path: Path | str = "configs/experiments/e5_staleness_sweep.yaml",
        seed: int = 42,
    ) -> None:
        """Initialize E5 experiment coordinator.

        Args:
            config: Optional pre-loaded E5ExperimentConfig instance.
            config_path: Path to configuration YAML.
            seed: Master random seed.
        """
        self.config = config or load_e5_config(config_path)
        self.seed = seed
        set_all_seeds(seed)

        self.data_path = Path("data/processed/load_profiles.parquet")
        self.labels_path = Path("data/processed/anomaly_labels.parquet")
        self.splits_path = Path("data/processed/splits.json")

        # Load shared datasets and splits
        self.df_feats = load_parquet(self.data_path)
        self.df_labels = load_parquet(self.labels_path)
        with open(self.splits_path, encoding="utf-8") as f:
            self.splits = json.load(f)

        self.train_idx = self.splits["train_indices"]
        self.val_idx = self.splits["validation_indices"]
        self.test_idx = self.splits["test_indices"]

        # 64 nodal electrical telemetry features
        self.elec_cols = [
            c
            for c in self.df_feats.columns
            if c.startswith("bus_") and (c.endswith("_p_kw") or c.endswith("_q_kvar"))
        ]
        if not self.elec_cols:
            self.elec_cols = [c for c in self.df_feats.columns if c != "timestamp"]

        self.observed_pwr = self.df_feats[self.elec_cols].copy()
        self.y_true_labels = self.df_labels["is_anomaly"].values.astype(int)

        # Baseline clean nominal DT estimate (Delta t = 0)
        logger.info("Generating baseline nominal DT estimate...")
        self.nominal_df = get_baseline_dt_estimates(seed=seed)[self.elec_cols].copy()

        # Frozen baseline models and thresholds
        self.frozen_models: dict[str, Any] = {}
        self.frozen_thresholds: dict[str, float] = {}
        self.frozen_normalizers: dict[str, Any] = {}
        self.feature_extractor: ResidualFeatureExtractor | None = None

        self._fit_baseline_models()

    def _fit_baseline_models(self) -> None:
        """Fit baseline detectors, forecasters, and normalizers on training split."""
        logger.info("Fitting baseline models under ideal synchronization (Delta t = 0)...")
        set_all_seeds(self.seed)

        # 1. Baseline Residual Engine (Delta t = 0)
        base_res_result = calculate_residual(
            observed=self.observed_pwr,
            dt_estimate=self.nominal_df,
            feature_names=self.elec_cols,
        )
        base_raw_res = base_res_result.values

        # Feature extractor matching E4 (direct 64 residual electrical features)
        feat_cfg = ResidualFeatureConfig(include_raw=True)
        self.feature_extractor = ResidualFeatureExtractor(config=feat_cfg)
        base_res_feats = self.feature_extractor.extract(base_raw_res)

        # Search for pre-trained Phase 7 E4 baseline artifacts
        e4_dir = None
        runs_dir = Path("experiments/runs")
        candidate_e4_dirs = [
            runs_dir / f"E4_RAW_VS_RESIDUAL_SEED{self.seed}_20260930",
            runs_dir / "E4_RAW_VS_RESIDUAL_SEED42_20260930",
        ]
        if runs_dir.exists():
            for p in sorted(runs_dir.glob("E4_RAW_VS_RESIDUAL_*"), reverse=True):
                if p.is_dir() and (p / "models" / "E4-3_lstm_autoencoder_raw.pt").exists():
                    if p not in candidate_e4_dirs:
                        candidate_e4_dirs.insert(0, p)

        for cand in candidate_e4_dirs:
            if cand.exists() and (cand / "models" / "E4-3_lstm_autoencoder_raw.pt").exists():
                e4_dir = cand
                break

        if e4_dir is not None:
            logger.info(f"Loading validated Phase 7 baseline models and normalizers from: {e4_dir}")
            models_dir = e4_dir / "models"
            if_raw = IsolationForestDetector.load(models_dir / "E4-1_isolation_forest_raw")
            if_res = IsolationForestDetector.load(models_dir / "E4-2_isolation_forest_residual")
            lstm_raw = LSTMAutoencoderDetector.load(models_dir / "E4-3_lstm_autoencoder_raw")
            lstm_res = LSTMAutoencoderDetector.load(models_dir / "E4-4_lstm_autoencoder_residual")
            res_normalizer = ResidualNormalizer.load(e4_dir / "residual_normalizer.json")

            self.frozen_models["if_raw"] = if_raw
            self.frozen_models["if_res"] = if_res
            self.frozen_models["lstm_raw"] = lstm_raw
            self.frozen_models["lstm_res"] = lstm_res

            self.frozen_thresholds["if_raw"] = float(if_raw.threshold)
            self.frozen_thresholds["if_res"] = float(if_res.threshold)
            self.frozen_thresholds["lstm_raw"] = float(lstm_raw.threshold)
            self.frozen_thresholds["lstm_res"] = float(lstm_res.threshold)
            self.frozen_normalizers["residual"] = res_normalizer
        else:
            logger.info("Fitting baseline anomaly detectors from scratch...")
            res_normalizer = ResidualNormalizer(method="z_score")
            res_normalizer.fit(base_res_feats[self.train_idx])
            self.frozen_normalizers["residual"] = res_normalizer

            norm_res_feats = res_normalizer.transform(base_res_feats)
            raw_telemetry = self.observed_pwr.values

            # IF Raw
            if_raw = IsolationForestDetector(contamination=0.05, random_state=self.seed)
            if_raw.fit(raw_telemetry[self.train_idx])
            val_scores_if_raw = if_raw.score_samples(raw_telemetry[self.val_idx])
            th_if_raw = float(np.percentile(val_scores_if_raw, 95.0))
            if_raw.set_threshold(th_if_raw)
            self.frozen_models["if_raw"] = if_raw
            self.frozen_thresholds["if_raw"] = th_if_raw

            # IF Residual
            if_res = IsolationForestDetector(contamination=0.05, random_state=self.seed)
            if_res.fit(norm_res_feats[self.train_idx])
            val_scores_if_res = if_res.score_samples(norm_res_feats[self.val_idx])
            th_if_res = float(np.percentile(val_scores_if_res, 95.0))
            if_res.set_threshold(th_if_res)
            self.frozen_models["if_res"] = if_res
            self.frozen_thresholds["if_res"] = th_if_res

            # LSTM-AE Raw
            lstm_raw = LSTMAutoencoderDetector(
                lookback_steps=24,
                encoder_units=[64, 32],
                latent_dim=16,
                decoder_units=[32, 64],
                epochs=50,
                patience=8,
                batch_size=64,
                learning_rate=0.001,
                seed=self.seed,
            )
            lstm_raw.fit(raw_telemetry[self.train_idx], X_val=raw_telemetry[self.val_idx])
            val_scores_lstm_raw = lstm_raw.score_samples(raw_telemetry[self.val_idx])
            th_lstm_raw = float(np.percentile(val_scores_lstm_raw, 95.0))
            lstm_raw.set_threshold(th_lstm_raw)
            self.frozen_models["lstm_raw"] = lstm_raw
            self.frozen_thresholds["lstm_raw"] = th_lstm_raw

            # LSTM-AE Residual
            lstm_res = LSTMAutoencoderDetector(
                lookback_steps=24,
                encoder_units=[64, 32],
                latent_dim=16,
                decoder_units=[32, 64],
                epochs=50,
                patience=8,
                batch_size=64,
                learning_rate=0.001,
                seed=self.seed,
            )
            lstm_res.fit(norm_res_feats[self.train_idx], X_val=norm_res_feats[self.val_idx])
            val_scores_lstm_res = lstm_res.score_samples(norm_res_feats[self.val_idx])
            th_lstm_res = float(np.percentile(val_scores_lstm_res, 95.0))
            lstm_res.set_threshold(th_lstm_res)
            self.frozen_models["lstm_res"] = lstm_res
            self.frozen_thresholds["lstm_res"] = th_lstm_res

        # 3. Fit Forecasting Models on Tabular and Sequence Splits
        target_name = self.config.forecasting.target_name
        tab_splits = prepare_forecasting_data(
            df=self.df_feats,
            splits=self.splits,
            lookback_steps=self.config.forecasting.lookback_steps,
            target_name=target_name,
            mode="tabular",
        )
        self.tab_splits = tab_splits

        # Persistence Forecaster
        pers_model = PersistenceForecaster(lag_feature_name="lag_1")
        pers_model.fit(
            X_train=tab_splits.X_train,
            y_train=tab_splits.y_train,
            feature_names=tab_splits.feature_names,
        )
        self.frozen_models["persistence"] = pers_model

        # XGBoost Forecaster
        xgb_model = XGBoostForecaster(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.05,
            random_state=self.seed,
            early_stopping_rounds=10,
        )
        xgb_model.fit(
            X_train=tab_splits.X_train,
            y_train=tab_splits.y_train,
            X_val=tab_splits.X_val,
            y_val=tab_splits.y_val,
            feature_names=tab_splits.feature_names,
        )
        self.frozen_models["xgboost"] = xgb_model

        # LSTM Forecaster
        seq_splits = prepare_forecasting_data(
            df=self.df_feats,
            splits=self.splits,
            lookback_steps=self.config.forecasting.lookback_steps,
            target_name=target_name,
            mode="sequence",
        )
        self.seq_splits = seq_splits

        lstm_forecast = LSTMForecaster(
            units=[64, 32],
            dropout=0.2,
            batch_size=32,
            epochs=20,
            patience=5,
            learning_rate=0.001,
            seed=self.seed,
        )
        lstm_forecast.fit(
            X_train=seq_splits.X_train,
            y_train=seq_splits.y_train,
            X_val=seq_splits.X_val,
            y_val=seq_splits.y_val,
            feature_names=seq_splits.feature_names,
        )
        self.frozen_models["lstm_forecast"] = lstm_forecast

        logger.info("Baseline models and thresholds successfully fitted and frozen.")

    def evaluate_condition(
        self,
        condition: StalenessCondition,
    ) -> tuple[dict[str, Any], dict[str, Any], pd.DataFrame, SynchronizationTrace]:
        """Execute full downstream evaluation for one synchronization condition.

        Args:
            condition: StalenessCondition to evaluate.

        Returns:
            Tuple of (forecasting_metrics_dict, anomaly_metrics_dict, pred_df, sync_trace).
        """
        logger.info(f"Evaluating Condition: {condition.condition_id}...")

        # 1. Generate synchronization trace and stale DT state
        sync_trace = simulate_synchronization_trace(
            condition=condition,
            nominal_df=self.nominal_df,
        )
        stale_dt_pwr = sync_trace.stale_estimate_df

        # 2. Compute Stale Residuals: r_t(Delta t) = y_t - y_hat_DT,t|t_sync
        res_result = calculate_residual(
            observed=self.observed_pwr,
            dt_estimate=stale_dt_pwr,
            feature_names=self.elec_cols,
        )
        raw_res = res_result.values

        # Residual diagnostics on test partition
        test_residuals = raw_res[self.test_idx]
        res_diagnostics = {
            "mean_residual": float(np.mean(test_residuals)),
            "mae_residual": float(np.mean(np.abs(test_residuals))),
            "rmse_residual": float(np.sqrt(np.mean(test_residuals**2))),
            "max_abs_residual": float(np.max(np.abs(test_residuals))),
        }

        # Extract and normalize residual features
        res_feats = self.feature_extractor.extract(raw_res)
        norm_res_feats = self.frozen_normalizers["residual"].transform(res_feats)

        # Slice test partition
        X_test_raw = self.observed_pwr.values[self.test_idx]
        X_test_res = norm_res_feats[self.test_idx]
        y_test_true = self.y_true_labels[self.test_idx]

        # 3. Anomaly Detection Evaluations
        anomaly_results: dict[str, Any] = {}
        pred_dict: dict[str, Any] = {
            "condition_id": [condition.condition_id] * len(self.test_idx),
            "step_index": self.test_idx,
            "aoi_seconds": sync_trace.realized_aoi_array[self.test_idx],
            "true_anomaly_label": y_test_true,
        }

        # 3.1 Raw + Isolation Forest
        scores_if_raw = self.frozen_models["if_raw"].score_samples(X_test_raw)
        th_if_raw = self.frozen_thresholds["if_raw"]
        y_pred_if_raw = (scores_if_raw >= th_if_raw).astype(int)
        m_if_raw = compute_anomaly_metrics(
            y_true=y_test_true,
            y_pred=y_pred_if_raw,
            scores=scores_if_raw,
        )
        m_if_raw["threshold"] = th_if_raw
        anomaly_results["if_raw"] = m_if_raw
        pred_dict["score_if_raw"] = scores_if_raw
        pred_dict["pred_if_raw"] = y_pred_if_raw

        # 3.2 Residual + Isolation Forest
        scores_if_res = self.frozen_models["if_res"].score_samples(X_test_res)
        th_if_res = self.frozen_thresholds["if_res"]
        y_pred_if_res = (scores_if_res >= th_if_res).astype(int)
        m_if_res = compute_anomaly_metrics(
            y_true=y_test_true,
            y_pred=y_pred_if_res,
            scores=scores_if_res,
        )
        m_if_res["threshold"] = th_if_res
        anomaly_results["if_res"] = m_if_res
        pred_dict["score_if_res"] = scores_if_res
        pred_dict["pred_if_res"] = y_pred_if_res

        # 3.3 Raw + LSTM Autoencoder
        scores_lstm_raw = self.frozen_models["lstm_raw"].score_samples(X_test_raw)
        th_lstm_raw = self.frozen_thresholds["lstm_raw"]
        y_pred_lstm_raw = (scores_lstm_raw >= th_lstm_raw).astype(int)
        m_lstm_raw = compute_anomaly_metrics(
            y_true=y_test_true,
            y_pred=y_pred_lstm_raw,
            scores=scores_lstm_raw,
        )
        m_lstm_raw["threshold"] = th_lstm_raw
        anomaly_results["lstm_raw"] = m_lstm_raw
        pred_dict["score_lstm_raw"] = scores_lstm_raw
        pred_dict["pred_lstm_raw"] = y_pred_lstm_raw

        # 3.4 Residual + LSTM Autoencoder
        scores_lstm_res = self.frozen_models["lstm_res"].score_samples(X_test_res)
        th_lstm_res = self.frozen_thresholds["lstm_res"]
        y_pred_lstm_res = (scores_lstm_res >= th_lstm_res).astype(int)
        m_lstm_res = compute_anomaly_metrics(
            y_true=y_test_true,
            y_pred=y_pred_lstm_res,
            scores=scores_lstm_res,
        )
        m_lstm_res["threshold"] = th_lstm_res
        anomaly_results["lstm_res"] = m_lstm_res
        pred_dict["score_lstm_res"] = scores_lstm_res
        pred_dict["pred_lstm_res"] = y_pred_lstm_res

        anomaly_results["residual_diagnostics"] = res_diagnostics

        # 4. Load Estimation (Forecasting) Evaluations
        # Target: Total feeder load in kW
        p_cols = [c for c in self.elec_cols if c.endswith("_p_kw")]
        total_p_true = self.df_feats[p_cols].sum(axis=1).values
        y_test_load = total_p_true[self.test_idx]
        pred_dict["true_total_load_kw"] = y_test_load

        # Under synchronization staleness, the DT only has telemetry up to t_sync.
        # Under hold_last_state, compute total load from held DT telemetry:
        stale_p_total = stale_dt_pwr[p_cols].sum(axis=1).values

        # 4. Load Estimation (Forecasting) Evaluations
        # Build stale feature DataFrame where telemetry reflects held state
        stale_df = self.df_feats.copy()
        stale_df["total_load_p_kw"] = stale_p_total

        stale_tab_splits = prepare_forecasting_data(
            df=stale_df,
            splits=self.splits,
            lookback_steps=self.config.forecasting.lookback_steps,
            target_name=self.config.forecasting.target_name,
            mode="tabular",
        )
        stale_seq_splits = prepare_forecasting_data(
            df=stale_df,
            splits=self.splits,
            lookback_steps=self.config.forecasting.lookback_steps,
            target_name=self.config.forecasting.target_name,
            mode="sequence",
        )

        y_true_tab = self.tab_splits.y_test
        y_true_seq = self.seq_splits.y_test

        y_pred_pers = self.frozen_models["persistence"].predict(stale_tab_splits.X_test)
        y_pred_xgb = self.frozen_models["xgboost"].predict(stale_tab_splits.X_test)
        y_pred_lstm = self.frozen_models["lstm_forecast"].predict(stale_seq_splits.X_test)

        forecasting_results: dict[str, Any] = {
            "persistence": compute_forecasting_metrics(y_true_tab, y_pred_pers),
            "xgboost": compute_forecasting_metrics(y_true_tab, y_pred_xgb),
            "lstm": compute_forecasting_metrics(y_true_seq, y_pred_lstm),
        }

        pred_dict["true_total_load_kw"] = y_true_tab
        pred_dict["pred_persistence_kw"] = y_pred_pers
        pred_dict["pred_xgboost_kw"] = y_pred_xgb
        # Sequence predictions align with end of lookback window; pad to match tabular length if needed
        if len(y_pred_lstm) < len(y_true_tab):
            diff = len(y_true_tab) - len(y_pred_lstm)
            pred_dict["pred_lstm_kw"] = np.concatenate([np.full(diff, y_pred_lstm[0]), y_pred_lstm])
        else:
            pred_dict["pred_lstm_kw"] = y_pred_lstm

        pred_df = pd.DataFrame(pred_dict)

        return forecasting_results, anomaly_results, pred_df, sync_trace


def run_staleness_sweep(
    config_path: Path | str = "configs/experiments/e5_staleness_sweep.yaml",
    seed: int = 42,
    output_base_dir: Path | str = "experiments/runs",
    coordinator: E5ExperimentCoordinator | None = None,
    conditions_to_run: list[StalenessCondition] | None = None,
    run_id: str | None = None,
    baseline_only: bool = False,
) -> Path:
    """Execute Experiment E5: Controlled Synchronization Staleness Sweep.

    Evaluates all 24 synchronization conditions (or specified subset),
    computes baseline-relative degradation, and saves comprehensive artifacts.

    Args:
        config_path: Path to experiment YAML config.
        seed: Master random seed.
        output_base_dir: Output base runs directory.
        coordinator: Optional pre-initialized E5ExperimentCoordinator.
        conditions_to_run: Optional subset of conditions to execute.
        run_id: Optional explicit run directory name.
        baseline_only: If True, execute only the baseline condition (Delta t = 0, P_drop = 0.0).

    Returns:
        Path to completed experiment run directory.
    """
    date_str = datetime.now().strftime("%Y%m%d")
    actual_run_id = run_id or f"E5_STALENESS_SWEEP_SEED{seed}_{date_str}"
    run_dir = Path(output_base_dir) / actual_run_id
    ensure_dir(run_dir)

    logger.info(f"Initializing Experiment E5: Staleness Sweep (Run ID: {actual_run_id})...")
    config = load_e5_config(config_path)

    if coordinator is None:
        coordinator = E5ExperimentCoordinator(config=config, seed=seed)

    # Build 24-condition matrix if not explicitly passed
    if conditions_to_run is None:
        if baseline_only:
            conditions = [StalenessCondition(staleness_seconds=0, packet_drop_rate=0.0, seed=seed)]
        else:
            conditions = []
            for interval in config.synchronization.intervals_seconds:
                for p_drop in config.synchronization.packet_drop_rates:
                    conditions.append(
                        StalenessCondition(
                            staleness_seconds=interval,
                            packet_drop_rate=p_drop,
                            seed=seed,
                        )
                    )
    else:
        conditions = conditions_to_run

    logger.info(f"Total conditions to evaluate: {len(conditions)}")

    all_forecasting_metrics: dict[str, Any] = {}
    all_anomaly_metrics: dict[str, Any] = {}
    all_aoi_stats: dict[str, Any] = {}
    all_sync_logs: list[pd.DataFrame] = []
    all_predictions: list[pd.DataFrame] = []
    comparison_rows: list[dict[str, Any]] = []

    # 1. First execute baseline condition (Delta t = 0, P_drop = 0.0)
    baseline_cond = StalenessCondition(staleness_seconds=0, packet_drop_rate=0.0, seed=seed)
    logger.info(f"Executing Baseline Condition: {baseline_cond.condition_id}...")
    b_fc, b_anom, b_preds, b_sync = coordinator.evaluate_condition(baseline_cond)

    baseline_fc_metrics = b_fc
    baseline_anom_metrics = b_anom

    # 2. Iterate through all experimental conditions
    for idx, cond in enumerate(conditions):
        logger.info(f"[{idx + 1}/{len(conditions)}] Running {cond.condition_id}...")
        if cond.staleness_seconds == 0 and cond.packet_drop_rate == 0.0:
            fc_res, anom_res, pred_df, sync_trace = b_fc, b_anom, b_preds, b_sync
        else:
            fc_res, anom_res, pred_df, sync_trace = coordinator.evaluate_condition(cond)

        all_forecasting_metrics[cond.condition_id] = fc_res
        all_anomaly_metrics[cond.condition_id] = anom_res
        all_aoi_stats[cond.condition_id] = sync_trace.aoi_statistics
        all_sync_logs.append(sync_trace.logs_df)
        all_predictions.append(pred_df)

        # Build comparison records for forecasting models
        for model_name, metrics in fc_res.items():
            for m_key, m_val in metrics.items():
                b_val = baseline_fc_metrics[model_name][m_key]
                abs_delta = m_val - b_val
                rel_deg = (abs_delta / b_val) if abs(b_val) > 1e-9 else 0.0
                comparison_rows.append(
                    {
                        "condition_id": cond.condition_id,
                        "staleness_seconds": cond.staleness_seconds,
                        "packet_drop_rate": cond.packet_drop_rate,
                        "realized_mean_aoi": sync_trace.aoi_statistics["mean_aoi"],
                        "realized_p95_aoi": sync_trace.aoi_statistics["p95_aoi"],
                        "task": "load_estimation",
                        "model": model_name,
                        "detector": "None",
                        "representation": "raw",
                        "metric": m_key,
                        "value": m_val,
                        "baseline_value": b_val,
                        "absolute_delta": abs_delta,
                        "relative_degradation": rel_deg,
                        "status": "SUCCESS",
                    }
                )

        # Build comparison records for anomaly detection
        for det_key in ["if_raw", "if_res", "lstm_raw", "lstm_res"]:
            det_name, rep = det_key.split("_")
            det_full = "isolation_forest" if det_name == "if" else "lstm_autoencoder"
            rep_full = "raw" if rep == "raw" else "residual"
            metrics = anom_res[det_key]

            for m_key, m_val in metrics.items():
                if isinstance(m_val, (int, float)):
                    b_val = baseline_anom_metrics[det_key][m_key]
                    # Higher is better for precision, recall, f1, pr_auc, roc_auc
                    if m_key in ["f1", "pr_auc", "roc_auc", "precision", "recall"]:
                        abs_delta = m_val - b_val
                        # Degradation magnitude D = b_val - m_val
                        deg_mag = b_val - m_val
                        rel_deg = (deg_mag / b_val) if abs(b_val) > 1e-9 else 0.0
                    else:
                        # FPR or latency (lower is better)
                        abs_delta = m_val - b_val
                        rel_deg = (abs_delta / b_val) if abs(b_val) > 1e-9 else 0.0

                    comparison_rows.append(
                        {
                            "condition_id": cond.condition_id,
                            "staleness_seconds": cond.staleness_seconds,
                            "packet_drop_rate": cond.packet_drop_rate,
                            "realized_mean_aoi": sync_trace.aoi_statistics["mean_aoi"],
                            "realized_p95_aoi": sync_trace.aoi_statistics["p95_aoi"],
                            "task": "anomaly_detection",
                            "model": "None",
                            "detector": det_full,
                            "representation": rep_full,
                            "metric": m_key,
                            "value": m_val,
                            "baseline_value": b_val,
                            "absolute_delta": abs_delta,
                            "relative_degradation": rel_deg,
                            "status": "SUCCESS",
                        }
                    )

    # 3. Save Artifacts
    logger.info("Persisting experiment artifacts...")

    # 3.1 AoI statistics JSON
    save_json(all_aoi_stats, run_dir / "aoi_statistics.json")

    # 3.2 Metrics JSON
    hierarchical_metrics = {
        "experiment": "E5",
        "seed": seed,
        "baseline_condition": baseline_cond.condition_id,
        "synchronization": all_aoi_stats,
        "forecasting": all_forecasting_metrics,
        "anomaly_detection": all_anomaly_metrics,
    }
    save_json(hierarchical_metrics, run_dir / "metrics.json")

    # 3.3 Comparison CSV
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df.to_csv(run_dir / "comparison.csv", index=False)

    # 3.4 Synchronization Logs Parquet
    combined_sync_logs = pd.concat(all_sync_logs, ignore_index=True)
    save_parquet(combined_sync_logs, run_dir / "synchronization_logs.parquet")

    # 3.5 Predictions Parquet
    combined_preds = pd.concat(all_predictions, ignore_index=True)
    save_parquet(combined_preds, run_dir / "predictions.parquet")

    # 3.6 Configuration Snapshot
    with open(run_dir / "config_snapshot.yaml", "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2))

    # 3.7 Reproducibility Manifest
    manifest_data = create_manifest(
        experiment_id=config.experiment.id,
        run_id=run_id,
        config_file=str(config_path),
        config_version=config.experiment.version,
        random_seed=seed,
        synchronization_interval=0,
        missed_update_policy=config.synchronization.missed_update_policy,
        input_representation="raw_and_residual",
        model_type="multi_model_suite",
        dataset_version="v1.0",
        extra_metadata={
            "experiment_name": config.experiment.name,
            "conditions_count": len(conditions),
            "intervals_seconds": config.synchronization.intervals_seconds,
            "packet_drop_rates": config.synchronization.packet_drop_rates,
            "dataset_info": {
                "description": "IEEE 33-bus benchmark feeder hybrid simulation dataset",
                "resolution_minutes": 15,
                "total_timesteps": len(coordinator.df_feats),
                "test_timesteps": len(coordinator.test_idx),
                "test_anomalies": int(np.sum(coordinator.y_true_labels[coordinator.test_idx])),
            },
            "output_files": [
                "manifest.json",
                "config_snapshot.yaml",
                "aoi_statistics.json",
                "metrics.json",
                "comparison.csv",
                "synchronization_logs.parquet",
                "predictions.parquet",
                "summary.md",
            ],
        },
    )
    save_json(manifest_data, run_dir / "manifest.json")

    # 3.8 Summary Markdown
    _generate_summary_markdown(
        run_dir=run_dir,
        run_id=run_id,
        seed=seed,
        conditions=conditions,
        all_aoi_stats=all_aoi_stats,
        comparison_df=comparison_df,
    )

    logger.info(f"Experiment E5 completed successfully. Run directory: {run_dir}")
    return run_dir


def _generate_summary_markdown(
    run_dir: Path,
    run_id: str,
    seed: int,
    conditions: list[StalenessCondition],
    all_aoi_stats: dict[str, Any],
    comparison_df: pd.DataFrame,
) -> None:
    """Generate high-level summary report for Experiment E5."""
    summary_lines = [
        "# Experiment E5: Controlled Synchronization Staleness Sweep — Summary Report",
        "",
        f"- **Run ID:** `{run_id}`",
        f"- **Execution Timestamp:** `{datetime.now().isoformat()}`",
        f"- **Random Seed:** `{seed}`",
        f"- **Total Conditions Executed:** `{len(conditions)}`",
        "",
        "## 1. Synchronization & Realized Age of Information (AoI) Table",
        "",
        "| Staleness (s) | P_drop | Scheduled Updates | Successful Updates | Dropped Updates | Actual Drop Rate | Mean AoI (s) | P95 AoI (s) | Max AoI (s) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for cond in conditions:
        st = all_aoi_stats[cond.condition_id]
        summary_lines.append(
            f"| {cond.staleness_seconds} | {cond.packet_drop_rate:.2f} | {st['scheduled_updates']} | "
            f"{st['successful_updates']} | {st['dropped_updates']} | {st['actual_drop_rate']:.4f} | "
            f"{st['mean_aoi']:.2f} | {st['p95_aoi']:.2f} | {st['max_aoi']:.2f} |"
        )

    summary_lines.extend(
        [
            "",
            "## 2. Key Performance Degradation Overview",
            "",
            "### Anomaly Detection F1-Score vs. Synchronization Condition",
            "",
        ]
    )

    f1_df = comparison_df[comparison_df["metric"] == "f1"]
    if not f1_df.empty:
        pivot_f1 = f1_df.pivot_table(
            index=["staleness_seconds", "packet_drop_rate"],
            columns=["detector", "representation"],
            values="value",
        )
        summary_lines.append(pivot_f1.to_markdown())

    summary_lines.extend(
        [
            "",
            "### Load Forecasting MAPE (%) vs. Synchronization Condition",
            "",
        ]
    )

    mape_df = comparison_df[comparison_df["metric"] == "mape"]
    if not mape_df.empty:
        pivot_mape = mape_df.pivot_table(
            index=["staleness_seconds", "packet_drop_rate"],
            columns="model",
            values="value",
        )
        summary_lines.append(pivot_mape.to_markdown())

    with open(run_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))
