# WESLR ARC Remaining Failure Trace V1

## Status
Trace/report only. No solver behavior changes, no depth-3, no `rotate_object_canvas`, no public ARC/Kaggle contact.

## Context
- Repo: `weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Current HEAD: `4b36b52fd4ce5f0ceca7740f765b7df6adc2fbbf`
- Measurement snapshot:
  - Known-family baseline: `41 / 3 / 4 / 0`
  - Original held-out baseline: `1 / 2 / 11 / 0`
  - After depth-2 search: `5 / 5 / 4 / 0`
  - After depth-2 repair: `7 / 3 / 4 / 0`
  - After safe output-shape primitives: `9 / 3 / 2 / 0`

## Remaining blockers
- `fill_region_then_extract_object`: partial
- `remove_noise_then_complete_line`: partial
- `rotate_then_recolor`: unsupported

## Primitive execution trace summary

### `fill_region_then_extract_object`
- Considered candidates: 3 per held-out variant.
- Executed candidates:
  - `fill_region` → `extract_largest_object`
  - `extract_largest_object`
- Failed closed before execution: none observed.
- Rejected before execution: none observed.
- Selected top-2 always validated as structurally distinct packets.

### `remove_noise_then_complete_line`
- Considered candidates: 3 per held-out variant.
- Executed candidates:
  - `remove_background_noise` → `line_completion`
  - `extract_largest_object`
- Failed closed before execution: none observed.
- Rejected before execution: none observed.
- Selected top-2 validated cleanly.

### `rotate_then_recolor`
- Considered candidates: 2 per held-out variant.
- Executed candidates:
  - `rotate_object_90` → `recolor_symbol`
  - `extract_largest_object`
- Failed closed before execution: none observed.
- Rejected before execution: none observed.
- The safe set has no canvas-rotation primitive, so this family remains outside the V1 envelope.

## Parameter proposal trace summary

### `fill_region_then_extract_object`
- Train-derived parameter proposal stayed narrow:
  - `border_value` inferred from input border/background
  - `background_value` fixed from train pair background
- The exact held-out prediction stayed color-wrong for the remaining variant(s): predicted fill color `8`, expected `3`.
- The failure source is not grid validity; it is a color/shape mismatch between train-derived fill semantics and held-out output.
- `crop_to_non_background_bbox` did not become the chosen repair path because the train pair was already solved exactly by `fill_region` + `extract_largest_object`.

### `remove_noise_then_complete_line`
- Train-derived parameter proposal stayed bounded:
  - `background_value` from input background
  - `line_value` from output non-background color
  - `row_index` from dominant output row
- The remaining partial variant underfilled the line and placed pixels on the wrong row: predicted `[[5, 5, 0, 0, 0, 0], [5, 5, 5, 5, 5, 5], ...]`, expected `[[5, 5, 5, 5, 5, 0], ...]`.
- This points to span inference / row placement, not unsafe grid metadata.
- A safe span primitive is likely still missing for the partial case.

### `rotate_then_recolor`
- Train-derived parameter proposal is blocked by primitive availability, not by parameter syntax.
- The current proxy candidate uses `rotate_object_90` with object-value inference, but the held-out output needs canvas-level rotation and different canvas bounds.
- The failure is structural: the safe V1 primitive set does not include a canvas-rotation primitive.

## Candidate rejection trace summary
- Invalid grid: not observed in the remaining blockers.
- Invalid color: not observed in the remaining blockers.
- Invalid shape: not observed in the remaining blockers.
- Output-size mismatch: observed in `rotate_then_recolor`.
- Unsafe primitive position: not observed.
- Unsupported typed signature: not observed for the considered safe candidates.
- Candidate cap / pruning: not binding; the held-out families only surfaced 2-3 candidate packets each.
- Ranking penalty: shape-construction penalty did not drive selection away from the exact train-fit candidate in the fill family; the main issue is held-out mismatch, not ranking collapse.

## Top-2 ranking audit summary

### `fill_region_then_extract_object`
- Selected top-2:
  1. `fill_region` → `extract_largest_object` (exact on train, partial on held-out)
  2. `extract_largest_object` (partial on train, partial on held-out)
- No exact held-out candidate existed in the safe V1 candidate set.
- Structural diversity remained intact, but it did not change the outcome.

### `remove_noise_then_complete_line`
- Selected top-2:
  1. `remove_background_noise` → `line_completion` (partial on one variant, exact on the other)
  2. `extract_largest_object` (weak fallback)
- The exact train-fit candidate was selected; the issue is that the proposal is still underfitting the held-out line span / row placement.
- Structural diversity did not create a better safe alternative.

### `rotate_then_recolor`
- Selected top-2:
  1. `rotate_object_90` → `recolor_symbol`
  2. `extract_largest_object`
- The safe ranking is not the blocker; the primitive envelope is.
- There is no safe canvas-level rotation candidate to rank higher.

## Mismatch category trace summary

### `fill_region_then_extract_object`
- `wrong color`
- `wrong reflection/rotation orientation`
- No `output-size mismatch`
- No `extra pixels` / `missing pixels` on the held-out partial cases

### `remove_noise_then_complete_line`
- `extra pixels`
- `missing pixels`
- `wrong color`
- `wrong count`
- `wrong position`
- `wrong reflection/rotation orientation`

### `rotate_then_recolor`
- `extra pixels`
- `missing pixels`
- `output-size mismatch`
- `wrong color`
- `wrong position`
- `wrong reflection/rotation orientation`

## Counterfactual primitive-pair trace summary

### A. `fill_region_then_extract_object`
- Would a safe V1 primitive have helped? Possibly `crop_to_non_background_bbox`, but only if the held-out mismatch were bbox-related; the observed failures are primarily color/orientation drift.
- Would a risky/later primitive have helped? Not obviously; the failure is not canvas rotation.
- Would depth-3 actually be needed? Unlikely from the current trace; the best safe candidate already exists and solves train exactly.
- Root cause classification: parameter proposal is adequate for train, but held-out color/orientation mismatch remains; ordering is not the main issue.
- Safest next intervention: fill/crop trace repair focused on output-color and bbox consistency.

### B. `remove_noise_then_complete_line`
- Would a safe V1 primitive have helped? `crop_to_non_background_bbox` does not address the span/row issue; the gap is line-span inference.
- Would a risky/later primitive have helped? `derive_line_span_canvas` or a safe equivalent would likely address the underfilled span, but that primitive was intentionally not in V1.
- Would depth-3 actually be needed? Probably not; the current failure is a two-step parameterization gap, not a composition-depth gap.
- Root cause classification: parameter proposal / primitive availability for line span.
- Safest next intervention: a trace-repair lane for line-span parameterization, with a bounded safe span primitive if it can be designed without widening the envelope.

### C. `rotate_then_recolor`
- Would a safe V1 primitive have helped? No; the safe V1 set lacks canvas-level rotation.
- Would a risky/later primitive have helped? Yes, `rotate_object_canvas` is the obvious missing capability.
- Would depth-3 actually be needed? No clear evidence. The current failure is a primitive-capability gap, not a search-depth gap.
- Root cause classification: primitive availability, not parameter syntax.
- Safest next intervention: design-only work for a safe canvas rotation primitive, with strict bounding and fail-closed rules.

## UNKNOWN ENGINE pressure summary
- Unknown/failure/friction signal: the safe V1 envelope improved count-pattern completion, but two partial families still show shape/placement friction and one family remains outside the safe rotation envelope.
- Pressure diagnosis: the remaining gap is not general search depth; it is mixed primitive coverage and parameter proposal fidelity.
- Gap hypothesis: bounded safe fill/crop repair for color/shape consistency, bounded line-span repair for completion, and a separate design lane for safe canvas rotation.
- Bounded next intervention: do not expand to depth-3; instead split the remaining pressure into a fill/line trace repair lane and a rotate design lane.
- Measurable success criteria: held-out exact rises above `9`, unsupported drops below `2` if rotation is addressed, partial drops below `3` if fill/line is addressed, and known-family baseline stays unchanged.

## Recommended next lane
Primary: `IMPLEMENT_ARC_FILL_AND_LINE_TRACE_REPAIR_V1`

Fallback: `DESIGN_ARC_SAFE_ROTATE_OBJECT_CANVAS_V1`

## Notes
- No public ARC/Kaggle contact.
- No solver behavior changed.
- No depth-3 expansion was justified by this trace.
- No `rotate_object_canvas` implementation was performed.
