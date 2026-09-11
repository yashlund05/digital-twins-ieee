# PHASES.md — Master Project Execution Roadmap

> **Project:** Digital Twin of Power Grid for Load Estimation and Anomaly Prediction
> **Subtitle:** Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin
> **Version:** 1.0.0 — September 2026

> [!IMPORTANT]
> This roadmap defines what must be built, in what order, and how to verify each phase.
> No phase may be considered complete until its Definition of Done is satisfied.
> Later phases must not depend on undocumented behavior from earlier phases.

---

## Phase Overview

| Phase | Name | Status | Depends On |
|-------|------|--------|------------|
| 0 | Repository & Research Governance | In Progress | — |
| 1 | Environment & Infrastructure | Not Started | 0 |
| 2 | Data Pipeline | Not Started | 1 |
| 3 | IEEE 33-Bus Digital Twin | Not Started | 2 |
| 4 | Synchronization Engine | Not Started | 3 |
| 5 | Baseline Load Estimation | Not Started | 4 |
| 6 | Anomaly Detection | Not Started | 4 |
| 7 | Residual Engine | Not Started | 4 |
| 8 | Controlled Staleness Experiments | Not Started | 5, 6, 7 |
| 9 | Joint Analysis | Not Started | 8 |
| 10 | Statistical Validation | Not Started | 9 |
| 11 | Reproducibility & Ablations | Not Started | 10 |
| 12 | Paper-Ready Results | Not Started | 11 |
| 13 | Final Packaging & Release | Not Started | 12 |

---

## PHASE 0 — Repository & Research Governance

### Goal
Create the complete research repository foundation, documentation system, development governance, experiment framework, and architecture documentation. The repository must be ready for team implementation.

### Research Question Addressed
None directly — this phase establishes the infrastructure to answer RQ1.

### Inputs
- Research specification
- Literature review (`docs/research/literature-review.md`)
- Team composition

### Outputs
- Complete repository structure
- All governance files (AGENTS.md, CLAUDE.md, GEMINI.md, CODEX.md, AI_RULES.md, VIBECODING.md)
- All documentation (architecture, methodology, experiments, decisions)
- Configuration scaffolding
- GitHub templates
- Python package structure (no ML code yet)

### Modules
- None implemented yet — placeholder structure only

### Dependencies
- None

### Acceptance Criteria
- [ ] All 29 checklist items in specification Section 29 satisfied
- [ ] Literature review preserved intact
- [ ] No fabricated results exist anywhere
- [ ] No secrets committed
- [ ] No unnecessary dependencies
- [ ] Repository cloneable and `pip install -e .` succeeds

### Tests
- `pyproject.toml` parses correctly
- Package imports successfully
- Configuration files parse as valid YAML

### Experiments
- None

### Expected Artifacts
- Complete repository as specified

### Team Roles
- Research Lead: Owns all documentation and governance
- Integration Lead: Owns `pyproject.toml`, `Makefile`, CI structure

### Definition of Done
- All specification acceptance criteria satisfied
- Team has reviewed and acknowledged governance documents
- Repository pushed to GitHub

---

## PHASE 1 — Environment & Infrastructure

### Goal
Establish a fully reproducible development environment. Verify that all required software (Python, OpenDSS, core libraries) is installable and functional. Set up CI pipeline.

### Research Question Addressed
None directly — enables reproducible execution of all subsequent phases.

### Inputs
- `pyproject.toml` from Phase 0
- Team development environments

### Outputs
- Verified Python environment with all dependencies
- OpenDSS confirmed functional (via `opendssdirect.py` or `py-dss-interface`)
- CI pipeline (GitHub Actions)
- Utility modules: `src/utils/config.py`, `src/utils/logging.py`, `src/utils/io.py`
- Pydantic configuration schemas
- `make` targets: `validate-env`, `test`, `format`, `lint`

### Modules
- `src/utils/config.py` — configuration loading and Pydantic validation
- `src/utils/logging.py` — structured logging setup
- `src/utils/io.py` — file I/O helpers
- `src/utils/reproducibility.py` — seed setting, environment capture

### Dependencies
- Phase 0 complete

### Acceptance Criteria
- [ ] `pip install -e "[dev]"` succeeds on all team machines
- [ ] `python -c "import opendssdirect; print('OK')"` succeeds
- [ ] `make test` runs and passes (with placeholder tests)
- [ ] Configuration loading and validation works
- [ ] Logging produces structured output
- [ ] CI pipeline runs on push to `develop`

