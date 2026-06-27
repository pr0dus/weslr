# WESLR MICRO-THEORY COLLAPSED PRESSURE CATEGORY EXPERIMENT V1

## Status
Experiment/report only. Local-only. Synthetic-only existing cases. Canonical ledger unchanged. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, no push preparation, and no push.

## 1. Executive summary
`collapsed_category_experiment_partial_success`

The collapsed-category experiment was useful, but the three candidate merges did not behave equally well.

Two merges reduced overlap without obvious safety loss in most cases:
- `absence_of_expected_change_pressure`
- `salience_distractor_pressure`

The third merge remained risky:
- `overfit_specificity_pressure`

It preserved catches in the tested cases, but it consistently lost diagnostic sharpness exactly where prior work depended on distinguishing private-concept inflation from coordinate anchoring. So the experiment supports selective continuation, not canonical collapse.

## 2. Method
- manual design-only experiment
- synthetic-only existing cases
- collapsed categories are experimental only
- canonical ledger remains unchanged
- activation gate remains in play
- no executable schema
- no implementation
- no provider/model calls
- no public ARC/Kaggle data
- no hidden test output leakage

Method note:
Each case was reread through a collapsed-category lens and compared against prior original-category behavior. The question was not whether the cases still looked readable, but whether collapse preserved catches, safe failure, auditability, and diagnostic sharpness.

## 3. Collapse definitions

### A. `absence_of_expected_change_pressure`
Merges:
- negative-evidence pressure
- non-change pressure

Must preserve:
- absence of transformation
- meaningful unchanged regions
- expected-but-missing effects
- evidence from what did not happen

Working interpretation:
Use one family when explanation depends on what lawfully stayed unchanged or what expected effect never occurred.

### B. `salience_distractor_pressure`
Merges:
- distractor-rejection pressure
- color/appearance bait pressure

Must preserve:
- visible-but-incidental features
- color bait
- appearance bait
- salience traps
- rejected salient explanations

Working interpretation:
Use one family when attention must be pulled away from an attractive but incidental feature or object.

### C. `overfit_specificity_pressure`
Merges:
- concept-bloat pressure
- coordinate-overfit pressure

Must preserve:
- invented unnecessary concepts
- train-specific overfit
- coordinate-specific overfit
- overly narrow private language
- weak generality under counterfactual movement

Working interpretation:
Use one family when an explanation becomes too specific, too private, or too brittle to generalize safely.

## 4. Non-collapse list
These remain separate because collapse would still damage structure now:
- exception vs contradiction/precedence
  - local violator identification is not the same as ranking conflicting pressures
- target-location vs role stability
  - task-time selection is not the same as cross-example representational continuity
- action-type vs output-shape
  - operation class and output form can diverge
- rival-grammar vs unresolved ambiguity
  - rival grammar explains why ambiguity exists; it is not merely the ambiguity state itself
- target/action/representation certainty channels
  - they must remain split to prevent fake confidence

## 5. Per-case collapsed trial

### 5.1 role/color inversion
- source artifact: `WESLR_MICRO_THEORY_SYNTHETIC_LEVEL_TRACE_MOCKS_V1.md`
- synthetic-only: `true`
- previous relevant catch: reject appearance bait; preserve role-first targeting
- original pressure behavior: role stability, relation stability, target-location, color/appearance bait, distractor-rejection; overlap present between salience families; safety depended on demoting visible appearance
- collapsed pressure behavior: `salience_distractor_pressure` replaces both salience families; activation clearer; gate mode unchanged (`focused_ledger`); dormant marking still useful
- safety check: protective catch preserved `yes`; safe failure preserved `yes`; rival grammar handling preserved `n/a`; certainty preserved `yes`; counterfactual preserved `n/a`
- auditability check: `same`; minor loss in separating “bait” from “distractor,” but not harmful here
- ceremony check: `reduced`; one salience family is enough
- merge decision: `supports merge`

### 5.2 absence/exception
- source artifact: `WESLR_MICRO_THEORY_SYNTHETIC_LEVEL_TRACE_MOCKS_V1.md`
- synthetic-only: `true`
- previous relevant catch: expected missing change handled without false full prediction
- original pressure behavior: absence, exception, target-location, action-type, negative-evidence, non-change; overlap clearly present in negative-evidence/non-change; safety depended on recognizing missing effect and preserved regions
- collapsed pressure behavior: `absence_of_expected_change_pressure` replaces both overlap families; activation clearer; gate mode unchanged (`focused_ledger`); dormant marking remains useful
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar `n/a`; certainty preserved `yes`; counterfactual `yes`
- auditability check: `same`; little meaningful detail lost
- ceremony check: `reduced`
- merge decision: `supports merge`

