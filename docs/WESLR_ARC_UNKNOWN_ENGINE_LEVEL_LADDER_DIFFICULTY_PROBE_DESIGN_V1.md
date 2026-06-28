# WESLR ARC UNKNOWN ENGINE LEVEL LADDER DIFFICULTY PROBE DESIGN V1

## 1. Executive verdict
`arc_unknown_engine_difficulty_probe_design_ready`

## 2. Why difficulty probe is needed
The current baseline smoke has become a stable confirmation surface rather than an information-rich frontier probe.

Current baseline facts:
- deterministic baseline ladder
- 12 generated levels
- 36 attempted tasks
- `task_exact_rate = 31 / 36 = 0.8611111111111112`
- `packet_exact_rate = 41 / 48 = 0.8541666666666666`
- repaired metric policy already proves `task_exact_rate` is the primary gate

Why repeated same-score smoke is not enough:
- V3/V4/V5 on the same deterministic ladder may only confirm stability of the same easy/mixed baseline
- frontier placeholders are still null/empty, so the current baseline is not yet exposing where the frozen solver breaks under harder pressure
- to learn something new, the system needs a controlled harder probe that preserves the baseline while increasing synthetic task difficulty in a separate mode
- the correct next question is not “does the same ladder still pass?” but “where does the frozen solver begin to fail when difficulty pressure rises in a governed way?”

## 3. Baseline preservation
Baseline preservation policy:
- keep current Smoke V2 baseline untouched as the reference lane
- do not overwrite baseline metric meaning
- baseline task exact remains `31 / 36 = 0.8611111111111112`
- baseline packet exact remains `41 / 48 = 0.8541666666666666`
- baseline reports continue to use the repaired metric surface exactly as-is
- harder probe results must be reported separately under a distinct difficulty-probe mode
- any future harder probe runner must label output clearly so baseline and harder-probe metrics cannot be confused

Recommended separation:
- **baseline mode**: current synthetic ladder, current metric semantics, continuity reference
- **difficulty-probe mode**: separate internal synthetic ladder expansion that preserves the frozen solver and only changes generator-side pressure

## 4. Difficulty axes
Proposed harder synthetic axes and what each tests:

1. **multi-step transformation**
   - tests whether single-step primitive confidence breaks when the real rule composes two clean operations
2. **object movement plus color change**
   - tests interaction between spatial movement and recolor inference
3. **reflection plus translation**
   - tests whether mirrored structure plus post-transform displacement causes brittle candidate ranking
4. **distractor objects**
   - tests robustness against irrelevant but plausible competing objects
5. **partial occlusion**
   - tests whether incomplete structural evidence leads to safe failure instead of overconfident wrong candidates
6. **role reversal**
   - tests whether train examples cause the solver to lock onto source/target roles incorrectly
7. **exception case**
   - tests whether an otherwise regular family contains a bounded exception that defeats naive pattern compression
8. **negative evidence / non-change**
   - tests whether the solver can correctly prefer no-op or preserve-state behavior when change is a trap
9. **shape count change**
   - tests whether the solver overfits object identity when the true rule depends on object count transformations
10. **symmetry trap**
    - tests whether visually symmetric distractors cause incorrect symmetry-family selection
11. **coordinate overfit trap**
    - tests whether absolute-position bias defeats a relational rule
12. **concept-bloat trap**
    - tests whether extra colors/components trick the solver into inferring a more complex rule than necessary
13. **composed transformations**
    - tests clean two-pressure family composition without changing solver depth policy
14. **train/test rule shift trap**
    - tests whether training examples are just narrow enough to support a wrong candidate grammar that fails on test
15. **ambiguous rival grammar**
    - tests safe failure under two plausible but competing explanations

## 5. Tiering policy
### Tier 0 — baseline/easy
- current simplest toy family behavior
- used only for continuity and sanity
- should remain easiest reference surface

### Tier 1 — current known baseline mixed families
- current Smoke V2 ladder behavior
- mixed but still governed baseline
- canonical baseline score reference lives here

### Tier 2 — composed two-pressure levels
- combine two bounded pressures without changing solver depth policy
- examples: movement+recolor, reflection+translation, distractor+count rule
- intended to reveal first meaningful task-rate drop while still remaining interpretable

