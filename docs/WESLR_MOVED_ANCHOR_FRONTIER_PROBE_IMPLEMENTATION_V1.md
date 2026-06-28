# WESLR MOVED ANCHOR FRONTIER PROBE IMPLEMENTATION V1

## 1. Executive verdict
`moved_anchor_frontier_probe_implemented`

## 2. Implementation summary
- **Module**: `weslr/arc_moved_anchor_probe.py`
- **Public function**: `run_moved_anchor_frontier_probe_v1()`
- **Mode**: `moved_anchor_probe_v1`
- Returns a pure in-memory dictionary with standard ARC metrics, moved-anchor-specific metrics, and relation-first metadata.

## 3. Probe families implemented
All 8 synthetic families:
1. `anchor_translated_target_preserved` — Tier 2, exact
2. `anchor_moved_distractor_at_old_coord` — Tier 3, partial (bait)
3. `anchor_role_preserved_color_changed` — Tier 4, exact
4. `anchor_role_preserved_shape_changed` — Tier 4, exact
5. `multiple_anchors_one_valid` — Tier 4, partial (disambiguation)
6. `anchor_moved_near_boundary` — Tier 3, partial (edge effects)
7. `anchor_moved_offset_constant` — Tier 2, exact
8. `anchor_absent_ambiguous` — Tier 5, unsupported (safe failure)

## 4. Metric and frontier surface
- **Standard metrics**: task exact/partial/unsupported/failed counts and rates; packet metrics.
- **Moved-anchor specific metrics**:
  - `moved_anchor_failure_count` / `rate`
  - `old_anchor_coordinate_bait_count` / `rate`
  - `anchor_role_preservation_success_count` / `rate`
  - `ambiguous_anchor_safe_failure_count` / `rate`
- **Frontier fields**: `first_stable_moved_anchor_frontier`, `hardest_moved_anchor_tier`, `next_recommended_pressure_family`

## 5. Relation-first connection
- Metadata fields present:
  - `coordinate_form_example`: `"anchor_at(old_x, old_y) → target_offset"`
  - `relational_form_example`: `"anchor_role(anchor_id) → target_offset"`
  - `relation_first_poc_candidate`: boolean (True if moved_anchor_failure_count > 0)
  - `rewrite_outcome_options`: list of possible rewrite outcomes
- **No compiler behavior implemented** — pure metadata for future POC design.

## 6. Baseline/coordinate-probe separation
- `baseline_reference` contains unchanged baseline Smoke V2 metrics.
- `coordinate_probe_reference_present = True` flag indicates coordinate-overfit probe data is accessible separately.
- No mutation of baseline or coordinate-overfit probe outputs.

## 7. Solver freeze review
- `solver_behavior_changed = False`
- `solver_primitives_added = False`
- No depth-3, no retry fill, no patching.

## 8. Boundary review
- `synthetic_only = True`
- `public_arc_used = False`
- `kaggle_used = False`
- `benchmark_claim_safe = False`
- No `.weslr`, no external calls, protected files unchanged.

## 9. Test summary
- **14 moved-anchor tests passed**
- Existing tests still pass:
  - 9 coordinate-overfit tests
  - 6 difficulty-probe tests
  - 8 smoke-metrics tests
- **Total: 37 tests passed**

## 10. Recommended next safe local follow-up
`REVIEW_MOVED_ANCHOR_FRONTIER_PROBE_IMPLEMENTATION_V1`

---
All validation gates pass; protected files unchanged; `.weslr` untouched; push avoided.