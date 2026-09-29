# ADR-0005: Load Mapping Redesign for Physical Plausibility

> **Status:** Accepted — 2026-09-30, approver: **Research Lead** (B0 numbers approved: p99.9 anchor, α=1.0 primary / α=0.3 fallback, balanced assignment, 2.0× cap applied at mapping)
> **Date:** 2026-09-30 (v2, after B0 re-measurement; v1 draft same day)
> **Deciders:** Research Lead, Data Engineer, DT Engineer
> **Consulted:** Anomaly Detection Engineer, Integration Lead
> **Informed:** All Contributors
> **Supersedes (in part):** the mean-matching scaling convention of `src/data/mapper.py` (in force since the Phase 2 implementation); does **not** supersede ADR-0004 (injection stays additive sigma-based per bus).
>
> **v2 changelog (B0):** recommendation renamed as its own **Option (iv) — Re-anchor only**; the v1 claim "per-bus max/mean falls to ≈ 2.6–6.6" is **retracted** (it came from a discarded buggy script that flattened all bus means; correct figures below); all mapping statistics re-measured on the **pre-injection** series; anchor-percentile sensitivity added (full-horizon solves); balanced household assignment added; PR-AUC-improvement claim removed.

---

## 1. Context and Problem Statement

The current mapping assigns 2 Pecan Street households per load bus (households reused across
buses) and scales each bus so that the **mean** of its physical series equals the Baran & Wu
(1989) nominal load (`scaling_factor = nom_p / mean_raw`, `src/data/mapper.py:120`). Measured
consequences (pre-injection series unless stated; all values re-measured 2026-09-30):

| Symptom | Measured value |
|---|---|
| Per-bus peak/mean ratio (pre-injection, current assignment) | 4.48 – 6.85 (median 5.62) |
| Worst single bus above 2× nominal, post-injection series | bus 29, 17 steps = 0.049 % (natural peak) |
| Feeder total P (post-injection parquet) | mean 1.004×, p99.9 3.25×, max **3.72×** nominal (13,830 kW) |
| Minimum bus voltage over the year | **0.6979 pu** (bus 33); Vmin < 0.90 pu at 32.17 % of timesteps |
| Per-bus scaling factors | 17.1 – 225.2 ("a 1 kW home becomes up to 225 kW") |

Below `Vminpu = 0.85`, OpenDSS converts constant-PQ loads to constant-Z
(`src/digital_twin/topology.py:143`): at the worst step the solver consumes 8,354 kW against
10,070 kW fed. The heavy tail also makes natural coincidence peaks collide with injected-anomaly
score magnitudes, and it collapses the voltage channel that Phase 7 residuals will need.

**Household inventory (hard constraint).** The raw export `data/raw/15minute_data_austin.csv`
contains exactly **25 distinct households** (`dataid`: 661, 1642, 2335, 2361, 2818, 3039, 3456,
3538, 4031, 4373, 4767, 5746, 6139, 7536, 7719, 7800, 7901, 7951, 8156, 8386, 8565, 9019, 9160,
9278, 9922), each with near-complete 15-min coverage (34,468–35,036 rows). The loader applies no
household-selection filter (`src/data/loader.py` pivots every `dataid` present); 25 is the full
inventory. The current mapping uses 22 of the 25 (661, 3456, 7719 unused).

### Root-cause observation

The 25-home **feeder aggregate** itself peaks at **3.14×** its mean (summer coincidence), and
per-bus household pairs peak at 4.5–6.9× their means (pre-injection). Scaling so that
*mean = nominal* therefore guarantees the feeder operates far above its design loading whenever
households coincide. Baran & Wu's 3,715 kW / 2,300 kVAR is a **design peak**, not an annual
mean — the benchmark reference solution (Vmin ≈ 0.9131 pu at bus 18) describes the feeder *at
that peak*. The binding error is the **anchor**, not the household shapes.

---

## 2. Acceptance Criteria (any accepted mapping must satisfy ALL of)

- **AC-1 Convergence:** 100 % of the 35,040 timesteps solve (`Converged() == True`).
- **AC-2 Voltage:** at least **99 %** of timesteps with Vmin ≥ 0.90 pu.
- **AC-3 Thermal plausibility:** no bus above **2× its nominal** rating for more than **0.1 %**
  of timesteps (≤ 35 steps per bus), measured on the **final** (injected) series.

---

## 3. Candidates Considered (all numbers measured on the actual 25-home dataset)

### Option (i) — Aggregate K households per bus, disjoint sets

- **Households needed:** 32 × K disjoint; K=2 needs **64**, K=4 needs 128. With 25 available the
  maximum disjoint K is **0** — **infeasible** with this dataset even at K=1. Feasible only with
  more data (full Dataport license, another year, second region).
