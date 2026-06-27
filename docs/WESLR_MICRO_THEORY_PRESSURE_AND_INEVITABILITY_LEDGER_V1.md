# WESLR MICRO-THEORY PRESSURE AND INEVITABILITY LEDGER V1

## Status
Design/report only. Bounded exploratory posture. No implementation, no executable schemas, no runtime solver work, no solver patching, no provider/model calls, no public ARC/Kaggle ingestion, no benchmark/public claims, no learned scorer implementation, no final-answer generation, no `.weslr` writes, and no push.

## 1. Executive definition
A design-only ledger for recording why a temporary micro-language is pressured by train evidence, why its train outputs become inevitable or not, and whether the same train-derived language safely forces a test prediction or requires abstention.

The ledger is not a solver and not a score engine. It is a bounded interpretability artifact for exposing:
- which evidence pressures a micro-theory into existence
- which rival explanations remain live
- whether train outputs are genuinely forced or only loosely supported
- whether a train-derived representation can be applied forward to test input without hidden leakage
- when safe failure is the correct result

## 2. Why this ledger is needed
The Micro-Theory synthetic trace mocks and their review exposed a specific gap: the trace format became meaningfully useful before the pressure and inevitability vocabulary became disciplined enough.

The ledger is needed because:
- pressure sources were still under-specified
- inevitability labels were too vague
- target certainty and action certainty were not separated cleanly
- contradiction precedence was not first-class enough
- rejected outputs were not auditable enough
- evaluator-only packet boundary was not clean enough

Without a ledger, the direction risks two failures:
1. explanation becomes literary instead of comparative
2. schema hardening happens too early around vague qualitative fields

The ledger exists to keep Micro-Theory ambitious internally while remaining bounded, inspectable, and fail-closed.

## 3. Bidirectional Micro-Theory discipline
Micro-Theory should be bidirectional.

It should not only run:
`input -> representation -> micro-theory -> output`

It should also run backward from train outputs:
`train output -> required evidence -> required pressure ledger -> required representation`

### A. Backward-from-train-output discipline
Backward design from train outputs is allowed.

Backward-from-train-output asks:
- Given this train output, what must have been causal?
- Which role, relation, absence, exception, contradiction, or pressure makes this output inevitable?
- Which visible features are incidental?
- Which rival outputs are rejected, and why?
- What evidence would be missing if the output were not justified?

This is not answer leakage because train outputs are part of the visible training evidence. The ledger is allowed to reason backward from train outputs into the minimum explanatory structure needed to justify them.

### B. Forward-to-test-input discipline
Test prediction must run forward from train-derived representation.

Forward-to-test-input asks:
- Does the train-derived language parse the test input?
- Are the same pressures present?
- Is the target forced?
- Is the action forced?
- Do rival grammars remain?
- Is the output unique?
- Is safe failure required?

### Correct boundary
Allowed:
- backward design from train outputs
- forward projection from train-derived representation into test input
- safe failure when train-derived requirements and test-time interpretation do not align

Forbidden:
- never infer from hidden test output
- never use evaluator-only expected test output to build the ledger
- never leak answer keys into solver-visible ledger fields

### Core bidirectional safety rule
If backward-derived requirements and forward test interpretation do not meet, use safe failure.

That means:
- the train-derived language may be well-supported on train
- but the test input may not instantiate that language cleanly enough
- in that case the correct outcome is abstention, not imaginative completion

## 4. Ledger packet structure
Conceptual ledger packet fields:
- `ledger_id`
- `ledger_version`
- `trace_id`
- `synthetic_level_id`
- `source_protocol`
- `synthetic_only`
- `non_claim_safe`
- `cognitive_gym_compatible`
- `solver_visible_fields`
- `evaluator_only_fields`
- `train_backward_pressure`
- `train_forward_consistency`
- `test_forward_projection`
- `target_certainty`
- `action_certainty`
- `representation_certainty`
- `rival_grammar_pressure`
- `absence_pressure`
- `exception_pressure`
- `contradiction_precedence_pressure`
- `negative_evidence_pressure`
- `distractor_rejection_pressure`
- `rejected_output_claims`
- `why_not_other_output`
- `inevitability_summary`
- `safe_failure_summary`
- `boundedness_notes`
- `inspectability_notes`

