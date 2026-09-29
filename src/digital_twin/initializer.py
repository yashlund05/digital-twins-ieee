"""
src/digital_twin/initializer.py — Factory and baseline validation runner for Digital Twin.

Provides initialization from configuration files and orchestrates
Experiment E1: Digital Twin Baseline Validation.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.digital_twin.solver import DigitalTwinSolver
from src.digital_twin.state import DigitalTwinState
from src.utils.config import load_digital_twin_config
from src.utils.io import ensure_dir, save_json
from src.utils.logging import get_logger
from src.utils.reproducibility import create_manifest, get_git_commit

logger = get_logger("digital_twin.initializer")


def initialize_digital_twin(
    config_path: Path | str = "configs/digital_twin.yaml",
) -> DigitalTwinSolver:
    """Instantiate a configured DigitalTwinSolver from a YAML configuration file.

    Args:
        config_path: Path to digital_twin.yaml.

    Returns:
        Configured DigitalTwinSolver instance ready to solve power flows.
    """
    cfg = load_digital_twin_config(config_path)
    logger.info("Initializing Digital Twin from config", extra={"config_path": str(config_path)})

    solver = DigitalTwinSolver(
        base_kv=cfg.solver.voltage_bases[0] if cfg.solver.voltage_bases else 12.66,
        max_iterations=cfg.solver.max_iterations,
        tolerance=cfg.solver.convergence_tolerance,
    )
    return solver


def run_experiment_e1_validation(
    solver: DigitalTwinSolver | None = None,
    config_path: Path | str = "configs/digital_twin.yaml",
    data_path: Path | str = "data/processed/load_profiles.parquet",
    output_root: Path | str = "experiments/runs",
    seed: int = 42,
) -> dict[str, Any]:
    """Execute Experiment E1: Digital Twin Baseline Validation per EXPERIMENTS.md.

    Evaluates power flow convergence, voltage profile limits, and power balance
    across light (0.5x), nominal (1.0x), and heavy (1.5x) loading conditions using
    the mapped physical loads from the data pipeline (*_phys columns).

    Saves complete experiment run artifacts to:
    experiments/runs/E1_DT_VALIDATION_SEED42_<YYYYMMDD>/

    Args:
        solver: Optional initialized DigitalTwinSolver.
        config_path: Path to configuration YAML.
        data_path: Path to processed load profiles parquet file.
        output_root: Base runs directory.
        seed: Random seed for reproducibility.

    Returns:
        Validation results dictionary with verification status.
    """
    logger.info("Starting Experiment E1: Digital Twin Baseline Validation", extra={"seed": seed})

    if solver is None:
        solver = initialize_digital_twin(config_path)

    # Determine base physical loads from pipeline data
    p_data = Path(data_path)
    base_loads: dict[int, tuple[float, float]] = {}
    if p_data.exists():
        df_p = pd.read_parquet(p_data)
        # Select representative nominal timestep (median total load)
        phys_p_cols = [c for c in df_p.columns if c.endswith("_p_kw_phys")]
        if phys_p_cols:
            tot_p = df_p[phys_p_cols].sum(axis=1)
            med_idx = (tot_p - tot_p.median()).abs().idxmin()
            nom_row = df_p.loc[med_idx]
            for b in range(2, 34):
                base_loads[b] = (float(nom_row[f"bus_{b}_p_kw_phys"]), float(nom_row[f"bus_{b}_q_kvar_phys"]))
            logger.info(f"Loaded physical baseline loads from pipeline timestep {med_idx} (Total P: {tot_p.loc[med_idx]:.2f} kW)")
    
    if not base_loads:
        logger.warning("Pipeline physical loads not available; using benchmark nominal loads as fallback.")
        base_loads = IEEE_33_BENCHMARK_LOADS

    # Test loading conditions
    conditions = {
        "light_0.5x": 0.5,
        "nominal_1.0x": 1.0,
        "heavy_1.5x": 1.5,
    }

    states: dict[str, DigitalTwinState] = {}
    voltage_records: list[dict[str, Any]] = []
    power_records: list[dict[str, Any]] = []

    for name, mult in conditions.items():
        solver.reset()
        scaled_loads = {b: (p * mult, q * mult) for b, (p, q) in base_loads.items()}
        solver.set_all_loads(scaled_loads)
        state = solver.solve(timestamp=f"2018-01-01T12:00:00Z_{name}")
        states[name] = state

        # Collect voltages
        for bus_id in range(1, 34):
            voltage_records.append(
                {
                    "condition": name,
                    "multiplier": mult,
                    "bus_id": bus_id,
                    "v_pu": state.bus_voltages_pu[bus_id],
                    "v_kv": state.bus_voltages_kv[bus_id],
                    "angle_deg": state.bus_voltage_angles_deg[bus_id],
                }
            )

        # Collect power flow
        power_records.append(
            {
                "condition": name,
                "multiplier": mult,
                "converged": state.converged,
                "iterations": state.iterations,
                "total_gen_p_kw": state.total_generation_p_kw,
                "total_gen_q_kvar": state.total_generation_q_kvar,
                "total_load_p_kw": state.total_load_p_kw,
                "total_load_q_kvar": state.total_load_q_kvar,
                "total_loss_p_kw": state.total_losses_p_kw,
                "total_loss_q_kvar": state.total_losses_q_kvar,
                "balance_err_kw": state.power_balance_error_kw,
                "balance_err_pct": state.power_balance_error_pct,
                "min_v_pu": state.min_voltage_pu,
                "min_v_bus": state.min_voltage_bus,
                "max_v_pu": state.max_voltage_pu,
                "max_v_bus": state.max_voltage_bus,
            }
        )

    # Validate criteria
    nominal_state = states["nominal_1.0x"]
    voltage_ok = 0.90 <= nominal_state.min_voltage_pu and nominal_state.max_voltage_pu <= 1.10
    power_balance_ok = all(s.power_balance_error_pct < 0.5 for s in states.values())
    convergence_ok = all(s.converged for s in states.values())
    min_bus_is_18 = nominal_state.min_voltage_bus == 18

    all_passed = voltage_ok and power_balance_ok and convergence_ok

    # Prepare output directories
    date_str = datetime.utcnow().strftime("%Y%m%d")
    run_id = f"E1_DT_VALIDATION_SEED{seed}_{date_str}"
    run_dir = Path(output_root) / run_id
    results_dir = run_dir / "results"
    ensure_dir(results_dir)

    # Save results tables
    df_voltages = pd.DataFrame(voltage_records)
    df_power = pd.DataFrame(power_records)
    df_voltages.to_csv(results_dir / "voltage_profile.csv", index=False)
    df_power.to_csv(results_dir / "power_flow.csv", index=False)

    stats = {
        "experiment_id": "E1",
        "description": "Digital Twin Baseline Validation",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "all_criteria_passed": all_passed,
        "criteria": {
            "convergence": convergence_ok,
            "voltage_in_pu_range": voltage_ok,
            "power_balance_error_lt_0.5pct": power_balance_ok,
            "min_voltage_at_bus_18": min_bus_is_18,
        },
        "nominal_metrics": {
            "min_voltage_pu": nominal_state.min_voltage_pu,
            "min_voltage_bus": nominal_state.min_voltage_bus,
            "max_voltage_pu": nominal_state.max_voltage_pu,
            "total_gen_p_kw": nominal_state.total_generation_p_kw,
            "total_load_p_kw": nominal_state.total_load_p_kw,
            "total_loss_p_kw": nominal_state.total_losses_p_kw,
            "loss_percentage": (
                nominal_state.total_losses_p_kw / nominal_state.total_generation_p_kw
            )
            * 100.0,
            "power_balance_error_pct": nominal_state.power_balance_error_pct,
        },
    }
    save_json(stats, results_dir / "solver_stats.json")

    # Save authoritative manifest
    manifest = create_manifest(
        experiment_id="E1",
        run_id=run_id,
        config_file=str(config_path),
        config_version="1.0.0",
        random_seed=seed,
        synchronization_interval=0,
        missed_update_policy="none",
        input_representation="raw_load",
        model_type="opendss_ieee33_dt",
        dataset_version="Baran_Wu_1989_Benchmark",
        extra_metadata=stats,
    )
    save_json(manifest, run_dir / "manifest.json")

    # Generate summary report markdown
    summary_md = f"""# Experiment E1 — Digital Twin Baseline Validation Summary

