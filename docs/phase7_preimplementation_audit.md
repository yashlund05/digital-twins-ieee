# Phase 7 Pre-Implementation Audit — Residual Engine & Experiment E4

> **Document:** `docs/phase7_preimplementation_audit.md`  
> **Status:** Pre-Implementation Architectural & Interface Audit  
> **Target:** Phase 7 (Residual Engine + Experiment E4)  
> **Date:** September 2026  
> **Author:** Power Systems ML Research Team  

---

## 1. Executive Summary

This audit establishes the rigorous baseline for **Phase 7: Residual Engine + Experiment E4**, ensuring strict backward compatibility with completed Phases 0–6, mathematical consistency, zero data leakage, and alignment with the master research questions:

* **RQ1:** How does Digital Twin synchronization staleness affect short-term load estimation and unsupervised anomaly detection?
* **H3:** Anomaly detection exhibits a steeper degradation profile than load forecasting as synchronization staleness increases.
* **H4:** Physics-based residual representations ($r_t = y_t - \hat{y}_{\text{DT}, t}$) outperform raw telemetry inputs under baseline synchronization conditions.

Phase 7 implements the **2×2 factorial baseline (Experiment E4)** under ideal baseline synchronization before controlled staleness is introduced in Phase 8 (Experiment E5).

---

## 2. Core Questions & Ground-Truth System Representations

Before defining interfaces, we explicitly resolve the core representation questions against the existing codebase:

| Question | Exact Codebase Representation | Source Location | Description & Dimensions |
|---|---|---|---|
| **Physical observation $y_t$** | Nodal active/reactive power telemetry: `df_feats[elec_cols]` where `elec_cols` = `bus_{2..33}_p_kw` (32) + `bus_{2..33}_q_kvar` (32). Or full feeder state `vec_phys = physical_state.to_feature_vector()` (104). | `src/anomaly_detection/trainer.py`<br>`src/digital_twin/state.py` | 64 continuous nodal load quantities (kW, kVAR) at time $t$ (or 104-d grid state: 33 voltages pu, 33 angles deg, 32 currents A, 6 system powers). |
| **Digital Twin estimate $\hat{y}_{\text{DT}, t}$** | The virtual twin's active state estimate corresponding to the synchronized state available at time $t$: $\hat{y}_{\text{DT}, t}$. In baseline E4, this is the DT's nominal physical state/profile before anomaly deviation, or the synchronized twin estimate from `SynchronizationEngine.step()`. | `src/digital_twin/state.py`<br>`src/synchronization/engine.py` | Exactly matching dimension and feature identity of $y_t$ (64 load features or 104 state features). |
| **Synchronization timestamp** | `last_sync_timestamp`: Floating-point epoch seconds (or ISO-8601 UTC string) recording when the last successful physical update was received into the DT. | `src/synchronization/engine.py`<br>`src/synchronization/logger.py` | `SyncLogRecord.last_sync_timestamp` and `SyncResult.sync_age_seconds`. |
| **Physical timestamp** | `physical_timestamp`: DatetimeIndex of the physical sample (UTC ISO-8601 string, e.g. `2018-01-01T00:15:00+00:00`) or epoch seconds $t$. | `src/data/pipeline.py`<br>`src/synchronization/engine.py` | Preserved on Pandas DataFrame indices and `DigitalTwinState.timestamp`. |
| **Age of Information (AoI)** | $\Delta(t) = t_{\text{reception}} - t_{\text{generation}}$. Managed centrally by `AoITracker`. In discrete simulation, $\text{AoI} = t_{\text{physical}} - t_{\text{last\_sync}}$. | `src/synchronization/aoi.py`<br>`src/synchronization/engine.py` | Floating-point seconds. Peak AoI, average AoI, and instantaneous AoI recorded in `SyncLogRecord`. |
| **Bus/load feature** | Specific electrical column: `bus_{id}_p_kw` (active load kW) and `bus_{id}_q_kvar` (reactive load kVAR) for buses $id \in \{2, \dots, 33\}$. | `src/data/mapper.py`<br>`src/data/schema.py` | Exact string names preserved across all transforms and residual outputs. |
| **Anomaly label** | Binary indicator: `is_anomaly \in {0, 1}` stored separately with event metadata (`anomaly_type`, `affected_buses`, `event_id`). | `src/data/anomaly_injector.py`<br>`data/processed/anomaly_labels.parquet` | Strictly isolated from model training; used exclusively for evaluation metrics. |
| **Train/val/test split** | Strict chronological partition: `train` (70%, steps 0..24527), `val` (15%, steps 24528..29783), `test` (15%, steps 29784..35039). | `src/data/splitter.py`<br>`data/processed/splits.json` | Leak-free verified: $\max(\text{train}) < \min(\text{val}) < \min(\text{test})$. |

