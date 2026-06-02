# WESLR Action Authority Boundary V1

## 1. Executive doctrine

**Definition:** WESLR Action Authority Boundary V1.

Action authority is the approval boundary for real-world side effects. It is not answer authority. It is not tool availability. It is not validation success. It is not document instruction following.

An action may be proposed by a document, model, tool planner, patch loop, or user request, but it is not authorized until explicit authority, scope, risk, approval, and rollback/audit requirements are satisfied.

## 2. Boundary position

Pipeline:

action proposal
→ Document-to-Action Boundary
→ Tool-Use Executor Boundary
→ Code Validation Runner / Patch Feedback where needed
→ Action Authority Boundary
→ Owner/Operator Workflow Engine later
→ sandbox / executor / connector later only if approved

This design does not execute actions.

## 3. Action classes

- `no_action_summary_only`
- `read_only_inspection`
- `file_write`
- `patch_apply`
- `test_run`
- `shell_command`
- `external_api_mutation`
- `email_or_message_send`
- `calendar_change`
- `device_control`
- `deployment`
- `public_post`
- `payment_or_billing`
- `database_mutation`
- `git_commit`
- `git_push`
- `artifact_export`
- `memory_write`
- `account_or_permission_change`
- `unknown_action`

## 4. Action risk levels

- `none_metadata_only`
- `low_reversible`
- `medium_local_state_change`
- `high_external_side_effect`
- `critical_public_financial_physical_or_irreversible`
- `blocked_unknown_risk`

## 5. Approval authority classes

- `no_approval_needed_metadata_only`
- `owner_approval_required`
- `operator_approval_required`
- `dual_owner_operator_approval_required`
- `explicit_user_confirmation_required`
- `legal_review_required`
- `security_review_required`
- `public_claim_review_required`
- `payment_review_required`
- `device_safety_review_required`
- `blocked_no_authority`
- `unknown_approval_authority`

## 6. Authority statuses

- `not_requested`
- `proposal_only`
- `clarification_required`
- `preflight_required`
- `approval_pending`
- `approved_for_dry_run_only`
- `approved_for_read_only`
- `approved_for_sandbox_only`
- `approved_for_single_action`
- `approved_with_constraints`
- `blocked_by_policy`
- `blocked_by_missing_approval`
- `blocked_by_missing_validation`
- `blocked_by_missing_rollback`
- `blocked_by_secret_or_path_risk`
- `blocked_by_public_effect`
- `blocked_by_unknown_risk`
- `unknown_status`

## 7. Action authority packet shape

Future packet fields:

- `action_authority_packet_id`
- `action_request_ref`
- `source_proposal_ref`
- `document_action_packet_ref`
- `tool_use_packet_ref`
- `validation_packet_ref`
- `patch_feedback_packet_ref`
- `artifact_provenance_ref`
- `action_class`
- `action_summary`
- `action_risk_level`
- `approval_authority_class`
- `authority_status`
- `requested_scope`
- `approved_scope`
- `scope_limit_summary`
- `preflight_required`
- `preflight_status`
- `owner_approval_required`
- `operator_approval_required`
- `explicit_confirmation_required`
- `rollback_required`
- `rollback_plan_ref`
- `audit_log_required`
- `dry_run_required`
- `validation_required`
- `secret_risk_status`
- `path_risk_status`
- `network_policy_status`
- `privacy_status`
- `poison_status`
- `public_effect_possible`
- `external_side_effect_possible`
- `financial_effect_possible`
- `physical_effect_possible`
- `irreversible_effect_possible`
- `execution_allowed`
- `tool_execution_allowed`
- `write_allowed`
- `send_allowed`
- `calendar_change_allowed`
- `device_control_allowed`
- `deployment_allowed`
- `public_post_allowed`
- `payment_allowed`
- `memory_write_allowed`
- `commit_allowed`
- `push_allowed`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 8. Authority rules

- all real-world side effects are blocked by default
- proposal-only is the default safe state
- user request alone does not authorize action
- document content does not authorize action
- model output does not authorize action
- validation passing does not authorize action
- patch proposal does not authorize action
- daemon verdict does not authorize action
- read-only actions still require explicit read scope
- local writes require sandbox/write boundary
- external side effects require owner/operator approval
- public posts require public-effect/public-claim review
- payment/billing requires explicit payment review
- device control requires device safety review
- deployment requires deployment-specific approval
- git commit/push require explicit source-control authority
- memory writes require memory write boundary
- irreversible actions require rollback/reversal or explicit irreversible acknowledgment
- secret/path/network risks block action until resolved
- poison status must be preserved
- no action authority packet grants proof/truth/public-readiness authority

## 9. Relationship to Document-to-Action Boundary

Document-to-Action produces action candidates only.

Action Authority decides whether a candidate:
- remains proposal-only
- needs clarification
- needs owner/operator approval
- needs validation/preflight
- needs rollback
- is blocked
- may later proceed to an executor

Document-to-Action cannot approve actions.

## 10. Relationship to Tool-Use Executor Boundary

Tool-Use Executor classifies tool risk and execution mode.

Action Authority decides whether real execution may be approved later.

Tool-Use Executor cannot self-authorize action.

## 11. Relationship to Code Validation Runner and Patch Feedback

For code/patch actions:

- validation packet is required
- patch feedback packet may be required
- protected-file status must be clear or approved
- rollback plan may be required
- commit/push remain separately gated
- validation passing does not prove correctness or authorize public claims