### 5.3 ambiguity/rival grammar safe failure
- source artifact: `WESLR_MICRO_THEORY_SYNTHETIC_LEVEL_TRACE_MOCKS_V1.md`
- synthetic-only: `true`
- previous relevant catch: safe-failure instead of fake inevitability
- original pressure behavior: rival-grammar, target-location, action-type, output-shape, counterfactual stability; little direct dependence on collapse candidates
- collapsed pressure behavior: no important merged family dominates; gate mode unchanged (`full_ledger`); dormant marking remains useful
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar preserved `yes`; certainty preserved `yes`; counterfactual preserved `yes`
- auditability check: `same`
- ceremony check: `unchanged`
- merge decision: `inconclusive`

### 5.4 contradiction-resolution
- source artifact: `WESLR_MICRO_THEORY_SYNTHETIC_LEVEL_TRACE_MOCKS_V1.md`
- synthetic-only: `true`
- previous relevant catch: precedence pressure blocks false symmetry fill
- original pressure behavior: contradiction/precedence, exception, negative-evidence, non-change, target-location, action-type; overlap present between negative-evidence/non-change, but safety depended mostly on keeping contradiction separate
- collapsed pressure behavior: `absence_of_expected_change_pressure` can replace the two overlap families; gate mode unchanged (`full_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; certainty preserved `yes`
- auditability check: `same`; precedence remains the sharp diagnostic center
- ceremony check: `reduced`
- merge decision: `supports merge`

### 5.5 stripe-anchor ablation
- source artifact: `WESLR_MICRO_THEORY_LEDGER_ABLATION_CONFIDENT_WRONG_MOCK_V1.md`
- synthetic-only: `true`
- previous relevant catch: live rival grammar and weak counterfactual stability downgrade confident wrong prediction
- original pressure behavior: rival-grammar, target-location, action-type, counterfactual stability, coordinate-overfit
- collapsed pressure behavior: `overfit_specificity_pressure` can stand in for coordinate-overfit only partially; gate mode unchanged (`full_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar preserved `yes`; certainty preserved `yes`; counterfactual preserved `yes`
- auditability check: `weaker`; anchoring-specific language becomes less crisp
- ceremony check: `unchanged`
- merge decision: `supports merge with caution`

### 5.6 Coincident Rival Grammar
- source artifact: `WESLR_MICRO_THEORY_ADVERSARIAL_BIDIRECTIONAL_MOCKS_V1.md`
- synthetic-only: `true`
- previous relevant catch: block fake inevitability while rival grammar survives
- original pressure behavior: rival-grammar, relation stability, target-location, counterfactual stability
- collapsed pressure behavior: no merge candidate materially changes core reading; gate mode unchanged (`full_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar preserved `yes`; counterfactual preserved `yes`
- auditability check: `same`
- ceremony check: `unchanged`
- merge decision: `inconclusive`

### 5.7 Train-Output Overfit
- source artifact: `WESLR_MICRO_THEORY_ADVERSARIAL_BIDIRECTIONAL_MOCKS_V1.md`
- synthetic-only: `true`
- previous relevant catch: overfit / coordinate-overfit exposed
- original pressure behavior: coordinate-overfit, counterfactual stability, rival-grammar, concept-bloat; overlap present but diagnostically valuable
- collapsed pressure behavior: `overfit_specificity_pressure` replaces both overfit families; activation is worse, not clearer; gate mode unchanged (`full_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar preserved `yes`; certainty preserved `yes`; counterfactual preserved `yes`
- auditability check: `weaker`; loss of distinction between private-concept excess and coordinate anchoring is real
- ceremony check: `reduced`
- merge decision: `argues against merge`

### 5.8 Target/Action Split Trap
- source artifact: `WESLR_MICRO_THEORY_ADVERSARIAL_BIDIRECTIONAL_MOCKS_V1.md`
- synthetic-only: `true`
- previous relevant catch: avoid false full prediction
- original pressure behavior: target-location, action-type, rival-grammar, output-shape
- collapsed pressure behavior: merge candidates mostly irrelevant; gate mode unchanged (`focused_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; certainty preserved `yes`
- auditability check: `same`
- ceremony check: `unchanged`
- merge decision: `inconclusive`

### 5.9 AGT-01 clean compact case
- source artifact: `WESLR_MORE_ACTIVATION_GATE_TRIALS_V1.md`
- synthetic-only: `true`
- previous relevant catch: compact no-op remains safe
- original pressure behavior: non-change, output-shape
- collapsed pressure behavior: `absence_of_expected_change_pressure` could substitute for non-change, but adds a slightly heavier name; gate mode unchanged (`compact_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`
- auditability check: `same`
- ceremony check: `unchanged`; no real win here
- merge decision: `supports merge with caution`

### 5.10 AGT-02 medium focused case
- source artifact: `WESLR_MORE_ACTIVATION_GATE_TRIALS_V1.md`
- synthetic-only: `true`
- previous relevant catch: focused relation-first targeting stays trustworthy
- original pressure behavior: relation stability, target-location, action-type, distractor-rejection
- collapsed pressure behavior: `salience_distractor_pressure` can replace distractor-rejection cleanly; gate mode unchanged (`focused_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`
- auditability check: `same`
- ceremony check: `slightly reduced`
- merge decision: `supports merge`

### 5.11 AGT-03 hidden rival risk case
- source artifact: `WESLR_MORE_ACTIVATION_GATE_TRIALS_V1.md`
- synthetic-only: `true`
- previous relevant catch: fake inevitability blocked
- original pressure behavior: rival-grammar, relation stability, target-location, counterfactual stability, output-shape
- collapsed pressure behavior: no merge candidate drives the case; gate mode unchanged (`full_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar preserved `yes`; counterfactual preserved `yes`
- auditability check: `same`
- ceremony check: `unchanged`
- merge decision: `inconclusive`

### 5.12 AGT-04 ignored-feature case
- source artifact: `WESLR_MORE_ACTIVATION_GATE_TRIALS_V1.md`
- synthetic-only: `true`
- previous relevant catch: ignored-feature fail-open still fires
- original pressure behavior: target-location, color/appearance bait, distractor-rejection, rival-grammar, relation stability
- collapsed pressure behavior: `salience_distractor_pressure` replaces both salience families; activation clearer in prose but slightly less diagnostic about whether the issue is raw bait or competing object salience; gate mode unchanged (`full_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar preserved `yes`
- auditability check: `same`
- ceremony check: `reduced`
- merge decision: `supports merge with caution`

### 5.13 AGT-05 certainty disagreement case
- source artifact: `WESLR_MORE_ACTIVATION_GATE_TRIALS_V1.md`
- synthetic-only: `true`
- previous relevant catch: certainty disagreement does not collapse into fake confidence
- original pressure behavior: target-location, action-type, output-shape, rival-grammar, counterfactual stability
- collapsed pressure behavior: no merge candidate materially changes the case; gate mode unchanged (`safe_failure_review`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; certainty preserved `yes`; counterfactual preserved `yes`
- auditability check: `same`
- ceremony check: `unchanged`
- merge decision: `inconclusive`

### 5.14 AGT-06 overfit / coordinate-specific case
- source artifact: `WESLR_MORE_ACTIVATION_GATE_TRIALS_V1.md`
- synthetic-only: `true`
- previous relevant catch: coordinate-specific overfit remains diagnosable
- original pressure behavior: coordinate-overfit, concept-bloat, counterfactual stability, rival-grammar, target-location
- collapsed pressure behavior: `overfit_specificity_pressure` activates, but activation is worse for diagnosis; gate mode unchanged (`full_ledger`)
- safety check: catch preserved `yes`; safe failure preserved `yes`; rival grammar preserved `yes`; counterfactual preserved `yes`
- auditability check: `weaker`; coordinate-specific brittleness becomes less directly inspectable
- ceremony check: `reduced`
- merge decision: `argues against merge`

## 6. Cross-case result table
| case | merged family involved | catch preserved | auditability | ceremony | merge decision |
|---|---|---|---|---|---|
| role/color inversion | salience_distractor_pressure | yes | same | reduced | supports merge |
| absence/exception | absence_of_expected_change_pressure | yes | same | reduced | supports merge |
| ambiguity/rival grammar | none material | yes | same | unchanged | inconclusive |
| contradiction-resolution | absence_of_expected_change_pressure | yes | same | reduced | supports merge |
| stripe-anchor ablation | overfit_specificity_pressure | yes | weaker | unchanged | supports merge with caution |
| Coincident Rival Grammar | none material | yes | same | unchanged | inconclusive |
| Train-Output Overfit | overfit_specificity_pressure | yes | weaker | reduced | argues against merge |
| Target/Action Split Trap | none material | yes | same | unchanged | inconclusive |
| AGT-01 | absence_of_expected_change_pressure | yes | same | unchanged | supports merge with caution |
| AGT-02 | salience_distractor_pressure | yes | same | slightly reduced | supports merge |
| AGT-03 | none material | yes | same | unchanged | inconclusive |
| AGT-04 | salience_distractor_pressure | yes | same | reduced | supports merge with caution |
| AGT-05 | none material | yes | same | unchanged | inconclusive |
| AGT-06 | overfit_specificity_pressure | yes | weaker | reduced | argues against merge |

## 7. Family-level merge decisions
- `absence_of_expected_change_pressure` → `merge_later`
- `salience_distractor_pressure` → `merge_later`
- `overfit_specificity_pressure` → `unsafe_to_merge`

Reasoning:
- the first two merges preserved catches and mostly reduced overlap cleanly, but they should still remain experimental until reviewed
- the third merge weakens diagnosis in exactly the area that earlier work flagged as sensitive

## 8. Protective-catch preservation review
- role/color inversion still rejects appearance/salience bait: yes
- absence/exception still handles expected missing changes: yes
- ambiguity/rival grammar still safe-fails: yes
- contradiction-resolution still activates precedence pressure: yes
- stripe-anchor ablation still catches live rival grammar and weak counterfactual stability: yes
- Coincident Rival Grammar still blocks fake inevitability: yes
- Train-Output Overfit still catches overfit: yes, but less sharply
- Target/Action Split Trap still avoids false full prediction: yes
- AGT-04 ignored-feature fail-open still fires: yes
- AGT-06 coordinate-specific overfit still remains diagnosable: yes, but weaker

## 9. Activation-gate interaction
- category collapse reduces gate complexity: somewhat
- gate modes changed: no
- collapse plus gating reduces ceremony more than gating alone: yes, slightly, mainly in overlap-heavy cases
- collapse plus gating hides uncertainty: not for the first two families; somewhat for the overfit family
- explicit dormant categories remain useful: yes
- gate fail-open rules still work: yes

## 10. Risk review
- diagnostic sharpness loss: real for `overfit_specificity_pressure`
- false simplification: moderate risk if all three merges were adopted together
- unsafe dormancy: not observed in this experiment
- overfit-specificity becoming too vague: yes, this is the central problem
- salience distractor becoming too broad: some risk, but manageable
- absence/non-change losing distinction: low-to-moderate risk, manageable
- future schema risk if collapsed too early: high
- whether any merge should be rejected now: yes; reject `overfit_specificity_pressure` for now

## 11. Trace packet schema implications
- schema remains premature: yes
- collapsed categories stable enough to encode later: only the first two look plausible later; not the third
- future packet should support both canonical and collapsed aliases: maybe later, but only after review and only as aliases, not replacements
- collapse decisions need another review before schema planning: yes

## 12. Recommended next safe local follow-up
`REVIEW_MICRO_THEORY_COLLAPSED_PRESSURE_CATEGORY_EXPERIMENT_V1`

Reason:
The experiment was useful and did not expose an immediate safety failure in execution, but it did reveal one merge that should not progress casually. The next safe step is review before any further collapse work.

## 13. Update WESLR_CURRENT_HANDOFF.md after artifact completion
This artifact should move the local lane state to:
- completed lane: `RUN_MICRO_THEORY_COLLAPSED_PRESSURE_CATEGORY_EXPERIMENT_V1`
- next lane: `REVIEW_MICRO_THEORY_COLLAPSED_PRESSURE_CATEGORY_EXPERIMENT_V1`

## 14. Explicitly forbidden next moves
Remain forbidden:
- runtime solver implementation
- executable ledger implementation
- executable schema implementation
- ChatResponder integration
- provider/model calls
- learned scorer implementation
- final-answer generation
- behavior-pack promotion
- public ARC/Kaggle evaluation
- public score claim
- Kaggle intake/test
- public ARC ingestion
- depth-3 as workaround
- primitive patching under this design
- push preparation
- push

## 15. Final recommendation
The collapsed-category experiment was useful.

Two merges appear safe enough to keep testing experimentally:
- `absence_of_expected_change_pressure`
- `salience_distractor_pressure`

One merge currently appears unsafe to continue toward collapse:
- `overfit_specificity_pressure`

Micro-Theory direction should continue.

Activation gate remains valid.

Schema planning remains premature.

What remains blocked:
- runtime solver implementation
- executable ledger implementation
- executable schema implementation
- provider/model calls
- public ARC/Kaggle intake/test
- public claims
- learned scorer implementation
- final-answer generation
- behavior-pack promotion
- push preparation
- push

What success should look like next:
- review confirms the first two merges really preserve auditability
- review confirms the overfit cluster should remain separate for now
- future simplification, if any, stays selective rather than global
