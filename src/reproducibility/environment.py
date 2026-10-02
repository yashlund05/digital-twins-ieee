"""src/reproducibility/environment.py — System environment and hardware provenance capture.

Captures Python runtime, operating system, core numerical and ML package versions,
CUDA availability, CPU architecture, and git repository state per Section 9.
"""

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import subprocess
import sys
from typing import Any


def get_installed_package_version(package_name: str) -> str:
    """Return installed version of a package, or 'not_installed'."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "not_installed"


def get_git_provenance(repo_path: str = ".") -> dict[str, Any]:
    """Capture current git commit, active branch, and working-tree cleanliness."""
    provenance = {
        "commit": "unknown",
        "branch": "unknown",
        "is_clean": False,
    }
    try:
        res_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        provenance["commit"] = res_commit.stdout.strip()
    except Exception:
        pass

    try:
        res_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        provenance["branch"] = res_branch.stdout.strip()
    except Exception:
        pass

    try:
        res_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        provenance["is_clean"] = len(res_status.stdout.strip()) == 0
    except Exception:
        pass

    return provenance


def capture_environment_metadata(repo_path: str = ".") -> dict[str, Any]:
    """Collect comprehensive hardware, operating system, runtime, and dependency versions.

    Degrades gracefully if optional packages or hardware interfaces (like CUDA) are unavailable.
    """
    tracked_packages = [
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "xgboost",
        "torch",
        "opendssdirect.py",
        "pydantic",
        "pyyaml",
        "matplotlib",
        "click",
        "pytest",
    ]

    pkg_versions = {pkg: get_installed_package_version(pkg) for pkg in tracked_packages}

    # CUDA and PyTorch device details
    cuda_available = False
    cuda_version = "none"
    device_name = "CPU"
    if importlib.util.find_spec("torch") is not None:
        try:
            import torch

            cuda_available = torch.cuda.is_available()
            if cuda_available:
                cuda_version = str(torch.version.cuda)
                device_name = torch.cuda.get_device_name(0)
        except Exception:
            pass

    env_dict = {
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count() or 1,
        "cuda_available": cuda_available,
        "cuda_version": cuda_version,
        "primary_device": device_name,
        "packages": pkg_versions,
        "git": get_git_provenance(repo_path),
    }

    # Deterministic fingerprint of the environment
    env_str = json.dumps(
        {
            "python": env_dict["python_version"],
            "os": env_dict["os_name"],
            "arch": env_dict["architecture"],
            "packages": env_dict["packages"],
            "git_commit": env_dict["git"]["commit"],
        },
        sort_keys=True,
    )
    env_dict["environment_hash"] = hashlib.sha256(env_str.encode("utf-8")).hexdigest()

    return env_dict
