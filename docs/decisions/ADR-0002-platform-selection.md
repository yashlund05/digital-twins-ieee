# ADR-0002: Simulation Platform and Machine Learning Stack Selection

> **Status:** Accepted
> **Date:** 2026-09-11
> **Deciders:** Integration Lead (@INTEGRATION_LEAD), Research Lead (@RESEARCH_LEAD), DT Owner (@DT_OWNER), ML Owner (@ML_OWNER)
> **Consulted:** Entire Team
> **Informed:** All Contributors

---

## 1. Context

To evaluate the impact of Digital Twin synchronization staleness on an electrical distribution network, we require:
1. An accurate, computationally efficient, physics-based power flow simulation platform capable of solving quasi-static time-series (QSTS) power flows on benchmark distribution feeders.
2. A machine learning and numerical computation stack capable of deterministic execution, reproducibility, and high-performance training/inference for time-series forecasting and unsupervised anomaly detection.
3. Open-source licensing and cross-platform operability to ensure total experimental reproducibility across academic research environments.

---

## 2. Decision

We select the following core technical stack:

### Power System Simulation
- **Platform:** **OpenDSS** (Electric Power Research Institute - EPRI) via the **OpenDSSDirect.py** Python interface.
- **Feeder Model:** **IEEE 33-bus radial distribution test feeder** (Baran & Wu, 1989 benchmark).
- **Simulation Mode:** Quasi-Static Time-Series (QSTS) with 1-second to 1-minute resolution time steps.

### Machine Learning & Data Processing
- **Deep Learning Framework:** **PyTorch** ($\ge 2.0.0$) for PyTorch-based models (LSTM and LSTM Autoencoder), enabling explicit control over CUDA/CPU seeds, deterministic algorithms (`torch.use_deterministic_algorithms`), and clean gradient isolation.
- **Tree-Based Ensembles:** **XGBoost** ($\ge 2.0.0$) for gradient boosted regression in load estimation.
- **Statistical & Unsupervised Learning:** **scikit-learn** ($\ge 1.3.0$) for `IsolationForest`, preprocessing scalers, and metric utilities.
- **Numerical Arrays & Dataframes:** **NumPy** ($\ge 1.24.0$) and **Pandas** ($\ge 2.0.0$).

### Experiment Configuration & Verification
- **Configuration Engine:** **PyYAML** + **Pydantic** ($\ge 2.0.0$) schemas for strictly typed, validated configuration files in `configs/`.
- **Testing Framework:** **pytest** ($\ge 7.4.0$) with coverage tracking via `pytest-cov`.

---

## 3. Consequences

### Positive
- **De Facto Power Systems Standard:** OpenDSS is the global industry and academic reference standard for distribution feeder analysis, ensuring validity and credibility in IEEE peer review.
- **In-Memory Speed:** `OpenDSSDirect.py` interfaces with the OpenDSS dynamic library directly through memory pointers, avoiding file I/O overhead during high-frequency time-series iterations.
- **Bitwise Seed Determinism:** PyTorch and scikit-learn allow programmatic seed locking across Python, NumPy, and C++ backends, satisfying the strict reproducibility protocol (`docs/methodology/REPRODUCIBILITY.md`).
- **Zero Proprietary Cost:** Entire stack is open-source (BSD/MIT/Apache), requiring no commercial licenses (such as MATLAB/Simulink).

### Negative & Constraints
- OpenDSSDirect on Linux/macOS requires precompiled shared libraries (`libopendssdirect`), though Windows wheels are self-contained. CI workflows must ensure compatible cross-platform runner configurations.
- OpenDSS COM interface is Windows-only; we strictly prohibit COM calls and mandate `OpenDSSDirect.py` for cross-platform compatibility.

---

## 4. Alternatives Considered

- **Alternative A: pandapower.**
  *Evaluated:* Pure-Python power flow engine based on PYPOWER.
  *Rejected:* Significantly slower for quasi-static time-series loops involving hundreds of thousands of simulation steps compared to compiled OpenDSS C/C++ engine.
- **Alternative B: GridLAB-D.**
  *Evaluated:* Agent-based distribution simulation tool from PNNL.
  *Rejected:* More complex deployment, heavier configuration syntax, and less lightweight Python integration for rapid ML loop prototyping.
- **Alternative C: TensorFlow / Keras.**
  *Evaluated:* Mature ML framework.
  *Rejected:* PyTorch offers cleaner native handling of sequence tensors, custom autoencoder loss implementations, and transparent PyTorch lightning / pure PyTorch execution pipelines.
- **Alternative D: MATLAB / Simulink / Simscape Electrical.**
  *Evaluated:* Widely used in power engineering.
  *Rejected:* Proprietary licensing precludes open-source public reproducibility on GitHub and cloud CI runners.

---

## 5. Compliance & Review

- No Python module may import `win32com.client` or use COM bindings for OpenDSS.
- All OpenDSS power flow interactions must be encapsulated within `src/digital_twin/`.
- Direct imports of ML frameworks outside their designated modules (`src/forecasting/`, `src/anomaly_detection/`) are prohibited.
