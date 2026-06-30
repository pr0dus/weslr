# WESLR ARC Reflect Guardrail-Preserving Integration Boundary V1

- Dispatch: `DESIGN_ARC_REFLECT_GUARDRAIL_PRESERVING_INTEGRATION_BOUNDARY_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `b7976a43`
- Previous reports:
  - `docs/WESLR_ARC_SYNTHETIC_120_DIAGNOSTIC_RUNNER_V1.md`
  - `docs/WESLR_ARC_STRIPPED_GUARDRAIL_DEFINITION_V1.md`
- Handoff note: `WESLR_CURRENT_HANDOFF.md` still points at stale verified HEAD `9ed508db...`; this design followed the operator-requested live repo state at `b7976a43`.

## 1. Executive verdict

Reflect integration into the synthetic suite support path appears **narrowly designable and likely safe**, but only if it is treated as a support-classification lane, not as a general solver repair lane.

Observed current state:
- reflect dry-run inference already exists
- reflect dry-run selected primitive already reaches `reflect_object_horizontal_or_vertical`
- reflect dry-run reaches `train_fit_status = fit`
- synthetic suite execution logic already has a reflect executor path
- reflect remains blocked mainly by **suite-level support classification**, not by total absence of reflect handling

Design conclusion:
- the narrow implementation lane should primarily enable reflect as a supported synthetic family and prove that no non-reflect ranking/regression is introduced
- `toy_task_type_preserved_only` must remain the primary stripped attribution baseline
- the fully stripped cohort must remain a lower-bound stress diagnostic only

Important caveat:
- there is a semantic mismatch between the **synthetic suite/local executor path**, which uses padding-aware reflect execution, and the **phase2 adapter validation/toy-candidate path**, which still uses bbox reflection in some reflect branches
- because this lane is design-only, that mismatch is recorded as a risk, not repaired here

## 2. Current reflect inference path

### 2.1 Dry-run structural inference

Reflect is currently inferred in:
- `weslr/arc_style_grid_solver_dry_run.py`
  - `_infer_reflect_object_parameters(...)`
  - `_infer_pair_structural_candidate_v1(...)`
  - `infer_arc_style_primitive_candidates_from_grid_delta_v1(...)`

Exact current path:
1. `_infer_pair_structural_candidate_v1(...)` checks reflect after object-count and before rotate-object.
2. `_infer_reflect_object_parameters(...)`:
   - infers `object_value` from dominant non-background value
   - gathers object cells
   - tries **padding-aware reflection first** via `_reflect_object_grid_with_padding(...)`
   - falls back to bbox reflection via `_reflect_bbox_grid(...)`
3. If either path matches train output exactly, it returns:
   - `axis`
   - `object_value`
   - `background_value`
4. `_infer_pair_structural_candidate_v1(...)` then emits:
   - `primitive_id = "reflect_object_horizontal_or_vertical"`
   - `candidate_role = "primary_exact"`
   - `required_constraints = ["axis_known", "single_object_known"]`
   - `train_fit_status = "fit"`
5. `infer_arc_style_primitive_candidates_from_grid_delta_v1(...)` keeps that exact family only when:
   - all train-pair exact inferences agree, and
   - `task_type == "reflect_object_horizontal_or_vertical"`

This is the current guardrail that prevents reflect from being silently reused for unrelated families.

### 2.2 Synthetic suite executor path

Reflect execution already exists in:
- `weslr/arc_style_synthetic_solver_suite.py`
  - reflect branch inside the suite-local primitive application helper

Observed behavior:
- if `primitive_id == "reflect_object_horizontal_or_vertical"`
- the suite-local executor:
  - infers/uses `background_value`
  - infers/uses `object_value`
  - reads `axis`
  - applies **padding-aware** `_reflect_object_grid_with_padding(...)`

This means the synthetic suite already knows how to execute reflect once it chooses to treat the family as supported.

### 2.3 Existing dry-run test evidence

Current direct evidence exists in:
- `weslr/tests/test_arc_style_grid_solver_dry_run_v1.py`
  - `test_reflect_object_family_is_inferred_in_dry_run_even_though_suite_level_support_remains_blocked`

That test currently proves:
- selected primitive is `reflect_object_horizontal_or_vertical`
- `train_fit_status == "fit"`
- `selected_unsupported_count == 0`

## 3. Current unsupported classification path

Reflect is currently blocked as unsupported in:
- `weslr/arc_style_synthetic_solver_suite.py`

Exact blocking points:

### 3.1 Supported family list
- `SUPPORTED_SYNTHETIC_FAMILIES_V1`
- reflect is **not present** in that set

### 3.2 Family support classification
- `_family_support_classification(family_id)`
- returns `"unsupported_transformation_family"` when the family is not in `SUPPORTED_SYNTHETIC_FAMILIES_V1`

### 3.3 Packet-result status assignment
- `_build_packet_result(...)`
- computes:
  - `supported_family = family_id in SUPPORTED_SYNTHETIC_FAMILIES_V1`
  - `top1_unsupported = not supported_family`
  - `packet_status = "unsupported"` if unsupported family
- for unsupported family, it records:
  - `unsupported_transformation_family`
  - `missing_primitive_executor`

Important nuance:
- the current `missing_primitive_executor` label is attached whenever the family is unsupported, even if a local reflect executor exists in the suite path
- for reflect, this is currently an **honesty-preserving blocked-support label**, not proof that no executor code exists anywhere

### 3.4 Current suite-level test expectation
Current unsupported classification is reinforced by:
- `weslr/tests/test_arc_style_synthetic_solver_suite_v1.py`
  - `test_solver_suite_records_unsupported_families_honestly`
- this test currently expects:
  - unsupported family counts remain non-zero
  - `reflect_object_horizontal_or_vertical` appears in unsupported families

## 4. Required implementation touchpoints

The narrow expected implementation lane should touch these files/functions only.

### 4.1 Required core touchpoints

1. `weslr/arc_style_synthetic_solver_suite.py`
   - `SUPPORTED_SYNTHETIC_FAMILIES_V1`
   - `_family_support_classification(...)`
   - `_build_packet_result(...)` only if failure labeling needs to stay semantically precise after reflect support is enabled

2. `weslr/tests/test_arc_style_synthetic_solver_suite_v1.py`
   - update unsupported-family assertions so reflect is no longer required to remain unsupported
   - add reflect-supported expectations

3. `weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`
   - add exact expectations for reflect family after support enablement
   - add no-regression expectations for non-reflect families and counts

4. `weslr/tests/test_arc_style_grid_solver_dry_run_v1.py`
   - likely no behavioral change required
   - retain current proof that reflect dry-run inference was already present before suite support enablement

### 4.2 Optional hardening touchpoints

These are **not required** for the narrow support-classification lane, but they are the main places where semantic consistency risk lives:

5. `weslr/arc_style_grid_adapter_phase2.py`
   - reflect branch in `validate_arc_style_train_pair_with_candidate_v1(...)` execution path
   - reflect branch in `_infer_candidate_for_toy_task(...)`

Why optional-only:
- the synthetic suite already executes reflect with padding-aware logic locally
- but phase2 adapter reflect validation currently uses bbox reflection in some paths
- if implementation wants a single reflect semantic across all synthetic reflect surfaces, these should be aligned deliberately in a follow-up or explicitly included in the integration lane with narrow tests

### 4.3 No other files should be in scope

Do **not** mix into reflect lane:
- `copy_grid` repairs
- `object_count_to_pattern` repairs
- stripped `rotate_object_90` repairs
- candidate_output_surface wiring
- replay/scoring/final-answer work
- ARC-AGI-2 participation claims

## 5. Guardrail preservation requirements

Reflect integration must preserve the verified stripped-mode doctrine.

### 5.1 Primary stripped attribution baseline
Must keep:
- `toy_task_type_preserved_only` as the primary stripped guardrail baseline

Reason:
- `toy_task_type` is a valid guardrail signal
- it constrains blueprint/family selection without exposing expected test output
- it preserves attribution clarity better than richer generator metadata

### 5.2 Lower-bound stress cohort
Must keep:
- `fully_stripped_train_pairs_plus_test_input_only` as lower-bound only

Reason:
- it strips family-specific `toy_task_type`
- it should not become the main reflect baseline for integration claims

### 5.3 Reflect-specific family isolation
Must preserve current family isolation in dry-run inference:
- reflect exact-family promotion should still require `task_type == "reflect_object_horizontal_or_vertical"`
- reflect enablement must not make reflect compete for unrelated families

### 5.4 No leakage expansion
Must preserve:
- `uses_test_output = false`
- `uses_task_id_for_candidate_selection = false`
- `uses_notes_for_candidate_selection = false`
- `lookup_table_detected = false`
- no expected-output injection into solver generation

## 6. Attribution baseline

Before implementation:
- canonical 120 reflect family = `0 exact / 10 unsupported`
- full metadata reflect rows infer reflect but are suite-blocked unsupported
- toy-task-type-preserved reflect rows infer reflect but are suite-blocked unsupported
- fully stripped reflect rows degrade further and are lower-bound only

Success after implementation should mean:

### 6.1 Reflect family success
At minimum:
- reflect full-metadata packets become exact rather than unsupported
- reflect `toy_task_type_preserved_only` packets become exact rather than unsupported
- reflect family no longer appears in unsupported-family summary

### 6.2 Canonical 120 success
At minimum:
- canonical total should improve by the number of reflect packets converted from unsupported to exact
- if all currently blocked reflect rows convert cleanly, the expected directional change is:
  - exact increases
  - unsupported decreases
  - failed stays zero
- no public score claim should be made from that increase

### 6.3 Non-reflect no-regression rule
Must hold:
- no change in `copy_grid` counts
- no change in `object_count_to_pattern` mismatch pocket
- no change in stripped `rotate_object_90` degradation pocket
- no new regressions in line completion, complete symmetry, or rotate ranking

### 6.4 Guardrail baseline success
Must hold:
- `toy_task_type_preserved_only` remains the primary stripped baseline in the diagnostic runner/reporting
- shuffled/renamed parity should remain a useful anti-spurious-metadata signal

## 7. Tests required

Required tests before or during implementation:

### 7.1 Synthetic suite support tests
1. Update `weslr/tests/test_arc_style_synthetic_solver_suite_v1.py`
   - reflect should no longer be required in unsupported families
   - suite exact/unsupported counts should be re-asserted with reflect-specific expectations

2. Add explicit reflect family supported test
   - prove reflect family packet results become exact
   - prove no reflect packet remains unsupported in supported modes

### 7.2 Diagnostic runner tests
3. Update/add `weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`
   - assert reflect family summary moves from unsupported to exact for full metadata
   - assert reflect family also converts under `toy_task_type_preserved_only`
   - keep fully stripped expectations separate as lower-bound stress behavior

4. Add no-regression snapshot-style assertions for non-reflect families
   - `copy_grid` still unchanged
   - `object_count_to_pattern` still unchanged
   - stripped `rotate_object_90` still unchanged

### 7.3 Dry-run inference retention tests
5. Keep existing dry-run reflect inference test
   - ensures suite support enablement is not confused with inference creation

### 7.4 Executor semantic tests
6. Expand reflect executor coverage in `weslr/tests/test_arc_style_grid_adapter_phase2_v1.py`
   - horizontal direct custom case
   - vertical direct custom case
   - padding-aware shape case
   - malformed input / missing object fail-closed case

Reason:
- today there is direct coverage for a horizontal case
- there is not yet enough explicit proof for vertical + padding-aware + malformed fail-closed coverage at the adapter/test layer

### 7.5 Validation gates
Must pass unchanged:
- `python3 weslr/tests/release_gate_v1.py`
- `git diff --check`
- `bash scripts/weslr_release_check.sh`
- `bash scripts/chat_weslr_de_health_check.sh --mode source-repo`

## 8. Non-goals

This reflect boundary lane must explicitly exclude:
- implementing reflect itself in this design lane
- changing dry-run solver ranking for copy/rotate families
- repairing `copy_grid`
- repairing `object_count_to_pattern`
- repairing stripped `rotate_object_90`
- adding candidate_output_surface
- adding replay/scoring/final-answer behavior
- touching ARC-AGI-2 participation
- touching `.weslr`
- editing protected runtime/chat files

## 9. Risk register

### Risk 1 — false capability inflation
Cause:
- treating reflect support enablement as if it proved broader ARC readiness
Mitigation:
- keep report wording synthetic-only and diagnostic-only
- no public score language

### Risk 2 — hidden executor semantic mismatch
Cause:
- synthetic suite uses padding-aware reflect, but some phase2 adapter reflect paths still use bbox reflect
Mitigation:
- either explicitly scope implementation to suite support only, or add narrow adapter alignment tests before claiming semantic uniformity

### Risk 3 — reflect starts competing with rotate/copy
Cause:
- touching dry-run ranking or family gating instead of only support classification
Mitigation:
- leave dry-run ranking logic unchanged
- preserve `task_type == reflect_object_horizontal_or_vertical` guard
- add no-regression assertions for copy/rotate counts and selected primitives

### Risk 4 — stripped-baseline confusion
Cause:
- reporting fully stripped as the primary baseline after reflect support
Mitigation:
- keep `toy_task_type_preserved_only` as the main stripped baseline
- explicitly label fully stripped as lower-bound only

### Risk 5 — misleading failure labels
Cause:
- leaving `missing_primitive_executor` language semantically stale after reflect becomes supported
Mitigation:
- review reflect-related failure labeling in `_build_packet_result(...)` during implementation
- ensure any remaining missing-executor label reflects reality

### Risk 6 — malformed-input overclaim
Cause:
- assuming reflect executor is proven safe on malformed/object-missing inputs without explicit tests
Mitigation:
- add fail-closed tests before calling reflect support hardened

## 10. Recommended implementation prompt

Recommended next lane:
- `INTEGRATE_REFLECT_PRIMITIVE_INTO_SYNTHETIC_SUITE_SUPPORT_V1`

Recommended implementation prompt:

> Integrate `reflect_object_horizontal_or_vertical` into the synthetic suite support path only.
>
> Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
> Branch: `occ-discovery-doctrine-implementation-20260613`
> Start HEAD: `b7976a43`
>
> Scope:
> - enable reflect as a supported synthetic family in the synthetic suite path
> - keep dry-run inference logic unchanged unless a narrow semantic bug is proven
> - preserve `toy_task_type_preserved_only` as the primary stripped guardrail baseline
> - keep fully stripped as lower-bound only
> - add reflect-supported tests and no-regression checks for non-reflect families
> - review reflect-related failure labeling so it remains honest after support enablement
>
> Do not:
> - repair copy_grid
> - repair object_count_to_pattern
> - repair stripped rotate
> - add candidate_output_surface, replay, scoring, or final-answer behavior
> - touch ARC-AGI-2 participation or `.weslr`
>
> Required success:
> - reflect full-metadata rows become exact rather than unsupported
> - reflect toy_task_type-preserved rows become exact rather than unsupported
> - no non-reflect regressions
> - validation passes

Final design judgment:
- reflect inference path identified: **yes**
- reflect unsupported block identified: **yes**
- narrow safe implementation lane exists: **yes, with guardrail and regression constraints**
