"""
src/residuals/__init__.py — Digital Twin Residual Engine package exports.

Computes physical-vs-virtual residuals: r_t = y_t - y_hat_DT,t.
Residuals serve as the alternative input representation for anomaly detectors
in the 2x2 design (Experiment E4) and are central to the raw-vs-residual
comparison under varying synchronization staleness (Experiment E5).
"""

from src.residuals.calculator import (
    ResidualResult,
    StateResidualResult,
    calculate_residual,
    calculate_state_residual,
)
from src.residuals.experiment_e4 import (
    get_baseline_dt_estimates,
    run_experiment_e4,
)
from src.residuals.features import (
    ResidualFeatureConfig,
    ResidualFeatureExtractor,
)
from src.residuals.normalizer import ResidualNormalizer

__all__ = [
    "calculate_residual",
    "calculate_state_residual",
    "ResidualResult",
    "StateResidualResult",
    "ResidualNormalizer",
    "ResidualFeatureConfig",
    "ResidualFeatureExtractor",
    "get_baseline_dt_estimates",
    "run_experiment_e4",
]
