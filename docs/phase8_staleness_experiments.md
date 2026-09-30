# Phase 8 — Controlled Synchronization Staleness & Experiment E5

## Research-Grade Specification and Experimental Documentation

> **Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin**  
> *Target Publication Level: IEEE Transactions on Smart Grid*

---

## 1. Executive Summary & Research Motivation

Phase 8 introduces **controlled synchronization staleness** ($\Delta t$) and **stochastic packet drops** ($P_{\text{drop}}$) into the physical-digital co-simulation loop of the IEEE 33-bus distribution feeder Digital Twin.

In real-world cyber-physical power distribution systems, physical metering infrastructure (e.g., smart meters, micro-PMUs, SCADA RTUs) communicates with the Digital Twin over bandwidth-constrained, jitter-prone, and lossy communication networks. While existing literature frequently presumes idealized, continuous real-time state mirroring ($\Delta t \to 0$), operational Digital Twins inevitably operate under delayed and stale state updates.

The core objective of Phase 8 is to quantify the causal degradation chain:
$$\Delta t \quad \xrightarrow{\quad} \quad \text{Digital Twin State Error } e^{DT}_t(\Delta t) \quad \xrightarrow{\quad} \quad \text{Residual Distortion } r_t(\Delta t) \quad \xrightarrow{\quad} \quad \begin{cases} \text{Load Estimation Degradation } (\Delta \text{MAPE}, \Delta \text{RMSE}) \\ \text{Anomaly Detection Degradation } (\Delta F_1, \Delta \text{AUC-ROC}, \Delta \text{AUC-PR}) \end{cases}$$

---

## 2. Mathematical Formulation

### 2.1 Synchronization Schedule and Age of Information (AoI)
Let physical time be discretized at sampling interval $T_s = 1\,\text{s}$ over horizon $t \in \{0, 1, \dots, T\}$. A scheduled synchronization event occurs at regular intervals:
$$t_k = k \cdot \Delta t, \quad k \in \mathbb{N}_0, \quad \Delta t \in \{0, 1, 5, 15, 60, 300\}\,\text{s}$$

Communication reliability across the cyber interface is modeled via independent Bernoulli packet arrivals:
$$B_k \sim \text{Bernoulli}(1 - P_{\text{drop}}), \quad P_{\text{drop}} \in \{0.0, 0.05, 0.10, 0.20\}$$

The effective received update sequence timestamp is:
$$t_{\text{last\_rx}}(t) = \max \left\{ t_j \le t \;\middle|\; B_j = 1 \right\}$$

The instantaneous Age of Information (AoI) $\Delta_{\text{AoI}}(t)$ is defined as:
$$\Delta_{\text{AoI}}(t) = t - t_{\text{last\_rx}}(t) \ge 0$$
Under an update arrival ($t = t_k$ and $B_k = 1$), $\Delta_{\text{AoI}}(t)$ resets to the transmission delay (0 in instantaneous arrival); in intervals between arrivals, $\Delta_{\text{AoI}}(t)$ grows with unit slope $\frac{d\Delta_{\text{AoI}}}{dt} = 1$.

### 2.2 Digital Twin Stale State Reconstruction (Hold-Last-State Policy)
Under the Zero-Order Hold / Hold-Last-State policy $\Pi_{\text{HLS}}$, the Digital Twin power-flow state estimate at time $t$ reflects the most recently received physical measurement:
$$\hat{y}^{DT}_{t | t_{\text{sync}}} = y^{DT}\left( t_{\text{last\_rx}}(t) \right)$$

### 2.3 Stale Residual Computation
The physical measurement at time $t$ is $y_t$. Under synchronization staleness $\Delta t$, the state residual vector $r_t(\Delta t)$ is formulated as:
$$r_t(\Delta t) = y_t - \hat{y}^{DT}_{t | t_{\text{sync}}} = y_t - y^{DT}\left( t_{\text{last\_rx}}(t) \right)$$

