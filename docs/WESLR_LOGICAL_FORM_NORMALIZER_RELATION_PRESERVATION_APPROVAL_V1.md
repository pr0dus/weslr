# WESLR LogicalFormNormalizer Relation Preservation Approval V1

## Status
- operator_approved_helper_phase
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- helper_only
- no_runtime_behavior_change

## Operator Decision
- APPROVE_RELATION_PRESERVATION_HELPERS_ONLY

## Scope of This Approval
Changes to `weslr/logical_form_normalizer.py` are allowed only for helper behavior that preserves relation carriers for predicate decomposition without changing parser, solver, or runtime behavior.

Approved implementation scope:
- relation-hint extraction from surface before stopword removal
- normalized relation-carrier atomic candidates using fingerprints only
- predicate helper use of preserved relation hints
- redacted diagnostics for relation-preservation behavior

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
