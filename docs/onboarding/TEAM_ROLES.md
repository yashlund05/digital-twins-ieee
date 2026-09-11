# Team Roles and Onboarding Guide

> **Version:** 1.0.0 — September 2026
> **Status:** Active Governance Document

---

## Overview

This repository operates as a collaborative academic research project. To maintain research integrity, reproducibility, and clear ownership, responsibilities are partitioned into explicit module roles.

Each role has a primary owner (designated in `CODEOWNERS`), specific module boundaries, and sign-off authority for architectural and methodology decisions.

---

## Team Role Directory

```
                                  +-----------------------+
                                  |    RESEARCH LEAD      |
                                  |    (@RESEARCH_LEAD)   |
                                  +-----------+-----------+
                                              |
                                  +-----------v-----------+
                                  |   INTEGRATION LEAD    |
                                  | (@INTEGRATION_LEAD)   |
                                  +-----------+-----------+
                                              |
      +-------------------+-------------------+-------------------+-------------------+
      |                   |                   |                   |                   |
+-----v-----+       +-----v-----+       +-----v-----+       +-----v-----+       +-----v-----+
|   DATA    |       |  DIGITAL  |       |   SYNC    |       |    ML     |       |  ANOMALY  |
|   OWNER   |       |   TWIN    |       |   OWNER   |       |   OWNER   |       |   OWNER   |
+-----------+       +-----------+       +-----------+       +-----------+       +-----------+
                          |                   |                   |
                          +-------------------+-------------------+
                                              |
                                  +-----------v-----------+
                                  |   EXPERIMENT OWNER    |
                                  |  (@EXPERIMENT_OWNER)  |
                                  +-----------+-----------+
                                              |
                                  +-----------v-----------+
                                  |  EVALUATION & STATS   |
                                  |     (@EVAL_OWNER)     |
                                  +-----------------------+
```

---

## Detailed Role Specifications

### 1. Research Lead (`@RESEARCH_LEAD`)
- **Primary Focus:** Scientific validity, research questions (RQ1–RQ4), literature alignment, manuscript integrity.
- **Owned Areas:**
  - `docs/research/`, `docs/methodology/`, `docs/decisions/`, `docs/paper/`, `docs/onboarding/`
  - Root governance files: `AGENTS.md`, `AI_RULES.md`, `VIBECODING.md`, `PHASES.md`, `LICENSE`
  - Final paper artifacts in `artifacts/`
  - PR sign-off on any methodology or research framing changes.
- **Key Metric:** Scientific soundness, avoidance of overclaims, zero fabricated data.

### 2. Integration Lead (`@INTEGRATION_LEAD`)
- **Primary Focus:** Repository infrastructure, build automation, CI/CD, cross-module interfaces.
- **Owned Areas:**
  - `pyproject.toml`, `Makefile`, `.gitignore`, `.env.example`
  - `src/cli/`, `src/utils/`
  - `docs/architecture/`
  - Test harness in `tests/integration/`
- **Key Metric:** Zero-dependency drift, clean environment reproduction across systems.

### 3. Digital Twin Owner (`@DT_OWNER`)
- **Primary Focus:** OpenDSS integration, IEEE 33-bus feeder simulation, electrical state calculation.
- **Owned Areas:**
  - `src/digital_twin/`
  - `configs/digital_twin.yaml`
  - OpenDSS test cases in `tests/unit/test_digital_twin.py`
- **Key Metric:** Power flow convergence, physical realism of feeder states ($V$, $P$, $Q$).

### 4. Synchronization Engine Owner (`@SYNC_OWNER`)
- **Primary Focus:** The experimental independent variable — staleness simulation, Age of Information (AoI), buffer management.
- **Owned Areas:**
  - `src/synchronization/`
  - `configs/synchronization.yaml`
  - `docs/architecture/SYNCHRONIZATION_ENGINE.md`
  - Tests in `tests/unit/test_synchronization.py` and `tests/validation/test_staleness_bounds.py`
- **Key Constraint:** Synchronization logic lives exclusively in this module. Any interface change requires an approved ADR.

