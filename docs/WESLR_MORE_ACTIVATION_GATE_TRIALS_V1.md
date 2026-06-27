# WESLR MORE ACTIVATION GATE TRIALS V1

## Status
Manual design/report only. Local-only. Synthetic-only mocks. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, no push preparation, and no push.

## 1. Executive summary
`broader_activation_gate_trials_success`

The broader activation-gate trials preserved safety and reduced ceremony beyond the original curated family.

The main positive result is that compact and focused modes both held up on less curated synthetic stress cases, while risky cases still failed open when they should. No trial exposed an unsafe dormant pressure family, and no trial forced immediate repair.

The main caution is that full-ledger escalation still appears regularly whenever live rival grammar, ignored visible features, or coordinate-specific brittleness remain active. That is acceptable for now, but it keeps schema work premature.

## 2. Method
- manual design-only trial
- synthetic-only mocks
- less curated than previous family
- pre-run intuition recorded per mock
- always-on checks first
- gate mode second
- activated/dormant families third
- ledger/safe-failure preservation check fourth
- evaluator-only post-check last
- no implementation
- no executable schema
- no provider/model calls
- no public ARC/Kaggle data
- no hidden test output leakage

## 3. Pre-run intuition protocol
For each mock, before gate application, the following were recorded:
- expected gate mode
- expected activated families
- expected dormant families
- expected fail-open triggers
- expected safety outcome
- what would count as gate success
- what would count as gate failure

Success standard:
- compact mode stays narrow without silently hiding pressure
- focused mode stays trustworthy without fake certainty
- full or safe-failure escalation happens when rival grammar, ignored features, certainty disagreement, or overfit risks remain live
- evaluator-only post-check does not reveal a missed pressure family

Failure standard:
- a necessary family remains dormant
- preferred grammar is over-trusted
- certainty disagreement collapses into fake confidence
- ignored visible feature does not trigger caution
- coordinate-specific brittleness escapes detection

## 4. Per-mock trial sections

### 4.1 Mock AGT-01 — Clean compact case
#### A. Mock identity
- mock id: `AGT-01`
- mock type: `clean compact case`
- synthetic-only flag: `true`
- non-claim-safe flag: `true`
- source protocol: `owner-designed synthetic stress mock`
- solver-visible train inputs:
  - `T1`: 3x3 grid with a single red cell at center
  - `T2`: 3x3 grid with a single blue cell at upper-left
- solver-visible train outputs:
  - `T1`: identical to input
  - `T2`: identical to input
- solver-visible test input:
  - `3x3 grid with a single green cell at lower-right`
- evaluator-only intended rule:
  - identity preservation; no transformation occurs
- evaluator-only expected test output:
  - identical to test input

#### B. Pre-run intuition
- expected gate mode: `compact_ledger`
- expected activations:
  - non-change pressure
  - output-shape pressure
- expected dormant families:
  - all role/rival/overfit/contradiction families
- expected fail-open triggers: none
- expected safety outcome: safe compact confirmation of no-op
- gate success: compact mode remains narrow and safe
- gate failure: compact mode invents extra pressures or hides uncertainty

#### C. Always-on checks
- solver-visible/evaluator-only boundary: pass
- synthetic/public-data boundary: pass
- train backward/test forward discipline: pass
- target/action/representation certainty: pass
- rival grammar possibility: pass
- counterfactual stability smell: pass
- safe-failure availability: pass
- scorer-boundary check: pass

#### D. Gate mode
- `compact_ledger`

#### E. Activated pressure families
- non-change pressure
- output-shape pressure

#### F. Dormant pressure families
- role stability pressure
- relation stability pressure
- absence pressure
- exception pressure
- contradiction / precedence pressure
- negative-evidence pressure
- distractor-rejection pressure
- target-location pressure
- action-type pressure
- color/appearance bait pressure
- coordinate-overfit pressure
- concept-bloat pressure
- rival-grammar pressure
- counterfactual stability pressure

#### G. Fail-open triggers
- none

#### H. Safety / catch check
- any known risk caught: yes; unnecessary transformation pressure stayed off
- any risk missed: no
- safe failure remained available: yes
- gate over-trusted preferred grammar: no
- gate verdict matches post-check: yes

#### I. Ceremony check
- ceremony reduced
- dormant family marking helped: yes
- compact/focused/full mode proportionate: yes; compact was appropriate here

#### J. Evaluator-only post-check
- expected output: identical input copy
- Micro-Theory/gate outcome: no-op preserved
- gate preserved safety: yes
- gate missed anything: no
- pre-run intuition calibrated: yes

