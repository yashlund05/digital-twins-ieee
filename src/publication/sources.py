"""src/publication/sources.py — Read-only source loader and registry for Phase 12.

Loads frozen artifacts from Phases 7–11 without mutation and establishes cryptographic
source integrity per Section 2.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.reproducibility.hashing import hash_file
from src.utils.io import load_json
from src.utils.logging import get_logger

logger = get_logger("publication.sources")


def load_phase12_sources_config(
    config_path: Path | str = "configs/publication/phase12_sources.yaml",
) -> dict[str, Any]:
    """Load and parse the Phase 12 sources YAML configuration."""
    p = Path(config_path)
    if not p.is_file():
        raise FileNotFoundError(f"Phase 12 configuration not found at {p}")
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("phase12", data)


class FrozenSourceRegistry:
    """Read-only registry managing frozen experimental evidence from Phases 7 to 11."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or load_phase12_sources_config()
        self.source_defs = self.config.get("source_runs", {})

        # Resolve paths
        self.phase7_dir = Path(
            self.source_defs.get("phase7_e4", {}).get(
                "path", "experiments/runs/E4_RAW_VS_RESIDUAL_SEED42_20260930"
            )
        )
        self.phase8_dir = Path(
            self.source_defs.get("phase8_e5", {}).get(
                "path", "experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930"
            )
        )
        self.phase9_dir = Path(
            self.source_defs.get("phase9_e6", {}).get(
                "path", "experiments/runs/E6_JOINT_ANALYSIS_SEED42_20261002"
            )
        )
        self.phase10_dir = Path(
            self.source_defs.get("phase10_e10", {}).get(
                "path", "experiments/runs/E10_MULTI_SEED_ANALYSIS_20261002"
            )
        )
        self.phase11_dir = Path(
            self.source_defs.get("phase11_e11", {}).get(
                "path", "experiments/runs/E11_PHASE11_20261002"
            )
        )

        self.source_hashes: dict[str, str] = {}
        self._record_source_hashes()

    def _record_source_hashes(self) -> None:
        """Compute cryptographic hashes for all registered source files."""
        for name, run_dir in [
            ("phase7_e4", self.phase7_dir),
            ("phase8_e5", self.phase8_dir),
            ("phase9_e6", self.phase9_dir),
            ("phase10_e10", self.phase10_dir),
            ("phase11_e11", self.phase11_dir),
        ]:
            if run_dir.exists():
                for item in run_dir.glob("*"):
                    if item.is_file():
                        rel = f"{name}/{item.name}"
                        self.source_hashes[rel] = hash_file(item)

    # -------------------------------------------------------------------------
    # Phase 7 E4 Baseline Loaders
    # -------------------------------------------------------------------------
    def load_phase7_e4_metrics(self) -> dict[str, Any]:
        p = self.phase7_dir / "metrics.json"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 7 E4 metrics.json at {p}")
        return load_json(p)

    def load_phase7_e4_comparison(self) -> pd.DataFrame:
        p = self.phase7_dir / "comparison.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 7 E4 comparison.csv at {p}")
        return pd.read_csv(p)

    # -------------------------------------------------------------------------
    # Phase 8 E5 Sweep Loaders
    # -------------------------------------------------------------------------
    def load_phase8_e5_comparison(self) -> pd.DataFrame:
        p = self.phase8_dir / "comparison.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 8 E5 comparison.csv at {p}")
        return pd.read_csv(p)

    def load_phase8_e5_aoi(self) -> dict[str, Any]:
        p = self.phase8_dir / "aoi_statistics.json"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 8 E5 aoi_statistics.json at {p}")
        return load_json(p)

    # -------------------------------------------------------------------------
    # Phase 9 E6 Hypothesis Testing Loaders
    # -------------------------------------------------------------------------
    def load_phase9_e6_h3(self) -> pd.DataFrame:
        p = self.phase9_dir / "H3_summary.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 9 E6 H3_summary.csv at {p}")
        return pd.read_csv(p)

    def load_phase9_e6_bootstrap(self) -> pd.DataFrame:
        p = self.phase9_dir / "bootstrap_results.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 9 E6 bootstrap_results.csv at {p}")
        return pd.read_csv(p)

    def load_phase9_e6_regression(self) -> pd.DataFrame:
        p = self.phase9_dir / "regression_results.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 9 E6 regression_results.csv at {p}")
        return pd.read_csv(p)

    # -------------------------------------------------------------------------
    # Phase 10 E10 Multi-Seed Loaders
    # -------------------------------------------------------------------------
    def load_phase10_e10_h3_summary(self) -> pd.DataFrame:
        p = self.phase10_dir / "multiseed_h3_summary.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 10 E10 multiseed_h3_summary.csv at {p}")
        return pd.read_csv(p)

    def load_phase10_e10_hypothesis_tests(self) -> pd.DataFrame:
        p = self.phase10_dir / "multiseed_hypothesis_tests.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 10 E10 multiseed_hypothesis_tests.csv at {p}")
        return pd.read_csv(p)

    def load_phase10_e10_seed_results(self) -> pd.DataFrame:
        p = self.phase10_dir / "seed_results.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 10 E10 seed_results.csv at {p}")
        return pd.read_csv(p)

    def load_phase10_e10_condition_statistics(self) -> pd.DataFrame:
        p = self.phase10_dir / "condition_statistics.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 10 E10 condition_statistics.csv at {p}")
        return pd.read_csv(p)

    def load_phase10_e10_interaction(self) -> pd.DataFrame:
        p = self.phase10_dir / "interaction_effects.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 10 E10 interaction_effects.csv at {p}")
        return pd.read_csv(p)

    # -------------------------------------------------------------------------
    # Phase 11 E11 Reproducibility & Ablation Loaders
    # -------------------------------------------------------------------------
    def load_phase11_reproducibility(self) -> pd.DataFrame:
        p = self.phase11_dir / "table_01_reproducibility.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 11 table_01_reproducibility.csv at {p}")
        return pd.read_csv(p)

    def load_phase11_ablations(self) -> pd.DataFrame:
        p = self.phase11_dir / "table_02_ablation_results.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 11 table_02_ablation_results.csv at {p}")
        return pd.read_csv(p)

    def load_phase11_transient_stats(self) -> pd.DataFrame:
        p = self.phase11_dir / "table_03_transient_statistics.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 11 table_03_transient_statistics.csv at {p}")
        return pd.read_csv(p)

    def load_phase11_change_point(self) -> pd.DataFrame:
        p = self.phase11_dir / "table_04_change_point_analysis.csv"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 11 table_04_change_point_analysis.csv at {p}")
        return pd.read_csv(p)

    def load_phase11_reproducibility_report(self) -> dict[str, Any]:
        p = self.phase11_dir / "reproducibility_report.json"
        if not p.is_file():
            raise FileNotFoundError(f"Missing Phase 11 reproducibility_report.json at {p}")
        return load_json(p)

    def export_source_registry_manifest(self) -> dict[str, Any]:
        """Export serialized dictionary of registry configuration and hashes."""
        return {
            "source_runs": {
                "phase7_e4": {"path": str(self.phase7_dir), "exists": self.phase7_dir.exists()},
                "phase8_e5": {"path": str(self.phase8_dir), "exists": self.phase8_dir.exists()},
                "phase9_e6": {"path": str(self.phase9_dir), "exists": self.phase9_dir.exists()},
                "phase10_e10": {"path": str(self.phase10_dir), "exists": self.phase10_dir.exists()},
                "phase11_e11": {"path": str(self.phase11_dir), "exists": self.phase11_dir.exists()},
            },
            "source_hashes": self.source_hashes,
        }
