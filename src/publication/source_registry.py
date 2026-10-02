"""src/publication/source_registry.py — Canonical scientific source registry for Phase 13.

Provides machine-readable tracking of every quantitative claim, mapping each to its
frozen source artifact with cryptographic verification per Phase 13 requirements.
"""

from dataclasses import asdict, dataclass, field
import math
from pathlib import Path
from typing import Any, Union
import yaml

from src.publication.sources import FrozenSourceRegistry
from src.utils.io import load_json, save_json
from src.utils.logging import get_logger

logger = get_logger("publication.source_registry")


@dataclass
class CanonicalClaim:
    """Dataclass representing a canonical scientific claim."""

    claim_id: str
    description: str
    value: Union[float, str]
    source_phase: str
    source_file: str
    source_field: str
    tolerance: float = 1e-4
    verified: bool = False
    actual_value: Union[float, str, None] = None


class Phase13SourceRegistry:
    """Registry for verifying Phase 13 claims against frozen artifacts."""

    def __init__(
        self,
        config_path: Union[str, Path] = "configs/publication/phase13_publication.yaml",
    ) -> None:
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.claims: dict[str, CanonicalClaim] = {}
        self._build_claims()

    def _load_config(self) -> dict[str, Any]:
        """Load the YAML configuration."""
        if not self.config_path.is_file():
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("phase13", data)

    def _build_claims(self) -> None:
        """Build CanonicalClaim objects from config."""
        claims_list = self.config.get("canonical_claims", [])
        default_tol = self.config.get("verification", {}).get("numerical_tolerance", 1e-4)

        for c_dict in claims_list:
            claim = CanonicalClaim(
                claim_id=c_dict["id"],
                description=c_dict["description"],
                value=c_dict["value"],
                source_phase=c_dict["source_phase"],
                source_file=c_dict["source_file"],
                source_field=c_dict["source_field"],
                tolerance=c_dict.get("tolerance", default_tol),
            )
            self.claims[claim.claim_id] = claim

    def get_claim(self, claim_id: str) -> CanonicalClaim:
        """Get a specific claim by ID."""
        if claim_id not in self.claims:
            raise KeyError(f"Claim {claim_id} not found in registry.")
        return self.claims[claim_id]

    def verify_all_claims(self, frozen_registry: FrozenSourceRegistry) -> dict[str, CanonicalClaim]:
        """Verify all canonical claims against frozen artifacts.

        Uses the actual data loading methods of FrozenSourceRegistry rather than
        relying on file paths.
        """
        logger.info("Verifying %d canonical claims against frozen artifacts...", len(self.claims))

        # Pre-load data from frozen registry
        e4_metrics = frozen_registry.load_phase7_e4_metrics()
        e5_comp = frozen_registry.load_phase8_e5_comparison()
        e10_h3 = frozen_registry.load_phase10_e10_h3_summary()
        e10_seeds = frozen_registry.load_phase10_e10_seed_results()
        e11_ablations = frozen_registry.load_phase11_ablations()
        e11_cp = frozen_registry.load_phase11_change_point()

        for claim_id, claim in self.claims.items():
            try:
                actual = self._resolve_actual_value(
                    claim,
                    e4_metrics=e4_metrics,
                    e5_comp=e5_comp,
                    e10_h3=e10_h3,
                    e10_seeds=e10_seeds,
                    e11_ablations=e11_ablations,
                    e11_cp=e11_cp,
                )
                claim.actual_value = actual

                if isinstance(claim.value, (int, float)) and isinstance(actual, (int, float)):
                    if claim.tolerance == 0:
                        claim.verified = int(claim.value) == int(actual)
                    else:
                        claim.verified = math.isclose(
                            float(claim.value), float(actual), abs_tol=claim.tolerance
                        )
                else:
                    claim.verified = str(claim.value).strip() == str(actual).strip()

                status = "PASS" if claim.verified else "FAIL"
                logger.info(
                    "Claim %s [%s]: expected=%s, actual=%s (status=%s)",
                    claim_id,
                    claim.description[:40],
                    claim.value,
                    actual,
                    status,
                )
            except Exception as exc:
                logger.error("Error verifying claim %s: %s", claim_id, exc)
                claim.verified = False
                claim.actual_value = f"ERROR: {exc}"

        return self.claims

    def _resolve_actual_value(
        self,
        claim: CanonicalClaim,
        **data: Any,
    ) -> Union[float, str, None]:
        """Resolve actual value from pre-loaded data."""
        # E4 baseline metrics
        if claim.source_phase == "phase7_e4":
            e4 = data["e4_metrics"]
            # e4 has keys like 'E4-1', 'E4-2', 'E4-3', 'E4-4'
            parts = claim.source_field.split(".")
            val = e4
            for p in parts:
                if isinstance(val, dict) and p in val:
                    val = val[p]
                else:
                    return None
            return float(val) if val is not None else None

        # E5 completeness
        elif claim.source_phase == "phase8_e5":
            e5 = data["e5_comp"]
            if claim.source_field == "condition_id.nunique":
                return int(e5["condition_id"].nunique())
            return None

        # E10 H3 summary
        elif claim.source_phase == "phase10_e10":
            if claim.source_file == "multiseed_h3_summary.csv":
                df = data["e10_h3"]
                ms_row = df[df["seed"] == "Multi-seed"]
                if ms_row.empty:
                    return None
                parts = claim.source_field.split(".")
                col = parts[1] if len(parts) > 1 else parts[0]
                val = ms_row[col].iloc[0]
                try:
                    return float(val)
                except ValueError:
                    return str(val)
            elif claim.source_file == "seed_results.csv":
                df = data["e10_seeds"]
                if claim.source_field == "seed_condition.nunique":
                    return int(len(df.groupby(["seed", "condition_id"])))
            return None

        # E11 ablations & change point
        elif claim.source_phase == "phase11_e11":
            if claim.source_file == "table_02_ablation_results.csv":
                df = data["e11_ablations"]
                if claim.source_field == "row_count":
                    return int(len(df))
            elif claim.source_file == "table_04_change_point_analysis.csv":
                df = data["e11_cp"]
                col = claim.source_field
                if col in df.columns:
                    return float(df[col].iloc[0])
            return None

        return None

    def export_registry(self, output_path: Path) -> None:
        """Export the verified registry to a JSON file."""
        data = {c_id: asdict(claim) for c_id, claim in self.claims.items()}
        save_json(data, output_path)
        logger.info("Exported canonical registry to %s", output_path)

    def summary(self) -> dict[str, int]:
        """Get a summary of verification results."""
        total = len(self.claims)
        verified = sum(1 for c in self.claims.values() if c.verified)
        failed = total - verified
        return {
            "total_claims": total,
            "verified_claims": verified,
            "failed_claims": failed,
        }
