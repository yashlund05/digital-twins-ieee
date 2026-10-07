"""tests/publication/test_phase19_final_submission_audit.py — Phase 19 Release Test Suite."""

import csv
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
E19_DIR = ROOT / "experiments" / "runs" / "E19_FINAL_SUBMISSION_AUDIT_20261006"


def test_historical_immutability():
    """Verify all historical phases E4-E18 are intact."""
    hist_file = E19_DIR / "historical_integrity.json"
    assert hist_file.exists(), "historical_integrity.json missing"
    with open(hist_file) as f:
        data = json.load(f)
    assert data["all_phases_intact"] is True
    assert data["total_audited"] == 11
    for r in data["records"]:
        assert r["match"] is True
        assert r["status"] == "VERIFIED_IMMUTABLE"


def test_canonical_claims_audit():
    """Verify all 24 claims are registered and 0 unresolved."""
    claims_csv = E19_DIR / "claims" / "all_publication_claims.csv"
    assert claims_csv.exists(), "all_publication_claims.csv missing"
    with open(claims_csv, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 24
    statuses = [r["status"] for r in reader]
    assert statuses.count("PASS") == 23
    assert statuses.count("WARNING") == 1  # C14 superseded
    assert "UNRESOLVED" not in statuses
    assert "CONFLICT" not in statuses


def test_manuscript_superlatives_zero():
    """Verify zero ungrounded superlatives in main.tex."""
    main_tex = E19_DIR / "manuscript" / "main.tex"
    assert main_tex.exists(), "main.tex missing"
    content = main_tex.read_text(encoding="utf-8").lower()
    forbidden = ["proves", "guaranteed", "universally", "always", "never", "eliminates", "perfect", "definitive", "state-of-the-art"]
    for w in forbidden:
        assert w not in content, f"Forbidden word found: {w}"


def test_bibliography_verified():
    """Verify zero placeholders in references.bib."""
    bib_file = E19_DIR / "manuscript" / "references.bib"
    assert bib_file.exists(), "references.bib missing"
    content = bib_file.read_text(encoding="utf-8")
    assert "VERIFY" not in content
    assert "placeholder" not in content.lower()


def test_reviewer_attack_matrix():
    """Verify all 20 reviewer objections addressed."""
    rev_csv = E19_DIR / "reviewer" / "final_hostile_reviewer_matrix.csv"
    assert rev_csv.exists(), "final_hostile_reviewer_matrix.csv missing"
    with open(rev_csv, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 20
    for r in reader:
        assert len(r["evidence"]) > 0
        assert len(r["response"]) > 0


def test_reproduction_results():
    """Verify reproduction checks all pass."""
    repro_file = E19_DIR / "reproducibility" / "reproduction_results.json"
    assert repro_file.exists(), "reproduction_results.json missing"
    with open(repro_file) as f:
        data = json.load(f)
    assert data["all_passed"] is True
    for c in data["checks_executed"]:
        assert c["status"] == "PASS"


def test_ieee_tsg_compliance_matrix():
    """Verify TSG compliance matrix has zero FAIL."""
    tsg_csv = E19_DIR / "manuscript" / "ieee_tsg_compliance_matrix.csv"
    assert tsg_csv.exists(), "ieee_tsg_compliance_matrix.csv missing"
    with open(tsg_csv, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    statuses = [r["status"] for r in reader]
    assert "FAIL" not in statuses
