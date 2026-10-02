"""src/reproducibility/comparator.py — Bitwise vs. numerical reproducibility comparators.

Classifies comparison results into distinct scientific equivalence categories per Section 13:
    BITWISE_IDENTICAL, NUMERICALLY_EQUIVALENT, STATISTICALLY_EQUIVALENT, DIFFERENT, NOT_COMPARABLE.
"""

from typing import Any

import numpy as np


def compare_arrays(
    actual: np.ndarray | list[float],
    reference: np.ndarray | list[float],
    abs_tol: float = 1e-6,
    rel_tol: float = 1e-4,
) -> dict[str, Any]:
    """Compare two floating-point arrays and classify their reproducibility equivalence.

    Returns:
        Structured metrics including max_abs_diff, mean_abs_diff, RMSE, and classification.
    """
    a = np.asarray(actual, dtype=np.float64)
    r = np.asarray(reference, dtype=np.float64)

    if a.shape != r.shape:
        return {
            "classification": "NOT_COMPARABLE",
            "error": f"Shape mismatch: {a.shape} vs {r.shape}",
        }

    # Check for NaN / Inf
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(r)):
        # Mask matching NaNs
        both_nan = np.isnan(a) & np.isnan(r)
        if not np.all(both_nan | (a == r)):
            return {
                "classification": "DIFFERENT",
                "error": "Non-finite values present with mismatched positions",
            }

    diff = np.abs(a - r)
    max_abs_diff = float(np.max(diff))
    mean_abs_diff = float(np.mean(diff))
    rmse = float(np.sqrt(np.mean(diff**2)))

    denom = np.maximum(np.abs(r), 1e-8)
    rel_diff = diff / denom
    max_rel_diff = float(np.max(rel_diff))

    if max_abs_diff == 0.0:
        classification = "BITWISE_IDENTICAL"
    elif max_abs_diff <= abs_tol or max_rel_diff <= rel_tol:
        classification = "NUMERICALLY_EQUIVALENT"
    elif np.isclose(np.mean(a), np.mean(r), atol=0.01) and np.isclose(
        np.std(a), np.std(r), atol=0.01
    ):
        classification = "STATISTICALLY_EQUIVALENT"
    else:
        classification = "DIFFERENT"

    return {
        "classification": classification,
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": mean_abs_diff,
        "rmse": rmse,
        "max_rel_diff": max_rel_diff,
        "abs_tolerance": abs_tol,
        "rel_tolerance": rel_tol,
        "length": len(a),
    }


def compare_metrics(
    actual: float,
    reference: float,
    tolerance: float = 1e-5,
) -> dict[str, Any]:
    """Compare two scalar performance metrics."""
    abs_diff = abs(actual - reference)
    rel_diff = abs_diff / max(abs(reference), 1e-8)

    if actual == reference:
        classification = "BITWISE_IDENTICAL"
    elif abs_diff <= tolerance or rel_diff <= tolerance:
        classification = "NUMERICALLY_EQUIVALENT"
    else:
        classification = "DIFFERENT"

    return {
        "classification": classification,
        "actual": actual,
        "reference": reference,
        "absolute_difference": abs_diff,
        "relative_difference": rel_diff,
        "tolerance": tolerance,
    }


def compare_prediction_series(
    actual_preds: np.ndarray,
    reference_preds: np.ndarray,
    actual_scores: np.ndarray | None = None,
    reference_scores: np.ndarray | None = None,
) -> dict[str, Any]:
    """Compare binary prediction classifications and continuous decision scores."""
    a_pred = np.asarray(actual_preds).astype(int)
    r_pred = np.asarray(reference_preds).astype(int)

    if len(a_pred) != len(r_pred):
        return {
            "classification": "NOT_COMPARABLE",
            "error": f"Prediction length mismatch: {len(a_pred)} vs {len(r_pred)}",
        }

    mismatches = int(np.sum(a_pred != r_pred))
    pct_agreement = float((len(a_pred) - mismatches) / len(a_pred) * 100.0)

    score_res = None
    if actual_scores is not None and reference_scores is not None:
        score_res = compare_arrays(actual_scores, reference_scores)

    if mismatches == 0:
        if score_res and score_res["classification"] == "BITWISE_IDENTICAL":
            classification = "BITWISE_IDENTICAL"
        else:
            classification = "NUMERICALLY_EQUIVALENT"
    else:
        classification = "DIFFERENT"

    return {
        "classification": classification,
        "prediction_count": len(a_pred),
        "mismatch_count": mismatches,
        "percent_agreement": pct_agreement,
        "score_comparison": score_res,
    }
