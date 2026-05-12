# WESLR Teaching Explanation Design V1

## Status

- design_only
- teaching_explanation
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose

Design how future `TeachingExplanation` records should explain safe `ProofStep` records to humans.

This phase defines the target explanation contract only. It does not implement teaching explanation generation, does not change runtime behavior, and does not add solver authority.

## Evidence

Redacted current evidence supports design-only work:

- synthetic proof steps exist
- actual fixture-pipeline conditional mappings: 5
- ad-hoc/test-only mappings: 0
- answer selection: no
- truth claims: no
- official score: no
- anti-gaming safe
- legibility safe

## Core Distinction

- `ProofStep` is a structured reasoning step.
- `TeachingExplanation` is a human-facing view over proof artifacts.
- `TeachingExplanation` must not create new reasoning authority.
- `TeachingExplanation` must not select answers.
- `TeachingExplanation` must not claim benchmark truth.
- Unsupported gaps remain visible.

A teaching explanation may describe what a proof artifact already says. It must not upgrade a candidate, infer a hidden answer, launder confidence, or make claims that the source `ProofStep` does not support.

## Proposed Explanation Modes

- beginner
- technical
- academic
- spock
- operator_audit

Mode intent:

- beginner: plain-language explanation with minimal formalism.
- technical: precise structural explanation with explicit pattern names.
- academic: formal terminology and validity/fallacy framing, still bounded by source evidence.
- spock: concise, highly logical explanation style; no extra authority.
- operator_audit: terse provenance, support status, safety, and unsupported-gap review.

## Proposed Explanation Structure

Future `TeachingExplanation` records should be able to expose:

- explanation_id
- source_proof_step_ids
- source_context_binding_ids
- teaching_mode
- support_status
- core_claim
- why_it_follows_or_fails
- pattern_name
- fallacy_name
- counterexample_note
- unsupported_gaps
- confidence
- human_explanation
- anti_gaming
- legibility

The existing schema already has `explanation_id`, `source_proof_step_ids`, `support_status`, `common_fallacy`, `learner_level`, `teaching_mode`, `step_by_step_explanation`, `uncertainty_note`, `human_explanation`, `unsupported_gaps`, `anti_gaming`, and `legibility`. Later schema alignment should decide whether to add explicit `source_context_binding_ids`, `core_claim`, `why_it_follows_or_fails`, `pattern_name`, `fallacy_name`, `counterexample_note`, and `confidence`, or map them into existing fields.

## Teaching Rules

- For modus ponens: explain rule application structurally: given a conditional P -> Q and an asserted P, Q is the structurally supported consequent.
- For modus tollens: explain contrapositive-style valid form structurally: given P -> Q and not Q, not P is structurally supported.
- For affirming consequent: explain why it is fallacy-shaped: given P -> Q and Q, P is not structurally licensed by the conditional alone.
- For denying antecedent: explain why it is fallacy-shaped: given P -> Q and not P, not Q is not structurally licensed by the conditional alone.
- For counterexample: explain the role of counterexample structurally: it shows how a proposed inference can fail without selecting a benchmark answer.
- For ambiguous/unsupported: explain what is missing, not pretend certainty.

All explanations must remain structural. “Supported form” means structurally supported form, not benchmark truth, item truth, answer correctness, or official validity scoring.

## Safety Boundaries

- no answer keys
- no item-ID authority
- no answer selection
- no official score claim
- no benchmark-specific tuning
- no raw benchmark storage by default
- no hidden symbolic authority
- no confidence laundering
- unsupported gaps visible

Additional constraints:

- No explanation may convert a `ProofStep` into answer choice selection.
- No explanation may claim truth/soundness beyond the source proof artifact.
- No explanation may hide uncertainty, unsupported assumptions, or missing refs.
- No explanation may use private symbolic markers as authority.
- No explanation may store raw benchmark text by default.

## Non-goals

- no implementation in this phase
- no teaching generation behavior
- no proof-chain generation
- no solver changes
- no MCQ adapter changes
- no runtime integration
- no scoring

This design document must not change parser, normalizer, solver, MCQ adapter, runtime, scoring, or proof behavior.

## Future Phases

A. design doc — current

B. existing `TeachingExplanation` schema alignment

C. teaching helper diagnostics on synthetic fixtures

D. explanation quality diagnostic

E. advisor review for explanation style

F. only later runtime integration audit

G. no official score claim

## Operator Decisions

Current completed gate:

- APPROVE_TEACHING_EXPLANATION_DESIGN_ONLY

Next possible operator decisions:

- APPROVE_TEACHING_EXPLANATION_SCHEMA_ALIGNMENT_ONLY
- APPROVE_TEACHING_EXPLANATION_HELPERS_DIAGNOSTICS_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
