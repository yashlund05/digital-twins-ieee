# Phase 7 — Digital Twin Residual Engine & Experiment E4 Specification

> **Module:** `src/residuals/`  
> **Status:** Phase 7 Implementation Complete  
> **Target:** IEEE Transactions on Smart Grid / Power Systems Journal  
> **Date:** September 2026  

---

## 1. Scientific Motivation & Research Objective

In smart grid Digital Twin (DT) literature, monitoring and anomaly detection frequently rely on physical-vs-virtual state residuals:
$$
r_t = y_t - \hat{y}^{DT}_t
$$
where $y_t$ represents physical feeder telemetry and $\hat{y}^{DT}_t$ represents the physics-based Digital Twin state estimate.

While residual-based monitoring has been demonstrated in isolated settings (e.g., transformer diagnostics, PV plants), prior scholarship routinely assumes zero-latency, continuous synchronization. In realistic distribution systems, communication latency, telemetry sampling, packet drops, and desynchronization introduce **synchronization staleness** (Age of Information - AoI).

Phase 7 establishes the **Residual Engine** and the **baseline Experiment E4** under ideal baseline synchronization ($\Delta t = 0$), comparing Raw vs. Residual representations across two core unsupervised detector architectures in a **2×2 factorial design**:

```
                    Isolation Forest       LSTM Autoencoder
Raw                      E4-1                    E4-3
Residual                 E4-2                    E4-4
```

This isolates the representational effect under ideal baseline conditions before controlled staleness sweeps ($\Delta t \in \{1s, 5s, 15s, 60s, 300s\}$) are introduced in Phase 8 (Experiment E5).

---

## 2. Mathematical Definition & Immutability

### 2.1 Pure Raw Residual Definition
For any aligned physical observation $y_t \in \mathbb{R}^D$ and synchronized Digital Twin estimate $\hat{y}^{DT}_t \in \mathbb{R}^D$:
$$
r_t = y_t - \hat{y}^{DT}_t
$$
computed element-wise across all feeder telemetry quantities (active load $P_i$, reactive load $Q_i$, or full 104-d grid state vectors).

### 2.2 Raw Residual Immutability Principle
The raw residual is a scientific primitive and must remain strictly immutable. Inside `src/residuals/calculator.py`:
- No hidden normalization or standardization
- No arbitrary clipping or thresholding
- No smoothing, filtering, or denoising
- No outlier removal or winsorization

All transformations occur downstream through explicit, configurable components:
```
Observed y_t + DT Estimate ŷ_DT,t
                 ↓
      calculator.py (Raw Residual r_t)
                 ↓
      normalizer.py (Train-Fitted Normalization)
                 ↓
      features.py (Configured Feature Extraction)
                 ↓
      Anomaly Detector (IF / LSTM-AE)
```

---

## 3. Subsystem Architecture

### 3.1 `src/residuals/calculator.py`
* **`calculate_residual(observed, dt_estimate, ...)`**:
  * Rigorously validates shape compatibility, non-empty arrays, numeric types, and checks for NaNs/Infs.
  * Rejects silent broadcasting and mismatched time indices.
  * Preserves metadata: `physical_timestamp`, `dt_sync_timestamp`, `aoi_seconds`, and feature identities.
  * Returns `ResidualResult`.
* **`calculate_state_residual(physical_state, dt_state)`**:
  * Specialized extractor operating on `DigitalTwinState` instances from `src.digital_twin.state`.
  * Computes full 104-d state vector difference, per-bus voltage errors (pu and kV), phase angle differences (deg), branch current errors (A), and system power residuals (kW, kVAR).

### 3.2 `src/residuals/normalizer.py`
* **`ResidualNormalizer`**:
  * Implements `fit`, `transform`, `fit_transform`, and `inverse_transform` following Scikit-learn conventions.
  * Supported methods:
    * `z_score`: Standardization $z = \frac{x - \mu}{\sigma + \epsilon}$
    * `min_max`: Range scaling $z = \frac{x - x_{\min}}{(x_{\max} - x_{\min}) + \epsilon}$
    * `robust`: Median and IQR scaling $z = \frac{x - \text{median}}{\text{IQR} + \epsilon}$
  * **Strict Zero-Leakage Guarantee:** `fit()` operates strictly on the training partition ($0 \dots 24527$). Validation and test partitions NEVER influence scaler statistics.
  * Full JSON serialization: `save()` and `load()`.

