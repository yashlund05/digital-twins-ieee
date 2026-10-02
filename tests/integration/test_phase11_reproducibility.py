"""tests/integration/test_phase11_reproducibility.py — Integration test for historical benchmark verification."""

from pathlib import Path
import pytest

from src.reproducibility.verifier import verify_historical_benchmarks


def test_verify_historical_benchmarks_integration(tmp_path):
    """Verify that historical frozen runs (E4, E5, E6, E10) are successfully audited."""
    out_dir = tmp_path / "verify_benchmarks"
    out_dir.mkdir()

    e4_path = Path("experiments/runs/E4_RAW_VS_RESIDUAL_SEED42_20260930")
    if not e4_path.exists():
        pytest.skip(f"E4 run not found at {e4_path}")

    report = verify_historical_benchmarks(
        output_dir=out_dir,
        phase7_e4_dir=e4_path,
        phase8_e5_dir="experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930",
        phase9_e6_dir="experiments/runs/E6_JOINT_ANALYSIS_SEED42_20261002",
        phase10_e10_dir="experiments/runs/E10_MULTI_SEED_ANALYSIS_20261002",
    )

    assert report["overall_status"] == "PASS"
    assert report["phase7_e4_status"] == "PASS"
    assert report["phase8_e5_status"] == "PASS"
    assert report["phase9_e6_status"] == "PASS"
    assert report["phase10_e10_status"] == "PASS"

    assert len(report["baseline_comparison"]) == 4
    for item in report["baseline_comparison"]:
        assert item["classification"] in ["BITWISE_IDENTICAL", "NUMERICALLY_EQUIVALENT"]
        assert item["abs_diff"] < 1e-3

    # Check generated artifacts
    assert (out_dir / "reproducibility_report.json").is_file()
    assert (out_dir / "reproducibility" / "baseline_comparison.csv").is_file()
    assert (out_dir / "reproducibility" / "selected_condition_comparison.csv").is_file()
