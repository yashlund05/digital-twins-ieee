# Phase 15 — Reproducibility & Cryptographic Provenance Audit

**Target Venue:** IEEE Transactions on Smart Grid  
**Auditor Mode:** Scientific Reproducibility & Cryptographic Verification Auditor  
**Reproducibility Score:** 92/100 (Grade: A)

---

## 1. Verified Cryptographic Pipeline

1. **Deterministic Hashing:** Every experimental execution generates a canonical `manifest.json` containing SHA-256 hashes of all input configurations, trained model binaries, parquet timeseries, output tables, and figures.
2. **Deterministic Random Seed Control:** All stochasticity in Python `random`, NumPy `np.random`, PyTorch CPU/CUDA, and Scikit-Learn is bound to explicit seeds (`42, 123, 456, 789, 101112`).
3. **Historical Numerical Equivalence:** In Phase 11 and Phase 14 audits, historical Phase 7 baseline metrics were independently reproduced with absolute differences $< 5.0 \times 10^{-7}$ (`abs_diff = 4.03e-7` on LSTM-AE raw $F_1$, `abs_diff = 8.82e-8` on LSTM-AE residual $F_1$).
4. **Figure-to-Source Traceability:** Every one of the 8 publication figures traces directly to an unmanipulated source CSV in `experiments/runs/E12_PUBLICATION_ARTIFACTS_20261002/source_data/`.

---

## 2. Identified Reproducibility Gaps
1. **Runtime Dependency Crash under Python 3.14:** The current local environment runs Python 3.14.6, causing the compiled OpenDSS C backend (`dss_python_backend`) to crash on Windows DLL loading. The framework requires Python 3.10 or 3.11.
2. **Missing Dockerfile:** While environment metadata and package versions are logged in manifests, a pinned `Dockerfile` or `conda-lock.yml` is recommended for permanent public archiving on GitHub / IEEE DataPort.
