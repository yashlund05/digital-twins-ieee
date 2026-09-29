"""
tests/unit/test_xgboost_model.py — Unit tests for XGBoostForecaster.
"""

from pathlib import Path

import numpy as np
import pytest

from src.forecasting.xgboost_model import XGBoostForecaster


@pytest.fixture
def synthetic_regression_data():
    """Create a reproducible linear-with-noise regression task."""
    rng = np.random.default_rng(42)
    X = rng.normal(size=(200, 5))
    # Target is 2*x0 - 1.5*x1 + noise
    y = 2.0 * X[:, 0] - 1.5 * X[:, 1] + rng.normal(scale=0.1, size=200)

    X_train, y_train = X[:150], y[:150]
    X_val, y_val = X[150:], y[150:]
    return X_train, y_train, X_val, y_val


def test_xgboost_forecaster_fit_and_predict(synthetic_regression_data):
    """Verify XGBoost model trains and predicts reasonable values."""
    X_train, y_train, X_val, y_val = synthetic_regression_data

    model = XGBoostForecaster(n_estimators=30, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train, X_val=X_val, y_val=y_val)

    assert model.is_fitted is True
    preds = model.predict(X_val)
    assert len(preds) == len(y_val)

    # Check that model learned the trend (R2 > 0.8)
    correlation = np.corrcoef(preds, y_val)[0, 1]
    assert correlation > 0.8


def test_xgboost_save_load(synthetic_regression_data, tmp_path: Path):
    """Verify serialization and restoration of XGBoost model weights and metadata."""
    X_train, y_train, X_val, y_val = synthetic_regression_data

    model = XGBoostForecaster(n_estimators=20, max_depth=3, random_state=42)
    feat_names = [f"feat_{i}" for i in range(5)]
    model.fit(X_train, y_train, feature_names=feat_names)

    orig_preds = model.predict(X_val)

    save_path = tmp_path / "xgb_test_model"
    model.save(save_path)

    loaded = XGBoostForecaster.load(save_path)
    assert loaded.is_fitted is True
    assert loaded.name == "xgboost"
    assert loaded.feature_names == feat_names

    loaded_preds = loaded.predict(X_val)
    np.testing.assert_allclose(orig_preds, loaded_preds, rtol=1e-5)
