"""
tests/integration/test_phase9_analysis.py — Integration test for Phase 9 joint analysis pipeline.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.statistics.analysis_runner import run_phase9_analysis
from src.utils.io import load_json


def test_phase9_end_to_end_analysis(tmp_path):
    """Execute end-to-end Phase 9 analysis using the corrected E5 run artifacts."""
    input_e5_dir = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not input_e5_dir.exists():
        pytest.skip(f"E5 corrected run not found at {input_e5_dir}")

    # Run analysis with fast bootstrap (100 iterations for smoke test)
    out_dir = run_phase9_analysis(
        input_e5_dir=input_e5_dir,
        output_base_dir=tmp_path,
        seed=42,
        n_boot=100,
        ci_level=0.95,
    )

    assert out_dir.exists()

    # 1. Verify required CSVs exist and are non-empty
    csv_files = [
        "degradation_metrics.csv",
        "regression_results.csv",
        "effect_sizes.csv",
        "statistical_tests.csv",
        "bootstrap_results.csv",
        "descriptive_statistics.csv",
        "H3_summary.csv",
    ]
    for f in csv_files:
        p = out_dir / f
        assert p.exists(), f"Missing CSV artifact: {f}"
        df = pd.read_csv(p)
        assert not df.empty, f"CSV artifact {f} is empty"

    # 2. Verify JSON validation and manifest
    val_json = load_json(out_dir / "phase9_input_validation.json")
    assert val_json["status"] == "PASS"
    assert val_json["total_conditions"] == 24

    manifest = load_json(out_dir / "manifest.json")
    assert manifest["experiment_id"] == "E6"

    # 3. Verify Markdown summaries
    assert (out_dir / "H3_summary.md").exists()
    assert (out_dir / "summary.md").exists()

    # 4. Verify all 8 publication figures exist
    figures_dir = out_dir / "figures"
    assert figures_dir.exists()
    expected_figures = [
        "fig_01_anomaly_f1_vs_staleness.png",
        "fig_02_anomaly_prauc_vs_staleness.png",
        "fig_03_load_mae_vs_staleness.png",
        "fig_04_load_rmse_vs_staleness.png",
        "fig_05_task_degradation_comparison.png",
        "fig_06_realized_aoi.png",
        "fig_07_staleness_packet_drop_interaction.png",
        "fig_08_h3_effect_comparison.png",
    ]
    for fig_name in expected_figures:
        fig_path = figures_dir / fig_name
        assert fig_path.exists(), f"Missing figure: {fig_name}"
        assert fig_path.stat().st_size > 1000, f"Figure {fig_name} is too small / corrupt"
