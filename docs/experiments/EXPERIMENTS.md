# Experiments

> **Project:** Digital Twin Power Grid — Synchronization Staleness Study
> **Version:** 1.0.0 — September 2026
> **Status:** Experiment definitions — none yet executed

> [!IMPORTANT]
> This document defines the experiments to be conducted. No experiment has been run yet.
> Results, metrics, and figures will be added as experiments are completed.
> Do NOT add results, estimates, or projected values to this document before experiments are run.

---

## Experiment Overview

| ID | Name | Phase | Status | Addresses |
|----|------|-------|--------|-----------|
| E1 | Digital Twin Baseline Validation | 3 | Not started | DT correctness |
| E2 | Load Estimation Baselines | 5 | Not started | Baseline load estimation |
| E3 | Anomaly Detection Baselines | 6 | Not started | Baseline anomaly detection |
| E4 | Raw vs. Residual Inputs | 7 | Not started | Input representation comparison |
| E5 | Synchronization Staleness Sweep | 8 | Not started | **RQ1 (primary)** |
| E6 | Degradation Profile Analysis | 9 | Not started | Degradation shape, H3 assessment |
| E7 | Missed-Update Transient Analysis | 11 | Not started | Transient effects |

---

## E1 — Digital Twin Baseline Validation

### Objective

Validate that the OpenDSS-based Digital Twin for the IEEE 33-bus feeder produces physically correct power flow results. Establish the virtual baseline against which physical states are compared.

### Research Role

Prerequisite for all subsequent experiments. If the DT does not correctly simulate the physical system, downstream results are invalid.

### Validation Criteria

- Bus voltage magnitudes within [0.90, 1.10] pu for all 33 buses
- Power balance: |P_generation - P_load - P_losses| < 0.5%
- Voltage profile consistent with published IEEE 33-bus reference values
- Solver convergence for all tested load conditions
- DT state serializable and reproducible

### Method

1. Initialize IEEE 33-bus OpenDSS model with reference parameters
2. Apply nominal load profile
3. Run power flow solver
4. Verify voltage, current, and power values against reference
5. Test under multiple load conditions (light, nominal, heavy)

### Inputs

- IEEE 33-bus topology definition
- Reference load parameters
- `configs/digital_twin.yaml`

### Expected Outputs

```
experiments/runs/E1_DT_VALIDATION_SEED42_<YYYYMMDD>/
├── manifest.json
├── results/
│   ├── voltage_profile.csv
│   ├── power_flow.csv
│   └── solver_stats.json
├── plots/
│   └── voltage_profile.png
└── summary.md
```

### Status

```
Status: Not started
Phase: 3
Blocked by: Phase 2 (data pipeline)
```

---

## E2 — Load Estimation Baselines

### Objective

Establish baseline load estimation performance for all three models under perfect synchronization (zero staleness). These baselines serve as the reference against which staleness-induced degradation is measured in E5.

### Research Role

Baseline establishment. Not a research contribution in itself — these are established methods used as experimental tools.

### Models

| Model | Role | Expected MAPE Range (literature) |
|-------|------|----------------------------------|
| Persistence | Lowest-complexity baseline | Higher than ML models |
| XGBoost | Nonlinear baseline | ~4–5% (Moon et al., 2022) |
| LSTM | Primary temporal model | ~3–4% (Kong et al., 2019) |

> [!NOTE]
> Expected ranges are from the literature review, not guaranteed on this dataset.
> Actual performance will be reported after E2 is executed.

### Metrics

**Primary:** MAE, RMSE, MAPE
**Secondary:** R² (if scientifically justified)

### Method

1. Train each model on training split (perfect synchronization, interval = 0)
2. Validate on validation split for hyperparameter selection
3. Evaluate on test split (one evaluation only — no test set tuning)
4. Report metrics with fixed seed

### Expected Outputs

```
experiments/runs/E2_BASELINE_PERSISTENCE_RAW_SEED42_<YYYYMMDD>/
experiments/runs/E2_BASELINE_XGBOOST_RAW_SEED42_<YYYYMMDD>/
experiments/runs/E2_BASELINE_LSTM_RAW_SEED42_<YYYYMMDD>/
```

### Status

```
Status: Not started
Phase: 5
Blocked by: Phase 4 (synchronization engine)
```

---

## E3 — Anomaly Detection Baselines

### Objective

Establish baseline anomaly detection performance for both detectors under perfect synchronization. Test the 2×2 design (detector × input representation) at zero staleness.

### Research Role

Baseline establishment and raw-vs-residual comparison under perfect synchronization.

### Detectors

| Detector | Input | Condition |
|----------|-------|----------|
| Isolation Forest | Raw | Baseline |
| Isolation Forest | Residual | Baseline |
| LSTM Autoencoder | Raw | Baseline |
| LSTM Autoencoder | Residual | Baseline |

> [!IMPORTANT]
> All detectors are trained WITHOUT anomaly labels (unsupervised).
> Anomaly labels are used ONLY for evaluation metric computation.

### Metrics

**Primary:** Precision, Recall, F1, PR-AUC
**Secondary:** ROC-AUC, FPR, Detection Latency

### Method

1. Train detectors on training split (normal data only, no anomalies in training)
2. Select threshold on validation split
3. Evaluate on test split (one evaluation only)
4. Report all four 2×2 conditions

### Expected Outputs

```
experiments/runs/E3_BASELINE_IF_RAW_SEED42_<YYYYMMDD>/
experiments/runs/E3_BASELINE_IF_RESIDUAL_SEED42_<YYYYMMDD>/
experiments/runs/E3_BASELINE_LSTMAE_RAW_SEED42_<YYYYMMDD>/
experiments/runs/E3_BASELINE_LSTMAE_RESIDUAL_SEED42_<YYYYMMDD>/
```

