# WESLR ARC-AGI2 Solver Generalization Architecture Review V1

- Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `main`
- Start HEAD: `9fc98f7e59fcca308b36fc4dbf3d8548d056e809`
- End HEAD: `9fc98f7e59fcca308b36fc4dbf3d8548d056e809`
- Commit status: clean before this report write
- Actual preflight HEAD: `9fc98f7e59fcca308b36fc4dbf3d8548d056e809`

## Current pipeline status

The public-data plumbing path is complete:
- manifest/checksum validation passed
- parse-only validation passed
- submission-shape dry run passed
- solver-candidate dry run passed structurally
- local public score check passed structurally
- elastic public challenge coverage repair passed
- `public_scoreable` covers `1120/1120` scoreable public tasks
- missing `0`
- malformed `0`
- correct `0`
- Kaggle submission `no`
- official percentage `none/0`

## Current solver failure summary

The current system is not failing on file selection, artifact shape, or coverage anymore.
It is failing on solver generalization.

Observed state:
- synthetic / structural dry runs succeed
- public scoreable coverage succeeds
- exact-match public scoring on the frozen candidate artifact is `0/1120`
- the candidate emitter is deterministic and shape-valid, but it is not a real ARC inductive solver

## What the current solver actually learned or implemented

Capability class:
- bounded candidate emission
- primitive-sequence reconstruction on toy/internal grids
- deterministic dry-run metadata generation
- surface validation of ARC-like packets
- not real ARC rule induction
- not multi-example reasoning
- not object-centric generalization

In practice, the current system learned how to:
- parse grids and emit two-output candidate packets
- maintain metadata and leakage guards
- apply a narrow primitive library to bounded synthetic examples
- pass shape/coverage gates

It did **not** learn how to:
- infer reusable rules from few examples
- generalize from toy grids to real ARC tasks
- choose among competing hypotheses using train-example consistency
- represent objects, regions, and transformations robustly enough for real ARC

Why synthetic success did not transfer:
- synthetic validation mostly checked packaging, packet shape, and deterministic candidate creation
- real ARC requires semantic induction from examples, not just well-formed outputs
- the current path does not have a sufficiently strong object/region/transform abstraction layer
- the current path does not have a train-consistency search and ranking loop that can reject bad hypotheses

## Synthetic-vs-real generalization gap

The gap is not a small tuning issue.
It is a missing architecture layer.

Synthetic validation exercises:
- candidate shape
- deterministic emission
- bounded primitives
- metadata safety
- structural coverage

Real ARC requires:
- object discovery
- region extraction
- shape identity tracking
- color role inference
- background/foreground separation
- symmetry and reflection detection
- translation and rotation reasoning
- cropping / bounding-box reasoning
- counting and quantity relations
- pattern continuation
- resizing and tiling
- compositional transformations
- hypothesis search across multiple examples
- contradiction handling
- candidate ranking by train-fit

## Missing capability map

### 1. Object discovery
Needed:
- connected components
- object boundaries
- canonical object descriptors

Current gap:
- no stable object-first abstraction layer before transformation search

### 2. Color role inference
Needed:
- background detection
- foreground role separation
- palette-role abstraction

Current gap:
- colors are mostly treated as raw cell values

### 3. Shape identity
Needed:
- canonical shape descriptors
- invariants under move/reflect/rotate

Current gap:
- no robust canonicalization

### 4. Geometric transformation reasoning
Needed:
- translation
- rotation
- reflection
- crop/translate combinations
- symmetry completion

Current gap:
- primitives exist, but there is no full hypothesis engine tying them to train pairs

### 5. Region cropping and resizing
Needed:
- object bounding boxes
- output resize rules
- copy/scale/tile operations

Current gap:
- not a first-class solver layer

### 6. Counting and quantity relations
Needed:
- object counts
- frequency-based color logic
- repeated-pattern rules

Current gap:
- no structured count-to-action mapping

### 7. Rule induction from few examples
Needed:
- candidate rule families
- train-pair consistency checks
- contradiction elimination

Current gap:
- current path produces candidates, but not serious inductive filtering

### 8. Multi-hypothesis search
Needed:
- competing candidate generation
- ranking
- fallback search
- abstention when uncertainty is high

Current gap:
- candidate diversity is too shallow

### 9. Compositional transformations
Needed:
- compose object extraction + move + recolor + resize + reflect