### Tier 3 — adversarial/distractor-heavy levels
- add misleading objects, symmetry traps, coordinate traps, and concept-bloat pressure
- intended to expose ranking brittleness and unsafe overfitting tendencies

### Tier 4 — ambiguity / safe-failure levels
- design tasks where unsupported or partial outcomes are healthy behavior
- intended to produce principled safe failure rather than accidental exacts
- useful for locating the first stable failure frontier

### Tier 5 — unknown-engine frontier levels
- strongest bounded synthetic difficulty
- mixes ambiguity, composed pressure, distractors, and rule-shift traps
- intended as the internal frontier layer for discovering blocker families and next pressure targets

Tiering rule:
- higher tier means harder synthetic pressure, not solver modification
- each tier must remain internal synthetic only
- harder tiers are separate probe tiers, not reinterpretations of baseline performance

## 6. Probe metric policy
Harder probe reporting must include at minimum:
- `attempted_task_count`
- `task_exact_count`
- `task_exact_rate`
- `task_partial_count`
- `task_partial_rate`
- `task_unsupported_count`
- `task_unsupported_rate`
- `packet_exact_count`
- `packet_exact_rate`
- `unsupported families`
- `blocker families`
- `first stable failure frontier`
- `hardest exact tier`
- `next recommended pressure family`

Metric interpretation policy:
- **task-level metrics are primary** for difficulty assessment and gate reasoning
- **packet-level metrics are diagnostic** for candidate quality, not the core frontier score
- unsupported family counts matter because safe unsupported outcomes can be signal, not just failure noise
- blocker families should identify where the frozen solver lacks bounded executable support or ranking confidence
- frontier fields should become meaningfully populated in harder probe mode rather than staying null/empty

Recommended additional probe outputs:
- tier-by-tier breakdown
- family-by-family breakdown
- first tier where `task_exact_rate` falls below baseline threshold
- first family with repeated stable unsupported/blocker behavior

## 7. Hardness interpretation
### If harder probe stays >= 85%
- not a failure
- indicates the harder mode still does not sufficiently pressure the frozen solver
- next probe should increase difficulty again in generator space only

### If harder probe lands in 70–85%
- useful frontier zone
- indicates the solver remains partially competent but is no longer comfortably above baseline threshold
- target first stable failure frontier and next recommended pressure family

### If harder probe lands in 40–70%
- meaningful stress exposure
- indicates the harder probe is revealing genuine weakness without necessarily collapsing into noise
- prioritize blocker-family analysis and safe-failure interpretation

### If harder probe lands below 40%
- probe may be too hard, too ambiguous, or too unsupported for the current frozen solver
- inspect whether the result is informative frontier signal or just unproductive adversarial overload
- adjust pressure design rather than patching solver behavior

### If result is unsupported/blocker-heavy
- not automatically bad
- may indicate the UNKNOWN ENGINE frontier more clearly than a mediocre exact score
- should drive the `first_stable_failure_frontier`, `unsupported families`, `blocker families`, and `next recommended pressure family` fields

Hardness gate rule:
- baseline pass threshold remains **85%**
- harder-probe drop below **85%** is not itself failure; it identifies frontier
- if harder probe remains above **85%**, difficulty should increase again
- if harder probe drops sharply, target the first stable failure frontier rather than changing the frozen solver

## 8. Boundary review
Confirmed for this design lane:
- no public ARC data
- no Kaggle data
- no official claims
- no solver changes
- no generator changes in this design lane
- no `.weslr` writes
- no external calls
- protected files unchanged

Solver freeze doctrine for future implementation:
- frozen solver behavior remains unchanged
- no new solver primitives
- no retry fill repair
- no depth-3 implementation
- no solver patching to pass the harder probe

## 9. Recommended next safe local follow-up
`REVIEW_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_DIFFICULTY_PROBE_DESIGN_V1`

Reason:
- this lane is design-only and introduces a meaningful strategic shift from repeated baseline smoke to controlled harder probing
- the design should be reviewed before implementing any harder synthetic generator/probe runner
- after review, the correct implementation lane is a generator/probe-only lane that preserves the solver freeze
