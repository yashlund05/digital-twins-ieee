---
name: Methodology Change
about: Propose a change to experimental protocol, data splitting, baseline models, or metrics
title: "[METHODOLOGY]: "
labels: ["methodology", "needs-adr"]
assignees: ""
---

> [!WARNING]
> Methodology changes alter experimental comparability and reproducibility. Any approved methodology change requires an Architectural Decision Record (ADR) in `docs/decisions/` and may invalidate previously collected experimental runs.

### Proposed Methodology Modification
Describe the exact modification proposed (e.g. data preprocessing, split boundaries, metric formula, model hyperparameter protocol).

### Scientific Rationale
Why is this change necessary? Did an assumption break or did new theoretical insights emerge?

### Affected Subsystems & Documents
- [ ] `docs/methodology/DATA_PROTOCOL.md`
- [ ] `docs/methodology/REPRODUCIBILITY.md`
- [ ] `docs/methodology/STATISTICAL_PROTOCOL.md`
- [ ] `docs/architecture/SYNCHRONIZATION_ENGINE.md`
- [ ] Existing experiment runs in `experiments/runs/`

### Impact on Historical Experiments
- Does this change require rerunning existing canonical experiments (E1–E7)?
- [ ] No — purely prospective for new experiments.
- [ ] Yes — previous runs will be archived and marked as deprecated in manifests.

### Required ADR Reference
- Link to corresponding ADR: `docs/decisions/ADR-XXXX-<title>.md`
