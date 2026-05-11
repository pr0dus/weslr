# WESLR LogicalFormNormalizer Predicate Helpers Approval V1

## Status
- operator_approved_helper_phase
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- helper_only
- no_runtime_behavior_change

## Operator Decision
- APPROVE_PREDICATE_DECOMPOSITION_HELPERS_ONLY

## Scope of This Approval
Changes to `weslr/logical_form_normalizer.py` are allowed only for predicate decomposition helper functions that build on existing atomic term candidates.

Approved implementation scope:
- relation-hint detection helpers
- conservative predicate candidate creation from atomic candidate IDs
- form-level predicate helper orchestration
- redacted predicate decomposition diagnostic summarization

These helper changes remain diagnostic/helper-only and do not change runtime behavior.

## Still Forbidden
- no parser wiring
- no solver wiring
- no MCQ adapter wiring
- no runtime wiring
- no answer selection
- no answer-key use
- no item-id authority
- no benchmark-specific tuning

## Safety Boundary
This approval does not authorize parser behavior changes, solver behavior changes, scoring changes, MCQ adapter integration, runtime integration, official score claims, or raw benchmark persistence by default.
