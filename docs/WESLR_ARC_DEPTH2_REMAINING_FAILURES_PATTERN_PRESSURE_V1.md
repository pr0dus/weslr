# WESLR ARC Depth-2 Remaining Failures Pattern Pressure V1

## Status
Diagnostic/report-only. No implementation, no depth-3 search, no public ARC/Kaggle contact, no solver tuning, no `.weslr` writes.

## 1. State summary

Observed synthetic-only state:

- Known-family baseline: `41 / 3 / 4 / 0`
- Held-out compositional before depth-2: `1 / 2 / 11 / 0`
- Held-out compositional after depth-2: `5 / 5 / 4 / 0`
- Exact improvement: `+4`
- Unsupported reduction: `11 -> 4`

Per-recipe held-out summary after depth-2:

- `count_object_then_emit_pattern`: `0 / 0 / 2 / 0`
- `extract_object_then_recolor`: `2 / 0 / 0 / 0`
- `fill_region_then_extract_object`: `0 / 2 / 0 / 0`
- `move_then_border`: `0 / 2 / 0 / 0`
- `reflect_then_recolor`: `2 / 0 / 0 / 0`
- `remove_noise_then_complete_line`: `1 / 1 / 0 / 0`
- `rotate_then_recolor`: `0 / 0 / 2 / 0`

Mismatch categories after depth-2 search:

- `extra pixels=4`
- `missing pixels=5`
- `output-size mismatch=4`
- `wrong color=9`
- `wrong count=5`
- `wrong position=7`
- `wrong reflection/rotation orientation=9`

## 2. Pattern-pressure diagnosis

### `count_object_then_emit_pattern` — unsupported `2/2`

This looks like a missing or weak count-to-pattern lane, not a general compositional failure.

Observed pressure:
- both variants stayed unsupported
- mismatch categories include output-size mismatch and wrong count elsewhere in the suite
- the recipe path depends on `remove_background_noise` -> `object_count_to_pattern`

Diagnosis:
- count extraction is probably happening, but the downstream pattern construction is not stabilizing into a valid exact program
- the pattern output shape may be too narrow or too rigid
- the program may be losing `row_index` / output-shape selection pressure

### `rotate_then_recolor` — unsupported `2/2`

This points to weak rotate/recolor composition support, not just a color-map issue.

Observed pressure:
- both variants unsupported
- mismatch categories strongly include wrong reflection/rotation orientation
- the recipe path depends on `rotate_object_90` -> `recolor_symbol`

Diagnosis:
- rotation candidate generation may be too brittle on axis/shape evidence
- recolor ranking may be arriving too late or with the wrong structural candidate
- the composition is probably not being generated, ranked, or executed with the right parameter pairing

### `fill_region_then_extract_object` — partial `2/2`

This is a near-fit, not a hard capability gap.

Observed pressure:
- both variants partial
- mismatch categories elsewhere show extra pixels, missing pixels, and output-size mismatch

Diagnosis:
- the fill/extract chain likely builds the right family but loses exact region boundaries
- the issue looks more like wrong region geometry than missing primitive coverage
- a parameter/ranking repair is likely more urgent than deeper search

### `move_then_border` — partial `2/2`

This also looks like a structural near-fit with ordering/position pressure.

Observed pressure:
- both variants partial
- mismatch categories emphasize wrong position, extra/missing pixels, and output-size mismatch

Diagnosis:
- move may be inferred correctly on one train pair but not stabilized across variants
- border application may be correct in spirit but wrong in order, extent, or frame value
- candidate ranking likely needs stronger exactness pressure before adding more depth

### `remove_noise_then_complete_line` — partial `1/2`

This is the weakest partial family and looks underfit rather than unsupported.

Observed pressure:
- one exact, one partial
- line-span and line-color are the obvious fragility points

Diagnosis:
- the denoise step likely works
- completion underfits line span or line coloring on one variant
- the issue is probably parameter proposal / ranking, not missing depth

## 3. Gap hypotheses

### H1 — missing or weak count-to-pattern parameter proposal

The count family still fails both variants. That suggests the `object_count_to_pattern` proposal path is not robust enough, or the candidate set is too narrow.

### H2 — missing shape/output-size construction after count