### Tests
- `tests/unit/test_config.py` — configuration loading and validation
- `tests/unit/test_logging.py` — logger initialization
- `tests/unit/test_reproducibility.py` — seed setting functions

### Experiments
- None

### Expected Artifacts
- Passing CI badge
- Environment lockfile (`requirements.lock` or equivalent)

### Team Roles
- Integration Lead: CI, environment
- All members: Verify environment on their machines

### Definition of Done
- All team members can run `make validate-env` successfully
- CI is green on `develop`

---

## PHASE 2 — Data Pipeline

### Goal
Implement the data pipeline from raw Pecan Street data to processed load profiles mapped to the IEEE 33-bus feeder. Implement synthetic anomaly injection. Implement and verify train/validation/test splits with temporal leakage prevention.

### Research Question Addressed
RQ1 (prerequisite): Data quality and preparation directly affect the validity of all downstream experiments.

### Inputs
- Pecan Street Dataport data (requires API access or manual download)
- IEEE 33-bus topology definition
- `docs/methodology/DATA_PROTOCOL.md`
- `configs/data.yaml`

### Outputs
- `data/processed/load_profiles.parquet` — cleaned, mapped load profiles
- `data/processed/anomaly_labels.parquet` — synthetic anomaly injection labels
- `data/processed/splits.json` — train/val/test split indices
- `src/data/` — complete data pipeline module

### Modules
- `src/data/loader.py` — raw data loading
- `src/data/preprocessor.py` — cleaning, normalization, feature engineering
- `src/data/mapper.py` — Pecan Street → IEEE 33-bus mapping
- `src/data/anomaly_injector.py` — synthetic fault injection
- `src/data/splitter.py` — temporal train/val/test split
- `src/data/schema.py` — Pydantic data schemas

### Dependencies
- Phase 1 complete
- Pecan Street data access obtained

### Acceptance Criteria
- [ ] Data pipeline produces deterministic output given fixed seed
- [ ] No temporal leakage between train/val/test splits (validated by test)
- [ ] All 33 IEEE bus nodes have mapped load profiles
- [ ] Anomaly injection is configurable and reproducible
- [ ] Data is documented as hybrid simulation dataset (not field measurements)
- [ ] Mapping protocol is documented in `docs/methodology/DATA_PROTOCOL.md`

### Tests
- `tests/unit/test_preprocessor.py` — normalization, scaling
- `tests/unit/test_mapper.py` — mapping correctness
- `tests/unit/test_anomaly_injector.py` — anomaly generation
- `tests/unit/test_splitter.py` — split boundaries, no leakage
- `tests/validation/test_data_integrity.py` — schema validation, range checks

### Experiments
- Preliminary: Data characterization notebook in `notebooks/exploration/`

### Expected Artifacts
- `data/processed/` — processed dataset
- `docs/methodology/DATA_PROTOCOL.md` — updated with actual mapping decisions
- `notebooks/exploration/data_exploration.ipynb`

### Team Roles
- Data Engineer: Owns all `src/data/` modules
- Research Lead: Reviews mapping protocol and anomaly injection decisions

### Definition of Done
- Data pipeline runs end-to-end: `python -m src.cli prepare-data`
- All data tests pass
- Mapping protocol reviewed and approved
- Anomaly injection parameters documented in configuration

---

## PHASE 3 — IEEE 33-Bus Digital Twin

### Goal
Implement the Digital Twin using OpenDSS for the IEEE 33-bus feeder. Validate power flow outputs against expected physical behavior. Establish the DT state representation.

### Research Question Addressed
RQ1 (prerequisite): The DT must correctly simulate the physical system before synchronization effects can be studied.

### Inputs
- IEEE 33-bus topology files
- `configs/digital_twin.yaml`
- `docs/architecture/SYSTEM_ARCHITECTURE.md`
- Processed load profiles from Phase 2

### Outputs
- Functional OpenDSS-based Digital Twin
- DT state object (voltages, currents, power flows for all nodes)
- Experiment E1 validation results

### Modules
- `src/digital_twin/topology.py` — IEEE 33-bus topology definition
- `src/digital_twin/solver.py` — OpenDSS power flow solver wrapper
- `src/digital_twin/state.py` — DT state data structure
- `src/digital_twin/initializer.py` — DT initialization from config

