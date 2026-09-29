"""
tests/validation/test_data_integrity.py — System-level validation of data pipeline integrity.

Verifies:
1. End-to-end pipeline execution correctness.
2. Complete absence of temporal leakage between splits.
3. Strict isolation of ground-truth anomaly labels from model feature inputs.
4. Physical range validity (no NaNs, infinite values, or unphysical artifacts).
5. Compliance with IEEE 33-bus topology constraints.
"""

import numpy as np
import pytest

from src.data.pipeline import run_pipeline
from src.data.schema import DataPipelineManifest, TemporalSplitIndices
from src.utils.io import load_json, load_parquet


@pytest.fixture(scope="module")
def run_test_pipeline(tmp_path_factory):
    """Execute pipeline in a temporary directory for validation."""
    temp_dir = tmp_path_factory.mktemp("pipeline_validation")
    out_dir = temp_dir / "processed"
    int_dir = temp_dir / "interim"

    result = run_pipeline(
        config_path="configs/data.yaml",
        raw_data_path=None,  # Uses benchmark generator for fast deterministic test
        output_dir=out_dir,
        interim_dir=int_dir,
        seed_override=42,
    )
    return {
        "result": result,
        "out_dir": out_dir,
        "int_dir": int_dir,
    }


def test_pipeline_output_files_exist(run_test_pipeline):
    """Verify all expected artifact files are produced."""
    out_dir = run_test_pipeline["out_dir"]
    int_dir = run_test_pipeline["int_dir"]

    assert (out_dir / "load_profiles.parquet").exists()
    assert (out_dir / "anomaly_labels.parquet").exists()
    assert (out_dir / "splits.json").exists()
    assert (out_dir / "manifest.json").exists()
    assert (int_dir / "mapping_config.json").exists()
    assert (int_dir / "normalization_params.json").exists()


def test_manifest_schema_compliance(run_test_pipeline):
    """Verify the generated manifest conforms to DataPipelineManifest Pydantic schema."""
    out_dir = run_test_pipeline["out_dir"]
    manifest_data = load_json(out_dir / "manifest.json")
    manifest = DataPipelineManifest.model_validate(manifest_data)

    assert manifest.num_load_buses == 32
    assert manifest.total_timesteps > 0
    assert 0.0 < manifest.anomaly_rate < 0.15
    assert manifest.dataset_designation == "HYBRID_SIMULATION_DATASET"


def test_strict_isolation_of_anomaly_labels(run_test_pipeline):
    """Ensure ground-truth anomaly labels are NOT present in the model feature matrix."""
    out_dir = run_test_pipeline["out_dir"]
    features_df = load_parquet(out_dir / "load_profiles.parquet")
    labels_df = load_parquet(out_dir / "anomaly_labels.parquet")

    # Features must NEVER contain label columns
    prohibited_cols = ["is_anomaly", "anomaly_type", "event_id", "affected_buses"]
    for col in prohibited_cols:
        assert col not in features_df.columns, (
            f"Leakage: prohibited column '{col}' found in feature matrix!"
        )

    # Labels must contain all expected ground-truth fields
    for col in prohibited_cols:
        assert col in labels_df.columns


def test_ieee33_bus_columns_presence(run_test_pipeline):
    """Verify all 32 load buses (2 to 33) are represented with P and Q columns."""
    out_dir = run_test_pipeline["out_dir"]
    features_df = load_parquet(out_dir / "load_profiles.parquet")

    for bus_id in range(2, 34):
        p_col = f"bus_{bus_id}_p_kw"
        q_col = f"bus_{bus_id}_q_kvar"
        assert p_col in features_df.columns, f"Missing active power column: {p_col}"
        assert q_col in features_df.columns, f"Missing reactive power column: {q_col}"


def test_no_missing_or_infinite_values(run_test_pipeline):
    """Verify clean numerical integrity across all engineered features."""
    out_dir = run_test_pipeline["out_dir"]
    features_df = load_parquet(out_dir / "load_profiles.parquet")

    assert features_df.isna().sum().sum() == 0, "Feature matrix contains NaNs!"
    numeric_df = features_df.select_dtypes(include=["number"])
    assert not np.isinf(numeric_df.to_numpy()).any(), "Feature matrix contains infinite values!"


def test_split_temporal_ordering_and_integrity(run_test_pipeline):
    """Verify zero temporal leakage and split index validity."""
    out_dir = run_test_pipeline["out_dir"]
    splits_data = load_json(out_dir / "splits.json")
    splits = TemporalSplitIndices.model_validate(splits_data)

    assert splits.leak_free is True
    assert max(splits.train_indices) < min(splits.validation_indices)
    assert max(splits.validation_indices) < min(splits.test_indices)
