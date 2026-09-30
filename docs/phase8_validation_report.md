# Phase 8 — Validation and Verification Report

> **Experiment E5: Controlled Synchronization Staleness Sweep**  
> **Repository:** `digital-twins-ieee1`  
> **Evaluation Date:** 2026-09-30  
> **Executed Run ID:** `E5_STALENESS_SWEEP_SEED42_20260930`

---

## 1. Compliance and Integrity Verification Checklist

| Requirement | Target Standard | Verification Result | Evidence / Details |
|---|---|:---:|---|
| **Phase Scope Confinement** | Implement Phase 8 ONLY | **PASS** | No Phase 9 hypothesis tests (H3 acceptance/rejection) or Phase 10 multi-seed scripts were executed. |
| **Baseline Equivalence** | $(\Delta t = 0, P = 0)$ matches Phase 7 E4 | **PASS** | Residual LSTM-AE $F_1 = 0.702158$, Raw IF $F_1 = 0.117647$, exactly identical to E4 baseline. |
| **Raw Input Invariance** | Raw anomaly metrics invariant across $\Delta t$ | **PASS** | Raw IF ($F_1 = 0.117647$) and Raw LSTM-AE ($F_1 = 0.210923$) remain strictly identical across all 24 conditions. |
| **Temporal Causality** | Zero future information leakage | **PASS** | For all $t$, $t_{\text{sync}} \le t$. Verified by unit and integration tests. |
| **Leakage-Free Normalization** | Train-only scaling statistics | **PASS** | Normalizers fit on clean training split only; frozen parameters applied downstream. |
| **No Test Re-Tuning** | Frozen thresholds $\tau_{95}$ | **PASS** | All anomaly thresholds calibrated on validation residuals and held static across test conditions. |
| **Full Factorial Coverage** | 24 / 24 conditions evaluated | **PASS** | 6 intervals $\times$ 4 drop rates with zero dropped conditions. |
| **Test Suite Regressions** | 100% test pass rate | **PASS** | All 144 unit, integration, and validation tests pass cleanly (`pytest` 144 passed in 110.85s). |

---

## 2. Test Execution Summary

The complete repository test suite was run via `python -m pytest`:

```text
================= 144 passed, 4 warnings in 110.85s (0:01:50) =================
- tests/unit/test_staleness_sweep.py: 13 passed
- tests/integration/test_staleness_pipeline.py: 1 passed
- tests/unit/test_sync_engine.py: 5 passed
- tests/unit/test_sync_policies.py: 5 passed
- tests/unit/test_residual_calculator.py: 10 passed
- tests/unit/test_residual_features.py: 6 passed
- tests/unit/test_residual_normalizer.py: 7 passed
- tests/unit/test_e4_baseline.py: 4 passed
- tests/unit/test_forecasting_models.py: 6 passed
- tests/unit/test_anomaly_detectors.py: 12 passed
- tests/validation/test_ieee33_sanity.py: 5 passed
- tests/validation/test_data_integrity.py: 6 passed
- tests/validation/test_repository_foundation.py: 5 passed
```

---

## 3. Realized Synchronization Metrics & Age of Information (AoI)

Audited over $N = 35{,}040$ discrete timesteps:

