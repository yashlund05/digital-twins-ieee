# AGENTS.md — General AI Agent Instructions

> This file applies to **any AI coding agent** operating inside this repository: GitHub Copilot, Codex, Claude, Gemini, Cursor, or any other agent-based coding tool.

---

## Project Context

This is a **multi-member academic research repository** for:

> **Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin**

- Research domain: Power systems + Digital Twins + Machine Learning
- Primary novelty: Controlled experimental investigation of synchronization staleness effects on downstream ML tasks
- Platform: Python, OpenDSS, IEEE 33-bus benchmark feeder, Pecan Street load data
- Team: Multiple contributors — see `CODEOWNERS` and `docs/onboarding/TEAM_ROLES.md`

**This is NOT:**
- A generic Digital Twin implementation
- A load forecasting tutorial
- An anomaly detection demo
- A novel architecture project
- A production system

---

## Mandatory Pre-Modification Procedure

Before modifying ANY code, an AI agent MUST:

1. **Read `AGENTS.md`** (this file) — understand the project and rules
2. **Read `AI_RULES.md`** — understand governance constraints
3. **Read `VIBECODING.md`** — understand the required task workflow
4. **Inspect the relevant module's `__init__.py`** and existing implementation
5. **Read the relevant `docs/architecture/` documentation** for affected subsystems
6. **Read relevant ADRs** in `docs/decisions/` for prior decisions
7. **Identify all affected modules** — not just the target file
8. **Check for existing tests** before implementing
9. **Check the current `experiments/` directory** for runs that may be affected

---

## Architecture Principles

### Synchronization is a first-class system component
The synchronization engine in `src/synchronization/` is the single authoritative abstraction for all synchronization logic. Do NOT scatter synchronization timing or staleness calculations across other modules.

### Configuration over hard-coding
All experimental parameters MUST come from configuration files in `configs/`. Never hard-code synchronization intervals, random seeds, model hyperparameters, or data paths.

### Reproducibility is non-negotiable
Every experiment run MUST produce a unique run identifier and store its complete configuration, random seed, git commit hash, and environment metadata.

### Interfaces are stable
Do not change module interfaces without:
1. Creating an ADR in `docs/decisions/`
2. Updating tests
3. Updating documentation
4. Notifying affected module owners (see `CODEOWNERS`)

### Modules are independently testable
Each module in `src/` must be independently importable and testable. Avoid circular dependencies.

---

## Coding Standards

- **Language**: Python 3.10+
- **Type hints**: Required on all public functions and class methods
- **Docstrings**: Required on all public functions, classes, and modules (NumPy or Google style)
- **Formatting**: Follow `pyproject.toml` configuration (black + ruff or equivalent)
- **Imports**: Absolute imports only within `src/`
- **Error handling**: Explicit, never silent. Log errors with context.
- **Logging**: Use the project's logging utilities in `src/utils/logging.py`. Never use bare `print()` in production code.
- **Configuration**: Load from config files via `src/utils/config.py`. Never read environment variables directly in module code.

---

## Research Integrity Requirements

An AI agent MUST NEVER:

- Invent experimental metrics, results, or performance numbers
- Invent dataset statistics or citations
- Claim an experiment was executed when it was not
- Modify experimental parameters without updating configuration files and documentation
- Silently alter the train/test split, random seeds, or data processing steps
- Remove or suppress failed experimental results
- Tune models on the test set
- Alter anomaly labels after observing model performance
- Cherry-pick favorable random seeds without disclosing the selection procedure
- Report only favorable detector configurations
- Hide negative results or failed experiments

If an experiment contradicts a hypothesis, **report it accurately**. A contradicted hypothesis is scientifically valuable.

---

## Directory Conventions

| Directory | Purpose | Rules |
|-----------|---------|-------|
| `src/` | All production source code | Modular, typed, tested |
| `src/synchronization/` | Synchronization engine only | All sync logic here, nowhere else |
| `src/digital_twin/` | OpenDSS wrapper and DT state | No ML logic |
| `src/forecasting/` | Load estimation models | No synchronization logic |
| `src/anomaly_detection/` | Anomaly detector implementations | No synchronization logic |
| `src/residuals/` | Residual computation | Depends on DT state only |
| `src/evaluation/` | Metric computation | Stateless, pure functions preferred |
| `src/experiments/` | Experiment orchestration | Calls other modules, no new ML logic |
| `src/cli/` | CLI entry points | Thin wrappers, no business logic |
| `configs/` | Experiment configurations | YAML, no Python logic |
| `experiments/runs/` | Experiment outputs | Never committed to Git if large |
| `tests/` | Test suite | Mirror `src/` structure |
| `docs/` | Documentation | Keep up to date |
| `data/raw/` | Raw input data | Never overwrite, never modify |
| `notebooks/` | Analysis only | No data generation logic |
| `artifacts/` | Paper-ready outputs | Generated, not manually edited |

---

## Testing Requirements

- Write tests alongside implementation, not after
- All new public functions must have at least one unit test
- All integration points must have an integration test
- Run `make test` before committing
- Never disable or skip tests without a documented reason
- Validation tests in `tests/validation/` must pass before any experiment is considered valid

---

## Experiment Reproducibility

- Every experiment MUST be runnable from: `python -m src.cli run-experiment --config <config_file>`
- Every experiment run MUST produce a manifest at: `experiments/runs/<run_id>/manifest.json`
- Never overwrite a previous experiment run
- Experiments run from notebooks only are not considered reproducible

---

## Git Rules

- Never commit directly to `main`
- Never commit `.env` files, API keys, or credentials
- Never commit raw dataset files >50MB without discussion
- Never commit generated model binaries unless intentionally versioned
- Follow commit conventions in `CONTRIBUTING.md`
- Include the affected module name in commit messages

---

## Dependency Rules

- Add new dependencies to `pyproject.toml` only
- Justify every new dependency in the PR description
- Prefer standard library and already-listed dependencies
- Never introduce ML frameworks not in the approved stack without creating an ADR
- Never install packages globally on shared systems

---

## Configuration Rules

- All configurable parameters live in `configs/`
- Configuration files use YAML format
- Configuration is validated with Pydantic schemas in `src/utils/config.py`
- Never hard-code paths, seeds, intervals, or thresholds
- Machine-specific paths belong in `.env`, not configs

---

## Security Rules

- Never commit API keys, tokens, passwords, or connection strings
- Never log sensitive information
- Use `.env` for local secrets; reference via `.env.example` for documentation
- Do not hard-code Pecan Street API credentials anywhere in the codebase

---

## Data Handling Rules

- `data/raw/` is read-only after initial download; never overwrite raw data
- All data processing produces outputs to `data/interim/` or `data/processed/`
- The dataset is a **hybrid simulation dataset** — never describe it as real field measurements of the IEEE feeder
- Document every data transformation step
- Data splits (train/validation/test) are defined in configuration and must prevent temporal leakage

---

## What to Do When Uncertain

1. Read existing documentation before asking
2. Check existing ADRs for prior decisions
3. If a decision has not been made, raise a research question issue using the issue template
4. Do not make architectural decisions silently
5. Flag methodology changes explicitly in PRs

---

*This file applies to all AI agents. For agent-specific instructions, see `CLAUDE.md`, `GEMINI.md`, and `CODEX.md`.*
