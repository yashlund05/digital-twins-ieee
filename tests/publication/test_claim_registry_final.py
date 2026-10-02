"""tests/publication/test_claim_registry_final.py — Tests for Phase 14 Final Claim Registry."""

import pytest

from src.audit.final_claims import FinalClaimRegistry
from src.publication.sources import FrozenSourceRegistry


@pytest.fixture
def final_registry():
    frozen_reg = FrozenSourceRegistry()
    reg = FinalClaimRegistry("configs/publication/phase14_final_audit.yaml")
    reg.verify_all_claims(frozen_reg)
    return reg


def test_all_18_claims_pass(final_registry):
    """Verify that all 18 canonical claims pass against frozen artifacts."""
    claims = final_registry.claims
    assert len(claims) >= 18

    failed = [c_id for c_id, c in claims.items() if c.status != "PASS"]
    assert len(failed) == 0, f"Claims failed: {failed}"


def test_baseline_e4_claims(final_registry):
    """Verify E4 baseline claims C01 through C04."""
    claims = final_registry.claims
    assert claims["C01"].verified_value == pytest.approx(0.977956, abs=1e-5)
    assert claims["C02"].verified_value == pytest.approx(0.538606, abs=1e-5)
    assert claims["C03"].verified_value == pytest.approx(0.117647, abs=1e-5)
    assert claims["C04"].verified_value == pytest.approx(0.088727, abs=1e-5)


def test_h3_statistics_claims(final_registry):
    """Verify H3 statistics claims C05 through C09."""
    claims = final_registry.claims
    assert claims["C05"].verified_value == pytest.approx(-1.223645, abs=1e-4)
    assert claims["C06"].verified_value == pytest.approx(-1.346260, abs=1e-4)
    assert claims["C07"].verified_value == pytest.approx(-1.113412, abs=1e-4)
    assert claims["C08"].verified_value == pytest.approx(1.0, abs=1e-4)
    assert claims["C09"].verified_value == "NOT_SUPPORTED"


def test_forecasting_baseline_claims(final_registry):
    """Verify forecasting baseline MAPE claims C15 through C17."""
    claims = final_registry.claims
    assert claims["C15"].verified_value == pytest.approx(8.950405, abs=1e-3)
    assert claims["C16"].verified_value == pytest.approx(9.063485, abs=1e-3)
    assert claims["C17"].verified_value == pytest.approx(14.732101, abs=1e-3)
