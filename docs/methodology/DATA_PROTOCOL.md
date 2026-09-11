# Data Protocol

> **Version:** 1.0.0 — September 2026
> **Status:** Protocol specification — implementation in Phase 2

---

## Dataset Designation

> [!IMPORTANT]
> **This project uses a Hybrid Simulation Dataset.**
>
> The dataset is composed of:
> - **IEEE 33-bus benchmark feeder** (network topology and parameters)
> - **Pecan Street Dataport** (real residential consumption patterns)
> - **Synthetic fault injection** (anomaly labels)
>
> This dataset does NOT represent real field measurements of the IEEE 33-bus feeder.
> Pecan Street data provides residential consumption **patterns** for mapping to the IEEE topology.
> The mapping is a research design choice, not a field measurement procedure.
>
> All results and conclusions are qualified to this hybrid simulation context.

---

## IEEE 33-Bus Topology

### Source

Baran & Wu (1989) IEEE 33-bus radial distribution test feeder, widely used as a benchmark in distribution-level DT research (Rossi & Benigni, 2024; Li et al., 2024; Li et al., 2022).

### Parameters

| Parameter | Value |
|-----------|-------|
| Number of buses | 33 |
| Slack bus | Bus 1 |
| Load buses | Buses 2–33 (32 buses) |
| Base voltage | 12.66 kV |
| Base power | 100 MVA |
| Configuration | Radial |
| Branches | 32 |

### Simulation Platform

OpenDSS (primary) via `opendssdirect.py` Python bindings.

OpenDSS is selected based on its established use in distribution-level DT research:
- Rossi & Benigni (2024): Practical DT of distribution system
- Pazouki & Kargarian (2022): Distribution grid DT with OpenDSS
- Li et al. (2024): PINN-based state estimation on IEEE 33-bus in OpenDSS

---

## Pecan Street Dataport

### Source

Pecan Street Inc. Dataport: https://dataport.pecanstreet.org

### Dataset Characteristics

| Property | Value |
|----------|-------|
| Type | Real residential smart meter data |
| Location | Austin, Texas, USA |
| Resolution | 1-minute (subset), 15-minute (primary) |
| Coverage | ~1,000+ homes, multi-year |
| Sub-metering | HVAC, EV, solar, whole-home |
| Format | CSV via API or bulk download |

### Data Access

Pecan Street data requires registration and agreement to data use terms at:
https://dataport.pecanstreet.org

Credentials are stored in `.env` (never committed). See `.env.example`.

### Known Limitations

| Limitation | Severity | Treatment |
|------------|----------|----------|
| Texas climate — may not generalize to other regions | Moderate | Document as scope limitation |
| Voluntary participants — potential self-selection bias | Low-Moderate | Acknowledge in limitations |
| Data quality varies across homes | Low | Apply cleaning pipeline |
| 1-minute resolution limited to a subset | Low | Use 15-minute resolution as primary |
| Residential loads only — IEEE 33-bus has industrial loads | Moderate | Scale and diversify via mapping protocol |

---

## Mapping Protocol

### Overview

Pecan Street residential load profiles are mapped to IEEE 33-bus nodes to create the virtual physical system state that drives the Digital Twin.

> [!NOTE]
> This mapping is a research design decision. The resulting dataset is a
> hybrid simulation — not a real-world measurement of the IEEE feeder.
> The mapping protocol must be fully documented and published.

### Mapping Procedure

**[PLACEHOLDER — mapping decisions to be finalized in Phase 2]**

The mapping procedure will address:

1. **Home-to-bus assignment:**
   - Strategy to be determined (random assignment, clustering by load magnitude, or rule-based)
   - Each of the 32 load buses receives at least one home's profile
   - Multiple homes per bus are aggregated (summed)

2. **Load scaling:**
   - Pecan Street residential loads (kW range) scaled to match IEEE 33-bus nominal loading
   - Scaling factor derived from IEEE 33-bus reference load data
   - Scaling applied per bus, not globally

