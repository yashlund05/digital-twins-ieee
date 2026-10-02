# Phase 9 — Joint Analysis & Hypothesis Testing

## Experiment E6: Cross-Task Degradation Modeling and Statistical Inference

> **Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin**  
> *Target Publication Level: IEEE Transactions on Smart Grid*

---

## 1. Executive Summary & Research Scope

Phase 9 implements the formal joint statistical analysis and hypothesis testing framework (Experiment E6) for the distribution-feeder Digital Twin research project. Building upon the 24 experimental conditions executed under Experiment E5 (Phase 8), Phase 9 performs cross-task degradation modeling, effect size estimation, and hypothesis evaluation to assess how synchronization staleness ($\Delta t$) and packet drops ($P_{\text{drop}}$) affect two core downstream operations:

1. **Short-Term Distribution Load Estimation** (regression task)
2. **Unsupervised Physics-Residual Anomaly Detection** (one-class classification / state reconstruction task)

In strict adherence to the project research integrity rules (`AGENTS.md`, `AI_RULES.md`), Phase 9 is an **analysis and statistical inference phase only**. It does not retrain models, alter feature sets, tune anomaly detection thresholds on test data, or cherry-pick seeds. All findings are derived deterministically from the reconciled and verified Phase 8 dataset (`experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930`).

---

## 2. Mathematical Formulations & Statistical Methodology

### 2.1 Standardized Directional Degradation

Because power-system downstream tasks utilize metrics with opposing optimization polarities, all metrics are normalized to a consistent, directional degradation metric where **positive values indicate performance loss relative to baseline** and **zero indicates identical baseline performance**.

Let $M_0$ denote the baseline metric value under ideal continuous synchronization ($\Delta t = 0\,\text{s}, P_{\text{drop}} = 0.0$), and let $M$ denote the observed metric value under a specific staleness condition $(\Delta t, P_{\text{drop}})$.

#### Directionality Registry
- **Higher-is-Better ($\mathcal{M}_{\text{hib}}$)**: $F_1$-score, Precision, Recall, PR-AUC, ROC-AUC, $R^2$.
- **Lower-is-Better ($\mathcal{M}_{\text{lib}}$)**: MAE, RMSE, MAPE, False Positive Rate (FPR), Detection Latency.

#### Formulations
The **absolute degradation** $D_{\text{abs}}$ is defined as:
$$D_{\text{abs}} = \begin{cases} M_0 - M, & M \in \mathcal{M}_{\text{hib}} \\ M - M_0, & M \in \mathcal{M}_{\text{lib}} \end{cases}$$

The **task-normalized (relative) degradation** $D_{\text{norm}}$ is defined as:
$$D_{\text{norm}} = \begin{cases} \dfrac{M_0 - M}{\max(|M_0|, \epsilon)}, & M \in \mathcal{M}_{\text{hib}} \\ \dfrac{M - M_0}{\max(|M_0|, \epsilon)}, & M \in \mathcal{M}_{\text{lib}} \end{cases}$$
where $\epsilon = 10^{-8}$ prevents division by zero.

### 2.2 Degradation Trajectory Regression Models

To model degradation profiles across nominal synchronization intervals $\Delta t$ and realized Age of Information (AoI), log-linear and two-way factorial models are estimated via ordinary least squares (OLS):

1. **Log-Linear Staleness Model**:
   $$D_{\text{norm}} = \beta_0 + \beta_{\Delta t} \ln(1 + \Delta t) + \epsilon$$
2. **Log-Linear Realized AoI Model**:
   $$D_{\text{norm}} = \gamma_0 + \gamma_{\text{AoI}} \ln(1 + \overline{\text{AoI}}) + \eta$$
3. **Two-Way Factorial Interaction Model**:
   $$D_{\text{norm}} = \alpha_0 + \alpha_1 \ln(1 + \Delta t) + \alpha_2 P_{\text{drop}} + \alpha_3 \left[ \ln(1 + \Delta t) \times P_{\text{drop}} \right] + \xi$$

The slope parameter $\beta$ quantifies the rate of normalized performance degradation per unit of log-staleness.

### 2.3 Effect Size Quantification

