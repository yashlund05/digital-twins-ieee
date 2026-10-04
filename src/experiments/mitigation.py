"""src/experiments/mitigation.py — Evaluation of Staleness Mitigation Strategies.

Implements benchmark experiments comparing:
1. Uncompensated Residual Baseline
2. Uncompensated Raw Baseline
3. Feature 1: AoI-Adaptive Dynamic Thresholding
4. Feature 2: Dual-Mode Inversion Compensator (Automated Representation Switching)

Demonstrates quantitative performance recovery across the full (Delta t, P_drop) grid.
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.anomaly_detection.dual_mode import DualModeInversionCompensator
from src.anomaly_detection.thresholds import AoIAdaptiveThreshold
from src.evaluation.anomaly_metrics import compute_anomaly_metrics
from src.utils.io import ensure_dir, save_json
from src.utils.logging import get_logger

logger = get_logger("experiments.mitigation")


def run_mitigation_benchmark(
    output_dir: Path | str,
    e5_seed42_dir: Path | str = "experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930",
    aoi_inversion_threshold: float = 5.0,
    gamma_adaptive: float = 0.08,
) -> dict[str, Any]:
    """Execute end-to-end benchmark of mitigation strategies across all staleness conditions.

    Args:
        output_dir: Directory where mitigation artifacts and metrics will be saved.
        e5_seed42_dir: Path to directory containing E5 predictions.parquet and comparison.csv.
        aoi_inversion_threshold: Critical AoI threshold for representation switching (seconds).
        gamma_adaptive: Scaling parameter for AoI-adaptive thresholding.

    Returns:
        Dictionary containing comparative DataFrame, summary metrics, and output paths.
    """
    out_path = Path(output_dir)
    ensure_dir(out_path)

    e5_path = Path(e5_seed42_dir)
    preds_file = e5_path / "predictions.parquet"
    if not preds_file.is_file():
        raise FileNotFoundError(f"Missing predictions.parquet at {preds_file}")

    logger.info(f"Loading predictions from {preds_file} for mitigation benchmark...")
    preds_df = pd.read_parquet(preds_file)

    # Required columns check
    score_res_col = "score_lstm_res" if "score_lstm_res" in preds_df.columns else "pred_lstm_res"
    score_raw_col = "score_lstm_raw" if "score_lstm_raw" in preds_df.columns else "pred_lstm_raw"
    aoi_col = "aoi_seconds" if "aoi_seconds" in preds_df.columns else "realized_aoi"
    y_true_col = (
        "true_anomaly_label" if "true_anomaly_label" in preds_df.columns else "anomaly_label"
    )

    # Ensure staleness_seconds and packet_drop_rate exist
    if "staleness_seconds" not in preds_df.columns or "packet_drop_rate" not in preds_df.columns:
        comp_file = e5_path / "comparison.csv"
        if comp_file.is_file():
            comp_df = pd.read_csv(comp_file)
            cond_map = (
                comp_df[["condition_id", "staleness_seconds", "packet_drop_rate"]]
                .drop_duplicates()
                .set_index("condition_id")
            )
            preds_df["staleness_seconds"] = preds_df["condition_id"].map(
                cond_map["staleness_seconds"]
            )
            preds_df["packet_drop_rate"] = preds_df["condition_id"].map(
                cond_map["packet_drop_rate"]
            )
        else:
            import re

            def parse_dt_pdrop(cid: str) -> tuple[int, float]:
                m_dt = re.search(r"DT(\d+)", cid)
                m_pd = re.search(r"PD(\d+)", cid)
                dt_val = int(m_dt.group(1)) if m_dt else 0
                pd_val = float(m_pd.group(1)) / 100.0 if m_pd else 0.0
                return dt_val, pd_val

            parsed = [parse_dt_pdrop(cid) for cid in preds_df["condition_id"]]
            preds_df["staleness_seconds"] = [p[0] for p in parsed]
            preds_df["packet_drop_rate"] = [p[1] for p in parsed]

    # Instantiate mitigation components
    dual_mode_comp = DualModeInversionCompensator(
        aoi_inversion_threshold=aoi_inversion_threshold,
        smooth_blending=False,
    )
    aoi_adaptive_selector = AoIAdaptiveThreshold(
        base_percentile=95.0,
        gamma=gamma_adaptive,
        scaling_function="sqrt",
    )

    # Calibrate baseline thresholds on fresh state data (dt=0, pd=0.0)
    fresh_df = preds_df[
        (preds_df["staleness_seconds"] == 0) & (preds_df["packet_drop_rate"] == 0.0)
    ]
    if fresh_df.empty:
        fresh_df = preds_df[preds_df[aoi_col] <= 1.0]
    if fresh_df.empty:
        fresh_df = preds_df

    th_res_base = float(np.percentile(fresh_df[score_res_col].values, 95.0))
    th_raw_base = float(np.percentile(fresh_df[score_raw_col].values, 95.0))
    aoi_adaptive_selector.fit(fresh_df[score_res_col].values, fresh_df[aoi_col].values)

    records = []
    conditions = preds_df["condition_id"].unique()

    for cond_id in conditions:
        cdf = preds_df[preds_df["condition_id"] == cond_id].copy()
        if cdf.empty:
            continue

        dt = float(cdf["staleness_seconds"].iloc[0]) if "staleness_seconds" in cdf.columns else 0.0
        pdrop = float(cdf["packet_drop_rate"].iloc[0]) if "packet_drop_rate" in cdf.columns else 0.0

        y_true = cdf[y_true_col].values.astype(int)
        sc_res = cdf[score_res_col].values.astype(float)
        sc_raw = cdf[score_raw_col].values.astype(float)
        aoi_vals = cdf[aoi_col].values.astype(float)

        # 1. Uncompensated Residual (Static Baseline Threshold)
        y_pred_res = (sc_res >= th_res_base).astype(int)
        m_res = compute_anomaly_metrics(y_true, y_pred_res, sc_res)

        # 2. Uncompensated Raw (Static Baseline Threshold)
        y_pred_raw = (sc_raw >= th_raw_base).astype(int)
        m_raw = compute_anomaly_metrics(y_true, y_pred_raw, sc_raw)

        # 3. Feature 1: AoI-Adaptive Dynamic Thresholding
        y_pred_adapt = aoi_adaptive_selector.apply_adaptive(sc_res, aoi_vals)
        m_adapt = compute_anomaly_metrics(y_true, y_pred_adapt, sc_res)

        # 4. Feature 2: Dual-Mode Inversion Compensator
        eval_dm = dual_mode_comp.evaluate_mitigation(
            y_true=y_true,
            scores_residual=sc_res,
            scores_raw=sc_raw,
            aoi_seconds=aoi_vals,
            threshold_residual=th_res_base,
            threshold_raw=th_raw_base,
        )
        m_dm = eval_dm["dual_mode_hybrid"]

        records.append(
            {
                "condition_id": cond_id,
                "staleness_seconds": dt,
                "packet_drop_rate": pdrop,
                "mean_aoi_seconds": float(np.mean(aoi_vals)),
                "f1_residual_uncompensated": m_res["f1"],
                "precision_residual": m_res["precision"],
                "recall_residual": m_res["recall"],
                "f1_raw_uncompensated": m_raw["f1"],
                "f1_aoi_adaptive_threshold": m_adapt["f1"],
                "precision_aoi_adaptive": m_adapt["precision"],
                "recall_aoi_adaptive": m_adapt["recall"],
                "f1_dual_mode_compensator": m_dm["f1"],
                "precision_dual_mode": m_dm["precision"],
                "recall_dual_mode": m_dm["recall"],
                "delta_f1_dual_mode_vs_residual": m_dm["f1"] - m_res["f1"],
                "percent_switched_to_raw": eval_dm["percent_switched_to_raw"],
            }
        )

    res_df = pd.DataFrame(records)
    csv_path = out_path / "mitigation_benchmark_results.csv"
    res_df.to_csv(csv_path, index=False)

    # Compute key benchmark summary metrics
    # Severe condition (dt=300, pd=0.20)
    severe_rows = res_df[
        (res_df["staleness_seconds"] == 300) & (res_df["packet_drop_rate"] == 0.20)
    ]
    if severe_rows.empty:
        severe_rows = res_df.tail(1)

    f1_res_severe = float(severe_rows["f1_residual_uncompensated"].iloc[0])
    f1_raw_severe = float(severe_rows["f1_raw_uncompensated"].iloc[0])
    f1_adapt_severe = float(severe_rows["f1_aoi_adaptive_threshold"].iloc[0])
    f1_dm_severe = float(severe_rows["f1_dual_mode_compensator"].iloc[0])

    summary = {
        "benchmark_conditions_count": len(res_df),
        "nominal_fresh_f1": float(
            res_df[res_df["staleness_seconds"] == 0]["f1_residual_uncompensated"].iloc[0]
        ),
        "severe_staleness_comparison": {
            "condition": "DT300_PD20",
            "uncompensated_residual_f1": f1_res_severe,
            "uncompensated_raw_f1": f1_raw_severe,
            "aoi_adaptive_threshold_f1": f1_adapt_severe,
            "dual_mode_compensator_f1": f1_dm_severe,
            "recovery_gain_dual_mode": f1_dm_severe - f1_res_severe,
        },
        "mean_f1_across_all_conditions": {
            "uncompensated_residual": float(res_df["f1_residual_uncompensated"].mean()),
            "uncompensated_raw": float(res_df["f1_raw_uncompensated"].mean()),
            "aoi_adaptive_threshold": float(res_df["f1_aoi_adaptive_threshold"].mean()),
            "dual_mode_compensator": float(res_df["f1_dual_mode_compensator"].mean()),
        },
    }

    save_json(summary, out_path / "mitigation_summary.json")

    logger.info(
        f"Mitigation benchmark complete across {len(res_df)} conditions. "
        f"Under severe staleness: Residual F1={f1_res_severe:.4f} -> Dual-Mode F1={f1_dm_severe:.4f} "
        f"(Gain: {f1_dm_severe - f1_res_severe:+.4f})"
    )

    return {
        "results_df": res_df,
        "summary": summary,
        "csv_path": csv_path,
    }
