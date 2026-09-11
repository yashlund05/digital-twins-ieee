# Experiment Configurations

This directory contains YAML configuration files for each experiment.

## Naming Convention

```
e<N>_<short_description>.yaml
```

Examples:
- `e1_dt_validation.yaml`
- `e2_load_estimation_baselines.yaml`
- `e3_anomaly_detection_baselines.yaml`
- `e4_raw_vs_residual.yaml`
- `e5_staleness_sweep.yaml`
- `e6_degradation_analysis.yaml`
- `e7_missed_update_transient.yaml`

## Structure

Each experiment config must include:

```yaml
experiment:
  id: E5
  name: staleness_sweep
  description: "..."
  seed: 42
  version: "1.0.0"

# Plus experiment-specific overrides of base configs
```

## Rules

- Experiment configurations are write-once after a run begins
- Do not modify a config that has been used for a completed run
- Create a new config version instead
- Every config must have a unique `name` + `seed` + `version` combination