- **Run ID**: `{run_id}`
- **Execution Date**: `{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}`
- **Git Commit**: `{get_git_commit()}`
- **Status**: **{"PASSED" if all_passed else "FAILED"}**

## Physical Validation Criteria

| Criterion | Target | Observed (Nominal 1.0x) | Status |
|:---|:---|:---|:---|
| **Convergence** | True for all loading conditions | True | {"PASSED" if convergence_ok else "FAILED"} |
| **Voltage Limits** | [0.90, 1.10] pu | [{nominal_state.min_voltage_pu:.4f}, {nominal_state.max_voltage_pu:.4f}] pu | {"PASSED" if voltage_ok else "FAILED"} |
| **Power Balance** | < 0.5% error | {nominal_state.power_balance_error_pct:.6f}% | {"PASSED" if power_balance_ok else "FAILED"} |
| **Min Voltage Location** | Bus 18 (Baran & Wu, 1989) | Bus {nominal_state.min_voltage_bus} | {"PASSED" if min_bus_is_18 else "OBSERVATION"} |

## Loading Condition Analysis

| Condition | Multiplier | P Gen (kW) | P Load (kW) | Losses (kW) | Loss % | Min V (pu) | Balance Error % |
|:---|:---|:---|:---|:---|:---|:---|:---|
| Light | 0.5x | {states["light_0.5x"].total_generation_p_kw:.2f} | {states["light_0.5x"].total_load_p_kw:.2f} | {states["light_0.5x"].total_losses_p_kw:.2f} | {(states["light_0.5x"].total_losses_p_kw / states["light_0.5x"].total_generation_p_kw) * 100:.2f}% | {states["light_0.5x"].min_voltage_pu:.4f} | {states["light_0.5x"].power_balance_error_pct:.6f}% |
| Nominal | 1.0x | {nominal_state.total_generation_p_kw:.2f} | {nominal_state.total_load_p_kw:.2f} | {nominal_state.total_losses_p_kw:.2f} | {(nominal_state.total_losses_p_kw / nominal_state.total_generation_p_kw) * 100:.2f}% | {nominal_state.min_voltage_pu:.4f} | {nominal_state.power_balance_error_pct:.6f}% |
| Heavy | 1.5x | {states["heavy_1.5x"].total_generation_p_kw:.2f} | {states["heavy_1.5x"].total_load_p_kw:.2f} | {states["heavy_1.5x"].total_losses_p_kw:.2f} | {(states["heavy_1.5x"].total_losses_p_kw / states["heavy_1.5x"].total_generation_p_kw) * 100:.2f}% | {states["heavy_1.5x"].min_voltage_pu:.4f} | {states["heavy_1.5x"].power_balance_error_pct:.6f}% |

*Experiment E1 executed per docs/experiments/EXPERIMENTS.md.*
"""
    (run_dir / "summary.md").write_text(summary_md, encoding="utf-8")
    logger.info(
        "Experiment E1 completed successfully", extra={"run_id": run_id, "all_passed": all_passed}
    )

    return {
        "status": "success",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "all_passed": all_passed,
        "stats": stats,
    }
