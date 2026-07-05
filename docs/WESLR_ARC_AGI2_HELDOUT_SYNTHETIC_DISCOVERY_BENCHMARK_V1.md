# WESLR ARC-AGI2 Held-Out Synthetic Discovery Benchmark V1

## Repo / branch
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Start / end state
- Original expected HEAD: `a9fcd6aeaaa594458f0fb4d3b93d95046a797762`
- Actual preflight HEAD: `a9fcd6aeaaa594458f0fb4d3b93d95046a797762`
- End HEAD: `0b118d83d4554fc55b4ebd177d111d9bc22562c2`
- Commit status: committed (`Implement ARC-AGI2 held-out synthetic discovery benchmark V1`)

## HEAD reconciliation
- `git rev-parse HEAD` → `a9fcd6aeaaa594458f0fb4d3b93d95046a797762`
- `git status --short` →
  - `?? docs/WESLR_ARC_AGI2_TASK_FEATURE_SIGNATURE_EXTRACTOR_V1.md`
  - `?? scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py`
  - `?? weslr/arc_heldout_synthetic_discovery_benchmark_v1.py`
  - `?? weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py`
- Ancestry: benchmark lane continued from the owner-approved head without solver tuning

## Files added/changed
- Added: `weslr/arc_heldout_synthetic_discovery_benchmark_v1.py`
- Added: `scripts/run_arc_heldout_synthetic_discovery_benchmark_v1.py`
- Added: `weslr/tests/test_arc_heldout_synthetic_discovery_benchmark_v1.py`
- Added: `docs/WESLR_ARC_AGI2_HELDOUT_SYNTHETIC_DISCOVERY_BENCHMARK_V1.md`

## Benchmark split design
- `dev` and `heldout` are synthetic-only splits built from the existing ARC-AGI2 synthetic discovery families.
- Seeds differ by split; dev is smoke-only, heldout is the measured benchmark split for this lane.
- Only `train_pairs` and `test_input` are forwarded to the universal runner.
- `expected_output` stays evaluator-side only.

## Seeds and configuration
- Dev seed: `2435`
- Heldout seed: `82435`
- Dev config: `tasks_per_family=3`, adversarial on, compositions on
- Heldout config: `tasks_per_family=5`, adversarial on, compositions on

## Dev results
- total tasks: `81`
- attempt 1 solved: `36`
- attempt 2 solved: `0`
- solved total: `36`
- unsolved total: `45`
- malformed: `0`
- fallback only: `39`
- exact two output pass: `True`
- composition solved count: `6`
- adversarial rejection pass: `15`
- adversarial rejection fail: `6`
- exception count: `6`
- deterministic replay pass: `True`

## Heldout results
- total tasks: `135`
- attempt 1 solved: `60`
- attempt 2 solved: `0`
- solved total: `60`
- unsolved total: `75`
- malformed: `0`
- fallback only: `65`
- exact two output pass: `True`
- composition solved count: `10`
- adversarial rejection pass: `25`
- adversarial rejection fail: `10`
- exception count: `10`
- deterministic replay pass: `True`

## Exact-two-output status
- Dev: `True`
- Heldout: `True`

## Deterministic replay status
- Dev: `True`
- Heldout: `True`
- Split replay/isolation overall: `True`

## Expected-output isolation status
- `expected_output` kept evaluator-side: `True`

## Split disjoint status
- Dev/heldout task-id disjointness: `True`

## Failure category summary
- Dev: `{'ambiguous_expected_rejection': 15, 'exception': 6, 'fallback_only': 24}`
- Heldout: `{'ambiguous_expected_rejection': 25, 'exception': 10, 'fallback_only': 40}`