3. **Temporal alignment:**
   - Pecan Street timestamps are in US Central time
   - Timestamps must be normalized to a consistent reference frame
   - Temporal gaps (missing data) are handled by forward-fill up to 60 minutes

4. **Diversity:**
   - Buses are assigned different home profiles to ensure load diversity
   - Industrial-scale buses (if any) use aggregated profiles scaled to appropriate levels

5. **Reproducibility:**
   - Mapping is deterministic given fixed random seed
   - Mapping configuration stored in `configs/data.yaml`
   - Mapping output stored at `data/interim/mapping_config.json`

### Documentation Commitment

The final mapping protocol will be documented here (Phase 2) and released as part of the reproducibility package.

---

## Synthetic Anomaly Generation

### Design Principles

- Anomalies are injected AFTER the normal load profile is established
- Anomaly injection parameters are fully specified in `configs/data.yaml`
- Injection is reproducible given a fixed seed
- Ground truth labels are stored separately from features

### Anomaly Types

| Fault Type | Description | Duration |
|------------|-------------|----------|
| voltage_sag | Sudden voltage magnitude reduction | 4 timesteps (configurable) |
| load_spike | Sudden load increase above expected | 4 timesteps (configurable) |
| phase_imbalance | Asymmetric loading across nodes | 4 timesteps (configurable) |

### Anomaly Rate

5% of timesteps contain anomalies (configurable in `configs/data.yaml`).

> [!CAUTION]
> Anomaly labels must NEVER be used in model training.
> They are reserved for evaluation only.
> Verify this constraint in `tests/validation/test_data_integrity.py`.

---

## Train / Validation / Test Split

### Split Strategy

**Temporal split — no shuffling.**

| Split | Proportion | Purpose |
|-------|-----------|----------|
| Train | 70% | Model training |
| Validation | 15% | Hyperparameter tuning, threshold selection |
| Test | 15% | Final evaluation (one use only) |

### Temporal Ordering

```
[Train][  Validation  ][    Test    ]
|------|--------------|------------|---> time
```

Test indices > all validation indices > all training indices.

> [!CAUTION]
> **No random shuffling before splitting.** Temporal leakage prevention is critical.
> Shuffled splits in time series data introduce future information into training.
> Verified in `tests/unit/test_splitter.py` and `tests/validation/test_data_integrity.py`.

### Test Set Rules

- The test set is evaluated ONCE per model, at the end of training
- No threshold tuning on the test set
- No model selection based on test set performance
- If a model must be retrained after seeing test results, the test results from the retrained model are clearly labeled as INVALID for the primary experiment

---

## Feature Engineering

### Temporal Features (all models)

- Hour of day (0–23)
- Day of week (0–6)
- Month (1–12)
- Is weekend (boolean)

### Lag Features (tabular models: XGBoost, IF)

- lag_1: previous timestep
- lag_24: 24-step lag (daily pattern at 15-min resolution = 6 hours)
- lag_96: 96-step lag (daily pattern at 15-min resolution = 24 hours)

### Synchronization Features (E5 investigation)

- sync_age_seconds: Age of the current DT state (from sync engine log)

> [!NOTE]
> Including sync_age as a feature is an optional analysis component.
> It does NOT imply that the models are given access to future information.
> Sync age at prediction time reflects the current (stale) state, not future states.

---

## Normalization

- Default: min-max normalization per bus per split period
- Normalization parameters are computed on the training split ONLY
- Same parameters applied to validation and test splits
- Stored at `data/interim/normalization_params.json`

---

## Timestamp Handling

- All timestamps stored as Unix epoch seconds (float)
- Timezone: UTC (normalized from Pecan Street US Central)
- Resolution: 15-minute intervals (primary)
- Synchronization engine uses the same timestamp reference

---

*Data Protocol v1.0.0 — Phase 0.*
*Mapping decisions to be finalized and documented in Phase 2.*
