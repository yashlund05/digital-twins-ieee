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
def validate_dt() -> None:
    """Validate the IEEE 33-bus Digital Twin via OpenDSS power flow.

    Runs Experiment E1: Digital Twin Baseline Validation.
    Checks physical constraint satisfaction and power flow correctness.
    """
    click.echo("[PLACEHOLDER] validate-dt command — implement in Phase 3")
    click.echo("See: docs/experiments/EXPERIMENTS.md (E1)")
    raise click.ClickException("Not yet implemented (Phase 3)")


@cli.command()
@click.option("--stage", default="all", help="Pipeline stage: all, interim, processed")
def prepare_data(stage: str) -> None:
    """Run the data preparation pipeline.

    Processes raw Pecan Street data and maps it to the IEEE 33-bus topology.
    Injects synthetic anomalies per the configured protocol.
    Produces train/validation/test splits with temporal leakage prevention.
    """
    click.echo(f"[PLACEHOLDER] prepare-data (stage={stage}) — implement in Phase 2")
    click.echo("See: docs/methodology/DATA_PROTOCOL.md")
    raise click.ClickException("Not yet implemented (Phase 2)")


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
