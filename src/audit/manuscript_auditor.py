"""src/audit/manuscript_auditor.py — Comprehensive Manuscript Consistency and LaTeX Audit.

Performs static syntax, citation, figure/table input path, and scientific language auditing
on the IEEE TSG manuscript package per Section 14–16.
"""

import re
import shutil
from pathlib import Path
from typing import Any

from src.publication.language_audit import audit_manuscript_language
from src.utils.io import save_json
from src.utils.logging import get_logger

logger = get_logger("audit.manuscript_auditor")


class ManuscriptPackageAuditor:
    """Auditor for LaTeX source, citations, labels, and scientific language in the manuscript."""

    def __init__(
        self,
        manuscript_dir: Path
        | str = "experiments/runs/E13_MANUSCRIPT_SUBMISSION_20261002/manuscript",
    ) -> None:
        self.manuscript_dir = Path(manuscript_dir)

    def audit_latex_structure(self) -> dict[str, Any]:
        """Perform static structural check on main.tex and its inputs."""
        main_tex_path = self.manuscript_dir / "main.tex"
        if not main_tex_path.is_file():
            return {"status": "FAIL", "error": f"main.tex not found at {main_tex_path}"}

        content = main_tex_path.read_text(encoding="utf-8")

        # 1. Check required structural tags
        has_doc_class = r"\documentclass" in content
        has_begin_doc = r"\begin{document}" in content
        has_end_doc = r"\end{document}" in content
        has_abstract = r"\begin{abstract}" in content

        # 2. Check input statements
        input_patterns = re.findall(r"\\input\{([^}]+)\}", content)
        missing_inputs = []
        for inp in input_patterns:
            target_path = self.manuscript_dir / inp
            if not target_path.is_file():
                # Check with .tex extension if omitted
                if not (self.manuscript_dir / f"{inp}.tex").is_file():
                    missing_inputs.append(inp)

        # 3. Check citations vs references.bib
        bib_path = self.manuscript_dir / "references.bib"
        bib_keys = set()
        if bib_path.is_file():
            bib_text = bib_path.read_text(encoding="utf-8")
            bib_keys = set(re.findall(r"@\w+\{([^,]+),", bib_text))

        cite_keys = set(re.findall(r"\\cite\{([^}]+)\}", content))
        # Split compound citations like \cite{ref1, ref2}
        individual_cites = set()
        for c in cite_keys:
            for part in c.split(","):
                individual_cites.add(part.strip())

        missing_cites = [c for c in individual_cites if c not in bib_keys]

        # 4. Check labels and cross references
        labels = set(re.findall(r"\\label\{([^}]+)\}", content))
        refs = set(re.findall(r"\\ref\{([^}]+)\}", content))
        missing_refs = [r for r in refs if r not in labels]

        passed = (
            has_doc_class
            and has_begin_doc
            and has_end_doc
            and has_abstract
            and len(missing_inputs) == 0
            and len(missing_cites) == 0
            and len(missing_refs) == 0
        )

        return {
            "status": "PASS" if passed else "FAIL",
            "document_tags_valid": has_doc_class and has_begin_doc and has_end_doc,
            "inputs_found": len(input_patterns),
            "missing_inputs": missing_inputs,
            "citations_found": len(individual_cites),
            "bib_keys_found": len(bib_keys),
            "missing_citations": missing_cites,
            "labels_found": len(labels),
            "references_found": len(refs),
            "missing_references": missing_refs,
        }

    def audit_manuscript_language(self) -> dict[str, Any]:
        """Perform language audit on main.tex and referenced inputs."""
        main_tex_path = self.manuscript_dir / "main.tex"
        if not main_tex_path.is_file():
            return {"status": "FAIL", "error": "main.tex not found"}

        content = main_tex_path.read_text(encoding="utf-8")
        rep = audit_manuscript_language(content, filename="manuscript/main.tex")

        # Also audit table files if present
        table_reports = []
        tables_dir = self.manuscript_dir / "tables"
        if tables_dir.is_dir():
            for t_file in tables_dir.glob("*.tex"):
                t_content = t_file.read_text(encoding="utf-8")
                t_rep = audit_manuscript_language(t_content, filename=f"tables/{t_file.name}")
                if t_rep.total_errors > 0 or t_rep.total_warnings > 0:
                    table_reports.append(t_rep)

        total_errs = rep.total_errors + sum(r.total_errors for r in table_reports)
        total_warns = rep.total_warnings + sum(r.total_warnings for r in table_reports)

        return {
            "status": "PASS" if total_errs == 0 else "FAIL",
            "total_errors": total_errs,
            "total_warnings": total_warns,
            "main_tex_findings": [f for f in rep.findings if f["severity"] == "ERROR"],
            "table_findings": [
                f for r in table_reports for f in r.findings if f["severity"] == "ERROR"
            ],
        }

    def copy_and_manifest_manuscript(self, dest_dir: Path) -> dict[str, Any]:
        """Copy manuscript package to target output directory and build manifest."""
        dest_manuscript = Path(dest_dir) / "manuscript"
        dest_manuscript.mkdir(parents=True, exist_ok=True)

        if self.manuscript_dir.is_dir():
            shutil.copytree(self.manuscript_dir, dest_manuscript, dirs_exist_ok=True)

        manifest = {
            "copied_from": str(self.manuscript_dir),
            "files": [p.name for p in dest_manuscript.rglob("*") if p.is_file()],
            "has_main_tex": (dest_manuscript / "main.tex").is_file(),
            "has_references_bib": (dest_manuscript / "references.bib").is_file(),
            "has_figures": (dest_manuscript / "figures").is_dir(),
            "has_tables": (dest_manuscript / "tables").is_dir(),
        }
        save_json(manifest, dest_manuscript / "manuscript_manifest.json")
        return manifest

    def run_full_manuscript_audit(self, output_dir: Path) -> dict[str, Any]:
        """Run structural and language audits, copy assets, and export report."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        struct_res = self.audit_latex_structure()
        lang_res = self.audit_manuscript_language()
        man_res = self.copy_and_manifest_manuscript(output_dir)

        overall_passed = struct_res["status"] == "PASS" and lang_res["status"] == "PASS"

        report = {
            "overall_manuscript_status": "PASS" if overall_passed else "FAIL",
            "latex_structure_audit": struct_res,
            "scientific_language_audit": lang_res,
            "manuscript_manifest": man_res,
        }
        save_json(report, output_dir / "manuscript_consistency.json")
        return report
