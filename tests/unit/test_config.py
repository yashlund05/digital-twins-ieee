"""Unit tests for configuration loaders and Pydantic schemas in src/utils/config.py."""

from pathlib import Path
import pytest
from src.utils.config import (
    BaseConfig,
    DataConfig,
    DigitalTwinConfig,
    ForecastingConfig,
    SynchronizationConfig,
    load_anomaly_detection_config,
    load_base_config,
    load_data_config,
    load_digital_twin_config,
    load_forecasting_config,
    load_synchronization_config,
    load_yaml,
)


@pytest.mark.unit
def test_load_base_config() -> None:
    """Validate configs/base.yaml parses into BaseConfig schema."""
    config = load_base_config("configs/base.yaml")
    assert isinstance(config, BaseConfig)
    assert config.project.name == "dt-power-grid-staleness"
    assert config.reproducibility.default_seed == 42


@pytest.mark.unit
def test_load_data_config() -> None:
    """Validate configs/data.yaml parses into DataConfig schema."""
    config = load_data_config("configs/data.yaml")
    assert isinstance(config, DataConfig)
    assert config.network.topology == "ieee_33_bus"
    assert config.network.num_buses == 33
    assert config.splits.train_ratio == 0.70
    assert config.splits.temporal is True


@pytest.mark.unit
def test_load_digital_twin_config() -> None:
    """Validate configs/digital_twin.yaml parses into DigitalTwinConfig schema."""
    config = load_digital_twin_config("configs/digital_twin.yaml")
    assert isinstance(config, DigitalTwinConfig)
    assert config.feeder == "ieee_33_bus"
    assert config.solver.backend == "opendssdirect"
    assert config.validation.voltage_pu_min == 0.90


@pytest.mark.unit
def test_load_synchronization_config() -> None:
    """Validate configs/synchronization.yaml parses into SynchronizationConfig schema."""
    config = load_synchronization_config("configs/synchronization.yaml")
    assert isinstance(config, SynchronizationConfig)
    assert config.interval_seconds == 60
    assert config.missed_update_policy == "hold_last_state"
    assert 0 in config.sweep_intervals_seconds
    assert 1800 in config.sweep_intervals_seconds


@pytest.mark.unit
def test_load_forecasting_config() -> None:
    """Validate configs/forecasting.yaml parses into ForecastingConfig schema."""
    config = load_forecasting_config("configs/forecasting.yaml")
    assert isinstance(config, ForecastingConfig)
    assert "persistence" in config.models
    assert "xgboost" in config.models
    assert "lstm" in config.models
    assert config.lookback_steps == 24


@pytest.mark.unit
def test_load_anomaly_detection_config() -> None:
    """Validate configs/anomaly_detection.yaml parses into AnomalyDetectionConfig schema."""
    config = load_anomaly_detection_config("configs/anomaly_detection.yaml")
    assert config.unsupervised is True
    assert "isolation_forest" in config.detectors
    assert "lstm_autoencoder" in config.detectors
    assert "raw" in config.input_representations
    assert "residual" in config.input_representations


@pytest.mark.unit
def test_load_yaml_nonexistent_file(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised for non-existent config path."""
    with pytest.raises(FileNotFoundError):
        load_yaml(tmp_path / "does_not_exist.yaml")
