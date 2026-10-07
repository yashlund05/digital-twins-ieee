# IEEE Transactions on Smart Grid — Reproducibility Release Package

This directory provides the definitive reproduction instructions and cryptographic manifests for:
**"Quantifying the Effect of Digital Twin Synchronization Staleness on Joint Short-Term Load Estimation and Unsupervised Anomaly Detection in a Distribution-Feeder Digital Twin"**

## 1. System Requirements & Environment
- **Operating System:** Windows 10/11, Ubuntu 22.04 LTS, or macOS (x86_64 or arm64)
- **Python Version:** Python 3.10, 3.11, or 3.14 (see locked package specs)
- **Primary Dependencies:** `numpy`, `scipy`, `pandas`, `scikit-learn`, `torch`, `dss-python` (OpenDSS C-backend)

To restore the exact environment:
```bash
pip install -r supplementary/reproducibility/environment_lock.txt
```

## 2. Reproduction Commands
1. **Historical Immutability & SHA-256 Audit:**
   ```bash
   python scripts/phase19_stage1_audit.py
   ```
2. **Claim Registry Verification:**
   ```bash
   python scripts/phase19_stage2_claim_audit.py
   ```
3. **Full Regression Test Suite:**
   ```bash
   pytest tests/ -v
   ```
4. **Computational Latency Microbenchmark:**
   ```bash
   python -m experiments.computational_microbenchmark
   ```
5. **Interactive Research Dashboard:**
   ```bash
   streamlit run app.py --server.port 5569
   ```

## 3. Cryptographic Verification
All experiment outputs and tables are hashed and recorded in `reproduction_manifest.json`.
