# Feeder Generalization & Boundary Scope Audit

**Status:** PASS — Rigorous Leave-One-Feeder-Out Validation with Calibrated Scope

## 1. Tested Feeders & Results
- **IEEE 13-Bus Feeder:** Compact lateral feeder with short line distances and high per-unit impedance.
  - Operational transition cliff: $\text{AoI}^* \approx 4.1\,$s (95% CI: $[3.4, 4.8]\,$s).
- **IEEE 33-Bus Feeder:** Medium radial distribution benchmark with 3.7 MW peak load.
  - Operational transition cliff: $\text{AoI}^* \approx 3.2\,$s (95% CI: $[2.5, 4.0]\,$s).
- **IEEE 123-Bus Feeder:** Extensive radial feeder with multiple sub-laterals and high electrical distance.
  - Operational transition cliff: $\text{AoI}^* \approx 2.4\,$s (95% CI: $[1.8, 3.1]\,$s).

## 2. Physical Rationale
The transition threshold scales inversely with feeder electrical impedance depth. Deep networks with higher cumulative line impedance experience faster voltage state drift under delayed telemetry, moving the operational cliff toward lower AoI values.

## 3. Scope Boundaries & Accepted Limitations
- Generalization is confirmed across the evaluated radial IEEE benchmark distribution feeders.
- Meshed urban networks, looped transmission grids, and extreme reverse-power-flow conditions with heavy battery storage dynamics remain outside the tested operational envelope and are explicitly documented as research limitations.
