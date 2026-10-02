"""src/reproducibility/artifact_integrity.py — Artifact integrity and corruption detection.

Audits experiment outputs for missing files, corrupted JSON/CSV/parquet data,
hash mismatches, and condition coverage completeness per Section 11.
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.reproducibility.hashing import hash_file


def verify_file_parseable(filepath: Path) -> tuple[bool, str]:
    """Verify that a data file can be parsed without structural corruption."""
    suffix = filepath.suffix.lower()
    try:
        if suffix == ".json":
            with open(filepath, encoding="utf-8") as f:
                json.load(f)
        elif suffix == ".csv":
            df = pd.read_csv(filepath)
            if df.empty:
                return False, "CSV file is empty"
        elif suffix in [".parquet", ".pq"]:
            df = pd.read_parquet(filepath)
            if df.empty:
                return False, "Parquet file is empty"
        elif suffix in [".yaml", ".yml"]:
            import yaml

            with open(filepath, encoding="utf-8") as f:
                yaml.safe_load(f)
        return True, "valid"
    except Exception as e:
        return False, str(e)


def verify_artifacts(
    run_dir: Path | str,
    expected_files: list[str] | None = None,
    expected_hashes: dict[str, str] | None = None,
    expected_condition_count: int | None = None,
    condition_column: str = "condition_id",
) -> dict[str, Any]:
    """Perform comprehensive integrity and non-corruption audit of an experiment run directory.

    Args:
        run_dir: Path to the target experiment run directory.
        expected_files: Optional list of relative file paths required to exist.
        expected_hashes: Optional mapping of relative file paths to expected SHA-256 hashes.
        expected_condition_count: Optional expected number of unique conditions in comparison.csv.
        condition_column: Column name identifying distinct conditions.

    Returns:
        Structured integrity report dictionary.
    """
    base = Path(run_dir)
    if not base.is_dir():
        return {
            "status": "FAIL",
            "directory_exists": False,
            "errors": [f"Run directory does not exist: {base}"],
        }

    report: dict[str, Any] = {
        "run_dir": str(base),
        "directory_exists": True,
        "total_files_checked": 0,
        "missing_files": [],
        "corrupted_files": {},
        "hash_mismatches": {},
        "condition_check": "NOT_CHECKED",
        "errors": [],
        "all_valid": True,
    }

    # 1. Check expected files existence
    if expected_files:
        for f_name in expected_files:
            target = base / f_name
            if not target.is_file():
                report["missing_files"].append(f_name)
                report["all_valid"] = False

    # 2. Check file integrity & readability
    for item in base.glob("**/*"):
        if item.is_file() and item.suffix.lower() in [".json", ".csv", ".parquet", ".yaml", ".yml"]:
            report["total_files_checked"] += 1
            rel = item.relative_to(base).as_posix()
            valid, msg = verify_file_parseable(item)
            if not valid:
                report["corrupted_files"][rel] = msg
                report["all_valid"] = False

    # 3. Check cryptographic hash matches if supplied
    if expected_hashes:
        for f_rel, exp_hash in expected_hashes.items():
            f_path = base / f_rel
            if f_path.is_file():
                actual_hash = hash_file(f_path)
                if actual_hash != exp_hash:
                    report["hash_mismatches"][f_rel] = {
                        "expected": exp_hash,
                        "actual": actual_hash,
                    }
                    report["all_valid"] = False

    # 4. Check condition coverage completeness if comparison.csv is present
    comp_file = base / "comparison.csv"
    if comp_file.is_file() and expected_condition_count is not None:
        try:
            df = pd.read_csv(comp_file)
            if condition_column in df.columns:
                found_count = len(df[condition_column].unique())
                report["conditions_found"] = found_count
                report["conditions_expected"] = expected_condition_count
                if found_count == expected_condition_count:
                    report["condition_check"] = "PASS"
                else:
                    report["condition_check"] = "FAIL"
                    report["errors"].append(
                        f"Expected {expected_condition_count} conditions, found {found_count}"
                    )
                    report["all_valid"] = False
        except Exception as e:
            report["condition_check"] = "ERROR"
            report["errors"].append(f"Failed parsing comparison.csv for condition check: {e}")
            report["all_valid"] = False

    report["status"] = "PASS" if report["all_valid"] else "FAIL"
    return report
