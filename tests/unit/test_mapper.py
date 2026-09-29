"""
tests/unit/test_mapper.py — Unit tests for IEEE 33-bus topology mapping.
"""

import pandas as pd
import pytest

from src.data.loader import generate_benchmark_residential_traces
from src.data.mapper import (
    IEEE_33_BENCHMARK_LOADS,
    TOTAL_NOMINAL_P_KW,
    TOTAL_NOMINAL_Q_KVAR,
    map_homes_to_ieee33,
)


@pytest.fixture
def sample_home_profiles():
    """Generate 10 homes for 7 days at 15-minute resolution."""
    return generate_benchmark_residential_traces(
        num_homes=10,
        num_days=7,
        resolution_minutes=15,
        seed=100,
    )


def test_benchmark_constants():
    """Verify standard Baran & Wu (1989) benchmark load totals."""
    assert len(IEEE_33_BENCHMARK_LOADS) == 32
    # Load buses are 2 through 33
    assert set(IEEE_33_BENCHMARK_LOADS.keys()) == set(range(2, 34))
    assert sum(p for p, _ in IEEE_33_BENCHMARK_LOADS.values()) == pytest.approx(TOTAL_NOMINAL_P_KW)
    assert sum(q for _, q in IEEE_33_BENCHMARK_LOADS.values()) == pytest.approx(
        TOTAL_NOMINAL_Q_KVAR
    )


def test_map_homes_to_ieee33_structure(sample_home_profiles):
    """Verify output columns, bus counts, and summary metadata."""
    active_df, reactive_df, summary = map_homes_to_ieee33(
        sample_home_profiles, seed=42, homes_per_bus=2
    )

    assert len(active_df.columns) == 32
    assert len(reactive_df.columns) == 32
    assert len(active_df) == len(sample_home_profiles)

    for bus_id in range(2, 34):
        assert f"bus_{bus_id}_p_kw" in active_df.columns
        assert f"bus_{bus_id}_q_kvar" in reactive_df.columns
        assert bus_id in summary.bus_mappings

    assert summary.total_nominal_p_kw == pytest.approx(3715.0)
    assert summary.total_nominal_q_kvar == pytest.approx(2300.0)


def test_map_homes_to_ieee33_scaling(sample_home_profiles):
    """Verify that mean bus power accurately reflects nominal capacity."""
    active_df, reactive_df, _ = map_homes_to_ieee33(sample_home_profiles, seed=42, homes_per_bus=2)

    for bus_id in range(2, 34):
        nom_p, nom_q = IEEE_33_BENCHMARK_LOADS[bus_id]
        mean_p = active_df[f"bus_{bus_id}_p_kw"].mean()
        mean_q = reactive_df[f"bus_{bus_id}_q_kvar"].mean()

        # Mean power should match benchmark nominal within 0.1%
        assert mean_p == pytest.approx(nom_p, rel=1e-2)
        if nom_p > 0:
            assert (mean_q / mean_p) == pytest.approx(nom_q / nom_p, rel=1e-2)


def test_map_homes_to_ieee33_determinism(sample_home_profiles):
    """Verify that identical random seeds produce identical mappings."""
    active1, reactive1, summary1 = map_homes_to_ieee33(sample_home_profiles, seed=123)
    active2, reactive2, summary2 = map_homes_to_ieee33(sample_home_profiles, seed=123)

    pd.testing.assert_frame_equal(active1, active2)
    pd.testing.assert_frame_equal(reactive1, reactive2)
    assert summary1.model_dump() == summary2.model_dump()