### 3.3 `src/residuals/features.py`
* **`ResidualFeatureExtractor`**:
  * Deterministic feature extraction governed by `ResidualFeatureConfig`:
    1. Direct residual: $r_t$
    2. Absolute residual: $|r_t|$
    3. Squared residual: $r_t^2$
    4. Spatial L2 norm magnitude: $||r_t||_2$
    5. Spatial Mean absolute residual: $\frac{1}{N}\sum_i |r_{t,i}|$
    6. Spatial Max absolute residual: $\max_i |r_{t,i}|$
    7. Causal temporal lag residuals: $r_{t-k}$ for configured backward lags $k > 0$.
  * **Causality Guarantee:** Features at timestep $t$ depend solely on observations $\le t$. No centered windows or future interpolation.

### 3.4 `src/residuals/experiment_e4.py`
* Orchestrates the 2×2 factorial design:
  * **E4-1:** Raw + Isolation Forest
  * **E4-2:** Residual + Isolation Forest
  * **E4-3:** Raw + LSTM Autoencoder
  * **E4-4:** Residual + LSTM Autoencoder
* Evaluates all four conditions under identical experimental budgets, seeds (`42`), and splits.
* Persists full paper-ready artifacts in `experiments/runs/E4_RAW_VS_RESIDUAL_SEED{seed}_{date}/`.

---

## 4. Leakage Prevention Protocol

| Safeguard | Implementation Mechanism | Validation Verification |
|---|---|---|
| **Temporal / Future Leakage** | Causal backward lags ($t-k$) only. Lag array initialized to zero for $t < k$. No centered rolling windows. | `test_causality_and_future_leakage_audit`: altering future rows leaves current features unchanged. |
| **Normalization Leakage** | `ResidualNormalizer.fit()` called strictly on `train_rows`. | `test_normalization_leakage_audit`: inserting $10^6$ into test set does not alter fitted mean/std. |
| **Label Leakage** | Detectors fitted strictly unsupervised without anomaly labels. | Verified: detectors accept only $X$, never $y$. Labels used exclusively in `compute_anomaly_metrics()`. |
| **Threshold Leakage** | Decision threshold calibrated on validation split scores (95th percentile). | Frozen threshold applied directly to test split scores without test label feedback. |
| **Split Leakage** | Strict chronological boundaries: Jan 1–Sep 13 (train), Sep 13–Nov 7 (val), Nov 7–Dec 31 (test). | $\max(\text{train}) < \min(\text{val}) < \min(\text{test})$ verified in `test_splitter.py`. |

---

## 5. Artifact Directory Specification

Each completed E4 run generates:
```
experiments/runs/E4_RAW_VS_RESIDUAL_SEED{seed}_{date}/
├── comparison.csv          # Machine-readable tabular summary across all 4 conditions
├── feature_config.json     # Configuration parameters for residual feature extraction
├── manifest.json           # Complete reproducibility manifest (git commit, seed, environment)
├── metrics.json            # Hierarchical metrics (val and test) for all 4 conditions
├── predictions.parquet     # Test set ground truth, anomaly scores, and predictions
├── raw_residuals.parquet   # Full raw residual matrix for auditability
├── residual_normalizer.json# Fitted normalizer parameters (mean, std, min, max, etc.)
├── summary.md              # Human-readable markdown executive summary
└── models/                 # Serialized weights and calibrated thresholds for all detectors
    ├── E4-1_isolation_forest_raw/
    ├── E4-2_isolation_forest_residual/
    ├── E4-3_lstm_autoencoder_raw/
    └── E4-4_lstm_autoencoder_residual/
```
