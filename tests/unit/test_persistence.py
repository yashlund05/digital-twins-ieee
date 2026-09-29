"""
tests/unit/test_persistence.py — Unit tests for PersistenceForecaster.
"""

from pathlib import Path

import numpy as np
import pytest

from src.forecasting.persistence import PersistenceForecaster


def test_persistence_fit_and_predict_tabular():
    """Verify persistence model predicts lag-1 column from tabular features."""
    X = np.array(
        [
            [10.0, 9.0],  # sample 0: lag_1=10.0, lag_2=9.0
            [12.0, 10.0],  # sample 1: lag_1=12.0, lag_2=10.0
            [15.0, 12.0],  # sample 2: lag_1=15.0, lag_2=12.0
        ]
    )
    y = np.array([12.0, 15.0, 18.0])

    model = PersistenceForecaster(lag_feature_name="lag_1")
    model.fit(X, y, feature_names=["lag_1", "lag_2"])

    preds = model.predict(X)
    np.testing.assert_array_equal(preds, [10.0, 12.0, 15.0])


def test_persistence_predict_unfitted_raises():
    """Verify predict on unfitted model raises RuntimeError."""
    model = PersistenceForecaster()
    with pytest.raises(RuntimeError):
        model.predict(np.array([[1.0]]))


def test_persistence_save_load(tmp_path: Path):
    """Verify persistence model serialization round-trip."""
    model = PersistenceForecaster(lag_feature_name="lag_1")
    X = np.array([[5.0, 1.0]])
    y = np.array([6.0])
    model.fit(X, y, feature_names=["lag_1", "other"])

    save_path = tmp_path / "persistence_model.json"
    model.save(save_path)
    assert save_path.exists()

    loaded = PersistenceForecaster.load(save_path)
    assert loaded.name == "persistence"
    assert loaded.is_fitted is True
    preds = loaded.predict(X)
    assert preds[0] == 5.0
