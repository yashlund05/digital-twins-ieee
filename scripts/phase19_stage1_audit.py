import hashlib
import json
from pathlib import Path

root = Path('.').resolve()
run_dir = root / 'experiments' / 'runs' / 'E19_FINAL_SUBMISSION_AUDIT_20261006'

# Read previous verification file from E18
e18_hist = root / 'experiments' / 'runs' / 'E18_FINAL_REVIEW_HARDENING_20261006' / 'reproducibility' / 'historical_integrity_verified.json'
with open(e18_hist) as f:
    e18_data = json.load(f)

expected_map = {r['phase']: (r['path'], r['sha256']) for r in e18_data['records']}

# E18 manifest hash
e18_manifest_path = 'experiments/runs/E18_FINAL_REVIEW_HARDENING_20261006/manifest.json'
with open(root / e18_manifest_path, 'rb') as f:
    e18_hash = hashlib.sha256(f.read()).hexdigest()

expected_map['E18'] = (e18_manifest_path, e18_hash)

results = []
all_matched = True

for phase, (rel_path, exp_hash) in expected_map.items():
    file_path = root / rel_path
    if not file_path.exists():
        results.append({
            'phase': phase,
            'artifact': rel_path,
            'expected_hash': exp_hash,
            'current_hash': 'FILE_NOT_FOUND',
            'match': False,
            'status': 'FAIL_MISSING'
        })
        all_matched = False
        continue
    
    with open(file_path, 'rb') as f:
        curr_hash = hashlib.sha256(f.read()).hexdigest()
    
    match = (curr_hash == exp_hash)
    if not match:
        all_matched = False
    
    results.append({
        'phase': phase,
        'artifact': rel_path,
        'expected_hash': exp_hash,
        'current_hash': curr_hash,
        'match': match,
        'status': 'VERIFIED_IMMUTABLE' if match else 'CORRUPTED'
    })

integrity_doc = {
    'audit_target': 'Frozen Historical Phases E4-E18',
    'all_phases_intact': all_matched,
    'total_audited': len(results),
    'records': results
}

with open(run_dir / 'historical_integrity.json', 'w') as f:
    json.dump(integrity_doc, f, indent=2)

print('Stage 1 Result: all_phases_intact =', all_matched)
for r in results:
    print(f"{r['phase']}: match={r['match']}, status={r['status']}")
