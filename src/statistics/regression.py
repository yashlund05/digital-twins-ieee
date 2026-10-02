"""
src/statistics/regression.py — Regression and factorial modeling for degradation trends.

Fits univariate (linear, log1p) and two-way factorial (staleness x packet drop)
regression models to quantify empirical association between staleness/AoI and degradation.
"""

from typing import Any

import numpy as np
import scipy.stats as stats


def fit_linear_regression(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
) -> dict[str, float]:
    """Fit simple ordinary least squares linear regression y = alpha + beta * x.

    Args:
        x: Predictor values (e.g. staleness or AoI).
        y: Response values (e.g. normalized degradation).

    Returns:
        Dictionary containing slope, intercept, r_squared, std_err, t_stat, p_value.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if len(x_arr) != len(y_arr):
        raise ValueError(f"Lengths must match: x has {len(x_arr)}, y has {len(y_arr)}")
    if len(x_arr) < 2:
        raise ValueError("Regression requires at least 2 observations.")

    # Guard against zero variance in x
    if np.allclose(x_arr, x_arr[0]):
        return {
            "slope": 0.0,
            "intercept": float(np.mean(y_arr)),
            "r_squared": 0.0,
            "std_err": 0.0,
            "t_statistic": 0.0,
            "p_value": 1.0,
            "n_samples": len(x_arr),
        }

    res = stats.linregress(x_arr, y_arr)
    t_stat = float(res.slope / res.stderr) if res.stderr and res.stderr > 0 else 0.0

    return {
        "slope": float(res.slope),
        "intercept": float(res.intercept),
        "r_squared": float(res.rvalue**2),
        "std_err": float(res.stderr) if res.stderr is not None else 0.0,
        "t_statistic": t_stat,
        "p_value": float(res.pvalue),
        "n_samples": len(x_arr),
    }


def fit_log_linear_regression(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
) -> dict[str, float]:
    """Fit regression with log1p-transformed predictor: y = alpha + beta * log(1 + x).

    Essential for nonuniformly spaced staleness intervals [0, 1, 5, 15, 60, 300].

    Args:
        x: Raw predictor (>= 0).
        y: Response values.

    Returns:
        Regression statistics dictionary.
    """
    x_arr = np.asarray(x, dtype=np.float64)
    if np.any(x_arr < 0):
        raise ValueError("x values must be non-negative for log1p transformation.")
    x_log = np.log1p(x_arr)
    out = fit_linear_regression(x_log, y)
    out["transform"] = "log1p"
    return out


def fit_two_way_factorial_regression(
    delta_t: np.ndarray | list[float],
    p_drop: np.ndarray | list[float],
    y: np.ndarray | list[float],
    use_log_dt: bool = True,
) -> dict[str, Any]:
    """Fit two-way factorial ordinary least squares model:
    y = b0 + b1 * dt + b2 * p_drop + b3 * (dt * p_drop).

    Args:
        delta_t: Synchronization interval values.
        p_drop: Packet drop rates.
        y: Response variable (degradation).
        use_log_dt: Whether to log1p transform delta_t.

    Returns:
        Dictionary of model coefficients, standard errors, p-values, and R-squared.
    """
    dt_arr = np.asarray(delta_t, dtype=np.float64)
    pd_arr = np.asarray(p_drop, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    n = len(y_arr)
    if not (len(dt_arr) == len(pd_arr) == n):
        raise ValueError("Inputs delta_t, p_drop, and y must have identical lengths.")

    x1 = np.log1p(dt_arr) if use_log_dt else dt_arr
    x2 = pd_arr
    x3 = x1 * x2

    # Design matrix with intercept
    X = np.column_stack([np.ones(n), x1, x2, x3])

    # OLS estimation via pseudo-inverse
    beta, residuals, rank, s = np.linalg.lstsq(X, y_arr, rcond=None)
    y_pred = X @ beta
    ss_res = np.sum((y_arr - y_pred) ** 2)
    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    # Degrees of freedom
    p = X.shape[1]
    df_resid = max(n - p, 1)
    sigma2 = ss_res / df_resid

    try:
        var_covar = sigma2 * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.maximum(np.diag(var_covar), 1e-12))
        t_stats = beta / se
        p_values = 2.0 * (1.0 - stats.t.cdf(np.abs(t_stats), df=df_resid))
    except np.linalg.LinAlgError:
        se = np.zeros(p)
        t_stats = np.zeros(p)
        p_values = np.ones(p)

    return {
        "intercept": float(beta[0]),
        "b_dt": float(beta[1]),
        "b_pdrop": float(beta[2]),
        "b_interaction": float(beta[3]),
        "se_intercept": float(se[0]),
        "se_dt": float(se[1]),
        "se_pdrop": float(se[2]),
        "se_interaction": float(se[3]),
        "p_intercept": float(p_values[0]),
        "p_dt": float(p_values[1]),
        "p_pdrop": float(p_values[2]),
        "p_interaction": float(p_values[3]),
        "r_squared": float(r_squared),
        "n_samples": n,
        "use_log_dt": use_log_dt,
    }
