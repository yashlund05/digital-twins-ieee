# Digital Twin of Power Grid for Load Estimation and Anomaly Prediction

> **Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin**

[![Status](https://img.shields.io/badge/Status-Research%20Infrastructure%20Initialization-yellow)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-Configuration--Driven-brightgreen)]()

---

## Research Problem

While Digital Twin architectures for power systems, ML-based load forecasting, and DT residual-based anomaly detection are individually established, **the effect of DT synchronization staleness on these downstream ML tasks has not been systematically quantified**. This study treats synchronization interval as a controlled experimental variable and measures the resulting degradation in both short-term load estimation and unsupervised anomaly detection under identical conditions on a distribution-feeder Digital Twin.

---

## Primary Research Question

> **RQ1:** How does Digital Twin synchronization staleness affect short-term load-estimation performance and unsupervised anomaly detection quality in a simulated distribution feeder, and do the two tasks exhibit differential sensitivity to staleness?

## Primary Hypothesis

> **H3:** Anomaly detection will exhibit a steeper degradation profile than load estimation as synchronization staleness increases, because anomaly detection relies on precise residual discrimination that is more sensitive to state divergence.

> [!IMPORTANT]
> H3 is a hypothesis under investigation, not an established result. All hypotheses will be reported as stated — including if results contradict the hypothesis.

---

## Research Contributions

This project's contribution is **experimental**, not architectural:

1. A controlled experimental framework treating DT synchronization staleness as an independent variable on a distribution-feeder DT
2. Joint evaluation of short-term load estimation and unsupervised anomaly detection under identical synchronization conditions
3. Controlled raw-vs-residual anomaly detection comparison under staleness variation
4. A reproducible distribution-feeder experimental protocol with documented mapping, synchronization logging, and evaluation methodology

> [!NOTE]
> The individual components used (LSTM, XGBoost, Isolation Forest, LSTM Autoencoder, OpenDSS, IEEE 33-bus) are established technologies. The contribution is the experimental investigation of their behavior under controlled synchronization staleness.

---

## System Architecture

```
Physical / Synthetic Grid State
            ↓
     Data Acquisition
            ↓
  Synchronization Engine  ←─── Configurable Interval
            ↓                   Staleness Logging
     Digital Twin State          AoI Tracking
            ↓
       OpenDSS Solver
            ↓
 ┌──────────┬───────────┐
 ↓                      ↓
Load Estimation      Residual Engine
 ↓                      ↓
Forecasting          Anomaly Detection
 (Persistence,        (Isolation Forest,
  XGBoost, LSTM)       LSTM Autoencoder)
                        ↓
              Raw / Residual Analysis
                   (2×2 Design)
                        ↓
                Evaluation Engine
                        ↓
              Statistical Analysis
                        ↓
                 Paper Artifacts
```

---

## Experiment Overview

| ID | Name | Status |
|----|------|--------|
| E1 | Digital Twin Baseline Validation | Not started |
| E2 | Load Estimation Baselines | Not started |
| E3 | Anomaly Detection Baselines | Not started |
| E4 | Raw vs Residual Inputs | Not started |
| E5 | Synchronization Staleness Sweep | Not started |
| E6 | Degradation Profile Analysis | Not started |
| E7 | Missed-Update Transient Analysis | Not started |

---

## Repository Structure

```
digital-twins-ieee/
├── README.md                   # This file
├── AGENTS.md                   # AI agent instructions (general)
├── CLAUDE.md                   # Claude-specific instructions
├── GEMINI.md                   # Gemini/Antigravity instructions
├── CODEX.md                    # Codex-style agent instructions
├── AI_RULES.md                 # Central AI governance
├── VIBECODING.md               # Human + AI collaboration workflow
├── PHASES.md                   # Master project roadmap
├── CONTRIBUTING.md             # Team collaboration guide
├── CODEOWNERS                  # Module ownership
├── LICENSE
├── .gitignore
├── .env.example
├── pyproject.toml
├── Makefile
│
├── configs/                    # Configuration-driven experimentation
├── src/                        # Source modules
├── tests/                      # Test suite
├── data/                       # Data (see data/README.md)
├── experiments/                # Experiment runs and artifacts
├── notebooks/                  # Analysis notebooks
├── scripts/                    # Utility scripts
├── docs/                       # Documentation system
└── artifacts/                  # Paper-ready figures and tables
```

See [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md) for full architecture documentation.

---

## Quick Start

### Prerequisites

- Python 3.10+
- OpenDSS (via `py-dss-interface` or `opendssdirect.py`)
- Git

### Installation

```bash
git clone https://github.com/yashlund05/digital-twins-ieee.git
cd digital-twins-ieee

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package in editable mode
pip install -e ".[dev]"

# Verify environment
make validate-env
```

### Configuration

Copy `.env.example` to `.env` and fill in required values:

```bash
cp .env.example .env
```

### Running an Experiment

```bash
# Validate Digital Twin
python -m src.cli validate-dt

# Run a specific experiment
python -m src.cli run-experiment --config configs/experiments/e1_dt_validation.yaml

# Evaluate results
python -m src.cli evaluate --run-id <RUN_ID>
```

---

## Development Workflow

See [VIBECODING.md](VIBECODING.md) for the full human + AI collaboration workflow.

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch conventions, commit standards, and team collaboration.

---

## Reproducibility

All experiments are configuration-driven. Every experiment run records:

- `experiment_id`, `timestamp`, `git_commit`
- `configuration_version`, `dataset_version`
- `random_seed`, `model_version`
- `synchronization_interval`, `missed_update_policy`
- `software_environment`, `hardware_environment`

See [docs/methodology/REPRODUCIBILITY.md](docs/methodology/REPRODUCIBILITY.md) for the full reproducibility protocol.

---

## Dataset

This project uses a **hybrid simulation dataset**:

- **Network topology**: IEEE 33-bus benchmark feeder
- **Consumption patterns**: Pecan Street Dataport (real residential load profiles)
- **Mapping**: Pecan Street loads mapped to IEEE 33-bus nodes (documented in [docs/methodology/DATA_PROTOCOL.md](docs/methodology/DATA_PROTOCOL.md))
- **Anomalies**: Synthetically injected per documented protocol

> [!IMPORTANT]
> This dataset does NOT represent real field measurements of the IEEE 33-bus feeder. Pecan Street data provides consumption patterns only. All results are qualified to this hybrid simulation context.

---

## Current Project Status

```
Status:                  Research infrastructure initialization
Phase:                   PHASE 0 — Repository & Research Governance
Latest completed phase:  PHASE 0 (in progress)
Latest completed experiment: None
Fabricated results:      None
Committed secrets:       None
```

---

## Research Limitations

1. IEEE 33-bus is a benchmark topology, not a real operational feeder
2. Pecan Street data mapped to IEEE topology creates a hybrid simulation dataset — not field validation
3. Synthetic anomalies cannot replicate all physical fault characteristics
4. Results are qualified to the evaluated topology, dataset, and detector combination
5. Simulation-based DT lacks field-level calibration and validation
6. Synchronization intervals in simulation may not perfectly represent real-world SCADA/AMI communication constraints

---

## Team Collaboration

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Branch naming conventions
- Commit message standards
- Pull request process
- Code review requirements
- Experiment coordination

See [docs/onboarding/TEAM_ROLES.md](docs/onboarding/TEAM_ROLES.md) for suggested role assignments.

---

## Citation

This project has not yet been published. A citation placeholder will be added upon submission.

```bibtex
@article{PLACEHOLDER,
  title   = {Quantifying the Effect of Digital Twin Synchronization Staleness on
             Joint Short-Term Load Estimation and Unsupervised Anomaly Detection
             in a Distribution-Feeder Digital Twin},
  author  = {[AUTHORS]},
  journal = {[JOURNAL]},
  year    = {[YEAR]},
  note    = {Under preparation}
}
```

---

## License

MIT License — see [LICENSE](LICENSE).

---

*This repository is the research infrastructure for an ongoing academic study. It does not contain experimental results because the experiments have not yet been performed.*
