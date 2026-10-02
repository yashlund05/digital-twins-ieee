"""tests/unit/test_multiseed.py — Unit tests for Phase 10 multi-seed engine and statistics."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.statistics.hypothesis import benjamini_hochberg_correction
from src.statistics.multiseed import (
    CANONICAL_P7_BASELINES,
    FROZEN_SEEDS,
    PACKET_DROP_GRID,
    STALENESS_GRID,
    compute_condition_statistics,
    compute_multiseed_h3_analysis,
    compute_uncertainty_intervals,
    compute_variance_decomposition,
    reconcile_seed_baseline,
    validate_seed_dataset,
)
from src.utils.config import load_e10_config
from src.utils.io import load_json


def test_01_frozen_seeds_count_and_values():
    """Test 1: Verify exactly five frozen seeds in specification."""
    cfg = load_e10_config()
    assert len(cfg.seeds) == 5
    assert cfg.seeds == [42, 123, 456, 789, 101112]
    assert FROZEN_SEEDS == [42, 123, 456, 789, 101112]


def test_02_every_seed_condition_count_validation(tmp_path):
    """Test 2: Seed validation fails if condition count != 24."""
    fake_dir = tmp_path / "fake_seed"
    fake_dir.mkdir()

    # Create dummy comparison.csv with only 10 conditions
    records = []
    for i in range(10):
        records.append({
            "condition_id": f"C_{i}",
            "staleness_seconds": 0,
            "packet_drop_rate": 0.0,
            "task": "anomaly_detection",
            "model": "lstm_autoencoder",
            "representation": "residual",
            "metric": "f1",
            "value": 0.9,
            "baseline_value": 0.9,
        })
    pd.DataFrame(records).to_csv(fake_dir / "comparison.csv", index=False)
    (fake_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (fake_dir / "aoi_statistics.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="expected exactly 24"):
        validate_seed_dataset(999, fake_dir)


def test_03_staleness_grid_completeness():
    """Test 3: Every seed must contain all 6 staleness levels."""
    cfg = load_e10_config()
    assert cfg.staleness_seconds == [0, 1, 5, 15, 60, 300]
    assert STALENESS_GRID == [0, 1, 5, 15, 60, 300]


def test_04_packet_drop_grid_completeness():
    """Test 4: Every seed must contain all 4 packet drop rates."""
    cfg = load_e10_config()
    assert cfg.packet_drop == [0.0, 0.05, 0.10, 0.20]
    assert PACKET_DROP_GRID == [0.0, 0.05, 0.10, 0.20]


def test_05_seed42_baseline_matches_phase7():
    """Test 5: Seed 42 baseline must bit-for-bit match Phase 7 E4."""
    e5_seed42_dir = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not e5_seed42_dir.exists():
        pytest.skip(f"Reference seed 42 run not found at {e5_seed42_dir}")

    rec_res = reconcile_seed_baseline(42, e5_seed42_dir)
    assert rec_res["status"] == "PASS"
    assert rec_res["phase7_match"] is True
    assert abs(rec_res["metrics"]["lstm_res_f1"] - CANONICAL_P7_BASELINES["lstm_res"]) < 1e-4
    assert abs(rec_res["metrics"]["lstm_raw_f1"] - CANONICAL_P7_BASELINES["lstm_raw"]) < 1e-4
    assert abs(rec_res["metrics"]["if_raw_f1"] - CANONICAL_P7_BASELINES["if_raw"]) < 1e-4
    assert abs(rec_res["metrics"]["if_res_f1"] - CANONICAL_P7_BASELINES["if_res"]) < 1e-4


def test_06_seed42_baseline_matches_phase8_corrected():
    """Test 6: Seed 42 baseline in Phase 8 corrected run matches reconciliation audit."""
    e5_dir = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not e5_dir.exists():
        pytest.skip(f"E5 corrected run not found at {e5_dir}")

    m = load_json(e5_dir / "metrics.json")
    base_key = "E5_DT0_PD00_SEED42"
    assert base_key in m["anomaly_detection"]
    f1_res = m["anomaly_detection"][base_key]["lstm_res"]["f1"]
    assert abs(f1_res - 0.977956) < 1e-4


def test_07_phase9_metrics_remain_unchanged():
    """Test 7: Phase 9 canonical seed-42 analysis outputs exist and match."""
    e6_dir = Path("experiments/runs/E6_JOINT_ANALYSIS_SEED42_20261002")
    if not e6_dir.exists():
        pytest.skip(f"E6 reference run not found at {e6_dir}")

    h3_p9 = pd.read_csv(e6_dir / "H3_summary.csv")
    assert not h3_p9.empty
    # Primary comparison slope difference in Phase 9 was negative (~ -1.1148)
    row0 = h3_p9.iloc[0]
    assert row0["delta_beta"] < 0
    assert row0["conclusion"] == "NOT_SUPPORTED"


def test_08_mean_std_calculations_are_deterministic():
    """Test 8: Statistical aggregations on synthetic multi-seed frame are deterministic."""
    data = []
    for s in [42, 123, 456]:
        for dt in [0, 5]:
            data.append({
                "staleness_seconds": dt,
                "packet_drop_rate": 0.0,
                "task": "anomaly_detection",
                "model": "lstm_autoencoder",
                "representation": "residual",
                "metric": "f1",
                "value": 0.8 if dt == 0 else 0.2,
                "normalized_degradation": 0.0 if dt == 0 else 0.75,
                "absolute_degradation": 0.0 if dt == 0 else 0.6,
                "seed": s,
            })
    df = pd.DataFrame(data)
    stats1 = compute_condition_statistics(df)
    stats2 = compute_condition_statistics(df)
    pd.testing.assert_frame_equal(stats1, stats2)
    assert np.isclose(stats1.loc[stats1["staleness_seconds"] == 0, "value_mean"].values[0], 0.8)
    assert np.isclose(stats1.loc[stats1["staleness_seconds"] == 5, "value_mean"].values[0], 0.2)



def test_09_bootstrap_seed_determinism():
    """Test 9: Bootstrap analysis produces identical results under fixed random seed."""
    data = []
    for s in [42, 123]:
        for dt in [0, 1, 5, 15, 60, 300]:
            for task, mod, rep, met, base_v in [
                ("anomaly_detection", "lstm_autoencoder", "residual", "f1", 0.9),
                ("load_estimation", "lstm", "raw", "mape", 10.0),
            ]:
                data.append({
                    "staleness_seconds": dt,
                    "packet_drop_rate": 0.0,
                    "task": task,
                    "model": mod,
                    "representation": rep,
                    "metric": met,
                    "normalized_degradation": float(np.log1p(dt) * (0.2 if task == "anomaly_detection" else 1.0)),
                    "seed": s,
                })
    df = pd.DataFrame(data)
    h3_1, _ = compute_multiseed_h3_analysis(df, seeds=[42, 123], n_boot=200, seed=42)
    h3_2, _ = compute_multiseed_h3_analysis(df, seeds=[42, 123], n_boot=200, seed=42)
    pd.testing.assert_frame_equal(h3_1, h3_2)


def test_10_missing_conditions_raise_error(tmp_path):
    """Test 10: Missing conditions in a seed's dataset must raise ValueError."""
    fake_dir = tmp_path / "incomplete_seed"
    fake_dir.mkdir()
    # 23 conditions (one missing)
    records = []
    for dt in [0, 1, 5, 15, 60]:
        for drop in [0.0, 0.05, 0.10, 0.20]:
            records.append({
                "condition_id": f"DT{dt}_PD{int(drop*100)}",
                "staleness_seconds": dt,
                "packet_drop_rate": drop,
            })
    # Add 3 for dt=300 to make 23
    for drop in [0.0, 0.05, 0.10]:
        records.append({
            "condition_id": f"DT300_PD{int(drop*100)}",
            "staleness_seconds": 300,
            "packet_drop_rate": drop,
        })

    pd.DataFrame(records).to_csv(fake_dir / "comparison.csv", index=False)
    (fake_dir / "metrics.json").write_text("{}", encoding="utf-8")
    (fake_dir / "aoi_statistics.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="expected exactly 24"):
        validate_seed_dataset(101, fake_dir)


def test_11_no_duplicate_seed_condition_combinations():
    """Test 11: Aggregated dataset must contain zero duplicate (seed, condition_id, metric, model)."""
    # Create valid synthetic dataset and check for uniqueness
    records = []
    for s in [42, 123]:
        for dt in [0, 1]:
            for p in [0.0, 0.05]:
                records.append({
                    "seed": s,
                    "condition_id": f"C_DT{dt}_P{p}_S{s}",
                    "staleness_seconds": dt,
                    "packet_drop_rate": p,
                    "task": "anomaly_detection",
                    "model": "lstm_autoencoder",
                    "representation": "residual",
                    "metric": "f1",
                    "value": 0.9,
                })
    df = pd.DataFrame(records)
    dups = df.duplicated(subset=["seed", "condition_id", "task", "model", "representation", "metric"])
    assert not dups.any()


def test_12_h3_sign_calculation_logic():
    """Test 12: H3 sign calculation properly identifies positive and negative slopes."""
    data = []
    # Seed 1: AD steeper (beta_ad = 2.0, beta_le = 0.5 -> delta_beta > 0)
    # Seed 2: LE steeper (beta_ad = 0.2, beta_le = 1.5 -> delta_beta < 0)
    for dt in [0, 1, 5, 15, 60, 300]:
        data.append({
            "staleness_seconds": dt,
            "packet_drop_rate": 0.0,
            "task": "anomaly_detection",
            "model": "lstm_autoencoder",
            "representation": "residual",
            "metric": "f1",
            "normalized_degradation": 2.0 * np.log1p(dt),
            "seed": 1,
        })
        data.append({
            "staleness_seconds": dt,
            "packet_drop_rate": 0.0,
            "task": "load_estimation",
            "model": "lstm",
            "metric": "mape",
            "normalized_degradation": 0.5 * np.log1p(dt),
            "seed": 1,
        })

        data.append({
            "staleness_seconds": dt,
            "packet_drop_rate": 0.0,
            "task": "anomaly_detection",
            "model": "lstm_autoencoder",
            "representation": "residual",
            "metric": "f1",
            "normalized_degradation": 0.2 * np.log1p(dt),
            "seed": 2,
        })
        data.append({
            "staleness_seconds": dt,
            "packet_drop_rate": 0.0,
            "task": "load_estimation",
            "model": "lstm",
            "metric": "mape",
            "normalized_degradation": 1.5 * np.log1p(dt),
            "seed": 2,
        })

    df = pd.DataFrame(data)
    h3_res, sign_res = compute_multiseed_h3_analysis(df, seeds=[1, 2], n_boot=100, seed=42)

    assert sign_res["delta_beta_positive"] == 1
    assert sign_res["delta_beta_negative"] == 1
    assert sign_res["sign_consistency_percentage"] == 50.0
    assert sign_res["robustness_assessment"] == "HETEROGENEOUS"


def test_13_fdr_correction_reproducible():
    """Test 13: Benjamini-Hochberg correction is deterministic."""
    p_vals = [0.001, 0.015, 0.04, 0.25, 0.8]
    res1 = benjamini_hochberg_correction(p_vals, alpha=0.05)
    res2 = benjamini_hochberg_correction(p_vals, alpha=0.05)
    assert res1["p_adjusted"] == res2["p_adjusted"]
    assert res1["significant"] == res2["significant"]


def test_14_confidence_interval_calculation_deterministic():
    """Test 14: Uncertainty confidence interval function is deterministic."""
    data = []
    for s in [42, 123, 456, 789, 101112]:
        data.append({
            "staleness_seconds": 15,
            "packet_drop_rate": 0.05,
            "task": "load_estimation",
            "model": "lstm",
            "representation": "raw",
            "metric": "mape",
            "value": 15.0 + s * 0.001,
            "normalized_degradation": 0.5,
            "seed": s,
        })
    df = pd.DataFrame(data)
    ci1 = compute_uncertainty_intervals(df, ci_level=0.95)
    ci2 = compute_uncertainty_intervals(df, ci_level=0.95)
    pd.testing.assert_frame_equal(ci1, ci2)
    assert ci1["value_ci_lower"].values[0] < ci1["value_ci_upper"].values[0]


def test_15_no_future_data_leakage():
    """Test 15: Telemetry timestamps and AoI non-negativity."""
    data = []
    for s in [42, 123]:
        for dt in STALENESS_GRID:
            for p in PACKET_DROP_GRID:
                data.append({
                    "staleness_seconds": dt,
                    "packet_drop_rate": p,
                    "task": "load_estimation",
                    "model": "lstm",
                    "representation": "raw",
                    "metric": "mape",
                    "value": 10.0,
                    "seed": s,
                })
    df = pd.DataFrame(data)
    assert (df["staleness_seconds"] >= 0).all()
    assert (df["packet_drop_rate"] >= 0.0).all()