### Conceptual interpretation of major packet sections
- `solver_visible_fields`: all evidence the solver may legally use
- `evaluator_only_fields`: hidden reference fields explicitly separated from solver reasoning
- `train_backward_pressure`: what the train outputs force the ledger to explain
- `train_forward_consistency`: whether the proposed representation actually reproduces train behavior coherently
- `test_forward_projection`: whether the train-derived language safely projects to test
- `target_certainty`: whether the thing-to-act-on is forced
- `action_certainty`: whether the operation is forced
- `representation_certainty`: whether the temporary language itself is stable enough to trust
- `inevitability_summary`: qualitative forcedness assessment, not a learned score
- `safe_failure_summary`: explicit failure trigger rather than vague uncertainty language

## 5. Pressure categories
The ledger should make pressure categories explicit.

### 5.1 Role stability pressure
- meaning: pressure to explain whether the same functional role persists across train pairs
- evidence source: repeated role behavior under changed appearance
- what increases pressure: role survives color/shape changes while output target remains stable
- what weakens pressure: target identity changes without stable role explanation
- safe-failure trigger: role assignments remain unstable across train pairs
- placeholder example: `synthetic target changes color but remains opening_side_target`

### 5.2 Relation stability pressure
- meaning: pressure to explain stable relational structure rather than raw appearance
- evidence source: containment, adjacency, symmetry, pairing, ordering
- what increases pressure: same relation explains all transformed objects
- what weakens pressure: relation changes per example or needs ad hoc exceptions
- safe-failure trigger: no stable relation family survives all train pairs
- placeholder example: `selected object is always nearest the opening`

### 5.3 Absence pressure
- meaning: pressure caused by something expected but not present
- evidence source: broken completion, missing counterpart, empty slot, forbidden gap
- what increases pressure: output acts on absence repeatedly across train pairs
- what weakens pressure: absence claim depends on speculative missing structure without support
- safe-failure trigger: multiple absence hypotheses remain equally live
- placeholder example: `three corners imply missing fourth corner`

### 5.4 Exception pressure
- meaning: pressure caused by one element violating a broader pattern
- evidence source: lone violator, protected object, anomaly object, non-member exception
- what increases pressure: output consistently responds to the violator or rejects it explicitly
- what weakens pressure: exception status is assigned only to save a weak grammar
- safe-failure trigger: exception ownership remains ambiguous
- placeholder example: `bright distractor remains untouched while frame completion matters`

### 5.5 Contradiction / precedence pressure
- meaning: pressure created when two real partial regularities conflict and one must outrank the other
- evidence source: local completion vs protection rule, symmetry vs containment, copy rule vs forbidden action
- what increases pressure: train evidence repeatedly shows one rule vetoing another
- what weakens pressure: precedence is asserted without repeated evidence
- safe-failure trigger: precedence claim remains unproven
- placeholder example: `local symmetry suggests fill, protected container vetoes fill`

### 5.6 Negative evidence pressure
- meaning: pressure from what did not happen but could have happened under a weaker grammar
- evidence source: unchanged distractors, preserved regions, absent transformations
- what increases pressure: candidate grammar must explain non-change explicitly
- what weakens pressure: grammar ignores preserved structure
- safe-failure trigger: non-change explanation missing for a critical region
- placeholder example: `distractor remains unchanged despite visual salience`

### 5.7 Distractor rejection pressure
- meaning: pressure to justify why tempting but wrong salience cues were not causal
- evidence source: vivid colors, isolated objects, symmetric bait, majority-color lure
- what increases pressure: train pairs repeatedly show the same distractor class ignored
- what weakens pressure: distractor rejection becomes a generic excuse without evidence
- safe-failure trigger: distractor cannot be rejected without hurting train coverage
- placeholder example: `bright external object is never transformed`

