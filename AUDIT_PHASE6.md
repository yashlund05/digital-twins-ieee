# Phase 6 Audit Report: AUDIT_PHASE6.md

Date: 2026-09-29
Target: Phase 6 Anomaly Detection and Related Dependencies

---

## 1. REPO STATE

### Output of: `git log --oneline -15`

```
a92b4ca feat(anomaly_detection): implement anomaly detection baselines and experiment E3 (Phase 6)
db03a5c feat(forecasting): implement baseline load estimation models (Phase 5)
690f35f feat(sync): implement synchronization engine and staleness tracking (Phase 4)
25ce91b feat(digital-twin): implement Phase 3 IEEE 33-bus OpenDSS Digital Twin and validate Experiment E1
46a6d6d feat(data): implement Phase 2 data pipeline, IEEE 33-bus mapping, and anomaly injection
bf8cb16 feat(infra): complete Phase 1 environment validation and dependencies
303a6e0 phase 1
c84fc29 feat: initialize repository foundation and research governance
```

### Output of: `git status`

```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

### Output of: `ls -R experiments/runs` (top 2 levels only)

*(Executed via PowerShell `Get-ChildItem -Path experiments/runs -Depth 1`)*

```
FullName                                                                                                
--------                                                                                                
D:\digital twins ieee\experiments\runs\E1_DT_VALIDATION_SEED42_20260929                                 
D:\digital twins ieee\experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929                      
D:\digital twins ieee\experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929                    
D:\digital twins ieee\experiments\runs\.gitkeep                                                         
D:\digital twins ieee\experiments\runs\E1_DT_VALIDATION_SEED42_20260929\results                         
D:\digital twins ieee\experiments\runs\E1_DT_VALIDATION_SEED42_20260929\manifest.json                   
D:\digital twins ieee\experiments\runs\E1_DT_VALIDATION_SEED42_20260929\summary.md                      
D:\digital twins ieee\experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929\models               
D:\digital twins ieee\experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929\comparison.csv       
D:\digital twins ieee\experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929\manifest.json        
D:\digital twins ieee\experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929\metrics.json         
D:\digital twins ieee\experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929\predictions.parquet  
D:\digital twins ieee\experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929\summary.md           
D:\digital twins ieee\experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929\models             
D:\digital twins ieee\experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929\comparison.csv     
D:\digital twins ieee\experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929\manifest.json      
D:\digital twins ieee\experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929\metrics.json       
D:\digital twins ieee\experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929\predictions.parquet
D:\digital twins ieee\experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929\summary.md         
```

### Output of: `ls src/anomaly_detection src/forecasting src/synchronization src/digital_twin src/data`

*(Executed via PowerShell `Get-ChildItem src/anomaly_detection, src/forecasting, src/synchronization, src/digital_twin, src/data`)*

```
FullName                                                       
--------                                                       
D:\digital twins ieee\src\anomaly_detection\__pycache__        
D:\digital twins ieee\src\anomaly_detection\detector.py        
D:\digital twins ieee\src\anomaly_detection\experiment_e3.py   
D:\digital twins ieee\src\anomaly_detection\isolation_forest.py
D:\digital twins ieee\src\anomaly_detection\lstm_autoencoder.py
D:\digital twins ieee\src\anomaly_detection\thresholds.py      
D:\digital twins ieee\src\anomaly_detection\trainer.py         
D:\digital twins ieee\src\anomaly_detection\__init__.py        
D:\digital twins ieee\src\forecasting\__pycache__              
D:\digital twins ieee\src\forecasting\base.py                  
D:\digital twins ieee\src\forecasting\evaluator.py             
D:\digital twins ieee\src\forecasting\experiment_e2.py         
D:\digital twins ieee\src\forecasting\features.py              
D:\digital twins ieee\src\forecasting\lstm_model.py            
D:\digital twins ieee\src\forecasting\persistence.py           
D:\digital twins ieee\src\forecasting\trainer.py               
D:\digital twins ieee\src\forecasting\xgboost_model.py         
D:\digital twins ieee\src\forecasting\__init__.py              
D:\digital twins ieee\src\synchronization\__pycache__          
D:\digital twins ieee\src\synchronization\aoi.py               
D:\digital twins ieee\src\synchronization\engine.py            
D:\digital twins ieee\src\synchronization\logger.py            
D:\digital twins ieee\src\synchronization\policies.py          
D:\digital twins ieee\src\synchronization\scheduler.py         
D:\digital twins ieee\src\synchronization\state_tracker.py     
D:\digital twins ieee\src\synchronization\__init__.py          
D:\digital twins ieee\src\digital_twin\__pycache__             
D:\digital twins ieee\src\digital_twin\initializer.py          
D:\digital twins ieee\src\digital_twin\solver.py               
D:\digital twins ieee\src\digital_twin\state.py                
D:\digital twins ieee\src\digital_twin\topology.py             
D:\digital twins ieee\src\digital_twin\__init__.py             
D:\digital twins ieee\src\data\__pycache__                     
D:\digital twins ieee\src\data\anomaly_injector.py             
D:\digital twins ieee\src\data\loader.py                       
D:\digital twins ieee\src\data\mapper.py                       
D:\digital twins ieee\src\data\pipeline.py                     
D:\digital twins ieee\src\data\preprocessor.py                 
D:\digital twins ieee\src\data\schema.py                       
D:\digital twins ieee\src\data\splitter.py                     
D:\digital twins ieee\src\data\__init__.py                     
```

---

## 2. TESTS

### Execution: `make test`

Command output:
```
make : The term 'make' is not recognized as the name of a cmdlet, function, script file, or operable program. Check 
the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ make test
+ ~~~~
    + CategoryInfo          : ObjectNotFound: (make:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```
*(Status: `make` is not installed on this Windows environment).*

### Execution: `pytest -q`

Command output:
```
Windows fatal exception: code 0xe0465043

Current thread 0x00007364 (most recent call first):
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 1176 in create_module
  File "<frozen importlib._bootstrap>", line 571 in module_from_spec
  File "<frozen importlib._bootstrap>", line 674 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\dss_python_backend\__init__.py", line 12 in <module>
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 883 in exec_module
  File "<frozen importlib._bootstrap>", line 688 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\opendssdirect\utils.py", line 3 in <module>
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 883 in exec_module
  File "<frozen importlib._bootstrap>", line 688 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap>", line 1078 in _handle_fromlist
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\opendssdirect\__init__.py", line 13 in <module>
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 883 in exec_module
  File "<frozen importlib._bootstrap>", line 688 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "D:\digital twins ieee\src\digital_twin\solver.py", line 9 in <module>
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 883 in exec_module
  File "<frozen importlib._bootstrap>", line 688 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "D:\digital twins ieee\src\digital_twin\initializer.py", line 14 in <module>
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 883 in exec_module
  File "<frozen importlib._bootstrap>", line 688 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "D:\digital twins ieee\src\digital_twin\__init__.py", line 11 in <module>
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap_external>", line 883 in exec_module
  File "<frozen importlib._bootstrap>", line 688 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "<frozen importlib._bootstrap>", line 241 in _call_with_frames_removed
  File "<frozen importlib._bootstrap>", line 992 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "D:\digital twins ieee\tests\integration\test_dt_pipeline.py", line 9 in <module>
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\assertion\rewrite.py", line 186 in exec_module
  File "<frozen importlib._bootstrap>", line 688 in _load_unlocked
  File "<frozen importlib._bootstrap>", line 1006 in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 1027 in _find_and_load
  File "<frozen importlib._bootstrap>", line 1050 in _gcd_import
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\importlib\__init__.py", line 126 in import_module
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\pathlib.py", line 587 in import_path
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\python.py", line 498 in importtestmodule
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\python.py", line 551 in _getobj
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\python.py", line 280 in obj
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\python.py", line 567 in _register_setup_module_fixture
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\python.py", line 554 in collect
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\runner.py", line 389 in collect
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\runner.py", line 344 in from_call
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\runner.py", line 391 in pytest_make_collect_report
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_callers.py", line 121 in _multicall
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_manager.py", line 120 in _hookexec
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_hooks.py", line 512 in __call__
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\runner.py", line 567 in collect_one_node
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 839 in _collect_one_node
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 974 in genitems
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 979 in genitems
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 979 in genitems
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 813 in perform_collect
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 353 in pytest_collection
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_callers.py", line 121 in _multicall
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_manager.py", line 120 in _hookexec
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_hooks.py", line 512 in __call__
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 342 in _main
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 289 in wrap_session
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\main.py", line 336 in pytest_cmdline_main
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_callers.py", line 121 in _multicall
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_manager.py", line 120 in _hookexec
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\pluggy\_hooks.py", line 512 in __call__
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\config\__init__.py", line 175 in main
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\site-packages\_pytest\config\__init__.py", line 201 in console_main
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\runpy.py", line 86 in _run_code
  File "C:\Users\lundy\AppData\Local\Programs\Python\Python310\lib\runpy.py", line 196 in _run_module_as_main
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-8.4.2, pluggy-1.6.0
rootdir: D:\digital twins ieee
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.14.2, cov-5.0.0
collected 105 items

......................................................................................................... [100%]
105 passed in 21.43s
```

Final summary line:
`105 passed in 21.43s`
Failures: 0
Skips: 0
Warnings / Uncaught exceptions: C++ exception `Windows fatal exception: code 0xe0465043` thrown by `dss_python_backend/__init__.py:12` during dynamic library initialization, caught/managed internally by OpenDSS backend without failing tests.

---

## 3. CLI CHECKS

### 1. `python -m src.cli validate-dt`

Full output (last 40 lines):
```
Running Experiment E1: Digital Twin Baseline Validation (config=configs/digital_twin.yaml, seed=42)...
[SUCCESS] Experiment E1 Validation PASSED.
  Run ID           : E1_DT_VALIDATION_SEED42_20260929
  Min Voltage      : 0.9114 pu (Bus 18)
  Max Voltage      : 0.9983 pu
  Total P Gen      : 3918.03 kW
  Total P Load     : 3714.95 kW
  Total P Losses   : 203.13 kW (5.18%)
  Power Balance Err: 0.001103%
  Outputs saved to : experiments\runs\E1_DT_VALIDATION_SEED42_20260929
```
Errors: None. Exit code: 0.

### 2. `python -m src.cli train-anomaly`

Full output (last 40 lines):
```
Starting Experiment E3: Anomaly Detection Baselines (seed=42, input=raw)...
[SUCCESS] Experiment E3 complete. Results and models saved to experiments\runs\E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929
```
Errors: None. Exit code: 0.

### 3. `python -m src.cli train-forecast`

Full output (last 40 lines):
```
Starting Experiment E2: Load Estimation Baselines (seed=42)...
[SUCCESS] Experiment E2 complete. Results and models saved to experiments\runs\E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929
```
Errors: None. Exit code: 0.

---

## 4. E2 RESULTS (load estimation)

Path: `experiments/runs/E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929/`

### Manifest: `experiments/runs/E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929/manifest.json`

```json
{
  "experiment_id": "E2",
  "run_id": "E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929",
  "timestamp": "2026-09-29T18:04:31.375888",
  "status": "COMPLETED",
  "reproducibility": {
    "git_commit": "690f35ff2cb2e4f299f85f2f1b89293bd21e1f8d",
    "git_branch": "feature/phase-5-baseline-load-estimation",
    "git_clean": false,
    "configuration_file": "configs/forecasting.yaml",
    "configuration_version": "1.0.0",
    "dataset_version": "v1.0",
    "random_seed": 42
  },
  "model": {
    "type": "multi_model_baseline",
    "version": "1.0.0"
  },
  "synchronization": {
    "interval_seconds": 0,
    "missed_update_policy": "hold_last_state"
  },
  "experiment_design": {
    "input_representation": "raw",
    "model_type": "multi_model_baseline"
  },
  "environment": {
    "timestamp": "2026-09-29T18:04:31.551433",
    "python_version": "3.10.11",
    "os": "Windows 10",
    "architecture": "AMD64",
    "packages": {
      "numpy": "2.2.6",
      "pandas": "2.3.3",
      "scipy": "1.15.3",
      "scikit-learn": "1.7.2",
      "xgboost": "3.0.5",
      "opendssdirect.py": "0.9.4",
      "pydantic": "2.13.3",
      "pyyaml": "6.0.3",
      "matplotlib": "3.10.9",
      "click": "8.4.2",
      "pytest": "8.4.2",
      "ruff": "0.16.2",
      "torch": "2.11.0+cu128"
    }
  }
}
```

### Metrics: `experiments/runs/E2_BASELINE_LOAD_ESTIMATION_SEED42_20260929/metrics.json`

```json
{
  "persistence": {
    "val": {
      "mae": 0.3894186801924916,
      "rmse": 0.5654138937812231,
      "mape": 4.035331722791187,
      "r2": 0.879936113608587
    },
    "test": {
      "mae": 0.28390709976445955,
      "rmse": 0.40581430548595326,
      "mape": 3.250303747744074,
      "r2": 0.9113769317515443
    }
  },
  "xgboost": {
    "val": {
      "mae": 0.3971532224883046,
      "rmse": 0.5372794961200142,
      "mape": 4.262478103573785,
      "r2": 0.8915873452779979
    },
    "test": {
      "mae": 0.33845758311098934,
      "rmse": 0.44842310088336673,
      "mape": 3.9863260605000845,
      "r2": 0.8917898417797084
    }
  },
  "lstm": {
    "val": {
      "mae": 0.3883078802208269,
      "rmse": 0.5396204798950103,
      "mape": 4.085358649311688,
      "r2": 0.8904361753771003
    },
    "test": {
      "mae": 0.3292976173825139,
      "rmse": 0.44702956936786836,
      "mape": 3.814413527957631,
      "r2": 0.8925611842797821
    }
  }
}
```

---

## 5. E3 RESULTS (anomaly detection)

Path: `experiments/runs/E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929/`

### Manifest: `experiments/runs/E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929/manifest.json`

```json
{
  "experiment_id": "E3",
  "run_id": "E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929",
  "timestamp": "2026-09-29T18:22:22.521868",
  "status": "COMPLETED",
  "reproducibility": {
    "git_commit": "db03a5c69006e1ca6af4815d0805d8a3a4b63f51",
    "git_branch": "feature/phase-6-anomaly-detection",
    "git_clean": false,
    "configuration_file": "configs/anomaly_detection.yaml",
    "configuration_version": "1.0.0",
    "dataset_version": "v1.0",
    "random_seed": 42
  },
  "model": {
    "type": "multi_detector_baseline",
    "version": "1.0.0"
  },
  "synchronization": {
    "interval_seconds": 0,
    "missed_update_policy": "hold_last_state"
  },
  "experiment_design": {
    "input_representation": "raw",
    "model_type": "multi_detector_baseline"
  },
  "environment": {
    "timestamp": "2026-09-29T18:22:22.690729",
    "python_version": "3.10.11",
    "os": "Windows 10",
    "architecture": "AMD64",
    "packages": {
      "numpy": "2.2.6",
      "pandas": "2.3.3",
      "scipy": "1.15.3",
      "scikit-learn": "1.7.2",
      "xgboost": "3.0.5",
      "opendssdirect.py": "0.9.4",
      "pydantic": "2.13.3",
      "pyyaml": "6.0.3",
      "matplotlib": "3.10.9",
      "click": "8.4.2",
      "pytest": "8.4.2",
      "ruff": "0.16.2",
      "torch": "2.11.0+cu128"
    }
  }
}
```

### Metrics: `experiments/runs/E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929/metrics.json`

```json
{
  "isolation_forest": {
    "val": {
      "threshold": 0.49157874698093135,
      "precision": 0.022813688212927757,
      "recall": 0.023809523809523808,
      "f1": 0.023300970873786405,
      "false_positive_rate": 0.05135891286970424,
      "pr_auc": 0.047566739770656216,
      "roc_auc": 0.5048905320188294,
      "detection_latency": 3.873015873015873
    },
    "test": {
      "threshold": 0.49157874698093135,
      "precision": 0.0514018691588785,
      "recall": 0.045081967213114756,
      "f1": 0.04803493449781659,
      "false_positive_rate": 0.040502793296089384,
      "pr_auc": 0.05132652606359568,
      "roc_auc": 0.5450680661494381,
      "detection_latency": 3.7540983606557377
    }
  },
  "lstm_autoencoder": {
    "val": {
      "threshold": 0.002832928264979273,
      "precision": 0.20532319391634982,
      "recall": 0.21428571428571427,
      "f1": 0.20970873786407768,
      "false_positive_rate": 0.04176658673061551,
      "pr_auc": 0.15648440718409673,
      "roc_auc": 0.6239674926725286,
      "detection_latency": 2.984126984126984
    },
    "test": {
      "threshold": 0.002832928264979273,
      "precision": 0.391304347826087,
      "recall": 0.11065573770491803,
      "f1": 0.17252396166134185,
      "false_positive_rate": 0.008379888268156424,
      "pr_auc": 0.1466173606759377,
      "roc_auc": 0.6291253450734631,
      "detection_latency": 3.4754098360655736
    }
  }
}
```

### Exact Input Types Run
- **raw only**.
- `residual` input was **NOT run** in this experiment run.

### Anomaly Base Rate on Test Set
- Total test samples: `5256`
- Anomalous test samples: `244`
- Exact fraction: `244 / 5256 = 0.04642313546423135` (~**4.64%**)

---

## 6. FILE CONTENTS

### `configs/anomaly_detection.yaml`
```yaml
# anomaly_detection.yaml — Anomaly Detection configuration

anomaly_detection:
  # Detectors included in experiments
  detectors:
    - isolation_forest
    - lstm_autoencoder

  # Input representations (2x2 design with detectors)
  input_representations:
    - raw         # Raw DT state features
    - residual    # Physical - DT_prediction residuals

  # Training is UNSUPERVISED — anomaly labels are NOT used in training
  # Labels are used ONLY for evaluation
  unsupervised: true

  isolation_forest:
    n_estimators: 100
    max_samples: auto
    contamination: 0.05  # Expected anomaly rate (must match data.yaml)
    random_state: 42     # Must match experiment seed
    n_jobs: -1

  lstm_autoencoder:
    encoder_units: [64, 32]
    latent_dim: 16
    decoder_units: [32, 64]
    lookback_steps: 24
    batch_size: 32
    epochs: 100
    patience: 10
    learning_rate: 0.001
    seed: 42             # Must match experiment seed

  # Threshold selection
  threshold:
    method: percentile   # Options: percentile, fixed, otsu
    percentile: 95       # 95th percentile of training scores = threshold
    # IMPORTANT: threshold is set on validation set, not test set

  metrics:
    primary:
      - precision
      - recall
      - f1
      - pr_auc
    secondary:
      - roc_auc
      - false_positive_rate
      - detection_latency  # timesteps from anomaly onset to detection

```

### `configs/data.yaml`
```yaml
# data.yaml — Data pipeline configuration

data:
  source:
    pecan_street:
      resolution_minutes: 15  # 15-min resolution (default); 1-min for subset
      homes: null             # null = use all available homes
      date_range:
        start: null           # Set to specific date, e.g., "2018-01-01"
        end: null             # Set to specific date, e.g., "2020-12-31"

  network:
    topology: ieee_33_bus
    num_buses: 33
    num_load_buses: 32       # Bus 1 is the slack/source bus

  preprocessing:
    normalize: true
    normalization_method: min_max  # Options: min_max, z_score, robust
    fill_missing: forward_fill
    max_gap_minutes: 60      # Gaps larger than this are flagged

  splits:
    # Temporal split — no shuffling to prevent leakage
    train_ratio: 0.70
    validation_ratio: 0.15
    test_ratio: 0.15
    # IMPORTANT: splits are temporal (ordered), not random
    temporal: true

  anomaly_injection:
    enabled: true
    anomaly_rate: 0.05       # 5% of time steps have anomalies
    seed: 42                 # Must match experiment seed
    fault_types:
      - voltage_sag          # Sudden voltage drop
      - load_spike           # Sudden load increase
      - phase_imbalance      # Asymmetric loading
    duration_timesteps: 4    # Duration of each fault event (timesteps)

  # IMPORTANT: Document this clearly
  dataset_description: >
    HYBRID SIMULATION DATASET.
    Network topology: IEEE 33-bus benchmark feeder.
    Load profiles: Pecan Street Dataport (real residential consumption patterns).
    Mapping: Pecan Street loads mapped to IEEE 33-bus nodes per documented protocol.
    Anomalies: Synthetically injected per the anomaly_injection configuration above.
    This dataset does NOT represent real field measurements of the IEEE 33-bus feeder.

```

### `configs/synchronization.yaml`
```yaml
# synchronization.yaml — Synchronization Engine configuration
# This is the most research-critical configuration file.
# Changes here directly affect the experimental independent variable.

synchronization:
  # Default synchronization interval (seconds)
  # Override in experiment configurations
  interval_seconds: 60

  # Policy when an update is missed
  # Options:
  #   hold_last_state  — DT retains the last successfully synchronized state
  #   zero_input       — DT input is zeroed (not recommended for most scenarios)
  missed_update_policy: hold_last_state

  # Logging configuration
  logging:
    enabled: true
    fields:
      - physical_timestamp       # Timestamp of physical measurement
      - dt_timestamp             # Timestamp of last DT state update
      - last_sync_timestamp      # Timestamp of last successful sync
      - sync_age_seconds         # Age of current DT state (physical_time - last_sync)
      - aoi_seconds              # Age of Information
      - update_interval_seconds  # Configured interval
      - missed_updates_count     # Cumulative missed updates
      - solver_time_ms           # OpenDSS solver execution time
      - inference_time_ms        # ML model inference time
      - residual_magnitude       # L2 norm of physical-DT residual vector

  # Age of Information (AoI) configuration
  aoi:
    # AoI definition: time since last successful update arrived
    definition: time_since_last_update
    max_aoi_seconds: null  # null = no cap; set to limit divergence

  # Intervals used in the staleness sweep experiment (E5)
  # These define the experimental levels of the independent variable
  # IMPORTANT: Do not change these without creating an ADR
  sweep_intervals_seconds: [0, 15, 30, 60, 120, 300, 600, 900, 1800]
  # interval 0 = perfect synchronization (baseline)
  # intervals > 0 = controlled staleness

```

### `src/anomaly_detection/thresholds.py`
```python
"""
src/anomaly_detection/thresholds.py — Unsupervised anomaly threshold selection.

Implements threshold selection strategies for converting continuous anomaly scores
into binary predictions without using ground-truth labels:
    - Percentile-based (e.g. 95th percentile, matching expected contamination)
    - Otsu's method (bimodal variance maximization)
    - Fixed threshold value
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from src.utils.logging import get_logger

logger = get_logger("anomaly_detection.thresholds")


class BaseThresholdSelector(ABC):
    """Abstract base class for threshold selection mechanisms."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.fitted_threshold: float | None = None

    @abstractmethod
    def fit(self, scores: np.ndarray) -> float:
        """Derive decision threshold from validation anomaly scores.

        Args:
            scores: Continuous anomaly scores (higher = more anomalous).

        Returns:
            Scalar threshold value.
        """
        ...

    def apply(self, scores: np.ndarray, threshold: float | None = None) -> np.ndarray:
        """Convert continuous anomaly scores to binary 0/1 predictions.

        Args:
            scores: Anomaly scores.
            threshold: Optional threshold override.

        Returns:
            Binary numpy int32 array (1 = anomaly, 0 = normal).
        """
        thresh = threshold if threshold is not None else self.fitted_threshold
        if thresh is None:
            raise RuntimeError("Threshold selector must be fitted before calling apply().")
        sc = np.asarray(scores, dtype=np.float64)
        return (sc >= thresh).astype(np.int32)


class PercentileThreshold(BaseThresholdSelector):
    """Selects threshold as a specific empirical percentile of the score distribution."""

    def __init__(self, percentile: float = 95.0) -> None:
        """Initialize percentile threshold selector.

        Args:
            percentile: Percentile cutoff in [0, 100] (default: 95.0).
        """
        super().__init__(name="percentile")
        if not (0.0 <= percentile <= 100.0):
            raise ValueError(f"Percentile must be in [0, 100], got {percentile}")
        self.percentile = percentile

    def fit(self, scores: np.ndarray) -> float:
        """Compute empirical percentile threshold."""
        sc = np.asarray(scores, dtype=np.float64)
        self.fitted_threshold = float(np.percentile(sc, self.percentile))
        logger.info(
            f"PercentileThreshold({self.percentile}%): selected threshold = {self.fitted_threshold:.6f}"
        )
        return self.fitted_threshold


class FixedThreshold(BaseThresholdSelector):
    """Uses a predefined static numerical cutoff."""

    def __init__(self, threshold: float = 0.5) -> None:
        super().__init__(name="fixed")
        self.threshold = threshold
        self.fitted_threshold = threshold

    def fit(self, scores: np.ndarray) -> float:
        self.fitted_threshold = self.threshold
        return self.fitted_threshold


class OtsuThreshold(BaseThresholdSelector):
    """Computes optimal threshold by maximizing inter-class variance (Otsu's method)."""

    def __init__(self, n_bins: int = 256) -> None:
        super().__init__(name="otsu")
        self.n_bins = n_bins

    def fit(self, scores: np.ndarray) -> float:
        """Find threshold maximizing between-class variance across score histogram."""
        sc = np.asarray(scores, dtype=np.float64)
        min_v, max_v = float(np.min(sc)), float(np.max(sc))
        if min_v == max_v:
            self.fitted_threshold = min_v
            return min_v

        counts, bin_edges = np.histogram(sc, bins=self.n_bins, range=(min_v, max_v))
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        total_count = len(sc)

        best_var = 0.0
        best_threshold = bin_centers[0]

        weight_0 = 0.0
        sum_0 = 0.0
        total_sum = float(np.sum(counts * bin_centers))

        for i in range(len(counts)):
            weight_0 += counts[i]
            if weight_0 == 0:
                continue
            weight_1 = total_count - weight_0
            if weight_1 == 0:
                break

            sum_0 += counts[i] * bin_centers[i]
            mean_0 = sum_0 / weight_0
            mean_1 = (total_sum - sum_0) / weight_1

            between_var = weight_0 * weight_1 * ((mean_0 - mean_1) ** 2)
            if between_var > best_var:
                best_var = between_var
                best_threshold = float(bin_centers[i])

        self.fitted_threshold = best_threshold
        logger.info(f"OtsuThreshold: selected threshold = {self.fitted_threshold:.6f}")
        return self.fitted_threshold


def get_threshold_selector(
    method: str = "percentile",
    **kwargs: Any,
) -> BaseThresholdSelector:
    """Factory function for instantiating threshold selectors.

    Args:
        method: Name of strategy ('percentile', 'fixed', 'otsu').
        **kwargs: Method-specific hyperparameters.

    Returns:
        BaseThresholdSelector instance.
    """
    m = method.lower().strip()
    if m == "percentile":
        pct = kwargs.get("percentile", 95.0)
        return PercentileThreshold(percentile=pct)
    elif m == "fixed":
        th = kwargs.get("threshold", 0.5)
        return FixedThreshold(threshold=th)
    elif m == "otsu":
        return OtsuThreshold(n_bins=kwargs.get("n_bins", 256))
    else:
        raise ValueError(
            f"Unknown threshold method: '{method}'. Valid options: ['percentile', 'fixed', 'otsu']"
        )
```

### `src/anomaly_detection/trainer.py`
```python
"""
src/anomaly_detection/trainer.py — Unsupervised anomaly detection training coordinator.

Orchestrates unsupervised model training, validation score threshold calibration,
and unbiased test set evaluation across Isolation Forest and LSTM Autoencoder.
Enforces that no anomaly labels are seen during model fitting.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.anomaly_detection.detector import BaseAnomalyDetector
from src.anomaly_detection.isolation_forest import IsolationForestDetector
from src.anomaly_detection.lstm_autoencoder import LSTMAutoencoderDetector
from src.anomaly_detection.thresholds import get_threshold_selector
from src.evaluation.anomaly_metrics import compute_anomaly_metrics
from src.utils.config import AnomalyDetectionConfig, load_anomaly_detection_config
from src.utils.io import load_parquet
from src.utils.logging import get_logger
from src.utils.reproducibility import set_all_seeds

logger = get_logger("anomaly_detection.trainer")


@dataclass
class AnomalyEvaluationResult:
    """Stores evaluation metrics and predictions for an anomaly detector."""

    detector_name: str
    split_name: str
    input_representation: str
    threshold: float
    metrics: dict[str, float]
    scores: np.ndarray
    y_pred: np.ndarray
    y_true: np.ndarray


class AnomalyDetectionTrainer:
    """Coordinates unsupervised anomaly detector fitting, thresholding, and evaluation."""

    def __init__(
        self,
        config: AnomalyDetectionConfig | None = None,
        data_path: Path | str = "data/processed/load_profiles.parquet",
        labels_path: Path | str = "data/processed/anomaly_labels.parquet",
        splits_path: Path | str = "data/processed/splits.json",
        seed: int = 42,
    ) -> None:
        """Initialize anomaly detection trainer.

        Args:
            config: AnomalyDetectionConfig instance or None (loads from yaml).
            data_path: Path to processed load profiles parquet.
            labels_path: Path to anomaly labels parquet.
            splits_path: Path to splits.json.
            seed: Master random seed.
        """
        self.config = config or load_anomaly_detection_config()
        self.data_path = Path(data_path)
        self.labels_path = Path(labels_path)
        self.splits_path = Path(splits_path)
        self.seed = seed

        self.trained_detectors: dict[str, BaseAnomalyDetector] = {}
        self.evaluation_results: list[AnomalyEvaluationResult] = []

    def prepare_data(
        self,
        input_representation: str = "raw",
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], list[str]]:
        """Extract features and labels strictly aligned with dataset splits.

        Args:
            input_representation: 'raw' (load profiles) or 'residual'.

        Returns:
            Tuple of (features_dict, labels_dict, event_ids_dict, feature_names).
        """
        df_feats = load_parquet(self.data_path)
        df_labels = load_parquet(self.labels_path)

        with open(self.splits_path, encoding="utf-8") as f:
            splits = json.load(f)

        # Select continuous electrical telemetry features (32 P + 32 Q bus quantities)
        elec_cols = [
            c for c in df_feats.columns if c.startswith("bus_") and ("_p_kw" in c or "_q_kvar" in c)
        ]
        if not elec_cols:
            elec_cols = [c for c in df_feats.columns if c not in ["timestamp"]]

        X_all = df_feats[elec_cols].values.astype(np.float32)
        y_all = df_labels["is_anomaly"].values.astype(np.int32)
        events_all = df_labels["event_id"].values

        def _map_indices(idx_list: list[Any]) -> list[int]:
            if not idx_list:
                return []
            if isinstance(idx_list[0], int):
                return idx_list
            # Map timestamps to integer row indices
            ts_to_row = {ts: r for r, ts in enumerate(df_feats.index)}
            return [ts_to_row[ts] for ts in idx_list if ts in ts_to_row]

        train_rows = _map_indices(splits["train_indices"])
        val_rows = _map_indices(splits["validation_indices"])
        test_rows = _map_indices(splits["test_indices"])

        features = {
            "train": X_all[train_rows],
            "val": X_all[val_rows],
            "test": X_all[test_rows],
        }
        labels = {
            "train": y_all[train_rows],
            "val": y_all[val_rows],
            "test": y_all[test_rows],
        }
        events = {
            "train": events_all[train_rows],
            "val": events_all[val_rows],
            "test": events_all[test_rows],
        }

        return features, labels, events, elec_cols

    def train_and_evaluate_all(
        self,
        detectors_to_run: list[str] | None = None,
        input_representation: str = "raw",
    ) -> tuple[dict[str, BaseAnomalyDetector], pd.DataFrame]:
        """Train detectors unsupervised, tune threshold on val, and evaluate on test."""
        set_all_seeds(self.seed)
        selected = detectors_to_run or self.config.detectors
        features, labels, events, feat_names = self.prepare_data(input_representation)

        # Threshold selector factory
        th_selector = get_threshold_selector(
            method=self.config.threshold.method,
            percentile=self.config.threshold.percentile,
        )

        for det_name in selected:
            logger.info(f"=== Training Detector: {det_name.upper()} (Unsupervised) ===")
            if det_name == "isolation_forest":
                detector = IsolationForestDetector(
                    config=self.config.isolation_forest,
                    random_state=self.seed,
                )
                # Fit strictly without labels
                detector.fit(features["train"], feature_names=feat_names)

                # Calibrate threshold on validation split scores (unsupervised)
                val_scores = detector.score_samples(features["val"])
                optimal_threshold = th_selector.fit(val_scores)
                detector.set_threshold(optimal_threshold)

                # Evaluate on Validation
                val_pred = detector.predict(features["val"])
                val_metrics = compute_anomaly_metrics(
                    y_true=labels["val"],
                    y_pred=val_pred,
                    scores=val_scores,
                    event_ids=events["val"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="val",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=val_metrics,
                        scores=val_scores,
                        y_pred=val_pred,
                        y_true=labels["val"],
                    )
                )

                # Evaluate on Test
                test_scores = detector.score_samples(features["test"])
                test_pred = detector.predict(features["test"])
                test_metrics = compute_anomaly_metrics(
                    y_true=labels["test"],
                    y_pred=test_pred,
                    scores=test_scores,
                    event_ids=events["test"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="test",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=test_metrics,
                        scores=test_scores,
                        y_pred=test_pred,
                        y_true=labels["test"],
                    )
                )
                self.trained_detectors[det_name] = detector

            elif det_name == "lstm_autoencoder":
                detector = LSTMAutoencoderDetector(
                    config=self.config.lstm_autoencoder,
                    seed=self.seed,
                )
                detector.fit(features["train"], X_val=features["val"], feature_names=feat_names)

                # Calibrate threshold on validation split scores
                val_scores = detector.score_samples(features["val"])
                optimal_threshold = th_selector.fit(val_scores)
                detector.set_threshold(optimal_threshold)

                val_pred = detector.predict(features["val"])
                val_metrics = compute_anomaly_metrics(
                    y_true=labels["val"],
                    y_pred=val_pred,
                    scores=val_scores,
                    event_ids=events["val"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="val",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=val_metrics,
                        scores=val_scores,
                        y_pred=val_pred,
                        y_true=labels["val"],
                    )
                )

                test_scores = detector.score_samples(features["test"])
                test_pred = detector.predict(features["test"])
                test_metrics = compute_anomaly_metrics(
                    y_true=labels["test"],
                    y_pred=test_pred,
                    scores=test_scores,
                    event_ids=events["test"],
                )
                self.evaluation_results.append(
                    AnomalyEvaluationResult(
                        detector_name=det_name,
                        split_name="test",
                        input_representation=input_representation,
                        threshold=optimal_threshold,
                        metrics=test_metrics,
                        scores=test_scores,
                        y_pred=test_pred,
                        y_true=labels["test"],
                    )
                )
                self.trained_detectors[det_name] = detector

        comparison_df = self.get_comparison_dataframe()
        return self.trained_detectors, comparison_df

    def get_comparison_dataframe(self) -> pd.DataFrame:
        """Format evaluation results into a summary DataFrame."""
        rows = []
        for r in self.evaluation_results:
            rows.append(
                {
                    "detector": r.detector_name,
                    "split": r.split_name,
                    "input": r.input_representation,
                    "threshold": r.threshold,
                    "precision": r.metrics["precision"],
                    "recall": r.metrics["recall"],
                    "f1": r.metrics["f1"],
                    "pr_auc": r.metrics["pr_auc"],
                    "roc_auc": r.metrics["roc_auc"],
                    "fpr": r.metrics["false_positive_rate"],
                    "latency_steps": r.metrics["detection_latency"],
                }
            )
        return pd.DataFrame(rows)

    def save_detectors(self, output_dir: Path | str) -> None:
        """Save trained detector weights and thresholds."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for name, det in self.trained_detectors.items():
            det.save(out / name)
        logger.info(f"Saved {len(self.trained_detectors)} detectors to {out}")
```

### `src/data/anomaly_injector.py`
```python
"""
src/data/anomaly_injector.py — Controlled synthetic anomaly injection.

Injects synthetic anomalies (load spikes, voltage sags, phase imbalances) into the
mapped bus load time series with reproducible random seeds.
Stores ground-truth labels separately to prevent data leakage during model training.
"""

import uuid

import numpy as np
import pandas as pd

from src.data.schema import AnomalyEvent
from src.utils.logging import get_logger

logger = get_logger("data.anomaly_injector")


def inject_synthetic_anomalies(
    active_power_df: pd.DataFrame,
    reactive_power_df: pd.DataFrame,
    anomaly_rate: float = 0.05,
    fault_types: list[str] | None = None,
    duration_timesteps: int = 4,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[AnomalyEvent]]:
    """Inject synthetic anomalies into active and reactive bus load profiles.

    Produces:
    1. Perturbed active power profiles.
    2. Perturbed reactive power profiles.
    3. Separate ground truth anomaly labels DataFrame (is_anomaly, anomaly_type, affected_buses).
    4. List of AnomalyEvent metadata records.

    Fault Types:
    - load_spike: sudden demand increase (2.5x - 4.0x) on target buses.
    - voltage_sag: severe load drop / fault sag (0.2x - 0.5x) on target buses.
    - phase_imbalance: asymmetric perturbation across a cluster of buses.

    Args:
        active_power_df: DataFrame of active power by bus.
        reactive_power_df: DataFrame of reactive power by bus.
        anomaly_rate: Fraction of timesteps that should be anomalous (e.g., 0.05 for 5%).
        fault_types: List of fault types to inject. Defaults to all 3 types.
        duration_timesteps: Duration of each anomaly event in discrete timesteps.
        seed: Random seed for deterministic reproducibility.

    Returns:
        Tuple of (injected_active_df, injected_reactive_df, anomaly_labels_df, event_list).
    """
    if fault_types is None:
        fault_types = ["voltage_sag", "load_spike", "phase_imbalance"]

    logger.info(
        "Injecting synthetic anomalies",
        extra={
            "rate": anomaly_rate,
            "fault_types": fault_types,
            "duration": duration_timesteps,
            "seed": seed,
        },
    )

    rng = np.random.default_rng(seed)
    n_timesteps = len(active_power_df)
    timestamps = active_power_df.index
    bus_cols_p = list(active_power_df.columns)
    bus_cols_q = list(reactive_power_df.columns)
    num_buses = len(bus_cols_p)

    injected_p = active_power_df.copy()
    injected_q = reactive_power_df.copy()

    # Labels arrays
    is_anomaly = np.zeros(n_timesteps, dtype=np.int32)
    label_types = ["none"] * n_timesteps
    affected_buses_str = ["none"] * n_timesteps
    event_ids = ["none"] * n_timesteps

    # Calculate target number of anomaly events
    target_anomalous_steps = int(n_timesteps * anomaly_rate)
    num_events = max(1, target_anomalous_steps // duration_timesteps)

    # Pick non-overlapping start indices with a safety buffer
    buffer_zone = duration_timesteps * 2
    available_indices = list(range(buffer_zone, n_timesteps - buffer_zone))
    rng.shuffle(available_indices)

    events: list[AnomalyEvent] = []
    occupied_indices: set[int] = set()

    for idx in available_indices:
        if len(events) >= num_events:
            break

        event_range = set(range(idx, idx + duration_timesteps))
        # Ensure no overlap with existing events
        if event_range.intersection(occupied_indices):
            continue

        # Choose fault type and target buses
        fault_type = str(rng.choice(fault_types))
        event_id = f"ANOM_{uuid.UUID(bytes=rng.bytes(16)).hex[:8]}"

        # Select 1 to 4 affected buses
        num_target_buses = rng.integers(1, min(5, num_buses + 1))
        target_indices = rng.choice(num_buses, size=num_target_buses, replace=False)
        target_buses_p = [bus_cols_p[b] for b in target_indices]
        target_buses_q = [bus_cols_q[b] for b in target_indices]
        bus_numbers = [int(b.split("_")[1]) for b in target_buses_p]

        end_idx = idx + duration_timesteps

        if fault_type == "load_spike":
            multiplier = float(rng.uniform(2.5, 4.0))
            for b_p, b_q in zip(target_buses_p, target_buses_q, strict=True):
                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] *= multiplier
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] *= multiplier

        elif fault_type == "voltage_sag":
            multiplier = float(rng.uniform(0.2, 0.5))
            for b_p, b_q in zip(target_buses_p, target_buses_q, strict=True):
                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] *= multiplier
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] *= multiplier

        elif fault_type == "phase_imbalance":
            multiplier = float(rng.uniform(2.0, 3.5))
            # Primary bus surges, others drop
            first_b_p, first_b_q = target_buses_p[0], target_buses_q[0]
            injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(first_b_p)] *= multiplier
            injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(first_b_q)] *= multiplier
            for b_p, b_q in zip(target_buses_p[1:], target_buses_q[1:], strict=True):
                injected_p.iloc[idx:end_idx, injected_p.columns.get_loc(b_p)] *= 0.4
                injected_q.iloc[idx:end_idx, injected_q.columns.get_loc(b_q)] *= 0.4

        # Record labels
        for step in range(idx, end_idx):
            is_anomaly[step] = 1
            label_types[step] = fault_type
            affected_buses_str[step] = ",".join(map(str, bus_numbers))
            event_ids[step] = event_id

        occupied_indices.update(event_range)

        events.append(
            AnomalyEvent(
                event_id=event_id,
                fault_type=fault_type,
                target_buses=bus_numbers,
                start_index=idx,
                end_index=end_idx,
                duration_timesteps=duration_timesteps,
                magnitude=multiplier,
                start_timestamp=timestamps[idx].isoformat(),
                end_timestamp=timestamps[end_idx - 1].isoformat(),
            )
        )

    labels_df = pd.DataFrame(
        {
            "is_anomaly": is_anomaly,
            "anomaly_type": label_types,
            "affected_buses": affected_buses_str,
            "event_id": event_ids,
        },
        index=timestamps,
    )

    actual_rate = float(np.mean(is_anomaly))
    logger.info(
        "Anomaly injection complete",
        extra={
            "num_events": len(events),
            "anomalous_steps": int(np.sum(is_anomaly)),
            "actual_rate": round(actual_rate, 4),
        },
    )

    return injected_p, injected_q, labels_df, events
