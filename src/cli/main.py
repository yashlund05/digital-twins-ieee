"""
main.py — CLI entry point

Usage:
    python -m src.cli <command> [options]
    dt-grid <command> [options]
"""

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
def run_e5(config: str, seed: int) -> None:
    """Run Experiment E5: Controlled Synchronization Staleness Sweep.

    Sweeps synchronization staleness intervals Delta t in {0, 1, 5, 15, 60, 300} s
    and packet drop rates in {0.0, 0.05, 0.10, 0.20} across load estimation
    and unsupervised anomaly detection.
    """
    from src.experiments.staleness_sweep import run_staleness_sweep

    click.echo(
        f"Starting Experiment E5: Controlled Synchronization Staleness Sweep (seed={seed}, config={config})..."
    )
    run_dir = run_staleness_sweep(config_path=config, seed=seed)
    click.echo(f"[SUCCESS] Experiment E5 complete. All artifacts saved to: {run_dir}")


@cli.command()
@click.option("--run-id", required=True, help="Experiment run ID to evaluate")
def evaluate(run_id: str) -> None:
    """Evaluate the results of a completed experiment run."""
    click.echo(f"[PLACEHOLDER] evaluate (run_id={run_id}) — implement in Phase 9")
    raise click.ClickException("Not yet implemented (Phase 9)")


@cli.command()
@click.option("--run-id", required=True, help="Experiment run ID")
def generate_figures(run_id: str) -> None:
    """Generate paper-ready figures from experiment results.

    See: docs/paper/FIGURE_TABLE_STANDARD.md for naming conventions.
    """
    click.echo(f"[PLACEHOLDER] generate-figures (run_id={run_id}) — implement in Phase 12")
    raise click.ClickException("Not yet implemented (Phase 12)")


if __name__ == "__main__":
    cli()
