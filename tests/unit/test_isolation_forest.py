"""
tests/unit/test_isolation_forest.py — Unit tests for IsolationForestDetector.
"""

from pathlib import Path

import numpy as np
import pytest

from src.anomaly_detection.isolation_forest import IsolationForestDetector


@pytest.fixture
def synthetic_anomaly_data():
    """Create a 2D dataset with dense normal cluster and clear outliers."""
    rng = np.random.default_rng(42)
    # 200 normal points clustered near (0, 0)
    normal = rng.normal(loc=0.0, scale=0.5, size=(200, 4))
    # 10 anomalies far out at (10, 10)
    anomalies = rng.normal(loc=10.0, scale=0.5, size=(10, 4))

    X_train = normal[:150]
    X_val = np.vstack([normal[150:], anomalies])
    y_val = np.array([0] * 50 + [1] * 10)
    return X_train, X_val, y_val


def test_isolation_forest_unsupervised_fit_and_score(synthetic_anomaly_data):
    """Verify IsolationForestDetector fits without labels and assigns higher scores to outliers."""
    X_train, X_val, y_val = synthetic_anomaly_data

    detector = IsolationForestDetector(n_estimators=30, contamination=0.05, random_state=42)
    detector.fit(X_train)

    assert detector.is_fitted is True

    scores = detector.score_samples(X_val)
    assert len(scores) == len(X_val)

    # Normal scores vs anomaly scores: anomalies must have higher scores
    normal_scores = scores[y_val == 0]
    anomaly_scores = scores[y_val == 1]
    assert np.mean(anomaly_scores) > np.mean(normal_scores)


def test_isolation_forest_predict_and_threshold(synthetic_anomaly_data):
    """Verify predict returns binary flags according to set threshold."""
    X_train, X_val, _ = synthetic_anomaly_data
    detector = IsolationForestDetector(n_estimators=20, random_state=42)
    detector.fit(X_train)

    with pytest.raises(RuntimeError, match="threshold"):
        detector.predict(X_val)

    detector.set_threshold(0.5)
    preds = detector.predict(X_val)
    assert set(np.unique(preds)).issubset({0, 1})


def test_isolation_forest_save_and_load(synthetic_anomaly_data, tmp_path: Path):
    """Verify serialization of model weights, threshold, and configuration."""
    X_train, X_val, _ = synthetic_anomaly_data
    detector = IsolationForestDetector(n_estimators=20, random_state=42)
    detector.fit(X_train)
    detector.set_threshold(0.65)

    orig_scores = detector.score_samples(X_val)

    save_path = tmp_path / "if_test"
    detector.save(save_path)

    loaded = IsolationForestDetector.load(save_path)
    assert loaded.is_fitted is True
    assert loaded.threshold == 0.65
    assert loaded.name == "isolation_forest"

    loaded_scores = loaded.score_samples(X_val)
    np.testing.assert_allclose(orig_scores, loaded_scores, rtol=1e-5)
