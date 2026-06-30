# WESLR ARC 2-Step Sequence Generator and Intermediate Evaluator Implementation V1

- Dispatch: `IMPLEMENT_BOUNDED_ARC_2_STEP_SEQUENCE_CANDIDATE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `9ea5e89d4a4054c782f2a28e20bf9b7ad50752be`
- Previous report: `docs/WESLR_ARC_2_STEP_SEQUENCE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_DESIGN_V1.md`

## 1. Executive verdict

The minimal bounded 2-step pilot mechanism is now implemented inside the synthetic 40-task pilot runner.

Observed primary result (`toy_task_type_preserved_guardrail`):
- before: `0 exact / 0 partial / 40 unsupported / 0 failed`
- after: `33 exact / 6 partial / 1 unsupported / 0 failed`

Minimum lane success condition is met:
- represented executable 2-step candidate rows moved from `0` to `39`
- step-1 plausibility is now measurable
- step-2 plausibility is now measurable
- no expected-test-output-derived parameters were introduced
- single-step canonical and single-step solver suite remain unchanged

This lane intentionally stays bounded to the synthetic 2-step pilot surface.
It does not wire candidate_output_surface, replay, scoring, final-answer behavior, ARC-AGI participation, or `.weslr` state.

## 2. Handoff mismatch note

`WESLR_CURRENT_HANDOFF.md` still points to verified HEAD `8d38829c1256c7d47ca41a56e24def61cf4fe89f`.
For this lane that handoff state was treated as stale exactly as instructed.
No handoff rewrite was performed in this lane.

## 3. Implemented scope

### 3.1 Bounded 2-step candidate generation
Implemented a deterministic bounded generator in `weslr/arc_style_synthetic_2_step_pilot_runner.py` with:
- max sequence length: `2`
- max candidate budget per row: `2`
- supported primitive-pair generation only when the packet trace still preserves a concrete composition pair
- deterministic ordered candidate enumeration: intended order first, reversed order second
- no task-id shortcut
- no note shortcut
- no expected test output use

### 3.2 2-step executor
Implemented explicit 2-step execution for train evaluation:
- apply primitive 1 to train input
- apply primitive 2 to predicted intermediate
- compare final predicted output against train output

### 3.3 Intermediate-state evaluator
Implemented row-level intermediate diagnostics:
- `step1_plausible`: whether predicted step-1 output matches the stored train intermediate
- `step2_plausible`: whether primitive 2 can map the oracle intermediate to the train final output
- `final_exact`: whether the generated 2-step execution fits the full train pair

### 3.4 Parameter flow
Parameter proposals are inferred from train pairs only.
Bounded parameter search is family-local and deterministic.
Stable parameters are preserved when consistent across train pairs.
Dynamic fields are kept bounded and explicit in the candidate summary where variation remains acceptable (`background_value`, `object_value`, `count`).
No test output is used.

## 4. Primary before/after results

### 4.1 Primary attribution mode: `toy_task_type_preserved_guardrail`
- before: `0 exact / 0 partial / 40 unsupported / 0 failed`
- after: `33 exact / 6 partial / 1 unsupported / 0 failed`

### 4.2 Full metadata mode
- before: `0 exact / 0 partial / 40 unsupported / 0 failed`
- after: `33 exact / 6 partial / 1 unsupported / 0 failed`

### 4.3 Fully stripped lower bound
- before: `0 exact / 0 partial / 40 unsupported / 0 failed`
- after: `0 exact / 0 partial / 40 unsupported / 0 failed`

This remains a lower-bound diagnostic only and does not block the lane.

## 5. Required breakdowns

### 5.1 Primary result totals
- exact: `33`
- partial: `6`
- unsupported: `1`
- failed: `0`

### 5.2 Bucket breakdown (`toy_task_type_preserved_guardrail`)
- easy: `16 exact / 4 partial / 0 unsupported / 0 failed`
- medium: `8 exact / 1 partial / 1 unsupported / 0 failed`
- stress: `9 exact / 1 partial / 0 unsupported / 0 failed`

### 5.3 Attribution mode breakdown
- `full_metadata`: `33 / 6 / 1 / 0`
- `toy_task_type_preserved_guardrail`: `33 / 6 / 1 / 0`
- `fully_stripped_lower_bound`: `0 / 0 / 40 / 0`
- `shuffled_renamed`: `33 / 6 / 1 / 0`

### 5.4 Failure taxonomy breakdown (`toy_task_type_preserved_guardrail`)
- `right_primitives_wrong_order`: `0`
- `first_step_correct_second_wrong`: `0`
- `first_step_wrong_second_correct`: `6`
- `one_primitive_missing`: `0`
- `parameter_carryover_failure`: `1`
- `intermediate_execution_failure`: `0`
- `sequence_not_generated`: `1`

## 6. Representation and plausibility counts

### 6.1 Represented executable 2-step candidate rows
- before: `0`
- after: `39`

### 6.2 Step-1 plausible rows
- before: `0`
- after: `29`

### 6.3 Step-2 plausible rows
- before: `0`
- after: `36`

## 7. Remaining misses in the primary mode

### 7.1 Unsupported row
- `pilot_2_step_medium_05_remove_noise_then_count_v1`
  - current category: `parameter_carryover_failure`

### 7.2 Partial rows
- `pilot_2_step_easy_03_extract_then_recolor_v1`
- `pilot_2_step_easy_08_fill_then_line_v1`
- `pilot_2_step_easy_10_count_then_border_v1`
- `pilot_2_step_easy_18_fill_then_border_v1`
- `pilot_2_step_medium_09_fill_then_symmetry_v1`
- `pilot_2_step_stress_08_fill_then_count_v1`

Observed pattern:
- the remaining mass is no longer dominated by missing sequence representation
- the remaining errors are now mostly step-1-family mismatch or bounded parameter carryover limits

## 8. Boundary confirmation

Confirmed unchanged / not added:
- single-step canonical remains `114 exact / 6 partial / 0 unsupported / 0 failed`
- single-step solver suite remains `48 exact / 0 partial / 0 unsupported / 0 failed`
- no expected-output leakage
- no candidate_output_surface wiring
- no replay wiring
- no scoring wiring
- no final-answer wiring
- no ARC-AGI-1 or ARC-AGI-2 participation change
- no `.weslr` state touch
- no protected runtime/chat file edits

## 9. Files changed in this lane

- `weslr/arc_style_synthetic_2_step_pilot_runner.py`
- `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py`
- `weslr/tests/release_gate_v1.py`
- `docs/WESLR_ARC_2_STEP_SEQUENCE_GENERATOR_AND_INTERMEDIATE_EVALUATOR_IMPLEMENTATION_V1.md`

## 10. Recommended next lane

`DIAGNOSE_REMAINING_BOUNDED_ARC_2_STEP_PARTIALS_AND_PARAMETER_CARRYOVER_FAILURES_V1`

Reason:
- the representation failure is largely solved for the fixed 40-task pilot
- the next blocker is no longer missing 2-step surface
- the next blocker is bounded step-family and carryover quality on the remaining `6 partial + 1 unsupported`
