"""tests/publication/test_phase13_language_audit.py — Tests for Phase 13 scientific language audit."""

from pathlib import Path
import pytest

from src.publication.language_audit import (
    audit_manuscript_directory,
    audit_manuscript_language,
    export_language_audit_report,
)


def test_clean_language_passes():
    """Verify clean scientific text passes audit."""
    clean_text = (
        "We evaluate the effect of staleness on load estimation. "
        "The empirical findings suggest an association between staleness and error. "
        "Under the evaluated protocol, the residual model achieved higher F1."
    )
    report = audit_manuscript_language(clean_text)
    assert report.status == "PASS"
    assert report.total_errors == 0


def test_prohibited_phrases_flagged():
    """Verify prohibited phrases are flagged as errors."""
    bad_text = (
        "This proves that staleness causes catastrophic failure. "
        "The proposed approach is mathematically optimal and universally superior. "
        "The model is guaranteed to work in all cases."
    )
    report = audit_manuscript_language(bad_text)
    assert report.status == "FLAGGED"
    assert report.total_errors > 0

    flagged_phrases = [f["phrase"] for f in report.findings if f["severity"] == "ERROR"]
    assert any("causes" in p.lower() for p in flagged_phrases)
    assert any("mathematically optimal" in p.lower() for p in flagged_phrases)
    assert any("universally superior" in p.lower() for p in flagged_phrases)


def test_comments_ignored():
    """Verify comments are excluded from language audit."""
    commented_text = "% This proves that staleness causes failure\nValid scientific observation."
    report = audit_manuscript_language(commented_text)
    assert report.status == "PASS"
    assert report.total_errors == 0


def test_audit_manuscript_directory(tmp_path: Path):
    """Verify directory scanning and JSON export."""
    tex_file = tmp_path / "section.tex"
    tex_file.write_text("We observe empirical trends.", encoding="utf-8")

    report = audit_manuscript_directory(tmp_path)
    assert report.status == "PASS"
    assert report.total_files_scanned == 1

    out_file = tmp_path / "lang_report.json"
    export_language_audit_report(report, out_file)
    assert out_file.is_file()
