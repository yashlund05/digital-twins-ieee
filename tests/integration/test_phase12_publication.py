"""tests/integration/test_phase12_publication.py — End-to-end integration test for Phase 12 pipeline."""

from pathlib import Path
import pytest
import pandas as pd

from src.publication.publication_runner import run_phase12_publication_pipeline
from src.utils.io import load_json


def test_phase12_end_to_end_pipeline(tmp_path):
    out_dir = tmp_path / "E12_TEST_RUN"

    res_dir = run_phase12_publication_pipeline(
        config_path="configs/publication/phase12_sources.yaml",
        output_dir_override=out_dir,
        strict=True,
    )

    assert res_dir == out_dir
    assert out_dir.is_dir()

    # 1. Check Reports
    assert (out_dir / "summary.md").is_file()
    assert (out_dir / "publication_readme.md").is_file()
    assert (out_dir / "integrity_report.json").is_file()
    assert (out_dir / "source_registry.json").is_file()
    assert (out_dir / "manifest.json").is_file()

    manifest = load_json(out_dir / "manifest.json")
    assert manifest["reproducibility_status"] == "PASS"

    # 2. Check Figures (8 PNG + 8 PDF)
    fig_dir = out_dir / "figures"
    src_data_dir = out_dir / "source_data"
    for i in range(1, 9):
        pngs = list(fig_dir.glob(f"fig_0{i}_*.png"))
        pdfs = list(fig_dir.glob(f"fig_0{i}_*.pdf"))
        csvs = list(src_data_dir.glob(f"fig_0{i}_source.csv"))

        assert len(pngs) == 1, f"Missing fig_0{i} PNG"
        assert len(pdfs) == 1, f"Missing fig_0{i} PDF"
        assert len(csvs) == 1, f"Missing fig_0{i} source CSV"

    # 3. Check Tables (6 CSV + 6 TeX)
    tbl_dir = out_dir / "tables"
    for i in range(1, 7):
        csvs = list(tbl_dir.glob(f"table_0{i}_*.csv"))
        texs = list(tbl_dir.glob(f"table_0{i}_*.tex"))

        assert len(csvs) == 1, f"Missing table_0{i} CSV"
        assert len(texs) == 1, f"Missing table_0{i} TeX"

    # Table 3 must have all 24 conditions
    t3 = pd.read_csv(tbl_dir / "table_03_e5_condition_summary.csv")
    assert len(t3) == 24

    # Table 4 must have multi-seed H3 results
    t4 = pd.read_csv(tbl_dir / "table_04_multiseed_results.csv")
    assert len(t4) == 6
    assert (t4["delta_beta"] < 0).all()

    # 4. Check LaTeX Documents
    lat_dir = out_dir / "latex"
    for req_tex in ["figures.tex", "tables.tex", "notation.tex", "publication_results.tex", "phase12_artifacts.tex"]:
        assert (lat_dir / req_tex).is_file()

    # 5. Check Provenance
    prov_dir = out_dir / "provenance"
    assert (prov_dir / "figure_provenance.json").is_file()
    assert (prov_dir / "table_provenance.json").is_file()
    assert (prov_dir / "hash_manifest.json").is_file()
    assert (prov_dir / "language_audit.json").is_file()