- **Expected peak/mean (if 64 homes existed):** ≈ 1 + (p−1)/√K with single-home p ≈ 8–10, i.e.
  ≈ 5–6.5 at K=2, ≈ 3.5–4 at K=4 — AC-3 would still be at risk under the mean anchor.
- **Detectability:** per-bus σ/mean falls ≈ 1/√K; injected absolute ΔP shrinks by the same
  factor; z-detectability unchanged by construction.
- **Honest limitations:** infeasible today; does not fix the anchor error.

### Option (ii) — Reuse households, add random time-of-day offsets

Simulated (production assignment; per-home-copy circular shift, ±2 h / ±4 h, seed 42):

| Variant | per-bus peak/mean (min/med/max) | worst bus >2× nominal | feeder max (×nom) |
|---|---|---|---|
| offsets ±2 h | 4.33 / 5.55 / 6.86 | **17.6 %** of steps | 3.48 |
| offsets ±4 h | 4.30 / 5.50 / 7.13 | **17.1 %** of steps | 3.17 |

- **Households needed:** 25 (reuse). **Detectability:** σ/mean ≈ 0.78–0.79 (baseline 0.81) —
  essentially unchanged.
- **Honest limitations:** fails AC-3 by two orders of magnitude; feeder max still >3× nominal;
  offsets are synthetic behavior; not recommended.

### Option (iii) — Smooth feeder shape + per-bus household residual at reduced amplitude, **mean-anchored**

`P_b(t) = nom_b·[(1−α)·F(t) + α·h_b(t)]` with the current mean-matching anchor retained:

| α | per-bus peak/mean (min/med/max) | worst bus >2× nominal | feeder max (×nom) |
|---|---|---|---|
| 0.2 | 3.18 / 3.41 / 3.77 | **10.9 %** of steps | 3.24 |
| 0.3 | 3.22 / 3.59 / 4.10 | **11.8 %** of steps | 3.30 |
| 0.5 | 3.64 / 4.03 / 4.76 | **13.4 %** of steps | 3.42 |

- **Honest limitations:** **fails AC-3 even as α → 0** because the feeder aggregate `F(t)` itself
  peaks at 3.14× its mean and the mean anchor amplifies that to 3.14× nominal. As α falls, all
  buses converge to one shared shape (correlation → 1), making bus-level anomalies trivially
  separable — an unrealistic task. Rejected as the fix; its shape machinery is reused in
  Option (iv)'s fallback.

---

## 4. Option (iv) — Re-anchor only (ADOPTED CANDIDATE)

**Keep the real household shapes and the 2-home-per-bus protocol; replace the mean-matching
anchor with a feeder-coincidence-peak anchor; balance the household assignment; cap the
background at 2.0× nominal.**

### 4.1 Construction

```
shape_b(t) = (1−α)·F(t) + α·h_b(t)                      # mean-1 shape for bus b
             α = 1.0 primary (pure real household shapes);
             α = 0.3 pre-approved fallback (damps bus-level peaks)
F(t)       = 25-home aggregate shape (mean 1)           # pre-injection series
h_b(t)     = assigned household-pair sum, normalized to mean 1
S(t)       = Σ_b nom_b · shape_b(t)                     # unnormalized feeder total (mean 3,715 kW)
s          = 3715 / percentile(S, 99.9)                 # ANCHOR — see 4.4
P_b(t)     = min( nom_b · s · shape_b(t) , 2.0·nom_b )  # 2.0× background cap, applied at mapping
Q_b(t)     = P_b(t) · (Q_b_nom / P_b_nom)               # benchmark power factor preserved
```

Injection (ADR-0004, additive σ-based) is applied **after** anchoring, on `P_b`/`Q_b`; the cap
therefore bounds the *background*, and injected spike peaks may exceed 2× nominal (see 4.5).

### 4.2 Balanced household assignment (adopted)

- All **25 homes** used (the 3 idle homes 661, 3456, 7719 come into service): 64 slots =
  **14 homes ×3 + 11 homes ×2** uses; exactly 2 distinct homes per bus; **no home twice at the
  same bus**; **no duplicated pair across buses** (a v1 draft assignment accidentally gave buses
  6 and 8 the identical pair — corr 1.0000 — and was discarded).
- Deterministic from seed 42 (shuffle attempt 2 of the seeded stream; algorithm: fixed use
  counts via seeded `choice`, seeded `shuffle`, first valid deal, pair-uniqueness check).
- Usage and per-bus tables are recorded in `mapping_config.json` at implementation time
  (`assigned_homes`, `home_use_counts`).

Measured on the balanced, pre-injection series: per-bus peak/mean **3.96 – 7.18** (median 5.45);
bus-pair shape correlation **0.759 mean for pairs sharing a home vs 0.531 for pairs that do
not** (uplift **+0.228**; 53 shared / 443 unshared pairs) — sharing a home still correlates two
buses; that is dataset-limited and is now measured, documented, and roughly uniform (each home
appears at 2–3 buses).

