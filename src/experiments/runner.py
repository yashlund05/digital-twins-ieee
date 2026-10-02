"""src/experiments/runner.py — Unified experiment execution orchestrator.

Provides a single dispatching interface to execute configured experiments:
- E1: Digital Twin Baseline Validation
- E2: Baseline Load Estimation
- E3: Baseline Anomaly Detection
- E4: Raw vs. Residual Inputs
- E5: Controlled Synchronization Staleness Sweep
"""

from pathlib import Path
from typing import Any

from src.digital_twin.initializer import run_experiment_e1_validation
from src.experiments.staleness_sweep import run_staleness_sweep
from src.forecasting.experiment_e2 import run_experiment_e2
from src.residuals.experiment_e4 import run_experiment_e4
from src.utils.logging import get_logger

logger = get_logger("experiments.runner")


def run_experiment(
    experiment_id: str,
    seed: int = 42,
    output_base_dir: Path | str = "experiments/runs",
    **kwargs: Any,
) -> Path | dict[str, Any]:
    """Execute an experiment by ID.

    Args:
        experiment_id: Identifier (e.g., 'E1', 'E2', 'E4', 'E5').
        seed: Random seed for reproducibility.
        output_base_dir: Base directory for run artifacts.
        **kwargs: Additional experiment-specific arguments.

    Returns:
        Path to output directory (or results dict for E1).
    """
    exp_id = experiment_id.upper()
    logger.info(f"Dispatching experiment: {exp_id} (Seed: {seed})...")

    if exp_id in ["E1", "E1_DT_VALIDATION"]:
        return run_experiment_e1_validation(output_root=output_base_dir, seed=seed)
    elif exp_id in ["E2", "E2_LOAD_ESTIMATION"]:
        return run_experiment_e2(seed=seed, output_base_dir=output_base_dir)
    elif exp_id in ["E4", "E4_RAW_VS_RESIDUAL"]:
        return run_experiment_e4(seed=seed, output_base_dir=output_base_dir)
    elif exp_id in ["E5", "E5_STALENESS_SWEEP"]:
        config_path = kwargs.get("config_path", "configs/experiments/e5_staleness_sweep.yaml")
        return run_staleness_sweep(
            config_path=config_path,
            seed=seed,
            output_base_dir=output_base_dir,
            conditions_to_run=kwargs.get("conditions_to_run"),
        )
    else:
        raise ValueError(f"Unsupported experiment ID: '{experiment_id}'. Supported: E1, E2, E4, E5")