---

## 3. Detailed Audit of Existing Subsystems

### 3.1 Existing Data Flow
```
Raw / Synthetic Benchmark Traces (25 homes, 365 days, 15-min)
                 ↓
      Data Cleaning & Resampling
                 ↓
      IEEE 33-Bus Node Mapping (32 load buses: P_kW, Q_kVAR)
                 ↓
      Synthetic Anomaly Injection (5% rate, 4-step duration)
                 ↓
      Temporal Splitting (70% Train, 15% Val, 15% Test)
                 ↓
      Training-Only Min-Max Normalization
                 ↓
      data/processed/load_profiles.parquet (Features)
      data/processed/anomaly_labels.parquet (Labels)
      data/processed/splits.json (Partition indices)
```

### 3.2 Existing Physical Observation Representation
* In `data/processed/load_profiles.parquet`:
  * Index: DatetimeIndex (15-minute resolution, 35,040 rows for 365 days).
  * 64 continuous nodal electrical columns: `bus_{i}_p_kw` and `bus_{i}_q_kvar` for $i \in [2, 33]$.
  * Additional engineered features (temporal harmonics, lag features) present in parquet but separated by column filters in model trainers.
* In `src/digital_twin/solver.py`:
  * `DigitalTwinSolver.solve_timestep_from_dataframe(row)` takes row with 64 P/Q columns and solves AC power flow on the IEEE 33-bus circuit.
  * Produces `DigitalTwinState`.

### 3.3 Existing Digital Twin State Representation
* `DigitalTwinState` (`src/digital_twin/state.py`):
  * `timestamp: str | None` (ISO 8601 UTC)
  * `converged: bool`, `iterations: int`
  * `bus_voltages_pu: dict[int, float]` (buses 1..33)
  * `bus_voltages_kv: dict[int, float]` (buses 1..33)
  * `bus_voltage_angles_deg: dict[int, float]` (buses 1..33)
  * `branch_currents_a: dict[str, float]` (lines L1..L32)
  * `total_generation_p_kw`, `total_generation_q_kvar`, `total_load_p_kw`, `total_load_q_kvar`, `total_losses_p_kw`, `total_losses_q_kvar`
  * `to_feature_vector()`: 1D NumPy `float64` array of shape `(104,)`.

### 3.4 Existing Synchronization Metadata & AoI Representation
* `SynchronizationEngine` (`src/synchronization/engine.py`):
  * Governed by `SynchronizationConfig` (`configs/synchronization.yaml`).
  * `scheduler`: `UpdateScheduler` (checks intervals and stochastic packet drops).
  * `aoi_tracker`: `AoITracker` (tracks instantaneous AoI, peak AoI, time-average AoI).
  * `policy`: `MissedUpdatePolicy` (default `hold_last_state`).
  * `divergence_tracker`: `StateDivergenceTracker` (computes L2 norm divergence and per-quantity errors).
  * `event_logger`: `SyncEventLogger` (produces `SyncLogRecord`).

