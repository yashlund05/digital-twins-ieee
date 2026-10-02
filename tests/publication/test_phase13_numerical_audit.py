"""tests/publication/test_phase13_numerical_audit.py — Tests for Phase 13 numerical audit."""

from pathlib import Path

import pytest

from src.publication.numerical_audit import NumericalConsistencyAudit
from src.publication.source_registry import Phase13SourceRegistry
from src.publication.sources import FrozenSourceRegistry


@pytest.fixture
def audit_instances():
    frozen_reg = FrozenSourceRegistry()
    source_reg = Phase13SourceRegistry("configs/publication/phase13_publication.yaml")
    source_reg.verify_all_claims(frozen_reg)
    audit = NumericalConsistencyAudit(source_reg, frozen_reg)
    return audit, source_reg, frozen_reg


def test_verify_e4_baseline(audit_instances):
    audit, _, _ = audit_instances
    res = audit.verify_e4_baseline()
    assert res["status"] == "PASS"
    assert res["details"]["Residual + LSTM-AE"]["passed"] is True
    assert res["details"]["Raw + LSTM-AE"]["passed"] is True
    assert res["details"]["Raw + IF"]["passed"] is True
    assert res["details"]["Residual + IF"]["passed"] is True


def test_verify_e10_h3(audit_instances):
    audit, _, _ = audit_instances
    res = audit.verify_e10_h3()
    assert res["status"] == "PASS"
    assert res["details"]["delta_beta"]["passed"] is True
    assert res["details"]["decision"]["actual"] == "NOT_SUPPORTED"


def test_verify_e11_change_point(audit_instances):
    audit, _, _ = audit_instances
    res = audit.verify_e11_change_point()
    assert res["status"] == "PASS"
    assert res["details"]["estimated_transition_aoi_seconds"]["actual"] == 0.0
    assert res["details"]["detection_status"]["actual"] == "DETECTED"


def test_verify_completeness(audit_instances):
    audit, _, _ = audit_instances
    res_e5 = audit.verify_e5_completeness()
    assert res_e5["status"] == "PASS"
    assert res_e5["details"]["actual_conditions"] == 24

    res_e10 = audit.verify_e10_completeness()
    assert res_e10["status"] == "PASS"
    assert res_e10["details"]["actual_seed_conditions"] == 120

    res_e11 = audit.verify_e11_completeness()
    assert res_e11["status"] == "PASS"


def test_run_full_audit(audit_instances, tmp_path: Path):
    audit, _, _ = audit_instances
    report = audit.run_full_audit()
    assert report["overall_status"] == "PASS"
    assert report["passed_checks"] == 6
    assert report["failed_checks"] == 0

    out_file = tmp_path / "numerical_report.json"
    audit.export_report(out_file)
    assert out_file.is_file()
