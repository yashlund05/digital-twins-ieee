## Pull Request Description

### Summary of Changes
Briefly describe the purpose and substance of this PR.

### Related Issues
Closes #

### Affected Modules & Documentation
- [ ] `src/data/`
- [ ] `src/digital_twin/`
- [ ] `src/synchronization/`
- [ ] `src/forecasting/`
- [ ] `src/anomaly_detection/`
- [ ] `src/residuals/`
- [ ] `src/evaluation/`
- [ ] `src/statistics/`
- [ ] `src/visualization/`
- [ ] `src/experiments/`
- [ ] `src/cli/` / `src/utils/`
- [ ] `docs/`
- [ ] `configs/`
- [ ] `tests/`

---

## Research Integrity & Governance Checklist

Please confirm every item before requesting review:

- [ ] **No Fabricated Data or Metrics:** This PR contains only verifiable code and genuine results. No metrics or citations have been invented.
- [ ] **Hybrid Simulation Disclosure:** Any data generated or documented explicitly discloses the hybrid nature (IEEE 33-bus + Pecan Street patterns).
- [ ] **Interface & ADR Compliance:** If public interfaces or research methodologies were modified, an approved ADR in `docs/decisions/` is included in this PR.
- [ ] **Test Coverage:** All new public functions have unit tests in `tests/unit/`.
- [ ] **No Overwritten Experiments:** No files in `experiments/runs/` have been overwritten or deleted.
- [ ] **Static Analysis Passed:**
  - `black --check .`
  - `ruff check .`
  - `mypy src/`
  - `pytest` passes with 0 failures
- [ ] **Secrets & Credentials:** No `.env` secrets, API tokens, or hardcoded credentials are included.