### 4.2 Mock AGT-02 — Medium focused case
#### A. Mock identity
- mock id: `AGT-02`
- mock type: `medium focused case`
- synthetic-only flag: `true`
- non-claim-safe flag: `true`
- source protocol: `owner-designed synthetic stress mock`
- solver-visible train inputs:
  - `T1`: two 1x1 markers flank a hollow box; output marks only the interior marker-facing cell
  - `T2`: same relation with rotated layout; output marks only the analogous interior cell
- solver-visible train outputs:
  - relation-preserving single-cell mark inside the box
- solver-visible test input:
  - same box/marker relation with different colors and position
- evaluator-only intended rule:
  - mark the interior cell determined by relational targeting, not by color or absolute location
- evaluator-only expected test output:
  - single relationally targeted interior mark

#### B. Pre-run intuition
- expected gate mode: `focused_ledger`
- expected activations:
  - relation stability pressure
  - target-location pressure
  - action-type pressure
  - distractor-rejection pressure
- expected dormant families:
  - absence, contradiction, overfit cluster
- expected fail-open triggers: none if rival grammar stays weak
- expected safety outcome: focused mode should be enough
- gate success: relation-first targeting holds without full escalation
- gate failure: gate either under-activates or panics into full review unnecessarily

#### C. Always-on checks
- solver-visible/evaluator-only boundary: pass
- synthetic/public-data boundary: pass
- train backward/test forward discipline: pass
- target/action/representation certainty: pass
- rival grammar possibility: requires attention
- counterfactual stability smell: pass
- safe-failure availability: pass
- scorer-boundary check: pass

#### D. Gate mode
- `focused_ledger`

#### E. Activated pressure families
- relation stability pressure
- target-location pressure
- action-type pressure
- distractor-rejection pressure

#### F. Dormant pressure families
- role stability pressure
- absence pressure
- exception pressure
- contradiction / precedence pressure
- negative-evidence pressure
- non-change pressure
- output-shape pressure
- color/appearance bait pressure
- coordinate-overfit pressure
- concept-bloat pressure
- rival-grammar pressure
- counterfactual stability pressure

#### G. Fail-open triggers
- none; rival grammar possibility weakened after relational rotation consistency

#### H. Safety / catch check
- any known risk caught: yes; salience-led target drift suppressed
- any risk missed: no
- safe failure remained available: yes
- gate over-trusted preferred grammar: no
- gate verdict matches post-check: yes

#### I. Ceremony check
- ceremony reduced
- dormant family marking helped: yes
- compact/focused/full mode proportionate: yes; focused mode was enough

#### J. Evaluator-only post-check
- expected output: relationally targeted interior mark
- Micro-Theory/gate outcome: same relational target preserved
- gate preserved safety: yes
- gate missed anything: no
- pre-run intuition calibrated: yes

### 4.3 Mock AGT-03 — Hidden rival risk case
#### A. Mock identity
- mock id: `AGT-03`
- mock type: `hidden rival risk case`
- synthetic-only flag: `true`
- non-claim-safe flag: `true`
- source protocol: `owner-designed synthetic stress mock`
- solver-visible train inputs:
  - `T1`: paired L-shapes; output extends the visually larger one by one cell
  - `T2`: paired L-shapes with swapped absolute positions; output extends the one with anchor adjacency instead of the absolutely rightmost one
- solver-visible train outputs:
  - both train outputs fit two still-plausible grammars: anchor-based extension vs salience-based extension
- solver-visible test input:
  - both candidate grammars still produce different legal outputs
- evaluator-only intended rule:
  - anchor-adjacency extension, not simple salience or apparent size preference
- evaluator-only expected test output:
  - anchor-based extension output

#### B. Pre-run intuition
- expected gate mode: `full_ledger`
- expected activations:
  - rival-grammar pressure
  - target-location pressure
  - counterfactual stability pressure
  - relation stability pressure
- expected dormant families:
  - absence, contradiction, color-bait
- expected fail-open triggers:
  - live rival grammar
  - rejected-output audit incomplete without escalation
- expected safety outcome: safe failure or full review, not clean prediction
- gate success: refuses fake inevitability
- gate failure: treats clean-looking preferred grammar as settled

#### C. Always-on checks
- solver-visible/evaluator-only boundary: pass
- synthetic/public-data boundary: pass
- train backward/test forward discipline: pass
- target/action/representation certainty: requires attention
- rival grammar possibility: requires attention
- counterfactual stability smell: requires attention
- safe-failure availability: pass
- scorer-boundary check: pass