The remaining mismatches include output-size mismatch, wrong count, extra pixels, and missing pixels. That suggests the count lane may need shape construction pressure, not just count inference.

### H3 — rotate/recolor composition is not being generated, ranked, or executed correctly

The rotate family is fully unsupported. That is consistent with broken candidate generation or ordering, not merely a bad parameter choice.

### H4 — fill/extract composition produces wrong region or extra/missing pixels

The fill/extract family is partial on both variants. That suggests a geometry mismatch rather than a missing primitive.

### H5 — move/border composition produces wrong position or border order

The move/border family is partial on both variants. The likely issue is ordering, extent, or frame-value inference.

### H6 — remove-noise/complete-line underfits line span or color

This family is close but not stable. The pressure looks like a line span / row-index / line-value repair problem.

### H7 — the mismatch profile argues for depth-2 parameter/ranking repair before depth-3

The current failure shape is mostly partial and unsupported, with strong mismatch signatures that look repairable inside depth-2. That makes a parameter/ranking repair lane more urgent than jumping to depth-3.

## 4. Option comparison

### A. depth-2 parameter/ranking repair

Pros:
- directly targets the observed partial/unsupported mix
- likely to recover exacts without changing the search depth
- keeps the current evidence boundary intact

Cons:
- may not fully solve the rotate/count family if candidate support itself is missing

### B. add missing depth-2 primitive-pair candidate support for count/rotate recipes

Pros:
- targets the two fully unsupported families directly
- likely necessary if the current candidate catalog is too thin

Cons:
- overlaps with repair work and may be more invasive than pure ranking fixes

### C. implement depth-3 search

Pros:
- could help if some recipes truly need three steps

Cons:
- current residuals do not yet justify depth-3 as the first move
- risks hiding a depth-2 candidate-generation defect

### D. expand held-out suite before repair

Pros:
- increases diagnostic confidence

Cons:
- delays fixing the already visible failure mode
- does not address the current lane decision

### E. touch public ARC/Kaggle data

Pros:
- none for this lane

Cons:
- violates the current synthetic-only diagnostic boundary
- would overstep the evidence model

## 5. Recommended next lane

### Primary
`IMPLEMENT_ARC_DEPTH2_REMAINING_FAILURE_REPAIR_V1`

Reason:
Depth-2 already improved exact and reduced unsupported. The remaining partials and mismatch categories point to candidate repair, ranking pressure, and parameter stabilization before any depth-3 jump.

### Fallback
`DESIGN_ARC_DEPTH3_SEARCH_BOUNDARY_V1`

Use this only if a bounded review shows the remaining failures truly require three primitive steps rather than broken depth-2 support.

## 6. Decision criteria

Use these measurable checks for the next lane:

- held-out exact improves above `5`
- held-out unsupported drops below `4`
- known-family baseline remains `41 / 3 / 4 / 0` or has no material regression
- top-2 packets remain valid
- solver-visible expected outputs remain absent from packets
- deterministic run remains stable
- no leakage flags appear
- no public-data contact occurs

## 7. Non-goals

Explicitly out of scope for this lane:

- no implementation in this report-only lane
- no depth-3 implementation
- no public ARC/Kaggle data
- no Kaggle-ready claim
- no official score claim
- no UNKNOWN ENGINE solver-authority claim
- no provider/model/API calls
- no ChatResponder/respond_chat calls
- no website/runtime wiring
- no `.weslr` writes

## 8. Sources inspected

- `weslr/arc_style_depth2_compositional_program_search.py`
- `weslr/tests/test_arc_style_depth2_compositional_program_search_v1.py`
- `weslr/arc_style_heldout_compositional_baseline.py`
- `weslr/arc_style_heldout_compositional_synthetic_generator.py`
- `weslr/arc_style_typed_primitive_signatures.py`
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/arc_style_grid_adapter_phase2.py`
- `docs/WESLR_ARC_STYLE_COMPOSITIONAL_PROGRAM_SEARCH_AND_HELDOUT_SYNTHETIC_EVALUATION_DESIGN_V1.md`
- `docs/WESLR_ARC_RESIDUAL_GAP_INTERNAL_ENGINE_PRESSURE_V1.md`
