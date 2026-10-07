# Phase 22 — Claim Registry & Canonical Traceability Audit

**Status:** PASS (23 PASS, 1 WARNING/Demarcated)  
**Audit Timestamp:** 2026-10-07T10:55:00Z  

## 1. 24 Canonical Claims Traceability Summary
| Claim ID | Claim Description | Canonical Metric | Status | Traceability / Demarcation Note |
|:---:|---|:---:|:---:|---|
| **C01** | E4 Fresh Residual LSTM-AE F1 Advantage | $F_1 = 0.978$ vs $0.539$ | **PASS** | `E4_RAW_VS_RESIDUAL_SEED42_20260930/metrics.json` |
| **C02** | E4 Baseline Anomaly Precision/Recall | Prec = 0.957, Rec = 1.000 | **PASS** | Direct evaluation matrix verified |
| **C03** | E4 Raw Isolation Forest Poor Performance | $F_1 = 0.118$ | **PASS** | Verified against test split |
| **C04** | E4 Residual Isolation Forest Failure | FPR = 1.000, $F_1 = 0.089$ | **PASS** | Verified; threshold saturation observed |
| **C05** | E5 Factorial Sweep Completeness | 24 conditions ($6 \times 4$) | **PASS** | All conditions present and reconciled |
| **C06** | E5 AoI Monotonic Degradation | Monotonic $F_1$ drop | **PASS** | Observed across all staleness tiers |
| **C07** | E5 Packet Drop Compounding | Drop penalty amplified at high $\Delta t$ | **PASS** | Confirmed via two-way ANOVA |
| **C08** | E6 Hypothesis H3 Non-Support | $\Delta\beta = -1.115$, $p = 1.000$ | **PASS** | Slope difference strictly negative |
| **C09** | E6 Load Forecasting Compounding Error | Recursive lag error dominates | **PASS** | Confirmed via multi-step metrics |
| **C10** | E10 Multi-Seed Falsification of H3 | Aggregate $\Delta\beta = -1.224$ | **PASS** | Negative across all 5 seeds |
| **C11** | E10 Wilcoxon Hypothesis Confirmation | $p = 1.000$ | **PASS** | Non-parametric rank sum verified |
| **C12** | E11 Missed-Update Transient Cliff | Severe F1 drop under drops | **PASS** | Intra-epoch trace verified |
| **C13** | E11 Instantaneous Change-Point AoI | Change point at $\mathrm{AoI} = 0$\,s | **PASS** | PELT micro-scale transition |
| **C14** | Macro Transition Cliff Interpretation | Operational envelope $[2.4, 4.1]$\,s | **WARNING** | Demarcated: distinguished micro vs macro cliff |
| **C15** | Out-of-Sample Threshold Portability | Non-42 FPR drops to $\approx 4.4\%$ | **PASS** | Validated under $\tau(\mathrm{AoI})$ model |
| **C16** | High-Res 33-Bus Transition at 3.2s | Maximum derivative at $3.2$\,s | **PASS** | Validated via fine-grained sweep |
| **C17** | Telemetry Noise Robustness (40dB) | MAPE degradation $< 0.35\%$ | **PASS** | Verified under Gaussian noise injection |
| **C18** | One-Class SVM Baseline Performance | Fresh $F_1 = 0.670 \rightarrow 0.046$ | **PASS** | Verified under boundary optimization |
| **C19** | GRU Forecaster Consistency | GRU MAPE aligns with LSTM | **PASS** | Difference $< 0.05\%$ MAPE |
| **C20** | Multi-Feeder Representation Inversion | Inversion on 13, 33, 123-bus | **PASS** | Observed across all 3 radial networks |
| **C21** | Operational Envelope Scaling with Depth | Envelope $[2.4, 4.1]$\,s | **PASS** | Inversely related to impedance depth |
| **C22** | Sub-Microsecond Residual Computation | $0.41\,\mu$s extraction time | **PASS** | Microbenchmarked on AMD64 |
| **C23** | 8 Adversarial H3 Formulations Reject H3 | All 8 formulations yield $\Delta\beta < 0$ | **PASS** | Table S6 verified |
| **C24** | 10-Seed Expansion Confirms Rejection | $N=10$ seeds, $p=1.000$ | **PASS** | Confirmed across expanded seeds |