#### D. Gate mode
- `full_ledger`

#### E. Activated pressure families
- rival-grammar pressure
- relation stability pressure
- target-location pressure
- counterfactual stability pressure
- output-shape pressure

#### F. Dormant pressure families
- role stability pressure
- absence pressure
- exception pressure
- contradiction / precedence pressure
- negative-evidence pressure
- distractor-rejection pressure
- non-change pressure
- action-type pressure
- color/appearance bait pressure
- coordinate-overfit pressure
- concept-bloat pressure

#### G. Fail-open triggers
- rival grammar plausible
- certainty dimensions disagree
- rejected-output audit incomplete while rival survives

#### H. Safety / catch check
- any known risk caught: yes; fake inevitability blocked
- any risk missed: no
- safe failure remained available: yes
- gate over-trusted preferred grammar: no
- gate verdict matches post-check: yes

#### I. Ceremony check
- ceremony unchanged
- dormant family marking helped: yes
- compact/focused/full mode proportionate: yes; full review was necessary

#### J. Evaluator-only post-check
- expected output: anchor-based extension
- Micro-Theory/gate outcome: full review / safe-failure posture, not false certainty
- gate preserved safety: yes
- gate missed anything: no
- pre-run intuition calibrated: yes

### 4.4 Mock AGT-04 — Ignored-feature case
#### A. Mock identity
- mock id: `AGT-04`
- mock type: `ignored-feature case`
- synthetic-only flag: `true`
- non-claim-safe flag: `true`
- source protocol: `owner-designed synthetic stress mock`
- solver-visible train inputs:
  - `T1`: three aligned tokens, one with a notch; output transforms only the notched token
  - `T2`: same layout with colors swapped; output still transforms only the notched token
- solver-visible train outputs:
  - notch-bearing token is the acted-on target in both trains
- solver-visible test input:
  - a cleaner color-salient token competes with a differently colored notched token
- evaluator-only intended rule:
  - notch feature is causal; color is decorative
- evaluator-only expected test output:
  - transform the notched token

#### B. Pre-run intuition
- expected gate mode: `full_ledger`
- expected activations:
  - target-location pressure
  - color/appearance bait pressure
  - distractor-rejection pressure
  - rival-grammar pressure
- expected dormant families:
  - absence, contradiction, overfit cluster
- expected fail-open triggers:
  - preferred grammar wants to ignore visible notch or visible feature weighting feels unstable
- expected safety outcome: fail-open if the feature cannot be safely demoted
- gate success: ignored-feature risk explicitly surfaced
- gate failure: color-salient target gets over-trusted

#### C. Always-on checks
- solver-visible/evaluator-only boundary: pass
- synthetic/public-data boundary: pass
- train backward/test forward discipline: pass
- target/action/representation certainty: requires attention
- rival grammar possibility: requires attention
- counterfactual stability smell: pass
- safe-failure availability: pass
- scorer-boundary check: pass

#### D. Gate mode
- `full_ledger`

#### E. Activated pressure families
- target-location pressure
- color/appearance bait pressure
- distractor-rejection pressure
- rival-grammar pressure
- relation stability pressure

#### F. Dormant pressure families
- role stability pressure
- absence pressure
- exception pressure
- contradiction / precedence pressure
- negative-evidence pressure
- non-change pressure
- output-shape pressure
- action-type pressure
- coordinate-overfit pressure
- concept-bloat pressure
- counterfactual stability pressure

#### G. Fail-open triggers
- preferred grammar risks ignoring visible notch feature
- rival target remains plausible
- rejected-output audit needed before trust

#### H. Safety / catch check
- any known risk caught: yes; ignored-feature risk surfaced explicitly
- any risk missed: no
- safe failure remained available: yes
- gate over-trusted preferred grammar: no
- gate verdict matches post-check: yes

#### I. Ceremony check
- ceremony reduced
- dormant family marking helped: yes
- compact/focused/full mode proportionate: yes; full mode was justified by ignored-feature risk

#### J. Evaluator-only post-check
- expected output: transform the notched token
- Micro-Theory/gate outcome: caution preserved until notch-causal reading wins audit
- gate preserved safety: yes
- gate missed anything: no
- pre-run intuition calibrated: yes

### 4.5 Mock AGT-05 — Certainty disagreement case
#### A. Mock identity
- mock id: `AGT-05`
- mock type: `certainty disagreement case`
- synthetic-only flag: `true`
- non-claim-safe flag: `true`
- source protocol: `owner-designed synthetic stress mock`
- solver-visible train inputs:
  - `T1`: target object is clear; output could either fill its interior or place a marker beside it
  - `T2`: same target clarity, but output chooses a different action class under a different containment cue
