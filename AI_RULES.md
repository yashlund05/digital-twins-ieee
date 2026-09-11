# AI_RULES.md — Central AI Governance Document

> This is the authoritative governance document for all AI agents operating in this repository.
> All agent-specific files (AGENTS.md, CLAUDE.md, GEMINI.md, CODEX.md) defer to this document.

---

## Research Integrity — The Non-Negotiable Core

This is an academic research project. The results will be submitted for peer review.
Violating research integrity rules is not recoverable — it can invalidate the entire study.

### NEVER DO

#### Results Integrity
- [ ] Invent experimental results
- [ ] Fabricate performance metrics (MAE, RMSE, MAPE, F1, PR-AUC, ROC-AUC, etc.)
- [ ] Invent dataset statistics
- [ ] Fabricate literature citations or DOIs
- [ ] Claim an experiment was executed when it was not
- [ ] Report estimated or projected results as actual experimental outputs

#### Experimental Design
- [ ] Silently change the research question or hypothesis
- [ ] Silently alter experimental parameters
- [ ] Silently change the train/test/validation split boundaries
- [ ] Silently change data preprocessing steps
- [ ] Silently alter anomaly injection parameters
- [ ] Silently alter synchronization interval definitions
- [ ] Tune models using test set data
- [ ] Select anomaly labels after observing model performance

#### Random Seed and Stochasticity
- [ ] Change random seeds without documenting the change in the experiment configuration
- [ ] Run multiple seeds and report only the best-performing seed without disclosing selection
- [ ] Cherry-pick favorable seeds after observing results

#### Result Reporting
- [ ] Delete or suppress failed experiments
- [ ] Remove inconvenient experimental results
- [ ] Report only favorable detector configurations
- [ ] Report only favorable synchronization intervals
- [ ] Hide negative results
- [ ] Omit failed convergence runs from reporting

#### Data Integrity
- [ ] Modify raw data files in `data/raw/`
- [ ] Overwrite experiment outputs without provenance record
- [ ] Fabricate or impute data beyond what the protocol specifies
- [ ] Describe the hybrid simulation dataset as real field measurements

#### Security and Credentials
- [ ] Commit API keys, tokens, or passwords
- [ ] Commit `.env` files
- [ ] Hard-code machine-specific absolute paths
- [ ] Commit private or proprietary datasets
- [ ] Commit generated model binaries without intentional versioning

#### Architecture
- [ ] Reorganize the repository structure without justification
- [ ] Change module interfaces without an ADR
- [ ] Add major new dependencies without justification
- [ ] Scatter synchronization logic outside `src/synchronization/`

---

### ALWAYS DO

#### Reproducibility
- [x] Record the random seed in every experiment manifest
- [x] Record the git commit hash in every experiment manifest
- [x] Record the configuration file version in every experiment manifest
- [x] Record the dataset version in every experiment manifest
- [x] Record the software environment (Python version, package versions) in every experiment manifest
- [x] Timestamp every experiment run
- [x] Use configuration files for all experimental parameters
- [x] Store experiment manifests at `experiments/runs/<run_id>/manifest.json`

#### Scientific Honesty
- [x] Report all experimental conditions, including those that perform poorly
- [x] Preserve failed experiment metadata even if results are negative
- [x] Explicitly state when results contradict a hypothesis
- [x] Use academically cautious language: "we investigate", "we quantify", "our results suggest", "within the evaluated topology"
- [x] Distinguish between: established facts | project hypotheses | assumptions | observations | conclusions

#### Documentation
- [x] Update `docs/` when architecture changes
- [x] Create an ADR for every significant methodological or architectural decision
- [x] Update the experiment manifest when experiment parameters change
- [x] Record the reason for any change to experimental design

#### Testing
- [x] Test changes before committing
- [x] Preserve regression tests
- [x] Run validation tests before any experiment is declared valid

---

## Hypothesis vs. Fact Distinction

The repository must clearly label all claims:

| Label | Meaning | Example |
|-------|---------|------|
| **[ESTABLISHED]** | Supported by peer-reviewed literature | LSTM achieves MAPE ~3.38% on residential STLF (Kong et al., 2019) |
| **[HYPOTHESIS]** | Proposed but not yet tested | H3: Anomaly detection degrades faster than load estimation |
| **[ASSUMPTION]** | Working assumption, not tested | Pecan Street load patterns are representative for mapping |
| **[OBSERVATION]** | Seen in current experiment run | Isolation Forest F1 drops at 300s interval |
| **[CONCLUSION]** | Verified across multiple runs and seeds | (None yet — experiments not started) |

---

## Forbidden Language

AI agents must not write:

- "first ever" — unless verified by systematic literature review
- "completely novel" — use "to the best of our verified search, no prior study..."
- "proves" — use "our results suggest" or "our experimental results indicate"
- "state-of-the-art" — unless verified against current benchmarks
- "solves" — use "addresses" or "investigates"
- "universally" — results are specific to the evaluated conditions
- "achieves X%" — without an actual completed experiment backing the claim
- "experiments show" — without an actual completed experiment

---

## Experiment Provenance Chain

Every result must be traceable:

```
config file → experiment run → manifest.json → results → figures → paper
```

If any link in the chain is broken or fabricated, the result is invalid.

---

## Escalation

If an AI agent encounters a situation where following these rules conflicts with a user request:

1. **State the conflict explicitly**
2. **Do not silently violate the rules**
3. **Propose an alternative that maintains integrity**

For example: if asked to "show sample results" for an experiment that has not been run, an AI agent must explicitly state that no experiment has been run and offer to show the result schema or placeholder structure instead.

---

*Last updated: September 2026*
*Version: 1.0.0*
*Status: Authoritative*
