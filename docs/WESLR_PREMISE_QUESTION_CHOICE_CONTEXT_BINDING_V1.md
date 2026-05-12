# WESLR Premise/Question/Choice Context Binding V1

## Status

- design_only
- context_binding
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose

WESLR needs a structural layer connecting premise propositions, question instructions, and choice propositions before proof steps or teaching explanations can be trusted.

The current offline reasoning spine can produce safe redacted records, but it still needs an explicit context-binding layer that records what the premises say, what the question asks, and how each choice relates to the target. This layer prepares later proof-step candidates without selecting answers, claiming truth, or changing runtime behavior.

## Problem

Current layers produce safe records, but proof-useful cross-role signal is weak:

- simple inference candidates are duplicate-support only
- premise/choice alignment remains sparse
- premise relation/context binding remains weak
- proof generation would be premature

A proof layer built directly on sparse proposition matches would risk creating private symbolic authority: it could appear to reason while hiding unsupported role assumptions. Context binding makes those assumptions explicit and visible first.

## Current architecture

Current offline path:

`parser → normalizer → predicates → propositions → choice-stem bindings → binding-derived propositions → proposition merges → simple inference candidates`

This path remains sound. The missing step is not a replacement for the spine; it is a bridge between proposition-level evidence and later proof-step generation.

## Missing layer

Define `ReasoningContextBindingCandidate`.

Purpose: a redacted structural object that binds:

- what the premises say
- what the question asks
- how each choice relates to the target

The object should hold references to existing safe records and describe the expected reasoning role without using answer keys, item IDs, raw benchmark text, or answer selection.

## Proposed fields for `ReasoningContextBindingCandidate`

- `schema_version`
- `binding_id`
- `source_premise_proposition_ids`
- `source_question_instruction_ids`
- `source_choice_proposition_ids`
- `question_target_type`
- `premise_context_type`
- `choice_target_role`
- `expected_reasoning_relation`
- `candidate_support_role`
- `confidence`
- `unsupported_gaps`
- `human_explanation`
- `legibility`
- `anti_gaming`

## Allowed `question_target_type` values

- `must_be_true`
- `must_be_false`
- `follows`
- `does_not_follow`
- `valid_argument`
- `invalid_argument`
- `counterexample`
- `completion`
- `unknown`

## Allowed `premise_context_type` values

- `given_fact`
- `conditional_rule`
- `quantified_rule`
- `exclusion_rule`
- `definition_like`
- `background_context`
- `mixed_context`
- `unknown`

## Allowed `choice_target_role` values

- `candidate_conclusion`
- `candidate_counterexample`
- `candidate_invalid_statement`
- `candidate_valid_statement`
- `candidate_restatement`
- `candidate_irrelevant`
- `fragment_needs_binding`
- `unknown`

## Allowed `expected_reasoning_relation` values

- `support`
- `contradict`
- `instantiate_rule`
- `apply_condition`
- `test_validity`
- `provide_counterexample`
- `complete_template`
- `unknown`

## Design doctrine

- Context binding is not proof.
- Context binding is not answer selection.
- Context binding is not a truth claim.
- Context binding prepares proof-step candidates by making roles explicit.
- Unsupported gaps must remain visible.
- Low-confidence bindings must not be silently promoted.

A context-binding record may say that a choice is structurally positioned as a candidate conclusion or candidate counterexample. It must not say that the choice is correct, true, selected, or scored.

## Connection to existing spine

- `PropositionCandidate` remains the claim unit.
- `ChoiceStemBindingCandidate` helps produce choice-side propositions.
- `PropositionMergeCandidate` deduplicates proposition candidates.
- `SimpleInferencePatternCandidate` marks weak pattern opportunities.
- `ReasoningContextBindingCandidate` should sit before `ProofStep`.
- `ProofStep` should consume context-bound proposition groups later.

The proposed placement is:

`parser → normalizer → predicates → propositions → choice-stem bindings → binding-derived propositions → proposition merges → simple inference candidates → reasoning context bindings → proof-step candidates later`

This keeps the proof layer downstream of explicit role/context records.

## Anti-gaming boundaries

The context-binding layer must preserve these boundaries:

- no answer keys
- no item IDs as authority
- no benchmark-specific tuning
- no answer selection
- no official score claim
- no raw benchmark storage by default
- no hidden symbolic authority

The layer may use record IDs created by WESLR as references, but it must not use benchmark item IDs as authority or as hidden labels for correctness.

## Synthetic curriculum recommendation

A future non-benchmark synthetic mini-curriculum should contain 10–20 examples for structural validation, not benchmark scoring. Recommended patterns:

- universal syllogism
- modus ponens
- modus tollens
- affirming the consequent
- denying the antecedent
- contradiction
- counterexample
- irrelevant choice
- noun-phrase choice binding
- invalid argument identification

Synthetic examples are for structural validation, not benchmark scoring. They should test whether WESLR can produce legible context bindings and visible unsupported gaps before any benchmark-facing proof diagnostics continue.

## Non-goals

- no implementation in this phase
- no parser changes
- no normalizer changes
- no teaching-spine code changes
- no solver changes
- no MCQ adapter changes
- no runtime integration
- no proof generation
- no answer selection

## Future phases

A. design doc — current

B. context-binding schema only

C. synthetic curriculum design

D. context-binding helper diagnostics

E. run on synthetic curriculum

F. run on redacted MMLU subset

G. only later proof-step candidate generation

H. runtime integration audit much later

I. no official score claim

## Operator decision options

- `APPROVE_CONTEXT_BINDING_SCHEMA_ONLY`
- `APPROVE_SYNTHETIC_LOGIC_CURRICULUM_DESIGN`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`
