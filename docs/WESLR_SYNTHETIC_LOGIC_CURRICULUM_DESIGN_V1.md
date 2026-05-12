# WESLR Synthetic Logic Curriculum Design V1

## Status

- design_only
- synthetic_curriculum
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose

Design a small synthetic curriculum to validate WESLR's reasoning spine on controlled, non-benchmark examples.

The curriculum is intended to make structural progress measurable before additional noisy benchmark-facing diagnostics. It should validate whether the offline reasoning spine can produce legible parser, proposition, context-binding, and inference-candidate records without relying on answer keys, item IDs, official scores, or raw benchmark text.

## Why synthetic

MMLU-style data is useful but noisy. It exposes real-world phrasing variation, but it also makes architectural progress hard to isolate because parsing, premise detection, context binding, and inference pattern quality all fail together.

Current diagnostics show safe structure but weak proof-useful signal. Simple inference candidates remain weak, premise/choice alignment is sparse, and context binding is not yet validated as a controlled substrate.

Synthetic examples allow controlled validation of parser → proposition → context binding → inference candidate behavior. A synthetic curriculum can deliberately cover one reasoning pattern at a time while keeping unsupported gaps visible.

Synthetic curriculum is not benchmark scoring. Synthetic examples are not benchmark scoring. They are structural validation fixtures for WESLR's own reasoning substrate.

## Curriculum categories

Plan 10–20 handcrafted examples across these categories:

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
- necessary/sufficient confusion
- quantifier reasoning
- negation reasoning
- disjunction reasoning

Each category should have at least one minimal example. Higher-priority categories may have paired positive/negative examples so WESLR can distinguish valid support from fallacy-shaped structure.

## Example schema

Synthetic example metadata, not implementation:

- `example_id`
- `logic_family`
- `input_form`
- `premise_templates`
- `question_instruction_template`
- `choice_templates`
- `expected_structural_pattern`
- `expected_context_binding_type`
- `expected_teaching_focus`
- `unsupported_gaps_allowed`
- `anti_gaming_notes`

The schema should describe expected structure, not correct answer selection. For example, `expected_structural_pattern` may name a pattern such as `modus_ponens` or `counterexample`, while `expected_context_binding_type` may identify whether a choice is expected to behave like a candidate conclusion, candidate counterexample, irrelevant choice, or fragment needing binding.

## Safety boundaries

- examples are handcrafted synthetic placeholders
- no external benchmark text
- no answer-key tuning
- no official score
- no item-ID authority
- no runtime integration
- no answer selection in this phase

The curriculum may include internally authored expected structural patterns. These are not benchmark answer keys and must not be used to claim official performance. They exist only to verify that WESLR can expose safe, legible structural records.

## How it connects to current spine

Expected validation path:

`synthetic example → parser → normalizer → propositions → choice-stem binding → proposition merge → simple inference candidate → reasoning context binding`

The curriculum should test whether each stage preserves enough safe structure for the next stage. It should especially check whether `ReasoningContextBindingCandidate` can bind premise propositions, question instructions, and choice propositions before any proof-step candidate generation.

## Future phases

A. curriculum design — current

B. synthetic curriculum schema only

C. synthetic fixture creation

D. dry-run diagnostic over synthetic examples

E. compare expected structural patterns

F. improve context binding helpers

G. only later proof-step candidate generation

H. no official score claim

## Operator decisions

- `APPROVE_SYNTHETIC_CURRICULUM_SCHEMA_ONLY`
- `REQUEST_REVISION`
- `REJECT_OR_DEFER`