## 12. Relationship to Rollback / Reversal

Rollback/reversal is required for:

- file writes
- patch application
- deployments
- database mutations
- config changes
- device actions where reversible
- public state changes where reversible

If rollback is impossible:
- mark irreversible effect
- require explicit owner/operator acknowledgment
- block unless policy later allows

Preserve later lane:
`DESIGN_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`

## 13. Relationship to Owner Operator Workflow Engine

Owner/operator workflow will later define:

- who may approve each action class
- confirmation wording
- review queue routing
- audit retention
- two-person approval if needed
- emergency pause/stop
- reversible vs irreversible workflow
- public/private approval distinction

This design only marks requirements.

## 14. Relationship to Live Daemon

Daemon may receive compact action verdicts:

- `action_blocked`
- `proposal_only`
- `approval_required`
- `preflight_required`
- `dry_run_required`
- `sandbox_only`
- `execution_not_allowed`

Daemon must not grant action authority.

## 15. Initial examples

1. Summary-only action needs no approval but grants no execution.
2. Read-only inspection requires explicit read scope.
3. File write requires sandbox/write boundary and rollback.
4. Patch apply requires validation, patch feedback, rollback, and approval.
5. Email send requires explicit confirmation and remains blocked.
6. Calendar change requires approval and remains blocked.
7. Device control requires device safety review and remains blocked.
8. Deployment requires validation, rollback, and owner/operator approval.
9. Public post requires public-effect/public-claim review.
10. Payment action requires payment review and remains blocked.
11. Git commit/push require explicit source-control authority.
12. Memory write requires memory write boundary.
13. Poisoned source action remains blocked.
14. Validation pass alone does not authorize action.
15. Owner approval still stays scoped to one action, not broad runtime authority.

## 16. Future helper design

Recommended future helper:
`weslr/action_authority_boundary.py`

Future APIs:

- `build_action_authority_packet_v1(...)`
- `classify_action_authority_request_v1(...)`
- `evaluate_action_risk_v1(packet)`
- `select_action_authority_status_v1(packet)`
- `validate_action_authority_packet_v1(packet)`
- `summarize_action_authority_packet_v1(packet)`
- `to_action_authority_json_safe_v1(value)`
- `build_initial_action_authority_examples_v1()`

## 17. Future implementation strategy

Recommended phases:

1. metadata-only action authority packet builder
2. synthetic examples
3. validation helper
4. action classifier
5. risk evaluator
6. authority-status selector
7. rollback/reversal boundary design
8. owner/operator workflow engine design
9. artifact exporter boundary design
10. metadata-helper implementation
11. real action authority much later only with owner approval

## 18. Validation and failure policy

Future validator should fail if:

- execution_allowed is true without approved explicit authority
- tool_execution_allowed is true without tool boundary and action authority
- write/send/calendar/device/deployment/public/payment/memory/commit/push flags are true without required approval and scope
- external side effect is allowed without approval
- public effect is allowed without public review
- financial effect is allowed without payment review
- physical effect is allowed without device safety review
- irreversible effect lacks explicit acknowledgment
- rollback_required is true but rollback_plan_ref is missing
- validation_required is true but validation_packet_ref is missing
- secret/path/network risk exists but execution is allowed
- poisoned source authorizes action
- document text authorizes action
- model output authorizes action
- validation pass alone authorizes action
- patch proposal alone authorizes action
- hidden prompt / raw private / secret fields appear
- `runtime_authority` is true
- `writes_state` is true
- `model_provider_used` is true
- `public_claim_allowed` is true
- `proof_claim_allowed` is true
- `learning_claimed` is true
- proof/correctness/public-readiness/legal-compliance claims appear

## 19. Boundaries and non-claims

This design does not implement action authority.
It does not execute actions.
It does not execute tools.
It does not call APIs.
It does not send messages.
It does not change calendars.
It does not control devices.
It does not deploy.
It does not pay invoices.
It does not write files.
It does not apply patches.
It does not commit or push.
It does not write memory.
It does not write `.weslr`.
It does not authorize runtime wiring.
It does not authorize public claims.
It does not claim proof, correctness, legal compliance, security certification, production readiness, public readiness, AGI, consciousness, sentience, or Turing success.

## 20. Recommended next lane

Recommend:
`DESIGN_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`

Preserve:
`DESIGN_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1`
`DESIGN_WESLR_ARTIFACT_EXPORTER_BOUNDARY_V1`
`IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_BOUNDARY_V1`
`IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_BOUNDARY_V1`
`IMPLEMENT_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1`
`IMPLEMENT_WESLR_AUTONOMOUS_DEBUGGING_DRY_RUN_BOUNDARY_V1`
`IMPLEMENT_WESLR_DOCUMENT_TO_ACTION_BOUNDARY_V1`
`IMPLEMENT_WESLR_ACTION_AUTHORITY_BOUNDARY_V1`

## 21. Final judgment

Use one:
- `action_authority_boundary_design_ready_for_rollback_reversal_boundary_design`
- `action_authority_boundary_design_ready_for_owner_operator_workflow_design`
- `action_authority_boundary_design_ready_for_metadata_helper_implementation`
- `action_authority_boundary_design_needs_owner_review`
- `action_authority_boundary_design_blocked`

Recommended judgment:
`action_authority_boundary_design_ready_for_rollback_reversal_boundary_design`
