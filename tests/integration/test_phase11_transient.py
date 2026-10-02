"""tests/integration/test_phase11_transient.py — Integration test for missed-update transient dynamics."""

from pathlib import Path

import pytest

from src.experiments.missed_update_transient import run_missed_update_transient_analysis


def test_missed_update_transient_pipeline(tmp_path):
    """Verify that missed-update transient dynamics and change-point estimation operate correctly."""
    e5_path = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not (e5_path / "predictions.parquet").exists():
        pytest.skip(f"E5 predictions not found at {e5_path}")

    out_dir = tmp_path / "transient_integration"
    out_dir.mkdir()

    res = run_missed_update_transient_analysis(
        output_dir=out_dir,
        e5_seed42_dir=e5_path,
        max_aoi_seconds=300,
    )

    timeseries_df = res["timeseries_df"]
    assert not timeseries_df.empty
    assert "realized_aoi" in timeseries_df.columns
    assert "residual_norm" in timeseries_df.columns

    by_aoi = res["by_aoi_df"]
    assert not by_aoi.empty
    assert "aoi_bin" in by_aoi.columns
    assert "mean_residual_norm" in by_aoi.columns

    # Verify that max AoI residual norm is greater than or equal to fresh AoI residual norm
    fresh_rows = by_aoi[by_aoi["aoi_bin"] == "0s (Fresh)"]
    stale_rows = by_aoi[by_aoi["aoi_bin"] == "121-300s"]

    if not fresh_rows.empty and not stale_rows.empty:
        r_zero = fresh_rows["mean_residual_norm"].iloc[0]
        r_high = stale_rows["mean_residual_norm"].iloc[0]
        assert r_high >= r_zero

    # Change point report
    cp_df = res["change_point_df"]
    assert not cp_df.empty
    assert "estimated_transition_aoi_seconds" in cp_df.columns
    est_aoi = cp_df["estimated_transition_aoi_seconds"].iloc[0]
    assert 0.0 <= est_aoi <= 300.0
