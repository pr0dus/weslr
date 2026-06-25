# WESLR ARC-Style Compositional Program Search and Held-Out Synthetic Evaluation Design V1

## Status
Design only. No solver implementation, no held-out generator implementation, no runtime wiring, no public ARC/Kaggle ingestion, and no score claims.

## 1. Baseline state

Current synthetic solver state:

- Before primitive expansion: `14 / 6 / 28 / 0`
- After primitive expansion: `14 / 30 / 4 / 0`
- After partial-to-exact repair: `41 / 3 / 4 / 0`

Residual gaps:

- `complete_symmetry`: still partially exact
- `object_count_to_pattern`: still partially exact
- `reflect_object_horizontal_or_vertical`: still honestly unsupported
- `candidate_generation_gap`: still `2`
- no held-out compositional synthetic suite yet
- no bounded compositional program search yet
- no typed primitive composition/search layer yet
- no public ARC data touched

Evidence boundary:

- current evidence is synthetic-only
- current evidence is known-family only
- no public ARC/Kaggle data has been touched

## 2. Architecture goal

Design a next-layer ARC-style architecture that tests whether WESLR can generalize beyond hand-authored family templates by combining:

- typed primitive signatures
- bounded depth-2/3 composition search
- train-only verification
- MDL / Occam ranking
- structured mismatch diff
- verifier-driven repair
- top-2 structurally distinct candidate selection
- held-out random/compositional synthetic evaluation

## 3. Existing WESLR substrate to reuse

This design is intended to sit on top of the documented WESLR substrate rather than inventing new authority surfaces.

Relevant documented helpers / surfaces:

- `docs/WESLR_UNKNOWN_ENGINE_BOUNDARY_V1.md` (diagnostic boundary only)
- `docs/WESLR_ARC_RESIDUAL_GAP_INTERNAL_ENGINE_PRESSURE_V1.md` (residual-gap diagnostic baseline)
- `docs/WESLR_ARC_STYLE_GRID_SOLVER_ADAPTER_DESIGN_V1.md`
- `weslr/arc_style_grid_schema_helpers.py`
- `weslr/arc_style_grid_adapter_phase2.py`
- `weslr/arc_style_grid_solver_dry_run.py`
- `weslr/arc_style_synthetic_task_generators.py`
- `weslr/arc_style_synthetic_solver_suite.py`
- `weslr/arc_agi2_submission_contract.py`
- related WESLR reasoning / friction / calibration helpers documented in repo

No new runtime API is created by this design.

## 4. Typed primitive signature design

Each primitive should declare a typed signature object, not just a primitive name.

### Required fields

- `name`
- `input_grid_constraints`
- `output_grid_constraints`
- `parameter_schema`
- `safe_parameter_proposal_method`
- `composability_tags`
- `shape_effects`
- `color_effects`
- `object_effects`
- `failure_behavior`
- `leakage_flags`
- `deterministic_identity`

### Example signature shape

```json
{
  "name": "move_single_object",
  "input_grid_constraints": ["rectangular", "single_object_present", "background_known"],
  "output_grid_constraints": ["rectangular", "same_palette_or_subset", "object_count_preserved"],
  "parameter_schema": {
    "direction": ["up", "down", "left", "right"],
    "steps": "integer>=1",
    "object_value": "optional",
    "background_value": "optional"
  },
  "safe_parameter_proposal_method": "derive from train input/output delta only",
  "composability_tags": ["translate", "single_object", "position_effect"],
  "shape_effects": ["preserve_shape"],
  "color_effects": ["preserve_color"],
  "object_effects": ["move_object"],
  "failure_behavior": ["unsupported_on_non_translation", "reject_if_multi_object_delta"],
  "leakage_flags": {
    "uses_test_output_for_candidate_generation": false,
    "uses_solution_file": false,
    "uses_answer_key": false
  },
  "deterministic_identity": "move_single_object:v1"
}
```

### Example primitive notes

- `recolor_symbol`
  - input: one or more colored cells or objects
  - output: same geometry, different color mapping
  - safe proposal: train-pair color delta only

- `move_single_object`
  - input: one translated object, background known
  - output: object moved by bounded vector
  - safe proposal: train-pair position delta only

- `extract_largest_object`
  - input: multiple connected components
  - output: largest connected component preserved, others removed
  - safe proposal: connected-component size comparison from train pairs only

- `rotate_object_90`
  - input: one object with stable bounding box
  - output: object rotated 90 degrees within bounded region
  - safe proposal: bbox/object cells from train pairs only

- `reflect_object_horizontal_or_vertical`
  - input: one object and a detectable axis candidate
  - output: reflected object across horizontal or vertical axis
  - safe proposal: axis chosen only by train-pair verification

- `complete_symmetry`
  - input: partial symmetric pattern plus background
  - output: mirrored completion across known axis set
  - safe proposal: axis candidate set from train-pair evidence only

- `object_count_to_pattern`
  - input: countable objects or symbols
  - output: pattern whose length/occupancy encodes the count
  - safe proposal: count and output-shape candidates from train pairs only

## 5. Bounded composition search design

V1 search depth:

- depth 2 and depth 3 only
- no depth 6–8 jump
- no uncontrolled recursion

### Search properties

- deterministic queue / beam order
- train-pair-only evaluation
- branch pruning
- duplicate structural program detection
- max candidate limits
- max runtime / step budget
- fail-closed execution
- no test input access during search / ranking
- test input execution only after final top-2 selection

