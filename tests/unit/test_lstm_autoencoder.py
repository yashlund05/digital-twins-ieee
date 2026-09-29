"""
tests/unit/test_lstm_autoencoder.py — Unit tests for PyTorch LSTMAutoencoderDetector.
"""

from pathlib import Path

import numpy as np
import torch

from src.anomaly_detection.lstm_autoencoder import (
    LSTMAutoencoderDetector,
    PyTorchLSTMAutoencoderNetwork,
)


def test_lstm_autoencoder_network_dimensions():
    """Verify PyTorchLSTMAutoencoderNetwork produces identical output reconstruction shape."""
    batch_size = 4
    seq_len = 10
    input_dim = 6

    net = PyTorchLSTMAutoencoderNetwork(
        input_dim=input_dim,
        seq_len=seq_len,
        encoder_units=[16, 8],
        latent_dim=4,
        decoder_units=[8, 16],
    )
    dummy_x = torch.randn(batch_size, seq_len, input_dim)
    recon = net(dummy_x)

    assert recon.shape == dummy_x.shape


def test_lstm_autoencoder_fit_and_reconstruction():
    """Verify LSTMAutoencoder fits unsupervised and scores higher on corrupted data."""
    rng = np.random.default_rng(42)
    # 40 samples, sequence length 8, 3 features
    normal_data = rng.normal(loc=0.0, scale=0.5, size=(40, 8, 3)).astype(np.float32)
    corrupted_data = rng.normal(loc=5.0, scale=2.0, size=(10, 8, 3)).astype(np.float32)

    detector = LSTMAutoencoderDetector(
        encoder_units=[16, 8],
        latent_dim=4,
        decoder_units=[8, 16],
        epochs=10,
        batch_size=16,
        seed=42,
    )
    detector.fit(normal_data)

    assert detector.is_fitted is True

    scores_normal = detector.score_samples(normal_data)
    scores_corrupted = detector.score_samples(corrupted_data)

    assert len(scores_normal) == 40
    assert len(scores_corrupted) == 10
    # Corrupted / anomalous sequences should yield higher mean reconstruction error
    assert np.mean(scores_corrupted) > np.mean(scores_normal)


def test_lstm_autoencoder_save_and_load(tmp_path: Path):
    """Verify serialization and restoration of LSTM Autoencoder weights and config."""
    rng = np.random.default_rng(42)
    data = rng.normal(size=(20, 6, 2)).astype(np.float32)

    detector = LSTMAutoencoderDetector(
        encoder_units=[8, 4],
        latent_dim=2,
        decoder_units=[4, 8],
        epochs=5,
        batch_size=8,
        seed=42,
    )
    detector.fit(data)
    detector.set_threshold(0.42)

    orig_scores = detector.score_samples(data)

    save_path = tmp_path / "lstmae_test"
    detector.save(save_path)

    loaded = LSTMAutoencoderDetector.load(save_path)
    assert loaded.is_fitted is True
    assert loaded.threshold == 0.42
    assert loaded.name == "lstm_autoencoder"

    loaded_scores = loaded.score_samples(data)
    np.testing.assert_allclose(orig_scores, loaded_scores, atol=1e-5)
