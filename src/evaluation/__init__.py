"""
src/evaluation — Evaluation Engine module.

Computes evaluation metrics for short-term load estimation and anomaly detection.

Load estimation metrics: MAE, RMSE, MAPE, R2
Anomaly detection metrics: Precision, Recall, F1, PR-AUC, ROC-AUC, FPR, Detection Latency

All metric functions are stateless and pure where possible.
"""

from src.evaluation.forecasting_metrics import (
    compute_forecasting_metrics,
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)

__all__ = [
    "compute_forecasting_metrics",
    "mean_absolute_error",
    "mean_absolute_percentage_error",
    "r2_score",
    "root_mean_squared_error",
]
