# WESLR ARC 2-Step Parameter Carryover and Contextual Inference Repair V1

- Dispatch: `REPAIR_BOUNDED_ARC_2_STEP_PARAMETER_CARRYOVER_AND_CONTEXTUAL_INFERENCE_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `bcf5ac2683b11a86a2cf7e453e9de2c14fbca52b`
- Previous report: `docs/WESLR_ARC_2_STEP_REMAINING_PARTIALS_AND_PARAMETER_CARRYOVER_DIAGNOSIS_V1.md`

## 1. Executive verdict

The bounded 2-step pilot was repaired without changing candidate budget, ranking, task inventory, fully-stripped policy, single-step solver behavior, or leakage posture.

Primary observed improvement:
- before repair: `33 exact / 6 partial / 1 unsupported / 0 failed`
- after repair: `39 exact / 1 partial / 0 unsupported / 0 failed`

This lane converts all previously unsupported rows into represented bounded 2-step evaluation and clears 6 of the 7 residual non-exacts. One bounded residual remains:
- `pilot_2_step_stress_08_fill_then_count_v1`
- status: `partial`
- remaining category: `right_primitives_wrong_order`

## 2. What changed

Implemented only narrow bounded parameter-carryover/contextual inference repairs inside `weslr/arc_style_synthetic_2_step_pilot_runner.py`:

1. **Context-aware fill_region parameter options**
   - Added border-aware/interior-aware fill parameter generation
   - Preserves bounded inference from train-derived current/target grids only
   - Distinguishes border value from fillable interior value in sequence mode

2. **Context-aware object_count_to_pattern parameter options**
   - Improved bounded row/pattern inference from interior rows when bordered outputs are present
   - Preserved dynamic `count=null`
   - Added bounded zero-count fallback so remove-noise/count rows can still emit executable candidates

3. **Bounded recolor / background candidate widening where needed**
   - Added bounded alternative background candidates for background-sensitive primitives
   - Still train-pair-derived only

4. **Joint bounded step-1 / step-2 sequence fit selection**
   - Sequence mode now scores bounded step-1 options by downstream step-2 solvability instead of choosing step 1 in isolation against the final output
   - No extra candidate budget added
   - No ranking rule changed across emitted sequence candidates

5. **Dynamic parameter summarization widened**
   - Marks more step parameters as dynamic when they vary per train pair instead of pretending they are stable

## 3. Required measurements

### 3.1 2-step pilot before/after
- before repair: `33 exact / 6 partial / 1 unsupported / 0 failed`
- after repair: `39 exact / 1 partial / 0 unsupported / 0 failed`

### 3.2 full_metadata before/after
- `33 / 6 / 1 / 0 -> 39 / 1 / 0 / 0`

### 3.3 toy_task_type_preserved_guardrail before/after
- `33 / 6 / 1 / 0 -> 39 / 1 / 0 / 0`

### 3.4 fully_stripped lower-bound unchanged policy
- yes
- remains `0 / 0 / 40 / 0`

### 3.5 represented 2-step candidate rows before/after
- `39 -> 40`

### 3.6 remaining non-exact rows count
- `7 -> 1`

### 3.7 remaining root-cause distribution after repair
- `right_primitives_wrong_order: 1`
- `first_step_correct_second_wrong: 0`
- `first_step_wrong_second_correct: 3`
- `one_primitive_missing: 0`
- `parameter_carryover_failure: 2`
- `intermediate_execution_failure: 0`
- `sequence_not_generated: 0`

Note: the taxonomy counts are runner-category counts over selected rows/modes and are not a drop-in replacement for the previous diagnosis root-cause rollup. The key empirical result is the score movement: `7 residual non-exacts -> 1 residual non-exact`.

### 3.8 accidental_composition_match count
- before repair: `1`
- after repair: `0`

### 3.9 candidate budget cutoff count
- before repair: `0`
- after repair: `0`

### 3.10 generator ambiguity count
- before repair: `0`
- after repair: `0`

### 3.11 single-step unchanged checks
- single-step canonical unchanged: yes (`114 / 6 / 0 / 0`)
- single-step solver suite unchanged: yes (`48 / 0 / 0 / 0`)

## 4. Residual row after repair

Remaining non-exact row:
- task_id: `pilot_2_step_stress_08_fill_then_count_v1`
- composition_pair: `fill_region -> object_count_to_pattern`
- status: `partial`
- selected candidate: reversed order candidate (`sequence:1`)
- remaining category: `right_primitives_wrong_order`

Observed residual interpretation:
- the intended ordered pair is represented
- the intended ordered pair still underperforms badly under the bounded current primitive semantics
- the reversed candidate remains lower mismatch (`42` vs `70`) and therefore wins without any ranking change
- this is no longer an unsupported-row / missing-carryover surface; it is a bounded residual where the current fill/count primitive semantics still favor the reversed order on this stress task

## 5. Row improvements attributable to the repair

These previously non-exact rows now became exact for the intended carryover/contextual reasons:
- `pilot_2_step_easy_08_fill_then_line_v1`
- `pilot_2_step_easy_10_count_then_border_v1`
- `pilot_2_step_easy_18_fill_then_border_v1`
- `pilot_2_step_medium_05_remove_noise_then_count_v1`
- `pilot_2_step_medium_09_fill_then_symmetry_v1`
- `pilot_2_step_easy_03_extract_then_recolor_v1`

Main repair effects by family:
- **fill_region carryover**: repaired for line/border/symmetry rows
- **object_count contextual row placement**: repaired for count-then-border
- **step-2 contextual inference after generated intermediate**: repaired for remove-noise/count and extract/recolor enough to clear the prior unsupported/partial residuals

## 6. Boundaries preserved

Confirmed unchanged / not added:
- no expected test output used during candidate generation
- no candidate budget increase
- no ranking change
- no task-inventory change
- no broad compatibility-matrix change
- no fully-stripped lower-bound policy change
- no single-step solver behavior change
- no candidate_output_surface wiring
- no replay wiring
- no scoring wiring
- no final-answer wiring
- no ARC-AGI-1 or ARC-AGI-2 participation change
- no `.weslr` touch
- no protected runtime/chat file edits

## 7. Files changed

- `weslr/arc_style_synthetic_2_step_pilot_runner.py`
- `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py`
- `weslr/tests/release_gate_v1.py`
- `docs/WESLR_ARC_2_STEP_PARAMETER_CARRYOVER_AND_CONTEXTUAL_INFERENCE_REPAIR_V1.md`

## 8. Validation

Executed:
- `python -m py_compile weslr/arc_style_synthetic_2_step_pilot_runner.py`
- `pytest -q weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py weslr/tests/test_arc_style_grid_solver_dry_run_v1.py`
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

Result: PASS

## 9. Recommended next lane

`DIAGNOSE_AND_DECIDE_BOUND_FOR_ARC_2_STEP_STRESS_FILL_THEN_COUNT_RIGHT_ORDER_RESIDUAL_V1`

Reason:
- the broad carryover/contextual inference surface is now largely repaired
- one stress residual remains, but it no longer looks like a generic missing-carryover problem
- the next decision should be whether this residual merits a narrow primitive-semantic repair or should be accepted as a bounded remaining failure before any 80-task expansion
