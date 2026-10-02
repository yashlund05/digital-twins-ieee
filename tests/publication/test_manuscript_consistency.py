"""tests/publication/test_manuscript_consistency.py — Tests for Manuscript LaTeX and Language Audit."""

import pytest

from src.audit.manuscript_auditor import ManuscriptPackageAuditor


@pytest.fixture
def manuscript_auditor():
    return ManuscriptPackageAuditor(
        manuscript_dir="experiments/runs/E13_MANUSCRIPT_SUBMISSION_20261002/manuscript"
    )


def test_manuscript_latex_structure(manuscript_auditor):
    """Verify that main.tex has valid LaTeX structure, tags, and all inputs exist."""
    res = manuscript_auditor.audit_latex_structure()
    assert res["status"] == "PASS"
    assert res["document_tags_valid"] is True
    assert len(res["missing_inputs"]) == 0
    assert len(res["missing_citations"]) == 0
    assert len(res["missing_references"]) == 0


def test_manuscript_scientific_language(manuscript_auditor):
    """Verify that manuscript has zero prohibited overclaim errors."""
    res = manuscript_auditor.audit_manuscript_language()
    assert res["status"] == "PASS"
    assert res["total_errors"] == 0
