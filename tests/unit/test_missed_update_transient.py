"""tests/unit/test_missed_update_transient.py — Unit tests for missed update transient analysis."""

from pathlib import Path

import pandas as pd
import pytest

from src.experiments.missed_update_transient import run_missed_update_transient_analysis


def test_run_missed_update_transient_execution(tmp_path):
    e5_dir = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not (e5_dir / "predictions.parquet").exists():
        pytest.skip("E5 predictions.parquet not available for transient testing")

    out_dir = tmp_path / "transient_test"
    out_dir.mkdir()

    res = run_missed_update_transient_analysis(
        output_dir=out_dir,
        e5_seed42_dir=e5_dir,
        max_aoi_seconds=300,
    )

    assert "timeseries_df" in res
    assert "by_aoi_df" in res
    assert "change_point_df" in res

    assert isinstance(res["timeseries_df"], pd.DataFrame)
    assert isinstance(res["by_aoi_df"], pd.DataFrame)
    assert isinstance(res["change_point_df"], pd.DataFrame)

    assert not res["timeseries_df"].empty
    assert not res["by_aoi_df"].empty
    assert not res["change_point_df"].empty

    trans_dir = out_dir / "transient"
    assert (trans_dir / "transient_timeseries.parquet").is_file()
    assert (trans_dir / "transient_by_aoi.csv").is_file()
    assert (trans_dir / "change_point_results.csv").is_file()
    assert (trans_dir / "transient_summary.csv").is_file()
