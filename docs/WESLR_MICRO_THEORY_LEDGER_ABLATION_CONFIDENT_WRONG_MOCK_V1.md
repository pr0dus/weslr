# WESLR MICRO-THEORY LEDGER ABLATION CONFIDENT WRONG MOCK V1

## Status
Manual design/report only. Local-only. Synthetic-only diagnostic. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, no push preparation, and no push.

## 1. Executive summary
`ledger_ablation_success_caught_confident_wrong`

The ledger caught a confident-wrong Micro-Theory failure on this synthetic mock.

Micro-Theory alone produced an elegant, compressed, confident test prediction from a private language centered on visible stripe completion. The ledger downgraded that confidence to `unsafe_to_predict` because rival grammar pressure remained live, rejected-output audit was incomplete, counterfactual stability was weak, and representation certainty was overstated.

This is the strongest evidence so far that the ledger does real protective work rather than merely decorating explanation after the fact.

## 2. Method
This diagnostic is manual design-only.

Method:
- construct one synthetic-only mock designed to tempt a neat but overconfident private language
- run a Micro-Theory-alone baseline first
- run a ledger-applied comparison second
- reveal evaluator-only intended rule and expected output only in the final post-check

Boundaries:
- no executable schema
- no solver/runtime/provider/model calls
- no public ARC/Kaggle data
- no hidden test output leakage into solver-visible sections
- evaluator-only expected output appears only in the post-check section

The goal is adversarial: make Micro-Theory look good on train, then test whether the ledger can stop a clean-looking but unsafe test projection.

## 3. Pre-run intuition record
Expected Micro-Theory-alone behavior:
- it will prefer a compact visible rule such as `extend the stripe toward the nearest open side` because that rule compresses both train examples cleanly
- it will speak in confident representational language because the train pairs look highly regular

Expected ledger behavior:
- it should notice that a second grammar remains alive: `project the stripe toward the side indicated by the anchor marker rather than the nearest open side`
- it should detect missing rival rejection and weak counterfactual stability
- it should downgrade inevitability and choose safe failure

Expected failure mode:
- train-output overfit to a visually elegant but under-justified orientation rule
- false inevitability caused by under-testing rival grammar survival

Expected safety outcome:
- Micro-Theory alone: confident wrong prediction
- ledger-applied: abstain or unsafe-to-predict

Why this mock should be useful:
- it tests whether the ledger can catch a failure that looks elegant rather than obviously sloppy
- it targets exactly the risk that private-language Micro-Theory becomes persuasive poetry without enough pressure accounting

## 4. Synthetic mock definition
- mock id: `ue_synth_confident_wrong_ablation_001`
- synthetic-only: `true`
- non-claim-safe: `true`

### Solver-visible train inputs
Train A:
- a 5x5 toy scene
- one horizontal stripe of two filled cells sits inside a frame
- a small anchor marker sits above the stripe on the left side
- one empty cell exists to the right of the stripe and one empty cell exists to the left

Train B:
- same stripe pattern shifted
- anchor marker again sits above the stripe on the left side
- both left and right extensions are visually possible, but output extends left

### Solver-visible train outputs
Train A output:
- stripe extends left by one cell

Train B output:
- stripe extends left by one cell

### Solver-visible test input
Test:
- same frame family
- same stripe family
- anchor marker now sits above the stripe on the right side
- both left and right one-cell extensions are visually possible

### Evaluator-only intended rule
- extend the stripe toward the side indicated by the anchor marker, not toward a globally fixed left side and not toward the nearest open boundary alone

### Evaluator-only expected test output
- stripe extends right by one cell

### Boundary notes
- solver-visible sections may use only the train inputs/outputs and test input
- evaluator-only intended rule and expected output are withheld until section 7
- this is owner-designed synthetic material, not benchmark evidence

## 5. Micro-Theory-alone baseline
Invented private language:
- `dominant continuation axis`
- `stripe lineage`
- `privileged completion side`
- `frame-local extension`

Roles:
- stripe body
- anchor marker
- candidate extension cell left
- candidate extension cell right

Relations:
- stripe has a stable horizontal continuation axis
- anchor sits above stripe but is treated as contextual decoration rather than directional authority
- left extension is interpreted as the canonical continuation side because it is the side used in train

Assumed transformation:
- extend the stripe by one cell on its privileged continuation side

Train explanation:
- both train outputs are elegantly explained by a simple “extend leftward” continuation theory
- anchor is absorbed as harmless scene ornament because train outputs do not force an alternative reading if one ignores anchor causality

Test projection:
- the same stripe lineage is projected to test
- left extension is predicted again

Predicted output claim:
- extend the test stripe left by one cell

Confidence language used by Micro-Theory alone:
- the continuation rule is compact, stable across train, and visually clean
- no further ambiguity appears operationally relevant
- prediction appears strongly justified

What it fails to inspect:
- whether anchor marker is actually causal rather than decorative
- whether a rival grammar survives train equally well
- whether the train evidence ever disambiguated fixed-left continuation from anchor-indicated continuation
- whether counterfactual movement of the anchor would change the prediction lawfully

Why this prediction is overconfident:
- it mistakes train consistency for causal uniqueness
- it compresses away the one feature that might actually govern orientation
- it never earns rejection of the anchor-directed rival output

## 6. Ledger-applied comparison
### Train backward pressure
- train outputs require explaining why the extension always occurs on the same side in train
- causal candidates:
  - grammar A: fixed-left continuation rule
  - grammar B: anchor-directed continuation rule
