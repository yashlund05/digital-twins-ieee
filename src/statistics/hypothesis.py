"""
src/statistics/hypothesis.py — Pre-specified hypothesis testing and multiple comparisons.

Implements the formal test of Research Hypothesis H3 (Differential Degradation):
    H0: beta_anomaly <= beta_load
    H3: beta_anomaly > beta_load (Anomaly detection exhibits steeper degradation)
along with paired non-parametric tests (Wilcoxon) and Benjamini-Hochberg FDR correction.
"""

from typing import Any
import numpy as np
import scipy.stats as stats

from src.statistics.bootstrap import bootstrap_difference_ci
from src.statistics.regression import fit_log_linear_regression


def test_differential_degradation_h3(
    predictor: np.ndarray | list[float],
    ad_normalized_degradation: np.ndarray | list[float],
    le_normalized_degradation: np.ndarray | list[float],
    n_boot: int = 2000,
    ci: float = 0.95,
    seed: int = 42,
) -> dict[str, Any]:
    """Perform formal statistical test of Hypothesis H3.

    Fits regression slopes:
        D_ad ~ log1p(x) -> beta_ad
        D_le ~ log1p(x) -> beta_le
    Computes slope difference:
        Delta_beta = beta_ad - beta_le

    Bootstraps the bivariate paired conditions to estimate the 95% CI and
    one-sided p-value for H3: beta_ad > beta_le.

    Args:
        predictor: Staleness intervals Delta_t or realized AoI values.
        ad_normalized_degradation: Task-normalized anomaly detection degradation array.
        le_normalized_degradation: Task-normalized load estimation degradation array.
        n_boot: Bootstrap iterations.
        ci: Confidence level.
        seed: Random seed.

    Returns:
        Structured dictionary containing slopes, difference, CI, p-value, and conclusion.
    """
    x_arr = np.asarray(predictor, dtype=np.float64)
    ad_arr = np.asarray(ad_normalized_degradation, dtype=np.float64)
    le_arr = np.asarray(le_normalized_degradation, dtype=np.float64)

    n = len(x_arr)
    if not (len(ad_arr) == len(le_arr) == n):
        raise ValueError("Predictor, AD degradation, and LE degradation must have identical lengths.")

    # 1. Point estimates on log1p scale
    ad_fit = fit_log_linear_regression(x_arr, ad_arr)
    le_fit = fit_log_linear_regression(x_arr, le_arr)

    beta_ad = ad_fit["slope"]
    beta_le = le_fit["slope"]
    delta_beta = beta_ad - beta_le

    # 2. Bootstrap difference in slopes
    rng = np.random.default_rng(seed)
    boot_diffs = np.empty(n_boot, dtype=np.float64)
    x_log = np.log1p(x_arr)

    for i in range(n_boot):
        idx = rng.choice(n, size=n, replace=True)
        bx = x_log[idx]
        b_ad = ad_arr[idx]
        b_le = le_arr[idx]

        denom = np.sum((bx - np.mean(bx)) ** 2)
        if denom > 1e-12:
            s_ad = np.sum((bx - np.mean(bx)) * (b_ad - np.mean(b_ad))) / denom
            s_le = np.sum((bx - np.mean(bx)) * (b_le - np.mean(b_le))) / denom
            boot_diffs[i] = s_ad - s_le
        else:
            boot_diffs[i] = 0.0

    alpha = 1.0 - ci
    ci_low = float(np.percentile(boot_diffs, 100.0 * (alpha / 2.0)))
    ci_high = float(np.percentile(boot_diffs, 100.0 * (1.0 - alpha / 2.0)))

    # One-sided empirical p-value for H3: delta_beta > 0 (null is delta_beta <= 0)
    p_value_one_sided = float(np.mean(boot_diffs <= 0))

    # Evaluate decision rule
    if p_value_one_sided < 0.05 and ci_low > 0:
        conclusion = "SUPPORTED"
        description = (
            f"H3 is statistically SUPPORTED: Anomaly detection degrades significantly steeper "
            f"than load estimation (Delta beta = {delta_beta:.4f}, 95% CI [{ci_low:.4f}, {ci_high:.4f}], "
            f"p = {p_value_one_sided:.4f})."
        )
    elif delta_beta > 0 and p_value_one_sided >= 0.05:
        conclusion = "INSUFFICIENT_EVIDENCE"
        description = (
            f"H3 is INCONCLUSIVE / INSUFFICIENT EVIDENCE: Observed slope difference is positive "
            f"(Delta beta = {delta_beta:.4f}) but does not achieve statistical significance "
            f"(p = {p_value_one_sided:.4f}, 95% CI [{ci_low:.4f}, {ci_high:.4f}])."
        )
    else:
        conclusion = "NOT_SUPPORTED"
        description = (
            f"H3 is NOT SUPPORTED: Anomaly detection does not degrade steeper than load estimation "
            f"(Delta beta = {delta_beta:.4f}, p = {p_value_one_sided:.4f})."
        )

    return {
        "beta_ad": beta_ad,
        "beta_le": beta_le,
        "delta_beta": delta_beta,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_level": ci,
        "p_value_one_sided": p_value_one_sided,
        "conclusion": conclusion,
        "description": description,
        "n_samples": n,
        "n_boot": n_boot,
    }


