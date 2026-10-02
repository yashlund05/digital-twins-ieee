"""tests/unit/test_publication_provenance.py — Unit tests for Phase 12 provenance and audit manifests."""

from src.publication.figure_factory import build_all_figures
from src.publication.latex import build_all_latex
from src.publication.provenance import (
    build_figure_provenance,
    build_hash_manifest,
    build_table_provenance,
)
from src.publication.sources import FrozenSourceRegistry
from src.publication.table_factory import build_all_tables


def test_provenance_manifest_generation(tmp_path):
    out_dir = tmp_path / "pub_run"
    out_dir.mkdir()
    (out_dir / "provenance").mkdir()

    registry = FrozenSourceRegistry()

    build_all_figures(registry, out_dir)
    build_all_tables(registry, out_dir)
    build_all_latex(out_dir)

    fig_prov = build_figure_provenance(out_dir, registry.source_hashes)
    assert len(fig_prov) == 8
    assert (out_dir / "provenance" / "figure_provenance.json").is_file()

    tbl_prov = build_table_provenance(out_dir, registry.source_hashes)
    assert len(tbl_prov) == 6
    assert (out_dir / "provenance" / "table_provenance.json").is_file()

    hash_man = build_hash_manifest(out_dir, registry.source_hashes)
    assert hash_man["total_generated_files_hashed"] > 20
    assert (out_dir / "provenance" / "hash_manifest.json").is_file()
