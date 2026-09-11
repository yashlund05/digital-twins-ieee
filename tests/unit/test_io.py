"""Unit tests for I/O helpers in src/utils/io.py."""

from pathlib import Path
import pandas as pd
import pytest
from src.utils.io import (
    ensure_dir,
    load_json,
    load_parquet,
    load_yaml_file,
    save_json,
    save_parquet,
    save_yaml,
)


@pytest.mark.unit
def test_ensure_dir(tmp_path: Path) -> None:
    """Verify recursive directory creation."""
    target = tmp_path / "deep" / "nested" / "output.csv"
    created = ensure_dir(target)
    assert created.is_dir()
    assert (tmp_path / "deep" / "nested").is_dir()


@pytest.mark.unit
def test_json_roundtrip(tmp_path: Path) -> None:
    """Verify JSON save and load consistency."""
    data = {"metric": "RMSE", "values": [0.12, 0.34, 0.56], "metadata": {"seed": 42}}
    file_path = tmp_path / "results" / "metrics.json"

    save_json(data, file_path)
    loaded = load_json(file_path)
    assert loaded == data


@pytest.mark.unit
def test_yaml_roundtrip(tmp_path: Path) -> None:
    """Verify YAML save and load consistency."""
    data = {"solver": {"backend": "opendss", "iterations": 100}}
    file_path = tmp_path / "configs" / "custom.yaml"

    save_yaml(data, file_path)
    loaded = load_yaml_file(file_path)
    assert loaded == data


@pytest.mark.unit
def test_parquet_roundtrip(tmp_path: Path) -> None:
    """Verify Parquet DataFrame save and load consistency."""
    df = pd.DataFrame({"bus_1": [1.0, 0.98, 0.99], "bus_2": [0.95, 0.94, 0.96]})
    file_path = tmp_path / "data" / "voltages.parquet"

    save_parquet(df, file_path)
    loaded = load_parquet(file_path)
    pd.testing.assert_frame_equal(loaded, df)