### Status

```
Status: Not started
Phase: 6
Blocked by: Phase 4 (synchronization engine) + Phase 7 (residual engine)
```

---

## E4 — Raw vs. Residual Inputs

### Objective

Systematically compare raw DT state features vs. physical-DT residuals as inputs to anomaly detectors under perfect synchronization.

### Research Role

Investigates whether residual features provide better anomaly detection than raw features (secondary contribution). Provides the input-representation baseline for the staleness sweep (E5).

### Design

```
                    Detector
              IF              LSTM-AE
Raw     [E4-1] IF+Raw    [E4-3] LSTMAE+Raw
Residual [E4-2] IF+Res   [E4-4] LSTMAE+Res
```

### Analysis

- Compare F1 and PR-AUC across the 2×2 design
- Identify whether residual features improve detection under perfect sync
- Establish the baseline for E5's raw-vs-residual comparison under staleness

### Status

```
Status: Not started
Phase: 7
Note: Largely completed as part of E3 under perfect synchronization
```

---

## E5 — Synchronization Staleness Sweep

### Objective

The **primary experiment**. Systematically vary the synchronization interval and measure the effect on both load estimation and anomaly detection performance.

### Research Role

Addresses **RQ1 directly**. The synchronization interval is the independent variable. This is the core research contribution.

### Independent Variable

**Synchronization interval** (Δt_sync) in seconds:
`[0, 15, 30, 60, 120, 300, 600, 900, 1800]`

> [!IMPORTANT]
> The sweep intervals are defined in `configs/synchronization.yaml` under `sweep_intervals_seconds`.
> Do not change these values without creating an ADR and re-running all affected experiments.

### Conditions (Full Design)

For each synchronization interval:

| Load Model | Detector | Input | Condition ID |
|------------|----------|-------|--------------|
| Persistence | — | Raw | E5-L0-P-R |
| XGBoost | — | Raw | E5-L0-X-R |
| LSTM | — | Raw | E5-L0-L-R |
| — | IF | Raw | E5-L0-IF-R |
| — | IF | Residual | E5-L0-IF-Res |
| — | LSTMAE | Raw | E5-L0-LSTMAE-R |
| — | LSTMAE | Residual | E5-L0-LSTMAE-Res |

(Repeated for each of the 9 interval levels)

### Synchronization Log

Every run records (per `docs/architecture/SYNCHRONIZATION_ENGINE.md`):
- physical_timestamp, dt_timestamp, last_sync_timestamp
- sync_age_seconds, aoi_seconds
- update_interval_seconds, missed_updates_count
- solver_time_ms, inference_time_ms
- residual_magnitude

### Expected Outputs

```
experiments/runs/E5_STALENESS_IF_RAW_SEED42_<DATE>/      (one per interval level)
experiments/runs/E5_STALENESS_IF_RESIDUAL_SEED42_<DATE>/
experiments/runs/E5_STALENESS_LSTMAE_RAW_SEED42_<DATE>/
experiments/runs/E5_STALENESS_LSTMAE_RESIDUAL_SEED42_<DATE>/
experiments/runs/E5_STALENESS_PERSISTENCE_RAW_SEED42_<DATE>/
experiments/runs/E5_STALENESS_XGBOOST_RAW_SEED42_<DATE>/
experiments/runs/E5_STALENESS_LSTM_RAW_SEED42_<DATE>/
```

### Status

```
Status: Not started
Phase: 8
Blocked by: Phases 5, 6, 7
```

---

## E6 — Degradation Profile Analysis

### Objective

Analyze the shape of the degradation curve for both tasks as synchronization staleness increases. Assess Hypothesis H3.

### Research Role

Secondary analysis of E5 results. Characterizes whether degradation is linear, nonlinear, threshold-based, or regime-dependent.

### H3 Assessment

> **H3 [HYPOTHESIS]:** Anomaly detection will exhibit a steeper degradation profile than load estimation as synchronization staleness increases.

E6 will explicitly assess H3 as: **Supported / Contradicted / Inconclusive**

> [!IMPORTANT]
> If H3 is contradicted by the experimental results, it will be reported accurately.
> A contradicted hypothesis is scientifically valuable and will be presented as such.

### Degradation Metrics

- Load estimation: MAPE vs. staleness interval (primary)
- Anomaly detection: F1 vs. staleness interval (primary); PR-AUC vs. staleness (secondary)
- DT state error: State divergence vs. staleness interval
- Relative sensitivity: (ΔF1 / F1_baseline) vs. (ΔMAPE / MAPE_baseline)

### Status

```
Status: Not started
Phase: 9
Blocked by: Phase 8 (E5 completion)
```

---

## E7 — Missed-Update Transient Analysis

### Objective

Study what happens in the time window immediately following a missed synchronization event. Quantify the transient growth of DT error, residuals, and ML performance degradation.

### Research Role

Extends the staleness analysis to non-steady-state conditions. Missed updates cause abrupt rather than gradual staleness accumulation.

### Method

1. Simulate controlled missed-update events (configured probability or schedule)
2. Measure, per timestep after missed update:
   - DT state error
   - Residual magnitude growth
   - Load estimation error
   - Anomaly score
   - Detector performance
3. Compare transient vs. steady-state staleness profiles

### Status

```
Status: Not started
Phase: 11
Blocked by: Phase 8 (E5 completion)
```

---

*Experiment definitions v1.0.0 — Phase 0.*
*Results will be added as experiments are completed.*
*No results are fabricated or estimated here.*