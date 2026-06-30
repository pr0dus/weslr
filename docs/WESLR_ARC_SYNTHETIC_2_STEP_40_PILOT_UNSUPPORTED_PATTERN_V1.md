# WESLR ARC Synthetic 2-Step 40 Pilot Unsupported Pattern V1

## 1. Executive verdict

Diagnostic verdict for `DIAGNOSE_ARC_SYNTHETIC_2_STEP_40_PILOT_UNSUPPORTED_PATTERN_V1`:
- the canonical 2-step 40 pilot remains `0 exact / 0 partial / 40 unsupported / 0 failed`
- the dominant unsupported cause is **absence of represented 2-step candidate sequences**, not runner instability
- the present bounded solver surface still evaluates effectively as a **single-step candidate selector** for this pilot
- failure mass is then concentrated into:
  - `parameter_inference_failure`: `22`
  - `ambiguous_train_evidence`: `9`
  - `one_primitive_missing`: `9`
- no evidence was found that the pilot runner itself changed status relative to the approved baseline

This lane is therefore closed as a **diagnosis-only lane**. No solver, generator, task, scoring, replay, final-answer, alias, ARC-AGI, `.weslr`, or protected runtime/chat changes were made.

## 2. Approved execution state for this lane

Approved live repo state used for this diagnosis:
- repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- branch: `occ-discovery-doctrine-implementation-20260613`
- start HEAD: `486ffd7436d8fe6b42057fae408150b9fd05f5eb`

## 3. Handoff mismatch note

`WESLR_CURRENT_HANDOFF.md` reported verified HEAD `9ed508dbdc7899774c7ca19e932a04c3842f584d`, which did not match the approved live repo HEAD for this lane.

Per explicit operator instruction for this lane only:
- the handoff verified HEAD was treated as stale
- diagnosis proceeded only on live HEAD `486ffd7436d8fe6b42057fae408150b9fd05f5eb`
- `WESLR_CURRENT_HANDOFF.md` was **not** updated in this lane

Recommended follow-up after this lane:
- `RECONCILE_WESLR_CURRENT_HANDOFF_TO_LIVE_HEAD_V1`

## 4. Canonical pilot confirmation

Canonical pilot result confirmed directly from `run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()`:
- exact: `0`
- partial: `0`
- unsupported: `40`
- failed: `0`

This matches the earlier pilot runner report and confirms that the unsupported diagnosis was performed against the same canonical baseline, not a changed runner state.

## 5. Sampled rows inspected

The following representative rows were re-inspected from the canonical pilot evaluation set:
- `pilot_2_step_easy_01_remove_noise_then_extract_v1`
- `pilot_2_step_easy_04_move_then_border_v1`
- `pilot_2_step_easy_08_fill_then_line_v1`
- `pilot_2_step_medium_03_rotate_then_reflect_v1`
- `pilot_2_step_stress_03_rotate_then_move_v1`
- `pilot_2_step_stress_08_fill_then_count_v1`

Observed canonical row facts:

| source_task_id | composition_pair | packet_status | train_fit_status | selected primitive sequence | failure category | note |
|---|---|---:|---:|---|---|---|
| `pilot_2_step_easy_01_remove_noise_then_extract_v1` | `remove_background_noise -> extract_largest_object` | `unsupported` | `unsupported` | `rotate(angle=90)` | `parameter_inference_failure` | wrong single-step family selected |
| `pilot_2_step_easy_04_move_then_border_v1` | `move_single_object -> border_frame` | `unsupported` | `unsupported` | `rotate(angle=90)` | `parameter_inference_failure` | both isolated steps can fit, but canonical row still unsupported |
| `pilot_2_step_easy_08_fill_then_line_v1` | `fill_region -> line_completion` | `unsupported` | `fit` | `fill_region(fill_value=4,border_value=3)` | `one_primitive_missing` | single-step fit exists, but canonical row still unsupported |
| `pilot_2_step_medium_03_rotate_then_reflect_v1` | `rotate_object_90 -> reflect_object_horizontal_or_vertical` | `unsupported` | `unsupported` | `rotate(angle=90)` | `parameter_inference_failure` | geometric family remains single-step-bound |
| `pilot_2_step_stress_03_rotate_then_move_v1` | `rotate_object_90 -> move_single_object` | `unsupported` | `unsupported` | `rotate(angle=90)` | `ambiguous_train_evidence` | order-sensitive pair not represented |
| `pilot_2_step_stress_08_fill_then_count_v1` | `fill_region -> object_count_to_pattern` | `unsupported` | `unsupported` | `rotate(angle=90)` | `ambiguous_train_evidence` | no represented 2-step path |

