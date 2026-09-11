"""CLI module execution entry point.

Allows running CLI via:
    python -m src.cli <command> [options]
"""

from src.cli.main import cli

if __name__ == "__main__":
    cli()
