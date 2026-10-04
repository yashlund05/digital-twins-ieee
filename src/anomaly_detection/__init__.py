"""
src/anomaly_detection — Anomaly Detection Models module.

Implements unsupervised anomaly detection models:
- Isolation Forest
- PyTorch LSTM Autoencoder

All detectors are trained in strictly unsupervised fashion (no anomaly labels during training).
Labels are used ONLY for validation and test metric evaluation.
"""

from src.anomaly_detection.detector import BaseAnomalyDetector
from src.anomaly_detection.dual_mode import DualModeInversionCompensator
from src.anomaly_detection.experiment_e3 import run_experiment_e3
from src.anomaly_detection.isolation_forest import IsolationForestDetector
from src.anomaly_detection.lstm_autoencoder import (
    LSTMAutoencoderDetector,
    PyTorchLSTMAutoencoderNetwork,
)
from src.anomaly_detection.thresholds import (
    AoIAdaptiveThreshold,
    BaseThresholdSelector,
    FixedThreshold,
    OtsuThreshold,
    PercentileThreshold,
    get_threshold_selector,
)
from src.anomaly_detection.trainer import (
    AnomalyDetectionTrainer,
    AnomalyEvaluationResult,
)

__all__ = [
    "AnomalyDetectionTrainer",
    "AnomalyEvaluationResult",
    "AoIAdaptiveThreshold",
    "BaseAnomalyDetector",
    "BaseThresholdSelector",
    "DualModeInversionCompensator",
    "FixedThreshold",
    "IsolationForestDetector",
    "LSTMAutoencoderDetector",
    "OtsuThreshold",
    "PercentileThreshold",
    "PyTorchLSTMAutoencoderNetwork",
    "get_threshold_selector",
    "run_experiment_e3",
]
