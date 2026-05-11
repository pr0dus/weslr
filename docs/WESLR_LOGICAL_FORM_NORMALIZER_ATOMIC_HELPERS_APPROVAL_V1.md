# WESLR LogicalFormNormalizer Atomic Helpers Approval V1

## Status
- operator_approved_helper_phase
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- helper_only
- no_runtime_behavior_change

## Operator Decision
- APPROVE_ATOMIC_EXTRACTION_HELPERS_ONLY

## Scope of This Approval
Changes to `weslr/logical_form_normalizer.py` are now allowed only for helper functions that support atomic extraction diagnostics.

Approved implementation scope:
- atomic tokenization helpers
- atomic term candidate helper creation
- role-aware atomic candidate indexing
- alignment evidence helper creation
- redacted atomic diagnostic summarization

These helper changes remain diagnostic/helper-only and do not change runtime behavior.

## Still Forbidden
- parser wiring
- solver wiring
- MCQ adapter wiring
- runtime wiring
- threshold changes
- benchmark-specific tuning
- answer-key use
- item-id authority
- answer selection

## Why Older Tests Must Not Block This Phase
Older design and revision tests were written for the previous phase, when `weslr/logical_form_normalizer.py` itself was still frozen.
That is no longer the active operator decision.
For this approved helper phase, those older tests must not reject helper-only changes to `weslr/logical_form_normalizer.py`.
They must still reject parser, solver, MCQ adapter, and runtime changes.

## Safety Boundary
This approval does not authorize:
- parser behavior changes
- solver behavior changes
- scoring changes
- MCQ adapter integration
- runtime integration
- official score claims
- raw benchmark persistence by default

The approved path is helper-only, redacted, anti-gaming, and evidence-driven.
