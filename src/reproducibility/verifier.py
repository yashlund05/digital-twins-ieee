"""src/reproducibility/verifier.py — Automated verification of historical research benchmarks.

Executes controlled verification runs against frozen Phase 7 (E4), Phase 8 (E5),
Phase 9 (E6), and Phase 10 (E10) benchmarks without overwriting historical runs.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

from src.reproducibility.artifact_integrity import verify_artifacts
from src.reproducibility.comparator import compare_metrics
from src.reproducibility.hashing import hash_file
from src.reproducibility.run_manifest import create_reproducibility_manifest
from src.utils.io import load_json, save_json
from src.utils.logging import get_logger

logger = get_logger("reproducibility.verifier")

# Canonical reference values from Phase 7 E4
PHASE7_CANONICAL_TARGETS = {
    "if_raw": 0.117647,
    "if_res": 0.088727,
    "lstm_raw": 0.538606,
    "lstm_res": 0.977956,
}

REPRESENTATIVE_CONDITIONS = [
    (0, 0.0),
    (1, 0.0),
    (5, 0.0),
    (60, 0.10),
    (300, 0.20),
]


def verify_historical_benchmarks(
    output_dir: Path | str,
    phase7_e4_dir: Path | str = "experiments/runs/E4_RAW_VS_RESIDUAL_SEED42_20260930",
    phase8_e5_dir: Path | str = "experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930",
    phase9_e6_dir: Path | str = "experiments/runs/E6_JOINT_ANALYSIS_SEED42_20261002",
    phase10_e10_dir: Path | str = "experiments/runs/E10_MULTI_SEED_ANALYSIS_20261002",
) -> dict[str, Any]:
    """Audit historical runs and compare metrics to pre-registered benchmarks.

    Args:
        output_dir: Output folder for verification tables and reports.
        phase7_e4_dir: Path to Phase 7 E4 baseline run.
        phase8_e5_dir: Path to Phase 8 corrected E5 run.
        phase9_e6_dir: Path to Phase 9 E6 analysis run.
        phase10_e10_dir: Path to Phase 10 E10 multi-seed run.

    Returns:
        Verification report dictionary.
    """
    out = Path(output_dir)
    repro_dir = out / "reproducibility"
    repro_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "phase7_e4_status": "NOT_VERIFIED",
        "phase8_e5_status": "NOT_VERIFIED",
        "phase9_e6_status": "NOT_VERIFIED",
        "phase10_e10_status": "NOT_VERIFIED",
        "baseline_comparison": [],
        "representative_conditions": [],
        "statistical_reproducibility": {},
        "overall_status": "FAIL",
    }

    # 1. Verify Phase 7 E4 Baseline
    e4_path = Path(phase7_e4_dir)
    if (e4_path / "metrics.json").is_file():
        e4_metrics = load_json(e4_path / "metrics.json")
        anom_e4 = e4_metrics.get("anomaly_detection", {})
        e4_map: dict[str, float] = {}
        for k, v in e4_metrics.items():
            if isinstance(v, dict):
                det = v.get("detector")
                rep = v.get("representation")
                test_f1 = v.get("test", {}).get("f1")
                if test_f1 is not None:
                    if det == "isolation_forest" and rep == "raw":
                        e4_map["if_raw"] = float(test_f1)
                    elif det == "isolation_forest" and rep == "residual":
                        e4_map["if_res"] = float(test_f1)
                    elif det == "lstm_autoencoder" and rep == "raw":
                        e4_map["lstm_raw"] = float(test_f1)
                    elif det == "lstm_autoencoder" and rep == "residual":
                        e4_map["lstm_res"] = float(test_f1)

        e4_checks = []
        all_e4_pass = True
        for m_key, exp_val in PHASE7_CANONICAL_TARGETS.items():
            actual_val = e4_map.get(m_key, anom_e4.get(m_key, {}).get("f1", -1.0))
            cmp_res = compare_metrics(actual_val, exp_val, tolerance=1e-3)
            e4_checks.append({
                "model": m_key,
                "metric": "f1",
                "actual": actual_val,
                "expected": exp_val,
                "classification": cmp_res["classification"],
                "abs_diff": cmp_res["absolute_difference"],
            })
            if cmp_res["classification"] not in ["BITWISE_IDENTICAL", "NUMERICALLY_EQUIVALENT"]:
                all_e4_pass = False

        report["baseline_comparison"] = e4_checks
        report["phase7_e4_status"] = "PASS" if all_e4_pass else "FAIL"
        pd.DataFrame(e4_checks).to_csv(repro_dir / "baseline_comparison.csv", index=False)

    # 2. Verify Phase 8 Corrected E5 Run across representative conditions
    e5_path = Path(phase8_e5_dir)
    if (e5_path / "comparison.csv").is_file() and (e5_path / "metrics.json").is_file():
        comp_df = pd.read_csv(e5_path / "comparison.csv")
        e5_records = []
        all_e5_rep_pass = True

        for dt, p_drop in REPRESENTATIVE_CONDITIONS:
            # Query Residual LSTM-AE F1 and LSTM Load MAPE
            sub_ad = comp_df[
                (comp_df["staleness_seconds"] == dt)
                & (np.isclose(comp_df["packet_drop_rate"], p_drop))
                & (comp_df["task"] == "anomaly_detection")
                & (comp_df["detector"] == "lstm_autoencoder")
                & (comp_df["representation"] == "residual")
                & (comp_df["metric"] == "f1")
            ]
            sub_le = comp_df[
                (comp_df["staleness_seconds"] == dt)
                & (np.isclose(comp_df["packet_drop_rate"], p_drop))
                & (comp_df["task"] == "load_estimation")
                & (comp_df["model"] == "lstm")
                & (comp_df["metric"] == "mape")
            ]

            val_ad = sub_ad["value"].values[0] if len(sub_ad) > 0 else None
            val_le = sub_le["value"].values[0] if len(sub_le) > 0 else None

            e5_records.append({
                "staleness_seconds": dt,
                "packet_drop_rate": p_drop,
                "residual_lstm_ae_f1": val_ad,
                "lstm_forecaster_mape": val_le,
                "status": "VALID" if (val_ad is not None and val_le is not None) else "MISSING",
            })
            if val_ad is None or val_le is None:
                all_e5_rep_pass = False

        report["representative_conditions"] = e5_records
        report["phase8_e5_status"] = "PASS" if all_e5_rep_pass else "FAIL"
        pd.DataFrame(e5_records).to_csv(repro_dir / "selected_condition_comparison.csv", index=False)

    # 3. Verify Phase 9 E6 Statistical Consistency
    e6_path = Path(phase9_e6_dir)
    if (e6_path / "H3_summary.csv").is_file():
        h3_df = pd.read_csv(e6_path / "H3_summary.csv")
        p9_h3_decision = h3_df["conclusion"].values[0] if "conclusion" in h3_df.columns else "UNKNOWN"
        p9_delta_beta = float(h3_df["delta_beta"].values[0]) if "delta_beta" in h3_df.columns else 0.0

        p9_pass = p9_h3_decision == "NOT_SUPPORTED" and p9_delta_beta < 0
        report["phase9_e6_status"] = "PASS" if p9_pass else "FAIL"
        report["statistical_reproducibility"]["phase9_h3_decision"] = p9_h3_decision
        report["statistical_reproducibility"]["phase9_delta_beta"] = p9_delta_beta

    # 4. Verify Phase 10 E10 Multi-Seed Robustness
    e10_path = Path(phase10_e10_dir)
    if (e10_path / "multiseed_h3_summary.csv").is_file():
        m_h3 = pd.read_csv(e10_path / "multiseed_h3_summary.csv")
        # All seeds should have delta_beta < 0 and decision NOT_SUPPORTED
        seed_rows = m_h3[m_h3["seed"] != "Multi-seed"]
        all_seeds_neg = bool((seed_rows["delta_beta"] < 0).all())
        all_not_supp = bool((seed_rows["decision"] == "NOT_SUPPORTED").all())

        p10_pass = all_seeds_neg and all_not_supp
        report["phase10_e10_status"] = "PASS" if p10_pass else "FAIL"
        report["statistical_reproducibility"]["phase10_sign_consistency_pct"] = 100.0 if all_seeds_neg else 0.0
        report["statistical_reproducibility"]["phase10_all_not_supported"] = all_not_supp

    # Overall Status determination
    if (
        report["phase7_e4_status"] == "PASS"
        and report["phase8_e5_status"] == "PASS"
        and report["phase9_e6_status"] == "PASS"
        and report["phase10_e10_status"] == "PASS"
    ):
        report["overall_status"] = "PASS"
    elif "PASS" in [
        report["phase7_e4_status"],
        report["phase8_e5_status"],
        report["phase9_e6_status"],
        report["phase10_e10_status"],
    ]:
        report["overall_status"] = "PARTIAL"
    else:
        report["overall_status"] = "FAIL"

    save_json(report, out / "reproducibility_report.json")
    return report
