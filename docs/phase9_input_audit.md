# Phase 9 — Input Audit & Provenance Verification

> **Audit Objective:** Systematically verify the availability, provenance, and validity of Phase 8 Experiment E5 artifacts prior to joint statistical analysis and hypothesis testing.

---

## 1. Inventory of Available E5 Experiment Runs

| Run Directory | Created Timestamp | Condition Count | Baseline Equivalence ($\Delta t = 0, P = 0$) | Implementation Provenance | Valid for Phase 9 Analysis? |
|---|---|:---:|:---:|---|:---:|
| `experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930` | 2026-09-30 20:44 | **24** | **PASS** (Res LSTM-AE F1 = 0.9780) | Post-reconciliation implementation (frozen Phase 7 E4 models, 64 features). | **YES (PRIMARY)** |
| `experiments/runs/E5_BASELINE_RECONCILIATION_SEED42_20260930` | 2026-09-30 17:46 | 1 | **PASS** (Res LSTM-AE F1 = 0.9780) | Post-reconciliation verification run (`--baseline-only`). | Verification only |
| `experiments/runs/E5_STALENESS_SWEEP_SEED42_20260930` | 2026-09-30 16:26 | 24 | **FAIL** (Res LSTM-AE F1 = 0.7022) | Pre-reconciliation implementation (retrained 10-epoch LSTM, 193 features). | **NO** (Superseded) |

---

## 2. Detailed Audit Findings

### 2.1 Condition Count
- Required by Phase 8/9 Protocol: **24 conditions** ($6 \text{ intervals} \times 4 \text{ drop rates}$).
- Valid Corrected Run: `E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930` contains all **24 conditions**.
- Missing conditions: **0**.

### 2.2 Seed Count
- Evaluated seeds: `seed = 42`.
- Single-seed experimental design; multi-seed statistical uncertainty is delegated to Phase 10.

### 2.3 Baseline Equivalence Verification
- Raw Isolation Forest: F1 = 0.117647 (E4: 0.117647) — **PASS**
- Residual Isolation Forest: F1 = 0.088727 (E4: 0.088727) — **PASS**
- Raw LSTM Autoencoder: F1 = 0.538606 (E4: 0.538606) — **PASS**
- Residual LSTM Autoencoder: F1 = 0.977956 (E4: 0.977956) — **PASS**
- Overall Baseline Equivalence Status: **100% BITWISE PASS**.

### 2.4 Artifact Completeness Check
All 8 required artifacts are verified present and non-empty in `E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930/`:
1. `manifest.json`: Verified.
2. `config_snapshot.yaml`: Verified.
3. `aoi_statistics.json`: Verified (24 conditions).
4. `comparison.csv`: Verified (168 model rows).
5. `metrics.json`: Verified (complete hierarchical dictionary).
6. `predictions.parquet`: Verified (pointwise test predictions across all conditions).
7. `synchronization_logs.parquet`: Verified (tick-by-tick logs).
8. `summary.md`: Verified.

**Conclusion:** `experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930` is the single authoritative, validated input dataset for Phase 9 analysis.
