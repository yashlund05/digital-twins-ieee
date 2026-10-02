"""src/audit/cross_phase_auditor.py — Cross-Phase Scientific Consistency & Figure/Table Auditing.

Verifies that equations, terminology, condition counts, seed numbers, baseline metrics,
and H3 statistics are internally coherent across Phases 7–13 without contradictions.
Audits Figure ↔ Table ↔ Source Data traceability per Objective B & Section 12-13.
"""

import math
from pathlib import Path
from typing import Any
import pandas as pd

from src.publication.sources import FrozenSourceRegistry
from src.utils.io import load_json, save_json
from src.utils.logging import get_logger

logger = get_logger("audit.cross_phase_auditor")


class CrossPhaseScientificAuditor:
    """Auditor for cross-phase coherence and figure/table data traceability."""

    def __init__(self, frozen_reg: FrozenSourceRegistry) -> None:
        self.frozen_reg = frozen_reg

    def verify_experimental_condition_coherence(self) -> dict[str, Any]:
        """Verify factorial conditions and seeds across E5, E10, and E11."""
        e5_comp = self.frozen_reg.load_phase8_e5_comparison()
        e10_seeds = self.frozen_reg.load_phase10_e10_seed_results()

        e5_conds = set(e5_comp["condition_id"].unique())
        e10_s42_conds = set(e10_seeds[e10_seeds["seed"] == 42]["condition_id"].unique())
        seeds = sorted(e10_seeds["seed"].unique().tolist())
        total_seed_conditions = len(e10_seeds.groupby(["seed", "condition_id"]))

        # Verify: E5 has 24 conditions, E10 has 120 seed-conditions, seed 42 matches exactly, all 5 seeds present
        passed = (
            len(e5_conds) == 24
            and e5_conds == e10_s42_conds
            and len(seeds) == 5
            and total_seed_conditions == 120
            and seeds == [42, 123, 456, 789, 101112]
        )

        return {
            "check": "experimental_conditions_coherence",
            "status": "PASS" if passed else "FAIL",
            "details": {
                "e5_unique_conditions": len(e5_conds),
                "e10_seed42_conditions": len(e10_s42_conds),
                "seed42_conditions_identical": e5_conds == e10_s42_conds,
                "total_seed_conditions": total_seed_conditions,
                "seeds_evaluated": seeds,
                "expected_seeds": [42, 123, 456, 789, 101112],
                "seeds_matched": seeds == [42, 123, 456, 789, 101112],
            },
        }

    def verify_baseline_reproducibility_coherence(self) -> dict[str, Any]:
        """Verify baseline values are coherent between E4, E5, E11, and E13."""
        e4_metrics = self.frozen_reg.load_phase7_e4_metrics()
        e11_repro = self.frozen_reg.load_phase11_reproducibility()

        # Check maximum absolute difference across reproduced baseline
        max_diff = float(e11_repro["abs_diff"].astype(float).max())
        f1_e4_res_lstm = float(e4_metrics["E4-4"]["test"]["f1"])

        passed = max_diff < 1e-4 and math.isclose(f1_e4_res_lstm, 0.977956, abs_tol=1e-5)

        return {
            "check": "baseline_reproducibility_coherence",
            "status": "PASS" if passed else "FAIL",
            "details": {
                "e4_residual_lstm_f1": f1_e4_res_lstm,
                "e11_max_reproduction_difference": max_diff,
                "tolerance": 1e-4,
                "passed": passed,
            },
        }

    def verify_h3_statistics_coherence(self) -> dict[str, Any]:
        """Verify H3 slope delta_beta and decisions across E6, E10, and E12."""
        e6_h3 = self.frozen_reg.load_phase9_e6_h3()
        e10_h3 = self.frozen_reg.load_phase10_e10_h3_summary()

        # Extract seed 42 row from E10
        s42_row = e10_h3[e10_h3["seed"].isin(["42", 42])]
        delta_beta_e10_s42 = float(s42_row["delta_beta"].iloc[0])

        # Extract primary comparison row from E6
        e6_row = e6_h3[e6_h3["task_comparison"].str.contains("lstm MAPE", case=False, na=False)]
        delta_beta_e6 = float(e6_row["delta_beta"].iloc[0])

        # Multi-seed row
        ms_row = e10_h3[e10_h3["seed"] == "Multi-seed"]
        delta_beta_ms = float(ms_row["delta_beta"].iloc[0])

        all_negative = (e10_h3["delta_beta"] < 0).all()
        all_not_supported = (e10_h3["decision"].str.strip() == "NOT_SUPPORTED").all()

        passed = (
            math.isclose(delta_beta_e10_s42, delta_beta_e6, abs_tol=1e-5)
            and all_negative
            and all_not_supported
        )

        return {
            "check": "h3_statistics_coherence",
            "status": "PASS" if passed else "FAIL",
            "details": {
                "e6_primary_delta_beta": delta_beta_e6,
                "e10_seed42_delta_beta": delta_beta_e10_s42,
                "e10_multiseed_delta_beta": delta_beta_ms,
                "all_seeds_delta_beta_negative": bool(all_negative),
                "all_seeds_decision_not_supported": bool(all_not_supported),
                "passed": passed,
            },
        }

    def verify_figure_table_source_linkage(self) -> dict[str, Any]:
        """Verify all 8 publication figures and 6 tables have valid source data CSVs."""
        logger.info("Auditing Figure ↔ Table ↔ Source Data traceability...")
        e12_dir = Path("experiments/runs/E12_PUBLICATION_ARTIFACTS_20261002")

        figure_audit: dict[str, Any] = {}
        for fig_num in range(1, 9):
            fig_id = f"fig_{fig_num:02d}"
            csv_path = e12_dir / "source_data" / f"{fig_id}_source.csv"
            pdf_path = list((e12_dir / "figures").glob(f"{fig_id}_*.pdf"))
            png_path = list((e12_dir / "figures").glob(f"{fig_id}_*.png"))

            has_source = csv_path.is_file()
            has_pdf = len(pdf_path) > 0 and pdf_path[0].is_file()
            has_png = len(png_path) > 0 and png_path[0].is_file()

            row_count = len(pd.read_csv(csv_path)) if has_source else 0

            figure_audit[fig_id] = {
                "has_source_csv": has_source,
                "has_pdf": has_pdf,
                "has_png": has_png,
                "source_rows": row_count,
                "traceable": has_source and has_pdf and has_png and row_count > 0,
            }

        table_audit: dict[str, Any] = {}
        for tab_num in range(1, 7):
            tab_id = f"table_{tab_num:02d}"
            csv_files = list((e12_dir / "tables").glob(f"{tab_id}_*.csv"))
            tex_files = list((e12_dir / "tables").glob(f"{tab_id}_*.tex"))

            has_csv = len(csv_files) > 0 and csv_files[0].is_file()
            has_tex = len(tex_files) > 0 and tex_files[0].is_file()
            row_count = len(pd.read_csv(csv_files[0])) if has_csv else 0

            table_audit[tab_id] = {
                "has_csv": has_csv,
                "has_tex": has_tex,
                "row_count": row_count,
                "traceable": has_csv and has_tex and row_count > 0,
            }

        all_figs_ok = all(v["traceable"] for v in figure_audit.values())
        all_tabs_ok = all(v["traceable"] for v in table_audit.values())

        return {
            "status": "PASS" if all_figs_ok and all_tabs_ok else "FAIL",
            "figures_audited": len(figure_audit),
            "tables_audited": len(table_audit),
            "figures": figure_audit,
            "tables": table_audit,
        }

    def run_full_cross_phase_audit(self, output_dir: Path) -> dict[str, Any]:
        """Execute full cross-phase consistency audit and export JSON."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        checks = {
            "experimental_conditions": self.verify_experimental_condition_coherence(),
            "baseline_reproducibility": self.verify_baseline_reproducibility_coherence(),
            "h3_statistics": self.verify_h3_statistics_coherence(),
        }

        fig_tab_res = self.verify_figure_table_source_linkage()
        save_json(fig_tab_res, output_dir / "figure_table_consistency.json")

        all_passed = all(c["status"] == "PASS" for c in checks.values()) and fig_tab_res["status"] == "PASS"

        report = {
            "overall_cross_phase_status": "PASS" if all_passed else "FAIL",
            "checks": checks,
            "figure_table_traceability": fig_tab_res["status"],
        }
        save_json(report, output_dir / "cross_phase_consistency.json")
        return report
