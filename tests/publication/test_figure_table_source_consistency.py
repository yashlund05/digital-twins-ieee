"""tests/publication/test_figure_table_source_consistency.py — Tests for Figure & Table Source Linkage."""

import pytest

from src.audit.cross_phase_auditor import CrossPhaseScientificAuditor
from src.publication.sources import FrozenSourceRegistry


def test_figure_table_traceability():
    """Verify all 8 figures and 6 tables have valid, non-empty source CSVs."""
    frozen_reg = FrozenSourceRegistry()
    auditor = CrossPhaseScientificAuditor(frozen_reg)
    res = auditor.verify_figure_table_source_linkage()

    assert res["status"] == "PASS"
    assert res["figures_audited"] == 8
    assert res["tables_audited"] == 6

    # Verify every individual figure has source data
    for fig_id, fig_info in res["figures"].items():
        assert fig_info["traceable"] is True, f"Figure {fig_id} is not traceable"

    # Verify every individual table has source data
    for tab_id, tab_info in res["tables"].items():
        assert tab_info["traceable"] is True, f"Table {tab_id} is not traceable"
