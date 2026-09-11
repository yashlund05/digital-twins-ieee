# Paper Alignment Guide

> **Paper Title:** Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin
> **Target Venues:** IEEE Transactions on Smart Grid / IEEE Transactions on Industrial Informatics
> **Version:** 1.0.0 — September 2026

---

## 1. Research Questions and Paper Mapping

The structure of this repository and the experiment pipeline (E1–E7) directly mirror the manuscript's narrative and empirical structure.

| Research Question (RQ) | Core Hypothesis / Question | Primary Experiment | Paper Section | Generated Figures & Tables |
|------------------------|----------------------------|--------------------|---------------|----------------------------|
| **RQ1** | How does synchronization staleness ($\Delta t \in \{1, 5, 15, 60, 300\}$ s) degrade load estimation accuracy across Persistence, XGBoost, and LSTM? | **E2** | Section IV-B | **Fig. 4**, **Table II** |
| **RQ2** | How does staleness affect unsupervised anomaly detection performance under raw measurements vs. DT state residuals? | **E3, E4** | Section IV-C | **Fig. 5**, **Table III** |
| **RQ3** | Is there an empirical critical staleness threshold beyond which downstream ML tasks degrade non-linearly? | **E5** | Section IV-D | **Fig. 6**, **Table IV** |
| **RQ4** | Does physics-based DT state residual input provide superior staleness resilience compared to raw telemetry? | **E3 vs. E4** | Section IV-E | **Fig. 7**, **Table V** |

---

## 2. Manuscript Section-to-Code Mapping

```
Manuscript Structure                     Repository Implementation
----------------------------------       ---------------------------------------
Section I: Introduction                  docs/research/literature-review.md
- Motivation & Literature Gaps           docs/decisions/ADR-0001-research-positioning.md
- Clear Scope & RQ Formulations

Section II: System Model & DT Sync       src/digital_twin/ (OpenDSS IEEE 33-bus)
- IEEE 33-Bus Feeder Model               src/synchronization/ (Engine & AoI)
- Telemetry & Latency Formulation        configs/synchronization.yaml
- Staleness Definition S(t)              docs/architecture/SYNCHRONIZATION_ENGINE.md

Section III: Joint ML Framework          src/forecasting/ (Persistence, XGBoost, LSTM)
- Short-Term Load Estimation             src/anomaly_detection/ (IF, LSTM-AE)
- Unsupervised Anomaly Detection         src/residuals/ (State residual engine)
- Raw vs. Residual Formulation           configs/forecasting.yaml, anomaly_detection.yaml

Section IV: Experimental Evaluation      experiments/runs/
- Setup & Hybrid Dataset Protocol        src/data/ (Pecan Street mapping)
- E1: Sanity Check & Verification        docs/experiments/EXPERIMENTS.md
- E2: Load Estimation vs. Staleness      src/experiments/run_experiment_2.py
- E3/E4: Anomaly Detection Factorial     src/experiments/run_experiment_3_4.py
- E5: Critical Threshold Search          src/experiments/run_experiment_5.py
- E6: Missed Updates Stress Test         src/experiments/run_experiment_6.py
- E7: Joint Multi-Objective Trade-off    src/experiments/run_experiment_7.py
- Statistical Significance Analysis      src/statistics/ (Wilcoxon, Friedman tests)

Section V: Discussion & Limitations      docs/methodology/DATA_PROTOCOL.md
- Hybrid Simulation Disclosure           docs/methodology/REPRODUCIBILITY.md
- Practical Grid Guidelines              artifacts/reports/
```

---

## 3. Mandatory IEEE Scientific Claim Guidelines

1. **Dataset Nature [ESTABLISHED / DISCLOSURE]:**
   - *Claim:* "Evaluated on a hybrid simulation benchmark coupling real residential smart meter load shapes from Pecan Street with the IEEE 33-bus radial distribution feeder in OpenDSS."
   - *Prohibited:* Never imply that the data represents real-world physical sensor streams collected directly from an operating utility IEEE 33-bus substation.
2. **Model Novelty [ESTABLISHED]:**
   - *Claim:* Standard, robust architectures (XGBoost, LSTM, Isolation Forest, LSTM-AE) are employed to isolate synchronization staleness as the primary experimental variable.
   - *Prohibited:* Do not claim novelty in the neural network or tree ensemble architectures themselves.
3. **Synchronization Variable [ESTABLISHED]:**
   - *Claim:* Staleness is systematically controlled across discrete step-holds and stochastic communication dropouts.
4. **Experimental Findings [OBSERVATION / CONCLUSION]:**
   - Every numerical claim in the text must match bit-for-bit the JSON output in `experiments/runs/<run_id>/results.json` and generated tables in `artifacts/tables/`.
   - Results contradicting initial hypotheses must be reported transparently.
