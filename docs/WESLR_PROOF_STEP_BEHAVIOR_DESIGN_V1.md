# WESLR ProofStep Behavior Design V1

## 1. Title

WESLR ProofStep Behavior Design V1

## 2. Status

- design_only
- proof_step_behavior
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## 3. Purpose

Design the rules for converting safe `ProofStepCandidate` records into future `ProofStep` records.

This is a design-only phase. It does not implement proof generation, create proof chains, generate teaching explanations, select answers, claim truth, alter scoring, or connect to runtime behavior.

## 4. Evidence

Redacted checkpoint metrics only:

- context bindings: 14/14
- proof-step candidates: 14
- proof-step-candidate-ready: 14/14
- question target unknown reduced: 11 → 3
- anti-gaming safe: yes
- legibility safe: yes
- no answer selection
- no truth claims
- no official score

These metrics indicate that proof-step candidates are structurally ready on the synthetic curriculum, while still requiring operator review before any behavior or schema execution phase.

## 5. Core distinction

`ProofStepCandidate` = possible proof move.

`ProofStep` = accepted structured reasoning step.

A future `ProofStep` is stronger than a `ProofStepCandidate`, but it remains bounded:

- `ProofStep` still must not select answers.
- `ProofStep` still must not claim benchmark truth.
- `ProofStep` must preserve confidence and unsupported gaps.
- `ProofStep` must remain inspectable and reviewable.

## 6. Proposed `ProofStep` behavior rules

A future `ProofStep` may be created only when all of the following are true:

- source candidate exists
- source context binding exists
- premise and choice proposition refs exist
- expected reasoning relation is known
- inference pattern hint is known
- unsupported gaps are acceptable and visible
- anti-gaming is safe
- legibility is safe

If any required source or safety condition is absent, the future behavior must produce an `ambiguous` or `unsupported` status rather than silently promoting the step.

## 7. Allowed proof-step statuses

- `supported`
- `contradicted`
- `counterexample_supported`
- `rule_application_supported`
- `template_completed`
- `ambiguous`
- `unsupported`

No proof-step status may mean selected, correct, official, solved, or benchmark-true.

## 8. Required fields for future `ProofStep`

- `proof_step_id`
- `source_candidate_id`
- `source_context_binding_ids`
- `source_premise_proposition_ids`
- `source_choice_proposition_ids`
- `reasoning_relation`
- `inference_pattern`
- `support_status`
- `confidence`
- `warrant`
- `unsupported_gaps`
- `human_explanation`
- `legibility`
- `anti_gaming`

Field intent:

- `proof_step_id`: local diagnostic identifier only; not an authority source.
- `source_candidate_id`: reference to the accepted source `ProofStepCandidate`.
- `source_context_binding_ids`: explicit context sources that anchor the proof step.
- `source_premise_proposition_ids`: premise proposition references used by the step.
- `source_choice_proposition_ids`: choice proposition references used by the step.
- `reasoning_relation`: known relation being evaluated, not inferred from answer keys.
- `inference_pattern`: known reasoning pattern, not hidden symbolic authority.
- `support_status`: conservative status from the allowed proof-step status set.
- `confidence`: diagnostic confidence only; not truth, score, or answer-selection confidence.
- `warrant`: human-inspectable reason the support status was assigned.
- `unsupported_gaps`: visible missing support, ambiguity, or unresolved context.
- `human_explanation`: concise review-facing explanation, not a teaching explanation.
- `legibility`: evidence the step is inspectable and does not hide assumptions.
- `anti_gaming`: evidence the step avoided benchmark-specific shortcuts.

## 9. Safety boundaries

- no answer keys
- no item-ID authority
- no answer selection
- no official score claim
- no benchmark-specific tuning
- no raw benchmark storage by default
- no hidden symbolic authority
- unsupported gaps visible
- Unsupported gaps must remain visible.
- low-confidence steps must not be silently promoted

Additional boundary notes:

- Candidate IDs, item IDs, fixture names, or benchmark positions must never be used as correctness signals.
- A `ProofStep` must not select an answer, rank choices, or imply correctness.
- A `ProofStep` must not claim benchmark truth or official benchmark status.
- Any later execution requires separately approved schema, diagnostics, and behavior gates.

## 10. Non-goals

- no implementation in this phase
- no proof generation
- no proof-chain generation
- no teaching explanation generation
- no solver changes
- no MCQ adapter changes
- no runtime integration
- no scoring

This document does not change parser, normalizer, teaching spine behavior, solver, MCQ adapter, runtime, interpretation, response contracts, or scoring.

## 11. Future phases

A. design doc — current

B. `ProofStep` schema review / existing schema alignment

C. helper diagnostics on synthetic fixtures

D. proof-step quality diagnostic

E. teaching explanation design

F. runtime integration audit much later

G. no official score claim

## 12. Operator decisions

- `APPROVE_PROOF_STEP_SCHEMA_ALIGNMENT_ONLY`
- `APPROVE_PROOF_STEP_HELPERS_DIAGNOSTICS_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`