- visible feature at risk of being incorrectly treated as incidental:
  - anchor side placement
- train evidence does not show anchor moving sides, so anchor-causality is not ruled out

### Test forward projection
- the train-derived representation parses test only ambiguously
- both fixed-left and anchor-directed grammars remain live at test

### Target certainty
- `strongly_supported`
- the target object family is clear: the stripe should be extended by one cell

### Action certainty
- `strongly_supported`
- the operation class is clear: add one continuation cell

### Representation certainty
- `weakly_supported`
- the representation for *which side* governs extension is not uniquely earned

### Rival grammar pressure
- high
- the anchor-directed grammar survives train perfectly and diverges on test exactly where it matters

### Rejected-output audit
- rejected output claim attempted by Micro-Theory alone:
  - extend left because left was the stable continuation side in train
- rejection reason against that confident claim:
  - train never disambiguated fixed-left from anchor-directed continuation
- evidence against confident-left inevitability:
  - anchor side never varied in train, so its directional role was never tested away
- remaining uncertainty:
  - high at the orientation-selection level
- unsafe if not rejected:
  - yes; confident-left prediction may be wrong despite clean train compression

### Why-not-other-output audit
- why not extend right?
  - because fixed-left grammar claims left is canonical
- why this audit fails:
  - it cannot show why anchor-right in test is non-causal using train-earned evidence
- unresolved rival output:
  - right extension remains live under anchor-directed grammar

### Counterfactual stability
- weak
- if anchor switched sides in a hypothetical train pair, fixed-left and anchor-directed grammars would diverge sharply
- no such disambiguating pair exists in train, so the baseline grammar lacks counterfactual robustness

### Pressure categories activated
- rival-grammar pressure
- relation stability pressure
- target-location pressure
- action-type pressure
- counterfactual stability pressure
- concept-bloat pressure
- coordinate-overfit pressure

### Inevitability label
- `unsafe_to_predict`

### Safe failure decision
- safe failure
- why:
  - target/action are clear, but representation certainty is not
  - rival grammar remains live
  - rejected-output audit is incomplete
  - counterfactual stability is too weak to justify confident side selection

## 7. Evaluator-only post-check
Evaluator-only expected test output:
- extend right by one cell

Comparison:
- Micro-Theory-alone prediction: extend left
- evaluator-only expected output: extend right
- ledger verdict: `unsafe_to_predict`

Whether the ledger prevented or downgraded the wrong prediction:
- yes
- it prevented a confident wrong side-selection claim by refusing to treat the side rule as inevitable

Whether the ledger caught the right failure mode:
- yes
- the core failure mode was unresolved rival grammar plus weak counterfactual stability around anchor causality

Whether the ledger merely got lucky:
- no
- the abstention was not a generic panic move; it was tied to specific structural deficits:
  - unearned rejection of a rival grammar
  - overstated representation certainty
  - train-output overfit
  - weak side-disambiguation counterfactuals

## 8. What the ablation proves
- the ledger did real work
- the ledger caught confident wrongness rather than merely narrating uncertainty afterward
- the ledger exposed uncertainty at the representation layer before evaluator-only reveal
- Micro-Theory alone is unsafe on this mock
- the ledger protects against private-language poetry by forcing causal pressure accounting and rival-output rejection

## 9. What the ablation does not prove
- one mock only
- synthetic-only evidence
- not benchmark evidence
- not public ARC/Kaggle evidence
- not solver implementation evidence
- not schema-readiness evidence
- not proof that every ledger category is necessary

## 10. Ceremony and complexity check
Necessary ledger fields here:
- train backward pressure
- test forward projection
- representation certainty
- rival grammar pressure
- rejected-output audit
- why-not-other-output audit
- counterfactual stability
- inevitability label
- safe failure decision

Unnecessary or low-yield fields here:
- absence pressure was not needed
- contradiction / precedence pressure was not needed
- non-change pressure was not doing primary work

Would activation gating have reduced ceremony?
- yes
- this mock benefited from using only activated fields rather than the full ledger surface

Did overlap categories matter?
- not much in this ablation
- the key issue was rival-grammar survival, not category overlap

Would collapsed categories have changed the result?
- probably no
- this diagnostic succeeded because of certainty/rival/counterfactual checks, not because of fine-grained overlap categories

## 11. Scorer-boundary check
Confirmed:
- no numeric score
- no learned scorer behavior
- no benchmark/public-performance implication
- qualitative inevitability only
- safe failure remains available

## 12. Recommended next safe local follow-up
`RUN_MICRO_THEORY_ADVERSARIAL_BIDIRECTIONAL_MOCKS_V1`

Reason:
This ablation suggests the ledger has real protective value, and the next risk is whether bidirectional pressure remains robust under a broader adversarial family rather than only one confident-wrong case.

## 13. Explicitly forbidden next moves
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

## 14. Final recommendation
The ledger ablation was successful.

Micro-Theory direction should continue.

The ledger has now shown real protective value against at least one confident-wrong private-language failure.

More adversarial mocks are needed.

Activation gating is a later optimization, not the immediate next need.

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
- more adversarial bidirectional mocks show the same protective pattern
- the ledger repeatedly catches confident-wrong projections before evaluator-only reveal
- activation gating can then be designed from evidence rather than taste
- schema remains blocked until adversarial diagnostics keep coming out clearly positive
