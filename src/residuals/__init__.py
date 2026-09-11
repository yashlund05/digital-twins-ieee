"""
residuals — Residual Engine

Computes physical-vs-virtual residuals: physical_measurement - dt_prediction.

Residuals serve as the alternative input representation for anomaly detectors
in the 2x2 design (Experiment E4) and are central to the raw-vs-residual
comparison under varying synchronization staleness (Experiment E5).
"""