```

### `src/data/splitter.py`
```python
"""
src/data/splitter.py — Strict temporal dataset splitting.

Partitions time-series data chronologically into training (70%), validation (15%),
and test (15%) splits without shuffling.
Enforces zero temporal leakage per DATA_PROTOCOL.md research integrity requirements.
"""

import pandas as pd

from src.data.schema import TemporalSplitIndices
from src.utils.logging import get_logger

logger = get_logger("data.splitter")


def compute_temporal_splits(
    total_timesteps: int,
    train_ratio: float = 0.70,
    validation_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> TemporalSplitIndices:
    """Compute strictly chronological indices for train, validation, and test sets.

    Guarantees:
    - Zero future leakage: max(train) < min(val) and max(val) < min(test).
    - No random shuffling.
    - Continuous time blocks.

    Args:
        total_timesteps: Total number of observations in the time series.
        train_ratio: Fraction for training split (default: 0.70).
        validation_ratio: Fraction for validation split (default: 0.15).
        test_ratio: Fraction for testing split (default: 0.15).

    Returns:
        TemporalSplitIndices schema containing the verified split indices.

    Raises:
        ValueError: If ratios do not sum to 1.0 or if total_timesteps is insufficient.
    """
    total_ratio = train_ratio + validation_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-5:
        raise ValueError(f"Split ratios must sum to 1.0, got: {total_ratio:.4f}")

    if total_timesteps < 10:
        raise ValueError(
            f"Insufficient timesteps ({total_timesteps}) for three-way temporal split."
        )

    n_train = int(total_timesteps * train_ratio)
    n_val = int(total_timesteps * validation_ratio)
    n_test = total_timesteps - n_train - n_val

    if n_train <= 0 or n_val <= 0 or n_test <= 0:
        raise ValueError("Calculated split sizes must all be strictly positive.")

    train_indices = list(range(0, n_train))
    val_indices = list(range(n_train, n_train + n_val))
    test_indices = list(range(n_train + n_val, total_timesteps))

    splits = TemporalSplitIndices(
        train_indices=train_indices,
        validation_indices=val_indices,
        test_indices=test_indices,
        temporal=True,
        leak_free=True,
    )

    logger.info(
        "Computed temporal splits successfully",
        extra={
            "train_size": len(train_indices),
            "val_size": len(val_indices),
            "test_size": len(test_indices),
            "total": total_timesteps,
        },
    )

    return splits


def get_split_date_ranges(
    timestamps: pd.DatetimeIndex,
    splits: TemporalSplitIndices,
) -> dict[str, dict[str, str]]:
    """Return human-readable ISO date ranges for each temporal split partition.

    Args:
        timestamps: Full DatetimeIndex of the dataset.
        splits: Computed split indices.

    Returns:
        Dictionary mapping partition name to start and end ISO timestamp strings.
    """
    return {
        "train": {
            "start": timestamps[splits.train_indices[0]].isoformat(),
            "end": timestamps[splits.train_indices[-1]].isoformat(),
            "count": str(len(splits.train_indices)),
        },
        "validation": {
            "start": timestamps[splits.validation_indices[0]].isoformat(),
            "end": timestamps[splits.validation_indices[-1]].isoformat(),
            "count": str(len(splits.validation_indices)),
        },
        "test": {
            "start": timestamps[splits.test_indices[0]].isoformat(),
            "end": timestamps[splits.test_indices[-1]].isoformat(),
            "count": str(len(splits.test_indices)),
        },
    }
```

### `src/digital_twin/state.py`
```python
"""
src/digital_twin/state.py — Digital Twin state representation.

Defines the state data structure representing the virtual physical state
of the IEEE 33-bus feeder at any discrete time instance.
Serializes to JSON and provides feature vector exports for downstream ML tasks.
"""

import json

import numpy as np
from pydantic import BaseModel, Field


class DigitalTwinState(BaseModel):
    """Complete snapshot of the IEEE 33-bus Digital Twin state."""

    timestamp: str | None = Field(default=None, description="ISO 8601 UTC timestamp")
    converged: bool = Field(..., description="Whether OpenDSS power flow converged")
    iterations: int = Field(default=1, ge=1, description="Number of solver iterations")

    # Nodal electrical quantities (buses 1 to 33)
    bus_voltages_pu: dict[int, float] = Field(
        ..., description="Positive-sequence voltage magnitude per bus in per-unit (pu)"
    )
    bus_voltages_kv: dict[int, float] = Field(
        ..., description="Voltage magnitude per bus in kV (line-to-neutral or line-to-line)"
    )
    bus_voltage_angles_deg: dict[int, float] = Field(
        ..., description="Voltage phase angle per bus in degrees"
    )

    # Branch electrical quantities (lines L1 to L32)
    branch_currents_a: dict[str, float] = Field(
        ..., description="Current magnitude per distribution line in Amperes"
    )

    # System-level power quantities (kW, kVAR)
    total_generation_p_kw: float = Field(
        ..., description="Total active power supplied by slack bus (kW)"
    )
    total_generation_q_kvar: float = Field(
        ..., description="Total reactive power supplied by slack bus (kVAR)"
    )
    total_load_p_kw: float = Field(
        ..., description="Total active load consumed across all load buses (kW)"
    )
    total_load_q_kvar: float = Field(
        ..., description="Total reactive load consumed across all load buses (kVAR)"
    )
    total_losses_p_kw: float = Field(..., description="Total technical active power losses (kW)")
    total_losses_q_kvar: float = Field(
        ..., description="Total technical reactive power losses (kVAR)"
    )

    # Physical validation metrics
    power_balance_error_kw: float = Field(..., description="|P_gen - P_load - P_loss| in kW")
    power_balance_error_pct: float = Field(
        ..., description="Power balance error as percentage of P_gen"
    )
    min_voltage_pu: float = Field(..., description="Minimum bus voltage magnitude in pu")
    min_voltage_bus: int = Field(..., description="Bus ID where minimum voltage occurs")
    max_voltage_pu: float = Field(..., description="Maximum bus voltage magnitude in pu")
    max_voltage_bus: int = Field(..., description="Bus ID where maximum voltage occurs")

    def to_feature_vector(self) -> np.ndarray:
        """Flatten state into a 1D numerical array for ML model inputs and residual calculation.

        Vector layout:
        - 33 bus voltages (pu): Bus 1..33
        - 33 bus voltage angles (deg): Bus 1..33
        - 32 branch currents (A): L1..L32
        - Total power and losses: [gen_p, gen_q, load_p, load_q, loss_p, loss_q]

        Returns:
            1D numpy float64 array of shape (104,).
        """
        voltages = [self.bus_voltages_pu[b] for b in range(1, 34)]
        angles = [self.bus_voltage_angles_deg[b] for b in range(1, 34)]
        currents = [self.branch_currents_a[f"L{i}"] for i in range(1, 33)]
        globals_vec = [
            self.total_generation_p_kw,
            self.total_generation_q_kvar,
            self.total_load_p_kw,
            self.total_load_q_kvar,
            self.total_losses_p_kw,
            self.total_losses_q_kvar,
        ]
        return np.array(voltages + angles + currents + globals_vec, dtype=np.float64)

    def to_json(self, indent: int | None = None) -> str:
        """Serialize state object to JSON string."""
        return json.dumps(self.model_dump(), indent=indent)
```

---

## 7. LEAKAGE CHECKS

### 1. Are any anomaly labels used during detector training? Where?
- **NO**.
- **Evidence**:
  - `src/anomaly_detection/trainer.py` lines 156–158:
    ```python
    # Fit strictly without labels
    detector.fit(features["train"], feature_names=feat_names)
    ```
  - `src/anomaly_detection/trainer.py` line 213:
    ```python
    detector.fit(features["train"], X_val=features["val"], feature_names=feat_names)
    ```
  - `src/anomaly_detection/isolation_forest.py` line 44:
    ```python
    def fit(self, X: np.ndarray, feature_names: list[str] | None = None) -> "IsolationForestDetector":
        # ...
        self.model.fit(X_arr)
    ```
  - `src/anomaly_detection/lstm_autoencoder.py` line 186:
    ```python
    def fit(self, X_train: np.ndarray, X_val: np.ndarray | None = None, feature_names: list[str] | None = None) -> "LSTMAutoencoderDetector":
        # PyTorch MSE loss between x_batch and model(x_batch); no y labels passed or used
    ```
  - Ground truth labels `labels["val"]` and `labels["test"]` are passed exclusively to `compute_anomaly_metrics()` at lines 167–171, 189–193, 222–226, and 243–247 of `src/anomaly_detection/trainer.py` for post-prediction scoring.

### 2. On which split is the anomaly threshold selected (train, val, or test)?
- **Validation split (`val`) only**.
- **Evidence**:
  - `src/anomaly_detection/trainer.py` lines 160–163:
    ```python
    val_scores = detector.score_samples(features["val"])
    optimal_threshold = th_selector.fit(val_scores)
    detector.set_threshold(optimal_threshold)
    ```
  - `src/anomaly_detection/trainer.py` lines 216–219:
    ```python
    val_scores = detector.score_samples(features["val"])
    optimal_threshold = th_selector.fit(val_scores)
    detector.set_threshold(optimal_threshold)
    ```
  - The threshold selector evaluates only continuous scores on `features["val"]`. The test set is scored using this fixed threshold without modification (lines 199 and 253).

### 3. On which split are scalers/normalizers fitted?
- **Training split (`train`) only**.
- **Evidence**:
  - `src/data/preprocessor.py` lines 140–185 (`fit_and_apply_normalization`):
    - Line 147: *"Fit scaler strictly on the training partition and normalize the entire dataset."*
    - Line 167: `train_data = df.iloc[train_indices][feature_columns]`
    - Lines 175–182: `v_min = float(np.nanmin(vals))`, `v_max = float(np.nanmax(vals))` derived exclusively from `train_data[col]`.
  - `src/forecasting/features.py` lines 183–193:
    - Normalization parameters are loaded from `data/processed/normalization_params.json` (which records the train-only min/max parameters).

### 4. Do the train/val/test splits overlap in time? Show split boundaries from `data/processed/splits.json`.
- **NO temporal overlap**.
- **Evidence from `data/processed/splits.json` and timestamp index**:
  - Index ranges:
    - Train: indices `[0, 24527]` (Length: 24,528)
    - Validation: indices `[24528, 29783]` (Length: 5,256)
    - Test: indices `[29784, 35039]` (Length: 5,256)
  - Timestamps:
    - **Train**: `2018-01-01 06:00:00+00:00` to `2018-09-13 17:45:00+00:00`
    - **Validation**: `2018-09-13 18:00:00+00:00` to `2018-11-07 11:45:00+00:00`
    - **Test**: `2018-11-07 12:00:00+00:00` to `2019-01-01 05:45:00+00:00`
  - Gap / boundary alignment: Exactly 15 minutes between `train.end` and `val.start`, and exactly 15 minutes between `val.end` and `test.start`. Contiguous and non-overlapping.

---

## 8. GAPS

### Phase 6 Acceptance Criteria & Definition of Done Audit

| Item | Requirement in `PHASES.md` | Audit Result | Evidence Path / Reason |
|---|---|---|---|
| **Acceptance Criteria 1** | Both detectors are trained in unsupervised mode (no anomaly labels in training) | **DONE** | [`src/anomaly_detection/trainer.py#L156-L158`](file:///d:/digital%20twins%20ieee/src/anomaly_detection/trainer.py#L156-L158), [`src/anomaly_detection/trainer.py#L213`](file:///d:/digital%20twins%20ieee/src/anomaly_detection/trainer.py#L213) |
| **Acceptance Criteria 2** | Both detectors produce anomaly scores | **DONE** | [`src/anomaly_detection/isolation_forest.py#L65-L79`](file:///d:/digital%20twins%20ieee/src/anomaly_detection/isolation_forest.py#L65-L79), [`src/anomaly_detection/lstm_autoencoder.py#L254-L281`](file:///d:/digital%20twins%20ieee/src/anomaly_detection/lstm_autoencoder.py#L254-L281) |
| **Acceptance Criteria 3** | Threshold selection is configurable and documented | **DONE** | [`src/anomaly_detection/thresholds.py#L57-L168`](file:///d:/digital%20twins%20ieee/src/anomaly_detection/thresholds.py#L57-L168), [`configs/anomaly_detection.yaml#L37-L40`](file:///d:/digital%20twins%20ieee/configs/anomaly_detection.yaml#L37-L40) |
| **Acceptance Criteria 4** | All metrics computed correctly | **DONE** | [`src/evaluation/anomaly_metrics.py#L1-L189`](file:///d:/digital%20twins%20ieee/src/evaluation/anomaly_metrics.py#L1-L189), [`tests/unit/test_anomaly_metrics.py`](file:///d:/digital%20twins%20ieee/tests/unit/test_anomaly_metrics.py) |
| **Acceptance Criteria 5** | Models are deterministic for fixed seeds | **DONE** | Verified in [`tests/unit/test_isolation_forest.py`](file:///d:/digital%20twins%20ieee/tests/unit/test_isolation_forest.py) & [`tests/unit/test_lstm_autoencoder.py`](file:///d:/digital%20twins%20ieee/tests/unit/test_lstm_autoencoder.py) |
| **Definition of Done 1** | E3 results produced for both detectors, both raw and residual inputs | **NOT DONE (PARTIAL)** | **Defect found**: `experiments/runs/E3_BASELINE_ANOMALY_DETECTION_SEED42_20260929/` contains results for **raw input only**. Residual input requires Phase 7 (Residual Engine), which is marked as "Ready" but was not yet implemented. Thus, DoD requirement "both raw and residual inputs" is **not fully satisfied**. |
| **Definition of Done 2** | `python -m src.cli train-anomaly` succeeds | **DONE** | Command executed cleanly and generated E3 artifacts. Exit code 0. |

---

### Inconsistencies & Deficiencies Found in Completed Phases

1. **Phase 6 Definition of Done Mismatch**:
   - `PHASES.md` line 455 states: *"E3 results produced for both detectors, both raw and residual inputs"*.
   - Only `raw` inputs have been run for E3. `residual` inputs cannot be run until Phase 7 (`src/residuals/`) is implemented. Marking Phase 6 fully "Completed" without residual input results is a DoD gap.

2. **Missing Module Specified in Phase 5**:
   - `PHASES.md` line 364 lists `- src/forecasting/predictor.py — inference interface` under Phase 5 Modules.
   - File does **not exist** (`d:/digital twins ieee/src/forecasting/predictor.py: The system cannot find the file specified`). Inference is implemented directly in `base.py`, `evaluator.py`, and individual model classes, but `predictor.py` was never created.

3. **Makefile Missing on Windows Host**:
   - `Makefile` exists in root, but `make` executable is not installed or available on this Windows host. Commands requiring `make test` fail at terminal execution.

4. **Transient C++ Dynamic Library Exception**:
   - Running `pytest` outputs `Windows fatal exception: code 0xe0465043` during `dss_python_backend` initialization on Windows. Although tests continue and all 105 pass, stderr captures this native command exception.