### Search order

1. single-primitive candidates
2. depth-2 compositions
3. depth-3 compositions
4. bounded fallback hypotheses

### Pruning rules

- reject duplicate structural signatures
- reject leakage flags immediately
- reject candidates that fail train verification early
- prune programs that only differ by irrelevant parameter permutations
- prune candidates with dominated MDL score and identical structure

## 6. Parameter proposal design

Parameters must be proposed from train input/output evidence only.

### Proposal channels

- color mappings
- movement vectors
- object bounding boxes
- axis candidates
- region / fill candidates
- count candidates
- shape / output pattern candidates

### Safe proposal rules

- never use test output
- never use solution files
- never use answer keys
- never use task ID shortcuts
- never use notes shortcuts
- never infer from benchmark examples outside the train pairs

### Proposal example

A two-step candidate may propose:

1. `extract_largest_object`
2. `recolor_symbol`

with the recolor mapping derived only from train input/output cell deltas.

## 7. MDL / ranking design

Candidate ranking should prefer the simplest exact program that is still stable.

### Ranking factors

- exact train fit dominates
- mismatch count
- shape mismatch penalty
- program length penalty
- parameter complexity penalty
- instability penalty
- leakage penalty as hard reject
- diversity bonus for top-2 structural difference

### Priority ordering

1. exact fit
2. lower mismatch count
3. smaller structural complexity
4. lower parameter entropy
5. lower instability
6. more diverse second candidate

### Diversity rule for top-2

Top-2 candidates should not be near-duplicates when avoidable.

Examples of structural diversity:

- different primitive family
- different composition length
- different axis family
- different region extraction strategy
- different object-selection strategy

## 8. Structured mismatch diff design

Mismatch diffs should be structured and verifier-driven.

### Mismatch categories

- wrong color
- wrong object
- wrong position
- wrong shape
- wrong count
- wrong symmetry axis
- wrong rotation/reflection orientation
- extra pixels
- missing pixels
- structural output-size mismatch

### Repair feed

The verifier should convert train-pair mismatch diffs into bounded repair hints such as:

- adjust color mapping
- adjust axis candidate
- adjust object selection
- adjust bounding box
- adjust count-to-pattern encoding
- adjust move vector
- adjust reflect orientation

### Repair boundary

- train-pair only
- no test-output feedback
- no solution-file feedback
- no answer-key feedback

## 9. Held-out synthetic evaluation design

The known-family suite remains the regression baseline.

A separate held-out compositional suite should be generated from random compositions of existing primitives.

### Held-out evaluation rules

- separate generator recipes from solver candidate rules
- deterministic seeds
- depth 2/3 compositions only for V1
- train/test split within each held-out task
- no solution leakage into solver
- report per-family and per-composition exact rates
- report aggregate exact / partial / unsupported / failed
- report failure ledger

### Example held-out composition families

- extract object then recolor
- move then border
- rotate then recolor
- remove noise then complete line
- count object then emit pattern
- reflect then recolor
- fill region then extract object

### Example split logic

- generator recipe decides the composition
- train pairs show the transformation pattern
- test inputs are withheld until after top-2 selection
- held-out recipe IDs are not used in solver candidate selection

### Evaluation outputs

- known-family baseline exact rate
- held-out compositional exact rate
- per-family exact / partial / unsupported / failed
- per-composition exact / partial / unsupported / failed
- failure ledger with mismatch categories
- deterministic-run comparison across repeated execution

## 10. Evidence threshold before public ARC data

Minimum evidence before any public ARC/Kaggle boundary consideration:

- known-family exact remains at least `41`
- held-out compositional suite exists
- held-out exact rate is reported
- depth-2/3 search improves held-out exact versus no-search baseline
- per-family / per-composition distribution reported
- leakage audit passes
- top-2 packets validate
- deterministic run stability
- public-data boundary remains intact

No fake official score claims.
No Kaggle-ready claim.
No public ARC contact until synthetic held-out proof exists.

## 11. Implementation sequence

Recommended future lanes in order:

A. implement typed primitive signature helper
B. implement held-out compositional synthetic generator
C. implement bounded program search dry-run helper
D. integrate top-2 structural selection
E. run known-family + held-out comparison
F. only then review whether the public ARC data boundary can be considered

## 12. Kill criteria

This path should be reconsidered if any of the following occur:

- known-family exact drops below `41`
- held-out compositional exact stays near zero
- search does not beat no-search baseline
- validation mismatch explodes without exact gain
- top-2 packets fail validation
- leakage boundary weakens
- runtime / candidate budget becomes uncontrolled

## 13. Non-goals

Explicitly out of scope:

- no implementation in this lane
- no public ARC/Kaggle data
- no Kaggle download
- no ARC data ingestion
- no public ARC samples
- no answer keys
- no benchmark examples copied
- no official score claims
- no Kaggle-ready claim
- no AGI claim
- no UNKNOWN ENGINE solver-authority claim
- no provider/model/API calls
- no ChatResponder/respond_chat calls
- no website/runtime wiring
- no `.weslr` writes

## 14. Final note

This design intentionally moves the question from "can the known synthetic families be repaired?" to "can bounded composition generalize on held-out synthetic tasks?" That is the right next evidence step before any public ARC boundary is considered.