### 5. Machine Learning Owner (`@ML_OWNER`)
- **Primary Focus:** Short-term load estimation models.
- **Owned Areas:**
  - `src/forecasting/` (Persistence, XGBoost, PyTorch LSTM)
  - `configs/forecasting.yaml`
  - Tests in `tests/unit/test_forecasting.py`
- **Key Constraint:** Standardized architectures; hyperparameters defined strictly via configs; no post-hoc tuning on test data.

### 6. Anomaly Detection Owner (`@ANOMALY_OWNER`)
- **Primary Focus:** Unsupervised anomaly detection and physics-based residual calculation.
- **Owned Areas:**
  - `src/anomaly_detection/` (Isolation Forest, LSTM Autoencoder)
  - `src/residuals/` (OpenDSS state residual engine)
  - `configs/anomaly_detection.yaml`
  - Tests in `tests/unit/test_anomaly_detection.py`, `tests/unit/test_residuals.py`, and `tests/validation/test_unsupervised_integrity.py`
- **Key Constraint:** Strict unsupervised protocol — models must never receive anomaly labels during fitting.

### 7. Data Pipeline Owner (`@DATA_OWNER`)
- **Primary Focus:** Data ingestion, temporal splitting, Pecan Street mapping, and synthetic anomaly injection.
- **Owned Areas:**
  - `src/data/`
  - `configs/data.yaml`
  - `data/` documentation and processing scripts
  - Tests in `tests/unit/test_data.py` and `tests/validation/test_no_data_leakage.py`
- **Key Constraint:** Strict temporal splitting without leakage; transparent disclosure of hybrid simulation nature.

### 8. Experiment Orchestration Owner (`@EXPERIMENT_OWNER`)
- **Primary Focus:** Automated execution of experiments E1–E7, configuration locking, run manifests.
- **Owned Areas:**
  - `src/experiments/`
  - `configs/experiments/`
  - `experiments/runs/`, `experiments/manifests/`
  - `docs/experiments/`
- **Key Constraint:** Every run must produce a verifiable `manifest.json`. Never overwrite historical run directories.

### 9. Evaluation & Statistics Owner (`@EVAL_OWNER`)
- **Primary Focus:** Pure metric computation, rigorous hypothesis testing, and publication figure/table generation.
- **Owned Areas:**
  - `src/evaluation/`, `src/statistics/`, `src/visualization/`
  - `tests/validation/`, `tests/regression/`
  - Figure and table formatting per `docs/paper/FIGURE_TABLE_STANDARD.md`
- **Key Constraint:** Pure functions, zero division safety, pre-specified hypothesis test protocol per `docs/methodology/STATISTICAL_PROTOCOL.md`.

---

## Contributor Onboarding Sequence

New human researchers or AI agents joining this project must complete the following onboarding checklist before contributing code:

### Step 1: Environment Setup
```bash
# 1. Clone the repository
git clone <repo-url>
cd "digital twins ieee"

# 2. Create and activate a clean virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install package in editable development mode
pip install -e ".[dev]"

# 4. Verify installation
python -c "import src; print(src.__version__)"
pytest
```

### Step 2: Mandatory Reading
- [ ] Read `AGENTS.md` and `AI_RULES.md` for scientific non-negotiables.
- [ ] Read `VIBECODING.md` for the test-first workflow.
- [ ] Read `PHASES.md` to see current project status and Phase deliverables.
- [ ] Read `docs/architecture/SYSTEM_ARCHITECTURE.md` to understand module data flows.
- [ ] Read `docs/methodology/DATA_PROTOCOL.md` and `docs/methodology/REPRODUCIBILITY.md`.

### Step 3: Git & Contribution Workflow
1. Create a feature branch matching your role and task:
   `feature/<module>-<short-description>` or `experiment/<e_number>-<desc>`
2. Follow commit message conventions: `feat(<module>): message` or `fix(<module>): message`.
3. Open a Pull Request using `.github/pull_request_template.md`.
4. Ensure all CI checks (black, ruff, mypy, pytest) pass.
5. Request review from the module owner specified in `CODEOWNERS`.
