"""
src/forecasting — Short-Term Load Estimation module.

Implements short-term load estimation models for distribution feeders:
- Persistence baseline
- XGBoost regressor
- PyTorch LSTM neural network

All models are evaluated under controlled synchronization staleness conditions.
"""

from src.forecasting.base import BaseLoadForecaster
from src.forecasting.evaluator import (
    ModelEvaluationResult,
    compare_models,
    evaluate_forecaster,
)
from src.forecasting.experiment_e2 import run_experiment_e2
from src.forecasting.features import (
    ForecastingDataSplits,
    compute_target_series,
    create_sequence_tensors,
    create_tabular_features,
    prepare_forecasting_data,
)
from src.forecasting.lstm_model import LSTMForecaster, PyTorchLSTMNetwork
from src.forecasting.persistence import PersistenceForecaster
from src.forecasting.trainer import ForecastingTrainer
from src.forecasting.xgboost_model import XGBoostForecaster

__all__ = [
    "BaseLoadForecaster",
    "ForecastingDataSplits",
    "ForecastingTrainer",
    "LSTMForecaster",
    "ModelEvaluationResult",
    "PersistenceForecaster",
    "PyTorchLSTMNetwork",
    "XGBoostForecaster",
    "compare_models",
    "compute_target_series",
    "create_sequence_tensors",
    "create_tabular_features",
    "evaluate_forecaster",
    "prepare_forecasting_data",
    "run_experiment_e2",
]
