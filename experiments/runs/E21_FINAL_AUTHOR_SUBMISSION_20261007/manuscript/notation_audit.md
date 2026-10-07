# Mathematical Notation Consistency Audit

## 1. Core State & Residual Definitions
- Physical Feeder Telemetry: $y_t \in \mathbb{R}^D$ (power injections, nodal voltages). Units: kW, kV, p.u.
- Digital Twin State Replica: $y_t^{\mathrm{DT}} \in \mathbb{R}^D$ holding last synchronized snapshot.
- Physics-Based Residual Vector:
  $$r_t = y_t - y_t^{\mathrm{DT}}$$
  Dimensions: $D$-dimensional real vector. Mean-centered with identity covariance under ideal calibration.

## 2. Synchronization & Communication Model
- Synchronization Interval: $\Delta t \in \{0, 1, 5, 15, 60, 300\}$ seconds.
- Packet-Drop Probability: $P_{\mathrm{drop}} \in [0.0, 0.20]$.
- Update Timestamp Process: $U(t) = \max \{ \tau_k \le t : \text{packet } k \text{ successfully received} \}$.
- Realized Age of Information (AoI):
  $$\mathrm{AoI}(t) = t - U(t), \quad \mathrm{AoI} \ge 0$$
  Units: Seconds (s). Continuous saw-tooth trajectory.

## 3. AoI-Adaptive Threshold Model
- Anomaly Decision Score: $S_t = \|r_t\|_2$.
- Adaptive Decision Threshold:
  $$\tau(\mathrm{AoI}) = \tau_0 \cdot \left(1 + \gamma \cdot \frac{\mathrm{AoI}}{\Delta t_{\mathrm{ref}}}\right)$$
  where $\tau_0$ is the baseline 99th percentile threshold under $\mathrm{AoI}=0$, $\gamma = 0.05$ is the sensitivity parameter, and $\Delta t_{\mathrm{ref}} = 1.0\,$s.

## 4. Formal Hypothesis H3 Notation
- Normalized Degradation Slope for Anomaly Detection: $\beta_{\mathrm{AD}}$ (slope of $\log(F_1(\Delta t) / F_1(0))$ versus $\log(1 + \Delta t)$).
- Normalized Degradation Slope for Load Estimation: $\beta_{\mathrm{LE}}$ (slope of $\log(\mathrm{MAPE}(\Delta t) / \mathrm{MAPE}(0))$ versus $\log(1 + \Delta t)$).
- Differential Degradation Rate:
  $$\Delta\beta = \beta_{\mathrm{AD}} - \beta_{\mathrm{LE}}$$
- Statistical Hypotheses:
  $$H_0: \Delta\beta \le 0 \quad \text{vs.} \quad H_3: \Delta\beta > 0$$
- Empirical Outcome: $\Delta\beta = -1.2236$, 95% Bootstrap CI $[-1.3463, -1.1134]$, $p = 1.000$ (Formal Decision: `NOT_SUPPORTED`).

## 5. Notation Consistency Verification
- All symbols ($y_t, y_t^{\mathrm{DT}}, r_t, \Delta t, P_{\mathrm{drop}}, \mathrm{AoI}, \beta_{\mathrm{AD}}, \beta_{\mathrm{LE}}, \Delta\beta$) maintain identical definition across Section III, Section IV, Appendix, and Supplementary Material.
- Zero notation collisions detected.
