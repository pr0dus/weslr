# WESLR Binding-to-Proposition Projection Design V1

## Status

- design_only
- binding_to_proposition_projection
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change

This document is a design artifact only. It does not authorize code changes, proposition generation, inference matching, parser changes, normalizer changes, teaching-spine changes, solver changes, MCQ adapter changes, runtime integration, answer selection, or scoring claims.

## Purpose

`ChoiceStemBindingCandidate` is a pre-proposition normalization aid. It exists to make noun-phrase choices and fragment choices structurally legible before they are considered for later proposition projection.

The purpose of this design is to describe how a future helper could project safe, sufficiently structured bindings into `PropositionCandidate` records without creating a separate reasoning path. Choice-stem binding may improve the inputs available to proposition construction, but it must remain subordinate to the existing teaching spine and its governance boundaries.

## Evidence

Redacted diagnostic evidence only:

- `44` binding candidates
- `5` projection-ready bindings
- `2` items with projection-ready bindings
- `binding_not_explicit = 12`
- `relation_not_explicit = 16`
- no answer-key use
- no official score claim

The evidence suggests that a small subset of current binding candidates has enough structure for a future projection-helper design, while most candidates remain weak or low-confidence and should not be forced into propositions.

## Projection rule

Future projection rule:

`ChoiceStemBindingCandidate → PropositionCandidate`

Existing spine rule to preserve:

`PredicateCandidate → PropositionCandidate`

Choice-stem binding may assist proposition construction, but must not bypass teaching spine governance. A future projection helper should produce the same kind of governed `PropositionCandidate` artifact expected by the teaching spine, not a parallel proposition type and not a direct reasoning route.

The binding layer is therefore an upstream normalization aid. It can supply safe hints or references, but the resulting proposition must remain inspectable, validated, and constrained by existing proposition rules.

## Projection readiness criteria

A binding is projection-ready only if it has enough safe structure. Minimum criteria:

- source choice statement id
- binding type not `unsupported_binding`
- human explanation
- at least one of:
  - implied relation hint
  - bound subject hint
  - bound object hint
  - choice is full claim
- no anti-gaming violations
- unsupported gaps visible

Additional conservative guidance:

- Low-confidence bindings should remain diagnostic unless explicitly promoted by later operator-approved rules.
- Bindings with `binding_not_explicit` or `relation_not_explicit` should not silently become strong propositions.
- If a binding has visible unsupported gaps, projection should preserve those gaps in the resulting proposition explanation or refuse projection.
- Projection readiness is not correctness, answerability, or score evidence.

## Binding type handling

Future projection behavior by binding type:

- `choice_completes_question_predicate`: May project only if the stem supplies a clear predicate frame and the choice supplies a safe completion. Unsupported relation gaps must remain visible.
- `choice_supplies_subject`: May project only if the stem provides a safe predicate/object frame and the choice safely fills the subject position.
- `choice_supplies_object`: May project only if the stem provides a safe subject/predicate frame and the choice safely fills the object position.
- `choice_supplies_conclusion`: May project to a conclusion-role proposition candidate only as a candidate claim, never as a selected answer or proof step.
- `choice_is_full_claim`: May project most directly when the choice already has enough full-claim structure, while still preserving source references and anti-gaming checks.
- `choice_is_fragment_unknown`: Should not project by default. It may remain as a diagnostic artifact until future classifier or instruction extraction improvements reduce ambiguity.
- `unsupported_binding`: Must not project. It indicates that projection would require unsupported semantic invention or unsafe assumptions.

## Anti-gaming boundaries

- no answer keys
- no item IDs as authority
- no benchmark-specific tuning
- no answer selection
- no official score claim
- no raw benchmark storage by default

Projection must not use correctness labels, answer positions, item identifiers, raw benchmark text storage, or benchmark-specific phrasing patches. It must remain structural and redacted.

## Non-goals

- no implementation in this phase
- no parser changes
- no normalizer changes
- no teaching-spine code changes
- no solver changes
- no MCQ adapter changes
- no runtime integration
- no inference matching

This phase does not generate propositions and does not alter runtime behavior.

## Future phases

A. design doc — current

B. schema/interface alignment if needed

C. projection helper diagnostics only

D. redacted coverage diagnostic

E. proposition quality diagnostic

F. simple inference diagnostics only

G. runtime integration audit later

H. no official-score claim

Each phase requires separate operator review before execution.

## Operator decision options

- APPROVE_BINDING_TO_PROPOSITION_HELPERS_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
