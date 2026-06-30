# WESLR ARC Synthetic 120 Diagnostic Runner V1

- Dispatch: `CANONIZE_ARC_SYNTHETIC_120_DIAGNOSTIC_RUNNER_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `60737809`
- Handoff mismatch note: `WESLR_CURRENT_HANDOFF.md` still points at stale verified HEAD `9ed508db...`; this lane followed the operator-requested live repo state at `60737809` and records the mismatch here only.

## 1. Executive verdict

A committed deterministic ARC synthetic diagnostic runner now exists at:
- `weslr/arc_style_synthetic_diagnostic_runner.py`
- entry point: `run_arc_style_synthetic_120_diagnostic_runner_v1()`

It canonizes a reproducible **120 packet evaluation** diagnostic from committed code.

Canonical 120 result at `60737809` after this lane's narrow dry-run fixes:
- exact: `102`
- partial: `8`
- unsupported: `10`
- failed: `0`
- exact %: `85.0%`

This is a **diagnostic/canonization result only**.
It is not a public capability claim, not an ARC-AGI-2 participation claim, and not benchmark authority.

## 2. Why legacy 80-task rerun was blocked

The prior verification lane found that the repo did not contain one committed callable entry point that reproduced the older continuity-only "80-task" report line.

At `60737809`, committed code exposed:
- `generate_arc_style_synthetic_task_suite_v1()` -> `36` synthetic task variants
- `run_arc_style_synthetic_solver_suite_v1()` -> `48` packet evaluations

What was missing:
- a single named committed runner that stabilized the historical continuity benchmark definition
- a canonical packet inventory explaining which packets counted toward the continuity run
- a reproducible path for stripped / preserved / shuffled attribution checks from committed code alone

This lane resolves that by committing a named deterministic 120-runner instead of trying to re-infer the historical 80-run shape from MD reports.

## 3. New canonical 120-runner entry point

Committed entry point:
- `weslr.arc_style_synthetic_diagnostic_runner.run_arc_style_synthetic_120_diagnostic_runner_v1`

Canonical construction:
- `48` full-metadata packet evaluations from the committed synthetic suite
- `36` `toy_task_type`-preserved-only packet rebuilds (first packet per task variant)
- `36` fully stripped `train_pairs + test_input` packet rebuilds (first packet per task variant)

Canonical total:
- `48 + 36 + 36 = 120`

Optional cheap extra mode also added and run:
- `36` shuffled/renamed packet perturbations (first packet per task variant)

Determinism:
- no randomness
- no provider/model/tool/retrieval calls
- fixed mode inventory
- fixed first-packet projection for metadata-only cohorts
- stable ordering by committed suite order

## 4. 120-task result

### Canonical 120

| Cohort | Packets | Exact | Partial | Unsupported | Failed | Exact % |
|---|---:|---:|---:|---:|---:|---:|
| full metadata | 48 | 41 | 3 | 4 | 0 | 85.4% |
| toy_task_type preserved only | 36 | 32 | 1 | 3 | 0 | 88.9% |
| fully stripped train_pairs + test_input only | 36 | 29 | 4 | 3 | 0 | 80.6% |
| **canonical total** | **120** | **102** | **8** | **10** | **0** | **85.0%** |

### Optional shuffled / renamed

| Cohort | Packets | Exact | Partial | Unsupported | Failed | Exact % |
|---|---:|---:|---:|---:|---:|---:|
| shuffled / renamed | 36 | 32 | 1 | 3 | 0 | 88.9% |

## 5. Family / variant breakdown

### Family summary across canonical 120

| Family | Exact | Partial | Unsupported | Failed |
|---|---:|---:|---:|---:|
| `copy_grid` | 6 | 4 | 0 | 0 |
| `recolor_symbol` | 10 | 0 | 0 | 0 |
| `move_single_object` | 10 | 0 | 0 | 0 |
| `fill_region` | 10 | 0 | 0 | 0 |
| `complete_symmetry` | 10 | 0 | 0 | 0 |
| `border_frame` | 10 | 0 | 0 | 0 |
| `extract_largest_object` | 10 | 0 | 0 | 0 |
| `remove_background_noise` | 10 | 0 | 0 | 0 |
| `line_completion` | 10 | 0 | 0 | 0 |
| `object_count_to_pattern` | 9 | 1 | 0 | 0 |
| `rotate_object_90` | 7 | 3 | 0 | 0 |
| `reflect_object_horizontal_or_vertical` | 0 | 0 | 10 | 0 |

### Requested specific statuses

#### `complete_symmetry` variant 2
Observed canonical rows:
- full metadata test input `0`: exact
- full metadata test input `1`: exact
- `toy_task_type`-preserved-only: exact
- fully stripped: exact

Selected primitive/candidate:
- primitive: `complete_symmetry`
- candidate id shape: `synthetic_complete_symmetry_variant_2_v1:complete_symmetry:0`

Judgment:
- **fixed and stable** in the canonical runner

#### `line_completion`
Observed canonical family result:
- exact `10`
- partial `0`
- unsupported `0`
- failed `0`

Judgment:
- **exact across the canonical 120**

#### `reflect_object_horizontal_or_vertical`
Observed canonical family result:
- exact `0`
- partial `0`
- unsupported `10`
- failed `0`

Important nuance:
- dry-run inference can now identify `reflect_object_horizontal_or_vertical` with `train_fit_status = fit`
- the synthetic suite still classifies the family as unsupported at packet-result level because it remains outside `SUPPORTED_SYNTHETIC_FAMILIES_V1` for suite-level support classification

Judgment:
- **still honestly unsupported at suite level**

## 6. Remaining failures and root causes

### Canonical non-exact rows

| Mode | task_id | family | variant | seed | test_input_index | inferred primitive | selected candidate id | train fit status | packet status | reason |
|---|---|---|---:|---|---:|---|---|---|---|---|
| full metadata | `synthetic_copy_grid_variant_2_v1` | `copy_grid` | 1 | n/a | 0 | `rotate` | `synthetic_copy_grid_variant_2_v1:rotate:0` | unsupported | partial | `validation_mismatch` |
| full metadata | `synthetic_copy_grid_variant_2_v1` | `copy_grid` | 1 | n/a | 1 | `rotate` | `synthetic_copy_grid_variant_2_v1:rotate:0` | unsupported | partial | `validation_mismatch` |
| full metadata | `synthetic_object_count_to_pattern_variant_2_v1` | `object_count_to_pattern` | 1 | n/a | 1 | `object_count_to_pattern` | `synthetic_object_count_to_pattern_variant_2_v1:object_count_to_pattern:0` | fit | partial | `validation_mismatch` |
| full metadata | `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1` | `reflect_object_horizontal_or_vertical` | 0 | n/a | 0 | `reflect_object_horizontal_or_vertical` | `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1:reflect_object_horizontal_or_vertical:0` | fit | unsupported | `unsupported_transformation_family, missing_primitive_executor` |
| full metadata | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1` | `reflect_object_horizontal_or_vertical` | 1 | n/a | 0 | `reflect_object_horizontal_or_vertical` | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1:reflect_object_horizontal_or_vertical:0` | fit | unsupported | `unsupported_transformation_family, missing_primitive_executor` |
| full metadata | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1` | `reflect_object_horizontal_or_vertical` | 1 | n/a | 1 | `reflect_object_horizontal_or_vertical` | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1:reflect_object_horizontal_or_vertical:0` | fit | unsupported | `unsupported_transformation_family, missing_primitive_executor` |
| full metadata | `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1` | `reflect_object_horizontal_or_vertical` | 2 | n/a | 0 | `reflect_object_horizontal_or_vertical` | `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1:reflect_object_horizontal_or_vertical:0` | fit | unsupported | `unsupported_transformation_family, missing_primitive_executor` |
| toy preserved only | `synthetic_copy_grid_variant_2_v1__toy_task_type_preserved_only` | `copy_grid` | 1 | n/a | 0 | `rotate` | `synthetic_copy_grid_variant_2_v1__toy_task_type_preserved_only:rotate:0` | unsupported | partial | `validation_mismatch` |
| toy preserved only | `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1__toy_task_type_preserved_only` | `reflect_object_horizontal_or_vertical` | 0 | n/a | 0 | `reflect_object_horizontal_or_vertical` | `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1__toy_task_type_preserved_only:reflect_object_horizontal_or_vertical:0` | fit | unsupported | `unsupported_transformation_family, missing_primitive_executor` |
| toy preserved only | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1__toy_task_type_preserved_only` | `reflect_object_horizontal_or_vertical` | 1 | n/a | 0 | `reflect_object_horizontal_or_vertical` | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1__toy_task_type_preserved_only:reflect_object_horizontal_or_vertical:0` | fit | unsupported | `unsupported_transformation_family, missing_primitive_executor` |
| toy preserved only | `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1__toy_task_type_preserved_only` | `reflect_object_horizontal_or_vertical` | 2 | n/a | 0 | `reflect_object_horizontal_or_vertical` | `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1__toy_task_type_preserved_only:reflect_object_horizontal_or_vertical:0` | fit | unsupported | `unsupported_transformation_family, missing_primitive_executor` |
| fully stripped | `synthetic_copy_grid_variant_2_v1__fully_stripped` | `copy_grid` | 1 | n/a | 0 | `rotate` | `synthetic_copy_grid_variant_2_v1__fully_stripped:rotate:0` | unsupported | partial | `validation_mismatch` |
| fully stripped | `synthetic_rotate_object_90_variant_1_v1__fully_stripped` | `rotate_object_90` | 0 | n/a | 0 | `rotate` | `synthetic_rotate_object_90_variant_1_v1__fully_stripped:rotate:0` | unsupported | partial | `candidate_generation_gap, validation_mismatch` |
| fully stripped | `synthetic_rotate_object_90_variant_2_v1__fully_stripped` | `rotate_object_90` | 1 | n/a | 0 | `rotate` | `synthetic_rotate_object_90_variant_2_v1__fully_stripped:rotate:0` | unsupported | partial | `candidate_generation_gap, validation_mismatch` |
| fully stripped | `synthetic_rotate_object_90_variant_3_v1__fully_stripped` | `rotate_object_90` | 2 | n/a | 0 | `rotate` | `synthetic_rotate_object_90_variant_3_v1__fully_stripped:rotate:0` | unsupported | partial | `candidate_generation_gap, validation_mismatch` |
| fully stripped | `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1__fully_stripped` | `reflect_object_horizontal_or_vertical` | 0 | n/a | 0 | `rotate` | `synthetic_reflect_object_horizontal_or_vertical_variant_1_v1__fully_stripped:rotate:0` | unsupported | unsupported | `candidate_generation_gap, unsupported_transformation_family, missing_primitive_executor` |
| fully stripped | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1__fully_stripped` | `reflect_object_horizontal_or_vertical` | 1 | n/a | 0 | `rotate` | `synthetic_reflect_object_horizontal_or_vertical_variant_2_v1__fully_stripped:rotate:0` | unsupported | unsupported | `candidate_generation_gap, unsupported_transformation_family, missing_primitive_executor` |
| fully stripped | `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1__fully_stripped` | `reflect_object_horizontal_or_vertical` | 2 | n/a | 0 | `rotate` | `synthetic_reflect_object_horizontal_or_vertical_variant_3_v1__fully_stripped:rotate:0` | unsupported | unsupported | `candidate_generation_gap, unsupported_transformation_family, missing_primitive_executor` |

