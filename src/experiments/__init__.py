"""src/experiments — Experiment Orchestration.

Orchestrates the end-to-end experiment pipeline:
- E1: Digital Twin Baseline Validation
- E2: Baseline Load Estimation
- E3: Baseline Anomaly Detection
- E4: Raw vs. Residual Inputs
- E5: Controlled Staleness Sweep
"""

from src.experiments.runner import run_experiment
from src.experiments.staleness_sweep import (
    E5ExperimentCoordinator,
    StalenessCondition,
    SynchronizationTrace,
    run_staleness_sweep,
    simulate_synchronization_trace,
)

__all__ = [
    "E5ExperimentCoordinator",
    "StalenessCondition",
    "SynchronizationTrace",
    "run_experiment",
    "run_staleness_sweep",
    "simulate_synchronization_trace",
]
