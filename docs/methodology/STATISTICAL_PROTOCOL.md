# Statistical Analysis Protocol

> **Version:** 1.0.0 — September 2026
> **Status:** Protocol specification — implementation in Phase 10

---

## Overview

This protocol defines the statistical framework for analyzing experimental results.

> [!NOTE]
> This protocol is defined before experiments are run to prevent post-hoc statistical design.
> Changing statistical methods after seeing results requires an ADR and full disclosure.

---

## Multiple Seeds

For primary experiments (E2, E3, E5), run with multiple seeds:

| Seed | Role |
|------|------|
| 42 | Primary seed (all experiments) |
| 123 | Replication seed 1 (Phase 10) |
| 456 | Replication seed 2 (Phase 10) |
| 789 | Replication seed 3 (Phase 10) |

**Minimum:** 4 seeds for confidence interval computation.

---

## Confidence Intervals

Bootstrap confidence intervals (95%) for all primary metrics:

```python
# Bootstrap CI procedure
n_bootstrap = 1000
alpha = 0.05
# Resample experiment results across seeds
# Report median and [alpha/2, 1-alpha/2] percentiles
```

---

## Degradation Analysis

For E6 (degradation profile analysis):

### Regression of performance vs. staleness

```
metric = f(staleness_interval)
```

Fit and compare:
1. Linear model: `metric = a * staleness + b`
2. Power law: `metric = a * staleness^b + c`
3. Piecewise linear: threshold detection

Report best-fit model with R² and residuals.

### Task sensitivity comparison (H3)

```
Relative degradation = (metric_stale - metric_baseline) / metric_baseline
```

Compare relative degradation slopes:
- Load estimation: MAPE relative degradation
- Anomaly detection: F1 relative degradation

Statistical test: paired t-test across staleness levels (or Wilcoxon signed-rank if non-normal).

> [!IMPORTANT]
> H3 is assessed as: **Supported / Contradicted / Inconclusive**.
> Do not cherry-pick a favorable interpretation.
> If results are inconclusive, report them as inconclusive.

---

## Effect Sizes

Report Cohen's d or equivalent for primary comparisons:
- Load estimation degradation effect across staleness levels
- Anomaly detection degradation effect across staleness levels
- Raw vs. residual performance difference

---

## Reporting Standards

| Item | Requirement |
|------|-------------|
| Point estimates | Always report |
| Confidence intervals | Always report (95% bootstrap) |
| Effect sizes | Report for primary comparisons |
| Number of seeds | Report explicitly |
| Statistical test used | Report with justification |
| Significance threshold | α = 0.05 (pre-specified here) |
| Multiple comparisons | Apply Bonferroni or Holm correction if >3 comparisons |

---

## What NOT to Do

- Do not select statistical tests after seeing results
- Do not report only significant results
- Do not p-hack by running more seeds until significance is achieved
- Do not cherry-pick the favorable confidence interval method
- Do not round p-values downward (report exact p-values)

---

*Statistical Protocol v1.0.0 — Phase 0.*
*Statistical analysis: Phase 10.*