| $\Delta t$ (s) | $P_{\text{drop}}$ | Scheduled Updates | Successful Updates | Dropped Updates | Actual Drop Rate | Mean AoI (s) | P95 AoI (s) | Max AoI (s) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.00 | 35040 | 35040 | 0 | 0.0000 | 0.00 | 0.00 | 0.00 |
| 0 | 0.05 | 35040 | 33269 | 1771 | 0.0505 | 0.05 | 1.00 | 3.00 |
| 0 | 0.10 | 35040 | 31602 | 3438 | 0.0981 | 0.11 | 1.00 | 4.00 |
| 0 | 0.20 | 35040 | 28058 | 6982 | 0.1993 | 0.25 | 1.00 | 6.00 |
| 1 | 0.00 | 35040 | 35040 | 0 | 0.0000 | 0.00 | 0.00 | 0.00 |
| 1 | 0.05 | 35040 | 33269 | 1771 | 0.0505 | 0.05 | 1.00 | 3.00 |
| 1 | 0.10 | 35040 | 31602 | 3438 | 0.0981 | 0.11 | 1.00 | 4.00 |
| 1 | 0.20 | 35040 | 28058 | 6982 | 0.1993 | 0.25 | 1.00 | 6.00 |
| 5 | 0.00 | 7008 | 7008 | 0 | 0.0000 | 2.00 | 4.00 | 4.00 |
| 5 | 0.05 | 7299 | 6936 | 363 | 0.0497 | 2.03 | 4.00 | 6.00 |
| 5 | 0.10 | 7611 | 6858 | 753 | 0.0989 | 2.07 | 4.00 | 8.00 |
| 5 | 0.20 | 8372 | 6668 | 1704 | 0.2035 | 2.16 | 4.00 | 10.00 |
| 15 | 0.00 | 2336 | 2336 | 0 | 0.0000 | 7.00 | 14.00 | 14.00 |
| 15 | 0.05 | 2446 | 2329 | 117 | 0.0478 | 7.03 | 14.00 | 16.00 |
| 15 | 0.10 | 2574 | 2320 | 254 | 0.0987 | 7.06 | 14.00 | 17.00 |
| 15 | 0.20 | 2885 | 2297 | 588 | 0.2038 | 7.14 | 14.00 | 20.00 |
| 60 | 0.00 | 584 | 584 | 0 | 0.0000 | 29.50 | 56.05 | 59.00 |
| 60 | 0.05 | 611 | 584 | 27 | 0.0442 | 29.51 | 57.00 | 61.00 |
| 60 | 0.10 | 643 | 583 | 60 | 0.0933 | 29.55 | 57.00 | 62.00 |
| 60 | 0.20 | 745 | 582 | 163 | 0.2188 | 29.63 | 57.00 | 65.00 |
| 300 | 0.00 | 117 | 117 | 0 | 0.0000 | 149.29 | 284.00 | 299.00 |
| 300 | 0.05 | 121 | 117 | 4 | 0.0331 | 149.30 | 284.00 | 300.00 |
| 300 | 0.10 | 129 | 117 | 12 | 0.0930 | 149.32 | 284.05 | 301.00 |
| 300 | 0.20 | 148 | 117 | 31 | 0.2095 | 149.36 | 285.00 | 302.00 |

---

## 4. Quantitative Results & Degradation Trajectories

### 4.1 Unsupervised Anomaly Detection $F_1$-Score

| Condition $(\Delta t, P_{\text{drop}})$ | IF (Raw) | IF (Residual) | LSTM-AE (Raw) | LSTM-AE (Residual) |
|---|---:|---:|---:|---:|
| **(0s, 0.00)** (Baseline) | 0.1176 | 0.0887 | 0.2109 | **0.7022** |
| (0s, 0.05) | 0.1176 | 0.0887 | 0.2109 | 0.5186 |
| (0s, 0.10) | 0.1176 | 0.0887 | 0.2109 | 0.4150 |
| (0s, 0.20) | 0.1176 | 0.0887 | 0.2109 | 0.2933 |
| **(1s, 0.00)** | 0.1176 | 0.0887 | 0.2109 | **0.7022** |
| (1s, 0.05) | 0.1176 | 0.0887 | 0.2109 | 0.5186 |
| (1s, 0.10) | 0.1176 | 0.0887 | 0.2109 | 0.4150 |
| (1s, 0.20) | 0.1176 | 0.0887 | 0.2109 | 0.2933 |
| **(5s, 0.00)** | 0.1176 | 0.0887 | 0.2109 | 0.1074 |
| (5s, 0.05) | 0.1176 | 0.0887 | 0.2109 | 0.1070 |
| (5s, 0.10) | 0.1176 | 0.0887 | 0.2109 | 0.1070 |
| (5s, 0.20) | 0.1176 | 0.0887 | 0.2109 | 0.1067 |
| **(15s, 0.00)** | 0.1176 | 0.0887 | 0.2109 | 0.0942 |
| (15s, 0.05) | 0.1176 | 0.0887 | 0.2109 | 0.0942 |
| (15s, 0.10) | 0.1176 | 0.0887 | 0.2109 | 0.0941 |
| (15s, 0.20) | 0.1176 | 0.0887 | 0.2109 | 0.0940 |
| **(60s, 0.00)** | 0.1176 | 0.0887 | 0.2109 | 0.0901 |
| (60s, 0.05) | 0.1176 | 0.0887 | 0.2109 | 0.0900 |
| (60s, 0.10) | 0.1176 | 0.0887 | 0.2109 | 0.0900 |
| (60s, 0.20) | 0.1176 | 0.0887 | 0.2109 | 0.0899 |
| **(300s, 0.00)** | 0.1176 | 0.0887 | 0.2109 | 0.0890 |
| (300s, 0.05) | 0.1176 | 0.0887 | 0.2109 | 0.0890 |
| (300s, 0.10) | 0.1176 | 0.0887 | 0.2109 | 0.0890 |
| (300s, 0.20) | 0.1176 | 0.0887 | 0.2109 | 0.0890 |