### Dependencies
- Phase 2 complete

### Acceptance Criteria
- [ ] OpenDSS solves IEEE 33-bus power flow successfully
- [ ] Bus voltages within expected range (per IEEE 33-bus reference)
- [ ] Power balance satisfied (generation ≈ load + losses)
- [ ] DT state object serializable to JSON
- [ ] Solver is deterministic for fixed inputs

### Tests
- `tests/unit/test_dt_topology.py` — IEEE 33-bus topology loading
- `tests/unit/test_dt_solver.py` — power flow solver
- `tests/validation/test_ieee33_sanity.py` — physical constraint validation
- `tests/integration/test_dt_pipeline.py` — data → DT integration

### Experiments
- **E1: Digital Twin Baseline Validation** (see `docs/experiments/EXPERIMENTS.md`)

### Expected Artifacts
- `experiments/runs/E1_DT_VALIDATION_<date>/` — E1 run outputs
- `notebooks/validation/dt_validation.ipynb`

### Team Roles
- Digital Twin Engineer: Owns all `src/digital_twin/` modules
- Research Lead: Reviews E1 results

### Definition of Done
- E1 validation passes all acceptance criteria
- Power flow sanity tests pass
- `python -m src.cli validate-dt` succeeds

---

## PHASE 4 — Synchronization Engine

### Goal
Implement the configurable synchronization engine. This is the most critical component of the research — it controls the independent variable (synchronization interval) and must be the single authoritative source of synchronization logic.

### Research Question Addressed
RQ1 (core): The synchronization engine is the mechanism through which staleness is introduced as a controlled experimental variable.

### Inputs
- `configs/synchronization.yaml`
- `docs/architecture/SYNCHRONIZATION_ENGINE.md`
- DT state module from Phase 3

### Outputs
- Configurable synchronization engine
- Synchronization event log schema
- Age of Information calculation
- Staleness tracking

### Modules
- `src/synchronization/engine.py` — core synchronization loop
- `src/synchronization/scheduler.py` — interval-based update scheduling
- `src/synchronization/aoi.py` — Age of Information calculation
- `src/synchronization/logger.py` — synchronization event logging
- `src/synchronization/policies.py` — missed-update policies (hold_last_state, etc.)
- `src/synchronization/state_tracker.py` — physical vs DT state divergence tracking

### Dependencies
- Phase 3 complete

### Acceptance Criteria
- [ ] Synchronization interval is configurable from `configs/synchronization.yaml`
- [ ] AoI is correctly calculated and logged
- [ ] Missed updates are detected and handled per policy
- [ ] Synchronization log captures: physical_timestamp, dt_timestamp, last_sync, sync_age, aoi, missed_updates
- [ ] Engine is independent from forecasting and anomaly detection modules
- [ ] Stale state is clearly distinguished from current state

### Tests
- `tests/unit/test_sync_engine.py` — interval scheduling, event generation
- `tests/unit/test_aoi.py` — AoI calculation correctness
- `tests/unit/test_sync_policies.py` — missed update policy behavior
- `tests/integration/test_dt_sync_integration.py` — DT + sync pipeline

### Experiments
- None (component test only in this phase)

### Expected Artifacts
- Synchronization log schema documented
- `configs/synchronization.yaml` finalized

### Team Roles
- Synchronization Engineer: Owns all `src/synchronization/` modules
- Digital Twin Engineer: Integration with DT state
- Research Lead: Validates against `docs/architecture/SYNCHRONIZATION_ENGINE.md`

### Definition of Done
- Synchronization engine passes all unit and integration tests
- AoI calculation verified against expected values
- Missed update policy documented and tested
- Synchronization log schema finalized

---

## PHASE 5 — Baseline Load Estimation

### Goal
Implement and validate the three load estimation models: Persistence, XGBoost, and LSTM. Establish baseline performance under perfect synchronization. Run Experiment E2.

### Research Question Addressed
RQ1 (baseline): Establishes the load estimation performance under ideal conditions (zero staleness) against which degradation will be measured.

### Inputs
- Processed data from Phase 2
- Synchronization engine from Phase 4 (at interval = 0, perfect sync)
- `configs/forecasting.yaml`

### Outputs
- Three trained and validated forecasting models
- Baseline metrics: MAE, RMSE, MAPE (optionally R²)
- Experiment E2 results

