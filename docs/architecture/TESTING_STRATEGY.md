# Testing Strategy

> **Component:** tests/ & CI Quality Assurance
> **Version:** 1.0.0 — September 2026
> **Status:** Specification (Phase 0) — enforced across all subsequent phases

---

## Overview

In academic research software, code defects directly corrupt scientific conclusions. A subtle indexing error, silent NaN propagation, or unnoticed temporal data leakage can invalidate an entire paper.

This testing strategy defines the verification architecture for the repository. Every subsystem has explicit testing requirements that must pass before any experimental run is considered scientifically valid.

```
       +---------------------------------------------+
       |             Validation Tests                |
       |  (tests/validation/ - Experiment Integrity) |
       +---------------------------------------------+
                              ^
                              |
       +---------------------------------------------+
       |             Regression Tests                |
       |   (tests/regression/ - Manifest & Seeds)    |
       +---------------------------------------------+
                              ^
                              |
       +---------------------------------------------+
       |             Integration Tests               |
       |  (tests/integration/ - Inter-Module Flows)  |
       +---------------------------------------------+
                              ^
                              |
       +---------------------------------------------+
       |                Unit Tests                   |
       |     (tests/unit/ - Isolated Functions)      |
       +---------------------------------------------+
```

---

## Testing Principles

1. **Tests Are Written Alongside Implementation:** No module code is committed without corresponding unit tests.
2. **Never Weaken Tests to Pass:** If an existing test fails after a change, that failure is an error signal. Tests are never modified, skipped, or deleted to produce a passing build.
3. **Deterministic Execution:** All tests must produce identical results regardless of execution order or host platform. Tests requiring randomness must explicitly set fixed seeds.
4. **Fast Feedback Loop:** The unit test suite must execute in under 30 seconds to support continuous test-driven iteration.
5. **Separation of Concerns:** Unit tests mock external dependencies (such as raw dataset files or long-running OpenDSS simulations); integration tests verify actual component hand-offs; validation tests enforce scientific protocol rules.

---

## Test Directory Structure

```
tests/
├── conftest.py                # Shared pytest fixtures, mock data, synthetic signals
├── unit/                      # Isolated module unit tests
│   ├── test_data.py           # Ingestion, preprocessing, and temporal splitting
│   ├── test_digital_twin.py   # OpenDSS interface, state representations, power flow
│   ├── test_synchronization.py# Staleness engine, buffers, AoI calculation
│   ├── test_forecasting.py    # Baseline, XGBoost, and LSTM estimators
│   ├── test_anomaly_detection.py # Isolation Forest and LSTM Autoencoder
│   ├── test_residuals.py      # DT residual calculation and drift tracking
│   ├── test_evaluation.py     # Pure evaluation metrics (RMSE, MAE, AUC, F1)
│   ├── test_statistics.py     # Hypothesis testing, Wilcoxon, Friedman tests
│   └── test_utils.py          # Config parsing, logging, and seed utilities
├── integration/               # Cross-module communication tests
│   ├── test_data_to_twin.py   # Data pipeline feeding OpenDSS power flow
│   ├── test_sync_to_models.py # Synchronization engine feeding forecasting & anomaly modules
│   ├── test_pipeline_flow.py  # End-to-end dry run (E1 verification run)
│   └── test_cli.py            # CLI entry points and argument parsing
├── validation/                # Research integrity and protocol assertions
│   ├── test_no_data_leakage.py# Temporal ordering: test set strictly succeeds train set
│   ├── test_unsupervised_integrity.py # Anomaly detectors never receive labels during training
│   ├── test_staleness_bounds.py# Synchronization staleness strictly respects configured intervals
│   └── test_configs.py        # All YAML configs validate against Pydantic schemas
└── regression/                # Historical benchmark and seed repeatability tests
    ├── test_seed_repeatability.py # Identical seed yields bitwise identical outputs
    └── test_manifest_verification.py # Run manifests record complete environment hash
```

---

## Subsystem-Specific Testing Requirements

### 1. Synchronization Engine (`src/synchronization/`)

The synchronization engine is the experimental independent variable. Test coverage must exceed 90%.

