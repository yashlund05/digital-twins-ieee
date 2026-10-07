# Phase 22 — E5 24-Condition Staleness Sweep Validation

**Status:** PASS  
**Audit Timestamp:** 2026-10-07T10:20:00Z  

## 1. Condition Matrix Completeness
Verified complete $6 \times 4 = 24$ factorial grid across:
- $\Delta t \in \{0, 1, 5, 15, 60, 300\}$\,s
- $P_{\mathrm{drop}} \in \{0.0, 0.05, 0.10, 0.20\}$

All 24 condition keys exist in `metrics.json` across Seed 42 and replicated seeds (123, 456, 789, 101112):
`E5_DT0_PD00_SEED42` through `E5_DT300_PD20_SEED42`.

## 2. Mandatory Baseline Reconciliation: E5 (0, 0) == E4
Cross-verification of Condition `E5_DT0_PD00_SEED42` vs. `E4`:
- **Isolation Forest Raw:** E5 $F_1 = 0.1176470588$ vs E4 $F_1 = 0.1176470588$ (Diff = $0.0$) $\rightarrow$ **PASS**
- **Isolation Forest Residual:** E5 $F_1 = 0.0887272727$ vs E4 $F_1 = 0.0887272727$ (Diff = $0.0$) $\rightarrow$ **PASS**
- **LSTM-AE Raw:** E5 $F_1 = 0.5386064030$ vs E4 $F_1 = 0.5386064030$ (Diff = $0.0$) $\rightarrow$ **PASS**
- **LSTM-AE Residual:** E5 $F_1 = 0.9779559118$ vs E4 $F_1 = 0.9779559118$ (Diff = $0.0$) $\rightarrow$ **PASS**

Baseline equivalence holds strictly with zero numerical drift.
