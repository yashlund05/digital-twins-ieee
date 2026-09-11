# Contributing to the Digital Twin Power Grid Research Repository

> This is a multi-member academic research project. Contributions must follow the research integrity rules in `AI_RULES.md` and the collaboration workflow in `VIBECODING.md`.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Branch Strategy](#branch-strategy)
3. [Commit Conventions](#commit-conventions)
4. [Pull Request Process](#pull-request-process)
5. [Experiment Coordination](#experiment-coordination)
6. [Research Integrity](#research-integrity)
7. [Documentation Requirements](#documentation-requirements)

---

## Code of Conduct

This is an academic research project. All contributors are expected to:

- Maintain scientific honesty and research integrity
- Respect module ownership boundaries (see `CODEOWNERS`)
- Document significant decisions before implementing them
- Communicate methodology changes before making them
- Preserve all experimental results, including negative results

---

## Branch Strategy

### Branch Names

| Branch | Purpose |
|--------|---------|
| `main` | Stable, tagged releases only. Never commit directly. |
| `develop` | Integration branch. Requires passing CI. |
| `feature/<name>` | New code features or modules |
| `experiment/<id>-<description>` | Experiment implementations (e.g., `experiment/e5-staleness-sweep`) |
| `research/<topic>` | Research documentation, hypothesis development |
| `fix/<issue>` | Bug fixes |
| `docs/<topic>` | Documentation updates |
| `chore/<task>` | Maintenance tasks (deps, config, tooling) |

### Branch Rules

- Never push directly to `main` or `develop`
- All changes to `main` require a PR from `develop`
- All changes to `develop` require a reviewed PR
- Experiment branches should be merged only after the experiment is validated
- Delete branches after merging

---

## Commit Conventions

Commit messages follow this format:

```
<type>(<scope>): <short description>

[optional body]

[optional footers]
```

### Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature or module |
| `fix` | Bug fix |
| `experiment` | Experiment implementation or result |
| `research` | Research documentation or analysis |
| `docs` | Documentation only |
| `test` | Test additions or fixes |
| `refactor` | Code restructuring (no behavior change) |
| `chore` | Maintenance (deps, config, tooling) |

### Scope

Use the module or area affected:
- `sync`, `dt`, `forecast`, `anomaly`, `residuals`, `eval`, `data`, `cli`, `config`, `docs`, `tests`

### Examples

```
feat(sync): add configurable synchronization engine with AoI tracking

experiment(e5): add 60s staleness sweep configuration and runner

research: document anomaly detection degradation hypothesis (H3)

test(sync): validate synchronization age calculation edge cases

docs: update experiment matrix with E5 staleness sweep parameters

fix(dt): correct OpenDSS solver initialization for IEEE 33-bus

chore(deps): add opendssdirect to pyproject.toml
```

### Commit Rules

- Keep commits small and focused on a single change
- Write commit messages in the imperative mood ("add", not "added")
- Reference issues or ADRs in the footer: `Closes #12`, `ADR: docs/decisions/ADR-0003-...`
- Never commit secrets, API keys, or `.env` files
- Never commit raw dataset files >50MB
- Never commit generated model binaries without discussion

---

## Pull Request Process

### Before Opening a PR

- [ ] Follow the VIBECODING workflow (`VIBECODING.md`)
- [ ] All tests pass: `make test`
- [ ] Code is formatted: `make format`
- [ ] Documentation is updated for architectural changes
- [ ] ADR is created if a significant decision was made
- [ ] No secrets are committed: `make check-secrets`

### PR Description Must Include

- **Objective**: What does this PR accomplish?
- **Motivation**: Why is this change needed?
- **Changes**: List of files changed and what changed
- **Research Impact**: Does this affect the research question, hypothesis, or experimental design? (`YES/NO`, details if YES)
- **Methodology Flags**: List any `[METHODOLOGY CHANGE]` flags
- **Test Coverage**: What was tested?
- **Open Questions**: Anything that needs reviewer decision?

### Review Requirements

- At least one reviewer required for all PRs to `develop`
- Module owner review required for changes to owned modules (see `CODEOWNERS`)
- Research methodology changes require review from Research Lead
- Experiment configurations require review from Experiment Owner

### Merge Strategy

- Use **squash merge** for feature branches to keep `develop` history clean
- Use **merge commit** for `develop → main` to preserve the integration history
- Never force-push to `develop` or `main`

---

## Experiment Coordination

### Before Starting an Experiment

1. Create an experiment branch: `experiment/e<N>-<description>`
2. Create the experiment configuration in `configs/experiments/`
3. Announce the experiment in the team channel
4. Confirm the configuration is reviewed before running

### Experiment Naming

Every experiment run gets a unique run ID:

```
E<N>_<DESCRIPTOR>_<MODEL>_<INPUT>_SEED<S>_<YYYYMMDD>

Examples:
E5_STALENESS_IF_RAW_SEED42_20261001
E5_STALENESS_LSTMAE_RESIDUAL_SEED42_20261001
E3_BASELINE_IF_RAW_SEED42_20260915
```

### Experiment Output Rules

- Never overwrite a previous experiment run
- All runs stored at `experiments/runs/<run_id>/`
- Every run must have a `manifest.json`
- Failed runs must be preserved with `status: FAILED` in manifest
- Results committed to the repository must be validated

---

## Research Integrity

All contributors must read and follow `AI_RULES.md`.

**Key rules:**

- Never delete or suppress failed experiments
- Never change random seeds after seeing results
- Never tune models on the test set
- Never fabricate metrics or citations
- Report all results, including those that contradict hypotheses
- Distinguish clearly: `[ESTABLISHED]` | `[HYPOTHESIS]` | `[ASSUMPTION]` | `[OBSERVATION]` | `[CONCLUSION]`

---

## Documentation Requirements

### When to Update Documentation

| Change | Required Documentation Update |
|--------|-------------------------------|
| New module | Module docstring + `docs/architecture/SYSTEM_ARCHITECTURE.md` |
| Interface change | ADR + all docs referencing the interface |
| New experiment | `docs/experiments/EXPERIMENTS.md` + `configs/experiments/` |
| Methodology change | ADR + `docs/methodology/` relevant file |
| New configuration parameter | `configs/` YAML + Pydantic schema |
| New CLI command | `docs/` + CLI help text |

### ADR Convention

Create an ADR for:
- Significant architectural decisions
- Methodology changes that affect experiment comparability
- New dependencies added to the stack
- Changes to the experiment design (E1–E7)

ADR location: `docs/decisions/ADR-XXXX-<short-description>.md`

See `docs/decisions/ADR-0001-research-positioning.md` for the template.

---

*For questions about this repository, consult the team roles in `docs/onboarding/TEAM_ROLES.md`.*
