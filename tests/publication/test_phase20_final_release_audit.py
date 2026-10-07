"""tests/publication/test_phase20_final_release_audit.py — Phase 20 Final Release Test Suite."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
E20_DIR = ROOT / "experiments" / "runs" / "E20_FINAL_SUBMISSION_RELEASE_20261007"


def test_e20_historical_immutability():
    """Verify all 12 historical phases E4-E19 are intact."""
    hist_file = E20_DIR / "HISTORICAL_INTEGRITY_MANIFEST.json"
    assert hist_file.exists(), "HISTORICAL_INTEGRITY_MANIFEST.json missing"
    with open(hist_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["all_phases_intact"] is True
    assert data["total_audited"] == 12
    for r in data["records"]:
        assert r["match"] is True
        assert r["status"] == "VERIFIED_IMMUTABLE"


def test_e20_release_manifest_and_sha256sums():
    """Verify release manifest and checksum file integrity."""
    rel_manifest = E20_DIR / "RELEASE_MANIFEST.json"
    sums_file = E20_DIR / "SHA256SUMS.txt"
    assert rel_manifest.exists(), "RELEASE_MANIFEST.json missing"
    assert sums_file.exists(), "SHA256SUMS.txt missing"
    with open(rel_manifest, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["release_verdict"] == "SUBMISSION_READY_WITH_MANUAL_CHECKS"
    assert data["historical_phases_intact"] == 12
    assert len(data["files"]) > 0


def test_e20_claim_matrix_completeness():
    """Verify all 24 claims are present in consistency matrix."""
    matrix_file = E20_DIR / "CLAIM_CONSISTENCY_MATRIX.md"
    assert matrix_file.exists(), "CLAIM_CONSISTENCY_MATRIX.md missing"
    content = matrix_file.read_text(encoding="utf-8")
    for i in range(1, 25):
        cid = f"C{i:02d}"
        assert cid in content, f"Claim {cid} missing from matrix"


def test_e20_manuscript_cleanliness():
    """Verify manuscript in E20 is free of superlatives and placeholders."""
    tex_file = E20_DIR / "manuscript" / "main.tex"
    bib_file = E20_DIR / "manuscript" / "references.bib"
    assert tex_file.exists(), "main.tex missing in E20"
    assert bib_file.exists(), "references.bib missing in E20"
    tex_txt = tex_file.read_text(encoding="utf-8").lower()
    forbidden = ["proves", "guaranteed", "universally", "always", "never", "eliminates", "perfect", "definitive", "state-of-the-art"]
    for w in forbidden:
        assert w not in tex_txt, f"Forbidden superlative: {w}"
    bib_txt = bib_file.read_text(encoding="utf-8")
    assert "VERIFY" not in bib_txt


def test_e20_author_metadata_uninvented():
    """Verify author metadata contains verified authors and unsupplied placeholders without fabrication."""
    yaml_file = ROOT / "configs" / "publication" / "author_metadata.yaml"
    assert yaml_file.exists(), "author_metadata.yaml missing"
    content = yaml_file.read_text(encoding="utf-8")
    assert "Ayush Vishwakarma" in content
    assert "Vipul Bhamare" in content
    assert "Yash Lund" in content
    assert "Vishwakarma University" in content
    assert "ZENODO_DOI_REQUIRED" in content
    assert "DEPARTMENT_REQUIRED" in content
    assert "REQUIRED_FROM_AUTHOR" in content
