"""tests/unit/test_ablations.py — Unit tests for controlled ablations engine."""

from pathlib import Path

import pandas as pd
import pytest

from src.experiments.ablations import run_controlled_ablations


def test_run_controlled_ablations_execution(tmp_path):
    # Test on existing completed seed 42 run
    e5_dir = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not (e5_dir / "comparison.csv").exists():
        pytest.skip("E5 seed 42 run not available for ablation testing")

    out_dir = tmp_path / "ablation_test"
    out_dir.mkdir()

    res = run_controlled_ablations(
        output_dir=out_dir,
        e5_seed42_dir=e5_dir,
        config_path="configs/experiments/e11_ablations.yaml",
    )

    assert "ablation_records" in res
    assert "ablation_df" in res
    assert isinstance(res["ablation_df"], pd.DataFrame)
    assert not res["ablation_df"].empty

    # Check generated files in ablations dir
    abl_dir = out_dir / "ablations"
    assert (abl_dir / "ablation_results.csv").is_file()
    assert (abl_dir / "ablation_summary.json").is_file()
    assert (abl_dir / "table_02_ablation_results.csv").is_file()

    # Check specific ablations exist in the dataframe
    ablation_ids = list(res["ablation_df"]["ablation_id"].unique())
    for exp_id in ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]:
        assert any(aid.startswith(exp_id) for aid in ablation_ids)
