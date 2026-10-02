"""tests/publication/test_phase13_submission_runner.py — Tests for Phase 13 submission pipeline."""

from pathlib import Path

from src.publication.submission_runner import run_phase13_submission_pipeline


def test_submission_pipeline_verify_only():
    """Verify that verify_only mode executes all audits without errors."""
    out_dir = run_phase13_submission_pipeline(
        config_path="configs/publication/phase13_publication.yaml",
        verify_only=True,
        strict=True,
    )
    assert out_dir is not None


def test_submission_pipeline_execution(tmp_path: Path):
    """Verify full execution of Phase 13 pipeline in temporary directory."""
    out_dir = run_phase13_submission_pipeline(
        config_path="configs/publication/phase13_publication.yaml",
        output_dir_override=str(tmp_path / "submission_test"),
        verify_only=False,
        strict=True,
    )
    assert out_dir.is_dir()
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "manuscript" / "main.tex").is_file()
    assert (out_dir / "manuscript" / "references.bib").is_file()
    assert (out_dir / "audit_reports" / "canonical_claims_registry.json").is_file()
    assert (out_dir / "audit_reports" / "numerical_audit_report.json").is_file()
    assert (out_dir / "audit_reports" / "cross_phase_audit_report.json").is_file()
    assert (out_dir / "audit_reports" / "language_audit_report.json").is_file()
    assert (out_dir / "audit_reports" / "claim_audit_report.json").is_file()
    assert (out_dir / "provenance" / "submission_manifest.json").is_file()