### 5.8 Non-change pressure
- meaning: pressure to explain why certain structures remain untouched
- evidence source: stable regions, protected interiors, preserved peers
- what increases pressure: non-change pattern aligns with causal boundary
- what weakens pressure: unchanged structure is left unexplained
- safe-failure trigger: grammar predicts too much change or cannot explain stability
- placeholder example: `protected area remains unchanged in all train pairs`

### 5.9 Output-shape pressure
- meaning: pressure to explain the structural form of the output rather than only its local targets
- evidence source: shape completion, count of added cells, symmetry of final output
- what increases pressure: same output form appears across train examples
- what weakens pressure: output form changes arbitrarily across examples
- safe-failure trigger: multiple incompatible output structures remain plausible
- placeholder example: `one corner is always completed, never multiple cells`

### 5.10 Target-location pressure
- meaning: pressure to force which object, region, absence, or role is the target
- evidence source: repeated target selection cues across train pairs
- what increases pressure: exactly one target satisfies the train-derived constraints
- what weakens pressure: multiple targets fit equally well
- safe-failure trigger: target remains ambiguous
- placeholder example: `only one gap qualifies as repair_target`

### 5.11 Action-type pressure
- meaning: pressure to force what action is taken once the target is known
- evidence source: fill vs mark vs recolor vs copy vs preserve distinction
- what increases pressure: train outputs consistently apply the same operation class
- what weakens pressure: multiple action types fit train examples equally well
- safe-failure trigger: target clear but action underdetermined
- placeholder example: `missing corner is clear, but fill versus mark remains unresolved`

### 5.12 Color / appearance bait pressure
- meaning: pressure caused by visible features that look causal but may be incidental
- evidence source: color inversion, shape swap, coordinate shift under stable role
- what increases pressure: appearance changes while role logic persists
- what weakens pressure: appearance actually tracks the transformation causally
- safe-failure trigger: cannot separate appearance bait from true causality
- placeholder example: `red target in train A becomes blue target in train B but keeps role`

### 5.13 Coordinate-overfit pressure
- meaning: pressure against grammars that memorize absolute location without lawful reason
- evidence source: train pairs with shifted geometry but stable relations
- what increases pressure: relation survives coordinate movement
- what weakens pressure: fixed coordinates are actually part of the lawful task
- safe-failure trigger: candidate grammar depends on brittle coordinates
- placeholder example: `target follows opening after container shifts`

### 5.14 Concept-bloat pressure
- meaning: pressure against grammars that invent too many concepts to explain simple evidence
- evidence source: excessive vocabulary, per-example roles, ad hoc exceptions
- what increases pressure: many unique concepts needed for few examples
- what weakens pressure: compact concept reuse across train pairs
- safe-failure trigger: representation becomes unbounded or uninspectable
- placeholder example: `new role name required for each train pair`

### 5.15 Rival-grammar pressure
- meaning: pressure caused by multiple compact grammars surviving simultaneously
- evidence source: two or more train-consistent explanations with different test predictions
- what increases pressure: rivals have similar train coverage and compression
- what weakens pressure: one train pair clearly disambiguates the rivals
- safe-failure trigger: rival outputs remain live at test time
- placeholder example: `mirror completion and count progression both survive`

### 5.16 Counterfactual stability pressure
- meaning: pressure to verify that the representation remains lawful under small, meaningful changes
- evidence source: role-preserving color swap, moved gap, removed distractor, outside-container variant
- what increases pressure: candidate remains stable under relevant counterfactuals
- what weakens pressure: candidate collapses under small lawful perturbations
- safe-failure trigger: no stable counterfactual profile exists
- placeholder example: `if gap moved outside container, veto disappears`

## 6. Target certainty vs action certainty
This must be first-class.

### Target certainty
`target_certainty` means whether the object, location, absence, relation, or role to act on is forced.

### Action certainty
`action_certainty` means whether the operation to perform on that target is forced.

### Representation certainty
`representation_certainty` means whether the temporary language itself is stable and inspectable enough to trust.

### Canonical cases
1. target clear, action unclear
   - outcome: safe failure or partial-safe claim
   - example: missing corner is clearly the target, but whether to fill or mark remains unresolved

