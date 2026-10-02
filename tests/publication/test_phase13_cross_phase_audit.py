"""tests/publication/test_phase13_cross_phase_audit.py — Tests for cross-phase consistency audit."""

from pathlib import Path
import pytest

from src.publication.cross_phase_audit import CrossPhaseConsistencyAudit
from src.publication.sources import FrozenSourceRegistry


@pytest.fixture
def cross_audit():
    frozen_reg = FrozenSourceRegistry()
    return CrossPhaseConsistencyAudit(frozen_reg)


def test_verify_e4_e11_reproducibility(cross_audit):
    res = cross_audit.verify_e4_e11_reproducibility()
    assert res["status"] == "PASS"
    assert res["details"]["passed"] is True
    assert res["details"]["max_absolute_difference"] < 1e-4


def test_verify_e5_e10_seed_consistency(cross_audit):
    res = cross_audit.verify_e5_e10_seed_consistency()
    assert res["status"] == "PASS"
    assert res["details"]["e5_condition_count"] == 24
    assert res["details"]["e10_s42_condition_count"] == 24
    assert res["details"]["conditions_identical"] is True


def test_verify_h3_consistency(cross_audit):
    res = cross_audit.verify_h3_consistency()
    assert res["status"] == "PASS"
    assert res["details"]["passed"] is True
    assert res["details"]["decision"] == "NOT_SUPPORTED"


def test_verify_all_seeds_not_supported(cross_audit):
    res = cross_audit.verify_all_seeds_not_supported()
    assert res["status"] == "PASS"
    assert res["details"]["all_consistent"] is True
    assert res["details"]["total_rows_checked"] == 6


def test_run_full_cross_phase_audit(cross_audit, tmp_path: Path):
    report = cross_audit.run_full_audit()
    assert report["overall_status"] == "PASS"
    assert report["passed_checks"] == 4
    assert report["failed_checks"] == 0

    out_file = tmp_path / "cross_phase_report.json"
    cross_audit.export_report(out_file)
    assert out_file.is_file()
