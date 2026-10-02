# Research Hypothesis H3: Differential Degradation Analysis

> **Hypothesis H3:** Anomaly detection exhibits a steeper degradation profile than short-term load estimation as Digital Twin synchronization staleness increases.

## 1. Primary Statistical Evidence

- **Primary Task Comparison:** Anomaly Detection (Residual LSTM-AE $F_1$) vs. Load Estimation (LSTM Forecaster MAPE)
- **Estimated Anomaly Degradation Slope ($\beta_{ad}$):** `0.1004`
- **Estimated Load Degradation Slope ($\beta_{le}$):** `1.2152`
- **Slope Difference ($\Delta \beta = \beta_{ad} - \beta_{le}$):** `-1.1148`
- **Bootstrap 95% Confidence Interval for $\Delta \beta$:** `[-1.3178, -0.9984]`
- **Empirical One-Sided Bootstrap $p$-value ($H_0: \Delta \beta \le 0$):** `1.0000`
- **Matched Paired Wilcoxon Signed-Rank Test Statistic:** `55.0` ($p = 9.8988e-01$)

## 2. Hypothesis Decision

### **RESULT: NOT_SUPPORTED**

H3 is NOT SUPPORTED: Anomaly detection does not degrade steeper than load estimation (Delta beta = -1.1148, p = 1.0000).

## 3. Comprehensive Model-Pair Comparisons (with Benjamini-Hochberg FDR)

| task_comparison                                 |   beta_ad |   beta_le |   delta_beta |    ci_low |   ci_high |   p_value_slope |   wilcoxon_stat |   p_value_wilcoxon | conclusion    |   p_adjusted | fdr_significant   |
|:------------------------------------------------|----------:|----------:|-------------:|----------:|----------:|----------------:|----------------:|-------------------:|:--------------|-------------:|:------------------|
| AD(LSTM-AE Residual F1) vs LE(persistence MAPE) |  0.100393 |  0.962387 |    -0.861994 | -1.02385  | -0.765026 |               1 |              55 |           0.989877 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(persistence RMSE) |  0.100393 |  0.848768 |    -0.748375 | -0.888481 | -0.665667 |               1 |              55 |           0.989877 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(persistence MAE)  |  0.100393 |  0.923256 |    -0.822863 | -0.973529 | -0.735134 |               1 |              48 |           0.994599 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(xgboost MAPE)     |  0.100393 |  1.25746  |    -1.15707  | -1.36337  | -1.03654  |               1 |              55 |           0.989877 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(xgboost RMSE)     |  0.100393 |  1.04102  |    -0.94063  | -1.1135   | -0.841593 |               1 |              55 |           0.989877 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(xgboost MAE)      |  0.100393 |  1.24348  |    -1.14308  | -1.33918  | -1.0311   |               1 |              48 |           0.994599 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(lstm MAPE)        |  0.100393 |  1.21517  |    -1.11477  | -1.31784  | -0.998395 |               1 |              55 |           0.989877 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(lstm RMSE)        |  0.100393 |  0.951134 |    -0.850741 | -1.01883  | -0.753806 |               1 |              55 |           0.989877 | NOT_SUPPORTED |            1 | False             |
| AD(LSTM-AE Residual F1) vs LE(lstm MAE)         |  0.100393 |  1.20101  |    -1.10061  | -1.31267  | -0.981181 |               1 |              45 |           0.995933 | NOT_SUPPORTED |            1 | False             |

## 4. Scientific Limitations

- **Single-Seed Limitation:** Results are evaluated on `seed = 42`. While within-condition matched tests achieve significance, multi-seed replication across independent stochastic Feeder realizations is required in Phase 10 to establish population-level inference.
- **Staleness Thresholding Effect:** Anomaly detection exhibits a steep cliff at $\Delta t = 5\,\text{s}$ ($F_1$ drops from 0.9780 to 0.1085), after which residual noise approaches baseline floor.