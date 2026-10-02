"""
src/statistics/degradation.py — Normalized and relative degradation metrics.

Defines directional degradation functions comparing observed performance
under synchronization staleness to baseline performance (Delta t = 0, Pdrop = 0).
Guarantees consistent polarity: positive values indicate performance deterioration.
"""

from typing import Any, Literal
import numpy as np
import pandas as pd

MetricDirection = Literal["lower_better", "higher_better"]

METRIC_DIRECTION: dict[str, MetricDirection] = {
    # Load estimation metrics (errors: lower is better)
    "mae": "lower_better",
    "rmse": "lower_better",
    "mape": "lower_better",
    "mse": "lower_better",
    # Anomaly detection metrics (performance: higher is better)
    "f1": "higher_better",
    "pr_auc": "higher_better",
    "roc_auc": "higher_better",
    "precision": "higher_better",
    "recall": "higher_better",
    # Anomaly detection error metrics (lower is better)
    "fpr": "lower_better",
    "false_positive_rate": "lower_better",
    "detection_latency": "lower_better",
    "latency_steps": "lower_better",
}


def get_metric_direction(metric_name: str) -> MetricDirection:
    """Return whether lower or higher values are better for a given metric.

    Args:
        metric_name: Metric identifier (case-insensitive).

    Returns:
        'lower_better' or 'higher_better'.
    """
    key = metric_name.lower().strip()
    if key in METRIC_DIRECTION:
        return METRIC_DIRECTION[key]
    raise ValueError(f"Unknown metric '{metric_name}'. Registered metrics: {list(METRIC_DIRECTION.keys())}")


def compute_absolute_degradation(
    observed: float | np.ndarray,
    baseline: float | np.ndarray,
    metric_name: str,
) -> float | np.ndarray:
    """Compute directional absolute degradation (positive indicates deterioration).

    For lower-is-better metrics (e.g. MAE, MAPE, FPR):
        abs_deg = observed - baseline
    For higher-is-better metrics (e.g. F1, PR-AUC):
        abs_deg = baseline - observed

    Args:
        observed: Metric value under test condition.
        baseline: Metric value at ideal baseline condition.
        metric_name: Name of metric.

    Returns:
        Absolute degradation value(s).
    """
    direction = get_metric_direction(metric_name)
    obs_arr = np.asarray(observed, dtype=np.float64)
    base_arr = np.asarray(baseline, dtype=np.float64)

    if direction == "lower_better":
        res = obs_arr - base_arr
    else:
        res = base_arr - obs_arr

    return float(res) if np.ndim(res) == 0 else res


def compute_relative_degradation(
    observed: float | np.ndarray,
    baseline: float | np.ndarray,
    metric_name: str,
    epsilon: float = 1e-8,
) -> float | np.ndarray:
    """Compute relative degradation normalized by baseline magnitude.

    Positive values indicate deterioration.

    Formula:
        rel_deg = absolute_degradation / max(abs(baseline), epsilon)

    Args:
        observed: Metric value under test condition.
        baseline: Metric value at ideal baseline.
        metric_name: Name of metric.
        epsilon: Protection floor against zero-division.

    Returns:
        Relative degradation ratio.
    """
    abs_deg = compute_absolute_degradation(observed, baseline, metric_name)
    base_arr = np.asarray(baseline, dtype=np.float64)
    denom = np.maximum(np.abs(base_arr), epsilon)
    res = abs_deg / denom
    return float(res) if np.ndim(res) == 0 else res


def compute_normalized_degradation(
    observed: float | np.ndarray,
    baseline: float | np.ndarray,
    metric_name: str,
    epsilon: float = 1e-8,
) -> float | np.ndarray:
    """Alias for compute_relative_degradation providing standard task-normalized score.

    Positive values indicate degradation relative to baseline.
    Zero indicates identical performance to baseline.
    """
    return compute_relative_degradation(observed, baseline, metric_name, epsilon=epsilon)


def build_degradation_dataframe(
    comparison_df: pd.DataFrame,
    epsilon: float = 1e-8,
) -> pd.DataFrame:
    """Enrich long-format comparison dataframe with standardized directional degradation columns.

    Args:
        comparison_df: DataFrame containing at minimum:
            ['condition_id', 'staleness_seconds', 'packet_drop_rate', 'task',
             'model', 'representation', 'metric', 'value', 'baseline_value']
        epsilon: Zero-division protection.

    Returns:
        DataFrame with standardized 'absolute_degradation' and 'normalized_degradation'.
    """
    df = comparison_df.copy()
    if "detector" in df.columns:
        if "model" in df.columns:
            df["model"] = df["model"].fillna(df["detector"])
        else:
            df["model"] = df["detector"]

    abs_degs = []
    norm_degs = []
    directions = []

    for _, row in df.iterrows():
        m_name = str(row["metric"]).lower()
        val = float(row["value"])
        b_val = float(row["baseline_value"])

        try:
            direction = get_metric_direction(m_name)
            abs_d = compute_absolute_degradation(val, b_val, m_name)
            norm_d = compute_normalized_degradation(val, b_val, m_name, epsilon=epsilon)
        except ValueError:
            direction = "lower_better"
            abs_d = val - b_val
            norm_d = (val - b_val) / max(abs(b_val), epsilon)

        directions.append(direction)
        abs_degs.append(abs_d)
        norm_degs.append(norm_d)

    df["metric_direction"] = directions
    df["absolute_degradation"] = abs_degs
    df["normalized_degradation"] = norm_degs
    return df
