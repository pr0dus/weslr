# WESLR ARC Safe Rotate Object Canvas Design V1

## Status
Design-only. No implementation, no solver behavior change, no depth-3, no fill repair, no public ARC/Kaggle data, no runtime wiring, no `.weslr` writes.

## 1. State summary

- Known-family baseline: `41 / 3 / 4 / 0`
- Held-out total: `10 / 2 / 2 / 0`
- Remaining blockers:
  - `fill_region_then_extract_object`: saturated partial
  - `rotate_then_recolor`: unsupported `2/2`
- Fill is saturated because train-exact fill behavior does not safely determine held-out color/orientation from train-only evidence.
- Rotate is now the correct design target because the unsupported family is blocked by missing safe canvas-level rotation, not depth or syntax.

## 2. Problem definition

Define `rotate_object_canvas` as a bounded structural primitive that:

- rotates the non-background object region
- preserves or safely derives canvas size
- preserves background
- allows later recolor composition
- avoids arbitrary output construction
- avoids answer-template behavior

## 3. Candidate primitive signature

Proposed primitive name:

- `rotate_object_canvas`

Candidate signature properties:

- allowed rotations: `90`, `180`, `270`
- train-only parameter inference
- background inference
- object bbox extraction
- canvas policy
- output-size policy
- placement policy
- fail-closed behavior
- typed signature metadata
- leakage flags

Candidate semantic envelope:

- infer the non-background bbox from train-observed object structure
- rotate bbox content by one allowed angle only when train evidence supports it
- preserve background semantics and composability with later recolor steps
- keep output-size and placement rules explicit, bounded, deterministic, and train-only
- emit unsupported/fail-closed when ambiguity remains

## 4. Canvas policy comparison

| Policy | Classification | Notes |
|---|---|---|
| A. preserve input canvas size | safe for V1 | Smallest safe default; avoids broad output synthesis |
| B. rotate bbox and place back on same anchor | safe for V1 | Safe when anchor is train-inferable and fit is bounded |
| C. crop to rotated object | risky but possible later | Can remove needed background/context |
| D. rotate bbox and place on new bounded canvas | safe for V1 | Acceptable only when the bounded canvas is train-derived and constrained |
| E. derive output canvas from train output shape | reject | Too broad; risks answer-template behavior |

## 5. Recommended V1 policy

Recommended policy:

- extract non-background bbox
- rotate bbox content
- preserve background
- preserve input canvas by default
- place rotated bbox on same anchor by default
- allow bounded train-derived canvas/anchor only when train pairs agree
- fail closed if ambiguous
- no evaluation output
- no task IDs or recipe names as direct hints

This keeps the primitive narrow, compositional, and compatible with later `recolor_symbol` usage without turning it into arbitrary output construction.

## 6. Train-only parameter proposal rules

Infer only from train input/output pairs.

Allowed train-only inference:

- background color
- object colors
- bbox
- rotation angle
- canvas size
- anchor/offset
- crop vs preserve-canvas policy
- recolor composition compatibility

Inference rules:

- background color: infer from stable train background structure only
- object colors: infer from train-visible foreground structure only
- bbox: infer from non-background extent only
- rotation angle: infer from train pair alignment under allowed rotations only
- canvas size: preserve input canvas by default; allow bounded train-derived size only when train pairs agree
- anchor/offset: infer from stable train alignment between rotated object position and canvas coordinates only
- crop vs preserve-canvas policy: default preserve-canvas; allow bounded alternative only when train evidence is stable and exact
- recolor composition compatibility: require that rotation preserves a stable post-rotation object surface suitable for later recolor steps

Explicitly forbidden:

- evaluation output
- public ARC examples
- task IDs
- recipe names as solver hints
- hardcoded held-out expected outputs
- arbitrary shape templates

## 7. Search integration design

Search integration should remain bounded and train-only:

- allowed as first step before `recolor_symbol`
- terminal use only when train-exact and shape-safe
- bounded angle/placement hypotheses
- candidate caps
- ranking penalties for unnecessary canvas expansion
- top-2 structural diversity
- train-only scoring
- JSON-safe summaries

Recommended integration details:

- limit angle hypotheses to `90/180/270`
- limit placement hypotheses to same-anchor first, with bounded train-derived alternatives only when justified
- cap candidate expansion so angle × placement combinations remain small
- penalize candidates that expand canvas unnecessarily or introduce ambiguous placement
- preserve top-2 diversity only across structurally distinct train-valid packets
- keep summaries deterministic, JSON-safe, and fail-closed on ambiguity

## 8. Safety constraints

Required constraints:

- deterministic
- rectangular grid validation
- grid size bounded
- colors `0..9`
- no bool cells
- no hidden state
- no `.weslr`
- no provider/model/API calls
- no public-data dependency
- no answer-key leakage
- fail closed on ambiguity
- no held-out generator expected output changes

## 9. Risks

Key risks:

- arbitrary output construction
- overfitting to synthetic rotate recipe
- output-shape leakage from train outputs
- masking deeper primitive errors
- candidate explosion
- unsafe rotation/placement combinations
- public ARC temptation

Mitigations:

- preserve a narrow V1 canvas policy
- bound angle and placement hypotheses tightly
- keep scoring train-only
- reject broad output-shape derivation policies
- fail closed whenever fit, anchor, or size is ambiguous
- keep public ARC/Kaggle data completely out of scope

## 10. Expected measurable effect if implemented later

Success criteria:

- held-out exact above `10`
- unsupported below `2`
- known-family baseline remains `41 / 3 / 4 / 0`
- fill remains saturated unless separately justified
- no leakage
- deterministic run stable
- evidence layer updated only after measured implementation improvement

## 11. Non-goals

Explicit non-goals:

- no implementation in this lane
- no depth-3
- no fill repair
- no public ARC/Kaggle data
- no benchmark examples/grids/solutions
- no official score claim
- no Kaggle-ready claim
- no AGI/sentience/consciousness claim
- no runtime wiring
- no ChatResponder/respond_chat
- no provider/model/API calls
- no `.weslr` writes

## 12. Decision

Recommended primary next lane:

- `IMPLEMENT_ARC_SAFE_ROTATE_OBJECT_CANVAS_V1`

Fallback:

- `DECLARE_ARC_ROTATE_CANVAS_UNSAFE_FOR_V1`