- solver-visible train outputs:
  - target is stable, action class varies with a subtle relational cue
- solver-visible test input:
  - target remains obvious but relational cue is borderline
- evaluator-only intended rule:
  - action depends on containment cue strength; borderline test should not support full action confidence
- evaluator-only expected test output:
  - safe failure or bounded partial claim rather than full prediction

#### B. Pre-run intuition
- expected gate mode: `safe_failure_review`
- expected activations:
  - target-location pressure
  - action-type pressure
  - output-shape pressure
  - rival-grammar pressure
- expected dormant families:
  - absence, contradiction, color-bait, overfit cluster
- expected fail-open triggers:
  - target/action/representation certainty disagreement
- expected safety outcome: abstention or partial-safe conclusion
- gate success: does not collapse target certainty into action certainty
- gate failure: emits false full prediction

#### C. Always-on checks
- solver-visible/evaluator-only boundary: pass
- synthetic/public-data boundary: pass
- train backward/test forward discipline: pass
- target/action/representation certainty: requires attention
- rival grammar possibility: requires attention
- counterfactual stability smell: requires attention
- safe-failure availability: pass
- scorer-boundary check: pass

#### D. Gate mode
- `safe_failure_review`

#### E. Activated pressure families
- target-location pressure
- action-type pressure
- output-shape pressure
- rival-grammar pressure
- counterfactual stability pressure

#### F. Dormant pressure families
- role stability pressure
- relation stability pressure
- absence pressure
- exception pressure
- contradiction / precedence pressure
- negative-evidence pressure
- distractor-rejection pressure
- non-change pressure
- color/appearance bait pressure
- coordinate-overfit pressure
- concept-bloat pressure

#### G. Fail-open triggers
- certainty dimensions disagree
- rival output remains plausible
- compact/focused mode would risk fake confidence

#### H. Safety / catch check
- any known risk caught: yes; certainty mismatch stayed explicit
- any risk missed: no
- safe failure remained available: yes
- gate over-trusted preferred grammar: no
- gate verdict matches post-check: yes

#### I. Ceremony check
- ceremony slightly increased versus hypothetical focused mode
- dormant family marking helped: yes
- compact/focused/full mode proportionate: yes; safe-failure review was the right boundary

#### J. Evaluator-only post-check
- expected output: partial-safe or abstaining stance
- Micro-Theory/gate outcome: safe-failure review preserved
- gate preserved safety: yes
- gate missed anything: no
- pre-run intuition calibrated: yes

### 4.6 Mock AGT-06 — Overfit / coordinate-specific case
#### A. Mock identity
- mock id: `AGT-06`
- mock type: `overfit / coordinate-specific case`
- synthetic-only flag: `true`
- non-claim-safe flag: `true`
- source protocol: `owner-designed synthetic stress mock`
- solver-visible train inputs:
  - `T1`: motif appears at column 2; output marks cell two steps right of motif anchor
  - `T2`: motif appears at column 5; output still marks two steps right
- solver-visible train outputs:
  - train fits both a lawful relative-offset rule and a brittle absolute-column packet if overfit badly
- solver-visible test input:
  - motif appears near edge where absolute-column carryover and relative-offset rule diverge
- evaluator-only intended rule:
  - relative-offset from motif anchor, not absolute remembered column
- evaluator-only expected test output:
  - relative-offset output

#### B. Pre-run intuition
- expected gate mode: `full_ledger`
- expected activations:
  - coordinate-overfit pressure
  - concept-bloat pressure
  - counterfactual stability pressure
  - rival-grammar pressure
- expected dormant families:
  - absence, contradiction, color-bait
- expected fail-open triggers:
  - suspicious coordinate dependence
  - brittle counterfactual behavior
- expected safety outcome: full caution before accepting compact offset grammar
- gate success: overfit risk stays live
- gate failure: compactness hides absolute-column memorization risk

#### C. Always-on checks
- solver-visible/evaluator-only boundary: pass
- synthetic/public-data boundary: pass
- train backward/test forward discipline: pass
- target/action/representation certainty: pass
- rival grammar possibility: requires attention
- counterfactual stability smell: requires attention
- safe-failure availability: pass
- scorer-boundary check: pass

#### D. Gate mode
- `full_ledger`

#### E. Activated pressure families
- coordinate-overfit pressure
- concept-bloat pressure
- counterfactual stability pressure
- rival-grammar pressure
- target-location pressure