### 4.2 Load Forecasting MAPE (%)

| Condition $(\Delta t, P_{\text{drop}})$ | Persistence | XGBoost | LSTM Forecaster |
|---|---:|---:|---:|
| **(0s, 0.00)** (Baseline) | 14.73% | 9.06% | **8.95%** |
| (0s, 0.05) | 14.95% | 9.13% | 8.96% |
| (0s, 0.10) | 15.23% | 9.22% | 9.01% |
| (0s, 0.20) | 15.81% | 9.47% | 9.17% |
| **(1s, 0.00)** | 14.73% | 9.06% | **8.95%** |
| (1s, 0.05) | 14.95% | 9.13% | 8.96% |
| (1s, 0.10) | 15.23% | 9.22% | 9.01% |
| (1s, 0.20) | 15.81% | 9.47% | 9.17% |
| **(5s, 0.00)** | 25.12% | 15.35% | 15.26% |
| (5s, 0.05) | 25.00% | 14.84% | 15.18% |
| (5s, 0.10) | 25.87% | 16.02% | 15.82% |
| (5s, 0.20) | 25.94% | 15.89% | 16.06% |
| **(15s, 0.00)** | 56.34% | 42.58% | 41.78% |
| (15s, 0.05) | 58.87% | 44.25% | 43.30% |
| (15s, 0.10) | 56.49% | 42.94% | 42.66% |
| (15s, 0.20) | 59.03% | 44.43% | 44.26% |
| **(60s, 0.00)** | 83.55% | 62.16% | 61.33% |
| (60s, 0.05) | 83.36% | 62.75% | 60.11% |
| (60s, 0.10) | 83.31% | 62.49% | 58.62% |
| (60s, 0.20) | 81.89% | 61.63% | 60.11% |
| **(300s, 0.00)** | 81.13% | 61.69% | 62.29% |
| (300s, 0.05) | 79.23% | 61.06% | 60.02% |
| (300s, 0.10) | 82.38% | 65.54% | 59.83% |
| (300s, 0.20) | 85.45% | 64.77% | 59.53% |

---

## 5. Artifact Verification

All machine-readable artifacts have been verified in:
`experiments/runs/E5_STALENESS_SWEEP_SEED42_20260930/`

- `manifest.json`: Verified JSON schema, git SHA, and execution parameters.
- `config_snapshot.yaml`: Verified YAML syntax and exact mirror of experiment configuration.
- `aoi_statistics.json`: Verified complete 24-condition AoI distribution metrics.
- `comparison.csv`: Verified long-format table containing all 168 rows (24 conditions $\times$ 7 models).
- `metrics.json`: Verified structured tree storing precision, recall, F1, AUC-ROC, AUC-PR, RMSE, MAE, MAPE.
- `predictions.parquet`: Verified non-empty parquet dataframe containing predictions across all conditions.
- `synchronization_logs.parquet`: Verified discrete update traces with true timestamps.
- `summary.md`: Verified markdown presentation.
