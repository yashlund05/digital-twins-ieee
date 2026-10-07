# Phase 22 — Phase 16 Validation Audit

**Status:** PASS  
**Audit Timestamp:** 2026-10-07T10:40:00Z  
**Target:** `experiments/runs/E16_JOURNAL_ENHANCEMENT_20261006/`  

## 1. Threshold Portability
Dynamic threshold model: $\tau(\mathrm{AoI}) = \tau_0(\mathrm{seed}) + \gamma \sqrt{\mathrm{AoI}}$.
- Uncorrected baseline across non-42 seeds exhibits near 100% false positive saturation.
- With out-of-sample fitted portability correction ($\gamma$), baseline FPR drops to $\approx 4.38$--$4.43\%$ across independent seeds.
- Overall mean evaluation FPR stabilizes at $0.241$.

## 2. High-Resolution AoI Sweep & Maximum Loss Derivative
- High-resolution evaluation over $[1, 5]$\,s demonstrates maximum loss derivative centered at $3.2$\,s on IEEE 33-bus.
- Operational transition interval identified at $[2.5, 4.0]$\,s.

## 3. Alternative Detectors & Telemetry Noise Robustness
- **One-Class SVM:** Fresh $F_1 = 0.6703$ (Precision = $1.0$, Recall = $0.5041$, FPR = $0$), degrading to $0.0455$ under severe staleness.
- **GRU Forecaster:** Fresh MAPE $= 9.00\%$ vs. LSTM $8.97\%$; stale GRU MAPE $= 15.59\%$ vs. LSTM $15.56\%$.
- **Noise Robustness:** 40 dB SNR ($\approx 1\%$ noise) causes $0.35\%$ increase in baseline MAPE; 30 dB SNR ($\approx 3.2\%$ noise) maintains stable relative rankings.
