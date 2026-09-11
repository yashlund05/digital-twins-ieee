"""Configuration loading and Pydantic validation schemas.

Provides typed, validated access to all YAML configuration files in the
configs/ directory. Prevents silent misconfigurations or type mismatches
before experiments execute.
"""

from pathlib import Path
from typing import Any, List, Optional
import yaml
from pydantic import BaseModel, Field


# =============================================================================
# Base & Infrastructure Configs
# =============================================================================


class ProjectMetadata(BaseModel):
    """Project metadata."""

    name: str = "dt-power-grid-staleness"
    version: str = "1.0.0"
    description: str = ""


class PathsConfig(BaseModel):
    """Core directory paths."""

    data_root: Path = Path("data/")
    experiment_root: Path = Path("experiments/")
    artifact_root: Path = Path("artifacts/")
    config_root: Path = Path("configs/")


class LoggingSettings(BaseModel):
    """Logging settings."""

    level: str = "INFO"
    format: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    file: Optional[Path] = None


class ReproducibilitySettings(BaseModel):
    """Reproducibility and determinism settings."""

    default_seed: int = 42
    deterministic: bool = True
    log_environment: bool = True


class BaseConfig(BaseModel):
    """Root configuration in configs/base.yaml."""

    project: ProjectMetadata = Field(default_factory=ProjectMetadata)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    reproducibility: ReproducibilitySettings = Field(default_factory=ReproducibilitySettings)


# =============================================================================
# Data Configuration
# =============================================================================


class DateRangeConfig(BaseModel):
    """Date range filter for raw data."""

    start: Optional[str] = None
    end: Optional[str] = None


class PecanStreetConfig(BaseModel):
    """Pecan street source configuration."""

    resolution_minutes: int = 15
    homes: Optional[List[str]] = None
    date_range: DateRangeConfig = Field(default_factory=DateRangeConfig)


class DataSourceConfig(BaseModel):
    """Data source options."""

    pecan_street: PecanStreetConfig = Field(default_factory=PecanStreetConfig)


class NetworkConfig(BaseModel):
    """Grid network topology configuration."""

    topology: str = "ieee_33_bus"
    num_buses: int = 33
    num_load_buses: int = 32


class PreprocessingConfig(BaseModel):
    """Data preprocessing parameters."""

    normalize: bool = True
    normalization_method: str = "min_max"
    fill_missing: str = "forward_fill"
    max_gap_minutes: int = 60


class SplitsConfig(BaseModel):
    """Dataset partition configuration."""

    train_ratio: float = 0.70
    validation_ratio: float = 0.15
    test_ratio: float = 0.15
    temporal: bool = True


class AnomalyInjectionConfig(BaseModel):
    """Synthetic anomaly injection settings."""

    enabled: bool = True
    anomaly_rate: float = 0.05
    seed: int = 42
    fault_types: List[str] = Field(
        default_factory=lambda: ["voltage_sag", "load_spike", "phase_imbalance"]
    )
    duration_timesteps: int = 4


