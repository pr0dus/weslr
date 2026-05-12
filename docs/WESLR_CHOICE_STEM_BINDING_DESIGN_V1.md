# WESLR Choice-Stem Binding Design V1

## Status

- design_only
- choice_stem_binding
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

This document is a design artifact only. It does not authorize implementation, runtime execution, parser changes, normalizer changes, teaching-spine changes, solver changes, MCQ adapter changes, answer selection, or official scoring claims.

## Problem

Many MCQ choices are noun phrases or other fragments rather than standalone propositions. The current choice-side predicate fallback can preserve these fragments structurally, but often has to emit an `unknown_relation` because the relation is not explicit inside the choice text itself.

That behavior is safe, because it avoids inventing unsupported semantics. However, it creates weak propositions: they are legible as fragments, but not strong enough for inference matching. Inference matching should not run on fallback-heavy propositions where the central relation is unknown or unsupported.

The missing design layer is a structural binding step between the question stem and the choice fragment. The stem often supplies the missing role, predicate, conclusion frame, or object/subject expectation that makes the choice interpretable as a proposition candidate.

## Evidence

Redacted diagnostic evidence only:

- choice_noun_phrase_only = 32
- unknown_relation choice predicates = 37
- relation_not_explicit = 37
- simple pattern candidates remain sparse
- no answer key used
- no official score claimed

These metrics indicate that the current issue is expected noun-phrase choice limitation plus missing choice-stem binding, not an answer-key problem or an official-score problem.

## Design goal

Turn:

> question stem + choice fragment

into:

> choice-bound proposition candidate template

without:

- answer selection
- answer-key use
- raw benchmark storage
- benchmark-specific tuning

The goal is structural proposition projection, not solving. A bound candidate should make the implicit relationship between stem and choice legible enough for later schema, diagnostics, and review phases.

## Binding model

Conceptual object: `ChoiceStemBindingCandidate`

Fields:

- `binding_id`: Stable local identifier for the binding candidate. It must not encode an item ID as authority.
- `source_question_instruction_id`: Reference to the parsed/redacted question instruction or stem representation that contributed the binding frame.
- `source_choice_statement_id`: Reference to the parsed/redacted choice statement or fragment representation being bound.
- `choice_role`: Structural role inferred for the choice within the question frame, such as subject, object, predicate completion, conclusion, full claim, or unknown fragment.
- `stem_binding_type`: One of the supported binding types listed below.
- `implied_relation_hint`: Non-authoritative relation hint supplied by the stem structure when explicit enough. It is a hint, not a truth claim.
- `bound_subject_hint`: Candidate subject position after stem-choice binding, if structurally supported.
- `bound_object_hint`: Candidate object position after stem-choice binding, if structurally supported.
- `confidence`: Design-level confidence for the binding structure, based on explicitness and unsupported gaps. It must not use answer correctness.
- `unsupported_gaps`: List of missing or ambiguous elements that remain unresolved, such as missing relation, missing subject, missing object, ambiguous conclusion frame, or unsupported comparison target.
- `human_explanation`: Short operator-legible explanation of why this binding was proposed and what remains unsupported.
- `anti_gaming`: Record of the safeguards applied: no answer keys, no item-ID authority, no benchmark-specific wording patches, no answer selection, and no official-score claim.
- `legibility`: Human-readable statement of the template produced and the limits of the template.

A binding candidate is a structural bridge from fragment to proposition candidate. It is not an answer, not a score, and not a benchmark-specific patch.

## Binding types

- `choice_completes_question_predicate`: The stem supplies a predicate frame and the choice completes it.
- `choice_supplies_subject`: The stem supplies a predicate/object frame and the choice supplies the subject.
- `choice_supplies_object`: The stem supplies a subject/predicate frame and the choice supplies the object.
- `choice_supplies_conclusion`: The stem asks for a conclusion and the choice supplies the candidate conclusion content.
- `choice_is_full_claim`: The choice is already a full claim and can be projected without stem completion beyond context tagging.
- `choice_is_fragment_unknown`: The choice is a fragment, but the stem does not provide enough structure to bind it safely.
- `unsupported_binding`: The attempted binding would require unsupported semantic invention or benchmark-specific assumptions.

## Safe examples as templates only

No raw benchmark examples are stored here. The following are generic placeholders only:

- `Which of the following is true?` + `A is B` → `choice_is_full_claim`
- `Which conclusion follows?` + `A` → `choice_supplies_conclusion`
- `Which object has property P?` + `A` → `choice_supplies_subject` or `choice_supplies_object`, depending on the normalized stem frame
- `Which statement is invalid?` + `If P then Q` → `choice_is_full_claim` with validity/evaluation left to later reasoning, not answer selection

These examples describe templates only. They do not encode benchmark content, answers, item IDs, or official scoring behavior.

## Anti-gaming boundaries

- no answer keys
- no item IDs as authority
- no benchmark-specific wording patches
- no official score claim
- no raw benchmark storage by default
- no answer selection
- binding is structural only

The binding layer must never learn from correctness labels, item identifiers, or benchmark-specific phrasing. It may only describe structurally supported relationships between a stem representation and a choice fragment representation.

## Runtime distinction

This belongs to the offline reasoning spine first. It is not `/chat` integration.

`/chat` integration requires a later runtime integration audit, including response-contract review, hardcoded-path review, and runtime behavior verification. Hardcoded contract paths are not the current cause of the noun-phrase choice limitation, but they could interfere later during integration if not audited.

## Future phases

A. design doc — current

B. schema only

C. helper diagnostics only

D. redacted coverage diagnostic

E. proposition projection update

F. only later inference-pattern diagnostics

G. runtime integration audit later

H. no official-score claim

No future phase is authorized by this document alone. Each phase requires operator review before execution.

## Operator decision options

- APPROVE_CHOICE_STEM_BINDING_SCHEMA_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
