"""tests/publication/test_phase13_source_registry.py — Tests for Phase 13 source registry."""

from pathlib import Path

import pytest

from src.publication.source_registry import Phase13SourceRegistry
from src.publication.sources import FrozenSourceRegistry


def test_registry_initialization():
    """Verify registry loads config and builds claims properly."""
    reg = Phase13SourceRegistry("configs/publication/phase13_publication.yaml")
    assert len(reg.claims) >= 13
    assert "C01" in reg.claims
    assert "C05" in reg.claims
    assert "C13" in reg.claims


def test_get_claim():
    """Verify retrieval of individual canonical claims."""
    reg = Phase13SourceRegistry("configs/publication/phase13_publication.yaml")
    claim_c01 = reg.get_claim("C01")
    assert claim_c01.claim_id == "C01"
    assert claim_c01.value == 0.977956
    assert claim_c01.source_phase == "phase7_e4"

    claim_c09 = reg.get_claim("C09")
    assert claim_c09.value == "NOT_SUPPORTED"

    with pytest.raises(KeyError):
        reg.get_claim("NON_EXISTENT_CLAIM")


def test_verify_all_claims():
    """Verify that all canonical claims pass against frozen artifacts."""
    frozen_reg = FrozenSourceRegistry()
    reg = Phase13SourceRegistry("configs/publication/phase13_publication.yaml")
    claims = reg.verify_all_claims(frozen_reg)

    summary = reg.summary()
    assert summary["total_claims"] >= 13
    assert summary["failed_claims"] == 0
    assert summary["verified_claims"] == summary["total_claims"]

    # Check key claims specifically
    assert claims["C01"].verified is True
    assert claims["C05"].verified is True
    assert claims["C09"].verified is True
    assert claims["C10"].verified is True
    assert claims["C11"].verified is True
    assert claims["C12"].verified is True
    assert claims["C13"].verified is True


def test_export_registry(tmp_path: Path):
    """Verify export to JSON."""
    frozen_reg = FrozenSourceRegistry()
    reg = Phase13SourceRegistry("configs/publication/phase13_publication.yaml")
    reg.verify_all_claims(frozen_reg)

    out_file = tmp_path / "registry.json"
    reg.export_registry(out_file)
    assert out_file.is_file()
    assert out_file.stat().st_size > 0
