"""tests/publication/test_aoi_change_point_consistency.py — Tests for Objective C AoI Investigation."""

from pathlib import Path
import pytest

from src.audit.aoi_investigator import C13AoIInvestigator


def test_aoi_investigation_verdict_case_b():
    """Verify that independent AoI investigation confirms Case B resolution."""
    inv = C13AoIInvestigator(run_dir_e11="experiments/runs/E11_PHASE11_20261002")
    findings = inv.run_investigation()

    assert findings["case_verdict"] == "CASE_B"
    assert findings["canonical_artifact_exists"] is True
    assert findings["canonical_stored_value"] == 0.0
    assert findings["canonical_status"] == "DETECTED"
    assert findings["canonical_ci"] == [0.0, 2.5]
    assert findings["macro_cliff_evidence"]["summary_mentions_5s"] is True


def test_aoi_report_generation(tmp_path: Path):
    """Verify markdown report generation."""
    inv = C13AoIInvestigator(run_dir_e11="experiments/runs/E11_PHASE11_20261002")
    out_file = tmp_path / "c13_report.md"
    text = inv.generate_investigation_report(out_file)

    assert out_file.is_file()
    assert "Case B" in text
    assert "0.0" in text
    assert "5.0" in text
