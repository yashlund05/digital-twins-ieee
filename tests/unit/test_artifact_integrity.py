"""tests/unit/test_artifact_integrity.py — Unit tests for artifact integrity checking."""

import pandas as pd
import pytest

from src.reproducibility.artifact_integrity import verify_artifacts, verify_file_parseable


def test_verify_file_parseable(tmp_path):
    # Valid JSON
    j = tmp_path / "valid.json"
    j.write_text('{"status": "ok"}', encoding="utf-8")
    ok, msg = verify_file_parseable(j)
    assert ok is True

    # Invalid JSON
    j_bad = tmp_path / "bad.json"
    j_bad.write_text('{status: ok}', encoding="utf-8")
    ok, msg = verify_file_parseable(j_bad)
    assert ok is False

    # Valid CSV
    c = tmp_path / "valid.csv"
    c.write_text("x,y\n1,2\n", encoding="utf-8")
    ok, msg = verify_file_parseable(c)
    assert ok is True

    # Empty CSV
    c_empty = tmp_path / "empty.csv"
    c_empty.write_text("", encoding="utf-8")
    ok, msg = verify_file_parseable(c_empty)
    assert ok is False


def test_verify_artifacts_pass(tmp_path):
    run_dir = tmp_path / "run_pass"
    run_dir.mkdir()
    (run_dir / "metrics.json").write_text('{"score": 1.0}', encoding="utf-8")
    df = pd.DataFrame({"condition_id": ["C1", "C2"], "val": [10, 20]})
    df.to_csv(run_dir / "comparison.csv", index=False)

    report = verify_artifacts(
        run_dir=run_dir,
        expected_files=["metrics.json", "comparison.csv"],
        expected_condition_count=2,
        condition_column="condition_id",
    )

    assert report["status"] == "PASS"
    assert report["all_valid"] is True
    assert report["total_files_checked"] == 2
    assert report["condition_check"] == "PASS"
    assert len(report["missing_files"]) == 0
    assert len(report["corrupted_files"]) == 0


def test_verify_artifacts_missing_and_corrupt(tmp_path):
    run_dir = tmp_path / "run_fail"
    run_dir.mkdir()
    (run_dir / "bad.json").write_text("not json content!", encoding="utf-8")

    report = verify_artifacts(
        run_dir=run_dir,
        expected_files=["missing.json"],
    )

    assert report["all_valid"] is False
    assert "missing.json" in report["missing_files"]
    assert "bad.json" in report["corrupted_files"]
