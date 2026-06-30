# WESLR Complete Symmetry Variant 2 Investigation / Fix V1

- Dispatch: `FIX_COMPLETE_SYMMETRY_VARIANT_2_GENERATOR_V1`
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `86c008e9`
- Lane scope note: `WESLR_CURRENT_HANDOFF.md` verified HEAD `9ed508db...` was treated as stale for this lane only, per operator instruction.
- Handoff file action: not modified.

## Handoff mismatch recorded

Observed at lane start:
- actual repo HEAD: `86c008e9`
- `WESLR_CURRENT_HANDOFF.md` verified HEAD: `9ed508dbdc7899774c7ca19e932a04c3842f584d`

This mismatch was recorded here only. `WESLR_CURRENT_HANDOFF.md` was not rewritten.

## Investigation result

The previously-reported `empty test_input` diagnosis for `synthetic_complete_symmetry_variant_2_v1` was stale in this lane.

Current `86c008e9` evidence showed:
- the generator produced valid `test_inputs`
- the task family remained `complete_symmetry`
- the problematic behavior came from solver-side structural inference, not from missing generator data

## Actual root cause

In `weslr/arc_style_grid_solver_dry_run.py`, `_infer_line_completion_parameters(...)` allowed a degenerate exact match when `input_grid == output_grid`.

For `synthetic_complete_symmetry_variant_2_v1`, the centered train pair is already symmetry-complete, so the raw train-pair inference path could misclassify that unchanged pair as `line_completion` instead of leaving it available for `complete_symmetry`.

That created inconsistent per-pair exact-family evidence in the raw structural inference path:
- two pairs inferred as `complete_symmetry`
- one unchanged centered pair inferred as degenerate `line_completion`

Once the exact-family set became inconsistent, the raw inference fallback path could degrade into unsupported fallback candidates instead of preserving the symmetry family.

## Narrow fix applied

File changed:
- `weslr/arc_style_grid_solver_dry_run.py`

Change:
- `_infer_line_completion_parameters(...)` now returns `None` immediately when `input_grid == output_grid`.

Effect:
- unchanged grids no longer count as degenerate `line_completion`
- the centered variant-2 symmetry pair remains classifiable as `complete_symmetry`
- the raw inference path for `synthetic_complete_symmetry_variant_2_v1` becomes internally consistent again

## Test coverage added

File changed:
- `weslr/tests/test_arc_style_grid_solver_dry_run_v1.py`

Added test:
- `test_complete_symmetry_variant_2_selects_complete_symmetry_not_degenerate_line_completion`

It verifies that the packetized solver path selects `complete_symmetry` for `synthetic_complete_symmetry_variant_2_v1`.

## Validation notes

Confirmed after fix:
- direct structural inference on raw `synthetic_complete_symmetry_variant_2_v1` now emits `symmetry_completion` only
- raw candidate blueprint selection now keeps `complete_symmetry` as the primary exact candidate instead of falling back through the prior inconsistent-family path
- packetized bounded solver run for `synthetic_complete_symmetry_variant_2_v1` selects:
  - `selected_candidate_id = synthetic_complete_symmetry_variant_2_v1:complete_symmetry:0`
  - `train_fit_status = fit`

## Scope conclusion

This lane did **not** confirm a generator defect in current HEAD `86c008e9`.
The confirmed defect was a narrow solver-side degenerate inference allowance affecting the variant-2 investigation path.
