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
    click.echo("[PLACEHOLDER] train-forecast — implement in Phase 5")
    raise click.ClickException("Not yet implemented (Phase 5)")


@cli.command()
@click.option("--config", default="configs/anomaly_detection.yaml", help="Anomaly config")
@click.option("--seed", default=42, type=int, help="Random seed")
def train_anomaly(config: str, seed: int) -> None:
    """Train anomaly detection models (Isolation Forest, LSTM Autoencoder).

    Runs Experiment E3: Anomaly Detection Baselines.
    """
    click.echo("[PLACEHOLDER] train-anomaly — implement in Phase 6")
    raise click.ClickException("Not yet implemented (Phase 6)")


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
