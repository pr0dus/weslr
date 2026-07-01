# ARC Synthetic 3‑Step Primitive Coverage – Batch 4 Review Report (V1)

**Repo:** `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch:** `occ-discovery-doctrine-implementation-20260613`
**Lane:** `REVIEW_ARC_SYNTHETIC_3_STEP_PRIMITIVE_COVERAGE_BATCH_4_IMPLEMENTATION_V1`

## 1. Staging status
- The implementation changes (`weslr/arc_synthetic_3_step_real_dispatch.py`) and the implementation report (`docs/WESLR_ARC_SYNTHETIC_3_STEP_PRIMITIVE_COVERAGE_BATCH_4_IMPLEMENTATION_V1.md`) are **staged** but **not yet committed**.

## 2. Current HEAD
- `git rev-parse HEAD` → `8f5af4ffd1f5b15d0a788a326539c159667f3e13`
- This matches the expected HEAD (`8f5af4ff`).

## 3. `normalize_position`
- Implements a real computation: finds connected components, selects the largest, computes centroid, normalizes by grid dimensions, and returns `norm_x`/`norm_y` trace fields. **Valid bounded arithmetic**.

## 4. `count_objects`
- Uses `_connected_components` to count components and returns `count`. **Real connected‑component counting**.

## 5. `place_back`
- Delegates to the existing Phase‑2 primitive `place_object_on_new_canvas` via `_apply_primitive_step`, preserving the adapter trace. **Real placement** (deterministic).

## 6. Optional placeholders
- Added a generic fallback that returns `{"primitive_id": name, "noop": True}` for any unmapped primitive.
- The task set includes the primitives `extract_boundary`, `mirror_object`, and `crop` which are **no‑op placeholders**, not real implementations.

## 7. Impact on scoring
- The pilot runner reports **20 exact** because the placeholder fallback marks those primitives as supported.
- Tasks using the placeholders are:
  - `F005_1`, `F005_2` (extract_boundary)
  - `F007_1`, `F007_2` (mirror_object)
  - `F008_1`, `F008_2` (crop)
- Since these primitives perform no meaningful work, counting them as *exact* inflates the score.

## 8. Scoring semantics
- The intended scoring model treats a task as **exact** only when each primitive yields a meaningful output/trace (i.e., real semantics, not a generic noop).
- Therefore, tasks that rely solely on the noop fallback should be **re‑classified** as *unsupported* (or *partial* if they produce some trace).

## 9. Re‑classification suggestion
- Re‑compute metrics with the six placeholder‑dependent tasks marked **unsupported**.
- Expected adjusted metrics:
  ```json
  {"exact": 14, "partial": 0, "unsupported": 6, "failed": 0, "represented_candidates": 8}
  ```

## 10. Verdict
- The implementation of the three priority primitives is sound and passes all validation suites.
- However, the current scoring **over‑credits** due to noop placeholders.
- **Verdict:** `accepted_but_score_needs_reclassification`

## 11. Diagnostic metadata separation
- The code keeps diagnostic fields (`diagnostic_expected_failure_categories`) separate from the solver result (`result`). No leakage observed.

## 12. Leakage flags
- All tasks assert `leakage_flags` are `False`. **Confirmed**.

## 13. Baselines
- No modifications to 2‑step or single‑step baselines were made. **Preserved**.

## 14. Recommended next lane
- After fixing the scoring (re‑classifying placeholder tasks) the logical next lane is still `DESIGN_WESLR_FIRST_CONTROLLED_REAL_EVIDENCE_DIRECTION_RUN_V1`.
- However, an intermediate **score‑audit / reclassification** lane could be introduced to formalize the metric adjustment before proceeding.

---
**Action items**
- Commit the implementation (already staged) and this review report.
- Adjust the scoring logic or test harness to treat the generic noop as *unsupported*.
- Re‑run the pilot to obtain the corrected metrics.
