"""Unit tests for logging utilities in src/utils/logging.py."""

import json
import logging
from pathlib import Path
import pytest
from src.utils.logging import get_logger, setup_logging


@pytest.mark.unit
def test_setup_logging_console() -> None:
    """Verify logger setup with standard console output."""
    setup_logging(level="DEBUG")
    logger = get_logger("test_module")
    assert logger.getEffectiveLevel() == logging.DEBUG


@pytest.mark.unit
def test_setup_logging_file(tmp_path: Path) -> None:
    """Verify logger writes structured log records to target file."""
    log_file = tmp_path / "test_run.log"
    setup_logging(level="INFO", log_file=log_file, use_json=True)
    logger = get_logger("test_json")

    logger.info("Synchronization event completed", extra={"interval": 60, "age": 12.5})

    assert log_file.is_file()
    with open(log_file, encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) >= 1
    data = json.loads(lines[0])
    assert data["message"] == "Synchronization event completed"
    assert data["level"] == "INFO"
    assert data["context"]["interval"] == 60
    assert data["context"]["age"] == 12.5