Standardized effect sizes are computed between baseline conditions and degraded states:
- **Parametric (Cohen's $d$)**:
  $$d = \frac{\overline{X}_{\text{stale}} - \overline{X}_{\text{base}}}{s_p}, \quad s_p = \sqrt{\frac{(n_1-1)s_1^2 + (n_2-1)s_2^2}{n_1 + n_2 - 2}}$$
- **Non-Parametric (Cliff's $\delta$)**:
  $$\delta = \frac{\#\left(X_{\text{stale}} > X_{\text{base}}\right) - \#\left(X_{\text{stale}} < X_{\text{base}}\right)}{n_1 \cdot n_2}$$
  Categorical thresholds: $|\delta| < 0.147$ (negligible), $0.147 \le |\delta| < 0.33$ (small), $0.33 \le |\delta| < 0.474$ (medium), $|\delta| \ge 0.474$ (large).

### 2.4 Research Hypothesis $H_3$ Formal Testing

#### Pre-Specified Hypothesis $H_3$
> **$H_3$:** Anomaly detection exhibits a steeper degradation profile than short-term load estimation as Digital Twin synchronization staleness increases.

#### Statistical Hypothesis Formulation
- **Null Hypothesis ($H_0$)**: $\Delta \beta = \beta_{\text{ad}} - \beta_{\text{le}} \le 0$ (Anomaly detection degrades at the same rate or less steeply than load estimation).
- **Alternative Hypothesis ($H_3$)**: $\Delta \beta = \beta_{\text{ad}} - \beta_{\text{le}} > 0$ (Anomaly detection degrades strictly steeper than load estimation).

Here, $\beta_{\text{ad}}$ and $\beta_{\text{le}}$ are the log-linear slopes of task-normalized degradation for residual LSTM-AE ($F_1$-score) and load estimation (LSTM MAPE) fitted over the 24 paired conditions.

#### Inference & Significance Testing
1. **Paired Bootstrap Resampling**: Resampling condition indices with replacement ($B = 2{,}000$ iterations, seed = 42) to construct the empirical distribution $F^*(\Delta \beta)$ and $95\%$ bootstrap percentile confidence interval $[c_{\text{low}}, c_{\text{high}}]$.
2. **Empirical One-Sided $p$-value**:
   $$p = \frac{1}{B} \sum_{b=1}^B \mathbb{I}\left( \Delta \beta^{(b)} \le 0 \right)$$
3. **Paired Wilcoxon Signed-Rank Test**: Non-parametric test on matched pairs across the 24 experimental conditions.
4. **False Discovery Rate (FDR) Control**: Benjamini-Hochberg procedure applied across all 9 model-metric pairwise tests at family-wise $\alpha = 0.05$.

---

## 3. Empirical Results and Findings

### 3.1 Primary Hypothesis Evaluation

The primary formal test was conducted comparing Anomaly Detection (Residual LSTM-AE $F_1$) against Load Estimation (LSTM Forecaster MAPE) across all 24 conditions:

| Parameter / Statistic | Observed Value | Interpretation |
|---|---|---|
| Anomaly Detection Slope ($\beta_{\text{ad}}$) | `0.1004` | Log-linear degradation rate of residual LSTM-AE $F_1$ |
| Load Estimation Slope ($\beta_{\text{le}}$) | `1.2152` | Log-linear degradation rate of LSTM load MAPE |
| Slope Difference ($\Delta \beta = \beta_{\text{ad}} - \beta_{\text{le}}$) | `-1.1148` | Load estimation degrades faster on normalized scale |
| 95% Bootstrap CI for $\Delta \beta$ | `[-1.3178, -0.9984]` | Zero is strictly excluded; upper bound is $< 0$ |
| Empirical One-Sided $p$-value ($H_0: \Delta \beta \le 0$) | `1.0000` | No bootstrap samples yielded $\Delta \beta > 0$ |
| Matched Paired Wilcoxon Statistic ($W$) | `55.0` ($p = 0.9899$) | Matched conditions fail one-sided superiority test |
| **Formal Decision for $H_3$** | **NOT SUPPORTED** | The null hypothesis cannot be rejected |

### 3.2 Full Pairwise Comparison Matrix (with Benjamini-Hochberg FDR)

To guarantee that the outcome is not an artifact of model or metric selection, the test was extended across all combinations of load forecasting models (`persistence`, `xgboost`, `lstm`) and error metrics (`MAPE`, `RMSE`, `MAE`):

| Task Comparison | $\beta_{\text{ad}}$ | $\beta_{\text{le}}$ | $\Delta \beta$ | 95% Bootstrap CI | $p_{\text{slope}}$ | Wilcoxon $W$ ($p$) | Conclusion | FDR Adj. $p$ | Significant? |
|---|---:|---:|---:|:---:|---:|---:|:---:|---:|:---:|
| AD (LSTM-AE $F_1$) vs LE (Persistence MAPE) | 0.1004 | 0.9624 | -0.8620 | [-1.0239, -0.7650] | 1.0000 | 55.0 (0.9899) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (Persistence RMSE) | 0.1004 | 0.8488 | -0.7484 | [-0.8885, -0.6657] | 1.0000 | 55.0 (0.9899) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (Persistence MAE)  | 0.1004 | 0.9233 | -0.8229 | [-0.9735, -0.7351] | 1.0000 | 48.0 (0.9946) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (XGBoost MAPE)     | 0.1004 | 1.2575 | -1.1571 | [-1.3634, -1.0365] | 1.0000 | 55.0 (0.9899) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (XGBoost RMSE)     | 0.1004 | 1.0410 | -0.9406 | [-1.1135, -0.8416] | 1.0000 | 55.0 (0.9899) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (XGBoost MAE)      | 0.1004 | 1.2435 | -1.1431 | [-1.3392, -1.0311] | 1.0000 | 48.0 (0.9946) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (LSTM MAPE)        | 0.1004 | 1.2152 | -1.1148 | [-1.3178, -0.9984] | 1.0000 | 55.0 (0.9899) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (LSTM RMSE)        | 0.1004 | 0.9511 | -0.8507 | [-1.0188, -0.7538] | 1.0000 | 55.0 (0.9899) | NOT_SUPPORTED | 1.0000 | No |
| AD (LSTM-AE $F_1$) vs LE (LSTM MAE)         | 0.1004 | 1.2010 | -1.1006 | [-1.3127, -0.9812] | 1.0000 | 45.0 (0.9959) | NOT_SUPPORTED | 1.0000 | No |

---

## 4. Scientific Discussion: Why $H_3$ Was Contradicted

The contradiction of $H_3$ reveals critical cyber-physical insights regarding metric dynamics and state estimation fidelity:

### 4.1 Bounded Classification Metric Saturation vs. Unbounded Regression Scaling
- **Anomaly Detection Saturation Floor**: $F_1$-score is bounded in $[0, 1]$. In the residual domain, $F_1$ drops precipitously from $0.9780$ at baseline to $0.1085$ at $\Delta t = 5\,\text{s}$. Once staleness exceeds $\Delta t = 5\,\text{s}$, the residual distribution is overwhelmed by hold-last-state drift, causing $F_1$ to hit the random/noise floor ($\approx 0.089$). Consequently, normalized degradation saturates at:
  $$D_{\text{norm}}^{\text{AD}} = \frac{0.9780 - 0.0887}{0.9780} \approx 0.909 \quad (\le 1.0)$$
- **Unbounded Load Forecasting Growth**: Conversely, regression metrics (MAPE, RMSE, MAE) are mathematically unbounded from above. As staleness increases to $\Delta t = 300\,\text{s}$, load estimation error expands dramatically:
  $$\text{MAPE: } 8.95\% \to 62.29\% \implies D_{\text{norm}}^{\text{LE}} = \frac{62.29 - 8.95}{8.95} \approx 5.96 \quad (596\% \text{ degradation})$$
  Because load estimation normalized degradation scales continuously (by a factor of ~6.0) while anomaly detection degradation saturates at $< 1.0$, the log-linear slope of load forecasting ($\beta_{\text{le}} \approx 1.22$) substantially exceeds that of anomaly detection ($\beta_{\text{ad}} \approx 0.10$).

### 4.2 Cyber-Physical Interpretation: The Critical Staleness Cliff
Rather than a smooth, continuous degradation, anomaly detection exhibits a **catastrophic phase transition** at low staleness ($\Delta t \le 5\,\text{s}$). Below $1\,\text{s}$, high-fidelity residual anomaly detection remains viable ($F_1 > 0.64$ at $P_{\text{drop}} = 0.05$); however, beyond $5\,\text{s}$, state estimation drift dominates the physical residual, rendering threshold-based detection completely inoperative. Load estimation, in contrast, degrades gracefully across the entire staleness spectrum.

---

## 5. Generated Artifacts & Visualizations

Experiment E6 produced 8 publication-grade vector/raster figures in `experiments/runs/E6_JOINT_ANALYSIS_SEED42_20261002/figures/`:

1. `fig_01_anomaly_f1_vs_staleness.png`: $F_1$-score degradation across nominal staleness $\Delta t$ and packet drop rates for all detector-representation pairs. Demonstrates the complete invariance of Raw representations and the steep cliff of Residual representations.
2. `fig_02_anomaly_prauc_vs_staleness.png`: Precision-Recall AUC curves across staleness, confirming threshold-independent separation loss.
3. `fig_03_load_mae_vs_staleness.png`: Load estimation MAE trajectory showing continuous, smooth error growth across models.
4. `fig_04_load_rmse_vs_staleness.png`: Load estimation RMSE trajectory illustrating error penalization under large delays.
5. `fig_05_task_degradation_comparison.png`: Dual-panel comparative plot showing absolute and normalized degradation profiles for both downstream tasks.
6. `fig_06_realized_aoi.png`: Realized Mean and P95 Age of Information (AoI) as a function of scheduled $\Delta t$ and packet loss.
7. `fig_07_staleness_packet_drop_interaction.png`: Interaction heatmaps displaying the compounding effect of $\Delta t \times P_{\text{drop}}$ on residual anomaly $F_1$ and load MAPE.
8. `fig_08_h3_effect_comparison.png`: Forest plot of regression slope differences ($\Delta \beta$) with 95% bootstrap confidence intervals for all 9 model-metric pairs.

---

## 6. Scientific Limitations & Phase 10 Transition

1. **Single-Seed Scope**: All findings in Phase 9 were established under frozen seed `seed = 42`. While within-condition paired tests achieve unambiguous statistical certainty ($p = 1.0000$), multi-seed population inference across independent stochastic feeder realizations is reserved for **Phase 10**.
2. **Threshold Calibration**: Thresholds were calibrated at the $\Delta t = 0\,\text{s}$ baseline ($\tau_{95}$) and kept static across all staleness conditions, reflecting realistic operational conditions where operators cannot dynamically recalibrate detectors for unmonitored communication delays.
