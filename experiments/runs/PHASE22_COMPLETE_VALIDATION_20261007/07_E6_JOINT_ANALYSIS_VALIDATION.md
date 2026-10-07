# Phase 22 — E6 Joint Analysis Validation

**Status:** PASS  
**Audit Timestamp:** 2026-10-07T10:25:00Z  
**Target:** `experiments/runs/E6_JOINT_ANALYSIS_SEED42_20261002/`  

## 1. Hypothesis H3 Evaluation & Slope Analysis
Pre-specified Hypothesis H3 posits that anomaly detection degrades more steeply than load forecasting under increasing Age-of-Information: $\beta_{\mathrm{AD}} > \beta_{\mathrm{LE}} \iff \Delta\beta > 0$.

Independent inspection of `H3_summary.csv`:
- **AD (LSTM-AE Residual $F_1$) vs LE (LSTM MAPE):**
  - $\beta_{\mathrm{AD}} = 0.100393$
  - $\beta_{\mathrm{LE}} = 1.215166$
  - $\Delta\beta = -1.114773$
  - 95% Confidence Interval: $[-1.317835, -0.998395]$
  - $p$-value: $1.0000$
  - Wilcoxon statistic: $55.0$ ($p = 0.989877$)
  - Decision: **NOT_SUPPORTED**

- **AD vs Persistence Baseline:** $\Delta\beta = -0.861994$, $p = 1.0000$ (NOT_SUPPORTED)
- **AD vs XGBoost Forecaster:** $\Delta\beta = -1.157066$, $p = 1.0000$ (NOT_SUPPORTED)

Across all nine comparison pairs in E6, $\Delta\beta$ is strictly negative and statistically significant against H3.
