"""Unit tests for reproducibility utilities in src/utils/reproducibility.py."""

import random

import numpy as np
import pytest

from src.utils.reproducibility import (
    create_manifest,
    get_environment_metadata,
    get_git_branch,
    get_git_commit,
    is_git_clean,
    set_all_seeds,
)


@pytest.mark.unit
def test_set_all_seeds() -> None:
    """Verify seed locking guarantees identical random sequences."""
    set_all_seeds(42)
    val1 = random.random()
    arr1 = np.random.rand(5)

    set_all_seeds(42)
    val2 = random.random()
    arr2 = np.random.rand(5)

    assert val1 == val2
    np.testing.assert_array_equal(arr1, arr2)


@pytest.mark.unit
def test_get_git_info() -> None:
    """Verify git metadata retrieval functions return valid strings."""
    commit = get_git_commit()
    branch = get_git_branch()
    clean = is_git_clean()

    assert isinstance(commit, str)
    assert len(commit) > 0
    assert isinstance(branch, str)
    assert isinstance(clean, bool)


@pytest.mark.unit
def test_get_environment_metadata() -> None:
    """Verify environment capture includes python, platform, and package versions."""
    meta = get_environment_metadata()
    assert "python_version" in meta
    assert "os" in meta
    assert "packages" in meta
    assert isinstance(meta["packages"], dict)


@pytest.mark.unit
def test_create_manifest() -> None:
    """Verify manifest conforms to schema requirements in docs/methodology/REPRODUCIBILITY.md."""
    manifest = create_manifest(
        experiment_id="E5",
        run_id="E5_STALENESS_IF_RAW_SEED42_20261001",
        config_file="configs/experiments/e5_staleness_sweep.yaml",
        config_version="1.0.0",
        random_seed=42,
        synchronization_interval=60,
        missed_update_policy="hold_last_state",
        input_representation="raw",
        model_type="isolation_forest",
    )

    assert manifest["experiment_id"] == "E5"
    assert manifest["run_id"] == "E5_STALENESS_IF_RAW_SEED42_20261001"
    assert manifest["reproducibility"]["random_seed"] == 42
    assert manifest["synchronization"]["interval_seconds"] == 60
    assert manifest["environment"]["python_version"] is not None
