"""
forecasting — Load Estimation Models

Implements short-term load estimation models:
- Persistence baseline
- XGBoost
- LSTM

All models are evaluated under controlled synchronization staleness
conditions as part of Experiment E5.
"""
