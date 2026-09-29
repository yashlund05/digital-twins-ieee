"""
src/evaluation/anomaly_metrics.py — Pure, stateless metrics for anomaly detection.

Implements primary and secondary classification and ranking metrics for unsupervised
anomaly detection per configs/anomaly_detection.yaml and docs/architecture/TESTING_STRATEGY.md:
    - Precision
    - Recall (True Positive Rate)
    - F1 Score
    - False Positive Rate (FPR)
    - Precision-Recall AUC (PR-AUC)
    - Receiver Operating Characteristic AUC (ROC-AUC)
    - Detection Latency (timesteps from anomaly event onset to detection)
"""

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from src.utils.logging import get_logger

logger = get_logger("evaluation.anomaly_metrics")


def precision_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute binary classification Precision: TP / (TP + FP)."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)
    tp = np.sum((yt == 1) & (yp == 1))
    fp = np.sum((yt == 0) & (yp == 1))
    if tp + fp == 0:
        return 0.0
    return float(tp / (tp + fp))


def recall_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute binary classification Recall (TPR): TP / (TP + FN)."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)
    tp = np.sum((yt == 1) & (yp == 1))
    fn = np.sum((yt == 1) & (yp == 0))
    if tp + fn == 0:
        return 0.0
    return float(tp / (tp + fn))


def f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute harmonic mean of Precision and Recall (F1 Score)."""
    p = precision_score(y_true, y_pred)
    r = recall_score(y_true, y_pred)
    if p + r == 0.0:
        return 0.0
    return float(2.0 * p * r / (p + r))


def false_positive_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute False Positive Rate (FPR): FP / (FP + TN)."""
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)
    fp = np.sum((yt == 0) & (yp == 1))
    tn = np.sum((yt == 0) & (yp == 0))
    if fp + tn == 0:
        return 0.0
    return float(fp / (fp + tn))


def pr_auc_score(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Compute Area Under Precision-Recall Curve (PR-AUC / Average Precision)."""
    yt = np.asarray(y_true, dtype=int)
    sc = np.asarray(scores, dtype=float)
    if len(np.unique(yt)) < 2:
        return 0.0
    return float(average_precision_score(yt, sc))


def compute_roc_auc_score(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Compute Area Under the Receiver Operating Characteristic (ROC-AUC)."""
    yt = np.asarray(y_true, dtype=int)
    sc = np.asarray(scores, dtype=float)
    if len(np.unique(yt)) < 2:
        return 0.5
    return float(roc_auc_score(yt, sc))


def calculate_detection_latency(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    event_ids: list[str] | np.ndarray | None = None,
) -> float:
    """Calculate mean detection latency in timesteps across all anomalous episodes.

    For each contiguous sequence of anomaly labels (or unique event_id), measures
    the number of timesteps from the first anomalous step until the detector flags it.
    If an anomaly is completely missed, penalizes by the full duration of the event.

    Args:
        y_true: Ground truth binary anomaly flags.
        y_pred: Predicted binary anomaly flags.
        event_ids: Optional array of event IDs corresponding to each step.

    Returns:
        Average detection latency in timesteps (>= 0.0).
    """
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)

    if np.sum(yt) == 0:
        return 0.0

    latencies: list[float] = []

    if event_ids is not None:
        ev_arr = np.asarray(event_ids)
        unique_events = [e for e in np.unique(ev_arr) if str(e) not in ("none", "nan", "")]
        for ev in unique_events:
            idx = np.where(ev_arr == ev)[0]
            if len(idx) == 0:
                continue
            preds_in_event = yp[idx]
            first_detected = np.where(preds_in_event == 1)[0]
            if len(first_detected) > 0:
                latencies.append(float(first_detected[0]))
            else:
                # Missed completely: penalty is event duration
                latencies.append(float(len(idx)))
    else:
        # Contiguous block identification
        in_event = False
        onset_idx = 0
        for i in range(len(yt)):
            if yt[i] == 1 and not in_event:
                in_event = True
                onset_idx = i
            elif yt[i] == 0 and in_event:
                # Event ended
                event_preds = yp[onset_idx:i]
                first_detected = np.where(event_preds == 1)[0]
                if len(first_detected) > 0:
                    latencies.append(float(first_detected[0]))
                else:
                    latencies.append(float(len(event_preds)))
                in_event = False

        if in_event:
            event_preds = yp[onset_idx : len(yt)]
            first_detected = np.where(event_preds == 1)[0]
            if len(first_detected) > 0:
                latencies.append(float(first_detected[0]))
            else:
                latencies.append(float(len(event_preds)))

    if not latencies:
        return 0.0
    return float(np.mean(latencies))


def compute_anomaly_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray | None = None,
    event_ids: list[str] | np.ndarray | None = None,
) -> dict[str, float]:
    """Compute the full standardized suite of anomaly detection metrics.

    Args:
        y_true: Ground truth binary anomaly flags.
        y_pred: Predicted binary anomaly flags.
        scores: Continuous anomaly scores (for ranking AUC metrics).
        event_ids: Optional anomaly event identifiers for latency computation.

    Returns:
        Dictionary of computed metrics (precision, recall, f1, fpr, pr_auc, roc_auc, detection_latency).
    """
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    fpr = false_positive_rate(y_true, y_pred)
    lat = calculate_detection_latency(y_true, y_pred, event_ids=event_ids)

    pr_auc = pr_auc_score(y_true, scores) if scores is not None else 0.0
    roc_auc = compute_roc_auc_score(y_true, scores) if scores is not None else 0.5

    return {
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "false_positive_rate": fpr,
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "detection_latency": lat,
    }