2. action clear, target unclear
   - outcome: unsafe prediction
   - example: operation is definitely recolor, but two candidate targets remain equally live

3. target and action clear
   - outcome: possible prediction
   - example: opening-side target is unique and recolor action is stable across train

4. representation unstable
   - outcome: safe failure
   - example: role system changes between train pairs and no compact language survives

### Why this separation matters
The previous trace mocks showed that one can know more about where the transformation belongs than about what exact transformation it is. The ledger must preserve that asymmetry rather than collapse it into a single confidence label.

## 7. Contradiction / precedence ledger
Rule conflict must be first-class.

Suggested fields:
- `conflicting_pressures`
- `lower_order_rule`
- `higher_order_rule`
- `precedence_claim`
- `evidence_for_precedence`
- `counterfactual_boundary`
- `safe_failure_if_precedence_unproven`

### Conceptual example
- local symmetry suggests fill
- protected container vetoes fill
- train evidence shows protection outranks local completion
- if the same gap were outside the protected region, symmetry fill becomes viable again

### Why precedence must be earned
Precedence cannot be asserted just because it sounds elegant. It must be supported by train evidence. If the ledger cannot justify why one pressure outranks another, then contradiction resolution is not proven and safe failure should remain available.

## 8. Rejected outputs and why-not ledger
Rejected outputs must become auditable.

Suggested fields:
- `rejected_output_claims`
- `why_not_other_output`
- `rival_output_claim`
- `rejection_reason`
- `evidence_against`
- `remaining_uncertainty`
- `unsafe_if_not_rejected`

### Purpose
This section prevents the ledger from sounding persuasive while hiding what alternative outputs were actually plausible.

### Example placeholder
- rival output claim: `fill both symmetric gaps`
- rejection reason: `train evidence only ever fills one role-selected gap`
- evidence against: `non-change pressure on the second gap remains unexplained`
- remaining uncertainty: `low`
- unsafe if not rejected: `yes, because two outputs would remain live`

## 9. Inevitability labels
These remain conceptual-only labels.
They are not learned scores, not benchmark measures, and not official performance claims.

Allowed labels:
- `forced`
- `strongly_supported`
- `weakly_supported`
- `unresolved`
- `unsafe_to_predict`

### Meanings
- `forced`: train evidence and forward test projection leave one bounded explanation and one bounded output path
- `strongly_supported`: one explanation is clearly better, but minor residual ambiguity remains
- `weakly_supported`: one explanation is plausible, but alternative explanations remain meaningful
- `unresolved`: train evidence does not sufficiently disambiguate the representation or output path
- `unsafe_to_predict`: prediction would exceed what the train-derived ledger can justify

### Non-goal
The ledger must not become a learned inevitability scorer in this design artifact.

## 10. Safe failure conditions
Safe failure triggers should include:
- rival grammars disagree
- target unclear
- action unclear
- target/action mismatch
- representation unstable
- contradiction precedence unproven
- rejected outputs not sufficiently rejected
- pressure evidence too weak
- evaluator-only leak risk
- public-data boundary risk
- concept bloat
- uninspectable private language

### Safe failure principle
Safe failure is not a minor fallback. It is the correct output whenever the train-derived ledger and forward test projection do not jointly force a bounded prediction.

## 11. Evaluator-only boundary
The ledger must preserve a conceptual split.

### Solver-visible
- train inputs
- train outputs
- test inputs
- train-derived ledger
- forward test projection

### Evaluator-only
- expected test output
- scoring result
- hidden validation labels
- post-hoc mismatch analysis

### Boundary rule
The ledger must not allow evaluator-only information to influence solver-visible pressure.

That means:
- no hidden test output in pressure categories
- no judge labels in solver-visible inevitability
- no post-hoc correctness signal inside the forward projection packet

## 12. Cognitive Gym compatibility
The ledger remains compatible with a future shared Cognitive Gym-style protocol by preserving:
- protocol-like fields
- synthetic level references
- solver-visible / evaluator-only split
- boundary flags
- auditable pressure categories
- explicit safe failure
- comparability across future agents / solvers
- no private mythology
- no public-performance claims

