"""tests/publication/test_phase14_final_audit.py — E2E test for Phase 14 Final Audit."""

from pathlib import Path

from src.audit.audit_runner import run_phase14_final_audit


def test_phase14_final_audit_execution(tmp_path: Path):
    """Verify that Phase 14 final audit executes cleanly and produces all expected artifacts."""
    out_dir = tmp_path / "final_audit_test"
    res_dir = run_phase14_final_audit(
        config_path="configs/publication/phase14_final_audit.yaml",
        output_dir_override=str(out_dir),
        strict=True,
    )

    assert res_dir.is_dir()
    assert (res_dir / "manifest.json").is_file()
    assert (res_dir / "audit_summary.json").is_file()
    assert (res_dir / "reproducibility_summary.json").is_file()
    assert (res_dir / "cross_phase_consistency.json").is_file()
    assert (res_dir / "claim_registry_final.json").is_file()
    assert (res_dir / "numerical_audit_final.json").is_file()
    assert (res_dir / "figure_table_consistency.json").is_file()
    assert (res_dir / "manuscript_consistency.json").is_file()
    assert (res_dir / "release_readiness.json").is_file()
    assert (res_dir / "claims" / "all_claims.csv").is_file()
    assert (res_dir / "discrepancies" / "c13_aoi_investigation.md").is_file()
    assert (res_dir / "reproducibility" / "command_manifest.json").is_file()
    assert (res_dir / "release" / "RELEASE_CHECKLIST.md").is_file()
