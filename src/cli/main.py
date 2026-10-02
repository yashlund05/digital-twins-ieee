"""
main.py — CLI entry point

Usage:
    python -m src.cli <command> [options]
    dt-grid <command> [options]
"""

from pathlib import Path
import click


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Digital Twin Power Grid Research CLI.

    Provides commands for running experiments, validating the Digital Twin,
    and generating paper-ready artifacts.

    Status: Research infrastructure initialization (Phase 0).
    Commands are scaffolded as placeholders pending Phase 1+ implementation.
    """
    pass


@cli.command()
@click.option(
    "--config", default="configs/digital_twin.yaml", help="Path to digital twin config YAML"
)
@click.option("--seed", default=42, type=int, help="Random seed for experiment")
def validate_dt(config: str, seed: int) -> None:
    """Validate the IEEE 33-bus Digital Twin via OpenDSS power flow.

    Runs Experiment E1: Digital Twin Baseline Validation.
    Checks physical constraint satisfaction and power flow correctness.
    """
    from src.digital_twin.initializer import run_experiment_e1_validation

    click.echo(
        f"Running Experiment E1: Digital Twin Baseline Validation (config={config}, seed={seed})..."
    )
    result = run_experiment_e1_validation(config_path=config, seed=seed)

    if result["all_passed"]:
        click.echo("[SUCCESS] Experiment E1 Validation PASSED.")
    else:
        click.echo("[WARNING] Experiment E1 Validation finished with warnings/failures.")

    metrics = result["stats"]["nominal_metrics"]
    click.echo(f"  Run ID           : {result['run_id']}")
    click.echo(
        f"  Min Voltage      : {metrics['min_voltage_pu']:.4f} pu (Bus {metrics['min_voltage_bus']})"
    )
    click.echo(f"  Max Voltage      : {metrics['max_voltage_pu']:.4f} pu")
    click.echo(f"  Total P Gen      : {metrics['total_gen_p_kw']:.2f} kW")
    click.echo(f"  Total P Load     : {metrics['total_load_p_kw']:.2f} kW")
    click.echo(
        f"  Total P Losses   : {metrics['total_loss_p_kw']:.2f} kW ({metrics['loss_percentage']:.2f}%)"
    )
    click.echo(f"  Power Balance Err: {metrics['power_balance_error_pct']:.6f}%")
    click.echo(f"  Outputs saved to : {result['run_dir']}")


@cli.command()
@click.option("--config", default="configs/data.yaml", help="Path to data configuration YAML")
@click.option("--raw-data", default=None, help="Path to raw Pecan Street CSV (optional override)")
@click.option("--seed", default=None, type=int, help="Random seed (overrides config)")
def prepare_data(config: str, raw_data: str | None, seed: int | None) -> None:
    """Run the data preparation pipeline.

    Processes raw Pecan Street data and maps it to the IEEE 33-bus topology.
    Injects synthetic anomalies per the configured protocol.
    Produces train/validation/test splits with temporal leakage prevention.
    """
    from src.data.pipeline import run_pipeline

    click.echo(f"Starting data preparation pipeline (config={config})...")
    result = run_pipeline(config_path=config, raw_data_path=raw_data, seed_override=seed)
    click.echo("[SUCCESS] Data pipeline execution complete.")
    click.echo(f"  Total timesteps : {result['manifest']['total_timesteps']}")
    click.echo(
        f"  Anomalies       : {result['manifest']['num_anomalies_injected']} ({result['manifest']['anomaly_rate'] * 100:.2f}%)"
    )
    click.echo(
        f"  Train split     : {result['manifest']['split_counts']['train']} steps ({result['splits']['train']['start']} to {result['splits']['train']['end']})"
    )
    click.echo(
        f"  Val split       : {result['manifest']['split_counts']['validation']} steps ({result['splits']['validation']['start']} to {result['splits']['validation']['end']})"
    )
    click.echo(
        f"  Test split      : {result['manifest']['split_counts']['test']} steps ({result['splits']['test']['start']} to {result['splits']['test']['end']})"
    )
    click.echo("  Processed files saved to data/processed/ and data/interim/")


@cli.command()
@click.option("--config", required=True, help="Path to experiment configuration YAML")
@click.option("--seed", default=None, type=int, help="Random seed (overrides config)")
def run_experiment(config: str, seed: int | None) -> None:
    """Run an experiment from a configuration file.

    Produces a unique run_id and stores all outputs in experiments/runs/<run_id>/.
    Writes manifest.json, metrics.json, config.yaml, and logs.
    """
    click.echo(f"[PLACEHOLDER] run-experiment (config={config}) — implement in Phase 8")
    click.echo("See: docs/experiments/EXPERIMENTS.md")
    raise click.ClickException("Not yet implemented (Phase 8)")


@cli.command()
@click.option("--config", default="configs/forecasting.yaml", help="Forecasting config")
@click.option("--seed", default=42, type=int, help="Random seed")
def train_forecast(config: str, seed: int) -> None:
    """Train load estimation models (Persistence, XGBoost, LSTM).

    Runs Experiment E2: Load Estimation Baselines.
    """
    from src.forecasting.experiment_e2 import run_experiment_e2

    click.echo(f"Starting Experiment E2: Load Estimation Baselines (seed={seed})...")
    run_dir = run_experiment_e2(seed=seed)
    click.echo(f"[SUCCESS] Experiment E2 complete. Results and models saved to {run_dir}")


@cli.command()
@click.option("--config", default="configs/anomaly_detection.yaml", help="Anomaly config")
@click.option("--seed", default=42, type=int, help="Random seed")
@click.option(
    "--input",
    "input_rep",
    default="raw",
    type=click.Choice(["raw", "residual"]),
    help="Input representation",
)
def train_anomaly(config: str, seed: int, input_rep: str) -> None:
    """Train anomaly detection models (Isolation Forest, LSTM Autoencoder).

    Runs Experiment E3: Anomaly Detection Baselines.
    """
    from src.anomaly_detection.experiment_e3 import run_experiment_e3

    click.echo(
        f"Starting Experiment E3: Anomaly Detection Baselines (seed={seed}, input={input_rep})..."
    )
    run_dir = run_experiment_e3(seed=seed, input_representation=input_rep)
    click.echo(f"[SUCCESS] Experiment E3 complete. Results and models saved to {run_dir}")


@cli.command()
@click.option("--config", default="configs/anomaly_detection.yaml", help="Anomaly config YAML")
@click.option("--seed", default=42, type=int, help="Random seed for experiment")
@click.option(
    "--norm",
    default="z_score",
    type=click.Choice(["z_score", "min_max", "robust"]),
    help="Residual normalization method",
)
def run_e4(config: str, seed: int, norm: str) -> None:
    """Run Experiment E4: Raw vs. Residual Inputs (2x2 Factorial Baseline).

    Compares Isolation Forest and LSTM Autoencoder on Raw vs. Residual representations
    under ideal baseline synchronization (Delta t_sync = 0).
    """
    from src.residuals.experiment_e4 import run_experiment_e4

    click.echo(
        f"Starting Experiment E4: Raw vs. Residual Inputs (seed={seed}, norm={norm}, config={config})..."
    )
    run_dir = run_experiment_e4(seed=seed, normalization_method=norm)
    click.echo(f"[SUCCESS] Experiment E4 complete. All artifacts saved to: {run_dir}")


@cli.command()
@click.option(
    "--config",
    default="configs/experiments/e5_staleness_sweep.yaml",
    help="Path to E5 experiment YAML configuration",
)
@click.option("--seed", default=42, type=int, help="Random seed for reproducibility")
@click.option("--baseline-only", is_flag=True, help="Execute only baseline condition (Delta t = 0, Pdrop = 0)")
@click.option("--run-id", default=None, help="Custom run directory identifier")
def run_e5(config: str, seed: int, baseline_only: bool, run_id: str | None) -> None:
    """Run Experiment E5: Controlled Synchronization Staleness Sweep.

    Sweeps synchronization staleness intervals Delta t in {0, 1, 5, 15, 60, 300} s
    and packet drop rates in {0.0, 0.05, 0.10, 0.20} across load estimation
    and unsupervised anomaly detection.
    """
    from src.experiments.staleness_sweep import run_staleness_sweep

    click.echo(
        f"Starting Experiment E5: Controlled Synchronization Staleness Sweep (seed={seed}, config={config}, baseline_only={baseline_only})..."
    )
    run_dir = run_staleness_sweep(
        config_path=config,
        seed=seed,
        baseline_only=baseline_only,
        run_id=run_id,
    )
    click.echo(f"[SUCCESS] Experiment E5 complete. All artifacts saved to: {run_dir}")


@cli.command()
@click.option("--seed", default=42, type=int, help="Random seed for reproducibility")
@click.option(
    "--input",
    "input_e5_dir",
    default="experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930",
    help="Path to validated E5 run directory",
)
@click.option("--bootstrap-iterations", default=1000, type=int, help="Number of bootstrap iterations")
@click.option("--confidence-level", default=0.95, type=float, help="Confidence level for CIs")
def run_e6(seed: int, input_e5_dir: str, bootstrap_iterations: int, confidence_level: float) -> None:
    """Run Experiment E6: Joint Statistical Analysis and Hypothesis Testing (Phase 9).

    Conducts degradation regressions, effect size calculations, non-parametric
    paired tests, Benjamini-Hochberg FDR adjustments, and pre-specified H3 testing.
    """
    from src.statistics.analysis_runner import run_phase9_analysis

    click.echo(
        f"Starting Experiment E6: Joint Analysis & Hypothesis Testing (seed={seed}, input={input_e5_dir})..."
    )
    run_dir = run_phase9_analysis(
        input_e5_dir=input_e5_dir,
        seed=seed,
        n_boot=bootstrap_iterations,
        ci_level=confidence_level,
    )
    click.echo(f"[SUCCESS] Experiment E6 complete. All artifacts and figures saved to: {run_dir}")


@cli.command()
@click.option("--run-id", required=True, help="Experiment run ID or directory to evaluate")
def evaluate(run_id: str) -> None:
    """Evaluate the results of a completed experiment run."""
    from src.statistics.analysis_runner import run_phase9_analysis

    input_dir = Path("experiments/runs") / run_id if not Path(run_id).exists() else Path(run_id)
    click.echo(f"Evaluating experiment run: {input_dir}...")
    out_dir = run_phase9_analysis(input_e5_dir=input_dir)
    click.echo(f"[SUCCESS] Evaluation complete. Results saved to: {out_dir}")


@cli.command()
@click.option("--run-id", required=True, help="Experiment run ID")
def generate_figures(run_id: str) -> None:
    """Generate paper-ready figures from experiment results.

    See: docs/paper/FIGURE_TABLE_STANDARD.md for naming conventions.
    """
    click.echo(f"[PLACEHOLDER] generate-figures (run_id={run_id}) — implement in Phase 12")
    raise click.ClickException("Not yet implemented (Phase 12)")


@cli.command()
@click.option("--seed", default=None, type=int, help="Execute/analyze a specific seed")
@click.option("--all-seeds", is_flag=True, help="Execute/analyze all frozen seeds in Phase 10")
@click.option(
    "--config",
    default="configs/experiments/e10_multiseed.yaml",
    help="Path to Phase 10 configuration YAML",
)
@click.option("--bootstrap-iterations", default=2000, type=int, help="Bootstrap resampling iterations")
@click.option("--confidence-level", default=0.95, type=float, help="Confidence level for intervals")
def run_e10(
    seed: int | None,
    all_seeds: bool,
    config: str,
    bootstrap_iterations: int,
    confidence_level: float,
) -> None:
    """Run Phase 10: Multi-Seed Uncertainty Quantification and Analysis (Experiment E10)."""
    from datetime import datetime
    from src.experiments.staleness_sweep import run_staleness_sweep
    from src.statistics.multiseed import run_multiseed_analysis
    from src.utils.config import load_e10_config

    cfg = load_e10_config(config)
    runs_dir = Path("experiments/runs")

    if not all_seeds and seed is None:
        raise click.UsageError("Must specify either --seed <int> or --all-seeds")

    target_seeds = cfg.seeds if all_seeds else [seed]
    click.echo(f"Starting Experiment E10 (seeds={target_seeds}, config={config})...")

    # Locate or execute E5 runs for required seeds
    seed_dirs: dict[int, Path] = {}

    for s in target_seeds:
        # Search for existing corrected E5 run
        cand_dirs = list(runs_dir.glob(f"E5_STALENESS_SWEEP_CORRECTED_SEED{s}_*"))
        if not cand_dirs and s == 42:
            cand_dirs = [runs_dir / "E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930"]

        if cand_dirs and (cand_dirs[0] / "comparison.csv").exists():
            s_dir = cand_dirs[0]
            click.echo(f"Found existing E5 run for seed {s}: {s_dir}")
            seed_dirs[s] = s_dir
        else:
            click.echo(f"Executing E5 staleness sweep for seed {s}...")
            date_str = datetime.now().strftime("%Y%m%d")
            s_run_id = f"E5_STALENESS_SWEEP_CORRECTED_SEED{s}_{date_str}"
            try:
                s_dir = run_staleness_sweep(
                    config_path="configs/experiments/e5_staleness_sweep.yaml",
                    seed=s,
                    run_id=s_run_id,
                )
                seed_dirs[s] = s_dir
                click.echo(f"[SUCCESS] Completed E5 sweep for seed {s} -> {s_dir}")
            except Exception as e:
                click.echo(f"[ERROR] Failed execution for seed {s}: {e}", err=True)
                raise click.ClickException(f"Seed {s} execution failed: {e}")

    if all_seeds:
        click.echo("All 5 seeds available. Executing Phase 10 multi-seed aggregation...")
        out_dir = run_multiseed_analysis(
            seed_dirs=seed_dirs,
            config_path=config,
            n_boot=bootstrap_iterations,
            ci_level=confidence_level,
        )
        click.echo(f"[SUCCESS] Phase 10 Multi-Seed Analysis complete! Outputs saved to: {out_dir}")


@cli.command()
@click.option(
    "--config",
    default="configs/experiments/e10_multiseed.yaml",
    help="Path to Phase 10 configuration YAML",
)
@click.option("--bootstrap-iterations", default=2000, type=int, help="Bootstrap resampling iterations")
@click.option("--confidence-level", default=0.95, type=float, help="Confidence level for intervals")
def analyze_multiseed(config: str, bootstrap_iterations: int, confidence_level: float) -> None:
    """Analyze completed multi-seed E5 runs and generate Phase 10 deliverables."""
    from src.statistics.multiseed import run_multiseed_analysis
    from src.utils.config import load_e10_config

    cfg = load_e10_config(config)
    runs_dir = Path("experiments/runs")
    seed_dirs: dict[int, Path] = {}

    for s in cfg.seeds:
        cand_dirs = list(runs_dir.glob(f"E5_STALENESS_SWEEP_CORRECTED_SEED{s}_*"))
        if not cand_dirs and s == 42:
            cand_dirs = [runs_dir / "E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930"]

        if cand_dirs and (cand_dirs[0] / "comparison.csv").exists():
            seed_dirs[s] = cand_dirs[0]
        else:
            raise click.ClickException(f"Missing completed E5 run for seed {s} in {runs_dir}")

    out_dir = run_multiseed_analysis(
        seed_dirs=seed_dirs,
        config_path=config,
        n_boot=bootstrap_iterations,
        ci_level=confidence_level,
    )
    click.echo(f"[SUCCESS] Phase 10 Multi-Seed Analysis complete! Outputs saved to: {out_dir}")


@cli.command()
@click.option(
    "--config",
    default="configs/experiments/e11_phase11.yaml",
    help="Path to Phase 11 configuration YAML",
)
@click.option(
    "--reproducibility-only",
    is_flag=True,
    default=False,
    help="Execute only Objective A reproducibility verification",
)
@click.option(
    "--ablations-only",
    is_flag=True,
    default=False,
    help="Execute only Objective B controlled ablations",
)
@click.option(
    "--transient-only",
    is_flag=True,
    default=False,
    help="Execute only Objective C missed-update transient analysis",
)
def run_e11(
    config: str,
    reproducibility_only: bool,
    ablations_only: bool,
    transient_only: bool,
) -> None:
    """Run Experiment E11: Phase 11 Master Reproducibility, Ablations, and Transient Dynamics."""
    from src.experiments.phase11_runner import run_phase11_experiment

    click.echo(f"Starting Phase 11 execution (config={config})...")
    out_dir = run_phase11_experiment(
        config_path=config,
        reproducibility_only=reproducibility_only,
        ablations_only=ablations_only,
        transient_only=transient_only,
    )
    click.echo(f"[SUCCESS] Phase 11 complete! Artifacts saved to: {out_dir}")


@cli.command()
@click.option(
    "--config",
    default="configs/experiments/e11_phase11.yaml",
    help="Path to Phase 11 configuration YAML",
)
@click.option(
    "--output-dir",
    default=None,
    help="Output directory for reproducibility audit report",
)
def verify_reproducibility(config: str, output_dir: str | None) -> None:
    """Verify historical benchmarks (Phase 7 E4, Phase 8 E5, Phase 9 E6, Phase 10 E10)."""
    from datetime import datetime
    import yaml
    from src.reproducibility.verifier import verify_historical_benchmarks

    with open(config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if output_dir is None:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = Path("experiments/runs") / f"VERIFY_REPRODUCIBILITY_{date_str}"
    else:
        out = Path(output_dir)

    benchmarks = cfg.get("reproducibility", {}).get("benchmarks", {})
    report = verify_historical_benchmarks(
        output_dir=out,
        phase7_e4_dir=benchmarks.get("phase7_e4", "experiments/runs/E4_RAW_VS_RESIDUAL_SEED42_20260930"),
        phase8_e5_dir=benchmarks.get("phase8_e5", "experiments/runs/E5_STALENESS_SWEEP_CORRECTED_SEED42_20260930"),
        phase9_e6_dir=benchmarks.get("phase9_e6", "experiments/runs/E6_JOINT_ANALYSIS_SEED42_20261002"),
        phase10_e10_dir=benchmarks.get("phase10_e10", "experiments/runs/E10_MULTI_SEED_ANALYSIS_20261002"),
    )
    click.echo(f"Verification Overall Status: {report['overall_status']}")
    click.echo(f"  Phase 7 E4 Baseline : {report['phase7_e4_status']}")
    click.echo(f"  Phase 8 E5 Sweep    : {report['phase8_e5_status']}")
    click.echo(f"  Phase 9 E6 Analysis : {report['phase9_e6_status']}")
    click.echo(f"  Phase 10 E10 Robust : {report['phase10_e10_status']}")
    click.echo(f"Audit report saved to: {out}")


@cli.command()
@click.option(
    "--run-dir",
    required=True,
    help="Path to run directory to audit",
)
def verify_artifacts_cli(run_dir: str) -> None:
    """Audit artifact integrity, cryptographic non-emptiness, and condition count."""
    from src.reproducibility.artifact_integrity import verify_artifacts

    r_path = Path(run_dir)
    res = verify_artifacts(r_path)
    click.echo(f"Artifact Integrity Status: {res['status']}")
    click.echo(f"  Files checked  : {res['total_files_checked']}")
    click.echo(f"  Missing files  : {len(res['missing_files'])}")
    click.echo(f"  Corrupted files: {len(res['corrupted_files'])}")


@cli.command()
@click.option(
    "--config",
    default="configs/publication/phase12_sources.yaml",
    help="Path to Phase 12 publication sources YAML",
)
@click.option(
    "--output-dir",
    default=None,
    help="Optional output directory override",
)
@click.option(
    "--verify-only",
    is_flag=True,
    default=False,
    help="Verify source integrity and completeness without writing artifacts",
)
@click.option(
    "--figures-only",
    is_flag=True,
    default=False,
    help="Generate only publication figures and source CSVs",
)
@click.option(
    "--tables-only",
    is_flag=True,
    default=False,
    help="Generate only publication tables (CSV and LaTeX)",
)
@click.option(
    "--latex-only",
    is_flag=True,
    default=False,
    help="Generate only LaTeX document fragments",
)
@click.option(
    "--strict/--no-strict",
    default=True,
    help="Enforce strict validation failure on source discrepancy",
)
def build_publication_artifacts(
    config: str,
    output_dir: str | None,
    verify_only: bool,
    figures_only: bool,
    tables_only: bool,
    latex_only: bool,
    strict: bool,
) -> None:
    """Build Phase 12 IEEE publication-ready figures, tables, LaTeX, and provenance."""
    from src.publication.publication_runner import run_phase12_publication_pipeline

    click.echo(f"Executing Phase 12 Publication Artifact Pipeline (config={config})...")
    res_dir = run_phase12_publication_pipeline(
        config_path=config,
        output_dir_override=output_dir,
        verify_only=verify_only,
        figures_only=figures_only,
        tables_only=tables_only,
        latex_only=latex_only,
        strict=strict,
    )
    if verify_only:
        click.echo("[SUCCESS] Publication source validation PASSED.")
    else:
        click.echo(f"[SUCCESS] Phase 12 publication artifacts successfully built: {res_dir}")


@cli.command()
@click.option(
    "--config",
    default="configs/publication/phase13_publication.yaml",
    help="Path to Phase 13 publication configuration YAML",
)
@click.option(
    "--output-dir",
    default=None,
    help="Optional output directory override",
)
@click.option(
    "--verify-only",
    is_flag=True,
    default=False,
    help="Run all audits without writing manuscript files",
)
@click.option(
    "--strict/--no-strict",
    default=True,
    help="Enforce strict validation failure on audit discrepancies",
)
def assemble_manuscript(
    config: str,
    output_dir: str | None,
    verify_only: bool,
    strict: bool,
) -> None:
    """Assemble IEEE TSG manuscript and run Phase 13 scientific audits."""
    from src.publication.submission_runner import run_phase13_submission_pipeline

    click.echo(f"Executing Phase 13 Manuscript Assembly & Audit Pipeline (config={config})...")
    res_dir = run_phase13_submission_pipeline(
        config_path=config,
        output_dir_override=output_dir,
        verify_only=verify_only,
        strict=strict,
    )
    if verify_only:
        click.echo("[SUCCESS] All Phase 13 scientific audits PASSED.")
    else:
        click.echo(f"[SUCCESS] Phase 13 manuscript package successfully assembled: {res_dir}")


if __name__ == "__main__":
    cli()



