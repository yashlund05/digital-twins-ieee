"""
src/evaluation/forecasting_metrics.py — Pure, stateless metrics for load estimation.

Implements primary regression metrics for short-term load forecasting:
    - Mean Absolute Error (MAE)
    - Root Mean Squared Error (RMSE)
    - Mean Absolute Percentage Error (MAPE)
    - Coefficient of Determination (R²)
"""

import numpy as np


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Mean Absolute Error (MAE).

    Args:
        y_true: Ground truth target values (1D or 2D array).
        y_pred: Predicted values matching y_true shape.

    Returns:
        MAE as float.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    return float(np.mean(np.abs(y_t - y_p)))


def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Root Mean Squared Error (RMSE).

    Args:
        y_true: Ground truth target values.
        y_pred: Predicted values matching y_true shape.

    Returns:
        RMSE as float.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    return float(np.sqrt(np.mean((y_t - y_p) ** 2)))


def mean_absolute_percentage_error(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-5,
) -> float:
    """Compute Mean Absolute Percentage Error (MAPE) as a percentage [0, 100].

    Uses an epsilon floor to prevent division-by-zero on low or zero loads:
        MAPE = (100 / N) * sum(|y_true - y_pred| / max(|y_true|, epsilon))

    Args:
        y_true: Ground truth target values.
        y_pred: Predicted values matching y_true shape.
        epsilon: Numerical stability constant.

    Returns:
        MAPE percentage as float.
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    denominator = np.maximum(np.abs(y_t), epsilon)
    return float(np.mean(np.abs(y_t - y_p) / denominator) * 100.0)


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Coefficient of Determination (R²).

    Args:
        y_true: Ground truth target values.
        y_pred: Predicted values matching y_true shape.

    Returns:
        R² score as float (-inf to 1.0).
    """
    y_t = np.asarray(y_true, dtype=np.float64)
    y_p = np.asarray(y_pred, dtype=np.float64)
    ss_res = np.sum((y_t - y_p) ** 2)
    ss_tot = np.sum((y_t - np.mean(y_t)) ** 2)
    if ss_tot == 0.0:
        return 1.0 if ss_res == 0.0 else 0.0
    return float(1.0 - (ss_res / ss_tot))


def compute_forecasting_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-5,
) -> dict[str, float]:
    """Compute standard suite of forecasting metrics.

    Args:
        y_true: Ground truth targets.
        y_pred: Model predictions.
        epsilon: Numerical stabilizer for MAPE.

    Returns:
        Dictionary containing mae, rmse, mape, and r2.
    """
    return {
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": root_mean_squared_error(y_true, y_pred),
        "mape": mean_absolute_percentage_error(y_true, y_pred, epsilon=epsilon),
        "r2": r2_score(y_true, y_pred),
    }
