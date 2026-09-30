"""
tests/unit/test_residual_calculator.py — Unit tests for the Digital Twin residual calculator.
"""

import numpy as np
import pandas as pd
import pytest

from src.digital_twin.state import DigitalTwinState
from src.residuals.calculator import (
    ResidualResult,
    StateResidualResult,
    calculate_residual,
    calculate_state_residual,
)


@pytest.fixture
def sample_dt_state():
    """Create a minimal valid DigitalTwinState for testing."""
    voltages_pu = {b: 1.0 for b in range(1, 34)}
    voltages_kv = {b: 12.66 for b in range(1, 34)}
    angles_deg = {b: 0.0 for b in range(1, 34)}
    currents_a = {f"L{i}": 10.0 for i in range(1, 33)}

    return DigitalTwinState(
        timestamp="2018-01-01T00:00:00Z",
        converged=True,
        iterations=2,
        bus_voltages_pu=voltages_pu,
        bus_voltages_kv=voltages_kv,
        bus_voltage_angles_deg=angles_deg,
        branch_currents_a=currents_a,
        total_generation_p_kw=3715.0,
        total_generation_q_kvar=2300.0,
        total_load_p_kw=3500.0,
        total_load_q_kvar=2200.0,
        total_losses_p_kw=215.0,
        total_losses_q_kvar=100.0,
        power_balance_error_kw=0.0,
        power_balance_error_pct=0.0,
        min_voltage_pu=0.95,
        min_voltage_bus=18,
        max_voltage_pu=1.0,
        max_voltage_bus=1,
    )


def test_zero_residual():
    """Identical observed and DT estimates must produce exact zero residual."""
    obs = np.array([[100.0, 200.0], [300.0, 400.0]], dtype=np.float64)
    est = np.array([[100.0, 200.0], [300.0, 400.0]], dtype=np.float64)

    result = calculate_residual(obs, est)
    assert isinstance(result, ResidualResult)
    np.testing.assert_allclose(result.values, 0.0, atol=1e-12)
    assert result.metadata["is_exact_zero"] is True


def test_positive_and_negative_residuals():
    """Calculate exact positive and negative residual differences."""
    obs = np.array([150.0, 50.0])
    est = np.array([100.0, 100.0])

    result = calculate_residual(obs, est)
    expected = np.array([50.0, -50.0])
    np.testing.assert_allclose(result.values, expected)
    assert result.metadata["max_abs_residual"] == 50.0


def test_dataframe_preservation():
    """Residual calculation on DataFrame preserves columns, index, and types."""
    index = pd.date_range("2018-01-01", periods=3, freq="15min")
    obs_df = pd.DataFrame(
        {"bus_2_p_kw": [10.0, 20.0, 30.0], "bus_3_p_kw": [5.0, 15.0, 25.0]}, index=index
    )
    est_df = pd.DataFrame(
        {"bus_2_p_kw": [8.0, 18.0, 28.0], "bus_3_p_kw": [5.0, 10.0, 20.0]}, index=index
    )

    result = calculate_residual(obs_df, est_df)
    assert isinstance(result.raw_residual, pd.DataFrame)
    assert list(result.raw_residual.columns) == ["bus_2_p_kw", "bus_3_p_kw"]
    assert result.raw_residual.index.equals(index)

    expected_diff = np.array([[2.0, 0.0], [2.0, 5.0], [2.0, 5.0]])
    np.testing.assert_allclose(result.raw_residual.values, expected_diff)


def test_metadata_preservation():
    """Metadata such as physical timestamp, dt_sync_timestamp, and AoI are preserved."""
    obs = np.array([[10.0]])
    est = np.array([[8.0]])
    phys_ts = ["2018-01-01T00:15:00Z"]
    sync_ts = ["2018-01-01T00:00:00Z"]
    aoi = 900.0

    result = calculate_residual(
        obs,
        est,
        physical_timestamps=phys_ts,
        dt_sync_timestamps=sync_ts,
        aoi_seconds=aoi,
        feature_names=["load_kw"],
    )

    assert result.physical_timestamps == phys_ts
    assert result.dt_sync_timestamps == sync_ts
    assert result.aoi_seconds == 900.0
    assert result.feature_names == ["load_kw"]


def test_shape_mismatch_raises_error():
    """Shape mismatch must raise ValueError and never broadcast silently."""
    obs = np.array([10.0, 20.0, 30.0])
    est = np.array([10.0, 20.0])

    with pytest.raises(ValueError, match="Shape mismatch"):
        calculate_residual(obs, est)


def test_nan_and_inf_raises_error():
    """Inputs with NaN or infinite values must raise ValueError."""
    obs_nan = np.array([10.0, np.nan])
    est_clean = np.array([10.0, 20.0])

    with pytest.raises(ValueError, match="NaN"):
        calculate_residual(obs_nan, est_clean)

    obs_inf = np.array([10.0, np.inf])
    with pytest.raises(ValueError, match="infinite"):
        calculate_residual(obs_inf, est_clean)


def test_empty_input_raises_error():
    """Empty arrays must raise ValueError."""
    with pytest.raises(ValueError, match="empty"):
        calculate_residual(np.array([]), np.array([]))


def test_unaligned_dataframe_index_raises_error():
    """Mismatched DataFrame indices must raise ValueError."""
    idx1 = pd.date_range("2018-01-01", periods=2, freq="15min")
    idx2 = pd.date_range("2018-01-02", periods=2, freq="15min")

    df1 = pd.DataFrame({"p": [1.0, 2.0]}, index=idx1)
    df2 = pd.DataFrame({"p": [1.0, 2.0]}, index=idx2)

    with pytest.raises(ValueError, match="Timestamp/index mismatch"):
        calculate_residual(df1, df2)


def test_calculate_state_residual_zero(sample_dt_state):
    """Identical DigitalTwinState snapshots produce zero state residual."""
    result = calculate_state_residual(sample_dt_state, sample_dt_state)

    assert isinstance(result, StateResidualResult)
    np.testing.assert_allclose(result.full_state_residual, 0.0, atol=1e-12)
    assert result.l2_norm == 0.0
    assert result.total_power_residual_kw == 0.0
    assert result.metadata["max_voltage_error_pu"] == 0.0


def test_calculate_state_residual_drift(sample_dt_state):
    """Divergent DigitalTwinState snapshots compute correct per-quantity residuals."""
    modified_state = sample_dt_state.model_copy(deep=True)
    modified_state.bus_voltages_pu[18] = 0.90  # Sag from 0.95 to 0.90 (-0.05 pu)
    modified_state.total_load_p_kw = 4000.0  # Spike from 3500 to 4000 (+500 kW)

    result = calculate_state_residual(modified_state, sample_dt_state)

    assert result.l2_norm > 0.0
    assert pytest.approx(result.bus_voltage_residual_pu[18], rel=1e-5) == -0.10
    assert pytest.approx(result.total_power_residual_kw, rel=1e-5) == 500.0
    assert result.metadata["max_voltage_error_pu"] == pytest.approx(0.10, rel=1e-5)
