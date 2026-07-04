# WESLR ARC-AGI2 Task / Primitive / Family Discovery Engine + Universal Runner Architecture V1

## Repository
- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`

## Heads
- Start HEAD: `e02b899c55aa989286837988931242a6ed4db497`
- Actual preflight HEAD: `e02b899c55aa989286837988931242a6ed4db497`
- End HEAD: `e02b899c55aa989286837988931242a6ed4db497` (design-only report state before report commit)
- Commit status: report pending commit

## Current capability spine
- object/bbox capability provider
- shape geometry capability provider
- color-role capability provider
- resize/tile/canvas capability provider
- count/quantity capability provider
- capability aggregator with exact-two-output contract
- shared hypothesis engine with exact train-consistency ranking

## Why manual-family accumulation is insufficient
Manual families are useful scaffolding, but they do not scale into discovery. They fail to provide:
- a task-level representation that explains *what changed* between train pairs
- a primitive registry that standardizes preconditions, effects, and rejection reasons
- bounded composition search for multi-primitive tasks
- a reusable way to collapse equivalent candidate families
- a universal runner that can coordinate discovery instead of hard-coding new adapters forever

In short: the current spine can *execute* known families, but it does not yet *discover* family structure.

## Task representation design
A WESLR ARC task packet should contain:
- raw `train_pairs` and `test_input`
- normalized grid metadata for every grid
- object summaries per grid
- color summaries per grid
- shape summaries per object / component
- size relations between input and output
- count relations (cells, objects, colors, components)
- candidate feature signatures
- safe trace fields only

Suggested packet layers:
1. `raw` — exact input/output grids for local inference only
2. `metadata` — task id, split, source tags, safe provenance
3. `summaries` — grid/object/color/shape/count summaries
4. `signatures` — compact feature deltas and primitive hints
5. `trace` — redacted reasoning breadcrumbs only

## Primitive registry design
Use a registry entry per primitive with these fields:
- `primitive_name`
- `input_type`
- `output_type`
- `preconditions`
- `effect_summary`
- `train_inference_fn`
- `executor_fn`
- `inverse_or_comparable_relation` (optional)
- `rejection_reasons`
- `trace_safe_metadata`

Example primitive buckets:
- crop_foreground_bbox
- crop_largest_object
- translate_object
- rotate_object
- reflect_object
- recolor_global
- recolor_foreground
- tile_grid
- scale_cells
- add_border
- count_objects
- select_largest
- select_most_frequent_color

Registry rule: primitives are declarative first, executable second.

## Primitive discovery engine design
Discovery should inspect only provided train pairs and produce primitive applicability hints from:
- feature deltas between input and output
- size relation detection
- color relation detection
- object relation detection
- shape relation detection
- count relation detection
- contradiction checks

Each primitive inference should return:
- candidate primitive name
- inferred parameters
- confidence or rank hint
- rejection reason when it fails
- trace-safe summary of why it matched

Important boundary: this engine should infer from train examples only. No public solution lookup, no hidden-answer access, no Kaggle loop.

## Family discovery engine design
Primitive hypotheses become family hypotheses through bounded composition:
- single-primitive families
- two-step compositions
- bounded primitive chains
- family templates
- train-consistency filtering
- contradiction elimination
- duplicate candidate collapse
- simplicity ranking

Constraints:
- no unbounded recursion
- no open-ended search tree
- no arbitrary symbolic planner
- no blind composition explosion

Recommended composition policy:
1. generate primitive candidates from each train pair
2. intersect candidate sets across all train pairs
3. compose only within a small bounded depth
4. require exact train consistency at each stage
5. collapse equivalent families by output signature and trace signature

## Universal family runner design
A universal runner should:
- accept a task packet
- build summaries and signatures
- run all registered primitive discoverers
- assemble family hypotheses from primitive matches
- execute each hypothesis against all train pairs
- reject inconsistent hypotheses
- rank surviving hypotheses
- execute top candidates on test input
- emit exactly two outputs
- preserve metadata-safe trace

This runner can eventually replace the current manually wired aggregator, or sit above it as a discovery layer that feeds the existing aggregator.

## Synthetic discovery test engine design
Use a synthetic-only discovery engine to generate:
- individual primitive tasks
- primitive combinations
- family template tasks
- adversarial near-misses
- ambiguity cases
- contradiction cases
- held-out synthetic validation tasks

This engine is for internal regression and architecture discovery only. It is not public ARC evaluation.

## Evaluation irreversibility boundary
Level 0:
- unit tests for primitives

Level 1:
- synthetic family tests

Level 2:
- synthetic held-out discovery tests

Level 3:
- frozen no-public-data package dry run

Level 4:
- public parse/shape checks only

Level 5:
- public score or Kaggle submission only after explicit owner approval

Boundary notes:
- public scoring is irreversible for blind claims
- public solution exposure cannot be undone
- Kaggle submission is not a casual retry surface
- no public score should be the main development loop

## Mapping from current modules to future architecture
- `arc_object_bbox_solver_v1` → primitive/family provider
- `arc_shape_geometry_v1` → primitive/family provider
- `arc_color_role_abstraction_v1` → primitive/family provider
- `arc_resize_tile_canvas_v1` → primitive/family provider
- `arc_count_quantity_relations_v1` → primitive/family provider
- `arc_agi2_capability_candidate_aggregator_v1` → temporary family coordinator
- `arc_hypothesis_engine_v1` → initial scoring/ranking foundation

## Risks / false-positive traps
- confusing a family coordinator with a discovery engine
- overfitting synthetic tasks to hand-picked templates
- accepting a primitive that matches one train pair but not all
- composing primitives without bounded depth
- collapsing distinct families too aggressively
- mixing trace metadata with raw data leakage
- treating public-score feedback as a normal inner-loop signal

## Claim boundary
This is a design-only architecture report.
It does not claim runtime discovery, public ARC readiness, Kaggle validity, or solver completeness.
It defines the next architecture step needed before adding more hand-coded families.

## Recommended next implementation lane
`PRIMITIVE_REGISTRY_V1`

Why this first:
- it gives the solver spine a stable vocabulary
- every discovery component needs standardized primitive definitions
- it is the smallest structural step that unlocks task signatures, family discovery, and a universal runner
- it prevents more isolated family code from accumulating without a shared architecture

## Validation status
Pending execution at write time.

## Readiness verdict
`task_primitive_family_discovery_engine_architecture_ready_for_primitive_registry_lane`
