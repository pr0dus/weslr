# WESLR MICRO-THEORY ADVERSARIAL BIDIRECTIONAL MOCKS V1

## Status
Manual design/report only. Local-only. Synthetic-only adversarial diagnostics. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, no push preparation, and no push.

## 1. Executive summary
`adversarial_mocks_ledger_holds_but_heavy`

The adversarial mocks strengthened confidence in the ledger.

Across three synthetic attacks, Micro-Theory alone repeatedly produced elegant but fragile forward projections, while the ledger either blocked false inevitability or downgraded prediction into partial-safe/unsafe-to-predict outcomes. That is a real win.

At the same time, ceremony risk remained visible enough that activation gating now looks like the best next design lane. The ledger held, but it held with noticeable weight.

## 2. Method
- handoff reconciled first
- manual design-only diagnostic
- synthetic-only adversarial mocks
- pre-run intuition recorded before each mock
- Micro-Theory-alone baseline first
- ledger-applied comparison second
- evaluator-only post-check last
- no executable schema
- no solver/runtime/provider/model calls
- no public ARC/Kaggle data
- no hidden test output leakage

## 3. Pre-run intuition protocol
For each mock I recorded:
- expected Micro-Theory-alone behavior
- expected ledger behavior
- expected failure mode
- expected safety outcome
- what would count as ledger success
- what would count as ledger failure

This was used consistently across all three mocks.

## 4. Mock A: Coincident Rival Grammar
### Pre-run intuition
- expected Micro-Theory-alone behavior: compress toward the cleaner-looking symmetry grammar
- expected ledger behavior: detect a second live grammar and refuse fake inevitability
- expected failure mode: compression mistaken for uniqueness
- expected safety outcome: safe failure
- ledger success: rival grammar caught before reveal
- ledger failure: one grammar declared forced without real rejection trail

### Mock definition
- mock id: `ue_adv_bidirectional_rival_001`
- synthetic-only: `true`
- non-claim-safe: `true`

Solver-visible train inputs:
- two train scenes each contain a diagonal pair and one extra marker near an edge
- both a `mirror completion` grammar and a `marker-directed completion` grammar explain train outputs equally well

Solver-visible train outputs:
- train A completes the upper-right candidate
- train B completes the upper-right candidate

Solver-visible test input:
- same diagonal family, but edge marker moves to the opposite side while mirror completion still remains plausible

Evaluator-only intended rule:
- completion follows marker-directed side, not pure mirror completion

Evaluator-only expected test output:
- complete the opposite-side candidate relative to the baseline mirror grammar

### Micro-Theory-alone baseline
- private language: `dominant diagonal completion`
- baseline behavior: predicts the mirror-consistent candidate with strong confidence
- problem: treats edge marker as non-causal ornament because train never forced separation

### Ledger-applied comparison
- train backward pressure: both mirror and marker-directed grammars remain alive
- test forward projection: test diverges exactly where live grammars disagree
- representation certainty: `weakly_supported`
- rival grammar pressure: high
- rejected-output audit: incomplete for rejecting marker-directed output
- counterfactual stability: weak because train never varied marker-side independently
- inevitability label: `unsafe_to_predict`
- safe failure: yes

### Evaluator-only post-check
- Micro-Theory-alone: wrong
- ledger: abstained
- whether ledger caught live rival grammar: yes
- whether compression was prevented from becoming fake inevitability: yes
- ceremony note: moderate, but worth it

## 5. Mock B: Train-Output Overfit
### Pre-run intuition
- expected Micro-Theory-alone behavior: invent a tidy coordinate-relative grammar from train coincidences
- expected ledger behavior: call out weak counterfactual stability and representation overfit
- expected failure mode: brittle private language fitted to train placements
- expected safety outcome: unsafe-to-predict
- ledger success: overfit identified before reveal
- ledger failure: brittle grammar promoted as strongly supported

### Mock definition
- mock id: `ue_adv_bidirectional_overfit_001`
- synthetic-only: `true`
- non-claim-safe: `true`

