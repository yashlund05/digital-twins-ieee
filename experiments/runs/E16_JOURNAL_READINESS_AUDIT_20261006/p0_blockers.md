# Phase 16 — P0 Submission Blockers (Immediate Desk-Reject Hazards)

1. P0-01: Bibliographic Integrity
   - File: experiments/runs/E13_MANUSCRIPT_SUBMISSION_20261002/manuscript/references.bib
   - Issue: 6 out of 10 references contain [VERIFY] placeholder tags.
   - Severity: FATAL (immediate return without review / desk-reject).
   - Remedy: Populate complete, verified citations for DT survey, AD survey, AoI theory, LSTM-AE, and LSTM forecaster.

2. P0-02: Multi-Seed Anomaly Detection Threshold Portability Defect
   - Files: E5 multi-seed sweeps (seeds 123, 456, 789, 101112)
   - Issue: Static 95th percentile threshold from seed 42 produces 100% false alarms (FPR=1.0, F1=0.0887) on other seeds.
   - Severity: HIGH SCIENTIFIC VULNERABILITY (undermines multi-seed generalizability of anomaly detection).
   - Remedy: Implement AoI-adaptive thresholding or per-seed validation calibration.
