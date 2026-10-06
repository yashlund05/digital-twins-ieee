# Reviewer 2: Machine Learning & Cyber-Physical Systems Specialist

Review Recommendation: MAJOR REVISION
Score: 62/100

Strengths:
1. Strict zero temporal leakage protocol; train-only normalizer fitting.
2. Novel empirical discovery of the residual representation inversion boundary at dt >= 5s.
3. Honest reporting of H3 falsification.

Major Concerns:
1. Fatal threshold portability failure on seeds 123, 456, 789, 101112 (FPR = 1.0).
2. Degenerate Residual Isolation Forest baseline (FPR = 1.0 even on seed 42).
3. Scale asymmetry in H3 (bounded F1 vs unbounded MAPE).
4. Missing modern/classical baselines (One-Class SVM, GRU).

Required Experiments:
1. EXP-ML-1: Implement AoI-adaptive thresholding or per-seed validation calibration.
2. EXP-ML-2: Add One-Class SVM and GRU baselines.
3. EXP-ML-3: Provide bounded scale-invariant degradation comparison for H3.