## 6. Clarification of the earlier inconsistency

The earlier diagnosis wording was too loose and should be corrected.

Correct interpretation:
1. the canonical pilot baseline remains `0 exact / 0 partial / 40 unsupported / 0 failed`
2. `pilot_2_step_easy_04_move_then_border_v1` was **not** a canonical fit; only its isolated step-1 and step-2 probes fit when evaluated separately outside the canonical pilot row
3. `pilot_2_step_easy_08_fill_then_line_v1` showed `train_fit_status = fit` for a selected single-step candidate, but its canonical `packet_status` still remained **unsupported**, so it still counts inside the 40 unsupported rows
4. therefore the prior wording suggesting two sampled rows had overall canonical fit status was wrong and should not be used as lane evidence

Short version:
- these were **internal supporting observations about isolated step behavior or train-fit**, not canonical pilot successes
- no canonical status change was found
- the table wording needed correction

## 7. Primary unsupported cause

### Primary cause
The primary unsupported cause is:
- **no represented executable 2-step candidate sequence is present in the evaluated candidate set**

### Why that is the main cause
Observed diagnosis pattern:
- sampled rows consistently selected single-step candidates such as `rotate(angle=90)` or `fill_region(...)`
- no sampled row exposed an intended ordered pair in the selected candidate sequence
- unsupported mass is therefore explained first by missing represented composition, then secondarily by parameter or ambiguity issues inside the fallback single-step surface

## 8. Sequence search / executor / intermediate-state findings

### Sequence search present?
**No** in the sense required for this pilot.

Reason:
- the current diagnostic evidence shows no effective search across represented two-step primitive sequences in the candidate surface actually used by the pilot
- candidate selection remains operationally single-step for the unsupported sample rows

### 2-step executor present?
**No** as an active canonical pilot mechanism.

Reason:
- the pilot does not surface an executed intended two-step primitive sequence in the unsupported rows
- the diagnosis found no evidence that a represented two-step candidate is being carried through canonical evaluation as the decisive path

### Intermediate-state evaluation present?
**No** in canonical pilot evaluation.

Reason:
- the lane required diagnosis only, and the canonical pilot rows do not include explicit intermediate-state scoring/evaluation fields
- isolated step probes can be constructed manually for diagnosis, but they are external diagnostic checks, not built-in canonical intermediate-state evaluation

## 9. Minimum mechanism needed before solver-side repair work can be evaluated meaningfully

Minimum mechanism needed:
- **represented bounded 2-step candidate generation plus explicit intermediate-state evaluation of step-1 and step-2 fit**

Why this is the minimum:
- without represented 2-step candidates, the pilot cannot distinguish missing-sequence-search from downstream executor/ranking issues
- without explicit intermediate-state evaluation, the pilot cannot cleanly separate:
  - first-step correct / second-step wrong
  - first-step wrong / second-step correct
  - one-primitive-missing
  - parameter carryover failure

This is a diagnosis statement only, not an implementation request for this lane.

## 10. Move-to-80 gate

Move-to-80 gate for any future expansion beyond the current 40-task pilot:

**Defined: Yes**

Do **not** expand to an 80-task or larger internal ladder until all of the following are true:
1. at least one canonical pilot row contains a represented 2-step primitive sequence in evaluation output
2. canonical evaluation distinguishes intermediate-state failure from final-step failure directly, not only by post-hoc manual probing
3. the canonical 40-task pilot produces at least one non-unsupported row for the right reason (represented 2-step composition), not via single-step shortcut behavior
4. the handoff manifest is reconciled to the live repo state before opening the next lane

## 11. Validation posture for this lane

Validation target for this lane:
- report-only diagnosis artifact
- no solver/generator/runner logic changes
- no runtime/chat/protected file changes
- no push

Expected validation set:
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

## 12. Closure judgment

Closure judgment:
- the unsupported pattern has been diagnosed sufficiently for this lane
- the primary unsupported cause is now explicit
- the earlier wording ambiguity about sampled-row fit status is corrected
- the lane should close on the diagnosis report only
- the next recommended lane remains:
  - `RECONCILE_WESLR_CURRENT_HANDOFF_TO_LIVE_HEAD_V1`
