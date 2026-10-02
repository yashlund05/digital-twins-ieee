# Phase 12 Publication Artifacts Package

- **Publication Target:** IEEE Transactions on Smart Grid
- **Date:** 20261002
- **Run Directory:** `experiments\runs\E12_PUBLICATION_ARTIFACTS_20261002`

## Directory Structure
- `figures/`: 8 publication figures (PNG 300 DPI + vector PDF)
- `tables/`: 6 IEEE-formatted tables in CSV and LaTeX (`.tex`)
- `source_data/`: Underlying CSV source datasets for every publication figure
- `latex/`: LaTeX environments, mathematical notation, and standalone paper wrapper
- `provenance/`: Traceability manifests, figure provenance, and SHA-256 hashes
- `summary.md`: Structured paper summary with findings, interpretations, and limitations
- `integrity_report.json`: Source completeness and baseline audit
- `manifest.json`: Cryptographic execution manifest

## Verification Command
```bash
python -m src.cli build-publication-artifacts --config configs/publication/phase12_sources.yaml --strict
```