- **Monotonic Timestamp Verification:** `t_dt` must never precede a previously applied update timestamp.
- **Staleness Upper and Lower Bounds:** For a configured interval $\Delta t$, the staleness $S(t)$ must satisfy $0 \le S(t) < \Delta t + \epsilon$ under normal transmission.
- **Missed Update Behavior:** Verify that missed updates trigger the configured policy (`hold_last_state` or `extrapolate`) without runtime crashes or NaN emissions.
- **Age of Information (AoI) Tracking:** AoI calculation must be verified against analytical step functions.
- **Buffer Invariance:** Buffer overflow/underflow cases must fail explicitly with structured exceptions rather than silent data dropping.

### 2. Data Pipeline & Temporal Leakage (`src/data/`)

- **Temporal Order Strictness:** For train split $[t_0, t_1]$, validation split $[t_2, t_3]$, and test split $[t_4, t_5]$, tests must assert $t_0 < t_1 < t_2 < t_3 < t_4 < t_5$.
- **No Future Information in Scalers:** Standardizers and min-max scalers must be fit **exclusively** on the training split and applied to validation/test splits.
- **Node Allocation Consistency:** All 33 buses in the IEEE feeder must have consistent load allocations across all splits.
- **Hybrid Dataset Metadata:** Tests must verify that every generated dataset artifact contains the hybrid simulation disclaimer metadata.

### 3. OpenDSS Digital Twin Wrapper (`src/digital_twin/`)

- **Power Flow Convergence:** Verify convergence checks detect ill-conditioned networks and non-convergent iterations.
- **Physical Feasibility Assertions:** Bus voltage magnitudes must be strictly positive and within physical bounds ($0.8 \le V_{pu} \le 1.2$ during normal operations).
- **Isolation of Simulation State:** Each test must run in a clean OpenDSS engine instance to avoid state pollution between runs.

### 4. Forecasting & Anomaly Detection (`src/forecasting/`, `src/anomaly_detection/`)

- **Unsupervised Label Isolation:** Unit tests must confirm that training methods for `IsolationForest` and `LSTMAutoencoder` do not accept or consume ground-truth anomaly labels.
- **Deterministic Predictions:** Given a fixed model seed and input tensor, model predictions must match across repeated calls.
- **Output Shape Invariance:** Model outputs must conform strictly to expected tensor shapes across variable batch sizes.
- **Zero Division Safety:** Anomaly threshold estimators and error scalers must handle zero-variance signals gracefully without `ZeroDivisionError` or infinite loss.

### 5. Residual Engine (`src/residuals/`)

- **Residual Equation Invariance:** $r(t) = y_{observed}(t) - \hat{y}_{DT}(t)$ must match exact floating-point arithmetic within machine precision.
- **Staleness-Induced Drift:** Verify that when physical state changes while DT state is held static, residual magnitude increases monotonically with physical deviation.

### 6. Evaluation & Statistical Metrics (`src/evaluation/`, `src/statistics/`)

- **Edge Case Protection:**
  - MAPE calculation must apply an epsilon floor ($\epsilon = 10^{-6}$) to prevent division by zero at near-zero loads.
  - AUC-ROC computation must raise a clean, documented exception if input contains only a single class, rather than crashing silently.
- **Pure Functions:** Evaluation functions must be pure: no mutation of input arrays or global state.
- **Statistical Test Validity:** Wilcoxon signed-rank and Friedman test wrappers must correctly reject identical distributions ($p > 0.05$) and detect significant differences ($p < 0.001$).

---

## Pytest Configuration & Markers

Pytest configuration is declared in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "unit: Isolated unit tests (fast, no external dependencies)",
    "integration: Cross-component integration tests",
    "validation: Research integrity and protocol verification tests",
    "regression: Reproducibility and historical baseline checks",
    "slow: Tests taking > 5 seconds (skipped during fast pre-commit)",
]
addopts = "-v --strict-markers -ra"
```

### Running Tests

```bash
# Run all tests
make test
# Or directly:
pytest

# Run fast unit tests only
pytest -m unit

# Run validation tests (must pass before running any experiment)
pytest -m validation

# Run with coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html
```

---

## Continuous Integration (CI) Quality Gates

Pull requests must satisfy all of the following quality gates before merging into `develop` or `main`:

1. **Linting and Formatting:** `ruff check .` and `black --check .` return 0 exit code.
2. **Type Checking:** `mypy src/` returns 0 exit code with no type errors.
3. **Test Suite:** 100% of unit, integration, and validation tests pass.
4. **Code Coverage:** Line coverage on `src/` must be $\ge 80\%$, with $\ge 90\%$ on `src/synchronization/` and `src/evaluation/`.
5. **No Tracked Run Overwrites:** CI verifies that no files inside `experiments/runs/` are modified in the PR.