test_differential_degradation_h3.__test__ = False


def paired_wilcoxon_test(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    alternative: str = "greater",
) -> dict[str, Any]:
    """Conduct paired Wilcoxon signed-rank test on matched conditions.

    Args:
        x: First matched measurements (e.g. AD degradation).
        y: Second matched measurements (e.g. LE degradation).
        alternative: 'greater', 'less', or 'two-sided'.

    Returns:
        Dictionary with 'statistic', 'p_value', 'alternative', 'n_pairs', 'n_nonzero_diff'.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if len(x_arr) != len(y_arr):
        raise ValueError(f"Paired test requires equal sample lengths: {len(x_arr)} vs {len(y_arr)}")

    diff = x_arr - y_arr
    nonzero = diff[diff != 0]

    if len(nonzero) < 3:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "alternative": alternative,
            "n_pairs": len(x_arr),
            "n_nonzero_diff": len(nonzero),
            "warning": "Fewer than 3 non-zero differences; test degenerate.",
        }

    res = stats.wilcoxon(x_arr, y_arr, alternative=alternative, zero_method="wilcox")
    return {
        "statistic": float(res.statistic),
        "p_value": float(res.pvalue),
        "alternative": alternative,
        "n_pairs": len(x_arr),
        "n_nonzero_diff": len(nonzero),
    }


def benjamini_hochberg_correction(
    p_values: list[float] | np.ndarray,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Perform Benjamini-Hochberg False Discovery Rate (FDR) control on p-values.

    Args:
        p_values: Array of unadjusted p-values.
        alpha: False discovery rate significance threshold (default: 0.05).

    Returns:
        Dictionary containing 'p_adjusted', 'significant', 'alpha', 'm_tests'.
    """
    p_arr = np.asarray(p_values, dtype=np.float64)
    m = len(p_arr)
    if m == 0:
        return {"p_adjusted": [], "significant": [], "alpha": alpha, "m_tests": 0}

    # Sort p-values and keep track of original indices
    order = np.argsort(p_arr)
    sorted_p = p_arr[order]

    # Adjusted p-values: p_adj_i = min(sorted_p_i * m / i, 1.0)
    ranks = np.arange(1, m + 1)
    adj_factors = m / ranks
    adj_p_sorted = np.minimum(1.0, sorted_p * adj_factors)

    # Enforce monotonicity: p_adj_i <= p_adj_{i+1}
    for i in range(m - 2, -1, -1):
        adj_p_sorted[i] = min(adj_p_sorted[i], adj_p_sorted[i + 1])

    # Revert to original order
    adj_p = np.empty_like(adj_p_sorted)
    adj_p[order] = adj_p_sorted
    significant = adj_p <= alpha

    return {
        "p_adjusted": [float(p) for p in adj_p],
        "significant": [bool(s) for s in significant],
        "alpha": alpha,
        "m_tests": m,
    }
