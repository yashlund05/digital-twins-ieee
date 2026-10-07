# Phase 22 — E4 Baseline Reproduction Audit

**Status:** PASS  
**Audit Timestamp:** 2026-10-07T10:15:00Z  
**Baseline Parameters:** $\Delta t = 0$\,s, $P_{\mathrm{drop}} = 0$, Seed = 42  

## 1. Reproduction & Comparison
We evaluated the canonical test set ($N_{\mathrm{test}} = 5,256$, $N_{\mathrm{train}} = 24,528$) predictions and metric calculations across all four baseline conditions.

| Condition | Model | Representation | Expected Metric | Observed Metric | Absolute Difference | Tolerance | Status |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **E4-1** | Isolation Forest | Raw | $F_1 = 0.1176470588$ | $F_1 = 0.1176470588$ | $0.0$ | $5 \times 10^{-7}$ | **PASS** |
| **E4-2** | Isolation Forest | Residual | $F_1 = 0.0887272727$ | $F_1 = 0.0887272727$ | $0.0$ | $5 \times 10^{-7}$ | **PASS** |
| **E4-3** | LSTM-AE | Raw | $F_1 = 0.5386064030$ | $F_1 = 0.5386064030$ | $0.0$ | $5 \times 10^{-7}$ | **PASS** |
| **E4-4** | LSTM-AE | Residual | $F_1 = 0.9779559118$ | $F_1 = 0.9779559118$ | $0.0$ | $5 \times 10^{-7}$ | **PASS** |

## 2. Physics-Residual Definition & Invariance Check
- Residual arithmetic: $r_t = y_t - y^{\mathrm{DT}}_t$
- Normalization: Scalers fit strictly on training set ($N_{\mathrm{train}} = 24,528$) without future or test leakage.
- No hidden clipping, smoothing, or post-hoc threshold cheating detected.
