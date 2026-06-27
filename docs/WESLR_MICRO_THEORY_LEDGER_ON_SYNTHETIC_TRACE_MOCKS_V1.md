# WESLR MICRO-THEORY LEDGER ON SYNTHETIC TRACE MOCKS V1

## Status
Manual design/report only. Synthetic-only mock application. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, and no push.

## 1. Executive summary
`ledger_application_useful_but_heavy`

Manual ledger application helped.

It did not collapse into pure ceremony, but it did reveal that the ledger is near the upper edge of tolerable complexity for compact synthetic traces. The application added real value in four places:
- clarifying what train outputs forced backward
- separating target certainty from action certainty
- making rival-output rejection auditable
- making contradiction / precedence explicit rather than atmospheric

The application was heaviest in the absence/exception and contradiction-resolution mocks, where several pressure families partially overlap. Even there, the ledger stayed more useful than ceremonial.

The main conclusion is:
- the ledger is worth keeping
- the ledger improves the four mocks materially
- schema hardening is still premature
- review should happen before any simplification or packet-schema lane

## 2. Method
This artifact is a manual design-only application of the Micro-Theory Pressure and Inevitability Ledger V1 to four existing synthetic trace mocks.

Method constraints:
- synthetic-only mocks
- no executable schema
- no solver behavior
- no runtime wiring
- no provider/model calls
- no public ARC/Kaggle data
- no hidden test output access
- no evaluator-only expected output usage

Discipline used:
- train pairs: backward-from-train-output reasoning only
- test input: forward-to-test-input reasoning only
- safe failure retained whenever target certainty, action certainty, representation certainty, or rival-grammar pressure did not jointly support a safe prediction

The goal was not to beautify the mocks. The goal was to see whether the ledger makes pressure, rejection, certainty, contradiction, and abstention more inspectable.

## 3. Per-mock ledger application

### 3.1 Mock 1 — role/color inversion

#### A. Mock identity
- `ledger_id`: `micro_pressure_application_role_color_inversion_001`
- `source_trace_id`: `micro_trace_mock_role_color_inversion_001`
- `synthetic_level_id`: `ue_synth_role_color_inversion_001`
- `synthetic_only`: `true`
- `non_claim_safe`: `true`
- `cognitive_gym_compatible`: `true`

#### B. Train backward pressure
- what train output required:
  - train outputs required that the transformed object be explainable by a stable functional role rather than a stable hue token
- causal role / relation / absence / exception / contradiction:
  - causal role: `opening_side_target`
  - causal relation: `nearest opening while inside container`
  - exception: train B makes prior color-based expectation fail
  - contradiction: none central
- what visible feature became incidental:
  - raw target color
  - external distractor color similarity
  - absolute container position
- what rival output was rejected:
  - `recolor object with train-A target color`
  - `recolor leftmost interior object`
- why the train output became more inevitable:
  - train B color inversion preserves role while breaking color-first selection, so role stability and appearance-bait rejection jointly make the role-first explanation stronger

#### C. Forward test projection
- whether train-derived representation parses test input:
  - yes; the test still contains one interior object satisfying the `opening_side_target` role
- target certainty:
  - `forced`
- action certainty:
  - `strongly_supported`
- representation certainty:
  - `strongly_supported`
- rival grammar pressure:
  - low; color-first and leftmost-first rivals are weakened by train inversion and opening-shift counterfactual logic
- safe prediction or safe failure:
  - safe prediction

#### D. Pressure categories activated
- role stability pressure
- relation stability pressure
- negative evidence pressure
- distractor rejection pressure
- non-change pressure
- target-location pressure
- action-type pressure
- color/appearance bait pressure
- coordinate-overfit pressure
- counterfactual stability pressure

#### E. Rejected outputs / why-not audit
- rejected output claim:
  - recolor the object with the same hue as the earlier train target
- rejection reason:
  - hue continuity fails when role continuity survives color inversion
- evidence against:
  - train B preserves transformed role but not transformed hue
- remaining uncertainty:
  - low
- unsafe if not rejected:
  - yes; color-first and role-first outputs could diverge on test

#### F. Inevitability label
- `strongly_supported`

#### G. Safe failure summary
- no safe failure needed
- why:
  - target is uniquely forced by role; action type is stable enough; representation is compact and reusable

