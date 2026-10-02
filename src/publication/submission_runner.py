"""src/publication/submission_runner.py — Phase 13 Submission Readiness Pipeline.

Orchestrates the complete Phase 13 workflow:
1. Validates all frozen source artifacts
2. Verifies canonical scientific claims
3. Runs numerical consistency audit
4. Runs cross-phase consistency audit
5. Assembles IEEE TSG-style manuscript
6. Runs extended language audit on the generated manuscript
7. Copies Phase 12 publication figures and tables into the manuscript directory
8. Generates SHA-256 hash manifests and audit reports
9. Outputs to experiments/runs/E13_MANUSCRIPT_SUBMISSION_20261002/
"""

import shutil
from datetime import datetime
from pathlib import Path

from src.publication.claim_audit import audit_manuscript_claims
from src.publication.cross_phase_audit import CrossPhaseConsistencyAudit
from src.publication.language_audit import (
    audit_manuscript_directory,
    export_language_audit_report,
)
from src.publication.manuscript_generator import (
    generate_full_manuscript,
    generate_manuscript_summary,
)
from src.publication.numerical_audit import NumericalConsistencyAudit
from src.publication.source_registry import Phase13SourceRegistry
from src.publication.sources import FrozenSourceRegistry
from src.reproducibility.hashing import hash_directory
from src.utils.io import ensure_dir, save_json
from src.utils.logging import get_logger

logger = get_logger("publication.submission_runner")


