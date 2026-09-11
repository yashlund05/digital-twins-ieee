"""
experiments — Experiment Orchestration

Orchestrates the end-to-end experiment pipeline:
- Staleness sweep (E5)
- Degradation analysis (E6)
- Missed-update transient analysis (E7)

All experiments are driven by configuration files in configs/experiments/.
Every run produces a unique run_id and stores its manifest.
"""
