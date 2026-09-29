"""
src/forecasting/trainer.py — Training coordinator for all load forecasting models.

Loads processed data, builds leak-free tabular and sequence splits, trains Persistence,
XGBoost, and LSTM models, and evaluates baseline metrics under perfect synchronization.
"""

import json
from pathlib import Path

import pandas as pd

from src.forecasting.base import BaseLoadForecaster
from src.forecasting.evaluator import ModelEvaluationResult, compare_models, evaluate_forecaster
from src.forecasting.features import prepare_forecasting_data
from src.forecasting.lstm_model import LSTMForecaster
from src.forecasting.persistence import PersistenceForecaster
from src.forecasting.xgboost_model import XGBoostForecaster
from src.utils.config import ForecastingConfig, load_forecasting_config
from src.utils.io import load_parquet
from src.utils.logging import get_logger
from src.utils.reproducibility import set_all_seeds

logger = get_logger("forecasting.trainer")


class ForecastingTrainer:
    """Coordinates end-to-end training and evaluation of load estimation models."""

    def __init__(
        self,
        config: ForecastingConfig | None = None,
        data_path: Path | str = "data/processed/load_profiles.parquet",
        splits_path: Path | str = "data/processed/splits.json",
        seed: int = 42,
    ) -> None:
        """Initialize forecasting trainer.

        Args:
            config: Optional ForecastingConfig instance.
            data_path: Path to processed load profiles parquet file.
            splits_path: Path to dataset splits JSON file.
            seed: Master random seed.
        """
        self.config = config or load_forecasting_config()
        self.data_path = Path(data_path)
        self.splits_path = Path(splits_path)
        self.seed = seed
        self.trained_models: dict[str, BaseLoadForecaster] = {}
        self.evaluation_results: list[ModelEvaluationResult] = []

    def train_and_evaluate_all(
        self,
        models_to_run: list[str] | None = None,
        target_name: str = "total_load_p_kw",
    ) -> tuple[dict[str, BaseLoadForecaster], pd.DataFrame]:
        """Train and evaluate the selected forecasting models.

        Args:
            models_to_run: List of model names to run (defaults to config.models).
            target_name: Target column name ('total_load_p_kw' or bus specific).

        Returns:
            Tuple of (trained_models_dict, comparison_dataframe).
        """
        set_all_seeds(self.seed)
        selected_models = models_to_run or self.config.models

        logger.info(f"Loading data from {self.data_path} and splits from {self.splits_path}...")
        df = load_parquet(self.data_path)
        with open(self.splits_path, encoding="utf-8") as f:
            splits = json.load(f)

        # 1. Prepare Tabular splits (for Persistence & XGBoost)
        logger.info("Preparing tabular features for Persistence and XGBoost...")
        tabular_splits = prepare_forecasting_data(
            df=df,
            splits=splits,
            lookback_steps=self.config.lookback_steps,
            target_name=target_name,
            mode="tabular",
        )

        # --- Persistence Model ---
        if "persistence" in selected_models:
            logger.info("--- Fitting Persistence Baseline ---")
            persistence_model = PersistenceForecaster(lag_feature_name="lag_1")
            persistence_model.fit(
                X_train=tabular_splits.X_train,
                y_train=tabular_splits.y_train,
                feature_names=tabular_splits.feature_names,
            )
            # Evaluate on Val & Test
            val_res = evaluate_forecaster(
                persistence_model, tabular_splits.X_val, tabular_splits.y_val, split_name="val"
            )
            test_res = evaluate_forecaster(
                persistence_model, tabular_splits.X_test, tabular_splits.y_test, split_name="test"
            )
            self.trained_models["persistence"] = persistence_model
            self.evaluation_results.extend([val_res, test_res])

        # --- XGBoost Model ---
        if "xgboost" in selected_models:
            logger.info("--- Fitting XGBoost Model ---")
            xgb_model = XGBoostForecaster(config=self.config.xgboost)
            xgb_model.fit(
                X_train=tabular_splits.X_train,
                y_train=tabular_splits.y_train,
                X_val=tabular_splits.X_val,
                y_val=tabular_splits.y_val,
                feature_names=tabular_splits.feature_names,
            )
            val_res = evaluate_forecaster(
                xgb_model, tabular_splits.X_val, tabular_splits.y_val, split_name="val"
            )
            test_res = evaluate_forecaster(
                xgb_model, tabular_splits.X_test, tabular_splits.y_test, split_name="test"
            )
            self.trained_models["xgboost"] = xgb_model
            self.evaluation_results.extend([val_res, test_res])

        # --- LSTM Model ---
        if "lstm" in selected_models:
            logger.info("--- Preparing Sequence Tensors & Fitting LSTM Model ---")
            seq_splits = prepare_forecasting_data(
                df=df,
                splits=splits,
                lookback_steps=self.config.lookback_steps,
                target_name=target_name,
                mode="sequence",
            )
            lstm_model = LSTMForecaster(
                config=self.config.lstm,
                seed=self.seed,
            )
            lstm_model.fit(
                X_train=seq_splits.X_train,
                y_train=seq_splits.y_train,
                X_val=seq_splits.X_val,
                y_val=seq_splits.y_val,
                feature_names=seq_splits.feature_names,
            )
            val_res = evaluate_forecaster(
                lstm_model, seq_splits.X_val, seq_splits.y_val, split_name="val"
            )
            test_res = evaluate_forecaster(
                lstm_model, seq_splits.X_test, seq_splits.y_test, split_name="test"
            )
            self.trained_models["lstm"] = lstm_model
            self.evaluation_results.extend([val_res, test_res])

        comparison_df = compare_models(self.evaluation_results)
        return self.trained_models, comparison_df

    def save_models(self, output_dir: Path | str) -> None:
        """Save all fitted models to designated directory.

        Args:
            output_dir: Destination folder.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        for name, model in self.trained_models.items():
            model.save(out_path / name)
        logger.info(f"Saved {len(self.trained_models)} models to {out_path}")
