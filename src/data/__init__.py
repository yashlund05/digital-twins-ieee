"""
data — Data pipeline module.

Handles loading, preprocessing, mapping, synthetic anomaly injection,
and temporal splitting of the hybrid simulation dataset used in
Digital Twin synchronization staleness experiments.

NOTE: This module works with a hybrid simulation dataset.
Pecan Street load profiles are mapped to the IEEE 33-bus topology.
The resulting dataset is NOT real field measurements of the IEEE feeder.
"""

from src.data.anomaly_injector import inject_synthetic_anomalies
from src.data.loader import generate_benchmark_residential_traces, load_pecan_street_csv
from src.data.mapper import IEEE_33_BENCHMARK_LOADS, map_homes_to_ieee33
from src.data.pipeline import run_pipeline
from src.data.preprocessor import (
    clean_and_resample,
    extract_lag_features,
    extract_temporal_features,
    fit_and_apply_normalization,
)
from src.data.schema import (
    AnomalyEvent,
    BusMappingInfo,
    DataPipelineManifest,
    MappingConfigSummary,
    NormalizationParameters,
    TemporalSplitIndices,
)
from src.data.splitter import compute_temporal_splits, get_split_date_ranges

__all__ = [
    "load_pecan_street_csv",
    "generate_benchmark_residential_traces",
    "clean_and_resample",
    "extract_temporal_features",
    "extract_lag_features",
    "fit_and_apply_normalization",
    "IEEE_33_BENCHMARK_LOADS",
    "map_homes_to_ieee33",
    "inject_synthetic_anomalies",
    "compute_temporal_splits",
    "get_split_date_ranges",
    "run_pipeline",
    "AnomalyEvent",
    "BusMappingInfo",
    "MappingConfigSummary",
    "TemporalSplitIndices",
    "NormalizationParameters",
    "DataPipelineManifest",
]
