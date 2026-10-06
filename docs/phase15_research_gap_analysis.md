# Phase 15 — Research Gap Analysis & Journal Gap Matrix

**Target Venue:** IEEE Transactions on Smart Grid (IEEE TSG)  
**Date:** 2026-10-06  
**Auditor Mode:** Scientific Gap Analysis & Prioritization Matrix

---

## 1. Systemic Journal Gap Matrix

| Category | Current State in Repository | Required Level for IEEE TSG | Identified Gap | Severity | Required Action | Priority |
|---|---|---|---|:---:|---|:---:|
| **Manuscript Citations** | 6 out of 10 references have `[VERIFY]` placeholders | 100% verified, authoritative references (30–45 citations) | Placeholders trigger instant desk-rejection | **CRITICAL** | Populate `references.bib` with verified IEEE TSG/PES papers | **P0** |
| **Anomaly Threshold Portability** | Static 95th pct threshold from Seed 42 fails on other seeds ($\text{FPR}=1.0$) | Robust thresholding that generalizes across seeds | High seed variance (84.9%) invalidates AD multi-seed conclusions | **CRITICAL** | Calibrate threshold per-seed on validation set or use AoI-adaptive threshold | **P0** |
| **Simulation Realism** | Clean OpenDSS co-simulation; zero measurement noise | Realistic sensor noise and parameter uncertainty | Real telemetry is noisy; clean residuals may be an artifact | **HIGH** | Benchmark under 1% Gaussian noise ($\text{SNR}=40\,\text{dB}$) | **P1** |
| **Transition Discretization** | Grid jumps from $\Delta t = 1\,$s to $5\,$s | Sub-second or 1-second resolution around cliff | Change point $\text{AoI}^* \approx 5.0\,$s lacks experimental data at 2, 3, 4s | **HIGH** | Sweep $\Delta t \in \{1, 2, 3, 4, 5, 8, 10\}\,$s | **P1** |
| **Statistical Sample Size** | $N=5$ random seeds | $N \ge 10$ seeds for stable variance decomposition | ANOVA degrees of freedom too low; wide variance CIs | **MEDIUM** | Expand seed grid to $N=10$ or freeze model weights | **P1** |
| **Machine Learning Baselines** | IF and LSTM-AE for AD; Persistence, XGBoost, LSTM for LE | Classical baseline (OC-SVM) + modern DL baseline (GRU) | Reviewers will request GRU and One-Class SVM | **MEDIUM** | Add OC-SVM and GRU baselines | **P1** |
| **Metric Scale Distortion in $H_3$** | Bounded F1 vs. Unbounded MAPE log-linear regression | Scale-invariant degradation comparison | Slope contrast $\Delta\beta = -1.22$ could be metric scale artifact | **MEDIUM** | Add normalized bounded comparison (Normalized RMSE vs. PR-AUC) | **P1** |
| **Feeder Realism / DERs** | Passive residential loads only; balanced equivalent | Active feeder context or explicit DER discussion | Modern smart grids have solar PV, EV, and storage | **LOW-MED** | Clarify scope in paper; evaluate DER injection scenario | **P2** |
| **Communication Modeling** | Deterministic interval + i.i.d. Bernoulli drop | Realistic burst loss or stochastic latency | Real packet drops are bursty / Markovian | **LOW-MED** | Add Gilbert-Elliott burst loss ablation | **P2** |
| **Reproducibility Environment** | Python 3.14 native OpenDSS DLL crash | Deterministic cross-platform virtual container | Tests fail on newer Python runtimes | **LOW** | Pin Python $\le 3.11$ in Dockerfile / environment spec | **P2** |

---

## 2. Priority Classification Definition

- **P0 (Submission Blocker):** Must be resolved before the PDF is submitted to ScholarOne. Submitting with P0 issues guarantees desk rejection or immediate technical return without review.
- **P1 (Major Scientific Weakness):** Issues that peer reviewers will seize upon to justify a "Major Revision" or "Reject". Addressing these pre-empts reviewer criticisms and elevates paper credibility.
- **P2 (Important Improvement):** Strengthens paper depth, technical rigor, and defensibility, increasing score from borderline to strong accept.
- **P3 (Nice-to-Have):** Future work extensions that can be discussed in Section V without new experiments.