### Modules
- `src/forecasting/persistence.py` — persistence baseline
- `src/forecasting/xgboost_model.py` — XGBoost load estimator
- `src/forecasting/lstm_model.py` — LSTM load estimator
- `src/forecasting/trainer.py` — training loop with reproducibility
- `src/forecasting/predictor.py` — inference interface
- `src/forecasting/features.py` — feature engineering for tabular models

### Dependencies
- Phase 4 complete

### Acceptance Criteria
- [ ] All three models train from configuration
- [ ] All three models produce deterministic outputs for fixed seeds
- [ ] Metrics computed correctly (validated against reference implementations)
- [ ] No temporal leakage in training
- [ ] Results match expected literature ranges (see literature review benchmarks)

### Tests
- `tests/unit/test_persistence.py`
- `tests/unit/test_xgboost_model.py`
- `tests/unit/test_lstm_model.py`
- `tests/unit/test_forecasting_metrics.py`
- `tests/integration/test_forecasting_pipeline.py`

### Experiments
- **E2: Load Estimation Baselines**

### Expected Artifacts
- `experiments/runs/E2_BASELINE_*` — E2 results for all three models
- Trained model artifacts in `experiments/runs/E2_*/`

### Team Roles
- ML/Forecasting Engineer: Owns `src/forecasting/`
- Data Engineer: Feature engineering support
- Evaluation Engineer: Metric validation

### Definition of Done
- E2 results produced for all three models
- Results validated against expected ranges from literature
- `python -m src.cli train-forecast` succeeds

---

## PHASE 6 — Anomaly Detection

### Goal
Implement and validate the two anomaly detectors: Isolation Forest and LSTM Autoencoder. Establish baseline detection performance under perfect synchronization. Run Experiment E3.

### Research Question Addressed
RQ1 (baseline): Establishes anomaly detection performance under ideal conditions against which degradation will be measured.

### Inputs
- Processed data with anomaly labels from Phase 2
- Synchronization engine from Phase 4 (perfect sync)
- `configs/anomaly_detection.yaml`

### Outputs
- Two trained and validated anomaly detectors
- Baseline metrics: Precision, Recall, F1, PR-AUC, ROC-AUC, FPR
- Experiment E3 results

### Modules
- `src/anomaly_detection/isolation_forest.py`
- `src/anomaly_detection/lstm_autoencoder.py`
- `src/anomaly_detection/trainer.py`
- `src/anomaly_detection/detector.py` — unified interface
- `src/anomaly_detection/thresholds.py` — threshold selection (unsupervised)

### Dependencies
- Phase 4 complete

### Acceptance Criteria
- [ ] Both detectors are trained in unsupervised mode (no anomaly labels in training)
- [ ] Both detectors produce anomaly scores
- [ ] Threshold selection is configurable and documented
- [ ] All metrics computed correctly
- [ ] Models are deterministic for fixed seeds

### Tests
- `tests/unit/test_isolation_forest.py`
- `tests/unit/test_lstm_autoencoder.py`
- `tests/unit/test_anomaly_metrics.py`
- `tests/integration/test_anomaly_pipeline.py`

### Experiments
- **E3: Anomaly Detection Baselines**

### Expected Artifacts
- `experiments/runs/E3_BASELINE_*` — E3 results for both detectors

### Team Roles
- Anomaly Detection Engineer: Owns `src/anomaly_detection/`
- Evaluation Engineer: Metric validation

### Definition of Done
- E3 results produced for both detectors, both raw and residual inputs
- `python -m src.cli train-anomaly` succeeds

---

## PHASE 7 — Residual Engine

### Goal
Implement the residual computation engine. Residuals are defined as the difference between physical measurements and DT predictions. Run Experiment E4 (raw vs. residual comparison).

### Research Question Addressed
RQ1 (mechanism): The residual engine provides the alternative input representation for the 2×2 experiment design.

### Inputs
- DT state from Phase 3
- Physical data from Phase 2
- Trained detectors from Phase 6

### Outputs
- Residual time series for all bus nodes
- E4 results (2×2 design: IF×Raw, IF×Residual, LSTMAE×Raw, LSTMAE×Residual)

### Modules
- `src/residuals/calculator.py` — physical − virtual residual computation
- `src/residuals/normalizer.py` — residual normalization
- `src/residuals/features.py` — residual feature extraction

