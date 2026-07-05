# WESLR ARC-AGI2 Synthetic Discovery Task Generator V1

## Repo / branch
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Start / end state
- Original expected HEAD: `1bdad9e485aa737f83c1abd40fe4567c211703ce`
- Actual preflight HEAD: `1bdad9e485aa737f83c1abd40fe4567c211703ce`
- End HEAD: `23711414c8f8da308a4b3a249481d0558ae39916`
- Commit status: committed (`Implement ARC-AGI2 synthetic discovery task generator V1`)

## HEAD reconciliation
- `git rev-parse HEAD` → `1bdad9e485aa737f83c1abd40fe4567c211703ce`
- `git status --short` →
  - `M weslr/tests/test_arc_universal_family_runner_v1.py`
  - `?? scripts/run_arc_synthetic_discovery_task_generator_v1.py`
  - `?? weslr/arc_synthetic_discovery_eval_v1.py`
  - `?? weslr/arc_synthetic_discovery_task_generator_v1.py`
  - `?? weslr/tests/test_arc_synthetic_discovery_eval_v1.py`
  - `?? weslr/tests/test_arc_synthetic_discovery_task_generator_v1.py`
  - plus the unrelated dirty file kept untouched: `docs/WESLR_ARC_AGI2_TASK_FEATURE_SIGNATURE_EXTRACTOR_V1.md`
- `git merge-base --is-ancestor 1bdad9e485aa737f83c1abd40fe4567c211703ce HEAD; echo $?` → `0`
- Ancestry verdict: safe to continue from current HEAD `1bdad9e485aa737f83c1abd40fe4567c211703ce`

## Files added/changed
- Added: `weslr/arc_synthetic_discovery_task_generator_v1.py`
- Added: `weslr/arc_synthetic_discovery_eval_v1.py`
- Added: `weslr/tests/test_arc_synthetic_discovery_task_generator_v1.py`
- Added: `weslr/tests/test_arc_synthetic_discovery_eval_v1.py`
- Added: `scripts/run_arc_synthetic_discovery_task_generator_v1.py`
- Updated: `weslr/tests/test_arc_universal_family_runner_v1.py`
- Added: `docs/WESLR_ARC_AGI2_SYNTHETIC_DISCOVERY_TASK_GENERATOR_V1.md`

## Generator summary
- Produces deterministic synthetic ARC-style tasks only.
- Covers single-step, two-step composition, and adversarial/rejection cases.
- Keeps task records JSON-safe and compact.
- No public ARC data, no scoring, no submission, no solver-visible expected outputs.

## Supported family list
- Single-step: `crop_foreground_bbox`, `crop_largest_object`, `translate_single_object`, `rotate_object_90`, `rotate_object_180`, `reflect_object_horizontal`, `reflect_object_vertical`, `recolor_foreground`, `swap_two_colors`, `tile_grid`, `scale_cells_integer`, `add_uniform_border`, `count_objects_to_line`, `object_count_to_square`, `select_largest_object`
- Two-step: `crop_then_recolor`, `crop_then_rotate_or_reflect`, `crop_then_tile`, `recolor_then_border`, `select_then_recolor`
- Adversarial/rejection: `inconsistent_train_examples`, `ambiguous_multiple_rules`, `unsupported_primitive_chain`, `near_match_one_cell`, `same_palette_wrong_geometry`, `same_geometry_wrong_recolor`, `count_tie_ambiguity`

## Adversarial case list
- Inconsistent train examples
- Ambiguous multiple rules
- Unsupported primitive chain
- Near match with one-cell mismatch
- Same palette, wrong geometry
- Same geometry, wrong recolor
- Count ambiguity / ties

## Deterministic seed behavior
- Corpus generation is deterministic for a fixed seed.
- Different seeds change the corpus identity via task ids and seed fields.
- Determinism was verified with same-seed replay equality.

## Evaluation runner summary
- Evaluates synthetic tasks by passing only `train_pairs` and `test_input` to the universal runner.
- Compares attempt 1 and attempt 2 against synthetic `expected_output` after solver output is produced.
- Records solved/unsolved, fallback-only, malformed, composition, and adversarial rejection behavior.
- Keeps reports compact and metadata-safe.

## Synthetic run configuration
- Command: `python scripts/run_arc_synthetic_discovery_task_generator_v1.py --seed 2435 --tasks-per-family 3 --include-adversarial --include-compositions`
- Corpus size: `81`
- Structure: `27` family labels × `3` variants each

## Synthetic run results
- Total tasks: `81`
- Solved by attempt 1: `36`
- Solved by attempt 2: `0`
- Unsolved: `45`
- Malformed: `0`
- Fallback-only: `39`
- Exact-two-output: `PASS`
- Composition solved count: `6`
- Adversarial rejection: `15` pass / `6` fail
- Deterministic replay status: `PASS`

## Per-family summary
- Generated: `3` tasks for every listed family.
- Solved families in this run: `crop_foreground_bbox`, `rotate_object_90`, `recolor_foreground`, `tile_grid`, `scale_cells_integer`, `add_uniform_border`, `count_objects_to_line`, `object_count_to_square`, `crop_then_tile`, `select_then_recolor`, plus the synthetic accept/reject cases that were intentionally solved or rejected by the evaluator.
- Harder or unsupported families mostly fell back or errored in the current source-repo run.

## Failure category summary
- `fallback_only`: `24`
- `ambiguous_expected_rejection`: `15`
- `exception`: `6`

## Exact-two-output status
- Universal runner exact-two-output contract passed on the synthetic corpus run.

## Expected-output isolation statement
- `expected_output` stays in the synthetic task/evaluation layer only.
- The solver-visible packet helper passes only `train_pairs` and `test_input` to the universal runner.
- This was verified by unit test.

## Validation summary
- `python -m py_compile weslr/arc_synthetic_discovery_task_generator_v1.py weslr/arc_synthetic_discovery_eval_v1.py weslr/arc_universal_family_runner_v1.py` ✅
- `python -m pytest -q weslr/tests/test_arc_synthetic_discovery_task_generator_v1.py weslr/tests/test_arc_synthetic_discovery_eval_v1.py` ✅
- `python -m pytest -q weslr/tests/test_arc_universal_family_runner_v1.py weslr/tests/test_arc_compositional_executor_v1.py` ✅
- `python -m pytest -q weslr/tests/test_arc_primitive_discovery_engine_v1.py weslr/tests/test_arc_family_discovery_engine_v1.py` ✅
- `git diff --check` ✅
- `python weslr/tests/release_gate_v1.py` ✅
- `./scripts/weslr_release_check.sh` ✅
- `./scripts/chat_weslr_de_health_check.sh --mode source-repo` ✅ (`PASS=6 FAIL=0 WARN=3 SKIP=0`)

## Limitations
- Synthetic-only lane.
- No public ARC data was read.
- No scoring or submission.
- Some synthetic families are intentionally hard or unresolved with the current source-repo runner.

## Next recommended lane
- Held-out discovery benchmark lane.
