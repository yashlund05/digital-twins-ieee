"""
tests/unit/test_anomaly_metrics.py — Unit tests for anomaly detection evaluation metrics.
"""

import numpy as np
import pytest

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


@pytest.fixture
def synthetic_binary_predictions():
    """Create controlled binary predictions with known TP, FP, TN, FN.

    Ground truth: [1, 1, 0, 0, 1, 0, 0, 0] (3 positives, 5 negatives)
    Predictions : [1, 0, 1, 0, 1, 0, 0, 0] (TP=2, FN=1, FP=1, TN=4)
    Precision   : 2 / (2 + 1) = 2/3 ≈ 0.6667
    Recall      : 2 / (2 + 1) = 2/3 ≈ 0.6667
    F1          : 2 * (2/3 * 2/3) / (4/3) = 2/3 ≈ 0.6667
    FPR         : FP / (FP + TN) = 1 / (1 + 4) = 0.20
    """
    y_true = np.array([1, 1, 0, 0, 1, 0, 0, 0], dtype=int)
    y_pred = np.array([1, 0, 1, 0, 1, 0, 0, 0], dtype=int)
    scores = np.array([0.9, 0.4, 0.7, 0.1, 0.85, 0.2, 0.15, 0.05], dtype=float)
    return y_true, y_pred, scores


def test_precision_recall_f1(synthetic_binary_predictions):
    """Verify standard binary classification metrics against manual calculations."""
    y_true, y_pred, _ = synthetic_binary_predictions
    p = precision_score(y_true, y_pred)
    r = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    fpr = false_positive_rate(y_true, y_pred)

    assert pytest.approx(p, rel=1e-3) == 2.0 / 3.0
    assert pytest.approx(r, rel=1e-3) == 2.0 / 3.0
    assert pytest.approx(f1, rel=1e-3) == 2.0 / 3.0
    assert pytest.approx(fpr, rel=1e-3) == 0.20


def test_roc_auc_and_pr_auc(synthetic_binary_predictions):
    """Verify AUC ranking metrics are strictly within [0, 1]."""
    y_true, _, scores = synthetic_binary_predictions
    roc = compute_roc_auc_score(y_true, scores)
    pr = pr_auc_score(y_true, scores)

    assert 0.5 <= roc <= 1.0
    assert 0.0 <= pr <= 1.0


def test_calculate_detection_latency_by_event():
    """Verify detection latency counts timesteps to first positive flag per event."""
    # Two events: event_1 (duration 4, detected at step 1), event_2 (duration 3, detected immediately at step 0)
    # Average latency: (1 + 0) / 2 = 0.5 steps
    y_true = np.array([0, 1, 1, 1, 1, 0, 0, 1, 1, 1])
    y_pred = np.array([0, 0, 1, 1, 0, 0, 0, 1, 1, 0])
    events = ["none", "ev1", "ev1", "ev1", "ev1", "none", "none", "ev2", "ev2", "ev2"]

    latency = calculate_detection_latency(y_true, y_pred, event_ids=events)
    assert pytest.approx(latency, rel=1e-3) == 0.5


def test_compute_anomaly_metrics_bundle(synthetic_binary_predictions):
    """Verify combined dictionary contains all primary and secondary metrics."""
    y_true, y_pred, scores = synthetic_binary_predictions
    res = compute_anomaly_metrics(y_true, y_pred, scores=scores)

    expected_keys = [
        "precision",
        "recall",
        "f1",
        "false_positive_rate",
        "pr_auc",
        "roc_auc",
        "detection_latency",
    ]
    for k in expected_keys:
        assert k in res