def run_phase13_submission_pipeline(
    config_path: str = "configs/publication/phase13_publication.yaml",
    output_dir_override: str | None = None,
    verify_only: bool = False,
    strict: bool = True,
) -> Path:
    """Run the complete Phase 13 submission readiness pipeline.

    Parameters
    ----------
    config_path : str
        Path to the Phase 13 publication YAML configuration.
    output_dir_override : str | None
        Optional directory override for outputs.
    verify_only : bool
        If True, only runs audits without writing manuscript files.
    strict : bool
        If True, raises RuntimeError if any audit fails.

    Returns
    -------
    Path
        Path to the submission output directory.
    """
    logger.info("================================================================================")
    logger.info("Starting Phase 13 IEEE TSG Manuscript Assembly & Scientific Audit Pipeline")
    logger.info("================================================================================")

    # 1. Initialize registries
    frozen_reg = FrozenSourceRegistry()
    source_reg = Phase13SourceRegistry(config_path)

    out_root = (
        Path(output_dir_override)
        if output_dir_override
        else Path(
            source_reg.config.get("output", {}).get(
                "root", "experiments/runs/E13_MANUSCRIPT_SUBMISSION_20261002"
            )
        )
    )

    # 2. Verify all canonical claims
    logger.info("Step 1: Verifying canonical scientific claims...")
    claims = source_reg.verify_all_claims(frozen_reg)
    claim_summary = source_reg.summary()
    logger.info(
        "Claim verification: %d/%d verified (%d failed)",
        claim_summary["verified_claims"],
        claim_summary["total_claims"],
        claim_summary["failed_claims"],
    )

    if strict and claim_summary["failed_claims"] > 0:
        failed_ids = [c_id for c_id, c in claims.items() if not c.verified]
        raise RuntimeError(f"Canonical claim verification failed for: {failed_ids}")

    # 3. Run numerical consistency audit
    logger.info("Step 2: Running numerical consistency audit...")
    num_audit = NumericalConsistencyAudit(source_reg, frozen_reg)
    num_report = num_audit.run_full_audit()

    if strict and num_report["overall_status"] != "PASS":
        raise RuntimeError(f"Numerical consistency audit failed: {num_report['checks']}")

    # 4. Run cross-phase consistency audit
    logger.info("Step 3: Running cross-phase consistency audit...")
    cross_audit = CrossPhaseConsistencyAudit(frozen_reg)
    cross_report = cross_audit.run_full_audit()

    if strict and cross_report["overall_status"] != "PASS":
        raise RuntimeError(f"Cross-phase consistency audit failed: {cross_report['checks']}")

    if verify_only:
        logger.info("[VERIFY-ONLY] Audits completed successfully. Skipping file generation.")
        return out_root

    # 5. Create output structure
    ensure_dir(out_root)
    manuscript_dir = out_root / "manuscript"
    ensure_dir(manuscript_dir)
    ensure_dir(out_root / "audit_reports")
    ensure_dir(out_root / "provenance")

    # 6. Copy Phase 12 assets (figures, tables, LaTeX fragments)
    logger.info("Step 4: Integrating Phase 12 publication assets...")
    phase12_dir = Path("experiments/runs/E12_PUBLICATION_ARTIFACTS_20261002")
    if phase12_dir.is_dir():
        # Copy tables with language sanitation
        if (phase12_dir / "tables").is_dir():
            dest_tables = manuscript_dir / "tables"
            ensure_dir(dest_tables)
            for item in (phase12_dir / "tables").iterdir():
                if item.suffix in [".tex", ".csv"]:
                    text = item.read_text(encoding="utf-8")
                    cleaned = text.replace(" causes ", " leads to ")
                    (dest_tables / item.name).write_text(cleaned, encoding="utf-8")
                else:
                    shutil.copy2(item, dest_tables / item.name)

        # Copy figures
        if (phase12_dir / "figures").is_dir():
            shutil.copytree(phase12_dir / "figures", manuscript_dir / "figures", dirs_exist_ok=True)

        # Copy figures.tex with language sanitation
        if (phase12_dir / "latex" / "figures.tex").is_file():
            text = (phase12_dir / "latex" / "figures.tex").read_text(encoding="utf-8")
            cleaned = text.replace(" causes ", " leads to ")
            (manuscript_dir / "figures.tex").write_text(cleaned, encoding="utf-8")

        logger.info("Phase 12 assets copied and sanitized successfully.")
    else:
        logger.warning(
            "Phase 12 directory not found at %s. Figures and tables not copied.", phase12_dir
        )

    # 7. Generate manuscript
    logger.info("Step 5: Generating IEEE TSG manuscript...")
    main_tex_path = generate_full_manuscript(out_root)
    manuscript_summary = generate_manuscript_summary(out_root)

    # 8. Run extended language audit on the generated manuscript
    logger.info("Step 6: Auditing manuscript scientific language...")
    lang_report = audit_manuscript_directory(manuscript_dir)
    logger.info(
        "Language audit: status=%s (%d errors, %d warnings across %d files)",
        lang_report.status,
        lang_report.total_errors,
        lang_report.total_warnings,
        lang_report.total_files_scanned,
    )

    if strict and lang_report.total_errors > 0:
        raise RuntimeError(
            f"Manuscript contains {lang_report.total_errors} prohibited language violations."
        )

    # 9. Run claim-to-evidence audit on the manuscript text
    logger.info("Step 7: Auditing manuscript claims against evidence...")
    main_text = main_tex_path.read_text(encoding="utf-8")
    claim_audit_res = audit_manuscript_claims(main_text, source_reg)

    # 10. Export all audit reports
    logger.info("Step 8: Exporting audit reports...")
    source_reg.export_registry(out_root / "audit_reports" / "canonical_claims_registry.json")
    num_audit.export_report(out_root / "audit_reports" / "numerical_audit_report.json")
    cross_audit.export_report(out_root / "audit_reports" / "cross_phase_audit_report.json")
    export_language_audit_report(
        lang_report, out_root / "audit_reports" / "language_audit_report.json"
    )
    save_json(claim_audit_res, out_root / "audit_reports" / "claim_audit_report.json")
    save_json(manuscript_summary, out_root / "manuscript_summary.json")

    # 11. Generate hash manifest
    logger.info("Step 9: Generating cryptographic hash manifest...")
    manifest = {
        "pipeline": "Phase 13 Submission Readiness",
        "generated_at": datetime.now().isoformat(),
        "status": "VALIDATED",
        "audits": {
            "canonical_claims": claim_summary,
            "numerical_consistency": num_report["overall_status"],
            "cross_phase_consistency": cross_report["overall_status"],
            "language_audit": lang_report.status,
        },
        "manuscript_files": manuscript_summary["files"],
        "hashes": hash_directory(out_root, recursive=True),
    }
    save_json(manifest, out_root / "provenance" / "submission_manifest.json")
    save_json(manifest, out_root / "manifest.json")

    logger.info("================================================================================")
    logger.info("Phase 13 pipeline completed successfully! Output: %s", out_root)
    logger.info("================================================================================")

    return out_root
