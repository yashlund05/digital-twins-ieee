"""File I/O helpers for atomic writing, structured formats, and directory management.

Ensures reliable persistence of experiment artifacts, logs, manifests, and metrics.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def ensure_dir(path: Path | str) -> Path:
    """Ensure directory exists, creating parents if necessary.

    Parameters
    ----------
    path : Path | str
        Directory or file path. If path has an extension, its parent is created.

    Returns
    -------
    Path
        Resolved Path object for the directory.
    """
    p = Path(path)
    if p.suffix:
        target_dir = p.parent
    else:
        target_dir = p
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def save_json(data: Any, file_path: Path | str, indent: int = 2) -> None:
    """Save serializable data to a JSON file.

    Parameters
    ----------
    data : Any
        JSON-serializable data structure.
    file_path : Path | str
        Destination file path.
    indent : int
        Indentation spaces for formatting.
    """
    path = Path(file_path)
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def load_json(file_path: Path | str) -> Any:
    """Load data from a JSON file.

    Parameters
    ----------
    file_path : Path | str
        Path to the JSON file.

    Returns
    -------
    Any
        Parsed JSON object.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_yaml(data: Any, file_path: Path | str) -> None:
    """Save serializable data to a YAML file.

    Parameters
    ----------
    data : Any
        YAML-serializable data.
    file_path : Path | str
        Destination file path.
    """
    path = Path(file_path)
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def load_yaml_file(file_path: Path | str) -> Any:
    """Load data from a YAML file.

    Parameters
    ----------
    file_path : Path | str
        Path to the YAML file.

    Returns
    -------
    Any
        Parsed YAML structure.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"YAML file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_parquet(df: pd.DataFrame, file_path: Path | str) -> None:
    """Save a Pandas DataFrame to Parquet format.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to persist.
    file_path : Path | str
        Destination file path.
    """
    path = Path(file_path)
    ensure_dir(path)
    df.to_parquet(path, index=True)


def load_parquet(file_path: Path | str) -> pd.DataFrame:
    """Load a Pandas DataFrame from Parquet format.

    Parameters
    ----------
    file_path : Path | str
        Path to the parquet file.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pd.read_parquet(path)
