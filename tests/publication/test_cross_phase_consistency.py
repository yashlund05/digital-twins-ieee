"""tests/publication/test_cross_phase_consistency.py — Tests for Cross-Phase Scientific Consistency."""

import pytest

from src.audit.cross_phase_auditor import CrossPhaseScientificAuditor
from src.publication.sources import FrozenSourceRegistry


@pytest.fixture
def auditor():
    frozen_reg = FrozenSourceRegistry()
    return CrossPhaseScientificAuditor(frozen_reg)


def test_experimental_condition_coherence(auditor):
    res = auditor.verify_experimental_condition_coherence()
    assert res["status"] == "PASS"
    assert res["details"]["e5_unique_conditions"] == 24
    assert res["details"]["total_seed_conditions"] == 120
    assert res["details"]["seeds_matched"] is True


def test_baseline_reproducibility_coherence(auditor):
    res = auditor.verify_baseline_reproducibility_coherence()
    assert res["status"] == "PASS"
    assert res["details"]["e11_max_reproduction_difference"] < 1e-4


def test_h3_statistics_coherence(auditor):
    res = auditor.verify_h3_statistics_coherence()
    assert res["status"] == "PASS"
    assert res["details"]["all_seeds_delta_beta_negative"] is True
    assert res["details"]["all_seeds_decision_not_supported"] is True
