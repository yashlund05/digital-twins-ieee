"""
tests/unit/test_mapper.py — Unit tests for IEEE 33-bus topology mapping (ADR-0005).
"""

import numpy as np
import pandas as pd
import pytest

from src.data.loader import generate_benchmark_residential_traces
from src.data.mapper import (
    ANCHOR_PERCENTILE,
    IEEE_33_BENCHMARK_LOADS,
    TOTAL_NOMINAL_P_KW,
    TOTAL_NOMINAL_Q_KVAR,
    load_assignment_file,
    map_homes_to_ieee33,
)


@pytest.fixture(scope="module")
def sample_home_profiles():
    """Generate 25 homes for 7 days at 15-minute resolution (full inventory size)."""
    return generate_benchmark_residential_traces(
        num_homes=25,
        num_days=7,
        resolution_minutes=15,
        seed=100,
    )


@pytest.fixture(scope="module")
def synthetic_assignment(sample_home_profiles):
    """Deterministic, structurally valid assignment over the synthetic homes."""
    homes = list(sample_home_profiles.columns)
    slots = homes * 2 + homes[:14]  # 64 slots: 14 homes x3, 11 homes x2
    rng = np.random.default_rng(7)
    for _ in range(1000):
        order = slots.copy()
        rng.shuffle(order)
        cand = [order[2 * i: 2 * i + 2] for i in range(32)]
        if all(a[0] != a[1] for a in cand) and len({frozenset(a) for a in cand}) == 32:
            return {b: sorted(cand[b - 2]) for b in range(2, 34)}
    raise AssertionError("could not build a valid synthetic assignment")


def test_benchmark_constants():
    """Verify standard Baran & Wu (1989) benchmark load totals."""
    assert len(IEEE_33_BENCHMARK_LOADS) == 32
    assert set(IEEE_33_BENCHMARK_LOADS.keys()) == set(range(2, 34))
    assert sum(p for p, _ in IEEE_33_BENCHMARK_LOADS.values()) == pytest.approx(TOTAL_NOMINAL_P_KW)
    assert sum(q for _, q in IEEE_33_BENCHMARK_LOADS.values()) == pytest.approx(
        TOTAL_NOMINAL_Q_KVAR
    )


def test_anchor_registry():
    """Anchor options map to the documented feeder percentiles."""
    assert ANCHOR_PERCENTILE["mean"] is None
    assert ANCHOR_PERCENTILE["feeder_p99"] == 99.0
    assert ANCHOR_PERCENTILE["feeder_p999"] == 99.9
    assert ANCHOR_PERCENTILE["feeder_max"] == 100.0


def test_map_homes_to_ieee33_structure(sample_home_profiles, synthetic_assignment):
    """Verify output columns, bus counts, and ADR-0005 summary metadata."""
    active_df, reactive_df, summary = map_homes_to_ieee33(
        sample_home_profiles, assignment=synthetic_assignment
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
    assert summary.anchor == "feeder_p999"
    assert summary.alpha == 1.0
    assert summary.cap_multiple == 2.0
    assert summary.anchor_scale > 0
    assert len(summary.home_use_counts) == 25


def test_feeder_p999_anchor_sets_design_peak(sample_home_profiles, synthetic_assignment):
    """ADR-0005: p99.9 of the feeder total equals the 3,715 kW design peak (small
    deviation allowed where the 2.0x background cap clips extreme bus steps)."""
    active_df, _, summary = map_homes_to_ieee33(
        sample_home_profiles, assignment=synthetic_assignment
    )
    total = active_df.sum(axis=1)
    assert np.percentile(total, 99.9) == pytest.approx(3715.0, rel=5e-3)


def test_background_cap_bounds_every_bus(sample_home_profiles, synthetic_assignment):
    """ADR-0005 AC-3 (mapping level): no bus above cap_multiple x nominal."""
    active_df, _, summary = map_homes_to_ieee33(
        sample_home_profiles, assignment=synthetic_assignment
    )
    for bus_id in range(2, 34):
        nom_p = IEEE_33_BENCHMARK_LOADS[bus_id][0]
        assert active_df[f"bus_{bus_id}_p_kw"].max() <= 2.0 * nom_p + 1e-9


def test_reactive_power_preserves_benchmark_power_factor(
    sample_home_profiles, synthetic_assignment
):
    """Q/P ratio per bus must equal the benchmark nominal ratio."""
    active_df, reactive_df, _ = map_homes_to_ieee33(
        sample_home_profiles, assignment=synthetic_assignment
    )
    for bus_id in range(2, 34):
        nom_p, nom_q = IEEE_33_BENCHMARK_LOADS[bus_id]
        ratio = reactive_df[f"bus_{bus_id}_q_kvar"] / active_df[f"bus_{bus_id}_p_kw"]
        assert ratio.mean() == pytest.approx(nom_q / nom_p, rel=1e-2)


def test_legacy_mean_anchor_matches_nominal_means(sample_home_profiles, synthetic_assignment):
    """The legacy 'mean' anchor reproduces the pre-ADR-0005 mean-matching behavior."""
    active_df, _, summary = map_homes_to_ieee33(
        sample_home_profiles, assignment=synthetic_assignment, anchor="mean", cap_multiple=None
    )
    assert summary.anchor_scale == pytest.approx(1.0)
    for bus_id in range(2, 34):
        nom_p = IEEE_33_BENCHMARK_LOADS[bus_id][0]
        mean_p = active_df[f"bus_{bus_id}_p_kw"].mean()
        assert mean_p == pytest.approx(nom_p, rel=1e-2)


def test_map_homes_to_ieee33_determinism(sample_home_profiles, synthetic_assignment):
    """Identical inputs and assignment produce identical outputs."""
    out1 = map_homes_to_ieee33(sample_home_profiles, assignment=synthetic_assignment)
    out2 = map_homes_to_ieee33(sample_home_profiles, assignment=synthetic_assignment)
    pd.testing.assert_frame_equal(out1[0], out2[0])
    pd.testing.assert_frame_equal(out1[1], out2[1])
    assert out1[2].model_dump() == out2[2].model_dump()


def test_invalid_assignment_rejected(sample_home_profiles):
    """Duplicated pairs or duplicate homes within a bus must raise."""
    bad_dup_home = {b: [1000, 1000] if b == 2 else [1001, 1002] for b in range(2, 34)}
    with pytest.raises(ValueError):
        map_homes_to_ieee33(sample_home_profiles, assignment=bad_dup_home)
    bad_dup_pair = {b: [1000, 1001] for b in range(2, 34)}
    with pytest.raises(ValueError):
        map_homes_to_ieee33(sample_home_profiles, assignment=bad_dup_pair)


def test_load_assignment_file_contract():
    """The tracked assignment file loads into a valid 32-bus dict."""
    assignment = load_assignment_file()
    assert sorted(assignment) == list(range(2, 34))
    assert all(len(v) == 2 for v in assignment.values())
