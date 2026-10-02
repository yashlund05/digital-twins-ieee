"""tests/integration/test_staleness_pipeline.py — Integration test for Experiment E5.

Tests the full pipeline on a fast smoke matrix:
- Intervals: [0, 5] s
- Packet drop rates: [0.0, 0.10]
- Evaluates:
    data -> scheduler -> packet drop -> sync engine -> hold-last-state
    -> AoI -> DT state -> residual -> anomaly detection -> forecasting -> metrics
- Verifies artifact creation, schema compliance, and baseline equivalence.
"""

import pandas as pd
import pytest

from src.experiments.staleness_sweep import (
    E5ExperimentCoordinator,
    StalenessCondition,
    run_staleness_sweep,
)
from src.utils.io import load_json, load_parquet


@pytest.fixture(scope="module")
def shared_coordinator():
    """Module-scoped coordinator to reuse fitted baseline models across tests."""
    return E5ExperimentCoordinator(seed=42)


def test_staleness_pipeline_smoke_run(shared_coordinator, tmp_path):
    """Execute smoke test of run_staleness_sweep across 4 conditions."""
    smoke_conditions = [
        StalenessCondition(staleness_seconds=0, packet_drop_rate=0.0, seed=42),
        StalenessCondition(staleness_seconds=0, packet_drop_rate=0.10, seed=42),
        StalenessCondition(staleness_seconds=5, packet_drop_rate=0.0, seed=42),
        StalenessCondition(staleness_seconds=5, packet_drop_rate=0.10, seed=42),
    ]

    run_dir = run_staleness_sweep(
        seed=42,
        output_base_dir=tmp_path,
        coordinator=shared_coordinator,
        conditions_to_run=smoke_conditions,
    )

    assert run_dir.exists()

    # 1. Verify all required artifacts exist
    expected_files = [
        "manifest.json",
        "config_snapshot.yaml",
        "aoi_statistics.json",
        "metrics.json",
        "comparison.csv",
        "synchronization_logs.parquet",
        "predictions.parquet",
        "summary.md",
    ]
    for fname in expected_files:
        assert (run_dir / fname).exists(), f"Missing artifact: {fname}"

    # 2. Check AoI statistics
    aoi_stats = load_json(run_dir / "aoi_statistics.json")
    assert len(aoi_stats) == 4

    # Baseline AoI should be 0.0
    dt0_pd0 = aoi_stats["E5_DT0_PD00_SEED42"]
    assert dt0_pd0["mean_aoi"] == 0.0
    assert dt0_pd0["dropped_updates"] == 0

    # DT5 AoI should be greater than DT0
    dt5_pd0 = aoi_stats["E5_DT5_PD00_SEED42"]
    assert dt5_pd0["mean_aoi"] > 0.0
    assert dt5_pd0["max_aoi"] == 4.0

    # DT5 with 10% packet drop should drop some packets
    dt5_pd10 = aoi_stats["E5_DT5_PD10_SEED42"]
    assert dt5_pd10["dropped_updates"] > 0
    assert dt5_pd10["actual_drop_rate"] > 0.0

    # 3. Check comparison.csv schema and contents
    comp_df = pd.read_csv(run_dir / "comparison.csv")
    assert not comp_df.empty
    assert "condition_id" in comp_df.columns
    assert "staleness_seconds" in comp_df.columns
    assert "packet_drop_rate" in comp_df.columns
    assert "task" in comp_df.columns
    assert "metric" in comp_df.columns
    assert "value" in comp_df.columns
    assert "relative_degradation" in comp_df.columns

    # 4. Check predictions.parquet
    preds_df = load_parquet(run_dir / "predictions.parquet")
    assert not preds_df.empty
    assert "condition_id" in preds_df.columns
    assert "score_if_raw" in preds_df.columns
    assert "score_if_res" in preds_df.columns
    assert "score_lstm_res" in preds_df.columns
    assert "pred_persistence_kw" in preds_df.columns
    assert "true_total_load_kw" in preds_df.columns

    # 5. Check manifest.json metadata
    manifest = load_json(run_dir / "manifest.json")
    assert manifest["experiment_id"] == "E5"
    assert manifest["reproducibility"]["random_seed"] == 42
    assert "git_commit" in manifest["reproducibility"]
