"""
tests/integration/test_forecasting_pipeline.py — Integration test for end-to-end forecasting pipeline.
"""

from pathlib import Path

import numpy as np
import pytest

from src.forecasting.evaluator import compare_models, evaluate_forecaster
from src.forecasting.features import prepare_forecasting_data
from src.forecasting.lstm_model import LSTMForecaster
from src.forecasting.persistence import PersistenceForecaster
from src.forecasting.xgboost_model import XGBoostForecaster
from src.utils.io import load_parquet


@pytest.fixture(scope="module")
def prepared_splits():
    """Load first 500 rows of processed load profiles and construct mini splits."""
    data_path = Path("data/processed/load_profiles.parquet")
    if not data_path.exists():
        pytest.skip("Processed profiles parquet not found in data/processed/")

    df = load_parquet(data_path).iloc[:500]
    total_len = len(df)
    train_n = int(total_len * 0.7)
    val_n = int(total_len * 0.15)

    splits = {
        "train_indices": list(df.index[:train_n]),
        "validation_indices": list(df.index[train_n : train_n + val_n]),
        "test_indices": list(df.index[train_n + val_n :]),
    }

    tabular = prepare_forecasting_data(df, splits, lookback_steps=12, mode="tabular")
    sequence = prepare_forecasting_data(df, splits, lookback_steps=12, mode="sequence")
    return tabular, sequence


def test_end_to_end_forecasting_pipeline(prepared_splits):
    """Verify Persistence, XGBoost, and LSTM models train, predict, and evaluate cleanly."""
    tabular, sequence = prepared_splits

    # 1. Persistence
    pers = PersistenceForecaster()
    pers.fit(tabular.X_train, tabular.y_train, feature_names=tabular.feature_names)
    eval_pers = evaluate_forecaster(pers, tabular.X_test, tabular.y_test, split_name="test")

    # 2. XGBoost
    xgb = XGBoostForecaster(n_estimators=30, max_depth=3, learning_rate=0.1, random_state=42)
    xgb.fit(
        tabular.X_train,
        tabular.y_train,
        X_val=tabular.X_val,
        y_val=tabular.y_val,
        feature_names=tabular.feature_names,
    )
    eval_xgb = evaluate_forecaster(xgb, tabular.X_test, tabular.y_test, split_name="test")

    # 3. LSTM
    lstm = LSTMForecaster(units=[16, 8], epochs=10, batch_size=32, seed=42)
    lstm.fit(
        sequence.X_train,
        sequence.y_train,
        X_val=sequence.X_val,
        y_val=sequence.y_val,
        feature_names=sequence.feature_names,
    )
    eval_lstm = evaluate_forecaster(lstm, sequence.X_test, sequence.y_test, split_name="test")

    # Assertions
    for res in [eval_pers, eval_xgb, eval_lstm]:
        assert not np.isnan(res.y_pred).any()
        assert res.metrics["mae"] > 0.0
        assert res.metrics["rmse"] > 0.0
        assert 0.0 <= res.metrics["mape"] <= 100.0

    # Comparison DataFrame
    comp_df = compare_models([eval_pers, eval_xgb, eval_lstm])
    assert len(comp_df) == 3
    assert set(comp_df["model"]) == {"persistence", "xgboost", "lstm"}
