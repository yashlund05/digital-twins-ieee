"""
src/statistics — Joint statistical analysis, degradation modeling, and hypothesis testing.
"""

from src.statistics.bootstrap import (
    bootstrap_ci,
    bootstrap_difference_ci,
    bootstrap_slope_ci,
)
from src.statistics.degradation import (
    METRIC_DIRECTION,
    build_degradation_dataframe,
    compute_absolute_degradation,
    compute_normalized_degradation,
    compute_relative_degradation,
    get_metric_direction,
)
from src.statistics.effect_sizes import (
    compute_cliffs_delta,
    compute_cohens_d,
)
from src.statistics.hypothesis import (
    benjamini_hochberg_correction,
    paired_wilcoxon_test,
    test_differential_degradation_h3,
)
from src.statistics.regression import (
    fit_linear_regression,
    fit_log_linear_regression,
    fit_two_way_factorial_regression,
)
from src.statistics.analysis_runner import run_phase9_analysis
from src.statistics.multiseed import run_multiseed_analysis

__all__ = [
    "METRIC_DIRECTION",
    "get_metric_direction",
    "compute_absolute_degradation",
    "compute_relative_degradation",
    "compute_normalized_degradation",
    "build_degradation_dataframe",
    "fit_linear_regression",
    "fit_log_linear_regression",
    "fit_two_way_factorial_regression",
    "compute_cohens_d",
    "compute_cliffs_delta",
    "bootstrap_ci",
    "bootstrap_difference_ci",
    "bootstrap_slope_ci",
    "test_differential_degradation_h3",
    "paired_wilcoxon_test",
    "benjamini_hochberg_correction",
    "run_phase9_analysis",
    "run_multiseed_analysis",
]

