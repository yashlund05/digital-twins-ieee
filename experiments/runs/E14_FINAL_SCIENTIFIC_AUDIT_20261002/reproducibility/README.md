# Reproducibility Package

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
