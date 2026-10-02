# Experiment E6: Joint Analysis and Hypothesis Testing — Summary Report

- **Run ID:** `E6_JOINT_ANALYSIS_SEED42_20261002`
- **Timestamp:** `2026-10-02T11:26:06.419192`
- **Seed:** `42`
- **H3 Test Outcome:** **NOT_SUPPORTED**

## 1. Key Regression Slopes (Normalized Degradation vs. $\log(1+\Delta t)$)

| task              | model            | representation   | metric              |   slope_log_dt |   r2_log_dt |   p_val_log_dt |
|:------------------|:-----------------|:-----------------|:--------------------|---------------:|------------:|---------------:|
| load_estimation   | persistence      | raw              | mae                 |      0.923256  |    0.90269  |    1.30561e-12 |
| load_estimation   | persistence      | raw              | rmse                |      0.848768  |    0.897109 |    2.41819e-12 |
| load_estimation   | persistence      | raw              | mape                |      0.962387  |    0.89934  |    1.89781e-12 |
| load_estimation   | persistence      | raw              | r2                  |     -0.413561  |    0.895927 |    2.74352e-12 |
| load_estimation   | xgboost          | raw              | mae                 |      1.24348   |    0.899994 |    1.76587e-12 |
| load_estimation   | xgboost          | raw              | rmse                |      1.04102   |    0.892318 |    3.9988e-12  |
| load_estimation   | xgboost          | raw              | mape                |      1.25746   |    0.898696 |    2.03649e-12 |
| load_estimation   | xgboost          | raw              | r2                  |     -0.236492  |    0.896268 |    2.64574e-12 |
| load_estimation   | lstm             | raw              | mae                 |      1.20101   |    0.876206 |    1.86924e-11 |
| load_estimation   | lstm             | raw              | rmse                |      0.951134  |    0.864975 |    4.88732e-11 |
| load_estimation   | lstm             | raw              | mape                |      1.21517   |    0.89408  |    3.33242e-12 |
| load_estimation   | lstm             | raw              | r2                  |     -0.21204   |    0.871828 |    2.74587e-11 |
| anomaly_detection | isolation_forest | raw              | precision           |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | raw              | recall              |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | raw              | f1                  |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | raw              | false_positive_rate |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | raw              | pr_auc              |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | raw              | roc_auc             |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | raw              | detection_latency   |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | raw              | threshold           |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | residual         | precision           |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | residual         | recall              |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | residual         | f1                  |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | residual         | false_positive_rate |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | residual         | pr_auc              |      0.0680103 |    0.256248 |    0.0116041   |
| anomaly_detection | isolation_forest | residual         | roc_auc             |      0.0819198 |    0.69186  |    4.72354e-07 |
| anomaly_detection | isolation_forest | residual         | detection_latency   |      0         |  nan        |  nan           |
| anomaly_detection | isolation_forest | residual         | threshold           |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | precision           |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | recall              |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | f1                  |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | false_positive_rate |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | pr_auc              |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | roc_auc             |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | detection_latency   |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | raw              | threshold           |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | residual         | precision           |      0.0868195 |    0.376772 |    0.00142116  |
| anomaly_detection | lstm_autoencoder | residual         | recall              |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | residual         | f1                  |      0.100393  |    0.474594 |    0.000197161 |
| anomaly_detection | lstm_autoencoder | residual         | false_positive_rate |     79.8623    |    0.725462 |    1.29865e-07 |
| anomaly_detection | lstm_autoencoder | residual         | pr_auc              |      0.0871101 |    0.421189 |    0.000601503 |
| anomaly_detection | lstm_autoencoder | residual         | roc_auc             |      0.0741771 |    0.77302  |    1.55735e-08 |
| anomaly_detection | lstm_autoencoder | residual         | detection_latency   |      0         |  nan        |  nan           |
| anomaly_detection | lstm_autoencoder | residual         | threshold           |      0         |  nan        |  nan           |

## 2. Publication Figures Generated

- `figures/fig_01_anomaly_f1_vs_staleness.png`
- `figures/fig_02_anomaly_prauc_vs_staleness.png`
- `figures/fig_03_load_mae_vs_staleness.png`
- `figures/fig_04_load_rmse_vs_staleness.png`
- `figures/fig_05_task_degradation_comparison.png`
- `figures/fig_06_realized_aoi.png`
- `figures/fig_07_staleness_packet_drop_interaction.png`
- `figures/fig_08_h3_effect_comparison.png`