# Synchronization Engine Architecture

> **Component:** src/synchronization/
> **Research Role:** Implements the experimental independent variable
> **Version:** 1.0.0 — September 2026
> **Status:** Architecture specification — implementation in Phase 4

---

## Overview

The Synchronization Engine is the most research-critical component of this system. It controls the independent variable of the experimental study: **synchronization staleness**.

All synchronization logic is centralized in this module. No other module may implement synchronization timing, staleness calculation, or Age of Information tracking.

> [!IMPORTANT]
> Changes to this module directly affect the experimental independent variable. Every change requires:
> 1. An ADR in `docs/decisions/`
> 2. Team review
> 3. Documentation update
> 4. Experiment re-validation if any runs have been completed

---

## Core Concepts

### Physical Timestamp

`t_physical` — The wall-clock time of a physical grid measurement.

In the simulation context, this is the simulated time of the synthetic physical state.

### Digital Twin Timestamp

`t_dt` — The timestamp of the state currently held by the Digital Twin.

This is the time of the last physical state that was successfully synchronized into the DT.

### Synchronization Interval

`Δt_sync` — The configured time between synchronization attempts.

This is the **experimental independent variable**. It is set in `configs/synchronization.yaml` and swept across multiple values in Experiment E5.

**Experimental levels (Experiment E5):**

| Level | Interval | Interpretation |
|-------|----------|----------------|
| L0 | 0 s | Perfect synchronization (baseline) |
| L1 | 15 s | Near-real-time (approximates fast SCADA) |
| L2 | 30 s | Standard SCADA rate |
| L3 | 60 s | 1-minute interval |
| L4 | 120 s | 2-minute interval |
| L5 | 300 s | 5-minute interval |
| L6 | 600 s | 10-minute interval |
| L7 | 900 s | 15-minute interval (AMI boundary) |
| L8 | 1800 s | 30-minute interval |

> [!NOTE]
> The synchronization intervals are aligned with documented real-world data rates:
> PMU: 30–120 Hz, SCADA: 2–10 s, AMI: 15 min–1 hr (Liu et al., 2023).
> This alignment supports generalizability of results.

### Synchronization Age

`age_sync = t_physical - t_last_successful_sync`

The time elapsed since the last successful synchronization update. This is the primary staleness metric.

### Age of Information (AoI)

Following the formalization in Guo et al. (2026) and Shu et al. (2022):

`AoI(t) = t_reception - t_generation`

Where:
- `t_generation` = timestamp when the physical measurement was generated
- `t_reception` = timestamp when the measurement was received by the DT synchronization engine

In our simulation context, AoI is equivalent to synchronization age for successful updates. For missed updates, AoI continues to grow beyond the nominal interval.

### Successful Update

A synchronization event where the physical state is successfully transferred to the Digital Twin.

Successful update conditions:
- Update arrived within the configured interval
- Physical state is valid (passes sanity checks)
- DT solver converges with the new state

### Missed Update

A synchronization event where no physical state update is applied to the Digital Twin.

Causes (in simulation):
- Configurable missed-update rate (for Experiment E7)
- Update arrives outside the window (not applicable in controlled simulation)

### Stale State

The Digital Twin state when `age_sync > 0`.

The degree of staleness is quantified by `age_sync`. A stale DT state diverges from the physical system state as the physical system evolves without being mirrored in the DT.

### State Divergence

`divergence = ||x_physical(t) - x_dt(t)||`

The L2 norm of the difference between the current physical state vector and the DT state vector.

State divergence is expected to grow with synchronization age, though the rate of growth depends on the physical system dynamics and the rate of change of load.

---

## Missed Update Policies

When a synchronization update is missed, the engine applies a policy:

### hold_last_state (default)

The DT retains its last successfully synchronized state. The DT does not evolve between updates.

- **Effect on load estimation:** Predictions are based on a frozen (stale) state. Error grows as physical load evolves.
- **Effect on anomaly detection:** Residuals are computed against a frozen baseline. Large physical changes produce large residuals — potentially generating false positives.

### Other policies (future extension)

- `linear_extrapolation`: Linearly extrapolate from last known state
- `zero_input`: Reset DT inputs to zero (not recommended)

All policies are configurable in `configs/synchronization.yaml`.

---

## Synchronization Log Schema

Every synchronization event is logged with the following fields:

```json
{
  "event_id": "<uuid>",
  "run_id": "<experiment_run_id>",
  "physical_timestamp": 1234567890.0,
  "dt_timestamp": 1234567830.0,
  "last_sync_timestamp": 1234567830.0,
  "sync_age_seconds": 60.0,
  "aoi_seconds": 60.0,
  "update_interval_seconds": 60,
  "update_successful": true,
  "missed_updates_count": 0,
  "solver_time_ms": 12.3,
  "inference_time_ms": 5.7,
  "residual_magnitude": 0.042,
  "policy_applied": "hold_last_state"
}
```

---

## Module Structure

```
src/synchronization/
├── __init__.py          # Module interface
├── engine.py            # Core synchronization loop
├── scheduler.py         # Interval-based update scheduling
├── aoi.py               # Age of Information calculation
├── logger.py            # Synchronization event logging
├── policies.py          # Missed-update policies
└── state_tracker.py     # Physical vs. DT state divergence tracking
```

---

## Interface Contract

The synchronization engine exposes:

```python
class SynchronizationEngine:
    def __init__(self, config: SynchronizationConfig) -> None: ...

    def step(
        self,
        physical_state: GridState,
        current_time: float,
    ) -> SynchronizationResult:
        """
        Process one synchronization step.

        Returns the DT state after applying the synchronization policy.
        Always returns a valid DT state (stale or fresh).
        Logs the synchronization event.
        """
        ...

    @property
    def current_aoi(self) -> float:
        """Current Age of Information in seconds."""
        ...

    @property
    def sync_age(self) -> float:
        """Time since last successful update in seconds."""
        ...
```

---

## Testing Requirements

See `docs/architecture/TESTING_STRATEGY.md` for full testing specification.

Minimum required tests:

1. **Unit: AoI calculation** — Verify AoI = t_reception - t_generation for various intervals
2. **Unit: Synchronization age** — Verify age grows correctly between updates
3. **Unit: Hold-last-state policy** — Verify DT state does not change during missed updates
4. **Unit: Event logging** — Verify all log fields are written correctly
5. **Integration: DT + Sync pipeline** — Verify that synchronization engine correctly updates DT state
6. **Integration: Staleness sweep** — Verify that different intervals produce different AoI values

---

## References

- Fan & Zhao (2024): "synchronization gap" is "rarely quantified" — direct gap this module addresses
- Guo et al. (2026): AoI-aware scheduling framework (AoI formalism)
- Shu et al. (2022): AoI-aware Digital Twin resource management
- Zhao et al. (2023): DT error grows when sync is not maintained (component-level evidence)
- Liu et al. (2023): Multi-rate data fusion requirements (PMU/SCADA/AMI rates)

---

*Synchronization Engine specification v1.0.0 — Phase 0.*
*Implementation: Phase 4.*
