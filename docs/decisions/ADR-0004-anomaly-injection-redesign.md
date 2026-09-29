# ADR-0004: Redesign of Synthetic Anomaly Injection and Detector Input Pipeline

> **Status:** Proposed (Pending Review)  
> **Date:** 2026-09-29  
> **Deciders:** Research Lead, Integration Lead, Anomaly Detection Engineer, Data Engineer, DT Engineer  
> **Consulted:** Entire Team  
> **Informed:** All Contributors  

---

## 1. Context and Problem Statement

A rigorous empirical audit of the Phase 2 data pipeline and Phase 6 anomaly detection baselines revealed several critical architectural and physical deficiencies:

1. **Anomaly Injection Coupling with Normalization:**
   - In `src/data/pipeline.py`, anomalies were injected on unnormalized kW/kVAR data. However, the resulting series was subsequently min-max normalized where negative values occurred because Pecan Street "grid" telemetry represents net exchange with the grid (including rooftop solar export), not gross household consumption.
   - Applying arbitrary multipliers ($2.5\times$ to $4.0\times$ or $0.2\times$ to $0.5\times$) on net-grid values that fluctuate around zero or negative values distorts the physical meaning of load spikes and drops.
2. **Nomenclature Inaccuracy (`voltage_sag`):**
   - The injector labeled a sudden drop in customer active load ($0.2\times$ to $0.5\times$) as `voltage_sag`.
   - In actual power systems, dropping downstream load causes local bus voltages to *rise* (reducing voltage drop $\Delta V = I R + X Q$), directly contradicting the name `voltage_sag`.
3. **Severe Telemetry Scale Disconnect in OpenDSS:**
   - `load_profiles.parquet` contains normalized values ($0.0 \sim 1.0$, mean $\approx 0.3$).
   - When `DigitalTwinSolver.solve_timestep_from_dataframe()` reads `row["bus_{id}_p_kw"]`, it reads the normalized float ($\sim 0.3$) directly without denormalizing back to physical kW. As a result, the feeder load solved by OpenDSS was $\sim 11.6$ kW instead of the nominal $3{,}715.0$ kW benchmark load, artificially inflating voltages to near 1.0000 pu.
4. **Sequence Dimension Collapse in LSTM Autoencoder:**
   - `configs/anomaly_detection.yaml` specifies `lookback_steps: 24`, yet `src/anomaly_detection/trainer.py` passed a 2D matrix $(N, 64)$ into `LSTMAutoencoderDetector.score_samples()`.
   - `_prepare_tensor()` expanded $(N, 64)$ to $(N, 1, 64)$, discarding temporal sequence modeling completely.
5. **Undefined Severity Tiers:**
   - All anomalies had uniform durations and overlapping multiplier ranges without discrete severity stratification (low, medium, high), preventing granular detection sensitivity analysis.

---

## 2. Architectural Decisions

### 2.1 Injection in Physical Units on Gross Consumption (Non-Negative Load)

1. **Source Channel Definition:**
   - The data pipeline shall load gross residential consumption (`use`) or enforce non-negative net load:
     $$P_{\text{gross}}(t) = \max(0.01, P_{\text{raw}}(t))$$
     ensuring that all bus loads represent true physical consumption in physical kW before mapping and injection.
2. **Pre-Normalization Physical Injection:**
   - All synthetic perturbations are applied **strictly in physical units (kW and kVAR)** on the unnormalized feeder loads.
   - Normalization (if applied for downstream tabular models) occurs **after** physical injection and mapping, preserving physical consistency.
3. **OpenDSS Ingestion Integrity:**
   - OpenDSS solvers must always receive **unnormalized physical loads (kW, kVAR)**. Processed telemetry files will store explicitly named unnormalized physical columns (`bus_{id}_p_kw_physical`) alongside normalized features, or maintain separate unnormalized physical telemetry stores.

---

### 2.2 Relative Magnitude Formulation with Absolute Noise Floor

To ensure that low-load buses receive physically meaningful anomalies without producing undetectable micro-perturbations:
1. **Diurnal Base Reference:**
   - For each bus $b \in \{2, \dots, 33\}$, compute the expected nominal load on the training partition:
     $$\bar{P}_{\text{train}}(b, h, w) = \mathbb{E}_{t \in \text{train}}\left[P_b(t) \mid \text{hour}(t) = h,\, \text{is\_weekend}(t) = w\right]$$
2. **Injected Perturbation Formula:**
   $$\Delta P_b(t) = \max\left(M_{\text{relative}} \cdot \bar{P}_{\text{train}}(b, h, w),\, \Delta P_{\text{floor}}\right)$$
   where $\Delta P_{\text{floor}} = 10.0\,\text{kW}$ is an absolute minimum injection threshold ensuring that anomalies are never lost in baseline sensor quantization noise.

---

### 2.3 Three Discrete Severity Tiers (Calibrated in Residual / Train $\sigma$)

All injected events are categorized into three standardized, discrete severity levels calibrated in units of each bus's training-set standard deviation $\sigma_{\text{train}, b}$ (calculated strictly on the training partition before injection):

