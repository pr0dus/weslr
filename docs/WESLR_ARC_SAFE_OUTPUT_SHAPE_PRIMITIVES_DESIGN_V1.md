# WESLR ARC Safe Output Shape Primitives Design V1

## Status
Design-only. No implementation, no solver behavior change, no depth-3, no public ARC/Kaggle contact, no runtime wiring, no `.weslr` writes.

## 1. State summary

Observed synthetic-only state:

- Known-family baseline: `41 / 3 / 4 / 0`
- Original held-out compositional baseline: `1 / 2 / 11 / 0`
- Held-out after depth-2 search: `5 / 5 / 4 / 0`
- Held-out after output-shape primitives: `9 / 3 / 2 / 0`
- Immediate pre-repair to repair movement: `7 / 3 / 4 / 0 -> 9 / 3 / 2 / 0`
- Exact delta vs original baseline: `+6`
- Partial delta vs original baseline: `+1`
- Unsupported delta vs original baseline: `-7`
- Exact delta vs pre-repair: `+2`
- Partial delta vs pre-repair: `-2`
- Unsupported delta vs pre-repair: `0`

Remaining clusters after repair:

- `count_object_then_emit_pattern`: `0 / 0 / 2 / 0`
- `rotate_then_recolor`: `0 / 0 / 2 / 0`
- `fill_region_then_extract_object`: `0 / 2 / 0 / 0`
- `remove_noise_then_complete_line`: `1 / 1 / 0 / 0`

Mismatch categories after repair:

- `extra pixels=5`
- `missing pixels=3`
- `output-size mismatch=4`
- `wrong color=7`
- `wrong count=3`
- `wrong position=5`
- `wrong reflection/rotation orientation=7`

## 2. Why output-shape construction is needed

The residual failures are not all depth-2 ranking defects. The remaining unsupported cases, especially `count_object_then_emit_pattern` and `rotate_then_recolor`, need primitives that can *construct or normalize the output canvas itself*, not just choose better parameters for existing canvas-preserving primitives.

### `count_object_then_emit_pattern`
Needs count-derived output construction:
- output width depends on the inferred count
- output height is small and fixed or train-derived
- the current `object_count_to_pattern` primitive can only paint onto an existing canvas, so it cannot safely create the final shape

### `rotate_then_recolor`
Needs safe rotated-object canvas/crop handling:
- the rotation result may need a bounded canvas that preserves object extent
- recoloring alone is insufficient when the rotated bounding box changes or when padding/background handling is decisive

### `fill_region_then_extract_object`
May need crop/bounding-box construction:
- train fit is close, but held-out still shows color/orientation mismatch pressure
- a crop or normalize-to-bbox helper can make the extracted object shape stable before recolor or subsequent placement

### `remove_noise_then_complete_line`
May need span-preserving construction:
- line completion is currently inferred on the existing grid, but the stable line span may need a dedicated construction step when row/column extent is the decisive factor

## 3. Candidate primitive families

### Safe for V1

| Primitive | Purpose | Notes |
|---|---|---|
| `construct_count_pattern` | Create a minimal output canvas whose width encodes the inferred count | Best fit for the unsupported count family |
| `crop_to_non_background_bbox` | Crop a grid to the tight non-background bounding box | Useful for rotate/crop/extract stability |
| `place_object_on_new_canvas` | Place a single object or bbox on a bounded canvas with explicit background | Helps rotate/crop/normalize flows |
| `preserve_input_canvas` | Explicitly keep the original canvas shape | Useful as a fail-closed no-op shape choice |

### Risky but possible later

| Primitive | Why risky |
|---|---|
| `rotate_object_canvas` | Easy to overfit if it starts inferring canvas extent from test-like structure |
| `normalize_object_to_bbox` | Useful, but can collapse needed background context if too aggressive |
| `construct_repeated_symbol_pattern` | Can drift into answer-key-like pattern synthesis if not tightly bounded |
| `derive_output_shape_from_train_delta` | Powerful, but too broad for V1 unless heavily constrained |
| `derive_line_span_canvas` | Useful for line completion, but easy to overgeneralize |

### Reject for now

