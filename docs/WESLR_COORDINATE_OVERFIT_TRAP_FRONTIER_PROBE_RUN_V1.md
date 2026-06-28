# WESLR COORDINATE OVERFIT TRAP FRONTIER PROBE RUN V1

## 1. Executive verdict
`coordinate_overfit_trap_frontier_probe_run_confirmed_frontier_signal`

## 2. Scope and boundary
- **Synthetic-only**: `synthetic_only = true`
- **No public ARC/Kaggle**: `public_arc_used = false`, `kaggle_used = false`
- **No official claims**: `benchmark_claim_safe = false`
- **Solver unchanged**: `solver_behavior_changed = false`, `solver_primitives_added = false`
- **No .weslr**: confirmed
- **No external calls**: pure Python execution

## 3. Command and environment
```
python -c "import sys; sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean'); from weslr.arc_coordinate_overfit_probe import run_coordinate_overfit_trap_frontier_probe_v1; print(run_coordinate_overfit_trap_frontier_probe_v1())"
```
- **Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **HEAD at execution**: `beeaabcf92feb15dc18cedec7ff29b3661015fd9`
- **Deterministic**: Yes — fixed probe case ledger, no randomness.

## 4. Baseline reference
- **Baseline task exact rate**: `0.8611111111111112` (31/36)
- **Baseline packet exact rate**: `0.8541666666666666` (41/48)
- **Baseline remains separate**: yes — stored in `baseline_reference` dict, unchanged.

## 5. Coordinate-overfit run metrics
| Metric | Count | Rate |
|--------|-------|------|
| Attempted tasks | 6 | — |
| Task exact | 4 | 0.6666666666666666 |
| Task partial | 1 | 0.16666666666666666 |
| Task unsupported | 1 | 0.16666666666666666 |
| Task failed | 0 | 0.0 |
| Packet exact | 8 | 0.8 |
| Packet partial | 1 | 0.1 |
| Packet unsupported | 1 | 0.1 |
| **Coordinate-overfit suspected** | **2** | **0.3333333333333333** |
| **Coordinate bait failure** | **1** | **0.16666666666666666** |
| **Relation preservation success** | **4** | **0.6666666666666666** |

## 6. Frontier result
- **First stable coordinate-overfit frontier**: `null` (no tier with ≥2 failures in this small sample)
- **Hardest coordinate-overfit tier**: `2` (from `hardest_partial_tier`)
- **Hardest exact tier**: `4` (Tier 4 has exact successes)
- **Hardest partial tier**: `2` (Tier 2 has partial: `moved_anchor`)
- **Remaining partial families**: `["moved_anchor"]`
- **Remaining blocker families**: `["moved_anchor", "coordinate_bait_distractor"]`
- **Remaining unsupported families**: `["coordinate_bait_distractor"]`
- **Next recommended pressure family**: `moved_anchor`

## 7. Interpretation
The coordinate-overfit probe yields **66.67% exact** (4/6), which is **below the 85% baseline threshold**, confirming that the coordinate-overfit pressure exposes a meaningful frontier signal:

- **Coordinate-overfit suspected rate**: 33.33% (2/6 families flagged)
- **Coordinate bait failure rate**: 16.67% (1/6 families flagged)  
- **Relation preservation success rate**: 66.67% (4/6 families succeeded)

The presence of `moved_anchor` as both a partial family and the next recommended pressure target is notable — it shows the frozen solver partially handles relational shifts but breaks down under anchor relocation.

**This is not a solver-patching authorization.** The result confirms the probe is useful and should inform future probe design, not solver modification.

## 8. Recommended next safe local follow-up
`REVIEW_COORDINATE_OVERFIT_TRAP_FRONTIER_PROBE_RUN_V1`

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.