Solver-visible train inputs:
- two scenes each contain a small cluster and a highlighted cell exactly two rows below its anchor
- outputs mark the cell two rows below
- in both trains, the lawful relation and the accidental absolute offset coincide

Solver-visible train outputs:
- mark the lower cell in both train examples

Solver-visible test input:
- anchor and cluster rotate so that the lawful relational target is now to the right, while a cell still exists two rows below

Evaluator-only intended rule:
- act on the role-defined follower cell, not the absolute two-rows-below offset

Evaluator-only expected test output:
- mark the right-side relational follower, not the lower cell

### Micro-Theory-alone baseline
- private language: `vertical inheritance slot`
- baseline behavior: confidently mark the two-rows-below cell
- problem: overfits a compact offset rule that was never stress-tested against rotation

### Ledger-applied comparison
- train backward pressure: train outputs do not disambiguate relational following from absolute vertical offset
- test forward projection: relational and offset grammars diverge
- representation certainty: `weakly_supported`
- counterfactual stability: poor; a rotated train pair would separate the grammars instantly
- coordinate-overfit pressure: active
- concept-bloat pressure: active but secondary
- rival grammar pressure: moderate to high
- inevitability label: `unsafe_to_predict`
- safe failure: yes

### Evaluator-only post-check
- Micro-Theory-alone: wrong
- ledger: abstained
- whether ledger caught overfit private language: yes
- whether counterfactual stability was tested: yes
- ceremony note: lower than Mock A because fewer families mattered

## 6. Mock C: Target/Action Split Trap
### Pre-run intuition
- expected Micro-Theory-alone behavior: speak as if clear target plus clear action on separate train slices implies a full prediction on test
- expected ledger behavior: split target certainty from action certainty and block false completion
- expected failure mode: target/action mismatch hidden under one confidence word
- expected safety outcome: partial-safe or safe failure
- ledger success: target acknowledged while action remains unresolved
- ledger failure: full prediction issued anyway

### Mock definition
- mock id: `ue_adv_bidirectional_target_action_001`
- synthetic-only: `true`
- non-claim-safe: `true`

Solver-visible train inputs:
- train A: a unique gap in a frame is repaired by filling
- train B: the same unique target family is indicated again, but output marks the target with a border token instead of filling it because of a subtle subtype cue
- the subtype cue is visible but weakly varied

Solver-visible train outputs:
- train A fills target
- train B marks target

Solver-visible test input:
- unique target is clear, but subtype cue is ambiguous between fill and mark regimes

Evaluator-only intended rule:
- ambiguous subtype means no safe full action prediction

Evaluator-only expected test output:
- no single safe action should be claimed; abstention is correct

### Micro-Theory-alone baseline
- private language: `repair the singular structural defect`
- baseline behavior: confidently fills the unique target because target salience dominates the narrative
- problem: confuses target certainty with action certainty

### Ledger-applied comparison
- target certainty: `forced`
- action certainty: `unresolved`
- representation certainty: `weakly_supported`
- train backward pressure: target family is clear, action law is not uniquely earned
- test forward projection: target parses cleanly, subtype cue does not
- rival grammar pressure: moderate between fill and mark action laws
- rejected-output audit: neither action can eliminate the other cleanly
- inevitability label: `unsafe_to_predict`
- safe failure: yes, with partial-safe statement that target is clear but action is not

### Evaluator-only post-check
- Micro-Theory-alone: overconfident and wrong to issue full fill prediction
- ledger: correct abstention / partial-safe stance
- target certainty: `forced`
- action certainty: `unresolved`
- representation certainty: `weakly_supported`
- whether ledger avoided false full prediction: yes
- ceremony note: worthwhile because the certainty split carried the whole catch

## 7. Optional Mock D: Precedence Ambiguity
Not included. I skipped it to keep the artifact sharp and avoid unnecessary bloat.

