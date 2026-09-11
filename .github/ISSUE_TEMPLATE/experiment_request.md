---
name: Experiment Request
about: Propose a new experiment run, replication, or parameter ablation
title: "[EXP]: "
labels: ["experiment"]
assignees: ""
---

### Experiment Identifier
- [ ] Existing canonical experiment: E1 | E2 | E3 | E4 | E5 | E6 | E7
- [ ] New ablation or sensitivity study: e.g., ABL-01, SENS-01

### Research Hypothesis
State the scientific hypothesis being tested using the standardized format:
> `[HYPOTHESIS]: ...`

### Target Paper Section
- [ ] Section IV-A (Feeder Setup & Validation)
- [ ] Section IV-B (Load Estimation Staleness Degradation - RQ1)
- [ ] Section IV-C (Anomaly Detection Under Staleness - RQ2)
- [ ] Section IV-D (Critical Staleness Threshold Analysis - RQ3)
- [ ] Section IV-E (Physics-Based Residual Resilience - RQ4)

### Experimental Configuration
- **Base Configuration File:** `configs/experiments/<name>.yaml`
- **Synchronization Intervals:** [e.g. 1s, 5s, 15s, 60s, 300s]
- **Random Seeds:** [e.g. 42 (primary), 123, 456 (replication)]
- **Models Evaluated:** [e.g. Persistence, XGBoost, LSTM / IF, LSTM-AE]
- **Input Representation:** [Raw telemetry | Physics-based DT residuals | Both]

### Resource Estimation
- Estimated execution time:
- Storage footprint for artifacts:

### Reproducibility Verification
- [ ] Produces `experiments/runs/<run_id>/manifest.json` with commit hash and seeds.
- [ ] Does not overwrite any prior experiment run directory.
