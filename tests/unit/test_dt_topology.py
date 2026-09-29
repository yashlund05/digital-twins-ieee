"""
tests/unit/test_dt_topology.py — Unit tests for IEEE 33-bus topology definition.
"""

from src.digital_twin.topology import (
    BASE_KV,
    IEEE_33_BRANCHES,
    IEEE_33_LOADS,
    FeederTopology,
    export_dss_file,
    generate_dss_circuit_commands,
)


def test_topology_data_structures():
    """Verify standard IEEE 33-bus graph structure (33 buses, 32 branches)."""
    assert len(IEEE_33_BRANCHES) == 32
    assert len(IEEE_33_LOADS) == 32
    assert BASE_KV == 12.66

    topology = FeederTopology()
    assert topology.num_buses == 33
    assert topology.num_branches == 32
    assert topology.slack_bus == 1


def test_generate_dss_circuit_commands():
    """Verify generated OpenDSS script command list."""
    commands = generate_dss_circuit_commands(load_multiplier=1.0)
    assert len(commands) > 40
    assert commands[0] == "Clear"
    assert "New Circuit.IEEE33Bus" in commands[1]
    assert any("Line.L1" in c for c in commands)
    assert any("Line.L32" in c for c in commands)
    assert any("Load.Load2" in c for c in commands)
    assert any("Load.Load33" in c for c in commands)


def test_generate_dss_circuit_commands_multiplier():
    """Verify that load_multiplier correctly scales load commands."""
    commands_1x = generate_dss_circuit_commands(load_multiplier=1.0)
    commands_2x = generate_dss_circuit_commands(load_multiplier=2.0)

    # Bus 2 has nominal kW=100. At 2x it should be kW=200.0
    load2_1x = next(c for c in commands_1x if "Load2" in c)
    load2_2x = next(c for c in commands_2x if "Load2" in c)

    assert "kW=100.0000" in load2_1x
    assert "kW=200.0000" in load2_2x


def test_export_dss_file(tmp_path):
    """Test exporting circuit to a .dss text file."""
    out_file = tmp_path / "ieee33_test.dss"
    res_path = export_dss_file(out_file)

    assert res_path.exists()
    content = res_path.read_text(encoding="utf-8")
    assert "Circuit.IEEE33Bus" in content
    assert "Line.L1" in content
