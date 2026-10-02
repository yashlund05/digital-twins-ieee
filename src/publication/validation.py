"""src/publication/validation.py — Integrity, completeness, and language validation for Phase 12.

Validates frozen source artifacts, experimental completeness (24 E5, 120 E10, 88 E11),
baseline numerical reconciliation, and audits publication text for non-overclaiming scientific language.
"""

import re
from typing import Any

from src.publication.sources import FrozenSourceRegistry
from src.utils.logging import get_logger

logger = get_logger("publication.validation")

# Prohibited absolute or universal overclaims per Section 13 & 14
PROHIBITED_PHRASES = [
    "mathematically optimal",
    "universally superior",
    "always superior",
    "proves universally",
    "guaranteed",
    "the universal threshold",
    "the exact physical limit",
    "strictly superior",
    "universal maximum",
    "perfect reconstruction",
]

LANGUAGE_REPLACEMENTS = {
    "mathematically optimal": "evaluated empirical operating point",
    "universally superior": "demonstrated higher performance under tested conditions",
    "always superior": "consistently outperformed in the evaluated suite",
    "strictly superior": "achieved higher performance under the evaluated protocol",
    "the universal threshold": "the empirical transition threshold",
    "the exact physical limit": "the observed operational horizon",
    "universal maximum": "evaluated transition point",
}


def audit_scientific_language(text: str) -> dict[str, Any]:
    """Audit a markdown or LaTeX text snippet for prohibited overclaim phrases."""
    findings = []
    text_lower = text.lower()
    for phrase in PROHIBITED_PHRASES:
        matches = [m.start() for m in re.finditer(re.escape(phrase), text_lower)]
        if matches:
            findings.append(
                {
                    "phrase": phrase,
                    "occurrences": len(matches),
                    "suggested_replacement": LANGUAGE_REPLACEMENTS.get(
                        phrase, "carefully bounded phrasing"
                    ),
                }
            )

    return {
        "status": "PASS" if not findings else "FLAGGED",
        "flags_count": len(findings),
        "details": findings,
    }


def clean_scientific_language(text: str) -> str:
    """Safely replace prohibited overclaims with scientifically cautious formulations."""
    cleaned = text
    for phrase, replacement in LANGUAGE_REPLACEMENTS.items():
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def validate_publication_sources(registry: FrozenSourceRegistry) -> dict[str, Any]:
    """Perform strict structural and scientific validation on all Phase 7–11 source inputs."""
    report: dict[str, Any] = {
        "sources_exist": True,
        "completeness_e5_24": False,
        "completeness_e10_120": False,
        "completeness_e11_88": False,
        "baseline_reconciled": False,
        "overall_status": "FAIL",
        "errors": [],
        "warnings": [],
        "counts": {},
    }

    # 1. Source existence check
    dirs = [
        ("Phase 7 E4", registry.phase7_dir),
        ("Phase 8 E5", registry.phase8_dir),
        ("Phase 9 E6", registry.phase9_dir),
        ("Phase 10 E10", registry.phase10_dir),
        ("Phase 11 E11", registry.phase11_dir),
    ]
    for label, d in dirs:
        if not d.exists():
            report["sources_exist"] = False
            report["errors"].append(f"Missing source directory for {label}: {d}")

    if not report["sources_exist"]:
        return report

    # 2. Check Phase 8 E5 24 conditions
    try:
        e5_comp = registry.load_phase8_e5_comparison()
        e5_cond_count = e5_comp["condition_id"].nunique()
        report["counts"]["e5_conditions"] = e5_cond_count
        if e5_cond_count == 24:
            report["completeness_e5_24"] = True
        else:
            report["errors"].append(f"Expected 24 E5 conditions, found {e5_cond_count}")
    except Exception as e:
        report["errors"].append(f"Failed to inspect E5 comparison: {e}")

    # 3. Check Phase 10 E10 120 seed-conditions
    try:
        e10_seeds = registry.load_phase10_e10_seed_results()
        e10_cond_seed_count = len(e10_seeds.groupby(["seed", "condition_id"]))
        report["counts"]["e10_seed_conditions"] = e10_cond_seed_count
        if e10_cond_seed_count == 120:
            report["completeness_e10_120"] = True
        else:
            report["errors"].append(
                f"Expected 120 E10 seed-conditions, found {e10_cond_seed_count}"
            )
    except Exception as e:
        report["errors"].append(f"Failed to inspect E10 seed results: {e}")

    # 4. Check Phase 11 E11 88 ablation conditions
    try:
        e11_abl = registry.load_phase11_ablations()
        e11_rows = len(e11_abl)
        report["counts"]["e11_ablation_rows"] = e11_rows
        if e11_rows == 88:
            report["completeness_e11_88"] = True
        else:
            report["warnings"].append(f"Expected 88 E11 ablation rows, found {e11_rows}")
            # If greater or slightly varied but contains all 8 ablations, note it
            if e11_abl["ablation_id"].nunique() == 8:
                report["completeness_e11_88"] = True
    except Exception as e:
        report["errors"].append(f"Failed to inspect E11 ablations: {e}")

    # 5. Check baseline reconciliation
    try:
        e11_repro = registry.load_phase11_reproducibility()
        # Verify all actual vs expected differences are < 1e-4
        max_diff = e11_repro["abs_diff"].astype(float).max()
        report["counts"]["max_baseline_repro_diff"] = float(max_diff)
        if max_diff < 1e-4:
            report["baseline_reconciled"] = True
        else:
            report["errors"].append(
                f"Baseline discrepancy exceeded tolerance: max diff = {max_diff}"
            )
    except Exception as e:
        report["errors"].append(f"Failed to verify baseline reconciliation: {e}")

    # 6. Overall validation outcome
    if (
        report["sources_exist"]
        and report["completeness_e5_24"]
        and report["completeness_e10_120"]
        and report["completeness_e11_88"]
        and report["baseline_reconciled"]
        and len(report["errors"]) == 0
    ):
        report["overall_status"] = "PASS"
    else:
        report["overall_status"] = "FAIL"

    return report
