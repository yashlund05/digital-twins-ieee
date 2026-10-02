"""src/publication/numerical_audit.py — Numerical consistency audit for Phase 13.

Verifies that all numerical values in the manuscript match their frozen source
artifacts within strict tolerances. No fabricated or interpolated numbers are permitted.
"""

import math
from pathlib import Path
from typing import Any

from src.publication.source_registry import Phase13SourceRegistry
from src.publication.sources import FrozenSourceRegistry
from src.utils.io import save_json
from src.utils.logging import get_logger

logger = get_logger("publication.numerical_audit")


class NumericalConsistencyAudit:
    """Audit class for numerical consistency checks across frozen artifacts."""

    def __init__(
        self,
        source_registry: Phase13SourceRegistry,
        frozen_registry: FrozenSourceRegistry,
        tolerance: float = 1e-4,
    ) -> None:
        self.source_reg = source_registry
        self.frozen_reg = frozen_registry
        self.tolerance = tolerance

    def verify_e4_baseline(self) -> dict[str, Any]:
        """Verify Phase 7 E4 baseline F1 values."""
        metrics = self.frozen_reg.load_phase7_e4_metrics()

        expected = {
            "Raw + IF": (0.117647, metrics.get("E4-1", {}).get("test", {}).get("f1")),
            "Residual + IF": (0.088727, metrics.get("E4-2", {}).get("test", {}).get("f1")),
            "Raw + LSTM-AE": (0.538606, metrics.get("E4-3", {}).get("test", {}).get("f1")),
            "Residual + LSTM-AE": (0.977956, metrics.get("E4-4", {}).get("test", {}).get("f1")),
        }

        details = {}
        all_passed = True
        for name, (exp_val, act_val) in expected.items():
            if act_val is None:
                passed = False
            else:
                passed = math.isclose(float(exp_val), float(act_val), abs_tol=self.tolerance)
            details[name] = {
                "expected": exp_val,
                "actual": act_val,
                "passed": passed,
                "abs_diff": abs(float(exp_val) - float(act_val)) if act_val is not None else None,
            }
            if not passed:
                all_passed = False

        return {
            "status": "PASS" if all_passed else "FAIL",
            "check": "e4_baseline_f1",
            "details": details,
        }

    def verify_e10_h3(self) -> dict[str, Any]:
        """Verify Phase 10 E10 multi-seed H3 summary values."""
        df = self.frozen_reg.load_phase10_e10_h3_summary()
        ms_row = df[df["seed"] == "Multi-seed"]

        if ms_row.empty:
            return {"status": "FAIL", "check": "e10_h3", "error": "Multi-seed row missing"}

        row = ms_row.iloc[0]
        expected = {
            "delta_beta": (-1.2236455016005805, float(row["delta_beta"])),
            "ci_lower": (-1.3462600065803283, float(row["ci_lower"])),
            "ci_upper": (-1.1134119167064354, float(row["ci_upper"])),
            "p_value_slope": (1.0, float(row["p_value_slope"])),
        }

        details = {}
        all_passed = True
        for name, (exp_val, act_val) in expected.items():
            passed = math.isclose(exp_val, act_val, abs_tol=self.tolerance)
            details[name] = {
                "expected": exp_val,
                "actual": act_val,
                "passed": passed,
                "abs_diff": abs(exp_val - act_val),
            }
            if not passed:
                all_passed = False

        decision = str(row["decision"]).strip()
        details["decision"] = {
            "expected": "NOT_SUPPORTED",
            "actual": decision,
            "passed": decision == "NOT_SUPPORTED",
        }
        if decision != "NOT_SUPPORTED":
            all_passed = False

        return {
            "status": "PASS" if all_passed else "FAIL",
            "check": "e10_h3_summary",
            "details": details,
        }

    def verify_e11_change_point(self) -> dict[str, Any]:
        """Verify Phase 11 E11 change point AoI value."""
        df = self.frozen_reg.load_phase11_change_point()
        val = float(df["estimated_transition_aoi_seconds"].iloc[0])
        status = str(df["status"].iloc[0]).strip()

        passed = math.isclose(val, 0.0, abs_tol=self.tolerance) and status == "DETECTED"

        return {
            "status": "PASS" if passed else "FAIL",
            "check": "e11_change_point_aoi",
            "details": {
                "estimated_transition_aoi_seconds": {
                    "expected": 0.0,
                    "actual": val,
                    "passed": math.isclose(val, 0.0, abs_tol=self.tolerance),
                },
                "detection_status": {
                    "expected": "DETECTED",
                    "actual": status,
                    "passed": status == "DETECTED",
                },
            },
        }

    def verify_e5_completeness(self) -> dict[str, Any]:
        """Verify 24 factorial conditions exist in Phase 8 E5."""
        comp = self.frozen_reg.load_phase8_e5_comparison()
        n_cond = int(comp["condition_id"].nunique())
        passed = n_cond == 24

        return {
            "status": "PASS" if passed else "FAIL",
            "check": "e5_condition_completeness",
            "details": {
                "expected_conditions": 24,
                "actual_conditions": n_cond,
                "passed": passed,
            },
        }

    def verify_e10_completeness(self) -> dict[str, Any]:
        """Verify 120 seed-conditions exist in Phase 10 E10."""
        seeds = self.frozen_reg.load_phase10_e10_seed_results()
        n_sc = int(len(seeds.groupby(["seed", "condition_id"])))
        passed = n_sc == 120

        return {
            "status": "PASS" if passed else "FAIL",
            "check": "e10_seed_condition_completeness",
            "details": {
                "expected_seed_conditions": 120,
                "actual_seed_conditions": n_sc,
                "passed": passed,
            },
        }

    def verify_e11_completeness(self) -> dict[str, Any]:
        """Verify 88 ablation evaluations (or 8 unique ablation IDs) in Phase 11."""
        abl = self.frozen_reg.load_phase11_ablations()
        n_rows = len(abl)
        n_ids = int(abl["ablation_id"].nunique())
        passed = (n_rows == 88) or (n_ids == 8)

        return {
            "status": "PASS" if passed else "FAIL",
            "check": "e11_ablation_completeness",
            "details": {
                "expected_ablation_evaluations": 88,
                "actual_ablation_rows": n_rows,
                "unique_ablation_ids": n_ids,
                "passed": passed,
            },
        }

    def run_full_audit(self) -> dict[str, Any]:
        """Run all numerical consistency checks and return full report."""
        logger.info("Executing comprehensive numerical consistency audit...")

        checks = {
            "e4_baseline": self.verify_e4_baseline(),
            "e10_h3": self.verify_e10_h3(),
            "e11_change_point": self.verify_e11_change_point(),
            "e5_completeness": self.verify_e5_completeness(),
            "e10_completeness": self.verify_e10_completeness(),
            "e11_completeness": self.verify_e11_completeness(),
        }

        all_passed = all(c.get("status") == "PASS" for c in checks.values())

        report = {
            "overall_status": "PASS" if all_passed else "FAIL",
            "total_checks": len(checks),
            "passed_checks": sum(1 for c in checks.values() if c.get("status") == "PASS"),
            "failed_checks": sum(1 for c in checks.values() if c.get("status") != "PASS"),
            "checks": checks,
        }

        logger.info(
            "Numerical consistency audit completed: status=%s (%d/%d passed)",
            report["overall_status"],
            report["passed_checks"],
            report["total_checks"],
        )
        return report

    def export_report(self, output_path: Path) -> None:
        """Export numerical consistency audit report to JSON."""
        report = self.run_full_audit()
        save_json(report, output_path)
        logger.info("Numerical audit report exported to %s", output_path)
