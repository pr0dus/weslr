# WESLR MOVED ANCHOR FRONTIER PROBE RUN V1

## 1. Executive verdict
`moved_anchor_frontier_probe_run_confirmed_frontier_signal`

The run confirms a strong moved-anchor signal (50% exact, 50% failure rate), confirming the frozen solver struggles with anchor identity/role tracking across location changes.

## 2. Scope and boundary
- **Synthetic-only**: `synthetic_only = true`
- **No public ARC/Kaggle**: `public_arc_used = false`, `kaggle_used = false`
- **No official claims**: `benchmark_claim_safe = false`
- **Solver unchanged**: `solver_behavior_changed = false`, `solver_primitives_added = false`
- **No .weslr**: confirmed
- **No external calls**: pure Python execution

## 3. Command and environment
```
python -c "import sys; sys.path.append('/data/data/com.termux/files/home/weslr-pr47-clean'); from weslr.arc_moved_anchor_probe import run_moved_anchor_frontier_probe_v1; print(run_moved_anchor_frontier_probe_v1())"
```
- **Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **HEAD at execution**: `ea0064e52eba3aed49249c778e75fe7714673a9c`

## 4. Baseline/coordinate reference
- **Baseline task exact rate**: `0.8611111111111112` (31/36) — unchanged
- **Coordinate-probe reference**: Available via `coordinate_probe_reference_present = true`
- Both references remain separate.

## 5. Moved-anchor run metrics
| Metric | Count | Rate |
|--------|-------|------|
| Attempted tasks | 8 | — |
| Task exact | 4 | 0.5 |
| Task partial | 3 | 0.375 |
| Task unsupported | 1 | 0.125 |
| Task failed | 0 | 0.0 |
| **Moved-anchor failure** | **4** | **0.5** |
| **Old-anchor coordinate bait** | **1** | **0.125** |
| **Anchor-role preservation success** | **4** | **0.5** |
| **Ambiguous-anchor safe failure** | **1** | **0.125** |

## 6. Frontier result
- **First stable moved-anchor frontier**: Tier 3 (`adversarial_distractor_heavy`)
- **Hardest moved-anchor tier**: 5 (`unknown_engine_frontier`)
- **Hardest exact tier**: 4
- **Hardest partial tier**: 4
- **Remaining partial families**: `anchor_moved_distractor_at_old_coord`, `multiple_anchors_one_valid`, `anchor_moved_near_boundary`
- **Remaining blocker families**: 4 families including `anchor_absent_ambiguous`
- **Next recommended pressure family**: `anchor_moved_distractor_at_old_coord`

## 7. Relation-first POC signal
- **relation_first_poc_candidate**: `true`
- **coordinate_form_example**: `anchor_at(old_x, old_y) → target_offset`
- **relational_form_example**: `anchor_role(anchor_id) → target_offset`
- **rewrite_outcome_options**: `full_rewrite`, `partial_rewrite`, `irreducible_coordinate_dependency`, `unsafe_prediction`

The result confirms the moved-anchor probe exposes a genuine weakness that could benefit from a manual relation-first rewrite strategy.

## 8. Interpretation
- **50% exact rate** (4/8) is well below the baseline 85%, confirming a strong moved-anchor signal.
- **50% moved_anchor_failure_rate** directly confirms the frozen solver struggles with anchor identity tracking.
- **12.5% old_anchor_coordinate_bait** specifically confirms coordinate bait is a real failure mode.
- **This does NOT authorize solver patching** — the result confirms the probe is a useful signal for future relation-first compiler POC design.

## 9. Recommended next safe local follow-up
`REVIEW_MOVED_ANCHOR_FRONTIER_PROBE_RUN_V1`

Rationale:
- Run confirmed strong moved-anchor signal.
- Relation-first POC candidate = true.
- A narrow review lane should assess whether to proceed with a manual relation-first compiler POC design or expand the moved-anchor probe cases first.

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.