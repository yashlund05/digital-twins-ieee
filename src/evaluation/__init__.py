"""
src/evaluation — Evaluation Engine module.

Computes evaluation metrics for short-term load estimation and anomaly detection.

Load estimation metrics: MAE, RMSE, MAPE, R2
Anomaly detection metrics: Precision, Recall, F1, PR-AUC, ROC-AUC, FPR, Detection Latency

All metric functions are stateless and pure where possible.
"""

from src.evaluation.anomaly_metrics import (
    calculate_detection_latency,
    compute_anomaly_metrics,
    compute_roc_auc_score,
    f1_score,
    false_positive_rate,
    pr_auc_score,
    precision_score,
    recall_score,
)
from src.evaluation.forecasting_metrics import (
    compute_forecasting_metrics,
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)

__all__ = [
    "calculate_detection_latency",
    "compute_anomaly_metrics",
    "compute_forecasting_metrics",
    "compute_roc_auc_score",
    "f1_score",
    "false_positive_rate",
    "mean_absolute_error",
    "mean_absolute_percentage_error",
    "pr_auc_score",
    "precision_score",
    "r2_score",
    "recall_score",
    "root_mean_squared_error",
]
