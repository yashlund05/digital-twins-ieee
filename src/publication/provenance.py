"""src/publication/provenance.py — Cryptographic provenance and audit trail generation for Phase 12.

Builds figure_provenance.json, table_provenance.json, and hash_manifest.json per Section 8 & 9.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.reproducibility.hashing import hash_directory, hash_file
from src.utils.io import save_json
from src.utils.logging import get_logger

logger = get_logger("publication.provenance")


def build_figure_provenance(
    output_dir: Path, source_hashes: dict[str, str]
) -> list[dict[str, Any]]:
    """Construct provenance records for all 8 publication figures."""
    figures_def = [
        {
            "figure_id": "fig_01",
            "title": "System Architecture & Co-Simulation Framework",
            "source_runs": [
                "configs/experiments/e5_staleness_sweep.yaml",
                "docs/architecture/SYSTEM_ARCHITECTURE.md",
            ],
            "source_files": ["SYSTEM_ARCHITECTURE.md"],
            "transformations": ["architectural_pipeline_rendering"],
            "random_seed": None,
            "png_file": "figures/fig_01_system_architecture.png",
            "pdf_file": "figures/fig_01_system_architecture.pdf",
            "source_csv": "source_data/fig_01_source.csv",
        },
        {
            "figure_id": "fig_02",
            "title": "Historical Baseline Reconciliation",
            "source_runs": ["phase7_e4", "phase11_e11"],
            "source_files": ["table_01_reproducibility.csv", "metrics.json"],
            "transformations": ["baseline_f1_comparison", "numerical_equivalence_test"],
            "random_seed": 42,
            "png_file": "figures/fig_02_baseline_reconciliation.png",
            "pdf_file": "figures/fig_02_baseline_reconciliation.pdf",
            "source_csv": "source_data/fig_02_source.csv",
        },
        {
            "figure_id": "fig_03",
            "title": "Anomaly Detection Degradation vs. Staleness",
            "source_runs": ["phase8_e5"],
            "source_files": ["comparison.csv"],
            "transformations": [
                "filter_anomaly_detection_f1",
                "group_by_staleness_and_packet_drop",
            ],
            "random_seed": 42,
            "png_file": "figures/fig_03_anomaly_staleness.png",
            "pdf_file": "figures/fig_03_anomaly_staleness.pdf",
            "source_csv": "source_data/fig_03_source.csv",
        },
        {
            "figure_id": "fig_04",
            "title": "Load Estimation Degradation vs. Staleness",
            "source_runs": ["phase8_e5"],
            "source_files": ["comparison.csv"],
            "transformations": ["filter_load_estimation_mape", "compute_packet_drop_bounds"],
            "random_seed": 42,
            "png_file": "figures/fig_04_load_estimation_staleness.png",
            "pdf_file": "figures/fig_04_load_estimation_staleness.pdf",
            "source_csv": "source_data/fig_04_source.csv",
        },
        {
            "figure_id": "fig_05",
            "title": "Raw vs. Residual Representation Transition",
            "source_runs": ["phase8_e5"],
            "source_files": ["comparison.csv"],
            "transformations": ["contrast_residual_and_raw_lstm_ae", "mark_transition_region"],
            "random_seed": 42,
            "png_file": "figures/fig_05_residual_vs_raw_transition.png",
            "pdf_file": "figures/fig_05_residual_vs_raw_transition.pdf",
            "source_csv": "source_data/fig_05_source.csv",
        },
        {
            "figure_id": "fig_06",
            "title": "Multi-Seed Uncertainty Trajectories",
            "source_runs": ["phase10_e10"],
            "source_files": ["seed_results.csv"],
            "transformations": ["extract_seed_traces", "compute_mean_and_95ci_band"],
            "random_seed": [42, 123, 456, 789, 101112],
            "png_file": "figures/fig_06_multiseed_uncertainty.png",
            "pdf_file": "figures/fig_06_multiseed_uncertainty.pdf",
            "source_csv": "source_data/fig_06_source.csv",
        },
        {
            "figure_id": "fig_07",
            "title": "Intra-Epoch Residual Drift vs. AoI",
            "source_runs": ["phase11_e11"],
            "source_files": ["table_03_transient_statistics.csv"],
            "transformations": ["bin_residual_norm_by_aoi", "plot_dual_axis_drift_and_f1"],
            "random_seed": 42,
            "png_file": "figures/fig_07_aoi_residual_transient.png",
            "pdf_file": "figures/fig_07_aoi_residual_transient.pdf",
            "source_csv": "source_data/fig_07_source.csv",
        },
        {
            "figure_id": "fig_08",
            "title": "H3 Hypothesis Testing Forest Plot",
            "source_runs": ["phase10_e10"],
            "source_files": ["multiseed_h3_summary.csv"],
            "transformations": ["extract_delta_beta_and_ci", "forest_plot_rendering"],
            "random_seed": [42, 123, 456, 789, 101112],
            "png_file": "figures/fig_08_h3_multiseed_effect.png",
            "pdf_file": "figures/fig_08_h3_multiseed_effect.pdf",
            "source_csv": "source_data/fig_08_source.csv",
        },
    ]

    records = []
    now_str = datetime.now().isoformat()
    for fd in figures_def:
        png_p = output_dir / fd["png_file"]
        pdf_p = output_dir / fd["pdf_file"]
        csv_p = output_dir / fd["source_csv"]

        records.append(
            {
                "figure_id": fd["figure_id"],
                "figure_title": fd["title"],
                "source_runs": fd["source_runs"],
                "source_files": fd["source_files"],
                "transformations": fd["transformations"],
                "random_seed": fd["random_seed"],
                "generated_by": "src.publication.figure_factory",
                "generated_at": now_str,
                "png_hash": hash_file(png_p) if png_p.is_file() else "",
                "pdf_hash": hash_file(pdf_p) if pdf_p.is_file() else "",
                "source_csv_hash": hash_file(csv_p) if csv_p.is_file() else "",
            }
        )

    save_json(records, output_dir / "provenance" / "figure_provenance.json")
    return records


def build_table_provenance(output_dir: Path, source_hashes: dict[str, str]) -> list[dict[str, Any]]:
    """Construct provenance records for all 6 publication tables."""
    tables_def = [
        {
            "table_id": "table_01",
            "title": "Experimental Configuration",
            "source_runs": [
                "configs/digital_twin.yaml",
                "configs/experiments/e5_staleness_sweep.yaml",
            ],
            "source_files": ["config_snapshot.yaml"],
            "transformations": ["structured_parameter_extraction"],
            "csv_file": "tables/table_01_experimental_configuration.csv",
            "tex_file": "tables/table_01_experimental_configuration.tex",
        },
        {
            "table_id": "table_02",
            "title": "Baseline Reconciliation",
            "source_runs": ["phase7_e4", "phase11_e11"],
            "source_files": ["metrics.json", "table_01_reproducibility.csv"],
            "transformations": ["metric_comparison", "tolerance_verification"],
            "csv_file": "tables/table_02_baseline_reconciliation.csv",
            "tex_file": "tables/table_02_baseline_reconciliation.tex",
        },
        {
            "table_id": "table_03",
            "title": "E5 Factorial Condition Summary",
            "source_runs": ["phase8_e5"],
            "source_files": ["comparison.csv"],
            "transformations": ["pivot_24_conditions", "aggregate_models"],
            "csv_file": "tables/table_03_e5_condition_summary.csv",
            "tex_file": "tables/table_03_e5_condition_summary.tex",
        },
        {
            "table_id": "table_04",
            "title": "Multi-Seed Degradation Results",
            "source_runs": ["phase10_e10"],
            "source_files": ["multiseed_h3_summary.csv"],
            "transformations": ["multi_seed_extraction", "ci_formatting"],
            "csv_file": "tables/table_04_multiseed_results.csv",
            "tex_file": "tables/table_04_multiseed_results.tex",
        },
        {
            "table_id": "table_05",
            "title": "Controlled Ablation Summary",
            "source_runs": ["phase11_e11"],
            "source_files": ["table_02_ablation_results.csv"],
            "transformations": ["ablation_synthesis", "cautious_interpretation_mapping"],
            "csv_file": "tables/table_05_ablation_summary.csv",
            "tex_file": "tables/table_05_ablation_summary.tex",
        },
        {
            "table_id": "table_06",
            "title": "Pairwise H3 Statistical Tests",
            "source_runs": ["phase10_e10"],
            "source_files": ["multiseed_hypothesis_tests.csv"],
            "transformations": ["hypothesis_test_table_formatting"],
            "csv_file": "tables/table_06_h3_statistics.csv",
            "tex_file": "tables/table_06_h3_statistics.tex",
        },
    ]

    records = []
    now_str = datetime.now().isoformat()
    for td in tables_def:
        csv_p = output_dir / td["csv_file"]
        tex_p = output_dir / td["tex_file"]

        row_cnt = 0
        col_cnt = 0
        if csv_p.is_file():
            df = pd.read_csv(csv_p)
            row_cnt = len(df)
            col_cnt = len(df.columns)

        records.append(
            {
                "table_id": td["table_id"],
                "table_title": td["title"],
                "source_runs": td["source_runs"],
                "source_files": td["source_files"],
                "transformations": td["transformations"],
                "row_count": row_cnt,
                "column_count": col_cnt,
                "generated_by": "src.publication.table_factory",
                "generated_at": now_str,
                "csv_hash": hash_file(csv_p) if csv_p.is_file() else "",
                "tex_hash": hash_file(tex_p) if tex_p.is_file() else "",
            }
        )

    save_json(records, output_dir / "provenance" / "table_provenance.json")
    return records


def build_hash_manifest(output_dir: Path, source_hashes: dict[str, str]) -> dict[str, Any]:
    """Generate master SHA-256 hash manifest across source runs and generated artifacts."""
    gen_hashes = hash_directory(output_dir, recursive=True)

    manifest = {
        "timestamp": datetime.now().isoformat(),
        "source_artifacts": source_hashes,
        "generated_artifacts": gen_hashes,
        "total_source_files_hashed": len(source_hashes),
        "total_generated_files_hashed": len(gen_hashes),
    }
    save_json(manifest, output_dir / "provenance" / "hash_manifest.json")
    return manifest
