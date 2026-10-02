# Experiment E4: Raw vs. Residual Inputs — Summary

- **Run ID:** `E4_RAW_VS_RESIDUAL_SEED42_20260930`
- **Date:** 2026-09-30T15:42:33.106618
- **Random Seed:** 42
- **Synchronization Interval:** 0 s (Baseline Level 0 — Perfect Synchronization)
- **Residual Normalization:** z_score
- **Threshold Strategy:** percentile (95.0th percentile)
- **Training Protocol:** Unsupervised (zero anomaly labels seen during fit)

## 2x2 Factorial Baseline Results

| condition | detector | representation | threshold | precision | recall | f1 | pr_auc | roc_auc | fpr | latency_steps | test_samples | true_anomalies | pred_anomalies |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E4-1 | isolation_forest | raw | 0.5032 | 0.1165 | 0.1189 | 0.1176 | 0.0939 | 0.7139 | 0.0439 | 3.2459 | 5256 | 244 | 249 |
| E4-2 | isolation_forest | residual | 0.2938 | 0.0464 | 1.0000 | 0.0887 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 5256 | 244 | 5256 |
| E4-3 | lstm_autoencoder | raw | 0.0007 | 0.4983 | 0.5861 | 0.5386 | 0.5610 | 0.9493 | 0.0287 | 1.3443 | 5256 | 244 | 287 |
| E4-4 | lstm_autoencoder | residual | 0.0004 | 0.9569 | 1.0000 | 0.9780 | 1.0000 | 1.0000 | 0.0022 | 0.0000 | 5256 | 244 | 255 |

## Scientific Notes
- All four conditions evaluated on identical test split partitions (Nov 7 - Dec 31, 2018).
- Normalization parameters fitted strictly on training partition with zero future leakage.
- Decision thresholds calibrated strictly on validation scores (never test split).
- Raw residuals preserved in `raw_residuals.parquet` without hidden smoothing or filtering.
