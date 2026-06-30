# WESLR ARC 2-Step Structural Sequence Visibility And Parameter Memory Repair V1

- Dispatch: `REPAIR_BOUNDED_ARC_2_STEP_STRUCTURAL_SEQUENCE_VISIBILITY_AND_PARAMETER_MEMORY_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `10f337b9b89e3bd9d58dbe59d06fb143182098f6`
- Previous report: `docs/WESLR_ARC_2_STEP_80_NEW_NON_EXACTS_DIAGNOSIS_V1.md`

## 1. Executive verdict

This lane applied a bounded structural repair in two parts:
1. **sequence-generation visibility repair** for `line_completion -> recolor_symbol`
2. **blackboard-style parameter memory trace** for 2-step candidates

Observed outcome:
- `pilot_2_step_easy_gen_10_line_recolor_vertical_v1` improved from `unsupported / sequence_not_generated` to `exact`
- `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` stayed `partial`, but now exposes an explicit parameter-memory contract trace instead of an opaque carryover miss
- known stress residual unchanged
- precision near-miss rows unchanged
- no single-step regression
- no leakage regression
- candidate budget and ranking unchanged

## 2. Structural change summary

### A. Sequence-generation visibility

Repair applied:
- when `line_completion -> recolor_symbol` reaches an exact intermediate and bounded recolor parameter options collapse to none, the runner now emits a deterministic visible identity recolor step
- no task-id shortcut
- no candidate budget expansion
- no primitive inventory expansion
- no ranking change

New diagnostic reason surfaced:
- `identity_recolor_visibility_repair`

### B. Parameter-memory / blackboard trace

Added bounded candidate trace fields:
- `step_1_exports`
- `step_2_imports`
- `carried_parameters`
- `dropped_parameters`
- `parameter_origin_by_key`
- `carryover_success`
- `sequence_visibility_reason`

Origin labels now used:
- `stable_train_inference`
- `dynamic_recomputed_from_current_input`
- `carried_from_step_1`
- `mixed`

This is diagnostic blackboard memory only:
- no `.weslr` persistence
- no runtime memory mutation
- no autonomous memory
- no replay/scoring/final-answer wiring

## 3. Before / after

### Original 40
- before: `39 / 1 / 0 / 0`
- after: `39 / 1 / 0 / 0`

### New 40-only
- before: `36 / 3 / 1 / 0`
- after: `37 / 3 / 0 / 0`

### Combined 80
- before: `75 / 4 / 1 / 0`
- after: `76 / 4 / 0 / 0`

### Represented candidates
- before: `79 / 80`
- after: `80 / 80`

### Unsupported count
- before: `1`
- after: `0`

### Parameter-carryover-failure count
- before: `1`
- after: `1`

### Accidental composition matches
- before: `1`
- after: `1`

## 4. Target row 1 — `pilot_2_step_easy_gen_10_line_recolor_vertical_v1`

### Before
- status: `unsupported`
- root cause: `sequence_not_generated`
- intended pair not emitted as an executable 2-step candidate because recolor parameter options collapsed after exact line completion

### After
- status: `exact`
- selected candidate: `pilot_2_step_easy_gen_10_line_recolor_vertical_v1__toy_task_type_preserved_guardrail:sequence:0`
- selected sequence:
  - step 1: `line_completion {background_value: 0, line_value: 3}`
  - step 2: `recolor_symbol {background_value: 0, from_value: 3, to_value: 3}`
- sequence visibility reason: `identity_recolor_visibility_repair`
- carryover trace:
  - `step_1_exports` exposes `background_value=0`, `object_value=3`, `line_value=3`
  - `step_2_imports` = `background_value, from_value, to_value`
  - carried parameters include `background_value=0` and `from_value=3`
  - `parameter_origin_by_key` shows mixed carry/recompute for background/from, stable-train for `to_value`

Judgment:
- the structural visibility repair worked
- the unsupported row is now represented and exact

## 5. Target row 2 — `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`

### Before
- status: `partial`
- root cause: `parameter_carryover_failure`
- selected reversed-order candidate still beat the intended ordered pair

### After
- status: `partial`
- root cause: `parameter_carryover_failure`
- selected candidate remains: `pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1__toy_task_type_preserved_guardrail:sequence:1`
- selected sequence remains reversed:
  - step 1: `recolor_symbol {background_value: 4}`
  - step 2: `extract_largest_object {}`
- sequence visibility reason: `standard_generated`

New explicit memory trace:
- candidate traces now show exported step-1 values and dropped values instead of hiding the failure inside a generic partial
- for the intended ordered candidate, the trace now makes visible:
  - exported extracted-object values differ across train pairs
  - step-2 imports require recolor memory keys
  - parameter origins are mixed rather than cleanly stable
  - carryover remains structurally underspecified for this row

Observed memory-contract gap:
- the lane now surfaces the missing handoff explicitly, but does **not** yet resolve the ordered extract/recolor ambiguity into an exact repair
- this satisfies the minimum requirement to expose the precise contract gap without broadening precision inference or touching the near-miss rows

## 6. Untouched rows / boundaries

### Known stress residual untouched
- `pilot_2_step_stress_08_fill_then_count_v1`
- untouched: `yes`
- still: `partial / right_primitives_wrong_order`

### Precision near-miss rows untouched
- `pilot_2_step_easy_gen_02_noise_recolor_color_swap_v1`
- `pilot_2_step_medium_ctx_09_extract_recolor_bg_transfer_v1`
- untouched: `yes`
- both remain: `partial / first_step_wrong_second_correct`

### Unchanged strategic boundaries
- candidate budget cutoff unchanged: `yes (0 -> 0)`
- generator ambiguity unchanged: `yes (0 -> 0)`
- ranking changed: `no`
- leakage boundaries preserved: `yes`
- single-step canonical unchanged: `yes (114 / 6 / 0 / 0)`
- single-step solver suite unchanged: `yes (48 / 0 / 0 / 0)`

## 7. Required judgment

### Structural repair applied
- yes

### Sequence-generation visibility repair applied
- yes

### Parameter memory / carryover repair applied
- yes, at the bounded blackboard-trace and explicit handoff level
- no, in the narrower sense of converting `extract_recolor_large_grid` to exact in this lane

### Minimum acceptable success check
- unsupported row becomes represented or precise blocker proven: `yes` (`represented and exact`)
- carryover row improves or exposes precise memory contract gap: `yes` (`precise gap exposed`)
- precision near-miss rows modified: `no`
- known stress residual repaired: `no`
- leakage regression: `no`
- single-step regression: `no`

## 8. Files changed

- `weslr/arc_style_synthetic_2_step_pilot_runner.py`
- `weslr/tests/test_arc_style_synthetic_2_step_pilot_runner_v1.py`
- `weslr/tests/release_gate_v1.py`
- `docs/WESLR_ARC_2_STEP_STRUCTURAL_SEQUENCE_VISIBILITY_AND_PARAMETER_MEMORY_REPAIR_V1.md`

## 9. Recommended next lane

`REPAIR_BOUNDED_ARC_2_STEP_EXTRACT_RECOLOR_MEMORY_CONTRACT_V1`

Reason:
- the line/recolor structural visibility blocker is now resolved
- the remaining structural work is a narrower ordered extract/recolor memory contract problem
- precision near-miss calibration rows should still stay out of scope until that contract lane is handled separately
