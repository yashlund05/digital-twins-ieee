# ADR-0003: Definition and Computation of Physical-Virtual Residuals

> **Status:** Revised (Awaiting Approval)  
> **Date:** 2026-09-29  
> **Deciders:** Research Lead, Integration Lead, Synchronization Engineer, Anomaly Detection Engineer  
> **Consulted:** Entire Team  
> **Informed:** All Contributors  

---

## 1. Context and Problem Statement

In Phase 7 (Residual Engine), we implement the physical-virtual residual computation subsystem to support the 2×2 factorial experiment design:
$$\{\text{Isolation Forest (IF)}, \text{LSTM-Autoencoder (LSTMAE)}\} \times \{\text{Raw Telemetry}, \text{Physical-Virtual Residuals}\}$$
under baseline synchronization (Experiment E4) and controlled staleness sweeps (Experiment E5).

A naive definition of residuals as $r(t) = y_{\text{phys}}(t) - y_{\text{DT}}(t)$ where the Digital Twin (DT) simply mirrors incoming telemetry fails completely: at perfect synchronization ($\Delta t_{\text{sync}} = 0$), the residual would be identically zero even when an anomaly occurs, hiding the fault. Conversely, treating the DT as an ungrounded black-box estimator decouples the residual from physical network synchronization.

This ADR establishes the rigorous mathematical and architectural definitions for:
1. Anomaly contamination handling across telemetry and synchronization boundaries.
2. The unified physical-virtual staleness and predictive observer model.
3. Feature alignment across Raw and Residual representations (including voltages).
4. Forecaster selection and out-of-fold training-split residual computation.
5. Strict freezing protocols for Experiment E5 staleness sweeps.
6. Hypothesis formulation and formal verification test definitions.

---

## 2. Core Decisions and System Specification

### 2.1 Anomaly Contamination and Propagation

**Architecture of Telemetry and Physical Injection:**
1. Ground-truth anomalous perturbations (load spikes, voltage sags, phase imbalances) are injected **strictly into the physical distribution feeder load profiles** ($P_{\text{phys}}(t), Q_{\text{phys}}(t)$) and propagated to physical power-flow state ($V_{\text{phys}}(t)$).
2. At every discrete time step $t$, the physical feeder state is sampled as telemetry $y_{\text{phys}}(t)$.
3. **Synchronization Interface:** If a synchronization event occurs at time $t$ ($t = k \cdot \Delta t_{\text{sync}}$), the telemetry packet sent across the communication network contains the physical measurement $y_{\text{phys}}(t)$ (including any active perturbation).
4. **DT Ingestion and Contamination Guard:**
   - The primary purpose of the DT in this architecture is to model the **nominal expected grid state**.
   - If an anomalous packet is synchronized into the DT at time $t$, naive autoregressive forecasters could ingest the corrupted load into their history window (lags $t-1, \dots, t-K$), thereby biasing the subsequent forecast $\hat{y}_{\text{DT}}(t+1)$ toward the anomaly and artificially reducing multi-step residuals ($r(t+1) \to 0$).
   - **Contamination Protocol:**
     - To prevent anomaly self-cancellation over multi-step fault events (configured as 4 steps / 1 hour in `configs/data.yaml`), the DT's load estimator uses a **filtered / clipped state update** or a **calendar-anchored forecast model**.
     - Specifically, the forecaster generates the conditional nominal expectation:
       $$\hat{P}_{\text{load}}(t) = f_{\text{primary\_forecaster}}\left(\mathbf{x}_{\text{context}}(t)\right)$$
       where $\mathbf{x}_{\text{context}}(t)$ relies on diurnal calendar cyclical features (hour, day of week, seasonal harmonics) and synchronized baselines. When state updates exceed physical operational limits (e.g. rate-of-change $\Delta P / \Delta t > \tau_{\text{ROC}}$), the DT maintains its robust nominal tracking estimate rather than absorbing the fault as a new steady state.

---

### 2.2 Unified Staleness and DT Predictive Observer Model

We reconcile synchronization timing into **one unified discrete-time staleness model**:

1. **Discrete Simulation Grid:** All physical telemetry is sampled at discrete 15-minute intervals ($T_s = 900\,\text{s}$):
   $$t \in \{0, 1, 2, \dots, N-1\}$$
2. **Synchronization Interval ($k$ steps):**
   Synchronization occurs every $k \ge 1$ timesteps ($k \in \{1, 2, 4, 8, \dots\}$, corresponding to intervals $\Delta t_{\text{sync}} = k \cdot T_s$).
   - **Baseline Synchronization:** Defined as $k = 1$ ($\Delta t_{\text{sync}} = 15\,\text{min}$, interval parameter 0 in idealized sweeps). At $k = 1$, synchronization is received every timestep without packet delay or loss.
   - **Staleness Levels ($k > 1$):** Synchronization packets arrive only at times $t_s = m \cdot k$ ($m \in \mathbb{N}$).
