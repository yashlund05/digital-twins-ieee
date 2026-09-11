"""Reproducibility utilities for experiment provenance and determinism.

Enforces deterministic seed configuration, environment state capture, git commit
tracking, and manifest generation per docs/methodology/REPRODUCIBILITY.md.
"""

import importlib.metadata
import os
import platform
import random
import subprocess
import sys
from datetime import datetime
from typing import Any

import numpy as np


def set_all_seeds(seed: int = 42) -> None:
    """Set random seeds across Python, NumPy, and PyTorch (if available).

    Parameters
    ----------
    seed : int
        Deterministic random seed.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)

    # PyTorch seed handling if present
    if "torch" in sys.modules or importlib.util.find_spec("torch") is not None:
        try:
            import torch

            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        except Exception:
            pass


def get_git_commit(repo_path: str = ".") -> str:
    """Retrieve the current HEAD git commit hash.

    Returns
    -------
    str
        Full SHA hash of current commit, or 'unknown' if not in a git repo.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def get_git_branch(repo_path: str = ".") -> str:
    """Retrieve the current active git branch name.

    Returns
    -------
    str
        Active branch name, or 'unknown'.
    """
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def is_git_clean(repo_path: str = ".") -> bool:
    """Check whether the working tree is clean with no uncommitted changes.

    Returns
    -------
    bool
        True if git status is clean, False otherwise.
    """
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return len(res.stdout.strip()) == 0
    except Exception:
        return False


def get_installed_packages(package_names: list[str] | None = None) -> dict[str, str]:
    """Capture version strings for key installed packages.

    Parameters
    ----------
    package_names : Optional[list[str]]
        Specific packages to query. Defaults to the core scientific stack.

    Returns
    -------
    dict[str, str]
        Dictionary mapping package name to version string.
    """
    if package_names is None:
        package_names = [
            "numpy",
            "pandas",
            "scipy",
            "scikit-learn",
            "xgboost",
            "opendssdirect.py",
            "pydantic",
            "pyyaml",
            "matplotlib",
            "click",
            "pytest",
            "ruff",
            "torch",
        ]

    installed = {}
    for pkg in package_names:
        try:
            installed[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            pass
    return installed


def get_environment_metadata() -> dict[str, Any]:
    """Capture complete machine and runtime software environment metadata.

    Returns
    -------
    dict[str, Any]
        Structured environment dictionary for inclusion in run manifests.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version.split()[0],
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "packages": get_installed_packages(),
    }


def create_manifest(
    experiment_id: str,
    run_id: str,
    config_file: str,
    config_version: str,
    random_seed: int,
    synchronization_interval: int,
    missed_update_policy: str,
    input_representation: str,
    model_type: str,
    dataset_version: str = "v1.0",
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an authoritative experiment manifest dictionary.

    Follows the schema specified in docs/methodology/REPRODUCIBILITY.md.
    """
    manifest = {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "status": "COMPLETED",
        "reproducibility": {
            "git_commit": get_git_commit(),
            "git_branch": get_git_branch(),
            "git_clean": is_git_clean(),
            "configuration_file": config_file,
            "configuration_version": config_version,
            "dataset_version": dataset_version,
            "random_seed": random_seed,
        },
        "model": {
            "type": model_type,
            "version": "1.0.0",
        },
        "synchronization": {
            "interval_seconds": synchronization_interval,
            "missed_update_policy": missed_update_policy,
        },
        "experiment_design": {
            "input_representation": input_representation,
            "model_type": model_type,
        },
        "environment": get_environment_metadata(),
    }

    if extra_metadata:
        manifest.update(extra_metadata)

    return manifest
