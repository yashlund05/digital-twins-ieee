"""Structured logging utilities for experiments and system modules.

Provides consistent, structured log output across CLI runs, background
workers, and experiment orchestration. Supports contextual metadata injection.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Structured formatter that outputs standard log format or JSON."""

    def __init__(self, use_json: bool = False) -> None:
        super().__init__()
        self.use_json = use_json

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with structured attributes."""
        timestamp = datetime.fromtimestamp(record.created).isoformat()

        # Extract custom extra attributes
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord("", 0, "", 0, "", (), None).__dict__
            and not k.startswith("_")
        }

        if self.use_json:
            payload: dict[str, Any] = {
                "timestamp": timestamp,
                "logger": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
            }
            if extras:
                payload["context"] = extras
            if record.exc_info:
                payload["exception"] = self.formatException(record.exc_info)
            return json.dumps(payload)

        # Standard console format
        msg = f"{timestamp} | {record.name} | {record.levelname} | {record.getMessage()}"
        if extras:
            context_str = " ".join(f"[{k}={v}]" for k, v in extras.items())
            msg = f"{msg} {context_str}"
        if record.exc_info:
            msg = f"{msg}\n{self.formatException(record.exc_info)}"
        return msg


def setup_logging(
    level: str = "INFO",
    log_file: Path | str | None = None,
    use_json: bool = False,
) -> None:
    """Initialize root logger with console and optional file handler.

    Parameters
    ----------
    level : str
        Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    log_file : Optional[Path | str]
        Path to output log file, if file logging is desired.
    use_json : bool
        If True, format logs as JSON lines.
    """
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    formatter = StructuredFormatter(use_json=use_json)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if requested
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Obtain a namespaced logger instance.

    Parameters
    ----------
    name : str
        Module name, typically `__name__`.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    return logging.getLogger(name)
