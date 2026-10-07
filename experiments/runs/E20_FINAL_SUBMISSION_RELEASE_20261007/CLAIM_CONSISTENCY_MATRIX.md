# Canonical Claim Consistency Matrix (C01–C24)

| Claim ID | Formal Claim Statement | Verified Number | Units | Seed Scope | Feeder Scope | AoI Scope | Model Scope | Evidence Source | Audit Status |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|---|:---:|
| **C01** | Baseline Residual LSTM-AE Anomaly Detection F1 under ideal synchronization | 0.977956 | F1 score | Seed 42 | IEEE 33-bus | $\Delta t = 0\,$s, $P_{\text{drop}}=0$ | LSTM-AE | `E4/metrics.json` | **PASS** |
| **C02** | Baseline Raw LSTM-AE Anomaly Detection F1 under ideal synchronization | 0.538606 | F1 score | Seed 42 | IEEE 33-bus | $\Delta t = 0\,$s, $P_{\text{drop}}=0$ | LSTM-AE | `E4/metrics.json` | **PASS** |
| **C03** | Baseline Raw Isolation Forest Anomaly Detection F1 under ideal synchronization | 0.117647 | F1 score | Seed 42 | IEEE 33-bus | $\Delta t = 0\,$s, $P_{\text{drop}}=0$ | Isolation Forest | `E4/metrics.json` | **PASS** |
| **C04** | Baseline Residual Isolation Forest Anomaly Detection F1 under ideal synchronization | 0.088727 | F1 score | Seed 42 | IEEE 33-bus | $\Delta t = 0\,$s, $P_{\text{drop}}=0$ | Isolation Forest | `E4/metrics.json` | **PASS** |
| **C05** | Multi-seed aggregate log-linear degradation slope difference $\Delta\beta$ | -1.223646 | Slope diff | 5 seeds | IEEE 33-bus | Full $6 \times 4$ grid | Joint Task | `E10/multiseed_h3_summary.csv` | **PASS** |
| **C06** | Multi-seed aggregate 95% bootstrap CI lower bound for $\Delta\beta$ | -1.346260 | Slope diff | 5 seeds | IEEE 33-bus | Full $6 \times 4$ grid | Joint Task | `E10/multiseed_h3_summary.csv` | **PASS** |
| **C07** | Multi-seed aggregate 95% bootstrap CI upper bound for $\Delta\beta$ | -1.113412 | Slope diff | 5 seeds | IEEE 33-bus | Full $6 \times 4$ grid | Joint Task | `E10/multiseed_h3_summary.csv` | **PASS** |
| **C08** | Multi-seed slope hypothesis test p-value for $H_3$ | 1.000000 | p-value | 5 seeds | IEEE 33-bus | Full $6 \times 4$ grid | Joint Task | `E10/multiseed_h3_summary.csv` | **PASS** |
| **C09** | Formal hypothesis decision for $H_3$ across all tested seeds | NOT_SUPPORTED | Decision | 5 seeds | IEEE 33-bus | Full $6 \times 4$ grid | Joint Task | `E10/multiseed_h3_summary.csv` | **PASS** |
| **C10** | Factorial synchronization conditions count per seed | 24 | Conditions | Factorial grid | IEEE 33-bus | $6 \times 4$ | Pipeline | `E5/comparison.csv` | **PASS** |
| **C11** | Total evaluated seed-condition pairs in multi-seed grid | 120 | Runs | 5 seeds | IEEE 33-bus | 24 conditions | Pipeline | `E10/seed_results.csv` | **PASS** |
| **C12** | Controlled ablation evaluation count across suites A1–A8 | 88 | Evaluations | Evaluated grid | IEEE 33-bus | Ablations | Pipeline | `E11/table_02_ablation_results.csv` | **PASS** |
| **C13** | Micro instantaneous residual departure change point | 0.0 | Seconds | High-res | IEEE 33-bus | Continuous | Residual norm | `E11/table_04_change_point_analysis.csv` | **PASS** |
| **C14** | Macro empirical operational transition cliff on 33-bus (Historical Coarse Bin) | 5.0 | Seconds | Coarse grid | IEEE 33-bus | Discrete bin | Residual LSTM-AE | `E11/summary.md` | **WARNING (Demarcated: superseded by continuous 3.2s on 33-bus and [2.4s, 4.1s] cross-feeder envelope)** |
| **C15** | Baseline LSTM load estimation MAPE under ideal synchronization | 8.9504 | % MAPE | Seed 42 | IEEE 33-bus | $\Delta t = 0\,$s, $P_{\text{drop}}=0$ | LSTM | `E5/comparison.csv` | **PASS** |
| **C16** | Baseline XGBoost load estimation MAPE under ideal synchronization | 9.0635 | % MAPE | Seed 42 | IEEE 33-bus | $\Delta t = 0\,$s, $P_{\text{drop}}=0$ | XGBoost | `E5/comparison.csv` | **PASS** |
| **C17** | Baseline Persistence load estimation MAPE under ideal synchronization | 14.7321 | % MAPE | Seed 42 | IEEE 33-bus | $\Delta t = 0\,$s, $P_{\text{drop}}=0$ | Persistence | `E5/comparison.csv` | **PASS** |
| **C18** | Total audited transient timesteps across active staleness epochs | 73584 | Timesteps | High-res | IEEE 33-bus | Intra-epoch | Telemetry | `E11/summary.md` | **PASS** |
| **C19** | Zero-Shot Leave-One-Feeder-Out representation inversion replication rate | 100% (3/3) | Rate | 10 seeds | IEEE 13, 33, 123 | Full sweep | LSTM-AE | `E18/table_14_lofo_transfer.csv` | **PASS** |
| **C20** | Operational transition cliff scaling envelope with electrical impedance depth | [2.4s, 4.1s] | Seconds | 10 seeds | IEEE 13 (4.1s), 33 (3.2s), 123 (2.4s) | Continuous | LSTM-AE | `E17/results/transition_cliff_cross_feeder.csv` | **PASS** |
| **C21** | $H_3$ falsification consistency across distinct mathematical error formulations | 100% (8/8) | Rate | 10 seeds | IEEE 33-bus | Full sweep | Multi-formulation | `E17/results/h3_adversarial_analysis.csv` | **PASS** |
| **C22** | Combined 10-seed expansion negative sign consistency rate for $\Delta\beta$ | 100% (10/10) | Rate | 10 seeds | IEEE 33-bus | Full sweep | Joint Task | `E17/results/seed_slopes_10seeds.csv` | **PASS** |
| **C23** | Hardware execution latency for physics residual arithmetic & threshold lookup | < 0.002 | ms | Benchmark | Standard AMD64 | Online batch=1 | Edge pipeline | `E18/table_15_computational_complexity.csv` | **PASS** |
| **C24** | False Positive Rate bound under AoI-adaptive dynamic thresholding | $\le 5.1\%$ | % FPR | Multi-seed | IEEE 33-bus | Full sweep | Adaptive LSTM-AE | `E17/results/threshold_sensitivity.csv` | **PASS** |

## Critical Demarcation Note on C13, C14, and C20:
- **C13 (Micro departure):** $\text{AoI}^* = 0.0\,$s (95% CI: $[0.0, 2.5]\,$s). Infinitesimal mathematical departure where residual noise departs from zero-mean baseline floor.
- **C14 (Historical Coarse Macro Cliff):** $\text{AoI}^* \approx 5.0\,$s (95% CI: $[3.5, 7.5]\,$s). Coarse historical factorial grid bin where discrete detection performance collapsed.
- **High-Resolution 33-Bus Transition:** $\text{AoI}^* \approx 3.2\,$s (95% CI: $[2.5, 4.0]\,$s). Continuous parameterization identifying the exact non-linear inflection cliff on IEEE 33-bus.
- **C20 (Cross-Feeder Envelope):** $\text{AoI}^* \in [2.4\,\text{s}, 4.1\,\text{s}]$. Rigorous Leave-One-Feeder-Out cross-topology evaluation establishing that transition cliffs scale monotonically with network electrical impedance depth (IEEE 13: 4.1s; IEEE 33: 3.2s; IEEE 123: 2.4s). The manuscript explicitly rejects any single universal fixed threshold.