Current gap:
- primitives are present, but not composed into a robust search space

## Proposed solver architecture

### Layer 1: grid parser / normalizer
- validate grid shape
- normalize representation
- keep a trace-safe, JSON-safe grid model

### Layer 2: object / region extraction
- connected components
- bounding boxes
- holes / borders / adjacency
- background estimation

### Layer 3: feature abstraction
- color roles
- symmetry signatures
- shape descriptors
- count summaries
- relative position features

### Layer 4: primitive transformation library
- move / reflect / rotate / crop / resize / fill / recolor / tile
- all primitives pure and traceable

### Layer 5: hypothesis generator
- generate candidate rules from train pairs
- object-level and grid-level hypotheses
- multiple hypothesis families per task

### Layer 6: hypothesis executor
- apply a candidate hypothesis to each train example
- produce predicted outputs

### Layer 7: train-consistency scorer
- exact-match fit on train pairs
- partial fit penalties
- contradiction penalties
- simplicity / interpretability penalties

### Layer 8: candidate ranker
- rank by train fit, consistency, and simplicity
- keep top-N candidates
- support abstain / fail-closed behavior

### Layer 9: two-output emission layer
- emit exactly two candidates per test input
- preserve metadata-only trace
- no answer-key or public-solution leakage

### Layer 10: trace / review layer
- explain why candidates were kept/rejected
- record mismatch categories
- support later lane-by-lane debugging

## WESLR component reuse map

Useful conceptual reuse:
- **Controlled candidate generation**: good template for bounded candidate families and reviewable metadata, but not sufficient for ARC induction. Source memory: `memory/2026-06-28.md` and `memory/2026-05-28-ranking-shadow.md`.
- **Candidate ranking / rejection discipline**: useful for hypothesis ranking and contradiction handling, but currently metadata-oriented rather than vision-oriented.
- **Rule pressure / conflict handling**: useful for forcing train-consistency checks and rejecting incoherent hypotheses.
- **Perspicuity / clarity scoring**: useful as a secondary ranker for interpretable hypotheses, not as the primary solver signal.
- **Dialectic generation**: useful for competing hypotheses and adversarial self-checks.
- **Replay / calibration ideas**: useful for reproducibility and search trace review.
- **Recursive research protocol ideas**: useful for lane discipline, not for solving ARC directly.
- **Unknown-engine style search scaffolding**: useful only as bounded proposal/search metadata, never as final-answer authority.

Not enough by themselves:
- metadata-only candidate generators
- structural validators
- coverage gates
- shape-only dry runs
- scoring wrappers

Those help the process, but they do not create ARC generalization.

## Next implementation roadmap

1. Build synthetic capability tests that isolate one family at a time.
2. Add an object/region extraction lane.
3. Add a crop / translate / reflect lane.
4. Add color-role abstraction and background inference.
5. Add hypothesis generation over those abstractions.
6. Add train-consistency scoring and contradiction rejection.
7. Add candidate ranking with fallback hypotheses.
8. Expand to compositional transformations and resizing.
9. Only then evaluate on broader held-out synthetic tasks.
10. Later, if warranted, compare against public data again without claiming blind generalization.

## Recommended first implementation lane

**Object extraction + bounding-box crop/translate solver**

Why first:
- Many ARC tasks depend on detecting objects before any higher-level rule can be found.
- It creates the base representation needed for movement, reflection, recoloring, and cropping.
- It is small enough to test exactly.
- It will expose whether the pipeline can actually reason over regions rather than raw pixels.
- It is the cleanest next step toward real generalization without jumping straight to complex search.

## Risks / false-positive traps

- mistaking packaging success for reasoning success
- mistaking synthetic shape validation for ARC generalization
- overfitting to public task ids or public scoreable coverage
- using public-solution-exposed data as if it were blind
- evaluating only exact-match on a tiny synthetic set
- adding more candidate wrappers without better abstractions
- confusing deterministic emission with inductive solver quality

## Claim boundary

- No official score claim.
- No Kaggle claim.
- No blind-generalization claim on the public solution-exposed set.
- No solver code changes in this lane.
- The public ARC set is contaminated for blind follow-up claims because solutions were already exposed in the local score lane.

## Readiness verdict

`solver_generalization_architecture_review_ready_for_first_real_capability_lane`
