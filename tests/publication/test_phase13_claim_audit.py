"""tests/publication/test_phase13_claim_audit.py — Tests for Phase 13 claim audit."""

import pytest

from src.publication.claim_audit import (
    audit_manuscript_claims,
    extract_numerical_claims,
    map_claim_to_source,
)
from src.publication.source_registry import Phase13SourceRegistry
from src.publication.sources import FrozenSourceRegistry


@pytest.fixture
def source_registry():
    frozen_reg = FrozenSourceRegistry()
    reg = Phase13SourceRegistry("configs/publication/phase13_publication.yaml")
    reg.verify_all_claims(frozen_reg)
    return reg


def test_extract_numerical_claims():
    text = "We report F1 = 0.978 with staleness of 5s and 10.5% degradation."
    claims = extract_numerical_claims(text)
    assert len(claims) >= 3
    values = [c["value"] for c in claims]
    assert any(abs(v - 0.978) < 1e-3 for v in values)
    assert any(abs(v - 5.0) < 1e-3 for v in values)


def test_map_claim_to_source(source_registry):
    matches = map_claim_to_source(0.977956, source_registry, tolerance=1e-4)
    assert "C01" in matches

    matches_h3 = map_claim_to_source(-1.2236, source_registry, tolerance=1e-3)
    assert "C05" in matches_h3


def test_audit_manuscript_claims(source_registry):
    text = (
        "The model achieves an F1 score of 0.977956 under baseline conditions. "
        "The H3 effect size was observed as -1.2236."
    )
    res = audit_manuscript_claims(text, source_registry)
    assert res["status"] == "success"
    assert res["matched"] >= 2
    assert res["total_claims_checked"] >= 2
