# ADR-0001: Research Positioning as Controlled Staleness Investigation

> **Status:** Accepted
> **Date:** 2026-09-11
> **Deciders:** Research Lead (@RESEARCH_LEAD), Entire Team
> **Consulted:** Integration Lead (@INTEGRATION_LEAD), Sync Owner (@SYNC_OWNER), ML Owner (@ML_OWNER), Anomaly Owner (@ANOMALY_OWNER), Eval Owner (@EVAL_OWNER), Data Owner (@DATA_OWNER)
> **Informed:** All Contributors

---

## 1. Context

Digital Twin (DT) technology is rapidly expanding in smart grid research. However, a comprehensive review of the literature (documented in `docs/research/literature-review.md`) reveals three foundational vulnerabilities in current scholarship:

1. **Unrealistic Telemetry Assumptions:** Most distribution-level DT studies assume instantaneous, zero-latency, continuous synchronization between the physical network and the virtual twin. In realistic distribution grids, bandwidth limitations, cellular/mesh packet delay, protocol aggregation cycles, and intermittent communication dropouts introduce non-trivial synchronization staleness.
2. **Conflation of Concepts:** The literature routinely conflates "digital shadow" (unidirectional data flow) with "digital twin" (bidirectional coupling). Furthermore, studies frequently evaluate either load forecasting or anomaly detection in isolation, ignoring the reality that DT state feeds both operational estimation and security/fault monitoring simultaneously.
3. **Overclaimed Novelty in Standard ML Architectures:** Many papers claim architectural novelty by applying standard deep learning models (e.g., vanilla LSTMs, basic autoencoders) to power system data, while neglecting rigorous characterization of physical-virtual desynchronization.

We require an explicit architectural and scientific decision on how to position our research, how to design the experimental independent variables, and how to frame our contribution for submission to a top-tier IEEE Transactions journal (e.g., IEEE Transactions on Smart Grid).

---

## 2. Decision

We make the following binding research positioning decisions:

1. **Primary Contribution Definition:** Our primary scientific contribution is the **rigorous quantification of the effect of Digital Twin synchronization staleness on joint short-term load estimation and unsupervised anomaly detection**. We do not claim to invent novel foundational neural network architectures.
2. **Controlled Independent Variable:** Synchronization staleness is established as a first-class experimental variable, controlled explicitly across five discrete update intervals:
   $$\Delta t \in \{1\,\text{s}, 5\,\text{s}, 15\,\text{s}, 60\,\text{s}, 300\,\text{s}\}$$
   plus missed-update stress scenarios (5%, 10%, 20% dropped updates).
3. **Standardized, Interpretable Models:** We employ standardized, reproducible baseline and reference models:
   - *Load Estimation:* Persistence baseline, XGBoost, and standard LSTM.
   - *Anomaly Detection:* Isolation Forest and LSTM Autoencoder.
4. **Raw vs. Residual 2x2 Factorial Design:** We evaluate whether feeding models physics-based Digital Twin state residuals ($r(t) = y(t) - \hat{y}_{DT}(t)$) provides greater robustness against synchronization staleness than feeding raw telemetry measurements.
5. **Hybrid Simulation Scope:** The benchmark is evaluated on the IEEE 33-bus radial distribution network parameterized with real residential consumption patterns from Pecan Street Dataport. This dataset is transparently designated and documented as a **hybrid simulation dataset**, never misrepresented as field measurements of the physical IEEE feeder.

---

## 3. Consequences

### Positive
- **Clear Scientific Novelty:** Provides a defensible, novel empirical characterization of a known gap in distribution-level DT research.
- **Reproducibility & Rigor:** By using standardized models and benchmark feeders, results can be replicated and compared directly without black-box proprietary barriers.
- **Dual-Task Insight:** Evaluates the trade-offs between estimation accuracy and anomaly detection sensitivity under identical synchronization conditions.

### Negative & Constraints
- **Simulation Qualification:** All claims must explicitly acknowledge the synthetic coupling between Pecan Street consumer profiles and the IEEE 33-bus topology.
- **Strict Protocol Discipline:** No post-hoc tuning of model hyperparameters or manipulation of random seeds after observing staleness curves is permitted.

---

## 4. Alternatives Considered

- **Alternative A: Proposing a Novel Deep Learning Architecture (e.g., Graph Attention Spatio-Temporal Network).**
  *Rejected.* ML architecture changes would confound the staleness analysis. It is impossible to isolate whether performance degradation stems from staleness or network hyperparameters.
- **Alternative B: Closed-Loop Active Control DT.**
  *Rejected.* Introducing autonomous closed-loop voltage regulation or switching adds feedback instability that obscures the direct relationship between data staleness and downstream ML performance. Open-loop monitoring and estimation is the prerequisite foundational study.
- **Alternative C: Purely Synthetic Load Profiles (e.g., Random Walk / Sinusoidal Curves).**
  *Rejected.* Purely synthetic loads lack real-world residential behavioral dynamics (solar PV intermittency, coincident peak cooking/HVAC loads, electric vehicle charging spikes).

---

## 5. Compliance & Review

- All experiment designs (E1–E7) must conform to this positioning.
- All manuscripts and reports must adhere to the standardized labeling: `[ESTABLISHED]`, `[HYPOTHESIS]`, `[ASSUMPTION]`, `[OBSERVATION]`, `[CONCLUSION]`.
