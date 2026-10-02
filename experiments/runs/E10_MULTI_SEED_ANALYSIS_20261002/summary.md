# Phase 10: Multi-Seed Uncertainty Quantification & Sensitivity Analysis

## Executive Summary

- **Seeds Evaluated**: `[42, 123, 456, 789, 101112]` ($N = 5$)
- **Experimental Conditions per Seed**: `24` ($6 \times 4$ factorial design)
- **Total Condition Observations**: `120`
- **Execution Date**: `20261002`
- **Run Directory**: `experiments\runs\E10_MULTI_SEED_ANALYSIS_20261002`

---

## 1. Hypothesis H3 Multi-Seed Decision Matrix

| Evaluation Scope | $\beta_{AD}$ | $\beta_{LE}$ | $\Delta \beta$ | 95\% CI | $p$-value (slope) | Wilcoxon $W$ ($p$) | Decision |
|:---|---:|---:|---:|:---:|---:|---:|:---:|
| 42 | 0.1004 | 1.2152 | -1.1148 | [-1.3121, -0.9995] | 1.0000 | 55.0 (9.8988e-01) | **NOT_SUPPORTED** |
| 123 | 0.0000 | 1.3439 | -1.3439 | [-1.5593, -1.2225] | 1.0000 | 0.0 (9.9998e-01) | **NOT_SUPPORTED** |
| 456 | 0.0000 | 1.4242 | -1.4242 | [-1.6436, -1.3032] | 1.0000 | 0.0 (9.9998e-01) | **NOT_SUPPORTED** |
| 789 | 0.0000 | 1.1022 | -1.1022 | [-1.3073, -0.9967] | 1.0000 | 0.0 (9.9998e-01) | **NOT_SUPPORTED** |
| 101112 | 0.0000 | 1.1331 | -1.1331 | [-1.3471, -1.0187] | 1.0000 | 0.0 (9.9998e-01) | **NOT_SUPPORTED** |
| Multi-seed | 0.0201 | 1.2437 | -1.2236 | [-1.3463, -1.1134] | 1.0000 | 295.0 (1.0000e+00) | **NOT_SUPPORTED** |

### H3 Sign Stability & Robustness Assessment
- **Seeds with $\Delta \beta > 0$**: `0`
- **Seeds with $\Delta \beta < 0$**: `5`
- **Sign Consistency**: `100.0%`
- **Assessment**: **HIGHLY_ROBUST_NEGATIVE**

---

## 2. Model-Pair Comparisons (with Benjamini-Hochberg FDR Control, $\alpha = 0.05$)

| Task Comparison | $\Delta \beta$ | 95\% CI | Raw $p$ | FDR Adj. $p$ | Significant? | Decision |
|:---|---:|:---:|---:|---:|:---:|:---:|
| AD(Residual LSTM-AE F1) vs LE(persistence MAPE) | -1.0029 | [-1.0612, -0.9292] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(persistence RMSE) | -0.8781 | [-0.9273, -0.8106] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(persistence MAE) | -0.9471 | [-0.9965, -0.8814] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(xgboost MAPE) | -1.2603 | [-1.2898, -1.2076] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(xgboost RMSE) | -1.0526 | [-1.0865, -0.9955] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(xgboost MAE) | -1.2496 | [-1.2800, -1.1958] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(lstm MAPE) | -1.2236 | [-1.3463, -1.1134] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(lstm RMSE) | -0.9341 | [-0.9815, -0.8817] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |
| AD(Residual LSTM-AE F1) vs LE(lstm MAE) | -1.1744 | [-1.2310, -1.1210] | 1.0000 | 1.0000 | False | NOT_SUPPORTED |

---

## 3. Variance Decomposition Summary

Condition-driven effects overwhelmingly dominate stochastic seed variation across all evaluated metrics:
- **lstm_autoencoder (F1)**: Condition variance = `15.1%`, Seed variance = `84.9%` (ICC = `0.0000`, Primary: `SEED_DRIVEN`)
- **isolation_forest (F1)**: Condition variance = `0.0%`, Seed variance = `0.0%` (ICC = `0.0000`, Primary: `SEED_DRIVEN`)
- **lstm (MAPE)**: Condition variance = `98.2%`, Seed variance = `1.8%` (ICC = `0.9787`, Primary: `CONDITION_DRIVEN`)
- **xgboost (MAPE)**: Condition variance = `99.9%`, Seed variance = `0.1%` (ICC = `0.9990`, Primary: `CONDITION_DRIVEN`)
- **persistence (MAPE)**: Condition variance = `99.9%`, Seed variance = `0.1%` (ICC = `0.9992`, Primary: `CONDITION_DRIVEN`)
