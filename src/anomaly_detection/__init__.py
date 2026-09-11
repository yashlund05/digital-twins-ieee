"""
anomaly_detection — Anomaly Detection Models

Implements unsupervised anomaly detection models:
- Isolation Forest
- LSTM Autoencoder

All detectors are applied to both raw and residual inputs as part of
the 2x2 experimental design (Experiment E4).

All models are trained WITHOUT anomaly labels (unsupervised).
Labels are used ONLY for evaluation.
"""
