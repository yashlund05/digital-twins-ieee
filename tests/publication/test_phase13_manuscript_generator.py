"""tests/publication/test_phase13_manuscript_generator.py — Tests for manuscript generator."""

from pathlib import Path

from src.publication.manuscript_generator import (
    generate_full_manuscript,
    generate_manuscript_summary,
)


def test_generate_full_manuscript(tmp_path: Path):
    main_tex = generate_full_manuscript(tmp_path)
    assert main_tex.is_file()
    assert main_tex.name == "main.tex"

    content = main_tex.read_text(encoding="utf-8")
    assert "\\begin{document}" in content
    assert "\\begin{abstract}" in content
    assert "0.978" in content
    assert "H3" in content
    assert "NOT_SUPPORTED" in content or "not supported" in content.lower()
    assert "\\bibliography{references}" in content

    bib_file = tmp_path / "manuscript" / "references.bib"
    assert bib_file.is_file()


def test_generate_manuscript_summary(tmp_path: Path):
    generate_full_manuscript(tmp_path)
    summary = generate_manuscript_summary(tmp_path)
    assert "main.tex" in summary["files"]
    assert "references.bib" in summary["files"]
    assert len(summary["sections"]) >= 7
