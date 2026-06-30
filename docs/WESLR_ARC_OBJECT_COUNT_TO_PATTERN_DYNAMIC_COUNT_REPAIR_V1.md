# WESLR ARC Object-Count-to-Pattern Dynamic Count Repair V1

- Dispatch: `REPAIR_ARC_OBJECT_COUNT_TO_PATTERN_DYNAMIC_COUNT_PARAMETER_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `92900694232a061d48e9f88205351d94bc326252`
- Previous report: `docs/WESLR_ARC_OBJECT_COUNT_TO_PATTERN_REMAINING_PARTIAL_DIAGNOSIS_V1.md`

## Root cause confirmation

Confirmed: the remaining `object_count_to_pattern` partial was caused by **train-frozen count parameterization**.

Before repair:
- the selected family was correct: `object_count_to_pattern`
- train fit was correct
- candidate parameters serialized `count=3`
- the second test input for `synthetic_object_count_to_pattern_variant_2_v1` contained 4 counted objects
- execution emitted only three pattern cells because it trusted the frozen train count

## Repair scope

This repair is narrow and limited to object-count dynamic parameterization.

Changed:
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/arc_style_grid_adapter_phase2.py`
- focused tests for adapter, dry-run, solver suite, and diagnostic runner

Not changed:
- synthetic generator
- expected-output generation
- validation logic
- copy_grid behavior
- rotate_object_90 behavior
- reflect behavior
- ranking bias
- expected-test-output usage during solver generation
- candidate_output_surface / replay / scoring / final-answer behavior
- ARC-AGI-2 participation
- `.weslr`
- protected runtime/chat files

## Implementation

### Freeze point repaired

Two places were freezing the train count into candidate parameters:

1. `weslr/arc_style_grid_solver_dry_run.py`
   - `_infer_object_count_to_pattern_parameters(...)`
2. `weslr/arc_style_grid_adapter_phase2.py`
   - toy-task candidate construction for `object_count_to_pattern`

### New behavior

For `object_count_to_pattern`, inferred parameters now encode:
- `count = null`
- `pattern_value = <train-inferred stable value>`
- `row_index = <train-inferred stable row>`
- `background_value = <train-inferred stable background>`

Execution already supported dynamic counting when `count is None`, so the repair reuses existing executor behavior instead of introducing new solver authority.

Result:
- train-pair fit is preserved
- count is recomputed from the current input grid at execution time
- the formerly partial object-count row now becomes exact

## Focused test coverage added/updated

Added/updated focused checks for:
- dynamic execution with train count 3 and test count 4 producing four pattern cells
- dry-run inference for `synthetic_object_count_to_pattern_variant_2_v1` keeping `count=null`
- solver-suite exactness for object-count variant 2
- updated suite and diagnostic baselines
- no expected test output usage in solver generation remains preserved

## Before / after results

### object_count_to_pattern
- before: `9 exact / 1 partial`
- after: `10 exact / 0 partial`

### canonical 120
- before: `113 exact / 7 partial / 0 unsupported / 0 failed`
- after: `114 exact / 6 partial / 0 unsupported / 0 failed`

### unchanged families
- copy_grid: `10 exact / 0 partial` → `10 exact / 0 partial`
- rotate_object_90: `7 exact / 3 partial` → `7 exact / 3 partial`
- reflect: `7 exact / 3 partial` → `7 exact / 3 partial`

## Evidence summary

Post-repair solver and diagnostic checks report:
- synthetic solver suite: `48 exact / 0 partial`
- `object_count_to_pattern` family in solver suite: `4 exact / 0 partial`
- canonical diagnostic: `114 exact / 6 partial / 0 unsupported / 0 failed`

## Leakage / authority posture

Confirmed unchanged:
- no expected-output leakage introduced
- solver generation still does not use test outputs
- no candidate_output_surface wiring
- no replay/scoring/final-answer behavior added

## Validation

Requested validation for this lane:
- `py_compile` on touched modules
- focused pytest for adapter / dry-run / synthetic solver suite / diagnostic runner
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

All requested validations passed for the committed result in this lane.
