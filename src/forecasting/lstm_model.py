"""
src/forecasting/lstm_model.py — PyTorch Long Short-Term Memory (LSTM) load estimator.

Implements the recurrent deep learning architecture for temporal sequence modeling
with early stopping, GPU/CUDA acceleration, and deterministic weight initialization.
"""

import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from src.forecasting.base import BaseLoadForecaster
from src.utils.config import LSTMConfig
from src.utils.logging import get_logger

logger = get_logger("forecasting.lstm")


class PyTorchLSTMNetwork(nn.Module):
    """Stacked LSTM neural network for single-step time-series load regression."""

    def __init__(
        self,
        input_dim: int,
        hidden_units: list[int] | None = None,
        dropout: float = 0.2,
    ) -> None:
        """Initialize the LSTM layers and regression head.

        Args:
            input_dim: Number of input features per timestep.
            hidden_units: List of hidden dimension sizes for each LSTM layer.
            dropout: Dropout probability between recurrent layers and before head.
        """
        super().__init__()
        self.lstm_layers = nn.ModuleList()
        curr_dim = input_dim
        units = hidden_units if hidden_units is not None else [64, 32]

        for h_dim in units:
            # Batch first: (batch, seq, feature)
            self.lstm_layers.append(
                nn.LSTM(
                    input_size=curr_dim,
                    hidden_size=h_dim,
                    batch_first=True,
                )
            )
            curr_dim = h_dim

        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(curr_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through recurrent network.

        Args:
            x: Input tensor of shape (batch, seq_len, input_dim).

        Returns:
            Predicted load tensor of shape (batch, 1).
        """
        out = x
        for i, lstm in enumerate(self.lstm_layers):
            out, _ = lstm(out)
            if i < len(self.lstm_layers) - 1:
                out = self.dropout(out)

        # Take final timestep output: out[:, -1, :]
        last_step = out[:, -1, :]
        last_step = self.dropout(last_step)
        prediction = self.head(last_step)
        return prediction.squeeze(-1)


class LSTMForecaster(BaseLoadForecaster):
    """PyTorch-based LSTM forecaster managing dataset collation, training, and inference."""

    def __init__(
        self,
        config: LSTMConfig | None = None,
        units: list[int] | None = None,
        dropout: float = 0.2,
        batch_size: int = 64,
        epochs: int = 50,
        patience: int = 8,
        learning_rate: float = 0.001,
        seed: int = 42,
    ) -> None:
        """Initialize LSTM forecaster.

        Args:
            config: Optional LSTMConfig instance.
            units: List of layer sizes (defaults to [64, 32]).
            dropout: Dropout rate.
            batch_size: Mini-batch size.
            epochs: Maximum training epochs.
            patience: Early stopping patience.
            learning_rate: Optimizer learning rate.
            seed: Random seed for reproducibility.
        """
        super().__init__(name="lstm")
        cfg = config or LSTMConfig()

        self.units = units or cfg.units
        self.dropout = dropout if dropout != 0.2 else cfg.dropout
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience
        self.learning_rate = learning_rate
        self.seed = seed

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.network: PyTorchLSTMNetwork | None = None
        self._input_dim: int = 0

    def _set_seeds(self) -> None:
        """Set random seeds for PyTorch operations."""
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

    def _prepare_tensor(self, X: np.ndarray) -> torch.Tensor:
        """Format input array to 3D tensor (batch, seq, feature)."""
        arr = np.asarray(X, dtype=np.float32)
        if arr.ndim == 2:
            # (samples, features) -> treat as sequence of length 1
            arr = np.expand_dims(arr, axis=1)
        elif arr.ndim != 3:
            raise ValueError(f"Expected 2D or 3D input array, got shape {arr.shape}")
        return torch.from_numpy(arr)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        feature_names: list[str] | None = None,
    ) -> "LSTMForecaster":
        """Train the PyTorch LSTM network with early stopping."""
        self._set_seeds()
        if feature_names is not None:
            self._feature_names = list(feature_names)

        t_X_train = self._prepare_tensor(X_train)
        t_y_train = torch.from_numpy(np.asarray(y_train, dtype=np.float32))

        self._input_dim = t_X_train.shape[2]
        self.network = PyTorchLSTMNetwork(
            input_dim=self._input_dim,
            hidden_units=self.units,
            dropout=self.dropout,
        ).to(self.device)

        train_dataset = TensorDataset(t_X_train, t_y_train)
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(self.seed),
        )

        has_val = X_val is not None and y_val is not None
        if has_val:
            t_X_val = self._prepare_tensor(X_val).to(self.device)
            t_y_val = torch.from_numpy(np.asarray(y_val, dtype=np.float32)).to(self.device)

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.network.parameters(), lr=self.learning_rate)

        best_val_loss = float("inf")
        patience_counter = 0
        best_state = None

        logger.info(
            f"Training LSTM on device '{self.device}' with {len(t_X_train)} samples for max {self.epochs} epochs..."
        )

        self.network.train()
        for epoch in range(1, self.epochs + 1):
            total_train_loss = 0.0
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                pred = self.network(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()

                total_train_loss += float(loss.item()) * len(batch_x)

            train_loss = total_train_loss / len(t_X_train)

            # Validation check
            if has_val:
                self.network.eval()
                with torch.no_grad():
                    val_pred = self.network(t_X_val)
                    val_loss = float(criterion(val_pred, t_y_val).item())
                self.network.train()

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = {k: v.cpu().clone() for k, v in self.network.state_dict().items()}
                    patience_counter = 0
                else:
                    patience_counter += 1

                if epoch % 5 == 0 or patience_counter == 0:
                    logger.debug(
                        f"Epoch {epoch:03d} | Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f}"
                    )

                if patience_counter >= self.patience:
                    logger.info(
                        f"Early stopping triggered at epoch {epoch} (best val loss: {best_val_loss:.5f})"
                    )
                    break

        if best_state is not None:
            self.network.load_state_dict(best_state)

        self.network.eval()
        self._is_fitted = True
        logger.info("LSTM training completed.")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate forecasts using trained LSTM."""
        if not self._is_fitted or self.network is None:
            raise RuntimeError("Model must be fitted before predict() is called.")

        self.network.eval()
        t_X = self._prepare_tensor(X)
        dataset = TensorDataset(t_X)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)

        preds = []
        with torch.no_grad():
            for (batch_x,) in loader:
                batch_x = batch_x.to(self.device)
                out = self.network(batch_x)
                preds.append(out.cpu().numpy())

        return np.concatenate(preds, axis=0).astype(np.float64)

    def save(self, file_path: Path | str) -> None:
        """Save network weights and hyperparameters."""
        if not self._is_fitted or self.network is None:
            raise RuntimeError("Cannot save unfitted model.")

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        weights_path = path.with_suffix(".pt")
        torch.save(self.network.state_dict(), weights_path)

        meta_path = path.with_suffix(".meta.json")
        meta = {
            "name": self.name,
            "input_dim": self._input_dim,
            "units": self.units,
            "dropout": self.dropout,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "feature_names": self._feature_names,
            "seed": self.seed,
            "is_fitted": self._is_fitted,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Saved LSTM weights to {weights_path} and metadata to {meta_path}")

    @classmethod
    def load(cls, file_path: Path | str) -> "LSTMForecaster":
        """Load network weights and restore model."""
        path = Path(file_path)
        meta_path = path.with_suffix(".meta.json")
        weights_path = path.with_suffix(".pt")

        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found at {meta_path}")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        instance = cls(
            units=meta.get("units", [64, 32]),
            dropout=meta.get("dropout", 0.2),
            batch_size=meta.get("batch_size", 64),
            learning_rate=meta.get("learning_rate", 0.001),
            seed=meta.get("seed", 42),
        )
        instance._input_dim = meta["input_dim"]
        instance._feature_names = meta.get("feature_names", [])

        network = PyTorchLSTMNetwork(
            input_dim=instance._input_dim,
            hidden_units=instance.units,
            dropout=instance.dropout,
        )
        state_dict = torch.load(weights_path, map_location=instance.device)
        network.load_state_dict(state_dict)
        network.to(instance.device)
        network.eval()

        instance.network = network
        instance._is_fitted = True
        return instance
