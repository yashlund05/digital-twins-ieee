"""tests/publication/test_phase21_final_author_submission.py — Phase 21 Author Submission Gate Tests."""

import json
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
E21_DIR = ROOT / "experiments" / "runs" / "E21_FINAL_AUTHOR_SUBMISSION_20261007"


def test_e21_directory_structure():
    """Verify all required subdirectories exist in E21 package."""
    assert E21_DIR.exists(), "E21 release package directory missing"
    assert (E21_DIR / "manuscript").is_dir()
    assert (E21_DIR / "supplementary").is_dir()
    assert (E21_DIR / "cover_letter").is_dir()
    assert (E21_DIR / "metadata").is_dir()
    assert (E21_DIR / "manifests").is_dir()
    assert (E21_DIR / "README.md").exists()
    assert (E21_DIR / "FINAL_SUBMISSION_CHECKLIST.md").exists()
    assert (E21_DIR / "HUMAN_ACTIONS_REQUIRED.md").exists()


def test_e21_author_metadata_structure():
    """Verify authors order, affiliation, and explicit placeholders in author_metadata.yaml."""
    yaml_path = E21_DIR / "metadata" / "author_metadata.yaml"
    assert yaml_path.exists(), "author_metadata.yaml missing in E21"
    with open(yaml_path, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    authors = meta.get("authors", [])
    assert len(authors) == 3, f"Expected 3 authors, got {len(authors)}"

    expected_authors = ["Ayush Vishwakarma", "Vipul Bhamare", "Yash Lund"]
    for idx, expected_name in enumerate(expected_authors):
        assert authors[idx]["name"] == expected_name
        assert authors[idx]["affiliation"] == "Vishwakarma University"
        assert authors[idx]["department"] == "DEPARTMENT_REQUIRED"
        assert authors[idx]["ieee_grade"] == "IEEE_MEMBERSHIP_GRADE_REQUIRED"
        assert authors[idx]["email"] == "REQUIRED_FROM_AUTHOR"

    assert meta["corresponding_author_designation"] == "CORRESPONDING_AUTHOR_REQUIRED"
    assert meta["zenodo"]["doi"] == "ZENODO_DOI_REQUIRED"


def test_e21_manuscript_author_block():
    """Verify manuscript main.tex formats author block with exact authors and explicit placeholders."""
    tex_path = E21_DIR / "manuscript" / "main.tex"
    assert tex_path.exists(), "main.tex missing in E21"
    content = tex_path.read_text(encoding="utf-8")

    assert "Ayush~Vishwakarma" in content
    assert "Vipul~Bhamare" in content
    assert "Yash~Lund" in content
    assert "Vishwakarma University" in content
    assert "[IEEE~MEMBERSHIP~GRADE~REQUIRED]" in content
    assert "[DEPARTMENT REQUIRED]" in content
    assert "[CORRESPONDING AUTHOR: CORRESPONDING\\_AUTHOR\\_REQUIRED]" in content
    assert "[FUNDING INFORMATION: FUNDING\\_INFORMATION\\_REQUIRED]" in content


def test_e21_cover_letter_authors():
    """Verify cover letter addresses IEEE TSG and includes verified author names and institution."""
    cl_path = E21_DIR / "cover_letter" / "DRAFT_IEEE_COVER_LETTER.md"
    assert cl_path.exists(), "DRAFT_IEEE_COVER_LETTER.md missing in E21"
    content = cl_path.read_text(encoding="utf-8")

    assert "Ayush Vishwakarma" in content
    assert "Vipul Bhamare" in content
    assert "Yash Lund" in content
    assert "Vishwakarma University" in content
    assert "IEEE Transactions on Smart Grid" in content


def test_e21_release_manifest_and_historical_integrity():
    """Verify E21 release manifest, sha256 checksums, and historical immutability."""
    rel_manifest_path = E21_DIR / "manifests" / "RELEASE_MANIFEST.json"
    sha_path = E21_DIR / "manifests" / "SHA256SUMS.txt"
    hist_manifest_path = E21_DIR / "manifests" / "HISTORICAL_INTEGRITY_MANIFEST.json"

    assert rel_manifest_path.exists()
    assert sha_path.exists()
    assert hist_manifest_path.exists()

    with open(rel_manifest_path, "r", encoding="utf-8") as f:
        rel_data = json.load(f)
    assert rel_data["verdict"] == "SUBMISSION_READY_WITH_MANUAL_CHECKS"
    assert rel_data["target_journal"] == "IEEE Transactions on Smart Grid"

    with open(hist_manifest_path, "r", encoding="utf-8") as f:
        hist_data = json.load(f)
    assert hist_data["all_phases_intact"] is True
    assert hist_data["total_audited"] == 12
