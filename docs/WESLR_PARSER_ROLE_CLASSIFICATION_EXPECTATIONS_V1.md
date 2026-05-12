# WESLR Parser Role Classification Expectations V1

## Status

- expectations_only
- parser_role_classification
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Purpose

This document defines synthetic expected parser role-classification behavior before any parser changes are made. It uses generic placeholder fragments only and does not use benchmark text, answer keys, item IDs as authority, official scoring, or answer selection.

These expectations are design constraints for later operator review. They do not change parser, normalizer, teaching-spine, solver, MCQ adapter, runtime, or scoring behavior.

## Role Expectation Table

| Synthetic placeholder fragment | Expected role | Expectation note |
| --- | --- | --- |
| "All A are B." | premise | Quantified evidence-bearing claim. |
| "If A then B." | premise | Conditional evidence-bearing claim. |
| "A is B and C is D." | premise | Conjunctive evidence-bearing claim. |
| "Which of the following must be true?" | question_instruction | Task direction; question instructions are not premises. |
| "Based on the statements above." | question_instruction or background | Framing/task direction; not an evidence-bearing premise by default. |
| "Context: A scenario is described." | background | Context frame; background is not evidence by default. |
| "Choice A: A is B." | choice_claim | Candidate-side claim; choice claims stay candidate-side. |
| ambiguous fragment | unsupported_fragment | Role is not safely established; unsupported fragments stay visible. |

## Role Expectations

### premise expectation

A premise is evidence-bearing content. Synthetic fragments such as "All A are B.", "If A then B.", and "A is B and C is D." should be expected to classify as premise when they are presented as asserted statements rather than task instructions or candidate choices.

### background expectation

Background frames context and is not evidence by default. Synthetic context-setting fragments should remain background unless a future approved helper can establish an explicit evidence-bearing warrant without hiding uncertainty.

### question_instruction expectation

A question_instruction asks what to do. Synthetic instruction fragments such as "Which of the following must be true?" are not premises and must not be promoted into evidence-bearing claims.

### choice_claim expectation

A choice_claim is candidate-side content. Synthetic choice-labeled fragments such as "Choice A: A is B." should remain candidate-side only and must not become premise-side evidence.

### unsupported_fragment expectation

An unsupported_fragment is a fragment whose role is not safely established. Ambiguous fragments should remain visible as unsupported fragments rather than being silently promoted to premise, background, or choice_claim.

## Safety Rules

- do not promote question instructions into premises
- do not promote background into premise unless evidence-bearing
- choice claims stay candidate-side
- unsupported fragments stay visible
- no answer-key use
- no item-ID authority
- no benchmark-specific tuning
- no official score claim
- no answer selection
- no raw benchmark question, choice, or answer storage

## Future Implementation Gate

Parser changes require:

- operator approval
- synthetic tests first
- redacted before/after diagnostics
- release gate pass
- no raw benchmark storage
- no answer selection
- no answer-key use
- no item-ID authority
- no benchmark-specific tuning
- no official score claim

## Operator Decision Options

- APPROVE_PARSER_ROLE_CLASSIFICATION_HELPERS_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
