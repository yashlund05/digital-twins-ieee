"""tests/unit/test_publication_tables.py — Unit tests for Phase 12 publication tables."""

from pathlib import Path
import pytest
import pandas as pd

from src.publication.sources import FrozenSourceRegistry
from src.publication.table_factory import (
    generate_table_01_configuration,
    generate_table_02_reconciliation,
    generate_table_03_e5_conditions,
    generate_table_04_multiseed,
    generate_table_05_ablations,
    generate_table_06_h3_statistics,
)


def test_generate_all_tables(tmp_path):
    tbl_dir = tmp_path / "tables"
    tbl_dir.mkdir()

    registry = FrozenSourceRegistry()

    t1_df, t1_tex = generate_table_01_configuration(tbl_dir)
    assert len(t1_df) >= 10
    assert (tbl_dir / "table_01_experimental_configuration.csv").is_file()
    assert (tbl_dir / "table_01_experimental_configuration.tex").is_file()

    t2_df, t2_tex = generate_table_02_reconciliation(registry, tbl_dir)
    assert len(t2_df) == 4
    assert (tbl_dir / "table_02_baseline_reconciliation.csv").is_file()
    assert (tbl_dir / "table_02_baseline_reconciliation.tex").is_file()

    t3_df, t3_tex = generate_table_03_e5_conditions(registry, tbl_dir)
    assert len(t3_df) == 24
    assert (tbl_dir / "table_03_e5_condition_summary.csv").is_file()
    assert (tbl_dir / "table_03_e5_condition_summary.tex").is_file()

    t4_df, t4_tex = generate_table_04_multiseed(registry, tbl_dir)
    assert len(t4_df) == 6
    assert (tbl_dir / "table_04_multiseed_results.csv").is_file()
    assert (tbl_dir / "table_04_multiseed_results.tex").is_file()

    t5_df, t5_tex = generate_table_05_ablations(registry, tbl_dir)
    assert len(t5_df) == 8
    assert (tbl_dir / "table_05_ablation_summary.csv").is_file()
    assert (tbl_dir / "table_05_ablation_summary.tex").is_file()

    t6_df, t6_tex = generate_table_06_h3_statistics(registry, tbl_dir)
    assert len(t6_df) == 9
    assert (tbl_dir / "table_06_h3_statistics.csv").is_file()
    assert (tbl_dir / "table_06_h3_statistics.tex").is_file()
