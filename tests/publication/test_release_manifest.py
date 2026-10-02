"""tests/publication/test_release_manifest.py — Tests for Release Readiness and Safety Gate."""

from pathlib import Path

from src.audit.release_readiness import ReleaseReadinessEvaluator


def test_safety_gate_evaluation():
    """Verify that safety gate passes when all conditions are zero defects."""
    evaluator = ReleaseReadinessEvaluator()
    status = evaluator.evaluate_gate(
        critical_discrepancies=0,
        unresolved_claims=0,
        failed_tests=0,
        missing_required_artifacts=0,
        manuscript_errors=0,
        provenance_errors=0,
    )
    assert status.is_publication_ready is True


def test_safety_gate_fails_on_any_defect():
    """Verify that safety gate rejects publication when any condition fails."""
    evaluator = ReleaseReadinessEvaluator()
    status = evaluator.evaluate_gate(
        critical_discrepancies=1,  # 1 defect
        unresolved_claims=0,
        failed_tests=0,
        missing_required_artifacts=0,
        manuscript_errors=0,
        provenance_errors=0,
    )
    assert status.is_publication_ready is False


def test_release_package_generation(tmp_path: Path):
    """Verify release package generates all 4 checklist markdown files."""
    evaluator = ReleaseReadinessEvaluator()
    gate_status = evaluator.evaluate_gate(0, 0, 0, 0, 0, 0)
    evaluator.generate_release_package(
        output_dir=tmp_path,
        gate_status=gate_status,
        summary_stats={"test": True},
    )

    rel_dir = tmp_path / "release"
    assert (rel_dir / "RELEASE_CHECKLIST.md").is_file()
    assert (rel_dir / "REPRODUCIBILITY_CHECKLIST.md").is_file()
    assert (rel_dir / "PUBLICATION_CHECKLIST.md").is_file()
    assert (rel_dir / "RELEASE_NOTES.md").is_file()
    assert (tmp_path / "release_readiness.json").is_file()