### 4.3 Anchor-percentile sensitivity (balanced assignment, α = 1.0, cap 2.0×, full 35,040-step OpenDSS solves, pre-injection series)

| Anchor | s | clipped bus-steps (2.0× cap) | feeder mean (×nom) | feeder max (×nom) | Vmin < 0.90 pu | min Vmin | AC-2 |
|---|---|---|---|---|---|---|---|
| p99 | 0.362066 | 79 (bus 26: 27) | 0.3621 | 1.206 | 114 (0.3253 %) | 0.8791 | **99.6747 % ✓** |
| **p99.9 (adopted)** | **0.324053** | **15 (bus 26: 10)** | **0.3241** | 1.084 | **14 (0.0400 %)** | **0.8927** | **99.9600 % ✓** |
| max | 0.298989 | 5 (bus 26: 5) | 0.2990 | 1.000 | 0 (0.0000 %) | 0.9019 | 100.0000 % ✓ |

All three converge 35,040/35,040 (AC-1 ✓). **p99.9 adopted**: it keeps the load factor near the
middle option while leaving an order-of-magnitude margin on AC-2 (0.040 % used of the 1 %
budget). The worst step of every anchor is the same coincidence-peak family
(2018-07-18 ≈ 22:00 UTC, bus 33).

### 4.4 The anchor is a dataset-construction constant

`s` is computed **once**, on the **pre-injection full-year series** (S over all 35,040 steps),
and stored in `mapping_config.json` as `anchor_scale`. It is **not a fitted statistic**: it uses
no labels, no train/val/test distinction, and no model; it has the same epistemic status as the
seeded household assignment and the benchmark nominalization itself — a fixed property of the
dataset version. It is nevertheless recorded openly here because it "sees" the whole horizon at
construction time; if the dataset window ever changes, `s` is recomputed and the dataset version
bumped. Downstream code must read `s` from the mapping config, never recompute it from splits.

The p99.9 percentile was chosen **after inspecting full-year voltage results**: the B0.2
sensitivity solves (§4.3) showed p99 leaves only a 3× margin on AC-2 (0.3253 % of steps below
0.90 pu against the 1 % budget) with the worst Vmin at 0.8791, while the max anchor gives a
100 % pass but the lowest load factor (0.299×). p99.9 keeps an order-of-magnitude AC-2 margin
(0.0400 % used) at a moderate load factor (0.3241×) — a decision made on measured full-horizon
OpenDSS evidence, not on load statistics alone.

### 4.5 Injection interaction and AC-3 on the final series (measured)

Simulating the current ADR-0004 additive injection on the anchored series (current assignment,
p99.9 anchor, seed 42, cap applied at mapping only): bus-steps above 2× nominal rise from 2
(pre-injection) to **89 across 17 buses** (worst bus 29: 17 steps = **0.0485 % ≤ 0.1 %**).
Per-bus AC-3 therefore **holds on the final series** — the 0.1 % budget absorbs spike peaks —
and the cap's role is to bound the *background*, not the anomalies. The definitive AC-3
verification runs on the regenerated parquet in the Stage-B1 integration test; if injection
pushes any bus past 0.1 % of steps, that will be **reported, and the criteria will not be
relaxed**.

### 4.6 Verification of the adopted variant (balanced assignment, p99.9 anchor, full-horizon OpenDSS)

| Variant | AC-1 | Vmin < 0.90 pu (AC-2 ≤ 1 %) | min Vmin | clipped bus-steps | feeder mean (×nom) |
|---|---|---|---|---|---|
| **α = 1.0 (primary)** | **35,040/35,040 (100 %)** | **14 (0.0400 %) → 99.9600 %** | 0.8927 (bus 33) | 15 | 0.3241 |
| α = 0.3 (fallback) | **35,040/35,040 (100 %)** | **0 (0.0000 %) → 100.0000 %** | 0.9021 (bus 18) | 0 | 0.3343 |

Implied effective scaling (α = 1.0): `s · nom_b / mean(raw_b)`; e.g. bus 2 ≈ 14.1, bus 24 ≈ 49.9,
bus 25 ≈ 69.5 under the current assignment — "a 1 kW home becomes ≈ 14–70 kW" instead of
17–225 kW. Load factor of the feeder: **0.324× nominal** (primary), 0.334× (fallback).

### 4.7 What this does to anomaly detectability (corrected)

