# Phase 18: Supplementary Material & Replication Guide

**Manuscript Title:** *Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin*  
**Target Venue:** IEEE Transactions on Smart Grid (IEEE TSG)  
**Package Version:** 1.0.0 (Submission Freeze)  
**Repository Source:** `digital-twins-ieee`

---

## 1. Overview of Supplementary Materials

This supplementary package provides full experimental matrices, cross-feeder topological parameters, Leave-One-Feeder-Out transfer results, computational complexity benchmarks, and complete replication scripts for all findings reported in the main manuscript.

### Directory Structure
```text
supplementary/
├── README.md                           <- This replication overview
├── robustness_tables/
│   ├── table_s1_full_factorial_24cond.csv
│   ├── table_s2_cross_feeder_summary.csv
│   ├── table_s3_lofo_transfer_results.csv
│   ├── table_s4_threshold_sensitivity.csv
│   ├── table_s5_computational_complexity.csv
│   └── table_s6_adversarial_h3_8formulations.csv
├── robustness_figures/
│   ├── fig_s1_cross_feeder_transition.pdf
│   ├── fig_s2_threshold_sensitivity.pdf
│   └── fig_s3_adversarial_h3_comparison.pdf
├── statistical_analysis/
│   ├── multiseed_variance_decomposition.csv
│   └── fdr_adjusted_hypothesis_matrix.csv
└── reproducibility/
    ├── command_manifest.json
    ├── environment_lock.txt
    └── hash_manifest.json
```

---

## 2. Replication Commands

Every number and table in the manuscript can be reproduced from the root repository directory via the following deterministic commands:

```bash
# 1. Run baseline physics validation (E1)
python -m src.cli validate-dt --config configs/digital_twin.yaml

# 2. Run baseline 2x2 factorial experiment (E4)
python -m src.cli run-e4 --seed 42

# 3. Run 24-condition factorial staleness sweep (E5)
python -m src.cli run-e5 --config configs/experiments/e5_staleness_sweep.yaml --seed 42

# 4. Run 10-seed multi-seed analysis (E10/E17)
python -m src.cli analyze-multiseed --seeds 42 123 456 789 101112 2024 31415 27182 65537 99991

# 5. Run full Phase 11-18 verification
python -m src.cli verify-reproducibility
```

---

## 3. Cryptographic Provenance Guarantee

All underlying artifacts from frozen phases E4 through E18 are protected with SHA-256 cryptographic hashes. Unmodified historical baseline metrics match to within $10^{-7}$ precision.
