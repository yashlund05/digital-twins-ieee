# Experiment E5: Controlled Synchronization Staleness Sweep — Summary Report

- **Run ID:** `E5_BASELINE_RECONCILIATION_SEED42_20260930`
- **Execution Timestamp:** `2026-09-30T17:46:02.066383`
- **Random Seed:** `42`
- **Total Conditions Executed:** `1`

## 1. Synchronization & Realized Age of Information (AoI) Table

| Staleness (s) | P_drop | Scheduled Updates | Successful Updates | Dropped Updates | Actual Drop Rate | Mean AoI (s) | P95 AoI (s) | Max AoI (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00 | 35040 | 35040 | 0 | 0.0000 | 0.00 | 0.00 | 0.00 |

## 2. Key Performance Degradation Overview

### Anomaly Detection F1-Score vs. Synchronization Condition

|          |   ('isolation_forest', 'raw') |   ('isolation_forest', 'residual') |   ('lstm_autoencoder', 'raw') |   ('lstm_autoencoder', 'residual') |
|:---------|------------------------------:|-----------------------------------:|------------------------------:|-----------------------------------:|
| (0, 0.0) |                      0.117647 |                          0.0887273 |                      0.538606 |                           0.977956 |

### Load Forecasting MAPE (%) vs. Synchronization Condition

|          |   lstm |   persistence |   xgboost |
|:---------|-------:|--------------:|----------:|
| (0, 0.0) | 8.9504 |       14.7321 |   9.06348 |