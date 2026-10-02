"""tests/integration/test_phase10_multiseed.py — Integration test for Phase 10 multi-seed pipeline."""

from pathlib import Path
import pandas as pd
import pytest

from src.statistics.multiseed import run_multiseed_analysis
from src.utils.io import load_json


def test_phase10_end_to_end_multiseed_pipeline(tmp_path):
    """Execute end-to-end Phase 10 analysis pipeline on mock/cloned multi-seed runs."""
    base_e5_dir = Path("experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930")
    if not base_e5_dir.exists():
        pytest.skip(f"Base E5 corrected run not found at {base_e5_dir}")

    # Create lightweight mock directories for all 5 seeds by referencing/cloning the base dataset
    seed_dirs = {}
    mock_base = tmp_path / "mock_runs"
    mock_base.mkdir()

    for s in [42, 123, 456, 789, 101112]:
        s_dir = mock_base / f"E5_SEED_{s}"
        s_dir.mkdir()

        # Copy comparison.csv and adapt condition IDs and seeds
        comp_df = pd.read_csv(base_e5_dir / "comparison.csv")
        comp_df["seed"] = s
        comp_df["condition_id"] = comp_df["condition_id"].str.replace("SEED42", f"SEED{s}")
        # Add slight deterministic stochastic jitter for non-baseline conditions
        jitter = (s - 42) * 1e-4
        mask_non_base = comp_df["staleness_seconds"] > 0
        comp_df.loc[mask_non_base, "value"] += jitter
        comp_df.to_csv(s_dir / "comparison.csv", index=False)

        # Copy metrics.json with matching seed keys
        m_dict = load_json(base_e5_dir / "metrics.json")
        anom_copy = {}
        for k, v in m_dict["anomaly_detection"].items():
            new_k = k.replace("SEED42", f"SEED{s}")
            anom_copy[new_k] = v
        m_dict["anomaly_detection"] = anom_copy
        (s_dir / "metrics.json").write_text(pd.Series(m_dict).to_json(), encoding="utf-8")
        (s_dir / "aoi_statistics.json").write_text("{}", encoding="utf-8")

        seed_dirs[s] = s_dir

    # Run complete Phase 10 analysis with small n_boot for fast test
    out_dir = run_multiseed_analysis(
        seed_dirs=seed_dirs,
        output_base_dir=tmp_path / "output",
        n_boot=100,
        ci_level=0.95,
    )

    assert out_dir.exists()

    # Verify all expected artifacts exist
    expected_csvs = [
        "seed_results.csv",
        "aggregated_metrics.csv",
        "condition_statistics.csv",
        "uncertainty_intervals.csv",
        "multiseed_h3_summary.csv",
        "multiseed_hypothesis_tests.csv",
        "multiseed_regression_results.csv",
        "multiseed_effect_sizes.csv",
        "sensitivity_analysis.csv",
        "interaction_effects.csv",
        "variance_decomposition.csv",
        "robustness_summary.csv",
    ]
    for c in expected_csvs:
        p = out_dir / c
        assert p.exists(), f"Missing CSV: {c}"
        df = pd.read_csv(p)
        assert not df.empty, f"Empty CSV: {c}"

    # Verify JSON validations and manifests
    assert (out_dir / "seed_validation.json").exists()
    assert (out_dir / "baseline_reconciliation.json").exists()
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "summary.md").exists()

    # Verify all 8 publication figures exist and are non-empty
    figures_dir = out_dir / "figures"
    assert figures_dir.exists()
    for i in range(1, 9):
        matches = list(figures_dir.glob(f"fig_{i:02d}_*.png"))
        assert len(matches) == 1, f"Missing figure {i:02d}"
        assert matches[0].stat().st_size > 1000
