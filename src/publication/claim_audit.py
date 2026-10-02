"""
Claim-to-evidence audit module for Phase 13.
"""

import re

from src.publication.source_registry import Phase13SourceRegistry
from src.utils.logging import get_logger

logger = get_logger(__name__)


def extract_numerical_claims(text: str) -> list[dict]:
    """
    Extracts numerical values from text using regex.
    Supports floats, percentages, and scientific notation.
    """
    # Regex to match numbers, including scientific notation and percentages
    pattern = r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?%?"
    matches = re.finditer(pattern, text)
    results = []
    for match in matches:
        val_str = match.group(0)
        is_percentage = val_str.endswith("%")
        clean_str = val_str.rstrip("%")
        try:
            val = float(clean_str)
            if is_percentage:
                val = val / 100.0
            results.append(
                {"value": val, "original_text": val_str, "start": match.start(), "end": match.end()}
            )
        except ValueError:
            pass
    return results


def map_claim_to_source(
    value: float, registry: Phase13SourceRegistry, tolerance: float = 1e-3
) -> list[str]:
    """
    Returns a list of claim_ids that match the value within the given tolerance.
    """
    matches = []
    for claim_id, claim in registry.claims.items():
        if claim.value is not None and isinstance(claim.value, (int, float)):
            if abs(float(claim.value) - value) <= tolerance:
                matches.append(claim_id)
    return matches


def audit_manuscript_claims(manuscript_text: str, registry: Phase13SourceRegistry) -> dict:
    """
    Scans manuscript text for numerical values and checks against the registry.
    """
    logger.info("Starting audit of manuscript claims")
    claims_found = extract_numerical_claims(manuscript_text)

    matched = 0
    mismatched = 0
    unverifiable = 0
    details = []

    for claim in claims_found:
        value = claim["value"]
        matches = map_claim_to_source(value, registry)

        detail = {
            "value": value,
            "original_text": claim["original_text"],
            "matched_claims": matches,
        }

        if matches:
            matched += 1
            detail["status"] = "matched"
        else:
            unverifiable += 1
            detail["status"] = "unverifiable"

        details.append(detail)

    return {
        "status": "success",
        "total_claims_checked": len(claims_found),
        "matched": matched,
        "mismatched": mismatched,
        "unverifiable": unverifiable,
        "details": details,
    }