The ledger is meant to strengthen migratability, not to create a private symbolic religion around UNKNOWN ENGINE.

## 13. Example ledger skeleton
Placeholder-only illustrative skeleton:

```json
{
  "ledger_id": "micro_pressure_ledger_mock_0001",
  "ledger_version": "MicroTheoryPressureInevitabilityLedgerV1",
  "trace_id": "micro_trace_mock_role_color_inversion_001",
  "synthetic_level_id": "ue_mock_level_ledger_001",
  "source_protocol": "cognitive_gym_style_mock_v1",
  "synthetic_only": true,
  "non_claim_safe": true,
  "cognitive_gym_compatible": true,
  "solver_visible_fields": {
    "train_inputs": ["placeholder_train_input_a", "placeholder_train_input_b"],
    "train_outputs": ["placeholder_train_output_a", "placeholder_train_output_b"],
    "test_inputs": ["placeholder_test_input"]
  },
  "evaluator_only_fields": {
    "expected_test_output": "evaluator_only_hidden",
    "score_result": null,
    "hidden_validation_labels": []
  },
  "train_backward_pressure": [
    {
      "pressure_category": "role_stability_pressure",
      "evidence_source": "target changes color while role stays stable",
      "required_representation": "role_graph",
      "required_rejection": "color_first_targeting"
    }
  ],
  "train_forward_consistency": {
    "representation_replays_train": true,
    "rival_grammars_remaining": ["position_first_targeting"]
  },
  "test_forward_projection": {
    "test_parses_under_train_language": true,
    "target_forced": true,
    "action_forced": true,
    "unique_output_path": true
  },
  "target_certainty": "forced",
  "action_certainty": "strongly_supported",
  "representation_certainty": "strongly_supported",
  "rival_grammar_pressure": [
    {
      "rival": "position_first_targeting",
      "status": "weakened",
      "reason": "fails moved-opening counterfactual"
    }
  ],
  "absence_pressure": [],
  "exception_pressure": [],
  "contradiction_precedence_pressure": [],
  "negative_evidence_pressure": [
    {
      "unchanged_region": "external_distractor",
      "why_it_matters": "explains non-change"
    }
  ],
  "distractor_rejection_pressure": [
    {
      "distractor": "same_color_external_object",
      "rejection_reason": "outside role boundary"
    }
  ],
  "rejected_output_claims": [
    {
      "rival_output_claim": "recolor leftmost object",
      "evidence_against": "opening relation explains train outputs better"
    }
  ],
  "why_not_other_output": [
    {
      "candidate": "recolor external distractor",
      "why_not": "non-change pressure remains unexplained"
    }
  ],
  "inevitability_summary": {
    "train_label": "strongly_supported",
    "test_projection_label": "strongly_supported",
    "overall_label": "strongly_supported"
  },
  "safe_failure_summary": {
    "required": false,
    "reason": null
  },
  "boundedness_notes": "mock ledger only; no executable behavior",
  "inspectability_notes": "all rejections and pressure claims are explicit"
}
```

This skeleton uses fake synthetic IDs only. It contains no public ARC/Kaggle content and no benchmark examples.

## 14. What is explicitly not implemented
This artifact does not implement:
- runtime solver
- executable ledger
- executable schema
- learned scorer
- final-answer generator
- ChatResponder integration
- provider/model calls
- public ARC/Kaggle evaluation
- benchmark claim
- public claim
- behavior-pack promotion

## 15. Recommended next safe follow-up
Recommended next safe follow-up:
`REVIEW_MICRO_THEORY_PRESSURE_AND_INEVITABILITY_LEDGER_V1`

Reason:
The ledger is conceptually dense and introduces new bidirectional discipline, certainty separation, contradiction precedence, and solver-visible / evaluator-only boundary rules. Review is the safest next lane before manual application or packet schema design.

## 16. Final note
The ledger should make Micro-Theory stricter, not looser. Its job is not to beautify explanations. Its job is to force explicit evidence, explicit rejection, explicit certainty boundaries, and explicit abstention when the train-derived language does not safely project forward.
