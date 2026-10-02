"""tests/integration/test_phase11_ablation.py — Integration test for Phase 11 controlled ablations."""

from pathlib import Path
import pytest
import pandas as pd

from src.experiments.ablations import run_controlled_ablations


def test_ablation_pipeline_and_representation_inversion(tmp_path):
    """Verify that controlled ablations A1–A8 execute properly and confirm representation inversion."""
    e5_path = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not (e5_path / "comparison.csv").exists():
        pytest.skip(f"E5 run not found at {e5_path}")

    out_dir = tmp_path / "ablation_integration"
    out_dir.mkdir()

    res = run_controlled_ablations(
        output_dir=out_dir,
        e5_seed42_dir=e5_path,
        config_path="configs/experiments/e11_ablations.yaml",
    )

    df = res["ablation_df"]
    assert not df.empty

    # Verify A1: Representation effect
    a1_rows = df[df["ablation_id"] == "A1_representation"]
    assert len(a1_rows) > 0

    # At baseline (dt=0, pd=0.0) for lstm_autoencoder, residual F1 is much higher than raw F1
    base_rows = a1_rows[(a1_rows["staleness_seconds"] == 0) & (a1_rows["model"] == "lstm_autoencoder")]
    assert not base_rows.empty
    v_res = base_rows["baseline_value"].iloc[0]
    v_raw = base_rows["ablation_value"].iloc[0]
    assert v_res > v_raw
    # Advantage at baseline should be ~0.4393
    assert abs((v_res - v_raw) - 0.4393) < 0.05

    # At stale condition (dt=60), raw performs better because residual is drifted
    stale_rows = a1_rows[(a1_rows["staleness_seconds"] == 60) & (a1_rows["model"] == "lstm_autoencoder")]
    if not stale_rows.empty:
        stale_res = stale_rows["baseline_value"].iloc[0]
        stale_raw = stale_rows["ablation_value"].iloc[0]
        assert stale_res <= stale_raw