### Root-cause summary

1. `copy_grid` variant 2 remains a real mismatch pocket.
   - The dry-run path still falls through to unsupported `rotate` instead of preserving copy behavior.

2. `object_count_to_pattern` variant 2 has one remaining packet-level validation mismatch.
   - Train fit stays `fit`, but the top-1 attempt does not equal the expected output for one test input.

3. `rotate_object_90` stays sensitive to full stripping.
   - Removing richer metadata degrades the stripped cohort into unsupported fallback `rotate` proposals for the first packet of each variant.

4. `reflect_object_horizontal_or_vertical` remains suite-level unsupported.
   - Dry-run can infer it.
   - Canonical suite support classification still blocks it as unsupported.

## 7. `toy_task_type` dependency status

Observed exact counts:
- full metadata: `41 / 48`
- `toy_task_type` preserved only: `32 / 36`
- fully stripped: `29 / 36`

Judgment:
- **dependency still present: yes**

More precise reading:
- keeping only `toy_task_type` plus minimal synthetic trace preserves more exactness than a fully stripped rebuild
- fully stripping causes targeted regressions, especially in `rotate_object_90` and reflected cases
- this is **not** the old all-or-nothing collapse claim; it is a narrower still-live metadata dependency

## 8. Expected-output leakage check

Observed boundaries remain intact:
- no solver-visible expected test outputs were used for candidate generation
- canonical trace flags remained:
  - `uses_test_output = false`
  - `uses_task_id_for_candidate_selection = false`
  - `uses_notes_for_candidate_selection = false`
  - `lookup_table_detected = false`
