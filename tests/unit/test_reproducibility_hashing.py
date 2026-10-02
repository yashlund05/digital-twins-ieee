"""tests/unit/test_reproducibility_hashing.py — Unit tests for cryptographic hashing utils."""

import numpy as np
import pandas as pd

from src.reproducibility.hashing import (
    hash_bytes,
    hash_dataframe,
    hash_dict,
    hash_directory,
    hash_file,
    hash_numpy_array,
)


def test_hash_bytes():
    h1 = hash_bytes(b"hello world")
    h2 = hash_bytes(b"hello world")
    h3 = hash_bytes(b"different content")

    assert isinstance(h1, str)
    assert len(h1) == 64
    assert h1 == h2
    assert h1 != h3


def test_hash_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("reproducibility test content", encoding="utf-8")

    h = hash_file(f)
    assert isinstance(h, str)
    assert len(h) == 64
    assert h == hash_bytes(b"reproducibility test content")


def test_hash_numpy_array():
    arr1 = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    arr2 = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    arr3 = np.array([1.0, 2.0, 3.0001], dtype=np.float64)

    h1 = hash_numpy_array(arr1)
    h2 = hash_numpy_array(arr2)
    h3 = hash_numpy_array(arr3)

    assert h1 == h2
    assert h1 != h3


def test_hash_dataframe():
    df1 = pd.DataFrame({"a": [1, 2], "b": [3.5, 4.5]})
    df2 = pd.DataFrame({"a": [1, 2], "b": [3.5, 4.5]})
    df3 = pd.DataFrame({"a": [1, 3], "b": [3.5, 4.5]})

    assert hash_dataframe(df1) == hash_dataframe(df2)
    assert hash_dataframe(df1) != hash_dataframe(df3)


def test_hash_dict():
    d1 = {"z": 100, "a": "apple", "m": [1, 2, 3]}
    d2 = {"a": "apple", "m": [1, 2, 3], "z": 100}
    d3 = {"a": "apple", "m": [1, 2, 4], "z": 100}

    assert hash_dict(d1) == hash_dict(d2)
    assert hash_dict(d1) != hash_dict(d3)


def test_hash_directory(tmp_path):
    d = tmp_path / "test_dir"
    d.mkdir()
    (d / "file_a.txt").write_text("aaa", encoding="utf-8")
    (d / "file_b.txt").write_text("bbb", encoding="utf-8")

    hashes = hash_directory(d)
    assert "file_a.txt" in hashes
    assert "file_b.txt" in hashes
    assert len(hashes["file_a.txt"]) == 64
