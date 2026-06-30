# WESLR ARC 2-Step 80-Pilot Expansion With Stress Residual Tracking V1

- Dispatch: `EXPAND_BOUNDED_ARC_2_STEP_PILOT_FROM_40_TO_80_WITH_STRESS_RESIDUAL_TRACKING_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `bf1ff08b60005fcf3321d461fc35abb64410b606`
- Previous report: `docs/WESLR_ARC_2_STEP_STRESS_FILL_THEN_COUNT_RESIDUAL_BOUND_DECISION_V1.md`

## 1. Executive verdict

The bounded synthetic 2-step pilot is now expanded from 40 to 80 tasks.

Observed results:
- original 40 preserved: `39 exact / 1 partial / 0 unsupported / 0 failed`
- new 40-only: `36 exact / 3 partial / 1 unsupported / 0 failed`
- combined 80: `75 exact / 4 partial / 1 unsupported / 0 failed`

Key outcome:
- the original 40-task baseline stayed intact
- the combined 80-task runner is implemented
- the accepted `fill_region -> object_count_to_pattern` stress residual remains tracked as `known_stress_residual`
- no single-step regression
- no leakage regression
- fully stripped remains lower-bound only

## 2. What was added

Added 40 new bounded 2-step tasks on top of the preserved original 40:
- 20 easy/medium generalization tasks
- 10 harder parameter/context-transfer tasks
- 10 stress/strangeness tasks

Expansion themes included:
- same pair, different colors
- same pair, different object sizes
- same pair, larger grids (`7x7`, `8x8` where safe)
- parameter transfer across step 1 -> step 2
- contextual/dynamic parameters after intermediate changes
- wrong-order traps
- single-step shortcut traps

No candidate budget increase, ranking change, fully-stripped policy change, solver-output wiring, replay/scoring/final-answer wiring, ARC-AGI participation change, or `.weslr` touch was introduced.

## 3. Runner/reporting changes

Implemented:
- preserved `run_arc_style_synthetic_2_step_40_pilot_diagnostic_v1()`
- added `build_arc_style_synthetic_2_step_80_pilot_plan_v1()`
- added `run_arc_style_synthetic_2_step_80_pilot_diagnostic_v1()`
- explicit reporting for:
  - original 40 result
  - new 40-only result
  - combined 80 result
  - accepted stress residual count
  - new unexplained failures count
  - candidate budget cutoff count
  - generator ambiguity count
  - accidental composition match count

## 4. Required results

### 4.1 Original 40 result
- `39 exact / 1 partial / 0 unsupported / 0 failed`
- preserved: yes

### 4.2 New 40-only result
- `36 exact / 3 partial / 1 unsupported / 0 failed`

### 4.3 Combined 80 result
- `75 exact / 4 partial / 1 unsupported / 0 failed`

### 4.4 Represented candidate rows
- original 40: `40 / 40`
- combined 80: `79 / 80`

### 4.5 Bucket breakdown — combined 80 primary mode
- easy: `27 exact / 2 partial / 1 unsupported / 0 failed`
- medium: `29 exact / 1 partial / 0 unsupported / 0 failed`
- stress: `19 exact / 1 partial / 0 unsupported / 0 failed`

### 4.6 Bucket breakdown — new 40-only primary mode
- easy: `7 exact / 2 partial / 1 unsupported / 0 failed`
- medium: `19 exact / 1 partial / 0 unsupported / 0 failed`
- stress: `10 exact / 0 partial / 0 unsupported / 0 failed`

### 4.7 Attribution mode breakdown — combined 80
- `full_metadata`: `75 / 4 / 1 / 0`
- `toy_task_type_preserved_guardrail`: `75 / 4 / 1 / 0`
- `fully_stripped_lower_bound`: `0 / 0 / 80 / 0`
- `shuffled_renamed`: `75 / 4 / 1 / 0`

### 4.8 Failure taxonomy breakdown — combined 80 primary mode
- `right_primitives_wrong_order`: `2`
- `first_step_correct_second_wrong`: `0`
- `first_step_wrong_second_correct`: `7`
- `one_primitive_missing`: `0`
- `parameter_carryover_failure`: `6`
- `intermediate_execution_failure`: `0`
- `sequence_not_generated`: `1`

### 4.9 Expansion tracking counts
- accepted stress residual count: `1`
- new unexplained failures count: `0`
- candidate budget cutoff count: `0`
- generator ambiguity count: `0`
- accidental composition match count: `1`

## 5. Non-exact rows after expansion

Combined 80 non-exacts:
1. `pilot_2_step_stress_08_fill_then_count_v1` — partial — `right_primitives_wrong_order` — known stress residual
2. `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1` — partial — `first_step_wrong_second_correct`
3. `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` — partial — `parameter_carryover_failure`
4. `pilot_2_step_easy_gen_10_line_recolor_vertical_v1` — unsupported — `sequence_not_generated`
5. `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1` — partial — `first_step_wrong_second_correct`

Interpretation:
- all remaining new non-exacts are classified
- no unexplained failure remains
- the sole unsupported new row is explained, not silent
- the prior accepted stress residual remains isolated and separately tracked

## 6. Stress residual tracking

Tracked unchanged as non-blocking:
- task_id: `pilot_2_step_stress_08_fill_then_count_v1`
- classification: `known_stress_residual`
- blocker for 80 expansion: no
- repaired in this lane: no

This lane preserves the prior boundary decision rather than quietly repairing or removing it.

## 7. Success-criteria judgment

Against the requested minimum acceptable success:
- original 40 preserved: yes
- all or most new rows have represented 2-step candidates: yes (`39 / 40`)
- unsupported count explained: yes (`1`, classified `sequence_not_generated`)
- failures classified: yes
- no leakage: yes
- no single-step regression: yes

Therefore this lane meets the expansion success bar.

## 8. Boundaries preserved

Confirmed unchanged:
- original 40 task inventory semantics preserved
- candidate budget unchanged
- ranking unchanged
- fully-stripped lower-bound policy unchanged
- no expected test output used during candidate generation
- no candidate_output_surface wiring
- no replay/scoring/final-answer behavior
- no ARC-AGI-1 / ARC-AGI-2 participation change
- no `.weslr` touch
- no protected runtime/chat file edits
- leakage boundaries preserved
- single-step canonical unchanged: `114 / 6 / 0 / 0`
- single-step solver suite unchanged: `48 / 0 / 0 / 0`

## 9. Files changed

- `weslr/arc_style_synthetic_2_step_pilot_runner.py`
- `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py`
- `weslr/tests/release_gate_v1.py`
- `docs/WESLR_ARC_2_STEP_80_PILOT_EXPANSION_WITH_STRESS_RESIDUAL_TRACKING_V1.md`

## 10. Validation

Executed:
- `python -m py_compile weslr/arc_style_synthetic_2_step_pilot_runner.py weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py weslr/tests/release_gate_v1.py`
- focused pytest for 2-step 40/80 runner + existing single-step diagnostic tests
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

Result: PASS

## 11. Recommended next lane

`DIAGNOSE_NEW_80_TASK_NON_EXACTS_WITHOUT_TOUCHING_KNOWN_STRESS_RESIDUAL_V1`

Reason:
- the 80-task expansion is now in place and stable
- original 40 baseline is preserved
- the next useful move is to diagnose the 4 new non-exact expansion rows separately from the already accepted stress residual
