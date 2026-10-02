"""src/publication — Phase 12 & Phase 13 Publication Infrastructure.

Provides paper-ready artifacts, IEEE manuscript generation, and scientific audit capabilities:
- FrozenSourceRegistry: Read-only access to historical experiment runs (E4–E11)
- Phase13SourceRegistry: Canonical claim-to-evidence registry
- NumericalConsistencyAudit: Numerical verification across phases
- CrossPhaseConsistencyAudit: Cross-phase mathematical consistency
- Language audit: Prohibited overclaim detection
- Manuscript assembly: IEEE TSG-style LaTeX generation
"""

# Phase 12 exports
# Phase 13 exports
from src.publication.claim_audit import (
    audit_manuscript_claims,
    extract_numerical_claims,
    map_claim_to_source,
)
from src.publication.cross_phase_audit import CrossPhaseConsistencyAudit
from src.publication.figure_factory import build_all_figures
from src.publication.language_audit import (
    LanguageAuditFinding,
    LanguageAuditReport,
    audit_manuscript_directory,
    audit_manuscript_language,
    export_language_audit_report,
)
from src.publication.latex import build_all_latex
from src.publication.manuscript_generator import (
    generate_full_manuscript,
    generate_manuscript_summary,
)
from src.publication.numerical_audit import NumericalConsistencyAudit
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
from src.publication.source_registry import (
    CanonicalClaim,
    Phase13SourceRegistry,
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
    # Phase 12
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
    # Phase 13
    "CanonicalClaim",
    "Phase13SourceRegistry",
    "NumericalConsistencyAudit",
    "CrossPhaseConsistencyAudit",
    "LanguageAuditFinding",
    "LanguageAuditReport",
    "audit_manuscript_language",
    "audit_manuscript_directory",
    "export_language_audit_report",
    "audit_manuscript_claims",
    "extract_numerical_claims",
    "map_claim_to_source",
    "generate_full_manuscript",
    "generate_manuscript_summary",
]
