"""src/reproducibility/run_manifest.py — Manifest generation with cryptographic provenance.

Generates schema-compliant run manifests with input/output artifact checksums,
configuration fingerprints, environment state, and explicit reproducibility statuses per Section 10.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from src.reproducibility.environment import capture_environment_metadata
from src.reproducibility.hashing import hash_directory

ReproducibilityStatus = Literal["PASS", "FAIL", "PARTIAL", "NOT_VERIFIED"]


def create_reproducibility_manifest(
    experiment_id: str,
    run_id: str,
    output_dir: Path | str,
    config_hash: str = "",
    dataset_hash: str = "",
    model_hash: str = "",
    seed: int = 42,
    conditions: list[Any] | None = None,
    input_artifacts: dict[str, str] | None = None,
    reproducibility_status: ReproducibilityStatus = "NOT_VERIFIED",
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct and serialize a comprehensive Phase 11 experiment execution manifest.

    Args:
        experiment_id: Identifier of the experiment (e.g. 'E7', 'E11').
        run_id: Unique run folder name.
        output_dir: Directory where outputs are located.
        config_hash: Canonical SHA-256 fingerprint of the experiment configuration.
        dataset_hash: Checksum of the input dataset.
        model_hash: Checksum of the model checkpoints used.
        seed: Random seed.
        conditions: List of evaluated condition specifications.
        input_artifacts: Mapping of input paths to their SHA-256 hashes.
        reproducibility_status: Explicit outcome status ('PASS', 'FAIL', 'PARTIAL', 'NOT_VERIFIED').
        extra_metadata: Optional domain-specific metadata.

    Returns:
        The generated manifest dictionary.
    """
    out_path = Path(output_dir)
    env_meta = capture_environment_metadata()

    # Hash all generated output artifacts
    output_hashes = hash_directory(out_path, recursive=True)

    manifest: dict[str, Any] = {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "seed": seed,
        "config_hash": config_hash,
        "timestamp": datetime.now().isoformat(),
        "reproducibility_status": reproducibility_status,
        "reproducibility": {
            "git_commit": env_meta["git"]["commit"],
            "git_branch": env_meta["git"]["branch"],
            "git_dirty": not env_meta["git"]["is_clean"],
            "random_seed": seed,
            "config_hash": config_hash,
            "dataset_hash": dataset_hash,
            "model_hash": model_hash,
            "environment_hash": env_meta["environment_hash"],
        },
        "conditions_count": len(conditions) if conditions is not None else len(output_hashes),
        "conditions": conditions or [],
        "environment": env_meta,
        "input_artifacts": input_artifacts or {},
        "output_artifacts": output_hashes,
        "file_hashes": output_hashes,
    }

    manifest["metadata"] = extra_metadata or {}
    manifest["extra_metadata"] = extra_metadata or {}

    manifest_file = out_path / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest
