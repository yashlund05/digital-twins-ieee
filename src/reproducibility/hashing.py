"""src/reproducibility/hashing.py — Cryptographic data and artifact hashing utilities.

Provides SHA-256 cryptographic hashing for files, directories, numpy arrays,
pandas DataFrames, and Python dictionaries to ensure end-to-end data integrity.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """Compute cryptographic hash of raw bytes."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def hash_file(filepath: Path | str, algorithm: str = "sha256") -> str:
    """Compute cryptographic hash of a file on disk.

    Args:
        filepath: Path to the target file.
        algorithm: Hash algorithm name ('sha256' default, 'md5', 'sha1').

    Returns:
        Hexadecimal hash string, or empty string if file does not exist.
    """
    p = Path(filepath)
    if not p.is_file():
        return ""

    h = hashlib.new(algorithm)
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def hash_directory(
    dir_path: Path | str,
    pattern: str = "*",
    recursive: bool = True,
    algorithm: str = "sha256",
) -> dict[str, str]:
    """Compute individual file hashes for all matching files in a directory.

    Args:
        dir_path: Target directory path.
        pattern: Glob pattern to filter files.
        recursive: Whether to search recursively.
        algorithm: Hash algorithm.

    Returns:
        Dictionary mapping relative file paths to their SHA256 hex hashes.
    """
    base = Path(dir_path)
    if not base.is_dir():
        return {}

    glob_fn = base.rglob if recursive else base.glob
    hashes = {}
    for f in sorted(glob_fn(pattern)):
        if f.is_file():
            rel_path = f.relative_to(base).as_posix()
            hashes[rel_path] = hash_file(f, algorithm=algorithm)
    return hashes


def hash_numpy_array(arr: np.ndarray, algorithm: str = "sha256") -> str:
    """Compute deterministic cryptographic hash of a NumPy array's bytes."""
    h = hashlib.new(algorithm)
    # Include shape, dtype, and contiguous bytes
    h.update(str(arr.shape).encode("utf-8"))
    h.update(str(arr.dtype).encode("utf-8"))
    h.update(np.ascontiguousarray(arr).tobytes())
    return h.hexdigest()


def hash_dataframe(df: pd.DataFrame, algorithm: str = "sha256") -> str:
    """Compute deterministic cryptographic hash of a Pandas DataFrame."""
    h = hashlib.new(algorithm)
    # Include columns, dtypes, index, and serialized values
    h.update(json.dumps(list(df.columns)).encode("utf-8"))
    h.update(json.dumps([str(t) for t in df.dtypes]).encode("utf-8"))
    # Serializing via CSV buffer with fixed float precision ensures cross-version determinism
    csv_bytes = df.to_csv(index=False, float_format="%.8f").encode("utf-8")
    h.update(csv_bytes)
    return h.hexdigest()


def hash_dict(d: dict[str, Any], algorithm: str = "sha256") -> str:
    """Compute deterministic hash of a nested dictionary using sorted keys."""
    canon_json = json.dumps(d, sort_keys=True, separators=(",", ":"))
    h = hashlib.new(algorithm)
    h.update(canon_json.encode("utf-8"))
    return h.hexdigest()
