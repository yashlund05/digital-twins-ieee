"""
src/anomaly_detection/lstm_autoencoder.py — PyTorch LSTM Autoencoder anomaly detector.

Implements the recurrent sequence-to-sequence autoencoder for unsupervised anomaly detection.
Trained to reconstruct normal operational power telemetry; anomalies (voltage dips,
load surges, phase imbalances) produce significantly higher reconstruction errors.
"""

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.anomaly_detection.detector import BaseAnomalyDetector
from src.utils.config import LSTMAutoencoderConfig
from src.utils.logging import get_logger

logger = get_logger("anomaly_detection.lstm_autoencoder")


class PyTorchLSTMAutoencoderNetwork(nn.Module):
    """Encoder-Decoder LSTM architecture for sequence reconstruction."""

    def __init__(
        self,
        input_dim: int,
        seq_len: int,
        encoder_units: list[int] | None = None,
        latent_dim: int = 16,
        decoder_units: list[int] | None = None,
    ) -> None:
        """Initialize encoder and decoder recurrent stacks.

        Args:
            input_dim: Number of electrical features per timestep.
            seq_len: Temporal window length (timesteps).
            encoder_units: Hidden unit sizes for encoder LSTMs.
            latent_dim: Bottleneck latent dimension.
            decoder_units: Hidden unit sizes for decoder LSTMs.
        """
        super().__init__()
        self.input_dim = input_dim
        self.seq_len = seq_len
        self.latent_dim = latent_dim

        enc_units = encoder_units or [64, 32]
        dec_units = decoder_units or [32, 64]

        # 1. Encoder
        self.enc_lstms = nn.ModuleList()
        curr_dim = input_dim
        for h_dim in enc_units:
            self.enc_lstms.append(nn.LSTM(input_size=curr_dim, hidden_size=h_dim, batch_first=True))
            curr_dim = h_dim

        self.enc_to_latent = nn.Linear(curr_dim, latent_dim)

        # 2. Decoder
        self.latent_to_dec = nn.Linear(latent_dim, dec_units[0])
        self.dec_lstms = nn.ModuleList()
        curr_dim = dec_units[0]
        for h_dim in dec_units:
            self.dec_lstms.append(nn.LSTM(input_size=curr_dim, hidden_size=h_dim, batch_first=True))
            curr_dim = h_dim

        self.reconstruction_head = nn.Linear(curr_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Encode input sequence to bottleneck and decode back to original space.

        Args:
            x: Input tensor of shape (batch, seq_len, input_dim).

        Returns:
            Reconstructed tensor matching shape of x.
        """
        # Encode
        out = x
        for lstm in self.enc_lstms:
            out, _ = lstm(out)

        # Bottleneck from last timestep
        latent = self.enc_to_latent(out[:, -1, :])  # (batch, latent_dim)

        # Decode: repeat latent vector across all seq_len steps
        dec_init = self.latent_to_dec(latent)  # (batch, dec_units[0])
        dec_in = dec_init.unsqueeze(1).repeat(1, self.seq_len, 1)  # (batch, seq_len, dec_units[0])

        out = dec_in
        for lstm in self.dec_lstms:
            out, _ = lstm(out)

        recon = self.reconstruction_head(out)  # (batch, seq_len, input_dim)
        return recon


class LSTMAutoencoderDetector(BaseAnomalyDetector):
    """LSTM Autoencoder anomaly detector scoring samples by reconstruction error."""

    def __init__(
        self,
        config: LSTMAutoencoderConfig | None = None,
        encoder_units: list[int] | None = None,
        latent_dim: int = 16,
        decoder_units: list[int] | None = None,
        lookback_steps: int = 24,
        batch_size: int = 64,
        epochs: int = 50,
        patience: int = 8,
        learning_rate: float = 0.001,
        seed: int = 42,
    ) -> None:
        """Initialize LSTMAutoencoderDetector.

        Args:
            config: Optional LSTMAutoencoderConfig instance.
            encoder_units: Hidden units for encoder.
            latent_dim: Bottleneck dimension.
            decoder_units: Hidden units for decoder.
            lookback_steps: Window length.
            batch_size: Mini-batch size.
            epochs: Maximum epochs.
            patience: Early stopping patience.
            learning_rate: Adam optimizer learning rate.
            seed: Master random seed.
        """
        super().__init__(name="lstm_autoencoder")
        cfg = config or LSTMAutoencoderConfig()

        self.encoder_units = encoder_units or cfg.encoder_units
        self.latent_dim = latent_dim if latent_dim != 16 else cfg.latent_dim
        self.decoder_units = decoder_units or cfg.decoder_units
        self.lookback_steps = lookback_steps if lookback_steps != 24 else cfg.lookback_steps
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience
        self.learning_rate = learning_rate
        self.seed = seed

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.network: PyTorchLSTMAutoencoderNetwork | None = None
        self._input_dim: int = 0

    def _set_seeds(self) -> None:
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

    def _prepare_tensor(self, X: np.ndarray) -> torch.Tensor:
        arr = np.asarray(X, dtype=np.float32)
        if arr.ndim == 2:
            arr = np.expand_dims(arr, axis=1)
        elif arr.ndim != 3:
            raise ValueError(f"Expected 2D or 3D array for LSTMAutoencoder, got shape {arr.shape}")
        return torch.from_numpy(arr)

    def fit(
        self,
        X_train: np.ndarray,
        X_val: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> "LSTMAutoencoderDetector":
        """Fit autoencoder on normal/unlabeled sequences (unsupervised)."""
        self._set_seeds()
        if feature_names is not None:
            self._feature_names = list(feature_names)

        t_X_train = self._prepare_tensor(X_train)
        self._input_dim = t_X_train.shape[2]
        seq_len = t_X_train.shape[1]

        self.network = PyTorchLSTMAutoencoderNetwork(
            input_dim=self._input_dim,
            seq_len=seq_len,
            encoder_units=self.encoder_units,
            latent_dim=self.latent_dim,
            decoder_units=self.decoder_units,
        ).to(self.device)

        train_dataset = TensorDataset(t_X_train)
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(self.seed),
        )

        has_val = X_val is not None
        if has_val:
            t_X_val = self._prepare_tensor(X_val).to(self.device)

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.network.parameters(), lr=self.learning_rate)

        best_val_loss = float("inf")
        patience_counter = 0
        best_state = None

        logger.info(
            f"Training LSTM Autoencoder on device '{self.device}' with {len(t_X_train)} samples for max {self.epochs} epochs..."
        )

        self.network.train()
        for epoch in range(1, self.epochs + 1):
            total_loss = 0.0
            for (batch_x,) in train_loader:
                batch_x = batch_x.to(self.device)
                optimizer.zero_grad()
                recon = self.network(batch_x)
                loss = criterion(recon, batch_x)
                loss.backward()
                optimizer.step()
                total_loss += float(loss.item()) * len(batch_x)

            train_loss = total_loss / len(t_X_train)

            if has_val:
                self.network.eval()
                with torch.no_grad():
                    val_recon = self.network(t_X_val)
                    val_loss = float(criterion(val_recon, t_X_val).item())
                self.network.train()

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = {k: v.cpu().clone() for k, v in self.network.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1

                if epoch % 5 == 0 or patience_counter == 0:
                    logger.debug(
                        f"Epoch {epoch:03d} | Train Recon MSE: {train_loss:.5f} | Val Recon MSE: {val_loss:.5f}"
                    )

                if patience_counter >= self.patience:
                    logger.info(
                        f"Early stopping at epoch {epoch} (best val MSE: {best_val_loss:.5f})"
                    )
                    break

        if best_state is not None:
            self.network.load_state_dict(best_state)

        self.network.eval()
        self._is_fitted = True
        logger.info("LSTM Autoencoder training complete.")
        return self

    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """Compute anomaly score as per-sample mean squared reconstruction error."""
        if not self._is_fitted or self.network is None:
            raise RuntimeError("Detector must be fitted before score_samples() is called.")

        self.network.eval()
        t_X = self._prepare_tensor(X)
        dataset = TensorDataset(t_X)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        scores = []
        with torch.no_grad():
            for (batch_x,) in loader:
                batch_x = batch_x.to(self.device)
                recon = self.network(batch_x)
                # Mean squared error per sequence: average over (seq_len, input_dim)
                sq_err = torch.mean((batch_x - recon) ** 2, dim=(1, 2))
                scores.append(sq_err.cpu().numpy())

        return np.concatenate(scores, axis=0).astype(np.float64)

    def save(self, file_path: Path | str) -> None:
        """Save model checkpoint and architecture parameters."""
        if not self._is_fitted or self.network is None:
            raise RuntimeError("Cannot save unfitted detector.")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        weights_path = path.with_suffix(".pt")
        torch.save(self.network.state_dict(), weights_path)

        meta_path = path.with_suffix(".meta.json")
        meta = {
            "name": self.name,
            "input_dim": self._input_dim,
            "seq_len": self.network.seq_len,
            "encoder_units": self.encoder_units,
            "latent_dim": self.latent_dim,
            "decoder_units": self.decoder_units,
            "threshold": self._threshold,
            "feature_names": self._feature_names,
            "seed": self.seed,
            "is_fitted": self._is_fitted,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Saved LSTM Autoencoder to {weights_path}")

    @classmethod
    def load(cls, file_path: Path | str) -> "LSTMAutoencoderDetector":
        """Load model checkpoint and restore autoencoder."""
        path = Path(file_path)
        meta_path = path.with_suffix(".meta.json")
        weights_path = path.with_suffix(".pt")

        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found at {meta_path}")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        instance = cls(
            encoder_units=meta.get("encoder_units", [64, 32]),
            latent_dim=meta.get("latent_dim", 16),
            decoder_units=meta.get("decoder_units", [32, 64]),
            seed=meta.get("seed", 42),
        )
        instance._threshold = meta.get("threshold")
        instance._input_dim = meta["input_dim"]
        instance._feature_names = meta.get("feature_names", [])

        network = PyTorchLSTMAutoencoderNetwork(
            input_dim=instance._input_dim,
            seq_len=meta["seq_len"],
            encoder_units=instance.encoder_units,
            latent_dim=instance.latent_dim,
            decoder_units=instance.decoder_units,
        )
        state_dict = torch.load(weights_path, map_location=instance.device)
        network.load_state_dict(state_dict)
        network.to(instance.device)
        network.eval()

        instance.network = network
        instance._is_fitted = True
        return instance
