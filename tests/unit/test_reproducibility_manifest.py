"""tests/unit/test_reproducibility_manifest.py — Unit tests for reproducibility manifest generation."""

from pathlib import Path
import pytest

from src.reproducibility.run_manifest import create_reproducibility_manifest
from src.utils.io import load_json


def test_create_reproducibility_manifest(tmp_path):
    out_dir = tmp_path / "run_test"
    out_dir.mkdir()
    (out_dir / "sample.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    manifest = create_reproducibility_manifest(
        experiment_id="E11",
        run_id="TEST_RUN_001",
        output_dir=out_dir,
        config_hash="abc123canonicalhash",
        seed=42,
        reproducibility_status="PASS",
        extra_metadata={"custom_key": "custom_val"},
    )

    assert manifest["experiment_id"] == "E11"
    assert manifest["run_id"] == "TEST_RUN_001"
    assert manifest["seed"] == 42
    assert manifest["config_hash"] == "abc123canonicalhash"
    assert manifest["reproducibility_status"] == "PASS"
    assert manifest["extra_metadata"]["custom_key"] == "custom_val"
    assert "environment" in manifest
    assert "file_hashes" in manifest
    assert "sample.csv" in manifest["file_hashes"]

    # Verify written to disk
    disk_manifest = load_json(out_dir / "manifest.json")
    assert disk_manifest["run_id"] == "TEST_RUN_001"
