# WESLR ARC Reflect Synthetic Suite Support Integration V1

- Dispatch: `INTEGRATE_REFLECT_PRIMITIVE_INTO_SYNTHETIC_SUITE_SUPPORT_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `6df40cf6`
- Previous report: `docs/WESLR_ARC_REFLECT_GUARDRAIL_PRESERVING_INTEGRATION_BOUNDARY_V1.md`
- Handoff note: `WESLR_CURRENT_HANDOFF.md` still points at stale verified HEAD `9ed508db...`; this lane followed the operator-requested live repo state at `6df40cf6`.

## 1. Executive verdict

Reflect has now been integrated into the **synthetic suite support path only**.

What changed:
- `reflect_object_horizontal_or_vertical` was added to `SUPPORTED_SYNTHETIC_FAMILIES_V1`
- no dry-run reflect inference/ranking logic was changed
- no copy/rotate/object-count repair work was mixed in
- reflect-specific stale unsupported labeling was removed implicitly by enabling the family in the support classification path

Result:
- reflect moved from suite-blocked unsupported to supported/exact where executable in full-metadata and `toy_task_type`-preserved modes
- canonical 120 improved materially from `102/120 exact` to `109/120 exact`
- non-reflect family counts stayed unchanged
- leakage boundaries stayed intact

## 2. Root cause of reflect unsupported status

The root cause was support classification, not absent reflect inference.

Before this lane:
- dry-run inference already selected `reflect_object_horizontal_or_vertical`
- dry-run already reached `train_fit_status = fit`
- synthetic suite already had a local padding-aware reflect execution branch
- but `weslr/arc_style_synthetic_solver_suite.py` left reflect outside `SUPPORTED_SYNTHETIC_FAMILIES_V1`

That caused:
- family classification = `unsupported_transformation_family`
- packet status = `unsupported`
- stale `missing_primitive_executor` failure labeling even though reflect execution logic existed locally in the suite path

## 3. Integration change

Touched implementation:
- `weslr/arc_style_synthetic_solver_suite.py`
  - added `reflect_object_horizontal_or_vertical` to `SUPPORTED_SYNTHETIC_FAMILIES_V1`

Touched tests:
- `weslr/tests/test_arc_style_synthetic_solver_suite_v1.py`
- `weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`
- `weslr/tests/test_arc_style_grid_adapter_phase2_v1.py`

Not changed:
- no edits to `weslr/arc_style_grid_solver_dry_run.py`
- no support-list changes outside the synthetic suite support path
- no rotate/copy ranking changes
- no candidate_output_surface/replay/scoring/final-answer behavior

## 4. Reflect before/after

### Before
Canonical 120 reflect family:
- exact: `0`
- partial: `0`
- unsupported: `10`
- failed: `0`

Mode split before:
- full metadata: `0 exact / 4 unsupported`
- `toy_task_type` preserved only: `0 exact / 3 unsupported`
- fully stripped: `0 exact / 3 unsupported`

### After
Canonical 120 reflect family:
- exact: `7`
- partial: `3`
- unsupported: `0`
- failed: `0`

Mode split after:
- full metadata: `4 exact / 0 partial / 0 unsupported`
- `toy_task_type` preserved only: `3 exact / 0 partial / 0 unsupported`
- fully stripped: `0 exact / 3 partial / 0 unsupported`

Interpretation:
- reflect now succeeds where the family guardrail is preserved
- fully stripped remains lower-bound only and still degrades reflect into partial outcomes

## 5. Canonical 120 before/after

### Before
- exact: `102`
- partial: `8`
- unsupported: `10`
- failed: `0`
- exact %: `85.0%`

### After
- exact: `109`
- partial: `11`
- unsupported: `0`
- failed: `0`
- exact %: `90.8%`

Delta:
- exact: `+7`
- partial: `+3`
- unsupported: `-10`
- failed: `0`

Important interpretation:
- this is a synthetic diagnostic improvement only
- it is not a public capability claim and not ARC-AGI-2 evidence

## 6. Guardrail-preserved stripped before/after

Primary stripped baseline remains `toy_task_type_preserved_only`.

### Before
- `32 exact / 1 partial / 3 unsupported / 0 failed`
- exact %: `88.9%`

### After
- `35 exact / 1 partial / 0 unsupported / 0 failed`
- exact %: `97.2%`

Interpretation:
- guardrail-preserving stripped reflect packets now convert to exact
- this confirms the verified doctrine: `toy_task_type` remains the main stripped attribution baseline

## 7. Fully stripped lower-bound before/after

### Before
- `29 exact / 4 partial / 3 unsupported / 0 failed`
- exact %: `80.6%`

### After
- `29 exact / 7 partial / 0 unsupported / 0 failed`
- exact %: `80.6%`

Interpretation:
- fully stripped did **not** improve exactness
- reflect rows moved from unsupported to partial, not exact
- this is exactly why fully stripped remains a lower-bound stress diagnostic rather than the main baseline

Optional shuffled/renamed:
- before: `32 exact / 1 partial / 3 unsupported / 0 failed`
- after: `35 exact / 1 partial / 0 unsupported / 0 failed`

## 8. Non-reflect regression check

Non-reflect canonical family summaries remained unchanged:
- `copy_grid`: before `6 exact / 4 partial / 0 unsupported` -> after `6 exact / 4 partial / 0 unsupported`
- `object_count_to_pattern`: before `9 exact / 1 partial / 0 unsupported` -> after `9 exact / 1 partial / 0 unsupported`
- `rotate_object_90`: before `7 exact / 3 partial / 0 unsupported` -> after `7 exact / 3 partial / 0 unsupported`

Full-metadata synthetic suite remained non-reflect stable as well:
- `copy_grid`: unchanged at `2 exact / 2 partial`
- `object_count_to_pattern`: unchanged at `3 exact / 1 partial`
- `rotate_object_90`: unchanged at `4 exact / 0 partial`

Judgment:
- no non-reflect regressions observed

## 9. Failure-label cleanup

Before this lane, reflect rows carried stale blocked-support labels:
- `unsupported_transformation_family`
- `missing_primitive_executor`

After reflect entered the supported family set:
- reflect no longer appears in unsupported family summary
- synthetic suite unsupported count dropped to `0`
- reflect no longer receives stale `missing_primitive_executor` labeling in supported modes

This cleanup happened without broad failure-ledger redesign because the stale labels were emitted only on the unsupported-family branch.

## 10. Expected-output leakage check

Leakage and attribution boundaries remained intact.

Observed runner flags after integration:
- `uses_test_output = false`
- `uses_task_id_for_candidate_selection = false`
- `uses_notes_for_candidate_selection = false`
- `lookup_table_detected = false`

Observed leakage flags after integration:
- `synthetic_only = true`
- `uses_kaggle_data = false`
- `uses_arc_public_data = false`
- `uses_hidden_private_data = false`
- `uses_solution_file = false`
- `uses_answer_key = false`
- `uses_test_output_for_candidate_generation = false`
- `official_score_claim = false`

Judgment:
- expected-output leakage remained avoided

## 11. Boundary preservation

Preserved boundaries:
- reflect exact-family promotion still depends on `task_type == "reflect_object_horizontal_or_vertical"`
- no dry-run ranking or family-competition logic was changed
- `toy_task_type_preserved_only` remains the primary stripped guardrail baseline
- fully stripped remains lower-bound only
- no copy-grid repair
- no object-count repair
- no stripped-rotate repair
- no candidate_output_surface/replay/scoring/final-answer behavior
- no `.weslr` access
- no protected runtime/chat file edits

## 12. Remaining limitations

1. Fully stripped reflect remains partial, not exact.
   - this is expected under the verified stripped doctrine
   - it should not be used as the main reflect baseline

2. Adapter/suite reflect semantics are now better covered by tests, but the lane still does **not** claim broad reflect completeness beyond this synthetic support surface.

3. Existing non-reflect pockets remain unresolved by design:
   - `copy_grid` partial pocket
   - `object_count_to_pattern` partial pocket
   - stripped `rotate_object_90` degradation pocket

4. This lane improves synthetic support classification only.
   - it does not create public benchmark authority
   - it does not imply hidden-benchmark readiness

## 13. Recommended next lane

Recommended next lane:
- `REPAIR_ARC_SYNTHETIC_COPY_GRID_VARIANT_2_AND_STRIPPED_ROTATE_METADATA_DEPENDENCY_V1`

Reason:
- reflect support is now integrated cleanly
- the remaining reproducible non-reflect pockets are still the main unresolved diagnostic issues
- keeping those separate preserves attribution clarity and prevents score inflation by mixing fixes