class DataConfig(BaseModel):
    """Root data configuration in configs/data.yaml."""

    source: DataSourceConfig = Field(default_factory=DataSourceConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    splits: SplitsConfig = Field(default_factory=SplitsConfig)
    anomaly_injection: AnomalyInjectionConfig = Field(default_factory=AnomalyInjectionConfig)
    dataset_description: str = ""


# =============================================================================
# Digital Twin Configuration
# =============================================================================


class DTSolverConfig(BaseModel):
    """OpenDSS solver settings."""

    backend: str = "opendssdirect"
    max_iterations: int = 100
    convergence_tolerance: float = 0.0001
    voltage_bases: List[float] = Field(default_factory=lambda: [12.66])


class DTStateConfig(BaseModel):
    """Tracking flags for Digital Twin state."""

    track_voltages: bool = True
    track_currents: bool = True
    track_power_flows: bool = True
    track_losses: bool = True


class DTValidationConfig(BaseModel):
    """Physical validity ranges for the IEEE 33-bus model."""

    voltage_pu_min: float = 0.90
    voltage_pu_max: float = 1.10
    max_power_imbalance_pct: float = 0.5


class DigitalTwinConfig(BaseModel):
    """Root Digital Twin configuration in configs/digital_twin.yaml."""

    feeder: str = "ieee_33_bus"
    topology_file: Optional[Path] = None
    solver: DTSolverConfig = Field(default_factory=DTSolverConfig)
    state: DTStateConfig = Field(default_factory=DTStateConfig)
    validation: DTValidationConfig = Field(default_factory=DTValidationConfig)


# =============================================================================
# Synchronization Configuration
# =============================================================================


class SyncLoggingConfig(BaseModel):
    """Logging settings for synchronization engine."""

    enabled: bool = True
    fields: List[str] = Field(default_factory=list)


class AoIConfig(BaseModel):
    """Age of Information tracking settings."""

    definition: str = "time_since_last_update"
    max_aoi_seconds: Optional[int] = None


class SynchronizationConfig(BaseModel):
    """Root synchronization configuration in configs/synchronization.yaml."""

    interval_seconds: int = 60
    missed_update_policy: str = "hold_last_state"
    logging: SyncLoggingConfig = Field(default_factory=SyncLoggingConfig)
    aoi: AoIConfig = Field(default_factory=AoIConfig)
    sweep_intervals_seconds: List[int] = Field(
        default_factory=lambda: [0, 15, 30, 60, 120, 300, 600, 900, 1800]
    )


# =============================================================================
# Forecasting Configuration
# =============================================================================


class XGBoostConfig(BaseModel):
    """XGBoost model parameters."""

    n_estimators: int = 200
    max_depth: int = 6
    learning_rate: float = 0.05
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    random_state: int = 42
    early_stopping_rounds: int = 20
    eval_metric: str = "rmse"


class LSTMConfig(BaseModel):
    """LSTM model parameters."""

    units: List[int] = Field(default_factory=lambda: [64, 32])
    dropout: float = 0.2
    batch_size: int = 32
    epochs: int = 100
    patience: int = 10
    learning_rate: float = 0.001
    optimizer: str = "adam"
    seed: int = 42


class ForecastMetricsConfig(BaseModel):
    """Forecasting evaluation metrics."""

    primary: List[str] = Field(default_factory=lambda: ["mae", "rmse", "mape"])
    secondary: List[str] = Field(default_factory=lambda: ["r2"])


class ForecastFeaturesConfig(BaseModel):
    """Forecasting feature definitions."""

    temporal: List[str] = Field(default_factory=list)
    lag_features: List[str] = Field(default_factory=list)
    dt_features: List[str] = Field(default_factory=list)


class ForecastingConfig(BaseModel):
    """Root forecasting configuration in configs/forecasting.yaml."""

    models: List[str] = Field(default_factory=lambda: ["persistence", "xgboost", "lstm"])
    horizon_steps: int = 1
    lookback_steps: int = 24
    xgboost: XGBoostConfig = Field(default_factory=XGBoostConfig)
    lstm: LSTMConfig = Field(default_factory=LSTMConfig)
    metrics: ForecastMetricsConfig = Field(default_factory=ForecastMetricsConfig)
    features: ForecastFeaturesConfig = Field(default_factory=ForecastFeaturesConfig)


# =============================================================================
# Anomaly Detection Configuration
# =============================================================================


class IsolationForestConfig(BaseModel):
    """Isolation Forest parameters."""

    n_estimators: int = 100
    max_samples: Any = "auto"
    contamination: float = 0.05
    random_state: int = 42
    n_jobs: int = -1


class LSTMAutoencoderConfig(BaseModel):
    """LSTM Autoencoder parameters."""

    encoder_units: List[int] = Field(default_factory=lambda: [64, 32])
    latent_dim: int = 16
    decoder_units: List[int] = Field(default_factory=lambda: [32, 64])
    lookback_steps: int = 24
    batch_size: int = 32
    epochs: int = 100
    patience: int = 10
    learning_rate: float = 0.001
    seed: int = 42


class ThresholdConfig(BaseModel):
    """Threshold selection settings."""

    method: str = "percentile"
    percentile: float = 95.0


class AnomalyMetricsConfig(BaseModel):
    """Anomaly detection metrics."""

    primary: List[str] = Field(default_factory=lambda: ["precision", "recall", "f1", "pr_auc"])
    secondary: List[str] = Field(default_factory=lambda: ["roc_auc", "false_positive_rate", "detection_latency"])


class AnomalyDetectionConfig(BaseModel):
    """Root anomaly detection configuration in configs/anomaly_detection.yaml."""

    detectors: List[str] = Field(default_factory=lambda: ["isolation_forest", "lstm_autoencoder"])
    input_representations: List[str] = Field(default_factory=lambda: ["raw", "residual"])
    unsupervised: bool = True
    isolation_forest: IsolationForestConfig = Field(default_factory=IsolationForestConfig)
    lstm_autoencoder: LSTMAutoencoderConfig = Field(default_factory=LSTMAutoencoderConfig)
    threshold: ThresholdConfig = Field(default_factory=ThresholdConfig)
    metrics: AnomalyMetricsConfig = Field(default_factory=AnomalyMetricsConfig)


# =============================================================================
# Experiment Configuration
# =============================================================================


class ExperimentMetadata(BaseModel):
    """Experiment run metadata."""

    id: str
    name: str
    description: str = ""
    seed: int = 42
    version: str = "1.0.0"


class ExperimentConfig(BaseModel):
    """Complete experiment execution configuration."""

    experiment: ExperimentMetadata
    base: Optional[BaseConfig] = None
    data: Optional[DataConfig] = None
    digital_twin: Optional[DigitalTwinConfig] = None
    synchronization: Optional[SynchronizationConfig] = None
    forecasting: Optional[ForecastingConfig] = None
    anomaly_detection: Optional[AnomalyDetectionConfig] = None


# =============================================================================
# Helper Loaders
# =============================================================================


def load_yaml(file_path: Path | str) -> dict[str, Any]:
    """Safely load and parse a YAML file into a dictionary.

    Parameters
    ----------
    file_path : Path | str
        Path to the YAML file.

    Returns
    -------
    dict[str, Any]
        Parsed YAML content.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        raise ValueError(f"Configuration file is empty: {path}")
    if not isinstance(data, dict):
        raise ValueError(f"Configuration root must be a mapping, got {type(data)} in {path}")
    return data


def load_base_config(file_path: Path | str = "configs/base.yaml") -> BaseConfig:
    """Load and validate base.yaml."""
    return BaseConfig(**load_yaml(file_path))


def load_data_config(file_path: Path | str = "configs/data.yaml") -> DataConfig:
    """Load and validate data.yaml."""
    raw = load_yaml(file_path)
    data_dict = raw.get("data", raw)
    return DataConfig(**data_dict)


def load_digital_twin_config(file_path: Path | str = "configs/digital_twin.yaml") -> DigitalTwinConfig:
    """Load and validate digital_twin.yaml."""
    raw = load_yaml(file_path)
    dt_dict = raw.get("digital_twin", raw)
    return DigitalTwinConfig(**dt_dict)


def load_synchronization_config(
    file_path: Path | str = "configs/synchronization.yaml",
) -> SynchronizationConfig:
    """Load and validate synchronization.yaml."""
    raw = load_yaml(file_path)
    sync_dict = raw.get("synchronization", raw)
    return SynchronizationConfig(**sync_dict)


def load_forecasting_config(file_path: Path | str = "configs/forecasting.yaml") -> ForecastingConfig:
    """Load and validate forecasting.yaml."""
    raw = load_yaml(file_path)
    forecast_dict = raw.get("forecasting", raw)
    return ForecastingConfig(**forecast_dict)


def load_anomaly_detection_config(
    file_path: Path | str = "configs/anomaly_detection.yaml",
) -> AnomalyDetectionConfig:
    """Load and validate anomaly_detection.yaml."""
    raw = load_yaml(file_path)
    anomaly_dict = raw.get("anomaly_detection", raw)
    return AnomalyDetectionConfig(**anomaly_dict)