**By construction, z-space detectability is invariant to the rescale.** Injected magnitudes are
defined as multiples of each bus's training-split σ, and the detectors' features are the
train-fitted min-max-normalized bus P/Q columns, which are re-derived from the new series with
the same train-only protocol. The rescale therefore does **not** — and is not claimed to —
improve PR-AUC or any score-based metric (the v1 draft claimed a false-positive improvement from
a tighter background; that claim is **retracted** as unsupported). What actually changes:

1. **The 2.0× cap** truncates background peaks at 2× nominal (15 bus-steps pre-injection at the
   adopted anchor) — a deliberate dataset property that slightly compresses the natural tail
   the detectors see.
2. **Injected spikes may exceed 2× nominal** (allowed; per-bus budget measured at 0.0485 %
   worst-case, §4.5) — anomaly peaks are not clipped by the mapping.
3. **The voltage channel stops collapsing** (Vmin ≥ 0.89 at all times vs 0.698 today; no
   constant-PQ→constant-Z crossings). The current E3 detectors consume only bus P/Q features, so
   this changes nothing for them — it matters for Phase 7 residual features and any future
   voltage-derived detector.
4. **Absolute anomaly kW shrink by the anchor factor ≈ 3.1×** (bus means fall from 1.0× to
   0.3241× nominal; 1/0.3241 = 3.086 ≈ 3.1 — this is the single canonical figure; any earlier
   "3.2×" statement is superseded). If absolute
   magnitudes matter against sensor noise, implement the ADR-0004 §2.2 absolute floor (10 kW) —
   currently unimplemented — as planned in Stage B1.

### 4.8 Honest limitations

1. The feeder runs at **0.324× nominal** on average; the benchmark loading corresponds to the
   coincidence peak. E1's Light/Nominal/Heavy multiplier semantics change and are redefined in
   Stage B1 (median load, coincidence-peak step, 1.15× peak).
2. Households are still reused (64 slots / 25 homes); sharing a home correlates two buses
   (+0.228 mean correlation uplift). Dataset-limited, not fixable by mapping.
3. The 2.0× cap is a winsorization of the background (15 bus-steps at the adopted anchor) and is
   recorded in the mapping manifest.
4. 14 timesteps (α = 1.0) remain below 0.90 pu — inside the AC-2 budget but nonzero; min Vmin
   0.8927 is reported, not hidden.
5. All downstream artifacts (load_profiles, labels, E1/E2/E3, normalization params, README /
   PHASES status) require regeneration; run directories are never overwritten.
6. Only 25 real households exist; any claim of household-level realism is bounded by that
   inventory (documented in DATA_PROTOCOL.md in Stage B1).

---

## 5. Alternatives Rejected / Deferred

- **Option (i):** infeasible with 25 homes; revisit with a larger panel (≥ 64 homes for K=2).
- **Option (ii) offsets-only:** fails AC-3 by ~170×; offset machinery could be combined with
  re-anchoring later if cross-bus decorrelation is ever needed.
- **Per-bus anchoring** (`s_b = 1/p99.9(shape_b)`, each bus's own p99.9 = its nominal): passes
  AC-3 with zero clipping and per-bus max/nom ≤ 1.45, but loses feeder-level design-peak
  semantics (feeder p99.9 ≈ 0.74× nominal); deferred as a config variant of `anchor`.
- **α < 1 smoothing as primary:** unnecessary once the anchor is fixed (α = 1.0 already passes
  with margin); retained only as the pre-approved fallback.

---

## 6. Implementation Notes (Stage B1, after approval)

- `src/data/mapper.py`: parameters `anchor` ("mean" | "feeder_p999"), `alpha` (default 1.0),
  `cap_multiple` (default 2.0), and the balanced-assignment routine (seed 42, use counts
  14×3 + 11×2, pair-unique); write `anchor_scale`, `assignment_seed`, `home_use_counts`, and
  `cap_multiple` into `mapping_config.json`.
- `configs/data.yaml`: expose `mapping.anchor`, `mapping.alpha`, `mapping.cap_multiple`,
  `mapping.balanced: true`.
- Cap ordering: cap applies at **mapping** time (pre-injection); AC-3 is verified on the final
  injected series by the new integration test; violations are reported, criteria are never
  loosened.
- Regenerate `load_profiles.parquet` (+ `*_phys`), `anomaly_labels.parquet` (with the
  `realized_ratio_kw` fix and the §2.2 10 kW floor), `splits.json`, `normalization_params.json`;
  add the all-timestep convergence integration test; revalidate E1 with redefined scenarios.
- Update `docs/methodology/DATA_PROTOCOL.md` (mapping limitations: 25-home inventory, reuse,
  +0.228 shared-home correlation uplift, anchor and cap) and README limitation #4 (replacing the
  stale 17,946 kW / 0.6416 pu figures).

---

*Measurements 2026-09-30; formulas in this text reproduce every number from the processed
artifacts and the raw household matrix. No `src/` code was changed for this ADR.*
