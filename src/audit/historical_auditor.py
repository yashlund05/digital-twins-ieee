"""src/audit/historical_auditor.py — Independent Audit of Frozen Historical Phases.

Independently audits Phases 7 through 13 without mutating any historical artifact.
Generates structured audit reports for each historical phase per Objective A.
"""

from pathlib import Path
from typing import Any
import pandas as pd

from src.publication.sources import FrozenSourceRegistry
from src.reproducibility.hashing import hash_directory, hash_file
from src.utils.io import load_json, save_json
from src.utils.logging import get_logger

logger = get_logger("audit.historical_auditor")


class HistoricalReproducibilityAuditor:
    """Independent auditor for frozen historical phases 7 through 13."""

    def __init__(self, frozen_reg: FrozenSourceRegistry) -> None:
        self.frozen_reg = frozen_reg
        self.reports: dict[str, dict[str, Any]] = {}

    def audit_phase07_e4(self) -> dict[str, Any]:
        """Audit Phase 7 E4 Baseline Experiment."""
        logger.info("Auditing Phase 7 E4...")
        e4_dir = self.frozen_reg.phase7_dir
        metrics = self.frozen_reg.load_phase7_e4_metrics()

        # Check required models & representations
        f1_values = {
            "Raw + IF": metrics.get("E4-1", {}).get("test", {}).get("f1"),
            "Residual + IF": metrics.get("E4-2", {}).get("test", {}).get("f1"),
            "Raw + LSTM-AE": metrics.get("E4-3", {}).get("test", {}).get("f1"),
            "Residual + LSTM-AE": metrics.get("E4-4", {}).get("test", {}).get("f1"),
        }

        has_manifest = (e4_dir / "manifest.json").is_file()
        rep = {
            "phase": "Phase 7 E4 Baseline",
            "run_dir": str(e4_dir),
            "status": "PASS" if all(v is not None for v in f1_values.values()) else "FAIL",
            "has_manifest": has_manifest,
            "f1_values": f1_values,
            "file_count": len(list(e4_dir.glob("*"))),
        }
        self.reports["phase07_e4"] = rep
        return rep

    def audit_phase08_e5(self) -> dict[str, Any]:
        """Audit Phase 8 E5 Staleness Sweep."""
        logger.info("Auditing Phase 8 E5...")
        e5_dir = self.frozen_reg.phase8_dir
        comp = self.frozen_reg.load_phase8_e5_comparison()
        aoi_stats = self.frozen_reg.load_phase8_e5_aoi()

        cond_count = comp["condition_id"].nunique()
        has_predictions = (e5_dir / "predictions.parquet").is_file()

        rep = {
            "phase": "Phase 8 E5 Factorial Staleness Sweep",
            "run_dir": str(e5_dir),
            "status": "PASS" if cond_count == 24 else "FAIL",
            "condition_count": int(cond_count),
            "expected_conditions": 24,
            "has_predictions_parquet": has_predictions,
            "aoi_stats_present": bool(aoi_stats),
            "file_count": len(list(e5_dir.glob("*"))),
        }
        self.reports["phase08_e5"] = rep
        return rep

    def audit_phase09_e6(self) -> dict[str, Any]:
        """Audit Phase 9 E6 Joint Statistical Degradation & H3."""
        logger.info("Auditing Phase 9 E6...")
        e6_dir = self.frozen_reg.phase9_dir
        h3_df = self.frozen_reg.load_phase9_e6_h3()
        boot_df = self.frozen_reg.load_phase9_e6_bootstrap()
        reg_df = self.frozen_reg.load_phase9_e6_regression()

        lstm_row = h3_df[h3_df["task_comparison"].str.contains("lstm MAPE", case=False, na=False)]
        delta_beta = float(lstm_row["delta_beta"].iloc[0]) if not lstm_row.empty else None
        conclusion = str(lstm_row["conclusion"].iloc[0]).strip() if not lstm_row.empty else None

        rep = {
            "phase": "Phase 9 E6 Joint Analysis & H3 Testing",
            "run_dir": str(e6_dir),
            "status": "PASS" if conclusion == "NOT_SUPPORTED" else "FAIL",
            "h3_comparisons_count": len(h3_df),
            "primary_delta_beta": delta_beta,
            "primary_decision": conclusion,
            "bootstrap_rows": len(boot_df),
            "regression_rows": len(reg_df),
        }
        self.reports["phase09_e6"] = rep
        return rep

    def audit_phase10_e10(self) -> dict[str, Any]:
        """Audit Phase 10 E10 Multi-Seed Analysis."""
        logger.info("Auditing Phase 10 E10...")
        e10_dir = self.frozen_reg.phase10_dir
        h3_sum = self.frozen_reg.load_phase10_e10_h3_summary()
        seeds_df = self.frozen_reg.load_phase10_e10_seed_results()
        tests_df = self.frozen_reg.load_phase10_e10_hypothesis_tests()

        sc_count = len(seeds_df.groupby(["seed", "condition_id"]))
        seeds = seeds_df["seed"].unique().tolist()
        ms_row = h3_sum[h3_sum["seed"] == "Multi-seed"]
        ms_decision = str(ms_row["decision"].iloc[0]).strip() if not ms_row.empty else None
        all_not_supported = (h3_sum["decision"].str.strip() == "NOT_SUPPORTED").all()

        rep = {
            "phase": "Phase 10 E10 Multi-Seed Uncertainty Analysis",
            "run_dir": str(e10_dir),
            "status": "PASS" if sc_count == 120 and all_not_supported else "FAIL",
            "total_seed_conditions": int(sc_count),
            "seeds_evaluated": [int(s) for s in seeds],
            "multiseed_decision": ms_decision,
            "all_seeds_not_supported": bool(all_not_supported),
            "pairwise_tests_count": len(tests_df),
        }
        self.reports["phase10_e10"] = rep
        return rep

    def audit_phase11_e11(self) -> dict[str, Any]:
        """Audit Phase 11 E11 Reproducibility, Ablations, and Transient Analysis."""
        logger.info("Auditing Phase 11 E11...")
        e11_dir = self.frozen_reg.phase11_dir
        repro_df = self.frozen_reg.load_phase11_reproducibility()
        abl_df = self.frozen_reg.load_phase11_ablations()
        cp_df = self.frozen_reg.load_phase11_change_point()
        trans_df = self.frozen_reg.load_phase11_transient_stats()

        max_diff = float(repro_df["abs_diff"].astype(float).max())
        unique_ablations = abl_df["ablation_id"].nunique()

        rep = {
            "phase": "Phase 11 E11 Reproducibility & Transient Analysis",
            "run_dir": str(e11_dir),
            "status": "PASS" if max_diff < 1e-4 and unique_ablations == 8 else "FAIL",
            "reproducibility_max_diff": max_diff,
            "reproducibility_passed": max_diff < 1e-4,
            "unique_ablation_ids": int(unique_ablations),
            "total_ablation_evaluations": len(abl_df),
            "change_point_stored_aoi": float(cp_df["estimated_transition_aoi_seconds"].iloc[0]),
            "transient_bins_count": len(trans_df),
        }
        self.reports["phase11_e11"] = rep
        return rep

    def audit_phase12_e12(self) -> dict[str, Any]:
        """Audit Phase 12 Publication Artifacts."""
        logger.info("Auditing Phase 12 E12...")
        e12_dir = Path("experiments/runs/E12_PUBLICATION_ARTIFACTS_20261002")
        fig_count = len(list((e12_dir / "figures").glob("*.pdf"))) if (e12_dir / "figures").is_dir() else 0
        tab_count = len(list((e12_dir / "tables").glob("*.csv"))) if (e12_dir / "tables").is_dir() else 0
        source_csvs = len(list((e12_dir / "source_data").glob("*.csv"))) if (e12_dir / "source_data").is_dir() else 0

        rep = {
            "phase": "Phase 12 Publication Artifacts",
            "run_dir": str(e12_dir),
            "status": "PASS" if fig_count == 8 and tab_count == 6 else "FAIL",
            "figures_pdf_count": fig_count,
            "tables_csv_count": tab_count,
            "source_csvs_count": source_csvs,
            "has_integrity_report": (e12_dir / "integrity_report.json").is_file(),
            "has_hash_manifest": (e12_dir / "provenance" / "hash_manifest.json").is_file(),
        }
        self.reports["phase12_e12"] = rep
        return rep

    def audit_phase13_e13(self) -> dict[str, Any]:
        """Audit Phase 13 Manuscript Package & Claims."""
        logger.info("Auditing Phase 13 E13...")
        e13_dir = Path("experiments/runs/E13_MANUSCRIPT_SUBMISSION_20261002")
        has_main_tex = (e13_dir / "manuscript" / "main.tex").is_file()
        has_bib = (e13_dir / "manuscript" / "references.bib").is_file()
        has_claims = (e13_dir / "audit_reports" / "canonical_claims_registry.json").is_file()

        claims_data = load_json(e13_dir / "audit_reports" / "canonical_claims_registry.json") if has_claims else {}
        verified_count = sum(1 for c in claims_data.values() if c.get("verified", False))

        rep = {
            "phase": "Phase 13 Manuscript & Claims Registry",
            "run_dir": str(e13_dir),
            "status": "PASS" if has_main_tex and has_bib and verified_count >= 13 else "FAIL",
            "has_main_tex": has_main_tex,
            "has_references_bib": has_bib,
            "claims_verified_count": verified_count,
            "total_claims_in_registry": len(claims_data),
        }
        self.reports["phase13_e13"] = rep
        return rep

    def run_all_historical_audits(self, output_dir: Path) -> dict[str, Any]:
        """Execute audits for all phases 7 through 13 and save reports."""
        out_phases = Path(output_dir) / "phase_audits"
        out_phases.mkdir(parents=True, exist_ok=True)

        audits = [
            ("phase07_e4", self.audit_phase07_e4),
            ("phase08_e5", self.audit_phase08_e5),
            ("phase09_e6", self.audit_phase09_e6),
            ("phase10_e10", self.audit_phase10_e10),
            ("phase11_e11", self.audit_phase11_e11),
            ("phase12_e12", self.audit_phase12_e12),
            ("phase13_e13", self.audit_phase13_e13),
        ]

        all_passed = True
        summary = {}
        for phase_name, audit_fn in audits:
            res = audit_fn()
            save_json(res, out_phases / f"{phase_name}.json")
            summary[phase_name] = res["status"]
            if res["status"] != "PASS":
                all_passed = False

        overall = {
            "overall_historical_status": "PASS" if all_passed else "FAIL",
            "phases_audited": len(audits),
            "passed_phases": sum(1 for s in summary.values() if s == "PASS"),
            "summary": summary,
        }
        save_json(overall, output_dir / "reproducibility_summary.json")
        return overall
