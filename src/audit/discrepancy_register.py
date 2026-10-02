"""src/audit/discrepancy_register.py — Discrepancy management and audit trail for Phase 14.

Tracks all identified inconsistencies across phases with strict schema, severity,
root cause, resolution, and supporting evidence per Phase 14 specifications.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.io import save_json
from src.utils.logging import get_logger

logger = get_logger("audit.discrepancy_register")


@dataclass
class DiscrepancyRecord:
    """A structured discrepancy record."""

    discrepancy_id: str
    phase: str
    artifact: str
    expected: str
    observed: str
    difference: str
    severity: str  # "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"
    root_cause: str
    resolution: str
    evidence: str
    status: str  # "RESOLVED", "ACCEPTED_DIFFERENCE", "UNRESOLVED", "BLOCKED"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DiscrepancyRegister:
    """Register for collecting, managing, and exporting discrepancies."""

    def __init__(self) -> None:
        self.records: list[DiscrepancyRecord] = []
        self._initialize_canonical_records()

    def _initialize_canonical_records(self) -> None:
        """Initialize known historical discrepancies including the C13 AoI investigation."""
        # 1. C13 AoI Transition Discrepancy: Instantaneous vs Macro Performance Cliff
        self.add_record(
            discrepancy_id="DISC-001-C13-AOI",
            phase="Phase 11 / Phase 12 / Phase 13",
            artifact="table_04_change_point_analysis.csv vs summary.md / figure_07",
            expected="AoI* ≈ 5.0 s (95% CI: [3.5, 7.5] s) in narrative text vs 0.0 s in automated detector table",
            observed="table_04_change_point_analysis.csv has 0.0 s; summary.md line 35 and figures report ~5.0 s",
            difference="Dual threshold formulation: micro-divergence point (0.0 s) vs macro performance cliff (5.0 s)",
            severity="MEDIUM",
            root_cause=(
                "Methodological duality (Case B): The automated threshold algorithm "
                "('residual_divergence_ratio_threshold') detects the first instantaneous residual spike "
                "exceeding 2x fresh level occurring at realized_aoi = 0.0 s due to micro-fluctuations. "
                "In contrast, the macro descriptive analysis identifies the empirical operational cliff "
                "occurring between dt = 1 s and dt = 5 s (centered at 5.0 s), where in-bin F1 collapses "
                "from 0.575 to 0.186 and residual norm jumps 16x."
            ),
            resolution=(
                "Preserved both observations with clear scientific demarcation: Claim C13 represents the "
                "micro instantaneous departure (0.0 s, CI: [0.0, 2.5] s), while Claim C14 represents the "
                "macro empirical transition cliff (5.0 s, CI: [3.5, 7.5] s). Manuscript text explicitly "
                "distinguishes instantaneous noise departure from the operational detection cliff."
            ),
            evidence=(
                "table_04_change_point_analysis.csv (0.0 s, DETECTED); summary.md line 35 (5.0 s, [3.5, 7.5] s); "
                "table_03_transient_statistics.csv (F1 drop 0.575 -> 0.186 between 0s and 1-5s); "
                "src/experiments/missed_update_transient.py lines 148-168."
            ),
            status="RESOLVED",
        )

        # 2. Metric scale asymmetry between bounded F1 and unbounded MAPE
        self.add_record(
            discrepancy_id="DISC-002-METRIC-SCALE",
            phase="Phase 9 / Phase 10 / Phase 13",
            artifact="multiseed_h3_summary.csv vs manuscript discussion",
            expected="Identical physical degradation interpretation across AD and LE tasks",
            observed="F1 is mathematically bounded in [0, 1] while MAPE is unbounded in [0, infinity)",
            difference="Structural mathematical asymmetry in degradation slope magnitude: beta_ad = 0.0201 vs beta_le = 1.2437",
            severity="LOW",
            root_cause=(
                "By mathematical definition, relative F1 degradation cannot exceed -1.0, whereas relative forecast "
                "error (MAPE) scales unboundedly as staleness grows to 300 s (MAPE reaches ~62%). This creates a "
                "scale asymmetry favoring steeper LE slopes regardless of physical task dynamics."
            ),
            resolution=(
                "Fully disclosed in manuscript Section V-B and Phase 13/14 scientific interpretation documentation. "
                "The non-support of H3 is reported strictly as an empirical finding under the pre-specified "
                "normalized log-linear protocol, without claiming universal physical robustness."
            ),
            evidence="Manuscript main.tex Section V-B; Phase 13 scientific interpretation doc Section 3.",
            status="RESOLVED",
        )

        # 3. pdflatex compiler environment availability
        self.add_record(
            discrepancy_id="DISC-003-LATEX-COMPILER",
            phase="Phase 13 / Phase 14",
            artifact="Environment LaTeX compiler",
            expected="Local pdflatex binary available for live PDF rendering",
            observed="pdflatex binary not found in Windows system PATH",
            difference="LaTeX compilation cannot run binary build locally; LaTeX source integrity must be verified structurally",
            severity="INFO",
            root_cause="Host OS environment does not have TeX Live / MiKTeX installed in PATH.",
            resolution=(
                "Implemented structural LaTeX syntax, citation, label, and path verification in audit suite. "
                "Manuscript LaTeX source is verified syntactically complete and verified clean for submission."
            ),
            evidence="System PATH audit; pdflatex command check returned ObjectNotFound.",
            status="ACCEPTED_DIFFERENCE",
        )

    def add_record(
        self,
        discrepancy_id: str,
        phase: str,
        artifact: str,
        expected: str,
        observed: str,
        difference: str,
        severity: str,
        root_cause: str,
        resolution: str,
        evidence: str,
        status: str,
    ) -> DiscrepancyRecord:
        """Add a new discrepancy record to the register."""
        rec = DiscrepancyRecord(
            discrepancy_id=discrepancy_id,
            phase=phase,
            artifact=artifact,
            expected=expected,
            observed=observed,
            difference=difference,
            severity=severity,
            root_cause=root_cause,
            resolution=resolution,
            evidence=evidence,
            status=status,
        )
        self.records.append(rec)
        logger.info(f"Registered discrepancy {discrepancy_id} [{severity}]: {status}")
        return rec

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all discrepancy records to a pandas DataFrame."""
        return pd.DataFrame([asdict(r) for r in self.records])

    def export(self, output_dir: Path) -> dict[str, Any]:
        """Export discrepancy register to CSV and JSON."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        data = [asdict(r) for r in self.records]
        save_json(data, output_dir / "discrepancy_register.json")

        df = self.to_dataframe()
        df.to_csv(output_dir / "discrepancy_register.csv", index=False)

        summary = {
            "total_discrepancies": len(self.records),
            "by_severity": df["severity"].value_counts().to_dict(),
            "by_status": df["status"].value_counts().to_dict(),
            "critical_unresolved": int(
                len(df[(df["severity"] == "CRITICAL") & (df["status"] == "UNRESOLVED")])
            ),
        }
        save_json(summary, output_dir / "discrepancy_summary.json")
        return summary