#### H. Ceremony risk note
The ledger helped more than it hurt here. This mock is one of the cleanest fits for the ledger because role stability, appearance bait, and distractor rejection become visibly separable.

---

### 3.2 Mock 2 — absence/exception

#### A. Mock identity
- `ledger_id`: `micro_pressure_application_absence_exception_001`
- `source_trace_id`: `micro_trace_mock_absence_exception_001`
- `synthetic_level_id`: `ue_synth_absence_exception_001`
- `synthetic_only`: `true`
- `non_claim_safe`: `true`
- `cognitive_gym_compatible`: `true`

#### B. Train backward pressure
- what train output required:
  - train outputs required that the acted-on location be an expected-but-absent frame member rather than any visible salient object
- causal role / relation / absence / exception / contradiction:
  - causal absence: `missing_corner_se`
  - causal role: `repair_target`
  - causal relation: rectangular completion / diagonal closure
  - exception: `loose_distractor` is bright, visible, and ignored
  - contradiction: weak local salience pressure conflicts with stronger absence-repair pressure, but no deep precedence object is needed
- what visible feature became incidental:
  - distractor brightness
  - distractor isolation
  - exact distractor distance from frame
- what rival output was rejected:
  - `transform the brightest isolated object`
  - `copy majority color into arbitrary empty position`
- why the train output became more inevitable:
  - repeated unchanged distractor plus repeated incomplete frame pressure makes absence-led repair more explanatory than salience-led action

#### C. Forward test projection
- whether train-derived representation parses test input:
  - yes; the test still instantiates an almost-complete frame with one missing member and one loud distractor
- target certainty:
  - `forced`
- action certainty:
  - `weakly_supported`
- representation certainty:
  - `strongly_supported`
- rival grammar pressure:
  - low for target selection, moderate for action type if train evidence does not fully separate `fill` from `mark`
- safe prediction or safe failure:
  - partial-safe claim only

#### D. Pressure categories activated
- absence pressure
- exception pressure
- negative evidence pressure
- distractor rejection pressure
- non-change pressure
- output-shape pressure
- target-location pressure
- action-type pressure
- counterfactual stability pressure

#### E. Rejected outputs / why-not audit
- rejected output claim:
  - transform the visible bright distractor
- rejection reason:
  - distractor has no frame-membership relation and cannot explain repeated missing-corner closure
- evidence against:
  - distractor remains unchanged across train while the broken frame is consistently repaired
- remaining uncertainty:
  - moderate, but mostly about action type, not target location
- unsafe if not rejected:
  - yes; salience-led targeting would produce a different output family

#### F. Inevitability label
- `weakly_supported`

#### G. Safe failure summary
- partial-safe claim only
- why:
  - target location is well-supported, but action type may remain underdetermined unless the trace already proves `fill` versus `mark`

#### H. Ceremony risk note
This mock showed real ledger value, especially for target/action separation. It also showed ledger heaviness because absence pressure, exception pressure, negative evidence pressure, and non-change pressure partially stack on the same phenomenon.

---

### 3.3 Mock 3 — ambiguity / rival grammar safe failure

#### A. Mock identity
- `ledger_id`: `micro_pressure_application_rival_grammar_001`
- `source_trace_id`: `micro_trace_mock_rival_grammar_001`
- `synthetic_level_id`: `ue_synth_rival_grammar_001`
- `synthetic_only`: `true`
- `non_claim_safe`: `true`
- `cognitive_gym_compatible`: `true`

#### B. Train backward pressure
- what train output required:
  - train outputs required an explanation for why one unit is added in a place jointly compatible with mirror completion and count progression
- causal role / relation / absence / exception / contradiction:
  - grammar A relation: mirror symmetry around centerline
  - grammar B relation: ordered progression toward terminal marker
  - possible absence under grammar A: `missing_mirror_partner`
  - possible absence under grammar B: `missing_next_count_step`
  - contradiction: not hard contradiction, but unresolved rivalry between two compact explanatory systems
- what visible feature became incidental:
  - superficial color layout that both grammars can restate
  - exact placement details not doing disambiguating work
- what rival output was rejected:
  - no decisive rejection available
- why the train output became more inevitable:
  - it did not become more inevitable; train evidence left both grammars alive

