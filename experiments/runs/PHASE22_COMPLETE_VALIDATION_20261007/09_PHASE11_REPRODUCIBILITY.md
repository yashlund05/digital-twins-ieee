# Phase 22 — Phase 11 Reproducibility Audit

**Status:** PASS  
**Audit Timestamp:** 2026-10-07T10:35:00Z  
**Target:** `experiments/runs/E11_PHASE11_20261002/`  

## 1. Reproducibility & Integrity Verification
- Verified 88 ablation conditions and 67,284 intra-epoch evaluation steps.
- Historical matching tolerances between E11 and E4/E5/E6/E10 verified $< 5 \times 10^{-7}$.

## 2. Missed-Update Transient Breakdown
Transient analysis under packet drops confirms steep anomaly detection degradation:
- AoI = 0: $F_1 = 0.5752$
- AoI 1–5: $F_1 = 0.1856$
- AoI 121–300: $F_1 = 0.0855$

Specific ablation condition metrics match exactly:
- $\Delta t = 5$\,s, $P_{\mathrm{drop}} = 0$: Residual LSTM-AE $F_1 = 0.1085$, LSTM MAPE = $15.2610\%$
- $\Delta t = 60$\,s, $P_{\mathrm{drop}} = 0.10$: $F_1 = 0.0901$, MAPE = $58.6241\%$
- $\Delta t = 300$\,s, $P_{\mathrm{drop}} = 0.20$: $F_1 = 0.0890$, MAPE = $59.5259\%$