| Primitive | Why reject now |
|---|---|
| `construct_constant_grid` | Too broad; can become a shape template shortcut |
| `preserve_object_canvas` | Too ambiguous unless it is just a constrained variant of `place_object_on_new_canvas` |
| `crop_to_object_bbox` | Acceptable only if it is strictly synonymous with non-background bbox crop; otherwise redundant |

## 4. Safety constraints for every primitive

Every candidate primitive must satisfy all of the following:

- deterministic inputs
- deterministic outputs
- rectangular-grid validation
- grid size bounds enforced
- color bounds limited to `0..9`
- no bool cells accepted
- no test-output access
- no public-data dependency
- no provider/model/API dependency
- no `.weslr` writes
- no hidden state
- no task-id hardcoding
- no recipe-name hardcoding
- no answer-key leakage
- fail-closed behavior on invalid or ambiguous inputs

## 5. Train-only parameter proposal

Output-shape parameters may be inferred only from train input/output pairs.

Allowed train-only signals:

- output height/width candidates from train outputs
- background color candidates from train inputs/outputs
- foreground color candidates from train outputs
- object count candidates from train inputs
- bounding-box candidates from train input/output comparison
- rotation or crop candidates from train geometry only
- emitted pattern dimensions from train outputs
- line span dimensions from train outputs

Explicitly forbidden:

- evaluation output access
- public ARC examples
- task IDs as direct hints
- recipe names as direct solver hints
- hardcoded held-out expected outputs
- any solver path that inspects test output before top-2 selection

## 6. Primitive-ranking interaction

Output-shape primitives should interact with depth-2 search as bounded structural candidates, not as unbounded generators.

Recommended placement:

- **first step** for `crop_to_non_background_bbox` or `preserve_input_canvas` when the shape decision drives the second primitive
- **second step** for `construct_count_pattern` after a count-producing primitive
- **terminal output constructor** for `place_object_on_new_canvas` when the final canvas shape is the main gap

Ranking rules:

- keep candidate count small and deterministic
- preserve top-2 structural diversity
- penalize shape overfitting when a candidate exactly matches train but uses unnecessary canvas expansion
- prefer the smallest shape that fits all train pairs
- do not let shape search inspect evaluation outputs

To avoid candidate explosion:

- cap output-shape variants per train pair
- keep at most one or two shape hypotheses per primitive family
- deduplicate by shape signature, not only by primitive name
- reject candidates that differ only by redundant padding

## 7. Recommended V1 subset

Smallest safe subset for implementation:

1. `construct_count_pattern`
2. `crop_to_non_background_bbox`
3. `place_object_on_new_canvas`
4. `preserve_input_canvas`

Why this subset:

- it directly addresses the unsupported count family
- it gives safe crop/normalize support for rotate and fill flows
- it adds a bounded canvas constructor without opening broad shape synthesis
- it keeps the initial footprint small enough for train-only ranking and top-2 diversity controls

`rotate_object_canvas` is intentionally deferred unless the crop/place subset still cannot separate rotate/crop failures safely.

## 8. Expected measurable effect

Success criteria for later implementation:

- held-out exact improves above `7`
- unsupported drops below `4`
- known-family baseline stays `41 / 3 / 4 / 0` or shows no material regression
- no leakage
- deterministic run stable
- evidence layer updated
- no public-data contact

## 9. Risks

- overfitting to held-out synthetic recipes
- shape-template leakage
- candidate explosion
- using train output shape too broadly
- accidentally building answer-key-like constructors
- weakening the synthetic generalization wall
- premature public ARC contact
- confusing crop helpers with hidden solver authority

Mitigations:

- strict train-only parameter inference
- small V1 primitive subset
- fail-closed validation
- no depth-3 change
- no task-id or recipe-name shortcuts
- keep shape candidates structurally simple and bounded

## 10. Decision

The code inspection and repair pattern support an output-shape construction design lane.

Recommended next implementation lane:

- `IMPLEMENT_ARC_SAFE_OUTPUT_SHAPE_PRIMITIVES_V1`

Fallback lane if later trace work shows the blocker is not shape construction:

- `RUN_ARC_REMAINING_FAILURE_TRACE_V1`

## 11. Boundary reminder

This design is synthetic-only, metadata-only, and train-only. It does not authorize solver behavior changes until explicitly implemented and reviewed.
