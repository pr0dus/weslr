# WESLR ARC Copy-Grid Variant 2 Generator Disambiguation V1

- Dispatch: `FIX_ARC_SYNTHETIC_COPY_GRID_VARIANT_2_GENERATOR_DISAMBIGUATION_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `7c48cf718505a4a4a97e8a3c36399d3884a7976c`
- Previous report: `docs/WESLR_ARC_COPY_GRID_ROTATE_AMBIGUITY_DIAGNOSIS_V1.md`

## Scope

This lane corrects the synthetic generator for `synthetic_copy_grid_variant_2_v1` only.

It does **not**:
- add copy-ranking bias
- add family guardrails
- normalize abstract `rotate` / `reflect` aliases
- change reflect support
- repair stripped rotate behavior
- repair `object_count_to_pattern`
- use expected test output during solver generation
- add replay / scoring / final-answer behavior
- touch ARC-AGI-2 participation
- touch `.weslr`
- edit protected runtime/chat files

## Generator change

Variant 2 was made intrinsically disambiguating by changing only its synthetic train/test examples:

- train pair 0 now uses a horizontal two-cell object (`2,2`) so concrete `rotate_object_90` no longer matches that pair
- variant 2 no longer injects the accent-color placements that were unnecessary for copy semantics in this lane
- train pair 2 was moved to an off-center single-cell copy case so all train-pair structural inferences stay in the `copy` family instead of mixing in `complete_symmetry`
- expected outputs remain exact copies of inputs

Task count and runner shape were kept stable.

## Focused outcome

For `synthetic_copy_grid_variant_2_v1`:

- concrete `copy` train fit: **3/3 → 3/3**
- concrete `rotate_object_90` train fit: **3/3 → 2/3**
- dry-run selected packet: **partial/partial → exact/exact**
- train-pair structural family inference: **mixed/ambiguous → copy/copy/copy**

## Before / after diagnostic summary

### Canonical 120
- exact: **109 → 113**
- partial: **11 → 7**
- unsupported: **0 → 0**
- failed: **0 → 0**

### copy_grid
- canonical family summary: **exact 6 / partial 4 → exact 10 / partial 0**

### rotate_object_90
- canonical family summary: **exact 7 / partial 3 → exact 7 / partial 3**
- unchanged: **yes**

### reflect_object_horizontal_or_vertical
- canonical family summary: **exact 7 / partial 3 → exact 7 / partial 3**
- unchanged: **yes**

### object_count_to_pattern
- canonical family summary: **exact 9 / partial 1 → exact 9 / partial 1**
- unchanged: **yes**

## Mode-level before / after

- full_metadata: **45/3 → 47/1**
- toy_task_type_preserved_only: **35/1 → 36/0**
- fully_stripped_train_pairs_plus_test_input_only: **29/7 → 30/6**
- shuffled_renamed: **35/1 → 36/0**

## Evidence notes

- `toy_task_type` preserved mode improved by one exact packet and removed its one partial packet.
- fully stripped mode improved by one exact packet and removed one partial packet.
- real `rotate_object_90` family results did not regress.
- reflect-family results did not regress.
- `object_count_to_pattern` results did not change.
- no expected-output leakage was introduced; solver generation still does not use test outputs.
- optional shuffled mode improved by the same one-packet margin as toy-task-type-preserved mode.

## Files changed

- `weslr/arc_style_synthetic_task_generators.py`
- `weslr/tests/test_arc_style_synthetic_task_generators_v1.py`
- `weslr/tests/test_arc_style_synthetic_solver_suite_v1.py`
- `weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`
- `docs/WESLR_ARC_COPY_GRID_VARIANT_2_GENERATOR_DISAMBIGUATION_V1.md`

## Validation

Requested validation for this lane:
- `py_compile` on touched modules
- focused pytest for synthetic generators / solver suite / diagnostic runner
- `python weslr/tests/release_gate_v1.py`
- `git diff --check`
- `./scripts/weslr_release_check.sh`
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo`

All requested validations passed for the committed result in this lane.

## Conclusion

The fix was achieved by correcting the synthetic generator, not by ranking bias.

`synthetic_copy_grid_variant_2_v1` is now intrinsically copy-aligned:
- copy remains exact
- concrete rotate no longer fits all train pairs
- the selected packet becomes exact
- rotate / reflect / object-count family totals stay unchanged outside the intended copy-grid improvement window
