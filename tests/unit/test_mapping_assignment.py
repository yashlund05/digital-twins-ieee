"""
tests/unit/test_mapping_assignment.py — Tests for the tracked household-to-bus
assignment file (configs/mapping_assignment.yaml, ADR-0005).

The assignment is a tracked dataset-construction constant: these tests pin its
structural contract so the mapping can never silently drift from it.
"""

import pytest
import yaml

from src.utils.io import load_yaml_file

ASSIGNMENT_PATH = "configs/mapping_assignment.yaml"


@pytest.fixture(scope="module")
def assignment():
    return load_yaml_file(ASSIGNMENT_PATH)


def test_assignment_file_exists_and_versioned(assignment):
    assert assignment["assignment_version"] == "1.0"
    assert assignment["homes_per_bus"] == 2
    assert assignment["num_load_buses"] == 32
    assert assignment["source_adr"] == "docs/decisions/ADR-0005-load-mapping.md"


def test_all_32_load_buses_present_exactly_once(assignment):
    buses = sorted(int(k) for k in assignment["bus_assignments"])
    assert buses == list(range(2, 34))


def test_use_counts_are_balanced_14x3_and_11x2(assignment):
    """ADR-0005 4.2: every home used 2-3 times; 14 homes x3, 11 homes x2 = 64 slots."""
    from collections import Counter

    uses = Counter(h for v in assignment["bus_assignments"].values() for h in v)
    assert len(uses) == 25, "all 25 households must be used"
    assert set(uses.values()) <= {2, 3}, "each home used 2 or 3 times"
    assert Counter(uses.values()) == Counter({3: 14, 2: 11})
    assert sum(uses.values()) == 64


def test_two_distinct_homes_per_bus(assignment):
    for bus, homes in assignment["bus_assignments"].items():
        assert len(homes) == 2, f"bus {bus} must have exactly 2 homes"
        assert homes[0] != homes[1], f"bus {bus} must have 2 distinct homes"


def test_no_duplicated_pair_across_buses(assignment):
    pairs = [frozenset(v) for v in assignment["bus_assignments"].values()]
    assert len(set(pairs)) == len(pairs), "no two buses may share the identical home pair"


def test_mapper_output_matches_assignment_file(sample_home_profiles, assignment):
    """The mapper must reproduce the tracked assignment exactly (B1.1 contract)."""
    from src.data.mapper import map_homes_to_ieee33

    assign = {int(k): v for k, v in assignment["bus_assignments"].items()}
    # Rename synthetic home columns to the real household ids so the tracked
    # assignment can be exercised end-to-end.
    rename = dict(zip(sample_home_profiles.columns, sorted(assign_h for v in assign.values() for assign_h in v)))
    profiles = sample_home_profiles.rename(columns=rename)
    _, _, summary = map_homes_to_ieee33(profiles, assignment=assign)
    for bus, homes in assign.items():
        assert sorted(summary.bus_mappings[bus].assigned_homes) == sorted(homes)


@pytest.fixture(scope="module")
def sample_home_profiles():
    """Small synthetic home matrix for mapper-contract tests."""
    from src.data.loader import generate_benchmark_residential_traces

    return generate_benchmark_residential_traces(
        num_homes=25, num_days=7, resolution_minutes=15, seed=100
    )


def test_assignment_file_is_valid_yaml_mapping_contract():
    with open(ASSIGNMENT_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    assert isinstance(raw, dict)
    assert "bus_assignments" in raw