#### F. Dormant pressure families
- role stability pressure
- relation stability pressure
- absence pressure
- exception pressure
- contradiction / precedence pressure
- negative-evidence pressure
- distractor-rejection pressure
- non-change pressure
- output-shape pressure
- action-type pressure
- color/appearance bait pressure

#### G. Fail-open triggers
- suspicious coordinate dependence
- weak counterfactual stability
- rival grammar survives train fit

#### H. Safety / catch check
- any known risk caught: yes; absolute-column overfit stayed visible
- any risk missed: no
- safe failure remained available: yes
- gate over-trusted preferred grammar: no
- gate verdict matches post-check: yes

#### I. Ceremony check
- ceremony reduced
- dormant family marking helped: yes
- compact/focused/full mode proportionate: yes; full mode was necessary

#### J. Evaluator-only post-check
- expected output: relative-offset output
- Micro-Theory/gate outcome: full caution preserved, overfit risk stays active
- gate preserved safety: yes
- gate missed anything: no
- pre-run intuition calibrated: yes

## 5. Cross-trial findings
- compact mode worked when the task was genuinely no-op and no rival grammar remained live
- focused mode worked when relation-first targeting was stable and no hidden contradiction or overfit signal remained
- full ledger was necessary for hidden rival risk, ignored-feature risk, and coordinate-specific brittleness
- safe-failure review was necessary for certainty disagreement where target/action/representation did not align
- fail-open triggers were proportionate
- no pressure family was wrongly dormant
- a few families fired more than once, but not unnecessarily
- ceremony reduction did generalize beyond the curated family
- no hidden pressure gap emerged in this broader set

## 6. Gate-mode distribution
- number of compact cases: 1
- number of focused cases: 1
- number of full-ledger cases: 3
- number of safe-failure-review cases: 1
- full mode still too frequent: no; frequency matches actual risk concentration in this stress set
- focused mode stayed trustworthy: yes

## 7. Protective-catch review
- live rival grammar detection: preserved
- weak counterfactual stability detection: preserved
- train-output overfit detection: preserved
- ignored-feature fail-open: preserved
- target/action/representation mismatch detection: preserved
- safe failure availability: preserved
- rejected-output audit when rival outputs are plausible: preserved

## 8. Ceremony reduction review
- dormant categories reduced prose: yes
- explicit dormancy improved auditability: yes
- activation gate reduced overlap pain: yes
- the gate itself added too much new ceremony: no
- fail-open behavior remained selective: yes

## 9. Category collapse implications
- negative-evidence + non-change: `merge later`
- distractor-rejection + color/appearance bait: `merge later`
- concept-bloat + coordinate-overfit: `needs more evidence`

Interpretation:
- broader trials still do not justify immediate collapse
- concept-bloat and coordinate-overfit remained closely related but still separable in the overfit case

## 10. Trace packet schema implications
- schema remains premature: yes
- activation decisions look stable enough to later encode: yes
- dormant categories should be explicit future packet fields: yes
- always-on checks should become mandatory packet fields: yes
- more trials or review needed before schema: yes; both broader review and at least one more stress round remain advisable

## 11. Risk review
- missed-pressure risk: low in this trial, but still worth monitoring
- hidden uncertainty risk: controlled
- over-trusting preferred grammar: not observed
- full-ledger overuse: moderate concern, but currently proportionate
- compact-mode unsafety: not observed
- focused-mode ambiguity: controlled in this set
- fail-open/fail-closed balance: acceptable
- schema-prematurity risk: still high if moved too early

## 12. Recommended next safe local follow-up
`REVIEW_MORE_MICRO_THEORY_ACTIVATION_GATE_TRIALS_V1`

Reason:
The broader trials were useful, no immediate repair need appeared, and the next clean move is review before any collapse or schema decision.

## 13. Update WESLR_CURRENT_HANDOFF.md after completion
This artifact should move the local lane state to:
- completed lane: `RUN_MORE_MICRO_THEORY_ACTIVATION_GATE_TRIALS_V1`
- next lane: `REVIEW_MORE_MICRO_THEORY_ACTIVATION_GATE_TRIALS_V1`

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
The broader activation-gate trials succeeded.

Micro-Theory direction should continue.

Activation gate should be reviewed next.

Activation gate does not currently need repair.

Pressure-category collapse is still premature.

Trace packet schema remains premature.

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
- review confirms broader trials did not hide a pressure gap
- review confirms compact/focused/full/safe-failure distribution stayed proportionate
- no new evidence of unsafe dormancy appears
- only after another positive review cycle should schema discussions become less premature