Decomposing $y_t$ into baseline state $y^{base}_t$ and anomaly perturbation $a_t$:
$$r_t(\Delta t) = a_t + \underbrace{\left[ y^{base}_t - y^{DT}(t) \right]}_{\approx 0 \text{ (ideal residual)}} + \underbrace{\left[ y^{DT}(t) - y^{DT}(t_{\text{last\_rx}}(t)) \right]}_{\text{staleness-induced drift } \epsilon_{\text{stale}}(t)}$$
As $\Delta_{\text{AoI}}(t)$ increases, the drift term $\epsilon_{\text{stale}}(t)$ inflates the background noise floor, degrading anomaly separability and distorting temporal feature representations.

---

## 3. Experimental Design Matrix (24 Conditions)

Experiment E5 executes a rigorous $6 \times 4$ full-factorial sweep:

| Staleness Interval $\Delta t$ | Packet Drop Rate $P_{\text{drop}}$ | Condition ID |
|---|---|---|
| **0 s** (Continuous baseline) | 0.00, 0.05, 0.10, 0.20 | C01, C02, C03, C04 |
| **1 s** (High-rate telemetry) | 0.00, 0.05, 0.10, 0.20 | C05, C06, C07, C08 |
| **5 s** (Fast sub-cycle polling)| 0.00, 0.05, 0.10, 0.20 | C09, C10, C11, C12 |
| **15 s** (SCADA-rate polling) | 0.00, 0.05, 0.10, 0.20 | C13, C14, C15, C16 |
| **60 s** (1-minute AMI interval) | 0.00, 0.05, 0.10, 0.20 | C17, C18, C19, C20 |
| **300 s** (5-minute AMI batch) | 0.00, 0.05, 0.10, 0.20 | C21, C22, C23, C24 |

### Downstream Evaluation Tasks:
1. **Load Estimation (3 models)**:
   - Persistence Predictor ($\hat{y}_{t+1} = y_{t}$)
   - Gradient Boosted Trees (XGBoost)
   - Long Short-Term Memory Network (PyTorch LSTM)
2. **Unsupervised Anomaly Detection (4 configurations)**:
   - Isolation Forest on Raw Features
   - Isolation Forest on Residual Features ($r_t$)
   - LSTM Autoencoder on Raw Features
   - LSTM Autoencoder on Residual Features ($r_t$)

---

## 4. Evaluation Strategy & Scientific Integrity Protocol

### Strategy 2 — Evaluation Under Realistic Deployment Drift:
1. **Offline Training on Baseline**:
   - All models (XGBoost, LSTM Forecaster, Isolation Forest, LSTM-AE) are trained strictly on clean training data under ideal baseline synchronization ($\Delta t = 0$).
   - Normalization statistics ($\mu_{\text{train}}, \sigma_{\text{train}}$) and anomaly decision thresholds ($\tau_{95}$) are frozen from the validation split under baseline synchronization.
2. **Evaluation Across Stale Test Traces**:
   - The test set is evaluated across each of the 24 distinct $(\Delta t, P_{\text{drop}})$ conditions.
   - For raw representations, sensor inputs $y_t$ bypass Digital Twin synchronization, preserving invariant baseline detection.
   - For residual representations, $r_t(\Delta t)$ reflects the true operational degradation caused by stale Digital Twin estimates.
   - No retraining or threshold re-tuning is permitted on test conditions.

---

## 5. Artifacts and Output Schema

Every run produces an auditable run directory:
`experiments/runs/E5_STALENESS_SWEEP_SEED<seed>_<timestamp>/` containing:

1. `manifest.json`: Full SHA-256 integrity hashes, git commit, CLI call, environment metadata.
2. `config_snapshot.yaml`: Complete locked configuration parameters.
3. `aoi_statistics.json`: Realized Age of Information distributions (mean, median, p95, p99, max) per condition.
4. `comparison.csv`: Long-format tabular metrics for all 24 conditions and all 7 model configurations.
5. `metrics.json`: Hierarchical JSON storing raw metrics, absolute degradation $\Delta M$, and relative degradation $\Delta M / M_0$.
6. `predictions.parquet`: Pointwise predictions, anomaly scores, and true binary labels across all conditions.
7. `synchronization_logs.parquet`: Full tick-by-tick timestamped audit log of scheduled, transmitted, and dropped updates.
8. `summary.md`: Human-readable markdown summary report with Markdown tables.
