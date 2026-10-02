"""
src/statistics/bootstrap.py — Deterministic non-parametric bootstrap resampling.

Provides bootstrap estimation of confidence intervals for sample means, medians,
paired differences, and regression slopes with strict reproducibility.
"""

from collections.abc import Callable

import numpy as np


def bootstrap_ci(
    data: np.ndarray | list[float],
    stat_func: Callable[[np.ndarray], float] = np.mean,
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> dict[str, float]:
    """Compute non-parametric bootstrap percentile confidence interval for a statistic.

    Args:
        data: 1D array of observations.
        stat_func: Statistic function mapping 1D array to scalar (default: np.mean).
        n_boot: Number of bootstrap resamples.
        ci: Confidence level (default: 0.95 for 95% CI).
        seed: Random seed for deterministic reproducibility.

    Returns:
        Dictionary with 'estimate', 'ci_low', 'ci_high', 'ci_level', 'n_boot', 'std_err'.
    """
    arr = np.asarray(data, dtype=np.float64)
    if len(arr) == 0:
        raise ValueError("Cannot bootstrap empty array.")

    rng = np.random.default_rng(seed)
    n = len(arr)
    boot_stats = np.empty(n_boot, dtype=np.float64)

    for i in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        boot_stats[i] = stat_func(sample)

    alpha = 1.0 - ci
    low_pct = 100.0 * (alpha / 2.0)
    high_pct = 100.0 * (1.0 - alpha / 2.0)

    ci_low = float(np.percentile(boot_stats, low_pct))
    ci_high = float(np.percentile(boot_stats, high_pct))
    estimate = float(stat_func(arr))

    return {
        "estimate": estimate,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_level": ci,
        "n_boot": n_boot,
        "std_err": float(np.std(boot_stats, ddof=1)),
    }


def bootstrap_difference_ci(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    stat_func: Callable[[np.ndarray], float] = np.mean,
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
    paired: bool = True,
) -> dict[str, float]:
    """Compute bootstrap CI for the difference: stat(x) - stat(y).

    Args:
        x: First group of observations.
        y: Second group of observations.
        stat_func: Statistic function (e.g. np.mean or np.median).
        n_boot: Bootstrap iterations.
        ci: Confidence level.
        seed: Random seed.
        paired: If True, resamples pairs (x_i, y_i) together.

    Returns:
        Dictionary with 'diff_estimate', 'ci_low', 'ci_high', 'ci_level', 'p_value_two_sided'.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if paired and len(x_arr) != len(y_arr):
        raise ValueError(
            f"Paired bootstrap difference requires matching sample sizes: {len(x_arr)} vs {len(y_arr)}"
        )

    rng = np.random.default_rng(seed)
    diff_stats = np.empty(n_boot, dtype=np.float64)

    if paired:
        diffs = x_arr - y_arr
        n = len(diffs)
        for i in range(n_boot):
            sample = rng.choice(diffs, size=n, replace=True)
            diff_stats[i] = stat_func(sample)
        estimate = float(stat_func(diffs))
    else:
        n_x, n_y = len(x_arr), len(y_arr)
        for i in range(n_boot):
            s_x = rng.choice(x_arr, size=n_x, replace=True)
            s_y = rng.choice(y_arr, size=n_y, replace=True)
            diff_stats[i] = stat_func(s_x) - stat_func(s_y)
        estimate = float(stat_func(x_arr) - stat_func(y_arr))

    alpha = 1.0 - ci
    ci_low = float(np.percentile(diff_stats, 100.0 * (alpha / 2.0)))
    ci_high = float(np.percentile(diff_stats, 100.0 * (1.0 - alpha / 2.0)))

    # Empirical two-sided bootstrap p-value against null hypothesis diff == 0
    p_pos = np.mean(diff_stats >= 0)
    p_neg = np.mean(diff_stats <= 0)
    p_val = float(min(1.0, 2.0 * min(p_pos, p_neg)))

    return {
        "diff_estimate": estimate,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_level": ci,
        "p_value_two_sided": p_val,
        "n_boot": n_boot,
        "std_err": float(np.std(diff_stats, ddof=1)),
    }


def bootstrap_slope_ci(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> dict[str, float]:
    """Compute bootstrap CI for the regression slope beta in y ~ x.

    Pairs (x_i, y_i) are resampled together to preserve bivariate structure.

    Args:
        x: Predictor array.
        y: Response array.
        n_boot: Number of resamples.
        ci: Confidence level.
        seed: Random seed.

    Returns:
        Dictionary with 'slope', 'ci_low', 'ci_high', 'ci_level', 'std_err'.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if len(x_arr) != len(y_arr):
        raise ValueError("x and y arrays must have identical lengths.")

    n = len(x_arr)
    rng = np.random.default_rng(seed)
    boot_slopes = np.empty(n_boot, dtype=np.float64)

    # Base slope
    denom = np.sum((x_arr - np.mean(x_arr)) ** 2)
    base_slope = (
        float(np.sum((x_arr - np.mean(x_arr)) * (y_arr - np.mean(y_arr))) / denom)
        if denom > 1e-12
        else 0.0
    )

    for i in range(n_boot):
        idx = rng.choice(n, size=n, replace=True)
        bx = x_arr[idx]
        by = y_arr[idx]
        b_denom = np.sum((bx - np.mean(bx)) ** 2)
        if b_denom > 1e-12:
            boot_slopes[i] = np.sum((bx - np.mean(bx)) * (by - np.mean(by))) / b_denom
        else:
            boot_slopes[i] = 0.0

    alpha = 1.0 - ci
    ci_low = float(np.percentile(boot_slopes, 100.0 * (alpha / 2.0)))
    ci_high = float(np.percentile(boot_slopes, 100.0 * (1.0 - alpha / 2.0)))

    return {
        "slope": base_slope,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "ci_level": ci,
        "n_boot": n_boot,
        "std_err": float(np.std(boot_slopes, ddof=1)),
    }