### Dependencies
- Phases 4, 5, 6 complete

### Acceptance Criteria
- [ ] Residuals correctly computed as (physical − DT_prediction)
- [ ] Residuals are zero (or near-zero) under perfect synchronization (sanity check)
- [ ] Residual features are informative under anomaly conditions (verified in E4)
- [ ] E4 2×2 design implemented and reproducible

### Tests
- `tests/unit/test_residual_calculator.py`
- `tests/unit/test_residual_features.py`
- `tests/integration/test_residual_pipeline.py`

### Experiments
- **E4: Raw vs. Residual Inputs**

### Expected Artifacts
- `experiments/runs/E4_RAW_VS_RESIDUAL_*`

### Team Roles
- Anomaly Detection Engineer: Owns `src/residuals/`
- Digital Twin Engineer: DT state interface

### Definition of Done
- E4 2×2 results produced
- Residual calculations verified

---

## PHASE 8 — Controlled Staleness Experiments

### Goal
Run the primary experimental investigation: systematically vary the synchronization interval and measure the effect on both load estimation and anomaly detection. This is the core of the research contribution. Run Experiment E5.

### Research Question Addressed
**RQ1 (primary):** How does DT synchronization staleness affect load estimation performance and anomaly detection quality?

### Inputs
- All models from Phases 5, 6, 7
- Synchronization engine from Phase 4
- `configs/experiments/e5_staleness_sweep.yaml`

### Outputs
- E5 results: metrics for all (staleness interval × detector × input representation) combinations
- Synchronization logs for each interval
- AoI measurements for each interval

### Modules
- `src/experiments/staleness_sweep.py`
- `src/experiments/runner.py`
- `src/evaluation/metrics.py` — unified metric computation

### Dependencies
- Phases 5, 6, 7 complete

### Acceptance Criteria
- [ ] All synchronization intervals tested (as specified in `configs/experiments/e5_staleness_sweep.yaml`)
- [ ] All (detector × input_representation) combinations tested
- [ ] Each run has a unique run_id and manifest
- [ ] Synchronization log produced for each run
- [ ] Results reproducible from configuration

### Tests
- `tests/integration/test_staleness_sweep.py` — short sweep with reduced intervals
- `tests/regression/test_e5_regression.py` — regression on previously validated outputs

### Experiments
- **E5: Synchronization Staleness Sweep** (primary)

### Expected Artifacts
- `experiments/runs/E5_*` — all staleness sweep runs
- Summary table across all conditions

### Team Roles
- Synchronization Engineer: Experiment coordination
- ML Engineer + Anomaly Engineer: Model inference
- Evaluation Engineer: Result aggregation

### Definition of Done
- All E5 conditions completed and manifests validated
- Results table produced
- No conditions skipped or fabricated

---

## PHASE 9 — Joint Analysis

### Goal
Analyze whether load estimation and anomaly detection exhibit differential sensitivity to staleness (H3). Run Experiment E6. Analyze degradation profiles.

### Research Question Addressed
**RQ1 (primary + H3):** Do the two tasks degrade at different rates? What is the shape of the degradation curve?

### Inputs
- E5 results from Phase 8
- `docs/methodology/STATISTICAL_PROTOCOL.md`

### Outputs
- Degradation profiles for load estimation and anomaly detection
- H3 assessment (supported/contradicted/inconclusive)
- Raw vs. residual comparison under staleness
- E6 analysis results

### Modules
- `src/statistics/degradation.py` — degradation profile analysis
- `src/statistics/regression.py` — performance vs. staleness regression
- `src/visualization/degradation_plots.py` — degradation figures

### Dependencies
- Phase 8 complete

### Acceptance Criteria
- [ ] H3 explicitly assessed (supported/contradicted/inconclusive) — do not cherry-pick result
- [ ] Both tasks analyzed under identical synchronization conditions
- [ ] Degradation curve shape characterized (linear/nonlinear/threshold)
- [ ] Raw vs. residual comparison included

### Experiments
- **E6: Degradation Profile Analysis**

### Expected Artifacts
- `artifacts/figures/Fig_03_load_degradation.*`
- `artifacts/figures/Fig_04_anomaly_degradation.*`
- `artifacts/figures/Fig_05_raw_vs_residual.*`
- `artifacts/figures/Fig_06_joint_sensitivity.*`

