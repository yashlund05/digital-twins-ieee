# Reproducibility Protocol

> **Version:** 1.0.0 — September 2026

---

## Principle

Every experiment in this repository must be reproducible from:
1. A configuration file
2. A random seed
3. A git commit hash
4. The specified dataset version

Notebook-only experiments are not considered reproducible.

---

## Experiment Manifest

Every experiment run produces a `manifest.json` at:
```
experiments/runs/<run_id>/manifest.json
```

### Manifest Schema

```json
{
  "experiment_id": "E5",
  "run_id": "E5_STALENESS_IF_RAW_SEED42_20261001",
  "timestamp": "2026-10-01T14:32:00+05:30",
  "status": "COMPLETED",

  "reproducibility": {
    "git_commit": "<full sha>",
    "git_branch": "experiment/e5-staleness-sweep",
    "git_clean": true,
    "configuration_file": "configs/experiments/e5_staleness_sweep.yaml",
    "configuration_version": "1.0.0",
    "dataset_version": "v1.0",
    "random_seed": 42
  },

  "model": {
    "type": "isolation_forest",
    "version": "1.0.0",
    "training_samples": null,
    "training_completed": null
  },

  "synchronization": {
    "interval_seconds": 300,
    "missed_update_policy": "hold_last_state",
    "sweep_level": 5
  },

  "experiment_design": {
    "input_representation": "raw",
    "detector": "isolation_forest",
    "forecasting_model": null
  },

  "environment": {
    "python_version": "3.11.5",
    "os": "Windows 11",
    "packages": {}
  },

  "hardware": {
    "cpu": null,
    "ram_gb": null,
    "gpu": null
  },

  "outputs": {
    "metrics_file": "metrics.json",
    "predictions_file": "predictions/anomaly_scores.parquet",
    "sync_log_file": "logs/sync_log.jsonl",
    "plots_dir": "plots/"
  }
}
```

---

## Run ID Convention

```
<EXPERIMENT_ID>_<DESCRIPTOR>_<MODEL>_<INPUT>_SEED<S>_<YYYYMMDD>

Examples:
E5_STALENESS_IF_RAW_SEED42_20261001
E5_STALENESS_LSTMAE_RESIDUAL_SEED42_20261001
E2_BASELINE_LSTM_RAW_SEED42_20260915
E3_BASELINE_LSTMAE_RESIDUAL_SEED42_20260920
E7_TRANSIENT_IF_RAW_SEED42_20261015
```

---

## Random Seed Policy

1. Seeds are set at the start of each experiment, before any stochastic operation
2. All seeds are recorded in the manifest
3. Seeds are never changed after an experiment run begins
4. Seeds are never selected by observing results
5. Multiple seeds for statistical validation are pre-registered before any run

```python
# Required seed initialization pattern
import random
import numpy as np


def set_all_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    # torch.manual_seed(seed)  # If PyTorch is used
    # tf.random.set_seed(seed)  # If TensorFlow is used
```

---

## Git State Requirements

- The git tree must be clean (no uncommitted changes to `src/`) before running any primary experiment
- The git commit hash is recorded in the manifest
- If running an experiment on a dirty tree, the manifest records `git_clean: false` and the run is flagged as preliminary

---

## Configuration Version Control

- All experiment configurations in `configs/experiments/` are committed to Git before the experiment runs
- A configuration file is never modified after a run that uses it has been committed
- New parameter settings create a new configuration file (e.g., `e5_staleness_sweep_v2.yaml`)

---

## Preventing Run Overwrites

The experiment runner must check whether a run with the same `run_id` already exists before starting. If it does, the runner exits with an error.

Runs are never deleted or overwritten, even if failed.

---

## Notebook Usage Policy

Notebooks are analysis and exploration tools ONLY:

| Allowed in notebooks | Not allowed in notebooks |
|---------------------|-------------------------|
| Consuming experiment results | Generating experiment results |
| Producing figures from artifacts | Training models |
| Exploratory data analysis | Defining data splits |
| Analysis of multiple runs | Creating primary metrics |

---

## Dataset Versioning

- The processed dataset is versioned (e.g., `v1.0`)
- The dataset version is recorded in the experiment manifest
- If the data pipeline changes, the dataset version increments
- Experiments from different dataset versions are not directly comparable

---

*Reproducibility Protocol v1.0.0 — Phase 0.*