### 3.5 Existing Anomaly Detection Input Format
* `AnomalyDetectionTrainer` (`src/anomaly_detection/trainer.py`):
  * Loads `data/processed/load_profiles.parquet` and selects `elec_cols` (64 continuous P/Q features).
  * Partitions rows by `splits["train_indices"]`, `splits["validation_indices"]`, `splits["test_indices"]`.
  * Models:
    * `IsolationForestDetector` (`src/anomaly_detection/isolation_forest.py`): accepts 2D array `(N, D)` where $D=64$.
    * `LSTMAutoencoderDetector` (`src/anomaly_detection/lstm_autoencoder.py`): generates rolling 3D sequences `(N - lookback + 1, lookback, D)` where `lookback=24`.
  * Threshold Selection (`src/anomaly_detection/thresholds.py`):
    * Configured by `configs/anomaly_detection.yaml` (percentile = 95.0).
    * Evaluated strictly on validation scores (`th_selector.fit(val_scores)`).
  * Test split evaluated with fixed threshold.

### 3.6 Existing Train/Validation/Test Boundaries
* File: `data/processed/splits.json`
  * `train_indices`: $[0, \dots, 24527]$ (24,528 steps, 70%, Jan 1 – Sep 13)
  * `validation_indices`: $[24528, \dots, 29783]$ (5,256 steps, 15%, Sep 13 – Nov 7)
  * `test_indices`: $[29784, \dots, 35039]$ (5,256 steps, 15%, Nov 7 – Dec 31)
* Zero temporal leakage enforced: $\max(\text{train}) < \min(\text{val}) < \min(\text{test})$.

### 3.7 Existing Random Seed Mechanism
* Utilities: `src/utils/reproducibility.py`:
  * `set_all_seeds(seed)` locks Python `random`, `numpy.random`, `torch.manual_seed`, and sets `torch.use_deterministic_algorithms(True)`.
  * Frozen master seeds: `[42, 123, 456, 789, 101112]`. Default seed: `42`.

### 3.8 Existing Evaluation Metrics
* `src/evaluation/anomaly_metrics.py`:
  * `compute_anomaly_metrics(y_true, y_pred, scores, event_ids)`:
    * Primary: `precision`, `recall`, `f1`, `pr_auc`
    * Secondary: `roc_auc`, `false_positive_rate`, `detection_latency`
  * Pure functions, robust to division-by-zero, handles edge cases (e.g. single-class arrays return 0.0 or nan gracefully).

### 3.9 Existing Experiment Runner Conventions
* Experiment E1: `src/digital_twin/initializer.py:run_experiment_e1_validation()`
* Experiment E2: `src/forecasting/experiment_e2.py:run_experiment_e2()`
* Experiment E3: `src/anomaly_detection/experiment_e3.py:run_experiment_e3()`
* Standard output structure in `experiments/runs/<RUN_ID>/`:
  * `models/` — serialized weights and thresholds
  * `manifest.json` — reproducibility metadata
  * `metrics.json` — multi-split metrics summary
  * `comparison.csv` — tabular overview
  * `summary.md` — human-readable markdown report
  * `predictions.parquet` — test predictions and scores

---

## 4. Phase 7 Integration Architecture

```
Physical Telemetry / Injected Load y(t)         Digital Twin State / Estimate ŷ_DT(t)
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        ↓
                         src/residuals/calculator.py
                                 r(t) = y(t) - ŷ_DT(t)
                                 (Raw residual immutability)
                                        ↓
                         src/residuals/normalizer.py
                                 (Train-only fitting, zero leakage)
                                        ↓
                         src/residuals/features.py
                                 (Direct, Abs, Sq, L2, Causal Lags)
                                        ↓
                       src/residuals/experiment_e4.py
                         (2×2 Design: [IF, LSTMAE] × [Raw, Residual])
                                        ↓
                    experiments/runs/E4_RAW_VS_RESIDUAL_*
```

