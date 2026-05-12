# WESLR Proof-Step Candidate Design V1

## 1. Title

WESLR Proof-Step Candidate Design V1

## 2. Status

- design_only
- proof_step_candidate
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## 3. Purpose

Design a safe candidate layer between `ReasoningContextBindingCandidate` and a future `ProofStep`.

This phase defines reviewable structure and boundaries only. It does not implement proof-step behavior, generate proof steps, select answers, claim truth, alter scoring, or connect to runtime behavior.

## 4. Evidence

Redacted checkpoint metrics only:

- context bindings: 14/14
- premise context unknown: 0
- bindings with all required refs: 14/14
- proof-step-candidate-ready bindings: 10/14
- anti-gaming safe: yes
- legibility safe: yes
- official score claimed: no

These metrics indicate that context-binding quality is now strong enough to design the next candidate layer, while still requiring operator review before any schema or behavior phase.

## 5. Core rule

`ProofStepCandidate` is not proof.

`ProofStepCandidate` is not answer selection.

`ProofStepCandidate` is not a truth claim.

It is only a structured hypothesis that a proof step may be possible.

A candidate is not proof, a candidate is not answer selection, and a candidate is not a truth claim. It must remain explicitly tentative until a later approved phase defines proof-step schema, diagnostics, promotion rules, and review gates.

## 6. Proposed object: `ProofStepCandidate`

Suggested fields:

- `candidate_id`
- `source_context_binding_ids`
- `source_premise_proposition_ids`
- `source_choice_proposition_ids`
- `candidate_type`
- `expected_reasoning_relation`
- `inference_pattern_hint`
- `support_status`
- `confidence`
- `unsupported_gaps`
- `human_explanation`
- `legibility`
- `anti_gaming`

Field intent:

- `candidate_id`: local diagnostic identifier only; not an authority source.
- `source_context_binding_ids`: references to prior context-binding candidates that provide role/target context.
- `source_premise_proposition_ids`: premise proposition references already surfaced by prior layers.
- `source_choice_proposition_ids`: choice proposition references already surfaced by prior layers.
- `candidate_type`: one of the allowed candidate types below.
- `expected_reasoning_relation`: carried from context binding or a later approved schema, never inferred from answer keys.
- `inference_pattern_hint`: weak hint only; not symbolic authority.
- `support_status`: conservative status from the allowed support-status set.
- `confidence`: diagnostic confidence only; not score, truth, or answer-selection confidence.
- `unsupported_gaps`: visible list of missing support, ambiguity, or unresolved context.
- `human_explanation`: short human-readable reason the candidate exists.
- `legibility`: evidence that the candidate can be inspected and taught.
- `anti_gaming`: evidence that the candidate did not rely on benchmark-specific shortcuts.

## 7. Allowed candidate types

- `support_step_candidate`
- `contradiction_step_candidate`
- `counterexample_step_candidate`
- `rule_application_candidate`
- `invalidity_test_candidate`
- `template_completion_candidate`
- `unsupported_step_candidate`

## 8. Allowed support statuses

- `candidate_only`
- `insufficient_support`
- `ambiguous`
- `unsupported`
- `unknown`

No support status may mean proven, true, selected, correct, official, or solved.

## 9. Connection to existing spine

Planned spine:

`ReasoningContextBindingCandidate → ProofStepCandidate → future ProofStep → future TeachingExplanation`

Relationship to existing candidate layers:

- `SimpleInferencePatternCandidate` may provide weak supporting signal.
- `PropositionMergeCandidate` may provide deduplicated proposition sources.
- `ReasoningContextBindingCandidate` is the main source of role/target context.
- `ProofStepCandidate` must not bypass context binding.

A `ProofStepCandidate` may only be proposed after source context has been made explicit by `ReasoningContextBindingCandidate`. If required context is absent, ambiguous, or unsupported, the proof-step candidate must preserve the gap instead of silently filling it.

## 10. Safety boundaries

- no answer keys
- no item-ID authority
- no answer selection
- no official score claim
- no benchmark-specific tuning
- no raw benchmark storage by default
- no hidden symbolic authority
- unsupported gaps visible
- Unsupported gaps must remain visible.
- low-confidence candidates not promoted silently
- no runtime integration in this phase

Additional boundary notes:

- Candidate IDs, item IDs, fixture names, or benchmark positions must never be used as correctness signals.
- `ProofStepCandidate` must not select an answer, rank choices, or imply correctness.
- Any later promotion from candidate to proof must require separately approved schema and behavior gates.

## 11. Non-goals

- no implementation in this phase
- no proof generation
- no solver changes
- no MCQ adapter changes
- no runtime integration
- no teaching explanation generation
- no scoring

This document does not change parser, normalizer, teaching spine behavior, solver, MCQ adapter, runtime, interpretation, response contracts, or scoring.

## 12. Future phases

A. design doc — current

B. schema only

C. helper diagnostics on synthetic fixtures

D. proof-step candidate quality diagnostic

E. only later actual `ProofStep` schema/behavior

F. teaching explanation later

G. runtime integration audit much later

H. no official score claim

## 13. Operator decisions

- `APPROVE_PROOF_STEP_CANDIDATE_SCHEMA_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`
