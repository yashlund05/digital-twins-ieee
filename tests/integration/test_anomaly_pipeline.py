"""
tests/integration/test_anomaly_pipeline.py — Integration test for unsupervised anomaly detection pipeline.
"""

from pathlib import Path

import pytest

from src.anomaly_detection.trainer import AnomalyDetectionTrainer
from src.utils.config import AnomalyDetectionConfig
from src.utils.io import load_parquet, save_json, save_parquet


@pytest.fixture(scope="module")
def mini_anomaly_environment(tmp_path_factory):
    """Create mini parquet files for quick integration testing of the anomaly pipeline."""
    tmp = tmp_path_factory.mktemp("mini_anomaly")
    data_path = Path("data/processed/load_profiles.parquet")
    labels_path = Path("data/processed/anomaly_labels.parquet")

    if not data_path.exists() or not labels_path.exists():
        pytest.skip("Processed profiles or labels parquet missing in data/processed/")

    df_feats = load_parquet(data_path).iloc[:400]
    df_labels = load_parquet(labels_path).iloc[:400]

    mini_feats_path = tmp / "mini_feats.parquet"
    mini_labels_path = tmp / "mini_labels.parquet"
    mini_splits_path = tmp / "mini_splits.json"

    save_parquet(df_feats, mini_feats_path)
    save_parquet(df_labels, mini_labels_path)

    # 400 steps: 280 train, 60 val, 60 test
    splits = {
        "train_indices": list(range(0, 280)),
        "validation_indices": list(range(280, 340)),
        "test_indices": list(range(340, 400)),
    }
    save_json(splits, mini_splits_path)

    return mini_feats_path, mini_labels_path, mini_splits_path


def test_unsupervised_anomaly_detection_pipeline(mini_anomaly_environment):
    """Verify Isolation Forest and LSTM Autoencoder train unsupervised and evaluate cleanly."""
    feats_p, labels_p, splits_p = mini_anomaly_environment

    cfg = AnomalyDetectionConfig()
    cfg.isolation_forest.n_estimators = 20
    cfg.lstm_autoencoder.epochs = 5
    cfg.lstm_autoencoder.batch_size = 16

    trainer = AnomalyDetectionTrainer(
        config=cfg,
        data_path=feats_p,
        labels_path=labels_p,
        splits_path=splits_p,
        seed=42,
    )

    trained_detectors, comp_df = trainer.train_and_evaluate_all(
        detectors_to_run=["isolation_forest", "lstm_autoencoder"]
    )

    assert "isolation_forest" in trained_detectors
    assert "lstm_autoencoder" in trained_detectors
    assert len(comp_df) == 4  # 2 models x 2 splits (val, test)

    for _, row in comp_df.iterrows():
        assert row["threshold"] is not None
        assert 0.0 <= row["precision"] <= 1.0
        assert 0.0 <= row["recall"] <= 1.0
        assert 0.0 <= row["f1"] <= 1.0
        assert 0.0 <= row["fpr"] <= 1.0
        assert row["latency_steps"] >= 0.0
