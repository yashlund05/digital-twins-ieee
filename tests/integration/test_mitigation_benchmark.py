"""tests/integration/test_mitigation_benchmark.py — Integration test for staleness mitigation."""

from pathlib import Path

import pytest

from src.experiments.mitigation import run_mitigation_benchmark


def test_mitigation_benchmark_pipeline(tmp_path):
    """Verify that the mitigation benchmark pipeline executes and computes recovery gains."""
    e5_dir = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not (e5_dir / "predictions.parquet").is_file():
        pytest.skip(f"E5 predictions not found at {e5_dir}")

    out_dir = tmp_path / "mitigation_run"
    out_dir.mkdir()

    res = run_mitigation_benchmark(
        output_dir=out_dir,
        e5_seed42_dir=e5_dir,
        aoi_inversion_threshold=5.0,
        gamma_adaptive=0.08,
    )

    df = res["results_df"]
    assert not df.empty
    assert "f1_residual_uncompensated" in df.columns
    assert "f1_dual_mode_compensator" in df.columns
    assert "delta_f1_dual_mode_vs_residual" in df.columns

    summ = res["summary"]
    assert "severe_staleness_comparison" in summ
    sev = summ["severe_staleness_comparison"]

    # Verify that under severe staleness, Dual-Mode achieves positive recovery gain
    assert sev["recovery_gain_dual_mode"] > 0.20
    assert (out_dir / "mitigation_benchmark_results.csv").is_file()
    assert (out_dir / "mitigation_summary.json").is_file()
