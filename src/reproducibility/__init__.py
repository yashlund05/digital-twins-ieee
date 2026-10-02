"""src/reproducibility — Cryptographic reproducibility, verification, and audit subsystem."""

from src.reproducibility.artifact_integrity import verify_artifacts, verify_file_parseable
from src.reproducibility.comparator import (
    compare_arrays,
    compare_metrics,
    compare_prediction_series,
)
from src.reproducibility.config_hash import canonicalize_value, compute_config_hash
from src.reproducibility.environment import capture_environment_metadata, get_git_provenance
from src.reproducibility.hashing import (
    hash_bytes,
    hash_dataframe,
    hash_dict,
    hash_directory,
    hash_file,
    hash_numpy_array,
)
from src.reproducibility.run_manifest import create_reproducibility_manifest
from src.reproducibility.verifier import verify_historical_benchmarks

__all__ = [
    "hash_bytes",
    "hash_file",
    "hash_directory",
    "hash_numpy_array",
    "hash_dataframe",
    "hash_dict",
    "canonicalize_value",
    "compute_config_hash",
    "capture_environment_metadata",
    "get_git_provenance",
    "verify_file_parseable",
    "verify_artifacts",
    "compare_arrays",
    "compare_metrics",
    "compare_prediction_series",
    "create_reproducibility_manifest",
    "verify_historical_benchmarks",
]