### Team Roles
- Evaluation Engineer: Analysis
- Research Lead: Interpretation, H3 assessment

### Definition of Done
- H3 explicitly addressed in documentation
- All figures generated programmatically
- Analysis notebook validated

---

## PHASE 10 — Statistical Validation

### Goal
Apply statistical rigor to experimental results. Multiple seeds, confidence intervals, effect sizes, and significance testing.

### Research Question Addressed
RQ1 (confidence): Are the observed degradation effects statistically significant and reproducible?

### Inputs
- E5, E6 results
- `docs/methodology/STATISTICAL_PROTOCOL.md`

### Outputs
- Statistical summary with confidence intervals
- Effect size estimates
- Significance tests

### Modules
- `src/statistics/bootstrap.py`
- `src/statistics/effect_size.py`
- `src/statistics/significance.py`

### Dependencies
- Phase 9 complete

### Acceptance Criteria
- [ ] Multiple seeds used (minimum as specified in `STATISTICAL_PROTOCOL.md`)
- [ ] Confidence intervals computed for primary metrics
- [ ] Effect size reported
- [ ] Statistical tests appropriate for the data type

### Experiments
- Repeated runs with multiple seeds (part of E5 design)

### Expected Artifacts
- `artifacts/tables/Table_06_statistical_results.*`

### Team Roles
- Evaluation/Statistics Engineer
- Research Lead: Statistical protocol compliance

### Definition of Done
- Statistical summary tables produced
- Protocol compliance documented

---

## PHASE 11 — Reproducibility & Ablations

### Goal
Verify full end-to-end reproducibility. Run ablation studies as specified. Document all findings.

### Research Question Addressed
RQ1 (robustness): Are results robust to implementation choices?

### Inputs
- All experiment configurations from Phases 5–10

### Outputs
- Reproduction report
- Ablation results (if planned)
- Final experiment registry

### Dependencies
- Phase 10 complete

### Acceptance Criteria
- [ ] All primary experiments reproducible from configuration files
- [ ] Reproduction produces matching results (within floating point tolerance)
- [ ] All experiment manifests valid and complete

### Experiments
- **E7: Missed-Update Transient Analysis** (if not completed in Phase 8)
- Ablation experiments as defined

### Definition of Done
- Reproduction verified independently
- Experiment registry complete

---

## PHASE 12 — Paper-Ready Results

### Goal
Generate all final paper figures, tables, and supplementary materials programmatically.

### Research Question Addressed
All — results package supports the full paper.

### Inputs
- All validated experiment results
- `docs/paper/PAPER_ALIGNMENT.md`
- `docs/paper/FIGURE_TABLE_STANDARD.md`

### Outputs
- All paper figures (PNG + PDF, high-resolution)
- All paper tables (LaTeX + CSV)
- Paper supplementary materials

### Dependencies
- Phase 11 complete

### Acceptance Criteria
- [ ] All figures generated programmatically (no manual editing)
- [ ] All tables generated from experimental results
- [ ] Figure and table naming follows standard in `FIGURE_TABLE_STANDARD.md`
- [ ] No fabricated results in any artifact

### Expected Artifacts
- `artifacts/figures/Fig_01_*` through `Fig_06_*`
- `artifacts/tables/Table_01_*` through `Table_06_*`
- `artifacts/reports/`

### Definition of Done
- All artifacts present and verified against experimental results
- Research Lead approved all figures and tables

---

## PHASE 13 — Final Packaging & Release

### Goal
Package the repository for public release, submit the paper, and archive the research artifact.

### Inputs
- Complete repository
- Paper draft
- Reviewer comments (if applicable)

### Outputs
- Tagged release on GitHub
- Zenodo DOI (or equivalent)
- Public dataset (or data card if data cannot be released)
- Final paper

### Dependencies
- Phase 12 complete
- Paper acceptance (or submission)

### Acceptance Criteria
- [ ] Repository passes all tests
- [ ] All secrets removed
- [ ] All experimental results reproducible
- [ ] README updated with final status
- [ ] Citation information added
- [ ] License verified

### Definition of Done
- GitHub release tagged
- DOI assigned
- Paper submitted

---

*This roadmap was established in Phase 0. Updates to phases require team discussion and must be reflected in an ADR.*
*Version: 1.0.0 — September 2026*
