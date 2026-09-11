# System Architecture

> **Project:** Digital Twin of Power Grid for Load Estimation and Anomaly Prediction
> **Version:** 1.0.0 — September 2026
> **Status:** Architecture specification (Phase 0) — not yet implemented

---

## Overview

This document defines the intended architecture for the Digital Twin synchronization staleness experimental system. The architecture is designed to support:

1. Controlled introduction of synchronization staleness as an experimental variable
2. Joint evaluation of load estimation and anomaly detection under identical conditions
3. Raw vs. residual input comparison
4. Full experiment reproducibility

> [!IMPORTANT]
> The individual components (LSTM, XGBoost, Isolation Forest, LSTM Autoencoder, OpenDSS) are established technologies. The architectural contribution is the experimental framework that introduces synchronization staleness as a controlled variable.

---

## System Data Flow

```
Physical / Synthetic Grid State
        (IEEE 33-bus + Pecan Street profiles)
                    |
                    v
         Data Acquisition Layer
            (src/data/)
                    |
                    v
     Synchronization Engine  <--- Configurable Interval
         (src/synchronization/)     Staleness Control
                    |                AoI Tracking
                    |                Missed Update Detection
                    |
          [Staleness Applied Here]
                    |
                    v
         Digital Twin State
            (src/digital_twin/)
                    |
                    v
           OpenDSS Solver
         (IEEE 33-bus power flow)
                    |
          +---------+---------+
          |                   |
          v                   v
   Load Estimation       Residual Engine
   (src/forecasting/)    (src/residuals/)
          |                   |
          v                   v
   Forecasting         Anomaly Detection
   - Persistence       (src/anomaly_detection/)
   - XGBoost           - Isolation Forest
   - LSTM              - LSTM Autoencoder
                             |
                    +--------+--------+
                    |                 |
                    v                 v
               Raw Input        Residual Input
               (2x2 Design: raw x IF, raw x LSTM-AE,
                             residual x IF, residual x LSTM-AE)
                    |                 |
                    +---------+-------+
                              |
                              v
                    Evaluation Engine
                    (src/evaluation/)
                              |
                              v
                  Statistical Analysis
                    (src/statistics/)
                              |
                              v
                     Paper Artifacts
                     (artifacts/)
```

---

## Module Responsibilities

### src/data/

**Responsibility:** Data ingestion, preprocessing, mapping, and splitting.

**Key functions:**
- Load raw Pecan Street data
- Map load profiles to IEEE 33-bus nodes
- Apply normalization and feature engineering
- Generate train/validation/test splits (temporal, no leakage)
- Inject synthetic anomalies per protocol

**Critical constraint:** This module produces the **hybrid simulation dataset**. It must never describe its output as real field measurements of the IEEE feeder.

**Does NOT contain:** Synchronization logic, ML model code.

---

### src/digital_twin/

**Responsibility:** Virtual representation of the IEEE 33-bus distribution feeder.

**Key functions:**
- Load IEEE 33-bus topology
- Initialize and run OpenDSS power flow solver
- Maintain DT state (voltages, currents, power flows)
- Expose DT state to synchronization and residual engines

**Critical constraint:** The DT state is updated ONLY through the synchronization engine. This module does not control when updates occur.

**Does NOT contain:** Synchronization scheduling, ML model code, metric computation.

---

### src/synchronization/

**Responsibility:** The most research-critical component. Controls the independent variable.

**Key functions:**
- Schedule DT state updates at configurable intervals
- Detect and handle missed updates
- Compute Age of Information (AoI)
- Track synchronization age (physical_time - last_sync_time)
- Log all synchronization events

**Critical constraint:** This is the ONLY module that implements synchronization logic. All other modules receive synchronization state via the engine's output, not by implementing their own timing.

**Configurable parameters (from configs/synchronization.yaml):**
- `interval_seconds`: The experimental independent variable
- `missed_update_policy`: What happens when an update is missed

---

### src/forecasting/

**Responsibility:** Short-term load estimation models.

**Key functions:**
- Implement Persistence, XGBoost, and LSTM models
- Train models on historical load data
- Generate predictions for each synchronization interval condition
- Feature engineering for tabular models

**Critical constraint:** Receives synchronization age as a potential feature, but does NOT implement synchronization logic itself.

---

### src/anomaly_detection/

**Responsibility:** Unsupervised anomaly detection.

**Key functions:**
- Implement Isolation Forest and LSTM Autoencoder
- Train in unsupervised mode (no labels used in training)
- Generate anomaly scores
- Apply threshold for binary classification

