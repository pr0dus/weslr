# WESLR Premise/Background Classification Design V1

## Status

- design_only
- premise_background_classification
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

## Problem

Premise proposition coverage is currently limited because some fragments appear to be classified as premise, background, or question-instruction incorrectly. The latest redacted diagnostics suggest that relation coverage is not only a relation-word problem: role classification itself is blocking premise-side proposition coverage before simple inference can safely improve.

This document is design only. It does not change parser behavior, normalizer behavior, teaching-spine behavior, solver behavior, runtime behavior, scoring, or answer selection.

## Evidence

Redacted diagnostic metrics:

- parsed premise statements: 23
- premise relation hints present: 11
- premise relation hints missing: 12
- background_or_instruction_misclassified: 10
- quantifier_relation_missing: 3
- conjunction_relation_missing: 4
- likely blocker: premise_role_misclassification
- no answer-key use
- no official score claim

These are diagnostic counts only. They are not truth claims, proof steps, answer choices, benchmark answers, or official scores.

## Role Definitions

### premise

A premise is evidence-bearing content: a fragment that asserts or supplies information that may support or constrain later reasoning. A premise may include explicit logical structure, ordinary-language claims, quantified claims, conjunctive facts, conditional facts, membership facts, or other content that can be treated as inferential evidence only after safe parsing and validation.

### background

Background is context-setting material. It may frame a domain, describe a situation, or introduce vocabulary, but it should not be treated as inferential evidence by default. Background can become premise-like only through an approved parser-role helper or later operator-reviewed design that preserves unsupported gaps.

### question_instruction

A question_instruction tells the system what task is being asked: infer, identify, select, evaluate, determine validity, or choose among candidate claims. Question instructions are not premises. They may guide structural parsing, but they must not become evidence-bearing claims by default.

### choice_claim

A choice_claim is candidate-side content. Choice claims remain candidate-side only: they may be parsed and compared structurally, but they are not premises and cannot become support for themselves.

### unsupported_fragment

An unsupported_fragment is content whose role, relation, or inferential status is not safely established. Unsupported fragments must stay visible, not silently promoted. They may be reported as gaps, diagnostic signals, or operator-review candidates.

## Classification Doctrine

- A premise is evidence-bearing content.
- Background frames context but should not be treated as inferential evidence by default.
- Question instructions ask what to do and are not premises.
- Choice claims remain candidate-side only.
- Unsupported fragments must stay visible, not silently promoted.
- Classification should be conservative when role evidence is ambiguous.
- Promotion from background or unsupported_fragment to premise requires explicit, auditable structural warrant.
- Parser role classification must remain redacted and must not inspect answer keys, correctness labels, item IDs as authority, or official scores.

## Risk

Promoting too much background into premise can create false inference support. A broad role-classification change might make unrelated context look like evidence, allowing duplicate-support or simple-pattern helpers to overcount structural overlap. This would increase apparent reasoning coverage without improving actual legibility or validity.

The safe direction is not "classify more as premise" by default. The safe direction is to define explicit premise warrants, preserve uncertainty, and keep unsupported or background-like fragments visible when their inferential role is not clear.

## Future Parser-Change Requirements

Any later parser change must:

- be redacted
- preserve anti-gaming
- avoid answer keys
- avoid item-ID authority
- avoid benchmark-specific tuning
- keep unsupported fragments visible
- include before/after diagnostics
- avoid answer selection
- avoid official score claims
- preserve choice_claim as candidate-side only
- preserve question_instruction as non-premise task direction

## Non-goals

- no parser code change in this phase
- no solver change
- no MCQ adapter change
- no runtime integration
- no answer selection
- no official score claim
- no normalizer change
- no teaching spine change
- no proof-step generation
- no inference matching implementation

## Future Phases

A. design doc — current

B. role-classification schema/test expectations

C. parser helper change only if approved

D. redacted before/after diagnostic

E. premise proposition coverage diagnostic

F. only later simple inference diagnostics

## Operator Decisions

- APPROVE_PARSER_ROLE_CLASSIFICATION_HELPERS_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
