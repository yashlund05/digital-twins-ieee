# Data Directory

> [!IMPORTANT]
> This project uses a **hybrid simulation dataset**.
> Raw data files are NOT committed to Git (see `.gitignore`).
> See `docs/methodology/DATA_PROTOCOL.md` for the full data protocol.

## Directory Structure

```
data/
├── raw/          # Raw, unmodified input data (read-only after download)
├── interim/      # Intermediate processing artifacts
├── processed/    # Final processed datasets used in experiments
└── README.md     # This file
```

## raw/

Contains:
- Raw Pecan Street Dataport download files (CSV format)
- IEEE 33-bus topology definition files

**Access:** Pecan Street data requires registration at https://dataport.pecanstreet.org  
**License:** Subject to Pecan Street data use agreement  
**Do NOT modify raw files after download.**

## interim/

Contains intermediate processing outputs:
- Cleaned Pecan Street load profiles (before IEEE mapping)
- Normalized time series
- Generated during: `python -m src.cli prepare-data --stage interim`

## processed/

Contains final experiment-ready datasets:
- `load_profiles.parquet` — Mapped IEEE 33-bus load profiles
- `anomaly_labels.parquet` — Synthetic fault injection labels
- `splits.json` — Train/validation/test split indices
- Generated during: `python -m src.cli prepare-data`

## Dataset Description

This dataset is a **hybrid simulation dataset** composed of:

| Component | Source | Role |
|-----------|--------|------|
| Network topology | IEEE 33-bus benchmark feeder | Grid structure and parameters |
| Load profiles | Pecan Street Dataport | Real residential consumption patterns |
| Anomaly labels | Synthetic injection (see `configs/data.yaml`) | Ground truth for anomaly evaluation |

> [!WARNING]
> This dataset does NOT represent real field measurements of the IEEE 33-bus feeder.
> Pecan Street provides consumption patterns, not measurements from this specific topology.
> All results are qualified to this hybrid simulation context.

## To Regenerate

```bash
# Download Pecan Street data (requires .env with credentials)
python -m src.cli download-data

# Run full data pipeline
python -m src.cli prepare-data
```
