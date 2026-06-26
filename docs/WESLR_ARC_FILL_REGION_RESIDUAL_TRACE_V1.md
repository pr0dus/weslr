# WESLR ARC Fill Region Residual Trace V1

## 1. State summary

- Known-family baseline: `41 / 3 / 4 / 0`
- Current held-out total: `10 / 2 / 2 / 0`
- Remaining blocker status:
  - `fill_region_then_extract_object`: `0 / 2 / 0 / 0`
  - `rotate_then_recolor`: `0 / 0 / 2 / 0`
- This is a trace-only lane: it records why fill remains partial under the current safe primitive set and does not change solver behavior.

## 2. Candidate execution trace

Family traced: `fill_region_then_extract_object`

### Candidates considered
- Recipe-specific depth-2 candidate using `fill_region` + `extract_largest_object`
- Alternate depth-1 fallback using `extract_largest_object`

### Candidates executed
- The depth-2 recipe-specific candidate executed on train and held-out.
- The depth-1 fallback was ranked but not selected.

### Candidates rejected
- The depth-1 fallback was rejected because it left the interior unfilled on train.
- No candidate was rejected for missing primitive support.
- No candidate was rejected because of depth limit.
- No candidate was rejected because of cap/pruning pressure.

### Exact train-fit candidate behavior
- Variant 0: `fill_region(border_value=0) -> extract_largest_object(background_value=0)`
  - Train: exact on both train pairs.
  - Held-out: partial.
- Variant 1: same structural candidate with the same behavior.
  - Train: exact on both train pairs.
  - Held-out: partial.

### Exact-on-train but partial-on-held-out?
- Yes.
- The selected depth-2 candidate is exact on train and partial on held-out for both fill variants.

### Cause category
- This is not a primitive-availability failure.
- This is primarily a parameter-under-determination failure:
  - the fill color is train-inferable but not held-out-inferable from the safe input-only signals
  - the held-out color/orientation drift is not predicted by the train evidence
  - ranking is not the blocker
  - ordering is not the blocker
  - the safe primitive set is sufficient for the train shape but not sufficient to generalize the held-out color/orientation choice

## 3. Parameter trace

### Fill color inference
- Train variant 0 output color: `8`
- Train variant 1 output color: `2`
- Held-out expected output colors: `3` and `5`
- The train pairs consistently support a fill color, but they do not expose a safe input-side signal that predicts the held-out color.

### Background inference
- Background is consistently inferred as `0`.
- Background inference is stable and not the source of the residual failure.

### Region geometry inference
- Geometry is stable: the rectangular interior is the region to fill.
- The geometry is already captured correctly by the current safe candidate.

### Crop/bbox inference
- `crop_to_non_background_bbox` is not required for the selected train-exact candidate.
- No crop/bbox mismatch is visible in the selected candidate path.

### Object orientation inference
- The residual mismatch includes orientation-style drift in the ledger.
- The train evidence does not provide a reliable orientation lock that resolves the held-out drift.

### Train evidence vs held-out behavior
- Train examples do not determine the held-out fill color.
- Train examples do not determine the held-out orientation-related residual.
- The held-out drift is therefore not safely predictable from the current train-only evidence.

## 4. Output mismatch trace

Observed residual mismatch categories for `fill_region_then_extract_object`:
- `wrong color`
- `wrong reflection/rotation orientation`

Not observed in the final selected trace:
- `extra pixels`
- `missing pixels`
- `bbox/crop mismatch`
- `background mismatch`
- `output-size mismatch`

Interpretation:
- The selected candidate gets the fill geometry right.
- The residual is semantic/color-orientation drift, not shape construction failure.

## 5. Existing primitive sufficiency

Current safe primitives reviewed for this family:
- `fill_region`
- `extract_largest_object`
- `crop_to_non_background_bbox`
- `place_object_on_new_canvas`
- `preserve_input_canvas`

Judgment:
- These primitives are enough to express the train-exact fill behavior.
- They are not enough, under current train-only evidence, to safely infer the held-out fill color/orientation.
- No additional safe primitive in this set resolves the residual ambiguity without introducing unsupported inference.

## 6. Counterfactual safe repair options

Evaluated without implementation:
- Stricter color consistency rule: would still not recover the held-out color from current train evidence.
- Train-only orientation lock: would not resolve the residual drift without a new input-side signal.
- Bbox/crop stabilization: not the blocker.
- Fill-region geometry refinement: geometry is already stable.
- Reject-underconstrained-fill candidate: already effectively the conclusion; the family is underdetermined for held-out color/orientation.
- Alternate ranking penalty: not the blocker.
- Safe failure / no more fill repair: supported by the trace.

## 7. Saturation decision

Decision: `DECLARE_ARC_FILL_REGION_SAFE_SATURATION_V1`

Reason:
- Train evidence supports the current fill geometry.
- Held-out color/orientation drift is not recoverable from the current safe input-only signal set.
- Another fill-only repair would likely add inference pressure without a grounded held-out discriminator.

## 8. Next-lane recommendation

Primary next lane: `DESIGN_ARC_SAFE_ROTATE_OBJECT_CANVAS_V1`

Fallback lane: `DECLARE_ARC_FILL_REGION_SAFE_SATURATION_V1`

## 9. UNKNOWN ENGINE pressure summary

- Pressure diagnosis: the residual failure is an unknown/underdetermined color-orientation gap, not a search-depth gap.
- Gap hypothesis: the fill family needs a different safe discriminator or should remain saturated under current constraints.
- Bounded next intervention: move to safe rotation-canvas design rather than widening fill inference.
- Measurable success criteria for any future fill implementation:
  - held-out exact improves above `10`
  - partial drops below `2` if fill is repaired
  - unsupported remains no worse than `2`
  - known-family baseline remains `41 / 3 / 4 / 0`
  - no leakage
  - deterministic run stable
  - controlled improvement evidence updated only after measured implementation improvement