#### C. Forward test projection
- whether train-derived representation parses test input:
  - yes under both live grammars
- target certainty:
  - `unresolved`
- action certainty:
  - `unresolved`
- representation certainty:
  - `weakly_supported`
- rival grammar pressure:
  - high; two compact train-consistent theories remain live and imply different safe outputs
- safe prediction or safe failure:
  - safe failure

#### D. Pressure categories activated
- rival-grammar pressure
- relation stability pressure
- output-shape pressure
- target-location pressure
- action-type pressure
- counterfactual stability pressure
- concept-bloat pressure

#### E. Rejected outputs / why-not audit
- rejected output claim:
  - none fully rejected; both candidate outputs remain live
- rejection reason:
  - no disambiguating train evidence exists
- evidence against:
  - counterfactual disambiguators are imaginable but absent from train
- remaining uncertainty:
  - high
- unsafe if not rejected:
  - yes; prediction would exceed what train-derived evidence justifies

#### F. Inevitability label
- `unsafe_to_predict`

#### G. Safe failure summary
- safe failure needed
- why:
  - rival grammars disagree, target/action are unresolved, and representation certainty is insufficiently unique for bounded prediction

#### H. Ceremony risk note
The ledger is extremely useful here. This is the best case for the design because it turns abstention into an explicit, structured result instead of a vague shrug.

---

### 3.4 Mock 4 — contradiction-resolution

#### A. Mock identity
- `ledger_id`: `micro_pressure_application_contradiction_resolution_001`
- `source_trace_id`: `micro_trace_mock_contradiction_resolution_001`
- `synthetic_level_id`: `ue_synth_contradiction_resolution_001`
- `synthetic_only`: `true`
- `non_claim_safe`: `true`
- `cognitive_gym_compatible`: `true`

#### B. Train backward pressure
- what train output required:
  - train outputs required that local symmetry pressure be real but vetoed inside protected containment zones
- causal role / relation / absence / exception / contradiction:
  - causal role: `protection_authority`
  - causal relation: protected containment outranks local symmetry completion
  - causal absence: `missing_symmetric_member` exists but is non-fillable inside protection scope
  - exception: protected container marks a lawful exception to naive symmetry repair
  - contradiction: strong and first-class; `local symmetry fill` conflicts with `protected interior must remain unchanged`
- what visible feature became incidental:
  - peer color matching once protection already explains the veto
- what rival output was rejected:
  - `always complete local symmetry even inside the protected container`
- why the train output became more inevitable:
  - repeated preservation of protected interiors across train pairs earns a precedence claim for protection over local completion

#### C. Forward test projection
- whether train-derived representation parses test input:
  - yes; the protected container relation and the tempting local gap both remain present
- target certainty:
  - `strongly_supported`
- action certainty:
  - `forced`
- representation certainty:
  - `strongly_supported`
- rival grammar pressure:
  - low to moderate; unconditional symmetry completion remains imaginable but is weakened by train-proven veto logic
- safe prediction or safe failure:
  - safe prediction

#### D. Pressure categories activated
- contradiction / precedence pressure
- exception pressure
- negative evidence pressure
- non-change pressure
- output-shape pressure
- target-location pressure
- action-type pressure
- rival-grammar pressure
- counterfactual stability pressure

#### E. Rejected outputs / why-not audit
- rejected output claim:
  - fill the gap to satisfy local symmetry
- rejection reason:
  - that output violates the higher-order protected-container rule repeated in train evidence
- evidence against:
  - protected regions remain unchanged across train even when symmetry temptation exists
- remaining uncertainty:
  - low
- unsafe if not rejected:
  - yes; symmetry-overfit would wrongly authorize a fill

#### F. Inevitability label
- `strongly_supported`

#### G. Safe failure summary
- no safe failure needed
- why:
  - precedence is earned by train evidence and the test instantiates the same protected contradiction pattern

#### H. Ceremony risk note
The ledger helped a lot here because contradiction / precedence became much clearer than in the original trace. This mock still carries some heaviness because exception, contradiction, negative evidence, and non-change partially interlock.

## 4. Cross-mock findings
Where the ledger helped most:
- mock 3: safe failure became precise rather than rhetorical
- mock 4: contradiction / precedence became first-class rather than prose-only
- mock 2: target/action separation became visibly necessary
- mock 1: appearance bait and role stability became easier to compare