- runner leakage flags remain synthetic-only and false for public/private benchmark leakage

Judgment:
- **expected-output leakage avoided**

## 9. Validation / pytest triage

### Touched implementation / test scope

Files added:
- `weslr/arc_style_synthetic_diagnostic_runner.py`
- `weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`

Files changed:
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/tests/test_arc_style_grid_solver_dry_run_v1.py`

### The 3 focused pytest failures from the prior lane

1. `test_rotate_object_canvas_family_is_inferred_for_canvas_level_rotation`
   - status before this lane: failing
   - diagnosis: **real narrow regression**
   - cause: rotate-canvas inference branch was immediately overwritten by a stray reflect candidate assignment
   - action: removed the overwrite
   - status now: **resolved**

2. `test_each_supported_toy_task_chooses_the_expected_primitive_family`
   - status before this lane: failing on `recolor_symbol -> line_completion`
   - diagnosis: **real narrow regression**
   - cause: line-completion inference accepted pure recolor edits because its fit check did not require background-to-line filling semantics
   - action: tightened `_infer_line_completion_parameters(...)` so changed cells must be same-row background-to-line fills
   - status now: **resolved**

3. `test_reflect_object_family_remains_unsupported_honestly`
   - status before this lane: failing
   - diagnosis: **stale expectation**, not a fresh code regression
   - cause: dry-run now infers `reflect_object_horizontal_or_vertical` with `train_fit_status = fit`, while suite-level support classification still reports the family as unsupported
   - action: updated the dry-run test to reflect current dry-run behavior without weakening suite-level unsupported reporting
   - status now: **resolved as stale-test triage**

### Validation status

Validation commands run for this lane:
- `python3 -m py_compile weslr/arc_style_grid_solver_dry_run.py weslr/arc_style_synthetic_diagnostic_runner.py weslr/tests/test_arc_style_grid_solver_dry_run_v1.py weslr/tests/test_arc_style_synthetic_diagnostic_runner_v1.py`
- focused pytest for runner / dry-run / synthetic suite / generator / stress
- `python3 weslr/tests/release_gate_v1.py`
- `git diff --check`
- `bash scripts/weslr_release_check.sh`
- `bash scripts/chat_weslr_de_health_check.sh --mode source-repo`

Validation result:
- `py_compile`: **PASS**
- focused pytest (`test_arc_style_synthetic_diagnostic_runner_v1.py`, `test_arc_style_synthetic_solver_suite_v1.py`, `test_arc_style_grid_solver_dry_run_v1.py`, `test_arc_style_synthetic_task_generators_v1.py`, `test_arc_style_grid_generalization_stress_v1.py`): **PASS**
- `python3 weslr/tests/release_gate_v1.py`: **PASS**
- `git diff --check`: **PASS**
- `bash scripts/weslr_release_check.sh`: **PASS**
- `bash scripts/chat_weslr_de_health_check.sh --mode source-repo`: **PASS** (with expected optional non-runtime-host WARN probes)

## 10. What this score does and does not prove

What it proves:
- committed code now has a deterministic named synthetic diagnostic runner
- the post-`complete_symmetry` variant-2 fix remains stable in a canonical diagnostic run
- the metadata-dependency question can be rerun from committed code
- leakage boundaries stayed intact

What it does **not** prove:
- ARC-AGI-2 readiness
- public benchmark performance
- hidden-benchmark competence
- production/runtime wiring readiness
- final-answer authority
- replay/scoring/candidate-output-surface behavior

## 11. Recommended next lane

Primary:
- `REPAIR_ARC_SYNTHETIC_COPY_GRID_VARIANT_2_AND_STRIPPED_ROTATE_METADATA_DEPENDENCY_V1`

Reason:
- the new runner is canonized
- the remaining canonical non-exact pockets are now explicit and reproducible
- the biggest remaining live issues are `copy_grid` variant 2, the one `object_count_to_pattern` packet mismatch, and stripped metadata dependency in `rotate_object_90`

Secondary only if the operator wants suite support expansion work:
- `DESIGN_ARC_REFLECT_SUITE_SUPPORT_BOUNDARY_V1`

Reason:
- reflect dry-run inference now exists
- suite-level support classification still intentionally leaves the family unsupported
- that boundary should be changed only deliberately, not silently inside a diagnostic lane