"""
src/data/loader.py — Ingestion module for raw Pecan Street residential load data.

Provides utilities for reading and parsing 15-minute interval smart meter recordings
from Pecan Street Dataport CSV files, handling timezone conversions, and formatting
into a structured multi-home time-series matrix.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.logging import get_logger

logger = get_logger("data.loader")


def load_pecan_street_csv(
    filepath: Path | str,
    load_column: str = "grid",
    date_range: tuple[str | None, str | None] | None = None,
    home_ids: list[int] | None = None,
) -> pd.DataFrame:
    """Load and parse Pecan Street 15-minute residential CSV data.

    Pivots the raw tabular format into a multi-column time-series DataFrame
    where rows are indexed by UTC timestamp and columns represent home IDs (dataid).

    Args:
        filepath: Path to the raw Pecan Street CSV file.
        load_column: Name of the load column to use (default: 'grid' for net power exchange).
        date_range: Optional tuple of (start_date, end_date) in ISO format (e.g. '2018-01-01').
        home_ids: Optional list of integer home IDs to filter. If None, all available homes are used.

    Returns:
        DataFrame indexed by UTC datetime with one column per home ID containing active power in kW.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns ('dataid', 'local_15min', load_column) are missing.
    """
    path = Path(filepath)
    if not path.exists():
        logger.error("Raw data file not found", extra={"filepath": str(path)})
        raise FileNotFoundError(f"Pecan Street raw data file not found at: {path}")

    logger.info(
        "Reading raw Pecan Street CSV file", extra={"filepath": str(path), "load_col": load_column}
    )

    # Read required columns
    cols_to_read = ["dataid", "local_15min"]
    if load_column in ["gross", "use"]:
        # If 'use' is not directly present, compute gross = grid + solar (clamped to >= 0)
        sample = pd.read_csv(path, nrows=5)
        if "use" in sample.columns:
            actual_load_col = "use"
            cols_to_read.append("use")
        else:
            actual_load_col = "grid"
            cols_to_read.extend(["grid", "solar"])
    else:
        actual_load_col = load_column
        cols_to_read.append(load_column)

    df = pd.read_csv(
        path,
        usecols=cols_to_read,
    )
    if "solar" in df.columns:
        df["solar"] = df["solar"].fillna(0.0).clip(lower=0.0)
        df["gross"] = (df["grid"] + df["solar"]).clip(lower=0.05)
        actual_load_col = "gross"
    elif actual_load_col in df.columns:
        df[actual_load_col] = df[actual_load_col].clip(lower=0.05)

    logger.info(
        "Loaded raw CSV records",
        extra={"total_records": len(df), "unique_homes": df["dataid"].nunique()},
    )

    # Parse timestamps to UTC
    df["timestamp"] = pd.to_datetime(df["local_15min"], utc=True)
    df.drop(columns=["local_15min"], inplace=True)

    # Filter homes if specified
    if home_ids is not None:
        df = df[df["dataid"].isin(home_ids)]
        logger.info("Filtered by requested home IDs", extra={"retained_homes": len(home_ids)})

    # Filter date range if specified
    if date_range is not None:
        start_date, end_date = date_range
        if start_date:
            start_ts = pd.to_datetime(start_date, utc=True)
            df = df[df["timestamp"] >= start_ts]
        if end_date:
            end_ts = pd.to_datetime(end_date, utc=True)
            df = df[df["timestamp"] <= end_ts]
        logger.info("Filtered by date range", extra={"start": start_date, "end": end_date})

    # Pivot: Index = timestamp, Columns = dataid, Values = actual_load_col
    # Handle any duplicate timestamps per home by taking the mean
    pivoted = df.pivot_table(
        index="timestamp",
        columns="dataid",
        values=actual_load_col,
        aggfunc="mean",
    )

    pivoted.sort_index(inplace=True)
    logger.info(
        "Pivoted residential load matrix ready",
        extra={
            "num_timestamps": len(pivoted),
            "num_homes": len(pivoted.columns),
            "start": str(pivoted.index.min()),
            "end": str(pivoted.index.max()),
        },
    )

    return pivoted


def generate_benchmark_residential_traces(
    num_homes: int = 25,
    num_days: int = 365,
    resolution_minutes: int = 15,
    start_date: str = "2018-01-01 00:00:00",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate realistic synthetic residential load profiles matching Pecan Street statistics.

    Used for testing, reproducibility, and continuous integration environments where
    the large raw dataset is not downloaded.

    Simulates diurnal patterns with dual peaks (morning 07:00-09:00, evening 18:00-22:00),
    weekend vs weekday behavioral variations, and stochastic residential spikes.

    Args:
        num_homes: Number of distinct home profiles to generate.
        num_days: Total number of days.
        resolution_minutes: Interval in minutes (default 15).
        start_date: UTC start datetime string.
        seed: Random seed for deterministic reproducibility.

    Returns:
        DataFrame indexed by UTC datetime with columns representing integer home IDs.
    """
    rng = np.random.default_rng(seed)
    timesteps_per_day = (24 * 60) // resolution_minutes
    total_timesteps = num_days * timesteps_per_day

    timestamps = pd.date_range(
        start=pd.to_datetime(start_date, utc=True),
        periods=total_timesteps,
        freq=f"{resolution_minutes}min",
    )

    hours = timestamps.hour + timestamps.minute / 60.0
    day_of_week = timestamps.dayofweek

    # Base residential daily curve (kW)
    # Morning peak around 8 AM, evening peak around 7:30 PM, night base load ~0.4 kW
    morning_peak = 1.2 * np.exp(-0.5 * ((hours - 8.0) / 1.5) ** 2)
    evening_peak = 2.0 * np.exp(-0.5 * ((hours - 19.5) / 2.0) ** 2)
    base_load = 0.45 + morning_peak + evening_peak

    # Weekend effect: shifted morning peak, higher midday usage
    weekend_mask = (day_of_week >= 5).astype(float)
    weekend_shift = 0.3 * np.exp(-0.5 * ((hours - 13.0) / 3.0) ** 2)
    diurnal_profile = base_load + weekend_mask * weekend_shift

    home_columns = [1000 + i for i in range(num_homes)]
    data = np.zeros((total_timesteps, num_homes), dtype=np.float64)

    for i in range(num_homes):
        # Home-specific scale and noise profile
        home_scale = rng.uniform(0.7, 1.6)
        home_noise = rng.normal(0, 0.15, size=total_timesteps)
        # Random appliances firing (stochastic bursts)
        burst_prob = rng.uniform(0.02, 0.05)
        bursts = (rng.uniform(0, 1, size=total_timesteps) < burst_prob) * rng.exponential(
            1.5, size=total_timesteps
        )

        trace = (diurnal_profile * home_scale) + home_noise + bursts
        # Net power can occasionally be slightly negative if solar is simulated, but mostly positive
        data[:, i] = np.clip(trace, -0.5, 12.0)

    df = pd.DataFrame(data, index=timestamps, columns=home_columns)
    df.index.name = "timestamp"
    logger.info(
        "Generated synthetic benchmark residential traces",
        extra={"homes": num_homes, "steps": total_timesteps},
    )
    return df
