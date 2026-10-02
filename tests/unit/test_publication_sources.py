"""tests/unit/test_publication_sources.py — Unit tests for Phase 12 frozen source loader and registry."""

from pathlib import Path
import pytest

from src.publication.sources import FrozenSourceRegistry, load_phase12_sources_config
from src.publication.validation import validate_publication_sources


def test_load_phase12_sources_config():
    cfg = load_phase12_sources_config()
    assert "source_runs" in cfg
    assert "phase7_e4" in cfg["source_runs"]
    assert "phase8_e5" in cfg["source_runs"]
    assert "phase9_e6" in cfg["source_runs"]
    assert "phase10_e10" in cfg["source_runs"]
    assert "phase11_e11" in cfg["source_runs"]


def test_frozen_source_registry_validation():
    registry = FrozenSourceRegistry()
    val_report = validate_publication_sources(registry)

    assert val_report["sources_exist"] is True
    assert val_report["completeness_e5_24"] is True
    assert val_report["completeness_e10_120"] is True
    assert val_report["completeness_e11_88"] is True
    assert val_report["baseline_reconciled"] is True
    assert val_report["overall_status"] == "PASS"
    assert len(val_report["errors"]) == 0


def test_source_data_loaders():
    registry = FrozenSourceRegistry()

    # Phase 7
    e4_m = registry.load_phase7_e4_metrics()
    assert isinstance(e4_m, dict)

    # Phase 8
    e5_df = registry.load_phase8_e5_comparison()
    assert len(e5_df) > 0
    assert e5_df["condition_id"].nunique() == 24

    # Phase 10
    e10_seeds = registry.load_phase10_e10_seed_results()
    assert len(e10_seeds["seed"].unique()) == 5
    assert len(e10_seeds.groupby(["seed", "condition_id"])) == 120

    # Phase 11
    e11_repro = registry.load_phase11_reproducibility()
    assert len(e11_repro) == 4
