"""src/audit/environment_auditor.py — Reproducibility Environment Snapshot and Command Manifest.

Captures system specifications, Python runtime, pip dependencies, Git metadata,
SHA-256 hash manifests, and deterministic command execution steps per Section 17 & 18.
"""

import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.reproducibility.hashing import hash_directory
from src.utils.io import save_json
from src.utils.logging import get_logger

logger = get_logger("audit.environment_auditor")


class EnvironmentSnapshotAuditor:
    """Captures execution environment and produces reproducibility artifacts."""

    def __init__(self, workspace_root: Path | str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def capture_environment_metadata(self) -> dict[str, Any]:
        """Capture OS, Python runtime, and hardware platform info."""
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "python_executable": sys.executable,
        }

    def capture_git_state(self) -> dict[str, Any]:
        """Capture local git branch, HEAD commit, and status without leaking secrets."""
        state = {
            "branch": "UNKNOWN",
            "commit_head": "UNKNOWN",
            "is_clean": False,
            "status_text": "",
        }
        try:
            b_out = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=self.workspace_root,
                text=True,
            ).strip()
            state["branch"] = b_out

            c_out = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.workspace_root,
                text=True,
            ).strip()
            state["commit_head"] = c_out

            s_out = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=self.workspace_root,
                text=True,
            ).strip()
            state["is_clean"] = len(s_out) == 0
            state["status_text"] = s_out if s_out else "CLEAN"
        except Exception as e:
            logger.warning(f"Could not read git state: {e}")
        return state

    def capture_dependencies(self) -> str:
        """Capture installed package dependencies via pip freeze."""
        try:
            out = subprocess.check_output(
                [sys.executable, "-m", "pip", "freeze"],
                cwd=self.workspace_root,
                text=True,
            )
            return out
        except Exception as e:
            logger.warning(f"Could not capture dependencies: {e}")
            return f"ERROR: {e}"

    def build_command_manifest(self) -> dict[str, Any]:
        """Build deterministic command list for reproducing all phases."""
        return {
            "title": "Deterministic Research Reproduction Command Manifest",
            "specification": "IEEE Transactions on Smart Grid Paper Package",
            "commands": [
                {
                    "step": 1,
                    "description": "Install Python dependencies",
                    "command": "python -m pip install -e .",
                },
                {
                    "step": 2,
                    "description": "Verify environment and historical artifacts",
                    "command": "python -m src.cli verify-artifacts --run-dir experiments/runs/E11_PHASE11_20261002",
                },
                {
                    "step": 3,
                    "description": "Run Phase 12 publication artifact build",
                    "command": "python -m src.cli build-publication-artifacts --strict",
                },
                {
                    "step": 4,
                    "description": "Assemble Phase 13 IEEE TSG manuscript and run scientific audits",
                    "command": "python -m src.cli assemble-manuscript --strict",
                },
                {
                    "step": 5,
                    "description": "Execute Phase 14 final scientific audit and release validation",
                    "command": "python -m src.cli run-final-audit --strict",
                },
                {
                    "step": 6,
                    "description": "Execute full test suite regression",
                    "command": "python -m pytest tests/ -q",
                },
            ],
        }

    def generate_reproducibility_package(self, output_dir: Path) -> dict[str, Any]:
        """Generate all reproducibility documents and hash manifests in reproducibility/."""
        repro_dir = Path(output_dir) / "reproducibility"
        repro_dir.mkdir(parents=True, exist_ok=True)

        env_meta = self.capture_environment_metadata()
        git_state = self.capture_git_state()
        deps = self.capture_dependencies()
        cmd_manifest = self.build_command_manifest()

        # Write environment.txt
        env_lines = [
            f"OS: {env_meta['platform']} ({env_meta['machine']})",
            f"Processor: {env_meta['processor']}",
            f"Python Runtime: {env_meta['python_version']}",
            f"Python Path: {env_meta['python_executable']}",
        ]
        (repro_dir / "environment.txt").write_text("\n".join(env_lines), encoding="utf-8")

        # Write git_state.txt
        git_lines = [
            f"Branch: {git_state['branch']}",
            f"Commit HEAD: {git_state['commit_head']}",
            f"Working Tree Clean: {git_state['is_clean']}",
            f"Porcelain Status:\n{git_state['status_text']}",
        ]
        (repro_dir / "git_state.txt").write_text("\n".join(git_lines), encoding="utf-8")

        # Write dependency_snapshot.txt
        (repro_dir / "dependency_snapshot.txt").write_text(deps, encoding="utf-8")

        # Write command_manifest.json
        save_json(cmd_manifest, repro_dir / "command_manifest.json")

        # Write README.md for reproducibility
        repro_readme = """# Reproducibility Package

This directory contains deterministic reproducibility specifications and environment snapshots
for the research paper:

> **Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin**

## Contents
- `environment.txt`: Operating system and Python runtime specifications.
- `dependency_snapshot.txt`: Complete package lock (`pip freeze`) capturing exact libraries.
- `git_state.txt`: Git branch, commit HEAD, and status.
- `command_manifest.json`: Step-by-step CLI commands required to verify and reproduce all results.
- `hash_manifest.json`: SHA-256 cryptographic hashes for generated artifacts.

## Quick Reproduction
```bash
python -m pip install -e .
python -m src.cli run-final-audit --strict
python -m pytest tests/ -q
```
"""
        (repro_dir / "README.md").write_text(repro_readme, encoding="utf-8")

        # Build hash manifest for output_dir
        hash_manifest = hash_directory(output_dir, recursive=True)
        save_json(hash_manifest, repro_dir / "hash_manifest.json")

        logger.info(f"Reproducibility package created at {repro_dir}")
        return {
            "environment": env_meta,
            "git_state": git_state,
            "commands": cmd_manifest,
            "total_hashes": len(hash_manifest),
        }
