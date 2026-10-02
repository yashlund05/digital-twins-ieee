"""src/publication — Phase 12 Paper-Ready Artifacts and IEEE Publication Package."""

from src.publication.figure_factory import build_all_figures
from src.publication.latex import build_all_latex
from src.publication.provenance import (
    build_figure_provenance,
    build_hash_manifest,
    build_table_provenance,
)
from src.publication.publication_runner import run_phase12_publication_pipeline
from src.publication.schemas import (
    FigureProvenanceRecord,
    Phase12Config,
    PublicationMetaConfig,
    SourceRunConfig,
    TableProvenanceRecord,
)
from src.publication.sources import FrozenSourceRegistry, load_phase12_sources_config
from src.publication.statistics_formatter import (
    format_ci,
    format_f1,
    format_p_value,
    format_percentage,
    format_scientific,
    sanitize_latex,
)
from src.publication.table_factory import build_all_tables
from src.publication.validation import (
    audit_scientific_language,
    clean_scientific_language,
    validate_publication_sources,
)

__all__ = [
    "FrozenSourceRegistry",
    "load_phase12_sources_config",
    "validate_publication_sources",
    "audit_scientific_language",
    "clean_scientific_language",
    "build_all_figures",
    "build_all_tables",
    "build_all_latex",
    "build_figure_provenance",
    "build_table_provenance",
    "build_hash_manifest",
    "run_phase12_publication_pipeline",
    "Phase12Config",
    "SourceRunConfig",
    "PublicationMetaConfig",
    "FigureProvenanceRecord",
    "TableProvenanceRecord",
    "format_f1",
    "format_percentage",
    "format_ci",
    "format_p_value",
    "format_scientific",
    "sanitize_latex",
]
