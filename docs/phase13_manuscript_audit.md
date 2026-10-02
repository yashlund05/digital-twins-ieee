# Phase 13 — Manuscript Claim-to-Evidence & Scientific Language Audit

## 1. Audit Overview

This document provides a detailed claim-by-claim audit for the manuscript:

> **Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin**

- Target Venue: IEEE Transactions on Smart Grid
- Audit Date: October 2, 2026
- Auditing Tools: `src.publication.claim_audit`, `src.publication.language_audit`, `src.publication.numerical_audit`

---

## 2. Claim-to-Evidence Traceability Matrix

| Claim ID | Quantitative Statement in Manuscript | Exact Value | Source Phase | Source File | Source Field | Cryptographic Hash | Verification |
|:---|:---|:---:|:---:|:---|:---|:---|:---:|
| `C01` | "physics-residual representation paired with an LSTM autoencoder achieves an anomaly detection F1 score of 0.978" | `0.977956` | Phase 7 E4 | `metrics.json` | `E4-4.test.f1` | Verified | **PASS** |
| `C02` | "outperforming the raw representation (F1 = 0.539)" | `0.538606` | Phase 7 E4 | `metrics.json` | `E4-3.test.f1` | Verified | **PASS** |
| `C03` | "isolation forest achieves F1 = 0.118 (raw)" | `0.117647` | Phase 7 E4 | `metrics.json` | `E4-1.test.f1` | Verified | **PASS** |
| `C04` | "and F1 = 0.089 (residual)" | `0.088727` | Phase 7 E4 | `metrics.json` | `E4-2.test.f1` | Verified | **PASS** |
| `C05` | "Δβ = -1.224" | `-1.223646` | Phase 10 E10 | `multiseed_h3_summary.csv` | `Multi-seed.delta_beta` | Verified | **PASS** |
| `C06` | "95% CI [-1.346, -1.113]" (lower) | `-1.346260` | Phase 10 E10 | `multiseed_h3_summary.csv` | `Multi-seed.ci_lower` | Verified | **PASS** |
| `C07` | "95% CI [-1.346, -1.113]" (upper) | `-1.113412` | Phase 10 E10 | `multiseed_h3_summary.csv` | `Multi-seed.ci_upper` | Verified | **PASS** |
| `C08` | "p = 1.000" | `1.0` | Phase 10 E10 | `multiseed_h3_summary.csv` | `Multi-seed.p_value_slope` | Verified | **PASS** |
| `C09` | "H3 is not supported" | `NOT_SUPPORTED` | Phase 10 E10 | `multiseed_h3_summary.csv` | `Multi-seed.decision` | Verified | **PASS** |
| `C10` | "24 conditions per seed" | `24` | Phase 8 E5 | `comparison.csv` | `condition_id.nunique` | Verified | **PASS** |
| `C11` | "120 total seed-conditions" | `120` | Phase 10 E10 | `seed_results.csv` | `seed_condition.nunique` | Verified | **PASS** |
| `C12` | "Eight controlled ablations (A1–A8)" | `88` rows / `8` IDs | Phase 11 E11 | `table_02_ablation_results.csv` | `row_count` / `nunique` | Verified | **PASS** |
| `C13` | "estimated change point occurs at AoI ≈ 0.0 s" | `0.0` | Phase 11 E11 | `table_04_change_point_analysis.csv` | `estimated_transition_aoi_seconds` | Verified | **PASS** |

---

## 3. Language Audit Results

The manuscript LaTeX and table files were audited against the extended prohibited phrases list:

- **Prohibited Causal Language**: Zero occurrences of `causes`, `proves that`, `confirms causality`, `causal mechanism`.
- **Prohibited Universal Claims**: Zero occurrences of `always`, `never fails`, `in all cases`, `universally superior`, `universal threshold`.
- **Prohibited Certainty Language**: Zero occurrences of `certainly`, `undoubtedly`, `conclusively proves`, `definitively shows`.
- **H3 Reversal Language**: Zero occurrences claiming H3 was supported or confirmed.
- **Qualified Language**: All cautionary terms ("significant", "optimal") are qualified with empirical context ("statistically significant at $\alpha = 0.05$", "evaluated empirical operating point").

---

## 4. Citation and Reference Verification

References in `manuscript/references.bib` are classified into two categories:

1. **Established Literature (Full Details)**:
   - Liu et al. (2008) — Isolation Forest (`ref_isolation_forest`)
   - Chen & Guestrin (2016) — XGBoost (`ref_xgboost`)
   - Baran & Wu (1989) — IEEE 33-Bus Radial Feeder (`ref_ieee33bus`)
   - OpenDSS Documentation — EPRI (`ref_opendss`)
   - Pecan Street Dataport — Pecan Street Inc. (`ref_pecan_street`)

2. **Placeholder / Team Confirmation Required (`[VERIFY]`)**:
   - `ref_dt_survey`: Survey on Digital Twin in power systems
   - `ref_ad_survey`: Survey on Anomaly Detection in smart grids
   - `ref_aoi_theory`: Age of Information introductory survey
   - `ref_lstm_ae`: LSTM autoencoder anomaly detection reference
   - `ref_lstm_forecast`: LSTM load forecasting reference

> [!NOTE]
> All entries marked `[VERIFY]` must be confirmed with specific citations by the co-authors before journal upload. No fictitious publication details or non-existent authors were fabricated.
