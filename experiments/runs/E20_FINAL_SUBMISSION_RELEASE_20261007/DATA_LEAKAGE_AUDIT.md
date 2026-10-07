# Data Leakage & Out-of-Sample Partitioning Audit

**Status:** PASS — Zero Information Leakage

## 1. Partitioning Protocol
- **Temporal Partitioning:** Chronological split into Train (70%), Validation (15%), Test (15%).
- **Chronological Direction:** Historical time strictly precedes prediction time. Zero random shuffling of temporal sequences.

## 2. Parameter Calibration Isolation
- **Feature StandardScalers & MinMaxScalers:** Fit strictly on training partition ($t \in [0, T_{\text{train}}]$). Validation and test sets transformed blindly.
- **Static Detection Threshold $\tau_0$:** Calibrated strictly as 99th percentile of residual norms on the clean validation partition under ideal synchronization. Zero test data observation.
- **Adaptive Parameter $\gamma$:** Calibrated over grid search on validation staleness sweep. Frozen prior to test evaluation.
- **Cross-Feeder Transfer (LOFO):** Target feeder data completely withheld during donor training. Evaluated in zero-shot transfer mode.