**Critical constraint:** Training must not use anomaly labels. Labels are for evaluation only.

---

### src/residuals/

**Responsibility:** Compute physical-vs-virtual residuals.

**Key functions:**
- Compute residual = physical_measurement - dt_prediction
- Normalize residuals
- Extract residual features for anomaly detectors

**Critical constraint:** Residuals are computed from the DT state, which is affected by synchronization staleness. Stale DT state produces stale residuals — this is the mechanism under investigation.

---

### src/evaluation/

**Responsibility:** Stateless metric computation.

**Key functions:**
- Load estimation metrics: MAE, RMSE, MAPE, R²
- Anomaly detection metrics: Precision, Recall, F1, PR-AUC, ROC-AUC, FPR, Detection Latency
- DT state metrics: State error, residual magnitude
- Synchronization metrics: AoI, sync age, missed update rate

**Design principle:** Pure functions where possible. No state. No side effects.

---

### src/statistics/

**Responsibility:** Statistical analysis of experimental results.

**Key functions:**
- Bootstrap confidence intervals
- Effect size estimation
- Performance vs. staleness regression
- Task sensitivity comparison (H3 assessment)

**Protocol:** See `docs/methodology/STATISTICAL_PROTOCOL.md`.

---

### src/experiments/

**Responsibility:** Experiment orchestration.

**Key functions:**
- Load and validate experiment configuration
- Generate unique run IDs
- Orchestrate the full experiment pipeline
- Write manifests, metrics, logs
- Ensure no run overwrites another

---

### src/cli/

**Responsibility:** CLI entry points.

**Design principle:** Thin wrappers only. No business logic in CLI. Every CLI command calls `src/experiments/` or module-level functions.

---

## Key Design Decisions

### Decision 1: Single Synchronization Abstraction

All synchronization logic lives in `src/synchronization/`. No other module implements timing or staleness calculation.

**Rationale:** The synchronization engine is the independent variable. Scattering synchronization logic would make it impossible to ensure that the experimental variable is cleanly controlled.

**ADR:** See `docs/decisions/ADR-0002-platform-selection.md`

### Decision 2: Configuration-Driven Experiments

All experimental parameters are in YAML configuration files. No hard-coded values.

**Rationale:** Reproducibility. An experiment must be fully reproducible from its configuration file, git commit, and random seed.

### Decision 3: Hybrid Simulation Dataset

Pecan Street load profiles are mapped to IEEE 33-bus nodes, producing a hybrid simulation dataset.

**Rationale:** The IEEE 33-bus feeder has no associated public field measurement dataset. Pecan Street provides real consumption patterns that can be realistically mapped.

**Critical limitation:** This is not field validation. Results are qualified to the hybrid simulation context.

**Data protocol:** See `docs/methodology/DATA_PROTOCOL.md`.

### Decision 4: Unsupervised Anomaly Detection

Both anomaly detectors are trained without anomaly labels.

**Rationale:** Unsupervised detection is the more realistic operational assumption and aligns with the literature (Liu et al., 2023; Gholami et al., 2022).

### Decision 5: 2×2 Experiment Design

Four conditions: (IF, LSTM-AE) × (raw, residual).

**Rationale:** Enables systematic comparison of detector type and input representation under identical synchronization conditions.

---

## Module Dependency Graph

```
data  →  digital_twin
      ↘
         synchronization  →  forecasting
         ↓                    ↓
         ↓                  evaluation
         ↓                    ↑
         digital_twin  →  residuals  →  anomaly_detection
                                              ↓
                                         evaluation
                                              ↓
                                         statistics
                                              ↓
                                         visualization
```

All modules depend on `utils`. `cli` depends on `experiments`, which depends on all pipeline modules.

---

## Experiment-Architecture Mapping

| Experiment | Primary Modules | Research Role |
|------------|----------------|---------------|
| E1 | digital_twin, evaluation | Validate DT correctness |
| E2 | data, forecasting, evaluation | Establish load estimation baselines |
| E3 | data, anomaly_detection, evaluation | Establish anomaly detection baselines |
| E4 | residuals, anomaly_detection, evaluation | Compare raw vs. residual inputs |
| E5 | synchronization, all | Core staleness sweep (primary research) |
| E6 | statistics, visualization | Degradation profile analysis |
| E7 | synchronization, all | Missed-update transient analysis |

---

*Architecture version 1.0.0 — established in Phase 0.*
*Updates require an ADR and team review.*
