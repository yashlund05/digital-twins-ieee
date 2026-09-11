# GEMINI.md — Gemini / Antigravity Agent Instructions

> Instructions for Gemini-based agents (including Antigravity) operating inside this research repository.
> Also read: `AGENTS.md` (general), `AI_RULES.md` (governance), `VIBECODING.md` (workflow).

---

## Critical Context

You (Gemini / Antigravity) are operating inside a **multi-member academic research repository**.

This repository has:
- Multiple active contributors with defined ownership areas (see `CODEOWNERS`)
- Active experiments that must not be disrupted
- Strict research integrity requirements (see `AI_RULES.md`)
- Established architecture that must not be reorganized without justification

**You must not**:
- Randomly reorganize the repository structure
- Rename existing files without creating a migration path
- Reorganize `src/` modules without a documented reason and team notification
- Change experiment outputs, configurations, or manifests without authorization
- Make sweeping refactors that affect multiple team members' work

---

## Repository Reconnaissance Procedure

Before ANY modification, execute this sequence:

### Step 1 — Identify Affected Modules
```
Read AGENTS.md           → understand project context and rules
Read AI_RULES.md         → understand governance constraints
Read VIBECODING.md       → understand required workflow
```

### Step 2 — Read Architecture Documentation
```
docs/architecture/SYSTEM_ARCHITECTURE.md    → full system design
docs/architecture/SYNCHRONIZATION_ENGINE.md → sync subsystem
docs/architecture/TESTING_STRATEGY.md       → test approach
```

### Step 3 — Inspect Affected Modules
```
src/<relevant_module>/__init__.py           → exported interface
src/<relevant_module>/<target_file>.py      → current implementation
tests/<relevant_test_directory>/            → existing tests
```

### Step 4 — Check Prior Decisions
```
docs/decisions/ADR-*.md                     → prior architectural decisions
```

### Step 5 — Check Active Experiments
```
experiments/runs/                           → any runs in progress?
experiments/manifests/                      → locked configurations
```

---

## Architecture-First Workflow

1. **Read before writing.** Never modify without understanding the existing structure.
2. **Identify the minimal change.** Do not refactor beyond what the task requires.
3. **Check ownership.** Consult `CODEOWNERS` for the module owner before changing cross-cutting code.
4. **Preserve interfaces.** If you must change an interface, create an ADR and notify the team.

---

## Implementation Workflow

Follow the VIBECODING workflow for every task:

```
PLAN → INSPECT → DESIGN → IMPLEMENT → TEST → RUN → VALIDATE → DOCUMENT → COMMIT
```

### Planning
- State the objective and the files to be affected
- Identify any research implications (does this touch methodology?)
- Flag any methodology changes before implementing

### Inspection
- Read all relevant files first
- Do not guess at existing behavior — read the code

### Design
- Choose the minimal implementation that satisfies the requirement
- Reuse existing abstractions before creating new ones

### Implementation
- Write type-annotated code
- Add docstrings to all public functions
- Follow existing code style in the module

### Testing
- Write tests alongside implementation
- Check that existing tests still pass
- Add integration tests for cross-module changes

### Validation
- For experiment-related changes: verify reproducibility
- For synchronization changes: validate against `docs/architecture/SYNCHRONIZATION_ENGINE.md`
- For data changes: validate against `docs/methodology/DATA_PROTOCOL.md`

### Documentation
- Update `docs/` for architectural changes
- Create ADR for significant decisions
- Update the relevant `__init__.py` exports if public interface changed

### Commit
- Follow commit conventions in `CONTRIBUTING.md`
- Include affected module in commit message
- Reference any issue or ADR number

---

## Experiment Workflow

When working with experiments:

1. **Never modify an active experiment run**
2. **Never overwrite `experiments/runs/<run_id>/` contents**
3. **Configuration changes create new experiment configurations**, not overwrite existing ones
4. **Every experiment run gets a unique `run_id`**
5. **Manifests in `experiments/runs/<run_id>/manifest.json` are write-once**

---

## Synchronization Engine Rules

The synchronization engine at `src/synchronization/` is the most critical research component.

- **All synchronization interval logic lives in `src/synchronization/` only**
- **No other module implements synchronization timing**
- **Changes to synchronization logic require an ADR and team notification**
- **Synchronization parameters must come from configuration, never hard-coded**

---

## Documentation Workflow

When updating documentation:

- Do not remove existing content without replacement
- Do not change research positioning or hypothesis framing without team input
- Preserve academically cautious language ("we investigate", "our results suggest")
- Do not change labels: [ESTABLISHED], [HYPOTHESIS], [ASSUMPTION], [OBSERVATION], [CONCLUSION]

---

## Git Workflow

- Work on feature branches: `feature/*`, `experiment/*`, `research/*`, `docs/*`
- Never commit to `main` or `develop` directly
- Reference the task or issue in the branch name
- Small, focused commits over large sweeping commits
- Commit messages follow `CONTRIBUTING.md` conventions

---

## Contributor Coordination

- When a change affects another contributor's owned module (see `CODEOWNERS`), flag it explicitly
- Use issue templates in `.github/ISSUE_TEMPLATE/` for methodology or architecture changes
- Create a methodology change issue before implementing significant design changes

---

*This file applies to Gemini/Antigravity-based agents only. See `AGENTS.md` for general rules.*
