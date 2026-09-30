"""
tests/integration/test_residual_pipeline.py — Integration tests for Phase 7 Residual Pipeline and E4.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.anomaly_detection.isolation_forest import IsolationForestDetector
from src.anomaly_detection.lstm_autoencoder import LSTMAutoencoderDetector
from src.residuals.calculator import calculate_residual
from src.residuals.experiment_e4 import get_baseline_dt_estimates, run_experiment_e4
from src.residuals.features import ResidualFeatureConfig, ResidualFeatureExtractor
from src.residuals.normalizer import ResidualNormalizer
from src.utils.config import IsolationForestConfig, LSTMAutoencoderConfig
from src.utils.io import load_json, load_parquet


@pytest.fixture(scope="module")
def prepared_data():
    """Verify processed parquet and splits exist before running integration tests."""
    data_path = Path("data/processed/load_profiles.parquet")
    labels_path = Path("data/processed/anomaly_labels.parquet")
    splits_path = Path("data/processed/splits.json")

    if not (data_path.exists() and labels_path.exists() and splits_path.exists()):
        pytest.skip("Processed dataset artifacts not found in data/processed/")

    return {
        "df_feats": load_parquet(data_path),
        "df_labels": load_parquet(labels_path),
        "splits": load_json(splits_path),
    }


def test_end_to_end_residual_pipeline(prepared_data):
    """Verify full pipeline: observation + estimate -> residual -> normalizer -> features -> detectors."""
    df_feats = prepared_data["df_feats"].iloc[:500]  # Fast slice for integration test
    splits = prepared_data["splits"]

    # Use first 300 for train, 100 for val, 100 for test
    train_idx = list(range(300))
    val_idx = list(range(300, 400))
    test_idx = list(range(400, 500))

    elec_cols = [
        c
        for c in df_feats.columns
        if c.startswith("bus_") and (c.endswith("_p_kw") or c.endswith("_q_kvar"))
    ]
    assert len(elec_cols) == 64

    # Generate baseline estimate
    df_dt = get_baseline_dt_estimates().iloc[:500]

    # 1. Raw residual calculation
    res_result = calculate_residual(
        observed=df_feats[elec_cols],
        dt_estimate=df_dt[elec_cols],
        physical_timestamps=list(df_feats.index),
        dt_sync_timestamps=list(df_feats.index),
        aoi_seconds=0.0,
    )
    assert res_result.raw_residual.shape == (500, 64)

    # 2. Train-only normalization (Zero Leakage)
    normalizer = ResidualNormalizer(method="z_score")
    train_res = res_result.raw_residual.iloc[train_idx].values
    normalizer.fit(train_res, feature_names=elec_cols)

    norm_train = normalizer.transform(res_result.raw_residual.iloc[train_idx].values)
    norm_val = normalizer.transform(res_result.raw_residual.iloc[val_idx].values)
    norm_test = normalizer.transform(res_result.raw_residual.iloc[test_idx].values)

    np.testing.assert_allclose(np.mean(norm_train, axis=0), 0.0, atol=1e-7)

    # 3. Feature extraction (direct + absolute)
    cfg = ResidualFeatureConfig(include_raw=True, include_absolute=True)
    extractor = ResidualFeatureExtractor(config=cfg)

    feat_train = extractor.extract(norm_train).astype(np.float32)
    feat_val = extractor.extract(norm_val).astype(np.float32)
    feat_test = extractor.extract(norm_test).astype(np.float32)

    assert feat_train.shape == (300, 128)  # 64 direct + 64 absolute

    # 4. Detector consumption: Isolation Forest
    if_config = IsolationForestConfig(n_estimators=10, random_state=42)
    if_detector = IsolationForestDetector(config=if_config, random_state=42)
    if_detector.fit(feat_train)

    val_scores = if_detector.score_samples(feat_val)
    assert val_scores.shape == (100,)
    assert not np.isnan(val_scores).any()

    # 5. Detector consumption: LSTM Autoencoder
    lstm_config = LSTMAutoencoderConfig(
        encoder_units=[16],
        latent_dim=8,
        decoder_units=[16],
        lookback_steps=8,
        epochs=1,
        batch_size=16,
        seed=42,
    )
    lstm_detector = LSTMAutoencoderDetector(config=lstm_config, seed=42)
    lstm_detector.fit(feat_train, X_val=feat_val)

    lstm_scores = lstm_detector.score_samples(feat_test)
    assert len(lstm_scores) == 100
    assert not np.isnan(lstm_scores).any()


def test_experiment_e4_execution_smoke(tmp_path, prepared_data):
    """Execute smoke test of run_experiment_e4 with Isolation Forest and verify all artifacts."""
    run_dir = run_experiment_e4(
        seed=42,
        output_base_dir=tmp_path,
        detectors=["isolation_forest"],  # Fast smoke test
        normalization_method="z_score",
    )

    assert run_dir.exists()
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "comparison.csv").exists()
    assert (run_dir / "summary.md").exists()
    assert (run_dir / "predictions.parquet").exists()
    assert (run_dir / "raw_residuals.parquet").exists()
    assert (run_dir / "residual_normalizer.json").exists()
    assert (run_dir / "models").exists()

    # Verify comparison.csv contents
    comp_df = pd.read_csv(run_dir / "comparison.csv")
    assert len(comp_df) == 2  # E4-1 (Raw) and E4-2 (Residual)
    assert set(comp_df["condition"]) == {"E4-1", "E4-2"}
    assert set(comp_df["representation"]) == {"raw", "residual"}

    # Verify manifest.json completeness
    manifest = load_json(run_dir / "manifest.json")
    assert manifest["experiment_id"] == "E4"
    assert manifest["reproducibility"]["random_seed"] == 42
    assert manifest["synchronization"]["interval_seconds"] == 0
    assert manifest["e4_metadata"]["ideal_sync"] is True
