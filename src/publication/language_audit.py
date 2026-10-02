"""src/publication/language_audit.py — Extended scientific language audit for Phase 13 manuscript.

Extends the Phase 12 validation.py language audit with comprehensive scanning
for overclaims, unsupported causal language, and non-conservative scientific phrasing
per Phase 13 Section 0 Rule 2: OBSERVATION ≠ INTERPRETATION ≠ CAUSAL CLAIM.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.publication.validation import PROHIBITED_PHRASES as BASE_PROHIBITED
from src.utils.io import save_json
from src.utils.logging import get_logger

logger = get_logger("publication.language_audit")


# Extended prohibited phrases beyond Phase 12 base set
EXTENDED_PROHIBITED_PHRASES: list[str] = [
    # Causal overclaims
    "causes",
    "proves that",
    "proves",
    "demonstrates that staleness causes",
    "confirms the causal",
    "establishes causality",
    "causal relationship",
    "causal mechanism",
    # Universal claims
    "always",
    "never fails",
    "in all cases",
    "without exception",
    "universally",
    "for all systems",
    "for all feeders",
    # Certainty overclaims
    "certainly",
    "undoubtedly",
    "unquestionably",
    "indisputably",
    "conclusively proves",
    "definitively shows",
    # H3 reversal language
    "H3 is supported",
    "H3 was supported",
    "hypothesis is confirmed",
    "hypothesis was confirmed",
    # AoI overclaims
    "universal threshold",
    "universal AoI",
    "exact threshold",
    "the optimal AoI",
]

# Phrases that should be used with caution (warning, not error)
CAUTIONARY_PHRASES: list[str] = [
    "significant",
    "optimal",
    "best",
    "worst",
    "failure",
    "success",
    "breakthrough",
    "novel contribution",
    "first to",
    "unprecedented",
]

# Recommended replacements for overclaiming language
EXTENDED_REPLACEMENTS: dict[str, str] = {
    "causes": "is associated with",
    "proves that": "provides evidence suggesting that",
    "proves": "provides evidence for",
    "causal relationship": "observed association",
    "causal mechanism": "hypothesized mechanism",
    "always": "consistently under tested conditions",
    "never fails": "did not fail under the evaluated conditions",
    "in all cases": "across all evaluated conditions",
    "certainly": "based on our experimental evidence",
    "undoubtedly": "based on the observed results",
    "conclusively proves": "provides consistent evidence that",
    "definitively shows": "suggests under the evaluated conditions",
    "universal threshold": "empirically observed transition threshold",
    "universal AoI": "the evaluated AoI range",
    "the optimal AoI": "the empirically identified AoI operating point",
}


@dataclass
class LanguageAuditFinding:
    """A single finding from the language audit."""

    phrase: str
    severity: str  # "ERROR" or "WARNING"
    line_number: int
    context: str
    suggested_replacement: str


@dataclass
class LanguageAuditReport:
    """Full report from scanning one or more manuscript files."""

    status: str = "PASS"
    total_files_scanned: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    findings: list[dict[str, Any]] = field(default_factory=list)
    files_scanned: list[str] = field(default_factory=list)


def _get_context(lines: list[str], line_idx: int, window: int = 1) -> str:
    """Extract surrounding context for a finding."""
    start = max(0, line_idx - window)
    end = min(len(lines), line_idx + window + 1)
    return " ... ".join(lines[start:end]).strip()[:200]


def audit_manuscript_language(text: str, filename: str = "<text>") -> LanguageAuditReport:
    """Perform comprehensive language audit on manuscript text.

    Parameters
    ----------
    text : str
        The manuscript text to audit (LaTeX, Markdown, or plain text).
    filename : str
        Identifier for the text source, used in reporting.

    Returns
    -------
    LanguageAuditReport
        Audit report with all findings.
    """
    report = LanguageAuditReport(
        total_files_scanned=1,
        files_scanned=[filename],
    )

    lines = text.split("\n")
    text_lower = text.lower()

    # Check base prohibited phrases (ERROR level)
    all_prohibited = list(BASE_PROHIBITED) + EXTENDED_PROHIBITED_PHRASES
    for phrase in all_prohibited:
        phrase_lower = phrase.lower()
        for match in re.finditer(re.escape(phrase_lower), text_lower):
            # Find the line number
            line_num = text[: match.start()].count("\n") + 1
            line_idx = line_num - 1
            context = _get_context(lines, line_idx)

            # Skip if inside a comment or citation
            line_text = lines[line_idx].strip() if line_idx < len(lines) else ""
            if line_text.startswith("%") or line_text.startswith("<!--"):
                continue

            replacement = EXTENDED_REPLACEMENTS.get(
                phrase_lower,
                "carefully bounded phrasing",
            )
            report.findings.append(
                {
                    "phrase": phrase,
                    "severity": "ERROR",
                    "line_number": line_num,
                    "file": filename,
                    "context": context,
                    "suggested_replacement": replacement,
                }
            )
            report.total_errors += 1

    # Check cautionary phrases (WARNING level)
    for phrase in CAUTIONARY_PHRASES:
        phrase_lower = phrase.lower()
        for match in re.finditer(r"\b" + re.escape(phrase_lower) + r"\b", text_lower):
            line_num = text[: match.start()].count("\n") + 1
            line_idx = line_num - 1
            context = _get_context(lines, line_idx)

            line_text = lines[line_idx].strip() if line_idx < len(lines) else ""
            if line_text.startswith("%") or line_text.startswith("<!--"):
                continue

            report.findings.append(
                {
                    "phrase": phrase,
                    "severity": "WARNING",
                    "line_number": line_num,
                    "file": filename,
                    "context": context,
                    "suggested_replacement": f"Use '{phrase}' with qualification (e.g., 'statistically significant', 'empirically optimal')",
                }
            )
            report.total_warnings += 1

    report.status = "PASS" if report.total_errors == 0 else "FLAGGED"
    return report


def audit_manuscript_directory(
    manuscript_dir: Path,
    extensions: tuple[str, ...] = (".tex", ".md", ".bib"),
) -> LanguageAuditReport:
    """Audit all manuscript files in a directory.

    Parameters
    ----------
    manuscript_dir : Path
        Directory containing manuscript files.
    extensions : tuple[str, ...]
        File extensions to scan.

    Returns
    -------
    LanguageAuditReport
        Combined audit report across all files.
    """
    combined = LanguageAuditReport()
    manuscript_path = Path(manuscript_dir)

    if not manuscript_path.is_dir():
        logger.warning("Manuscript directory not found: %s", manuscript_path)
        combined.status = "SKIPPED"
        return combined

    for ext in extensions:
        for fpath in manuscript_path.rglob(f"*{ext}"):
            try:
                text = fpath.read_text(encoding="utf-8")
            except Exception as exc:
                logger.warning("Could not read %s: %s", fpath, exc)
                continue

            sub_report = audit_manuscript_language(text, filename=str(fpath))
            combined.total_files_scanned += 1
            combined.total_errors += sub_report.total_errors
            combined.total_warnings += sub_report.total_warnings
            combined.findings.extend(sub_report.findings)
            combined.files_scanned.append(str(fpath))

    combined.status = "PASS" if combined.total_errors == 0 else "FLAGGED"
    return combined


def export_language_audit_report(report: LanguageAuditReport, output_path: Path) -> None:
    """Export language audit report to JSON.

    Parameters
    ----------
    report : LanguageAuditReport
        The audit report to export.
    output_path : Path
        Path to write the JSON report.
    """
    data = {
        "status": report.status,
        "total_files_scanned": report.total_files_scanned,
        "total_errors": report.total_errors,
        "total_warnings": report.total_warnings,
        "files_scanned": report.files_scanned,
        "findings": report.findings,
    }
    save_json(data, output_path)
    logger.info("Language audit report exported to %s", output_path)
