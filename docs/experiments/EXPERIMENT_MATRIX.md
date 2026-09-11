# Experiment Matrix

> **Version:** 1.0.0 — September 2026
> **Status:** Design specification — no experiments executed

---

## Overview

This document defines the formal experimental design matrix for the synchronization staleness study.

> [!IMPORTANT]
> This matrix defines what WILL be measured. No measurements have been taken.
> Results columns will be populated after experiments are executed.

---

## Independent Variables

| Variable | Values | Controlled By | Experiment |
|----------|--------|---------------|------------|
| Synchronization interval (Δt_sync) | 0, 15, 30, 60, 120, 300, 600, 900, 1800 s | `configs/synchronization.yaml` | E5 |
| Synchronization age (age_sync) | Derived from Δt_sync | Synchronization engine | E5, E6 |
| Missed-update condition | Controlled (yes/no, rate) | `configs/synchronization.yaml` | E7 |
| Detector type | Isolation Forest, LSTM Autoencoder | `configs/anomaly_detection.yaml` | E3, E4, E5 |
| Input representation | Raw, Residual | `configs/anomaly_detection.yaml` | E4, E5 |
| Forecasting model | Persistence, XGBoost, LSTM | `configs/forecasting.yaml` | E2, E5 |
| Anomaly condition | Absent (normal), Present (injected) | `configs/data.yaml` | E3, E5, E7 |

---

## Dependent Variables

### Load Estimation Metrics

| Metric | Definition | Unit | Primary? |
|--------|-----------|------|----------|
| MAE | Mean Absolute Error | kW | Yes |
| RMSE | Root Mean Square Error | kW | Yes |
| MAPE | Mean Absolute Percentage Error | % | Yes |
| R² | Coefficient of determination | — | Secondary |

### Anomaly Detection Metrics

| Metric | Definition | Primary? |
|--------|-----------|----------|
| Precision | TP / (TP + FP) | Yes |
| Recall | TP / (TP + FN) | Yes |
| F1 | Harmonic mean of Precision and Recall | Yes |
| PR-AUC | Area under Precision-Recall curve | Yes |
| ROC-AUC | Area under ROC curve | Secondary |
| FPR | False Positive Rate: FP / (FP + TN) | Secondary |
| Detection Latency | Timesteps from anomaly onset to first detection | Secondary |

### Digital Twin State Metrics

| Metric | Definition | Unit |
|--------|-----------|------|
| State error | ||x_physical - x_dt||₂ | pu |
| Residual magnitude | ||physical - DT_prediction||₂ | kW |
| Synchronization age | t_physical - t_last_sync | s |
| AoI | t_reception - t_generation | s |
| Solver latency | OpenDSS power flow execution time | ms |

---

## E5 Staleness Sweep Design Matrix

The primary experiment. Each cell represents one experimental condition.

### Load Estimation Sub-matrix

| Δt_sync (s) | Persistence MAPE | XGBoost MAPE | LSTM MAPE | Persistence RMSE | XGBoost RMSE | LSTM RMSE |
|-------------|------------------|--------------|-----------|-----------------|--------------|-----------|
| 0 (perfect) | — | — | — | — | — | — |
| 15 | — | — | — | — | — | — |
| 30 | — | — | — | — | — | — |
| 60 | — | — | — | — | — | — |
| 120 | — | — | — | — | — | — |
| 300 | — | — | — | — | — | — |
| 600 | — | — | — | — | — | — |
| 900 | — | — | — | — | — | — |
| 1800 | — | — | — | — | — | — |

> Results will be filled in after E5 is executed. "—" indicates not yet measured.

### Anomaly Detection Sub-matrix

| Δt_sync (s) | IF+Raw F1 | IF+Res F1 | LSTMAE+Raw F1 | LSTMAE+Res F1 | IF+Raw PR-AUC | IF+Res PR-AUC | LSTMAE+Raw PR-AUC | LSTMAE+Res PR-AUC |
|-------------|-----------|-----------|---------------|---------------|--------------|--------------|------------------|------------------|
| 0 (perfect) | — | — | — | — | — | — | — | — |
| 15 | — | — | — | — | — | — | — | — |
| 30 | — | — | — | — | — | — | — | — |
| 60 | — | — | — | — | — | — | — | — |
| 120 | — | — | — | — | — | — | — | — |
| 300 | — | — | — | — | — | — | — | — |
| 600 | — | — | — | — | — | — | — | — |
| 900 | — | — | — | — | — | — | — | — |
| 1800 | — | — | — | — | — | — | — | — |

> Results will be filled in after E5 is executed. "—" indicates not yet measured.

---

## E4 Raw vs. Residual Design Matrix (under perfect synchronization)

| Condition | Detector | Input | F1 | PR-AUC | ROC-AUC | FPR |
|-----------|----------|-------|----|--------|---------|-----|
| E4-1 | IF | Raw | — | — | — | — |
| E4-2 | IF | Residual | — | — | — | — |
| E4-3 | LSTMAE | Raw | — | — | — | — |
| E4-4 | LSTMAE | Residual | — | — | — | — |

---

## E2 Baseline Load Estimation Matrix

| Model | MAE (kW) | RMSE (kW) | MAPE (%) | R² |
|-------|---------|----------|----------|----|
| Persistence | — | — | — | — |
| XGBoost | — | — | — | — |
| LSTM | — | — | — | — |

---

## Hypothesis Assessment Matrix

To be completed after E5 and E6.

| Hypothesis | Prediction | Assessment | Evidence |
|------------|------------|------------|----------|
| H3: Anomaly detection degrades faster than load estimation | F1 degradation slope > MAPE degradation slope | *Not yet assessed* | *E5/E6 pending* |
| H4: Residual inputs outperform raw inputs | IF+Res F1 > IF+Raw F1; LSTMAE+Res F1 > LSTMAE+Raw F1 | *Not yet assessed* | *E4/E5 pending* |
| H5: Missed updates cause transient spikes | Post-miss degradation > steady-state degradation at same interval | *Not yet assessed* | *E7 pending* |

---

## Random Seed Policy

| Experiment | Default Seed | Additional Seeds (for statistical validation) |
|------------|-------------|-----------------------------------------------|
| E2 | 42 | 123, 456, 789 (Phase 10) |
| E3 | 42 | 123, 456, 789 (Phase 10) |
| E4 | 42 | 123, 456, 789 (Phase 10) |
| E5 | 42 | 123, 456, 789 (Phase 10) |
| E6 | — (analysis) | — |
| E7 | 42 | 123, 456, 789 (Phase 10) |

> [!CAUTION]
> Never change the primary seed (42) after any experiment has been run.
> Additional seeds for statistical validation must be pre-registered before running.

---

*Experiment matrix v1.0.0 — Phase 0.*
*Results will be added as experiments are executed.*