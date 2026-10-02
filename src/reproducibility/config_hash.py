"""src/reproducibility/config_hash.py — Canonical configuration fingerprinting.

Computes whitespace- and key-order-invariant canonical SHA-256 fingerprints
for experiment configurations to ensure semantic comparability.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


def canonicalize_value(val: Any) -> Any:
    """Recursively canonicalize configuration values for deterministic hashing.

    - Sorts dictionary keys.
    - Preserves list element order (scientifically significant in pipelines).
    - Normalizes floating point representations.
    - Unwraps Pydantic models.
    """
    if isinstance(val, BaseModel):
        val = val.model_dump()

    if isinstance(val, dict):
        return {str(k): canonicalize_value(v) for k, v in sorted(val.items())}
    elif isinstance(val, (list, tuple)):
        return [canonicalize_value(item) for item in val]
    elif isinstance(val, float):
        # Round near-integer floats or normalize representation
        if val.is_integer():
            return int(val)
        return round(val, 8)
    elif isinstance(val, (int, str, bool)) or val is None:
        return val
    else:
        return str(val)


def compute_config_hash(
    config: dict[str, Any] | BaseModel | Path | str, algorithm: str = "sha256"
) -> str:
    """Compute deterministic canonical hash of a configuration object or YAML file.

    Args:
        config: Configuration dictionary, Pydantic model, or path to YAML file.
        algorithm: Hash algorithm.

    Returns:
        Canonical SHA256 hex digest.
    """
    if isinstance(config, (str, Path)):
        p = Path(config)
        if p.is_file():
            with open(p, encoding="utf-8") as f:
                raw_cfg = yaml.safe_load(f)
        else:
            raw_cfg = yaml.safe_load(str(config))
    elif isinstance(config, BaseModel):
        raw_cfg = config.model_dump()
    elif isinstance(config, dict):
        raw_cfg = config
    else:
        raise TypeError(f"Unsupported config type: {type(config)}")

    canonical_obj = canonicalize_value(raw_cfg)
    canonical_json = json.dumps(canonical_obj, sort_keys=True, separators=(",", ":"))

    h = hashlib.new(algorithm)
    h.update(canonical_json.encode("utf-8"))
    return h.hexdigest()
