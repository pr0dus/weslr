# WESLR Human Conversation Evaluator Boundary V1

## 1. Purpose

Define the internal-only boundary for a future human conversation evaluator.
This closes the baseline gap: **no live human conversation evaluator yet**.
It is metadata-only, non-official, non-public, and non-live.

## 2. Relationship to Existing Pieces

- **Dataset registry**: source approval and governance gate.
- **Internal task corpus helpers**: task/corpus metadata layer.
- **Real response adapter helpers**: future safe adapter boundary.
- **Rehearsal runner**: gap/report metadata layer.
- **Baseline review**: source of the evaluator gap.
- **Live slice guard**: precedent only; not widened here.

## 3. Evaluator Scope

May evaluate later:
- human intent understanding
- frustration/urgency recognition
- correction assimilation
- continuity without false memory
- non-canned response formation
- uncertainty explanation
- action/governance boundary recognition
- source/evidence honesty
- operator burden reduction

Must not evaluate or claim:
- official Turing pass
- certified intelligence
- public readiness
- voice readiness
- live user safety readiness
- benchmark score
- model superiority

## 4. Conversation Input Policy

Allowed future inputs:
- synthetic WESLR-created conversation scenarios
- approved internal task descriptors
- redacted metadata-only conversation descriptors
- operator-approved internal test scripts

Blocked:
- raw private user conversations
- `.weslr` / private memory
- live user chats
- hidden / semi-private / private datasets
- raw transcripts by default
- provider/model outputs unless separately approved
- benchmark / Turing hidden materials

## 5. Evaluation Dimensions

- `intent_tracking`
- `continuity_tracking`
- `correction_assimilation`
- `human_concern_tracking`
- `specificity_non_cannedness`
- `uncertainty_honesty`
- `evidence_boundary_awareness`
- `action_governance_awareness`
- `tone_and_priority_fit`
- `safe_next_step_quality`

## 6. Result Labels

Internal qualitative labels only:
- `pass_internal_conversation_rehearsal`
- `partial_internal_conversation_rehearsal`
- `fail_internal_conversation_rehearsal`
- `inconclusive_internal_conversation_rehearsal`
- `blocked_by_source_governance`
- `blocked_by_privacy_boundary`
- `blocked_by_runtime_boundary`
- `needs_operator_review`

These are not scores, official results, or public claims.

## 7. Boundary / Preflight Rules

Fail closed if:
- raw/private/live transcript is requested
- `.weslr` / private memory is requested
- public / live / voice / final-answer authority is true
- official / Turing / intelligence claim flag is true
- source registry is missing or blocked
- raw response / transcript storage is requested
- UNKNOWN ENGINE authority appears
- next lane jumps to public / live / voice without review

## 8. Artifact Policy

- raw conversation text not stored by default
- use redacted descriptors and metadata labels
- final-answer authority false
- user-facing prose authority false
- operator review required
- unsupported/raw fields redacted

## 9. UNKNOWN ENGINE Role

Allowed:
- predict conversation failure zones
- suggest synthetic scenario variants
- compare predicted vs observed failure labels
- compress repeated conversation gaps

Forbidden:
- authority
- scoring/certification
- official Turing judge
- future certainty
- source/license approval
- runtime/live control
- automatic self-modification

## 10. Future Implementation Plan

Recommended next lanes:
- `REVIEW_WESLR_HUMAN_CONVERSATION_EVALUATOR_BOUNDARY_V1`
- `IMPLEMENT_WESLR_HUMAN_CONVERSATION_EVALUATOR_HELPERS_V1`
- `REVIEW_WESLR_HUMAN_CONVERSATION_EVALUATOR_HELPERS_V1`
- `DESIGN_WESLR_CONTEXT_PRESSURE_AND_CLIPBOARD_LIMIT_EVALUATION_V1`
- later `RERUN_WESLR_INTERNAL_EVALUATION_REHEARSAL_V1`

## 11. Review Criteria

Future review must verify:
- no implementation hidden in design
- no raw transcript retention
- no live / public / voice / final-answer authority
- no official Turing / intelligence claims
- evaluator remains internal qualitative metadata only
