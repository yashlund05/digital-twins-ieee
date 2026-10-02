"""
src/statistics/effect_sizes.py — Standardized effect size estimation.

Implements Cohen's d (independent and paired formulations) and Cliff's delta
(non-parametric ordinal effect size) with categorical magnitude interpretations.
"""

from typing import Any

import numpy as np


def compute_cohens_d(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    paired: bool = False,
) -> dict[str, Any]:
    """Compute Cohen's d effect size.

    For independent samples:
        d = (mean(x) - mean(y)) / s_pooled
        where s_pooled = sqrt(((n1-1)*s1^2 + (n2-1)*s2^2) / (n1+n2-2))

    For paired samples:
        diff = x - y
        d = mean(diff) / std(diff, ddof=1)

    Args:
        x: First sample array.
        y: Second sample array.
        paired: Whether samples are paired/matched.

    Returns:
        Dictionary with 'd', 'interpretation', and 'paired'.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if paired:
        if len(x_arr) != len(y_arr):
            raise ValueError(
                f"Paired Cohen's d requires equal sample sizes: {len(x_arr)} vs {len(y_arr)}"
            )
        diff = x_arr - y_arr
        s_diff = np.std(diff, ddof=1)
        if s_diff < 1e-12:
            d = 0.0
        else:
            d = float(np.mean(diff) / s_diff)
    else:
        n1, n2 = len(x_arr), len(y_arr)
        if n1 < 2 or n2 < 2:
            raise ValueError("Cohen's d requires at least 2 samples per group.")
        s1 = np.var(x_arr, ddof=1)
        s2 = np.var(y_arr, ddof=1)
        s_pooled = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / max(n1 + n2 - 2, 1))
        if s_pooled < 1e-12:
            d = 0.0
        else:
            d = float((np.mean(x_arr) - np.mean(y_arr)) / s_pooled)

    abs_d = abs(d)
    if abs_d < 0.2:
        interpretation = "negligible"
    elif abs_d < 0.5:
        interpretation = "small"
    elif abs_d < 0.8:
        interpretation = "medium"
    else:
        interpretation = "large"

    return {
        "d": d,
        "magnitude": abs_d,
        "interpretation": interpretation,
        "paired": paired,
        "n1": len(x_arr),
        "n2": len(y_arr),
    }


def compute_cliffs_delta(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
) -> dict[str, Any]:
    """Compute Cliff's delta non-parametric effect size.

    Formula:
        delta = ( #(x_i > y_j) - #(x_i < y_j) ) / (n1 * n2)

    Ranges from -1.0 to +1.0.

    Args:
        x: First sample group.
        y: Second sample group.

    Returns:
        Dictionary with 'delta', 'interpretation', 'n1', 'n2'.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    n1 = len(x_arr)
    n2 = len(y_arr)
    if n1 == 0 or n2 == 0:
        raise ValueError("Cliff's delta requires non-empty sample arrays.")

    # Vectorized pairwise comparison matrix
    diff = x_arr[:, np.newaxis] - y_arr[np.newaxis, :]
    greater = np.sum(diff > 0)
    less = np.sum(diff < 0)
    delta = float((greater - less) / (n1 * n2))

    abs_delta = abs(delta)
    if abs_delta < 0.147:
        interpretation = "negligible"
    elif abs_delta < 0.33:
        interpretation = "small"
    elif abs_delta < 0.474:
        interpretation = "medium"
    else:
        interpretation = "large"

    return {
        "delta": delta,
        "magnitude": abs_delta,
        "interpretation": interpretation,
        "n1": n1,
        "n2": n2,
    }
