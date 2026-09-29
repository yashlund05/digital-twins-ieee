"""
tests/unit/test_lstm_model.py — Unit tests for PyTorch LSTMForecaster.
"""

from pathlib import Path

import numpy as np
import torch

from src.forecasting.lstm_model import LSTMForecaster, PyTorchLSTMNetwork


def test_pytorch_lstm_network_dimensions():
    """Verify PyTorchLSTMNetwork forward pass outputs expected shape."""
    batch_size = 8
    seq_len = 12
    feat_dim = 4

    net = PyTorchLSTMNetwork(input_dim=feat_dim, hidden_units=[16, 8], dropout=0.1)
    dummy_input = torch.randn(batch_size, seq_len, feat_dim)
    output = net(dummy_input)

    assert output.shape == (batch_size,)


def test_lstm_forecaster_fit_and_predict():
    """Verify LSTMForecaster trains and generates continuous predictions."""
    rng = np.random.default_rng(42)
    # 50 samples, sequence length 6, 3 features
    X = rng.normal(size=(50, 6, 3)).astype(np.float32)
    y = np.sum(X[:, -1, :], axis=1) + rng.normal(scale=0.05, size=50).astype(np.float32)

    X_train, y_train = X[:40], y[:40]
    X_val, y_val = X[40:], y[40:]

    model = LSTMForecaster(units=[16, 8], epochs=10, batch_size=16, seed=42)
    model.fit(X_train, y_train, X_val=X_val, y_val=y_val)

    assert model.is_fitted is True
    preds = model.predict(X_val)
    assert len(preds) == len(y_val)
    assert not np.isnan(preds).any()


def test_lstm_save_and_load(tmp_path: Path):
    """Verify LSTM weights serialization and deserialization."""
    rng = np.random.default_rng(42)
    X = rng.normal(size=(30, 4, 2)).astype(np.float32)
    y = rng.normal(size=30).astype(np.float32)

    model = LSTMForecaster(units=[8, 4], epochs=5, batch_size=8, seed=42)
    model.fit(X, y)
    orig_preds = model.predict(X)

    save_path = tmp_path / "lstm_test"
    model.save(save_path)

    loaded = LSTMForecaster.load(save_path)
    assert loaded.is_fitted is True
    assert loaded.name == "lstm"

    loaded_preds = loaded.predict(X)
    np.testing.assert_allclose(orig_preds, loaded_preds, atol=1e-5)