| Severity Tier | Load Spike ($\Delta P$) | Load Drop ($\Delta P$) | Phase Imbalance ($\Delta P$) | Target Evaluation Role |
|---|---|---|---|---|
| **Low** | $+2.0\,\sigma_{\text{train}, b}$ | $-1.5\,\sigma_{\text{train}, b}$ | Primary: $+2.0\,\sigma$, Others: $-1.0\,\sigma$ | Sub-threshold sensitivity / detection boundary |
| **Medium** | $+3.5\,\sigma_{\text{train}, b}$ | $-2.5\,\sigma_{\text{train}, b}$ | Primary: $+3.5\,\sigma$, Others: $-1.5\,\sigma$ | Operational fault threshold |
| **High** | $+5.0\,\sigma_{\text{train}, b}$ | $-3.5\,\sigma_{\text{train}, b}$ | Primary: $+5.0\,\sigma$, Others: $-2.0\,\sigma$ | Gross failure / immediate trip condition |

- **Floor Constraint:** For `load_drop`, loads are clipped at a physical non-negative floor ($\ge 0.05\,\text{kW}$) to maintain physical validity without reverse power flow distortion.
- **Label Metadata Enhancement:** `data/processed/anomaly_labels.parquet` records `severity` (`low`, `medium`, `high`), `target_buses`, `realized_ratio_kw`, and `effect_size_sigma` for every event.
- **Evaluation Strictness:** Severity tiers and detection thresholds are calibrated and evaluated **strictly on the validation split**; test split labels are reserved exclusively for final locked evaluation.

---

### 2.4 Scaler Formulation: Pre-Injection Train Fitting

- Normalization parameters (and/or RobustScaler statistics) are fitted **strictly on the unperturbed pre-injection training split** (`active_df.iloc[:train_limit]`).
- This guarantees zero synthetic contamination in the normalization baseline and ensures that anomalies exhibit true outlier geometry in the transformed feature space.

---

### 2.5 Heavy Tail and Feeder Voltage Finding (Step 1b Analysis)

- **Full-Horizon Convergence:** The DT solver achieved **100.0000% convergence across all 35,040 timesteps** of the full year.
- **Voltage Drop & Extreme Tail:**
  - $V_{\min}$ reaches $0.6416\,\text{pu}$ during extreme peak coincidences ($P_{\text{tot}} = 17{,}946\,\text{kW}$, where 19/32 buses exceed $3\times$ nominal rating due to 2-home Pecan Street aggregation scaling up to $226\times$).
  - $32.04\%$ of timesteps exhibit $V_{\min} < 0.90\,\text{pu}$, and $75.00\%$ exhibit $V_{\min} < 0.95\,\text{pu}$.
  - *Design implication:* While OpenDSS converges unconditionally, the high coincidence of two scaled residential homes per bus causes heavy tails. The limitation ("two households per bus, scaled") is documented in `docs/methodology/DATA_PROTOCOL.md` and `README.md`.

---

### 2.6 Nomenclature Correction: Renaming `voltage_sag` to `load_drop`

1. **Renaming:**
   - The anomaly type previously named `voltage_sag` is formally renamed to **`load_drop`**.
   - *Justification:* Scaling customer bus power downwards is a demand-side loss of load (e.g. feeder trip, major breaker opening, load shedding). Calling a power drop a "voltage sag" violates standard power systems terminology (IEEE 1159).
2. **True Voltage Sag Modeling:**
   - Real voltage sags occur from distribution network faults (e.g. single line-to-ground faults). When physical OpenDSS simulation is coupled with the residual engine (Phase 7), voltage sags will be reflected in nodal voltage telemetry $V_{\text{phys}}(t) \ll 0.90\,\text{pu}$, while `load_drop` represents active power curtailment.

---

### 2.7 Sequence Tensor Rectification for LSTM-Autoencoder

1. **Sliding Window Generation:**
   - `src/anomaly_detection/trainer.py` must convert tabular arrays into genuine 3D temporal sliding windows:
     $$\mathbf{X}_{\text{seq}} \in \mathbb{R}^{N \times W \times D}, \quad W = \text{lookback\_steps} = 24, \quad D = 64$$
   - Each window $i$ covers timesteps $[t - W + 1, \dots, t]$.
2. **Explicit Label Alignment Rule:**
   - The reconstruction error of sequence window $[t - W + 1, \dots, t]$ is mapped **strictly to the label at the final timestep $t$**:
     $$\text{score}(t) = \frac{1}{W \cdot D} \sum_{\tau=0}^{W-1} \sum_{d=1}^D \left(x_{t - W + 1 + \tau, d} - \hat{x}_{t - W + 1 + \tau, d}\right)^2 \iff y(t)$$
3. **Automated Assertion Unit Test:**
   - A dedicated test `test_lstm_autoencoder_window_shape()` will assert that the tensor entering the neural network has `shape[1] == 24`.

---

### 2.8 Artifact Regeneration Protocol

The following pipeline artifacts must be regenerated from scratch on a clean git commit before proceeding to Phase 7:
1. `data/processed/load_profiles.parquet` (regenerated with gross/non-negative loads and clear unnormalized physical columns).
2. `data/processed/anomaly_labels.parquet` (regenerated with `severity`, `realized_ratio_kw`, `effect_size_sigma`, and `load_drop` types).
3. `data/processed/splits.json` and `data/interim/normalization_params.json`.
4. Rerun **Experiment E3** from a clean git branch `feature/phase-6-anomaly-redesign` to establish true, valid baselines for both detectors.

---

## 3. Status

- **Accepted and Implemented in Branch `fix/phase2-3-units-and-injection`**
