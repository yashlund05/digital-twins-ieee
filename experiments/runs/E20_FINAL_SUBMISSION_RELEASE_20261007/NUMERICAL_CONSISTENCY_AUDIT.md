# Numerical Consistency and Traceability Audit

**Status:** PASS — 100% Traceable to Canonical Repository Artifacts

## Verified Numerical Registry
1. **Anomaly Detection Baseline (Ideal Synchronization, $\Delta t = 0\,$s, $P_{\text{drop}} = 0$):**
   - Residual LSTM-AE: $F_1 = 0.977956$, Precision = $0.990712$, Recall = $0.965517$ (`E4/metrics.json`)
   - Raw LSTM-AE: $F_1 = 0.538606$, Precision = $0.627907$, Recall = $0.471264$ (`E4/metrics.json`)
   - Raw Isolation Forest: $F_1 = 0.117647$ (`E4/metrics.json`)
   - Residual Isolation Forest: $F_1 = 0.088727$ (`E4/metrics.json`)
   - One-Class SVM Baseline (Clean): $F_1 = 0.670299$, Precision = $1.000000$, Recall = $0.504098$, $\text{FPR} = 0.000000$ (`E16/table_05_anomaly_detector_baselines.csv`)

2. **Short-Term Load Forecasting Baselines (Ideal Synchronization):**
   - LSTM Model: $\text{MAPE} = 8.950405\%$ (`E5/comparison.csv`), Clean mean $\text{MAPE} = 8.970307\%$ (`E16/table_06_forecasting_baselines.csv`)
   - GRU Model: Clean mean $\text{MAPE} = 9.002728\%$ (`E16/table_06_forecasting_baselines.csv`)
   - XGBoost Model: $\text{MAPE} = 9.063485\%$ (`E5/comparison.csv`)
   - Persistence Model: $\text{MAPE} = 14.732101\%$ (`E5/comparison.csv`)

3. **Staleness Degradation at $\Delta t = 300\,$s:**
   - Residual LSTM-AE F1 collapses from $0.978$ to $0.186214$ ($-80.9\%$ relative collapse)
   - LSTM Load Estimation MAPE inflates from $8.95\%$ to $62.16\%$ (severe recursive error compounding)
   - GRU Load Estimation MAPE inflates from $9.00\%$ to $62.21\%$

4. **Hardware Latency Benchmarks (Standard AMD64):**
   - Physics Residual Telemetry Subtraction: $0.00041\,$ms ($0.41\,\mu$s)
   - AoI-Adaptive Dynamic Threshold Lookup: $0.00128\,$ms ($1.28\,\mu$s)
   - LSTM Autoencoder Batch=1 Inference: $0.609\,$ms ($609\,\mu$s)
   - XGBoost Tabular Inference: $0.480\,$ms ($480\,\mu$s)
   - Total Online Residual Anomaly Pipeline: $0.6107\,$ms (allowing $>1600\,$Hz sample rate)
