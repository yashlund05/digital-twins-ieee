"""
src/forecasting/evaluator.py — Model evaluation and comparison framework.

Provides standardized evaluation of load forecasters against validation and test splits,
aggregates regression metrics (MAE, RMSE, MAPE, R²), and formats comparative tables.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.evaluation.forecasting_metrics import compute_forecasting_metrics
from src.forecasting.base import BaseLoadForecaster
from src.utils.logging import get_logger

logger = get_logger("forecasting.evaluator")


@dataclass
class ModelEvaluationResult:
    """Stores predictions and metrics for a single model on a dataset split."""

    model_name: str
    split_name: str
    metrics: dict[str, float]
    y_true: np.ndarray
    y_pred: np.ndarray


def evaluate_forecaster(
    model: BaseLoadForecaster,
    X: np.ndarray,
    y: np.ndarray,
    split_name: str = "test",
) -> ModelEvaluationResult:
    """Evaluate a trained model against ground truth targets.

    Args:
        model: Trained BaseLoadForecaster instance.
        X: Input feature array.
        y: Ground truth targets.
        split_name: Dataset split name ('val' or 'test').

    Returns:
        ModelEvaluationResult with computed metrics and arrays.
    """
    logger.info(f"Evaluating {model.name} on {split_name} split ({len(y)} samples)...")
    y_pred = model.predict(X)
    metrics = compute_forecasting_metrics(y_true=y, y_pred=y_pred)

    logger.info(
        f"[{model.name.upper()} | {split_name.upper()}] "
        f"MAE: {metrics['mae']:.4f} kW | RMSE: {metrics['rmse']:.4f} kW | "
        f"MAPE: {metrics['mape']:.2f}% | R²: {metrics['r2']:.4f}"
    )

    return ModelEvaluationResult(
        model_name=model.name,
        split_name=split_name,
        metrics=metrics,
        y_true=y,
        y_pred=y_pred,
    )


def compare_models(results: list[ModelEvaluationResult]) -> pd.DataFrame:
    """Format a list of evaluation results into a clean comparison DataFrame.

    Args:
        results: List of ModelEvaluationResult instances.

    Returns:
        DataFrame indexed by (model, split) showing MAE, RMSE, MAPE, R².
    """
    rows = []
    for r in results:
        rows.append(
            {
                "model": r.model_name,
                "split": r.split_name,
                "mae_kw": r.metrics["mae"],
                "rmse_kw": r.metrics["rmse"],
                "mape_pct": r.metrics["mape"],
                "r2": r.metrics["r2"],
            }
        )
    return pd.DataFrame(rows)
