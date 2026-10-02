# Phase 11: Reproducibility, Ablation & Missed-Update Transient Analysis

## Executive Summary
- **Execution Date**: `20261002`
- **Run Directory**: `experiments\runs\E11_PHASE11_20261002`
- **Historical Reproducibility Status**: `PASS`
- **Controlled Ablations Executed**: `8` (A1–A8, `88` condition evaluations)
- **Transient Analysis Timesteps Audited**: `73584` timesteps across active staleness epochs
- **Integrity Status**: `PASS`

---

## 1. Objective A: Reproducibility Verification
- **Phase 7 E4 Baseline**: `PASS` (Residual LSTM-AE $F_1 = 0.9780$, Raw LSTM-AE $F_1 = 0.5386$, Raw IF $F_1 = 0.1176$, Res IF $F_1 = 0.0887$)
- **Phase 8 E5 Sweep**: `PASS` (all representative conditions matched)
- **Phase 9 E6 Statistical Test**: `PASS` ($H_3$ NOT_SUPPORTED, $\Delta \beta = -1.1148$)
- **Phase 10 E10 Multi-Seed Analysis**: `PASS` ($100\%$ sign consistency across 5 seeds)

---

## 2. Objective B: Controlled Ablation Analysis (A1–A8)
1. **A1 (Representation)**: At continuous baseline ($\Delta t = 0\,$s), Residual representation provides an overwhelming advantage ($+0.4393\, F_1$). Beyond $\Delta t = 5\,$s, hold-last-state drift corrupts residuals, inverting the advantage in favor of raw telemetry.
2. **A2 (Synchronization Freshness)**: Deterministic staleness without packet loss induces a sharp phase transition between $\Delta t = 1\,$s and $5\,$s ($F_1$ drops from $0.978$ to $0.108$).
3. **A3 (Packet Loss)**: Packet loss accelerates degradation by expanding realized AoI bursts. At $\Delta t = 1\,$s, $20\%$ loss reduces $F_1$ from $0.978$ to $0.323$.
4. **A4 (Factorial Interaction)**: Significant interaction effect ($p < 0.05$) confirms that staleness and packet loss compound nonlinearly.
5. **A5 (Missed-Update Policy)**: Zero-input policy destroys detection immediately ($F_1 \approx 0.089$). Hold-last-state provides stable zero-order reconstruction at short intervals.
6. **A6 (Detector Architecture)**: LSTM-AE consistently outperforms Isolation Forest by $+0.889\, F_1$ at baseline, demonstrating that sequential reconstruction captures cyber-physical dynamics far better than tree-based partitioning.
7. **A7 (Forecasting Architecture)**: LSTM achieves lowest MAPE at baseline ($8.95\%$) vs. XGBoost ($10.51\%$) and Persistence ($11.23\%$). All models scale continuously to $\sim 62\%$ at $\Delta t = 300\,$s.
8. **A8 (Threshold Calibration)**: The canonical 95th percentile threshold provides the optimal precision-recall trade-off; 90th percentile increases false alarms while 99th percentile impairs sensitivity.

---

## 3. Objective C: Missed-Update Transient Dynamics
- **Residual Inflation**: Residual norm $\|r_t\|_2$ expands approximately monotonically with elapsed Age of Information between sync arrivals.
- **Critical Transition Cliff**: The descriptive change-point analysis identifies a sharp performance transition at realized $\text{AoI} \approx 5.0\,$s ($[3.5\,$s, $7.5\,$s$]$), after which hold-last-state drift submerges true anomaly signals beneath the background noise floor.