## 8. Cross-mock findings
- where ledger succeeded: all three mocks
- where ledger struggled: not in correctness, but in weight and verbosity
- whether bidirectional discipline held: yes
- whether train-output overfitting was caught: yes
- whether live rival grammar was caught: yes
- whether target/action/representation split paid off: strongly yes
- whether rejected-output audit paid off: yes, especially in A and C
- whether counterfactual stability paid off: yes, especially in A and B
- whether safe failure was appropriately used: yes
- whether ceremony risk increased: yes, moderately

## 9. Architecture intuition vs ledger verdict
Mock A:
- intuition: rival grammar should survive
- actual baseline: overconfident mirror projection
- ledger verdict: unsafe-to-predict
- evaluator-only post-check: ledger correct
- calibration: intuition confirmed

Mock B:
- intuition: offset overfit should fail
- actual baseline: confident offset projection
- ledger verdict: unsafe-to-predict
- evaluator-only post-check: ledger correct
- calibration: intuition confirmed and strengthened

Mock C:
- intuition: action ambiguity should survive target clarity
- actual baseline: false full fill prediction
- ledger verdict: partial-safe / unsafe-to-predict
- evaluator-only post-check: ledger correct
- calibration: certainty split proved more central than expected

Architecture model change:
- the ledger now looks less like optional explanation hygiene and more like a necessary anti-overconfidence layer for bidirectional Micro-Theory work

## 10. Ceremony / activation-gate implications
Pressure categories that actually fired:
- rival-grammar pressure
- target-location pressure
- action-type pressure
- counterfactual stability pressure
- coordinate-overfit pressure
- concept-bloat pressure

Mostly unused here:
- absence pressure
- contradiction / precedence pressure
- negative-evidence pressure
- non-change pressure
- distractor-rejection pressure
- color/appearance bait pressure

Would a pre-ledger activation gate reduce ceremony?
- yes

Should activation gating be designed next?
- yes

Would activation gating risk skipping important hidden pressure?
- yes, if designed too aggressively
- it should gate by visible trigger families, not by a minimal-field ideology

## 11. Pressure-category overlap implications
Do these mocks support later merging?
- negative-evidence + non-change: maybe later, but not tested strongly here
- distractor-rejection + color/appearance bait: maybe later, but not central here
- concept-bloat + coordinate-overfit: still separable enough; B benefited from coordinate-overfit as the sharper diagnosis

Would any merge have harmed the adversarial catch?
- merging concept-bloat with coordinate-overfit too early would have made Mock B less precise
- the other candidate merges would not have materially changed these catches because they were mostly inactive

## 12. Scorer-boundary check
Confirmed:
- no numeric score
- no learned scorer behavior
- no benchmark/public-performance implication
- qualitative inevitability only
- safe failure remains available
- no final-answer generation

## 13. What this proves
- the ledger protects against private-language poetry better than Micro-Theory alone
- bidirectional discipline is strong enough for more synthetic stress
- Micro-Theory without ledger remains unsafe
- the ledger now looks ready for an activation-gate design lane
- trace packet schema remains premature

## 14. What this does not prove
- synthetic-only
- small mock count
- no public ARC/Kaggle evidence
- no benchmark evidence
- no implementation evidence
- no schema-readiness proof

## 15. Recommended next safe local follow-up
`DESIGN_MICRO_THEORY_LEDGER_ACTIVATION_GATE_V1`

Reason:
The ledger kept holding, but visible ceremony is now a recurring architectural theme. Activation gating is the best next design move before category collapse or schema work.

## 16. Explicitly forbidden next moves
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

## 17. Final recommendation
Adversarial mocks were useful.

The ledger held.

Micro-Theory direction should continue.

Activation gating is now needed.

Pressure-category collapse remains premature.

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
- activation-gate design reduces ceremony without suppressing important hidden pressure
- later adversarial mocks still catch the same failure families under gated activation
- schema remains blocked unless that lighter-weight design still preserves the protective catches
