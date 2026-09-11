# CODEX.md — Codex-Style Agent Instructions

> Instructions for Codex-style coding agents operating in this research repository.
> Also read: `AGENTS.md` (general), `AI_RULES.md` (governance), `VIBECODING.md` (workflow).

---

## Implementation Discipline

### Minimal diffs
Produce the smallest correct change. Do not refactor adjacent code unless it directly affects correctness.

### Test-first behavior
Write the test before the implementation whenever possible.
If writing test-first is not feasible, write the test immediately after and include it in the same commit.

### No speculation
Implement only what is specified. Do not add "helpful" features, optimizations, or extensions not requested.

### No silent changes
Every behavioral change must be visible in the diff and explained in the commit message.

---

## Dependency Discipline

- Add dependencies to `pyproject.toml` only
- Never run `pip install X` without adding to `pyproject.toml`
- Justify every new dependency in the commit or PR description
- Prefer standard library solutions for simple tasks
- Do not duplicate functionality already provided by listed dependencies

---

## Error Handling

- Use explicit exception types, not bare `except:`
- Log errors with context using the project logger (`src/utils/logging.py`)
- Fail loudly for configuration errors — invalid configs must raise immediately
- Never silently skip over synchronization or data errors in experiment code
- For experiments: an error in one run should not silently corrupt subsequent runs

---

## Reproducibility Requirements

Every experiment function MUST:

```python
# 1. Accept a seed parameter
def run_experiment(config: ExperimentConfig, seed: int) -> ExperimentResult: ...


# 2. Set all random states at the start
np.random.seed(seed)
torch.manual_seed(seed)  # if using PyTorch
random.seed(seed)

# 3. Record the seed in the manifest
manifest["random_seed"] = seed

# 4. Never modify seed inside the function without logging
```

---

## Experiment Determinism

- Use `deterministic=True` in PyTorch operations where available
- Use fixed seeds for all stochastic operations
- Document any non-deterministic behavior (e.g., GPU floating point) in the manifest
- Time-based seeds are not acceptable for experiments

---

## Configuration Management

Configuration loading pattern:

```python
# Always load from config file
from src.utils.config import load_config, ExperimentConfig

config = load_config("configs/experiments/e5.yaml")

# Validate immediately
config = ExperimentConfig(**raw_config)  # Pydantic validation

# Never read config mid-experiment
# Never modify config after loading
```

---

## CLI Conventions

CLI commands follow the pattern:

```bash
python -m src.cli <command> [options]
```

All CLI commands:
- Accept `--config` for configuration file path
- Accept `--run-id` where applicable
- Accept `--seed` as override (must be logged)
- Output a run ID on success
- Exit with non-zero status on failure
- Never require interactive input during experiment runs

---

## Logging Standards

```python
import logging
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Use structured logging with context
logger.info(
    "Synchronization update",
    extra={
        "sync_interval": config.synchronization.interval_seconds,
        "sync_age": age,
        "run_id": run_id,
    },
)
```

Log levels:
- `DEBUG`: Detailed internal state (not for production runs)
- `INFO`: Experiment progress, synchronization events, model milestones
- `WARNING`: Degraded conditions, missed updates, convergence warnings
- `ERROR`: Non-fatal errors that affect a single run
- `CRITICAL`: Errors that invalidate the experiment

---

## Type Hints

```python
# Required on all public functions
def compute_synchronization_age(
    physical_timestamp: float, dt_timestamp: float, last_sync_timestamp: float
) -> float: ...


# Use Pydantic for configuration types
from pydantic import BaseModel


class SynchronizationConfig(BaseModel):
    interval_seconds: int
    missed_update_policy: str
    max_age_seconds: int | None = None
```

---

## Docstrings

Use NumPy-style docstrings:

```python
def compute_age_of_information(generation_time: float, reception_time: float) -> float:
    """
    Compute Age of Information (AoI) as defined in Guo et al. (2026).

    Parameters
    ----------
    generation_time : float
        Timestamp (seconds) when the information was generated at the
        physical system.
    reception_time : float
        Timestamp (seconds) when the information was received by the
        Digital Twin synchronization engine.

    Returns
    -------
    float
        Age of Information in seconds. Always non-negative.

    Notes
    -----
    AoI is used as a formal metric for Digital Twin data freshness
    following the framework in Guo et al. (2026) and Shu et al. (2022).
    """
    ...
```

---

## Validation

Before any experiment result is considered valid:

1. Run `make validate-dt` — confirms OpenDSS and IEEE 33-bus topology are consistent
2. Run `make test-unit` — confirms module-level correctness
3. Run `make test-integration` — confirms pipeline correctness
4. Run `make test-validation` — confirms physical constraints are satisfied
5. Confirm manifest.json was written successfully

---

*This file applies to Codex-style agents only. See `AGENTS.md` for general rules.*