3. **DT State Prediction Formulation:**
   At any time $t$, let $t_{\text{last\_sync}} \le t$ be the timestamp of the most recent synchronization packet. The discrete staleness age is:
   $$\tau(t) = t - t_{\text{last\_sync}} \in \{0, 1, \dots, k-1\}$$
   The DT prediction $\hat{y}_{\text{DT}}(t) = [\hat{P}_{\text{DT}}(t), \hat{Q}_{\text{DT}}(t), \hat{V}_{\text{DT}}(t)]$ is generated as follows:
   - **Primary Forecast Component:** The primary forecaster predicts nominal active and reactive bus load expectations $\hat{P}_{\text{load}}(t)$ based on conditions synchronized at $t_{\text{last\_sync}}$ projected forward by $\tau(t)$ steps:
     $$\hat{P}_{\text{load}}(t) = f_{\text{forecaster}}\left(y_{\text{sync}}(t_{\text{last\_sync}}), \tau(t), \text{calendar}(t)\right)$$
   - **Power Flow Resolution:** The OpenDSS engine evaluates the AC power flow with loads $[\hat{P}_{\text{load}}(t), \hat{Q}_{\text{load}}(t)]$ to yield the virtual system voltages:
     $$\hat{V}_{\text{DT}}(t) = \text{OpenDSS}\left(\hat{P}_{\text{load}}(t), \hat{Q}_{\text{load}}(t)\right)$$
4. **Baseline Case ($k = 1, \tau(t) = 0$):**
   The DT receives the state from $t-1$, updates its autoregressive state, and forecasts the expected nominal load for step $t$.
   Because the forecaster predicts the smooth diurnal expectation, an abrupt physical anomaly at time $t$ ($P_{\text{phys}}(t) = 3.0 \times P_{\text{nominal}}(t)$) diverges starkly from $\hat{P}_{\text{DT}}(t)$, producing a large non-zero residual.
5. **Staleness Case ($k > 1, \tau(t) > 0$):**
   As $\tau(t)$ grows, the prediction $\hat{y}_{\text{DT}}(t)$ degrades due to compound forecasting error and hold-policy drift, injecting staleness noise into the residual $r(t)$.

---

### 2.3 Feature Space Alignment (Load and Voltage)

To prevent representation disparity between Raw and Residual modes, both feature spaces must include the exact same electrical quantities:

1. **Physical Quantities Monitored across all 32 load buses ($b \in \{2, \dots, 33\}$):**
   - Active power $P_b(t)$ (kW) — 32 features
   - Reactive power $Q_b(t)$ (kVAR) — 32 features
   - Voltage magnitude $V_b(t)$ (pu) — 32 features
2. **Total Dimensionality:**
   $$D = 32\,(P) + 32\,(Q) + 32\,(V) = 96\text{ continuous features}$$
3. **Exact Feature Vector Definitions:**
   - **Raw Telemetry Mode ($D = 96$):**
     $$\mathbf{x}_{\text{raw}}(t) = \left[P_{\text{phys}, 2..33}(t),\, Q_{\text{phys}, 2..33}(t),\, V_{\text{phys}, 2..33}(t)\right]$$
     *(Note: In Experiment E3, raw mode used $D = 64$ ($P$ and $Q$). For exact backward equivalence in Experiment E4, E4 will evaluate both the 64-feature parity set $[P, Q]$ and the 96-feature full electrical set $[P, Q, V]$, ensuring direct comparisons to E3).*
   - **Residual Telemetry Mode ($D = 96$, or $D = 64$ for direct E3 comparison):**
     $$\mathbf{r}_P(t) = P_{\text{phys}}(t) - \hat{P}_{\text{DT}}(t)$$
     $$\mathbf{r}_Q(t) = Q_{\text{phys}}(t) - \hat{Q}_{\text{DT}}(t)$$
     $$\mathbf{r}_V(t) = V_{\text{phys}}(t) - \hat{V}_{\text{DT}}(t)$$
     $$\mathbf{x}_{\text{residual}}(t) = \left[\tilde{\mathbf{r}}_P(t),\, \tilde{\mathbf{r}}_Q(t),\, \tilde{\mathbf{r}}_V(t)\right]$$
     where $\tilde{\mathbf{r}}$ denotes partition-normalized residuals.

---

### 2.4 Primary Forecaster Selection and Out-of-Fold Training Residuals

1. **Primary Forecaster:**
   - **XGBoost** is selected as the primary DT load forecaster for Phase 7 residuals.
   - *Rationale:* Deterministic, fast execution, strong non-linear tracking of diurnal calendar and lag interactions, low validation error (RMSE 0.537 kW, MAPE 3.99% on E2).
   - **Persistence Baseline:** Maintained strictly as an ablation / sensitivity benchmark model.
2. **Out-of-Fold (Rolling-Origin) Residuals on the Training Split:**
   - *Leakage / Overfitting Hazard:* If the forecaster evaluates predictions on the exact training samples it fitted, in-sample residuals $r_{\text{train}}$ will be artificially near-zero and overfitted. If the anomaly detector or normalizer fits on these artificially tight in-sample residuals, it will suffer extreme false alarm rates when evaluated on out-of-sample validation/test residuals.
   - *Resolution:* Residuals on the training partition ($t \in \text{train\_indices}$) **MUST be generated using rolling-origin out-of-fold cross-validation**:
     - Partition the training split into $K = 5$ contiguous chronological folds: $F_1, F_2, F_3, F_4, F_5$.
     - For fold $m \in \{2, \dots, K\}$: train XGBoost on folds $F_1 \dots F_{m-1}$ and predict residuals on fold $F_m$.
     - For fold $F_1$: fit on an initial warm-up fraction (e.g. first 50% of $F_1$) to predict the second half, or initialize via robust calendar prior.
   - This ensures all training-split residuals used to fit the residual normalizer are strictly **out-of-fold / out-of-sample**.

