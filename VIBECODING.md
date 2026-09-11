# VIBECODING.md — Human + AI Collaboration Workflow

> The authoritative workflow document for all human + AI development in this repository.
> Every AI coding task, whether initiated by a human or an agent, MUST follow this workflow.

---

## The VIBECODING Workflow

Every task in this repository follows this exact sequence:

```
 PLAN
  ↓
 INSPECT
  ↓
 DESIGN
  ↓
 IMPLEMENT
  ↓
 TEST
  ↓
 RUN
  ↓
 VALIDATE
  ↓
 DOCUMENT
  ↓
 COMMIT
```

No step may be skipped. If a step cannot be completed, the reason must be documented.

---

## Step Definitions

### PLAN
Before touching any file:

- State the objective clearly
- State why this change is needed
- Identify which files will be affected
- Identify which modules will be affected
- Identify whether the task has research implications
- Identify whether the task has methodology implications
- Confirm with the team if the task crosses module ownership boundaries

### INSPECT
Read before writing:

- Read all existing code in affected modules
- Read relevant documentation in `docs/`
- Read relevant ADRs in `docs/decisions/`
- Read existing tests for affected modules
- Understand the current behavior before changing it

**If inspection reveals unexpected complexity or design, stop and re-plan.**

### DESIGN
Before writing code:

- Choose the implementation approach
- State assumptions explicitly
- Identify tradeoffs
- Identify which abstractions to reuse
- Identify whether a new ADR is needed
- Identify whether the design affects experiment comparability

### IMPLEMENT
- Write code that satisfies the design
- Follow coding standards in `AGENTS.md`
- Type-annotate all public functions
- Add docstrings
- Handle errors explicitly
- Use configuration, never hard-code parameters

### TEST
- Write or update unit tests
- Write or update integration tests if cross-module
- Run the full test suite: `make test`
- Fix failures before proceeding

### RUN
For experiment-related changes:

- Run the affected experiment with the new code
- Verify the output format matches expected schema
- Verify the manifest is written correctly
- Verify logs are produced

For non-experiment changes:

- Verify the change works end-to-end
- Run affected CLI commands if applicable

### VALIDATE
- Confirm the output matches the objective
- For experiments: confirm no temporal leakage, correct splits, correct seed
- For synchronization changes: confirm AoI and staleness calculations match `docs/architecture/SYNCHRONIZATION_ENGINE.md`
- For data changes: confirm conformance to `docs/methodology/DATA_PROTOCOL.md`
- For ML changes: confirm metric computation matches `docs/methodology/STATISTICAL_PROTOCOL.md`

### DOCUMENT
- Update `docs/` for any architecture changes
- Create or update ADR if a significant decision was made
- Update the relevant module's docstring/README if behavior changed
- Update `PHASES.md` task status if a phase milestone was completed

### COMMIT
- Stage only the intended changes
- Write a commit message following `CONTRIBUTING.md` conventions
- Reference any related issue or ADR
- Confirm no secrets, API keys, or raw data are staged
- Push to the correct branch (never `main` directly)

---

## Standard Task Template

For every AI-assisted task, fill out this template before starting:

```
TASK:
  [Brief name of the task]

OBJECTIVE:
  [What this task achieves]

WHY:
  [Why this task is needed now]

FILES AFFECTED:
  [List of files that will be created or modified]

DEPENDENCIES:
  [Other modules or tasks this depends on]

RESEARCH IMPACT:
  [Does this affect the research question, hypothesis, or experimental design?]
  [YES / NO — if YES, describe the impact]

IMPLEMENTATION PLAN:
  [Step-by-step description of the implementation]

TEST PLAN:
  [What tests will be written or updated]

EXPERIMENT IMPACT:
  [Does this affect any existing or planned experiments?]
  [YES / NO — if YES, list affected experiments and describe the impact]

EXPECTED OUTPUT:
  [What the output should look like when the task is complete]

ACTUAL OUTPUT:
  [Filled in after implementation]

DOCUMENTATION UPDATED:
  [List of documentation files updated]
```

---

## Mandatory Methodology Change Declaration

An AI agent MUST explicitly declare when a task changes any of the following:

| Change | Declaration Required | ADR Required |
|--------|---------------------|---------------|
| Research question or hypothesis | **[HYPOTHESIS CHANGE]** | Yes |
| Synchronization interval logic | **[SYNC METHODOLOGY CHANGE]** | Yes |
| Experimental design (E1–E7) | **[EXPERIMENT DESIGN CHANGE]** | Yes |
| Evaluation metrics | **[METRIC METHODOLOGY CHANGE]** | Depends |
| Data generation or processing | **[DATA METHODOLOGY CHANGE]** | Depends |
| Anomaly injection | **[ANOMALY METHODOLOGY CHANGE]** | Yes |
| Model architecture | **[MODEL METHODOLOGY CHANGE]** | Depends |
| Train/val/test split | **[SPLIT METHODOLOGY CHANGE]** | Yes |
| Random seed handling | **[SEED METHODOLOGY CHANGE]** | Yes |
| Paper-facing result generation | **[RESULT METHODOLOGY CHANGE]** | Yes |

Declarations must appear in:
- The task template (RESEARCH IMPACT section)
- The PR description
- The commit message (as a trailer or flag)
- An ADR (if ADR Required = Yes)

---

## Forbidden Shortcuts

| Shortcut | Why Forbidden |
|----------|---------------|
| Skipping INSPECT | Leads to duplicate implementations, broken interfaces |
| Skipping TEST | Introduces silent bugs into the experiment pipeline |
| Skipping DOCUMENT | Breaks the paper → code traceability chain |
| Implementing without a task template | Loses research context |
| Committing without review | Bypasses research integrity checks |
| Hard-coding parameters | Breaks reproducibility |
| Notebook-only experiments | Not reproducible from CLI |

---

## When a Task Reveals Unexpected Complexity

If, during INSPECT or DESIGN, you discover that the task is more complex than anticipated:

1. **Stop**
2. **Document what you found**
3. **Revise the task template with updated scope**
4. **Confirm with the team before proceeding**
5. **Do not silently expand the scope of a task**

---

## Experiment-Specific Workflow Addition

For any task that produces or modifies experiment results:

```
Before RUN:
  □ Confirm config file is version-controlled
  □ Confirm random seed is set in config
  □ Confirm git tree is clean (no uncommitted changes to src/)
  □ Confirm data splits are frozen
  □ Confirm test set has not been used for any tuning

After RUN:
  □ Confirm manifest.json was written
  □ Confirm metrics.json was written
  □ Confirm all expected output files exist
  □ Confirm run_id is unique
  □ Confirm no previous run was overwritten
```

---

*This document is the authoritative workflow reference for all contributors (human and AI).*
*Version: 1.0.0 — September 2026*
