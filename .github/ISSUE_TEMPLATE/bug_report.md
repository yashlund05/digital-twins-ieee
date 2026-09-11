---
name: Bug Report
about: Report a defect, test failure, or unexpected behavior in repository code
title: "[BUG]: "
labels: ["bug"]
assignees: ""
---

### Affected Module
Select the primary module affected:
- [ ] `src/data/` (Data pipeline, Pecan Street mapping)
- [ ] `src/digital_twin/` (OpenDSS interface, IEEE 33-bus model)
- [ ] `src/synchronization/` (Staleness engine, AoI tracking)
- [ ] `src/forecasting/` (Load estimation models)
- [ ] `src/anomaly_detection/` (Unsupervised anomaly detectors)
- [ ] `src/residuals/` (Residual computation engine)
- [ ] `src/evaluation/` (Evaluation metrics)
- [ ] `src/statistics/` (Statistical tests)
- [ ] `src/experiments/` (Experiment runner)
- [ ] `src/cli/` or `src/utils/` (Infrastructure, config, CLI)
- [ ] Other / Configuration

### Bug Description
A clear and concise description of the bug.

### Steps to Reproduce
1. Execute command: `...`
2. Configuration used: `configs/...`
3. Error encountered: `...`

### Expected Behavior
A clear description of what you expected to happen.

### Actual Output / Stack Trace
```text
Paste terminal output, pytest failure log, or stack trace here
```

### Environment Information
- OS: [e.g. Windows 11, Ubuntu 22.04]
- Python Version: [e.g. 3.10.11]
- OpenDSSDirect Version: [e.g. 0.8.4]
- Commit Hash: [e.g. `git rev-parse --short HEAD`]

### Additional Context
Add any other context about the problem here (e.g., related experiment run, dataset split).