### 4.1 Integration Points

1. **`src/residuals/calculator.py`**:
   * Pure functional and object-oriented residual calculation:
     `calculate_residual(observed, dt_estimate, ...)`
   * Direct DataFrame / NumPy element-wise difference: $r(t) = y(t) - \hat{y}_{\text{DT}}(t)$.
   * Input validation: shape compatibility, feature alignment, timestamp alignment, check for non-numeric/NaN/Inf.
   * Metadata preservation: `physical_timestamp`, `dt_sync_timestamp`, `aoi_seconds`, `feature_names`.
   * Raw residual immutability: No hidden clipping, smoothing, or standardization.

2. **`src/residuals/normalizer.py`**:
   * `ResidualNormalizer`: Scikit-learn style `fit`, `transform`, `fit_transform`.
   * Supported methods: `z_score`, `min_max`, `robust`.
   * **Zero Leakage**: Scaler parameters (`mean`, `std`, `min`, `max`, `median`, `iqr`) computed **strictly** on the training partition (`train_indices`). Test and validation samples NEVER influence normalization parameters.
   * Full serialization: `to_dict()`, `from_dict()`, `save()`, `load()`.

3. **`src/residuals/features.py`**:
   * `ResidualFeatureExtractor`:
     * Direct residual $r_t$
     * Absolute residual $|r_t|$
     * Squared residual $r_t^2$
     * L2 norm residual vector magnitude $||r_t||_2$
     * Mean absolute residual $\frac{1}{N}\sum |r_{t,i}|$
     * Max absolute residual $\max_i |r_{t,i}|$
     * Causal temporal features: strictly backward-looking lag residuals $r_{t-k}$ (no future leakage, no centered windows).
   * Configurable feature selection via dictionary / config.

4. **`src/residuals/experiment_e4.py`**:
   * Orchestrates the 2×2 factorial design:
     * Condition 1: Raw + Isolation Forest
     * Condition 2: Raw + LSTM Autoencoder
     * Condition 3: Residual + Isolation Forest
     * Condition 4: Residual + LSTM Autoencoder
   * Uses identical hyperparameters, random seeds (`42`), training splits, and threshold calibration protocols (validation 95th percentile).
   * Generates `manifest.json`, `metrics.json`, `comparison.csv`, `summary.md`, `predictions.parquet`.

5. **`src/cli/main.py`**:
   * Expose `run-e4` command: `python -m src.cli run-e4 --seed 42`.

---

## 5. Pre-Implementation Leakage Safeguards

| Leakage Risk | Preventative Mechanism | Verification Test |
|---|---|---|
| **Scaler / Normalization Leakage** | `ResidualNormalizer.fit()` called strictly on `X_res[train_indices]`. `transform()` applied to val and test. | `test_normalizer_zero_leakage`: assert test values do not shift training mean/std. |
| **Temporal / Future Leakage** | Feature extractor rolling windows use only past timesteps ($t, t-1, \dots$). No centered rolling windows. | `test_features_causality`: assert modifying future row $t+1$ does not alter features at $t$. |
| **Label Leakage** | Detectors and normalizers never receive `anomaly_labels`. Labels used only in `compute_anomaly_metrics()`. | `test_unsupervised_label_isolation`: assert fitting runs without labels. |
| **Split Boundary Leakage** | Enforce $\max(\text{train}) < \min(\text{val}) < \min(\text{test})$ on all residual feature rows. | `test_split_temporal_integrity`: verify split indices strictly increasing. |
| **DT State Leakage** | The DT estimate at physical time $t$ uses strictly $t_{\text{sync}} \le t$. | `test_dt_state_causality`: verify DT timestamp never exceeds physical timestamp. |

---

## 6. Audit Sign-Off

The existing repository architecture is fully understood, verified by passing all 105 existing tests. We are ready to proceed with the implementation plan for Phase 7.