Where the ledger was heavy:
- mock 2 and mock 4 carried the most category overlap
- non-change pressure and negative evidence pressure often feel adjacent
- distractor rejection pressure and appearance bait pressure can partially overlap in salience-heavy scenes

Whether target/action separation mattered:
- yes, strongly
- mock 2 would have stayed under-described without it
- mock 3 also benefited because unresolved target/action status became a structured abstention reason

Whether rejected-output audit mattered:
- yes
- especially in mock 1 and mock 4, it made the rival-output boundary much sharper
- in mock 3, the inability to reject rivals became itself an important audit result

Whether contradiction precedence improved:
- yes, especially in mock 4
- the ledger made it possible to say that local symmetry remains real but lower-order

Whether safe failure was better disciplined:
- yes
- mock 3 improved the most
- mock 2 also benefited through partial-safe claim discipline

Whether bidirectional pressure helped:
- yes
- backward-from-train-output clarified what causal commitments the train outputs forced
- forward-to-test-input kept the method from drifting into answer-key fantasy

Cross-mock conclusion:
The ledger improved all four mocks, but not equally. It was most valuable wherever the core difficulty was ambiguity, contradiction, or partial certainty. It was least novel, though still useful, in the cleaner role/color inversion case.

## 5. Scorer-boundary check
Confirmed:
- labels stayed qualitative
- no numeric scoring was introduced
- no learned scorer behavior was introduced
- no benchmark/public-performance implication was made
- safe failure remained available

The application did not drift into fake confidence scoring. Even the inevitability labels remained coarse descriptive categories rather than hidden metrics.

## 6. Complexity / ceremony check
Useful fields:
- `train_backward_pressure`
- `test_forward_projection`
- `target_certainty`
- `action_certainty`
- `representation_certainty`
- `rejected_output_claims`
- `why_not_other_output`
- `safe_failure_summary`

Heavier fields or category clusters:
- negative evidence pressure + non-change pressure
- distractor rejection pressure + color/appearance bait pressure in some cases
- exception pressure can partially blend with contradiction / precedence pressure in protected-rule scenes

Whether manual application remained readable:
- yes, but close to the limit for compact mock artifacts

Whether schema hardening is premature:
- yes
- the application helped, but the complexity profile should be reviewed before any packet schema lane

Potential future merge candidates if later simplification is needed:
- negative evidence pressure with non-change pressure
- distractor rejection pressure with color/appearance bait pressure in selected contexts

## 7. Cognitive Gym compatibility
Confirmed:
- synthetic level references preserved
- trace/ledger metadata preserved
- solver-visible/evaluator-only split respected
- boundary flags preserved
- auditable pressure categories preserved
- explicit safe failure preserved
- no private mythology
- no public-performance claims

The application remains protocol-migratable rather than private or mystical.

## 8. Recommended next safe follow-up
`REVIEW_MICRO_THEORY_LEDGER_ON_SYNTHETIC_TRACE_MOCKS_V1`

Reason:
The application was useful and materially clarifying, but it was also dense enough that a review pass should assess whether the added structure is genuinely proportionate before any simplification or schema lane.

## 9. Explicitly forbidden next moves
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
- depth-3 as workaround
- primitive patching under this design

## 10. Final recommendation
Ledger application was useful.

Micro-Theory direction should continue.

Review is needed before schema work.

Simplification is not yet mandatory, but may become relevant if review agrees that the overlapping pressure families create unnecessary ceremony.

Trace packet schema is still premature.

What remains blocked:
- runtime solver implementation
- executable ledger implementation
- executable schema implementation
- solver patching
- provider/model calls
- public data ingestion
- public claims
- learned scorer implementation
- final-answer generation
- behavior-pack promotion

What success should look like next:
- a review confirms whether the added ledger structure is proportionate
- the review identifies whether any pressure families should merge
- the review confirms that safe failure, rejected-output audit, and certainty separation are materially better than in the original mocks
- schema work remains blocked unless that review stays clearly positive

## 11. Final note
I’m glad we ran the ledger manually before any schema lane. It surfaced the real tradeoff clearly: this design adds genuine interpretive discipline, but it also carries enough weight that it should earn its complexity through review before becoming more formal.