## Per-family summary — dev
| family | generated | solved | unsolved | fallback | exception | dominant failure |
|---|---:|---:|---:|---:|---:|---|
| add_uniform_border | 3 | 3 | 0 | 0 | 0 | none |
| ambiguous_multiple_rules | 3 | 3 | 0 | 0 | 0 | none |
| count_objects_to_line | 3 | 3 | 0 | 0 | 0 | none |
| count_tie_ambiguity | 3 | 0 | 3 | 3 | 0 | ambiguous_expected_rejection |
| crop_foreground_bbox | 3 | 3 | 0 | 0 | 0 | none |
| crop_largest_object | 3 | 0 | 3 | 0 | 3 | exception |
| crop_then_recolor | 3 | 0 | 3 | 3 | 0 | fallback_only |
| crop_then_rotate_or_reflect | 3 | 0 | 3 | 3 | 0 | fallback_only |
| crop_then_tile | 3 | 3 | 0 | 0 | 0 | none |
| inconsistent_train_examples | 3 | 0 | 3 | 3 | 0 | ambiguous_expected_rejection |
| near_match_one_cell | 3 | 0 | 3 | 3 | 0 | ambiguous_expected_rejection |
| object_count_to_square | 3 | 3 | 0 | 0 | 0 | none |
| recolor_foreground | 3 | 3 | 0 | 0 | 0 | none |
| recolor_then_border | 3 | 0 | 3 | 3 | 0 | fallback_only |
| reflect_object_horizontal | 3 | 0 | 3 | 3 | 0 | fallback_only |
| reflect_object_vertical | 3 | 0 | 3 | 3 | 0 | fallback_only |
| rotate_object_180 | 3 | 0 | 3 | 3 | 0 | fallback_only |
| rotate_object_90 | 3 | 3 | 0 | 0 | 0 | none |
| same_geometry_wrong_recolor | 3 | 0 | 3 | 3 | 0 | ambiguous_expected_rejection |
| same_palette_wrong_geometry | 3 | 0 | 3 | 3 | 0 | ambiguous_expected_rejection |
| scale_cells_integer | 3 | 3 | 0 | 0 | 0 | none |
| select_largest_object | 3 | 0 | 3 | 0 | 3 | exception |
| select_then_recolor | 3 | 3 | 0 | 0 | 0 | none |
| swap_two_colors | 3 | 0 | 3 | 3 | 0 | fallback_only |
| tile_grid | 3 | 3 | 0 | 0 | 0 | none |
| translate_single_object | 3 | 0 | 3 | 3 | 0 | fallback_only |
| unsupported_primitive_chain | 3 | 3 | 0 | 0 | 0 | none |

## Per-family summary — heldout
| family | generated | solved | unsolved | fallback | exception | dominant failure |
|---|---:|---:|---:|---:|---:|---|
| add_uniform_border | 5 | 5 | 0 | 0 | 0 | none |
| ambiguous_multiple_rules | 5 | 5 | 0 | 0 | 0 | none |
| count_objects_to_line | 5 | 5 | 0 | 0 | 0 | none |
| count_tie_ambiguity | 5 | 0 | 5 | 5 | 0 | ambiguous_expected_rejection |
| crop_foreground_bbox | 5 | 5 | 0 | 0 | 0 | none |
| crop_largest_object | 5 | 0 | 5 | 0 | 5 | exception |
| crop_then_recolor | 5 | 0 | 5 | 5 | 0 | fallback_only |
| crop_then_rotate_or_reflect | 5 | 0 | 5 | 5 | 0 | fallback_only |
| crop_then_tile | 5 | 5 | 0 | 0 | 0 | none |
| inconsistent_train_examples | 5 | 0 | 5 | 5 | 0 | ambiguous_expected_rejection |
| near_match_one_cell | 5 | 0 | 5 | 5 | 0 | ambiguous_expected_rejection |
| object_count_to_square | 5 | 5 | 0 | 0 | 0 | none |
| recolor_foreground | 5 | 5 | 0 | 0 | 0 | none |
| recolor_then_border | 5 | 0 | 5 | 5 | 0 | fallback_only |
| reflect_object_horizontal | 5 | 0 | 5 | 5 | 0 | fallback_only |
| reflect_object_vertical | 5 | 0 | 5 | 5 | 0 | fallback_only |
| rotate_object_180 | 5 | 0 | 5 | 5 | 0 | fallback_only |
| rotate_object_90 | 5 | 5 | 0 | 0 | 0 | none |
| same_geometry_wrong_recolor | 5 | 0 | 5 | 5 | 0 | ambiguous_expected_rejection |
| same_palette_wrong_geometry | 5 | 0 | 5 | 5 | 0 | ambiguous_expected_rejection |
| scale_cells_integer | 5 | 5 | 0 | 0 | 0 | none |
| select_largest_object | 5 | 0 | 5 | 0 | 5 | exception |
| select_then_recolor | 5 | 5 | 0 | 0 | 0 | none |
| swap_two_colors | 5 | 0 | 5 | 5 | 0 | fallback_only |
| tile_grid | 5 | 5 | 0 | 0 | 0 | none |
| translate_single_object | 5 | 0 | 5 | 5 | 0 | fallback_only |
| unsupported_primitive_chain | 5 | 5 | 0 | 0 | 0 | none |

## Comparison to previous synthetic generator run
- Prior run context: 81 tasks, 36 attempt_1 solved, 45 unsolved, 39 fallback-only, 6 exceptions.
- Dev split reproduces that context exactly for the same seed and lower task-per-family setting: `81` tasks, `36` attempt_1 solved, `45` unsolved, `39` fallback-only, `6` exceptions.
- Heldout is larger and harder: `135` tasks, `60` attempt_1 solved, `75` unsolved, `65` fallback-only, `10` exceptions.

## Limitations
- Synthetic-only benchmark; no public ARC data was read.
- The benchmark measures current solver behavior; it does not repair families or tune the solver.
- Some families are intentionally adversarial or ambiguous and will remain unsolved.

## Next recommended lane
- Failure cluster repair lane.
