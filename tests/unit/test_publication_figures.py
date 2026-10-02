"""tests/unit/test_publication_figures.py — Unit tests for Phase 12 figure generation."""

from pathlib import Path

import pandas as pd

from src.publication.figure_factory import (
    generate_figure_01_architecture,
    generate_figure_02_baseline_reconciliation,
    generate_figure_03_anomaly_staleness,
    generate_figure_04_load_estimation,
    generate_figure_05_representation_transition,
    generate_figure_06_multiseed_uncertainty,
    generate_figure_07_aoi_transient,
    generate_figure_08_h3_forest,
)
from src.publication.sources import FrozenSourceRegistry


def test_generate_all_figures(tmp_path):
    fig_dir = tmp_path / "figures"
    fig_dir.mkdir()
    src_dir = tmp_path / "source_data"
    src_dir.mkdir()

    registry = FrozenSourceRegistry()

    f1 = generate_figure_01_architecture(fig_dir, src_dir)
    f2 = generate_figure_02_baseline_reconciliation(registry, fig_dir, src_dir)
    f3 = generate_figure_03_anomaly_staleness(registry, fig_dir, src_dir)
    f4 = generate_figure_04_load_estimation(registry, fig_dir, src_dir)
    f5 = generate_figure_05_representation_transition(registry, fig_dir, src_dir)
    f6 = generate_figure_06_multiseed_uncertainty(registry, fig_dir, src_dir)
    f7 = generate_figure_07_aoi_transient(registry, fig_dir, src_dir)
    f8 = generate_figure_08_h3_forest(registry, fig_dir, src_dir)

    for i, res in enumerate([f1, f2, f3, f4, f5, f6, f7, f8], 1):
        png = Path(res["png"])
        pdf = Path(res["pdf"])
        csv = Path(res["csv"])

        assert png.is_file(), f"Figure {i} PNG does not exist"
        assert pdf.is_file(), f"Figure {i} PDF does not exist"
        assert csv.is_file(), f"Figure {i} CSV does not exist"

        assert png.stat().st_size > 1000
        assert pdf.stat().st_size > 1000
        assert csv.stat().st_size > 50

        # Check source CSV is valid tabular data
        df = pd.read_csv(csv)
        assert len(df) > 0
