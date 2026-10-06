# Phase 15 — Accuracy Gap Analysis & Performance Enhancement Opportunities

**Target Venue:** IEEE Transactions on Smart Grid  
**Auditor Mode:** Scientific Performance & Detection/Estimation Optimization Analysis  
**Guiding Principle:** Accuracy gains must be physically motivated, leak-free, and methodologically sound. No test-set tuning or artificial metric inflation.

---

## 1. Anomaly Detection Performance Gap Analysis

### Baseline Diagnosis
- **Ideal Sync ($\Delta t = 0\,$s, Seed 42):** Residual LSTM-AE achieves near-perfect performance ($F_1 = 0.978$, Precision = $0.957$, Recall = $1.000$, $\text{FPR} = 0.002$).
- **Stale Sync ($\Delta t \ge 5\,$s, Seed 42):** Precision collapses to $0.057$, $\text{FPR}$ surges to $0.800$, causing $F_1$ to collapse to $0.1085$.
- **Seeds 123, 456, 789, 101112:** Precision is $0.0464$, $\text{FPR} = 1.000$, and $F_1 = 0.0887$ across *all* conditions.

### Root Causes
1. **Residual Noise Floor Inflation:** Under hold-last-state extrapolation, normal load fluctuations between updates generate non-zero physical-virtual residuals $r_t = y_t - y_{\text{last}}$, which mimic anomaly signatures.
2. **Fixed Threshold Vulnerability:** A static scalar threshold $\tau_0$ calibrated on clean training residuals cannot distinguish between an actual cyber-physical fault and residual drift induced by a 5-second communication delay.
3. **Threshold Calibration Portability:** The threshold $\tau_0 = 3.82 \times 10^{-4}$ was derived from Seed 42's nominal validation set. Different random seeds generate slightly different physical load realizations whose nominal reconstruction errors exceed $3.82 \times 10^{-4}$, triggering permanent false alarms.

### Scientifically Defensible Improvement Opportunities
1. **AoI-Adaptive Dynamic Thresholding:**
   - *Formulation:* $\tau(t) = \tau_0 + \gamma \sqrt{\text{AoI}(t)}$
   - *Rationale:* Since hold-last-state drift variance grows approximately with elapsed staleness ($\sigma^2 \propto \text{AoI}$), expanding the detection threshold dynamically restores precision without suppressing true anomalies.
   - *Status in Repo:* `AoIAdaptiveThreshold` class already drafted in `src/anomaly_detection/thresholds.py`! Needs systematic benchmarking.
2. **Dual-Mode Representation Switching:**
   - *Formulation:* When $\text{AoI} < \text{AoI}^* \approx 5.0\,$s, evaluate residuals $r_t$ (leveraging $F_1 = 0.978$ fidelity). When $\text{AoI} \ge 5.0\,$s, switch input representation to raw telemetry $y_t$ (leveraging stable $F_1 = 0.539$).
   - *Rationale:* Bypasses the representation inversion collapse entirely, preventing $F_1$ from dropping below the raw floor ($0.539$).
   - *Status in Repo:* `DualModeInversionCompensator` implemented in `src/anomaly_detection/dual_mode.py`!

---

## 2. Load Estimation Performance Gap Analysis

### Baseline Diagnosis
- **Baseline ($\Delta t = 0\,$s):** LSTM MAPE is $8.95\%$, XGBoost is $9.06\%$, Persistence is $14.73\%$.
- **Severe Staleness ($\Delta t = 300\,$s):** All models degrade to MAPE $\sim 60\text{--}65\%$, with Persistence at $85.45\%$.

### Root Causes
1. **Autoregressive Feedback Decay:** Forecasters rely on recent lag features ($y_{t-1}, y_{t-2}$). Under communication hold, lags become static repeats, starving the recurrent network of real derivative information.
2. **Missing Weather & Exogenous Context:** Models rely exclusively on univariate historical load and calendar cyclical features. Temperature and solar irradiance drastically improve morning/evening ramp prediction.

### Scientifically Defensible Improvement Opportunities
1. **Physics-Guided State Interpolation:** Replace raw Zero-Order Hold (ZOH) with an OpenDSS power-flow-guided linear predictor based on feeder total current injection slope.
2. **Gated Recurrent Unit (GRU) with Explicit AoI Feature:** Feed normalized realized $\text{AoI}(t)$ directly as an auxiliary input feature into the forecaster, allowing the recurrent network to learn staleness-dependent weighting.

---

## 3. Improvement Evaluation Matrix

| Improvement Opportunity | Target Task | Expected Scientific Benefit | Implementation Risk | Computational Cost | Priority |
|---|---|---|---|---|:---:|
| **AoI-Adaptive Dynamic Thresholding** | Anomaly Detection | Recovers $F_1$ from $0.108 \to 0.65+$ at $\Delta t = 5\,$s; restores multi-seed generality | Low | Negligible (post-processing) | **P0** |
| **Dual-Mode Representation Switching** | Anomaly Detection | Guarantees lower-bound $F_1 \ge 0.538$ across all staleness conditions | Low | Negligible | **P0** |
| **Per-Seed Validation Calibration** | Anomaly Detection | Fixes $\text{FPR}=1.0$ artifact across Seeds 123..101112 | Low | Negligible | **P0** |
| **GRU Forecaster Baseline** | Load Forecasting | Provides direct architectural control against LSTM | Low | Low (<10 min training) | **P1** |
| **AoI Auxiliary Feature in Forecaster** | Load Forecasting | Reduces MAPE inflation by conditioning predictions on freshness | Medium | Medium | **P2** |