---

### 2.5 Strict Normalizer and Detector Freezing for Experiment E5

To isolate synchronization staleness as an independent variable:
1. **Calibration at Baseline Synchronization ($k = 1$):**
   - The residual normalizer (RobustScaler / StandardScaler) is fitted **strictly on the out-of-fold training split residuals** at baseline sync ($k = 1$).
   - Both anomaly detectors (Isolation Forest, LSTM-Autoencoder) are trained **strictly on normalized training residuals** at baseline sync ($k = 1$).
   - The anomaly decision threshold $\theta^*$ is calibrated **strictly on validation split normalized residuals** at baseline sync ($k = 1$).
2. **Frozen Evaluation Across Staleness Sweep ($k \in \{1, 2, 4, 8, \dots\}$):**
   - The normalizer parameters, trained detector model weights, and decision threshold $\theta^*$ are **completely frozen**.
   - As staleness increases, incoming test telemetry is subtracted from stale DT predictions, normalized using the frozen normalizer, and scored by the frozen detectors using $\theta^*$.
   - *Ablation Variant:* A secondary ablation experiment may evaluate "detector retrained under staleness", but the primary research protocol freezes the baseline-calibrated detectors.

---

### 2.6 Scientific Positioning: Hypothesis Formulation

The claim that residuals outperform raw telemetry is explicitly defined as a **falsifiable scientific hypothesis**, not a presumed fact:

> **Hypothesis H1:** *Under baseline synchronization ($k = 1$), an unsupervised anomaly detector trained on normalized physical-virtual residuals $\mathbf{x}_{\text{residual}}$ achieves higher anomaly detection F1 score and lower false positive rate (FPR) than the identical detector architecture trained on raw telemetry $\mathbf{x}_{\text{raw}}$, because subtraction of nominal model predictions attenuates diurnal cyclic variance.*
>
> **Hypothesis H2:** *As synchronization staleness $\Delta t_{\text{sync}}$ increases, the performance of residual-based detectors degrades faster than raw-telemetry detectors, because stale DT predictions introduce state drift noise into the residual vector.*

If experimental results contradict H1 or H2, the empirical findings will be reported faithfully without post-hoc cherry-picking.

---

### 2.7 Verification Testing Protocol

We replace the naive "$r \approx 0$" assertion with two rigorous physical verification tests:

1. **Oracle-DT Sanity Test (`test_oracle_dt_residual_zero`):**
   - When the DT is provided the exact ground-truth unperturbed physical load ($P_{\text{DT}} \equiv P_{\text{phys\_clean}}$), the resulting power flow solution satisfies:
     $$\|P_{\text{phys}} - P_{\text{DT}}\|_2 < 10^{-6} \text{ kW}, \quad \|V_{\text{phys}} - V_{\text{DT}}\|_2 < 10^{-6} \text{ pu}$$
   - Confirms exact mathematical and OpenDSS convergence parity between physical and virtual solver instances.

2. **Residual Signal-to-Noise Ratio (SNR) Test (`test_residual_snr_anomaly_contrast`):**
   - Evaluate the mean residual norm under nominal operating conditions versus anomaly injection conditions:
     $$\text{SNR}_{\text{residual}} = \frac{\mathbb{E}_{t \in \text{anomalies}}\left[\|\mathbf{r}(t)\|_2\right]}{\mathbb{E}_{t \in \text{nominal}}\left[\|\mathbf{r}(t)\|_2\right]}$$
   - **Pass Criterion:** Under baseline synchronization ($k = 1$), $\text{SNR}_{\text{residual}} \ge 5.0$ across all three fault types (load spike, voltage sag, phase imbalance). This verifies that anomalies stand out distinctly above background forecasting noise.

---

## 3. Implementation Deliverables (Phase 7)

Upon user approval of this revised ADR:
1. `src/residuals/calculator.py`: `ResidualCalculator` implementing out-of-fold predictions, OpenDSS voltage evaluation, and vector differencing.
2. `src/residuals/normalizer.py`: `ResidualNormalizer` fitted strictly on train out-of-fold residuals, saved to `data/processed/residual_normalization_params.json`.
3. `src/residuals/features.py`: `ResidualFeatureExtractor` providing $D=64$ and $D=96$ tabular and 3D sequence tensors for IF and LSTMAE.
4. `src/residuals/experiment_e4.py`: 2×2 factorial evaluation script (`run_experiment_e4()`) and CLI command `train-residual`.
5. Tests in `tests/unit/test_residual_calculator.py`, `tests/unit/test_residual_features.py`, and `tests/integration/test_residual_pipeline.py`.
