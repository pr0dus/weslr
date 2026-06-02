# WESLR Owner Operator Workflow Engine V1

## 1. Executive doctrine

**Definition:** WESLR Owner Operator Workflow Engine V1.

Owner/operator workflow is the human-governance routing boundary for future WESLR actions, approvals, reviews, confirmations, pauses, audit records, and escalation.

It is not execution authority by itself.
It is not proof/correctness authority.
It is not public-readiness authority.

A proposed action may be routed for owner/operator review, but routing does not equal approval and approval does not grant broad runtime authority.

## 2. Boundary position

Pipeline:

proposal / document action / tool-use proposal / patch proposal / rollback requirement
→ Code Validation Runner where needed
→ Patch Feedback Loop where needed
→ Tool-Use Executor Boundary
→ Document-to-Action Boundary where source-derived
→ Action Authority Boundary
→ Rollback and Reversal Boundary
→ Owner Operator Workflow Engine
→ executor/sandbox/connector later only if explicitly approved

This design does not execute workflow actions.

## 3. Human authority roles

- `owner`
- `operator`
- `admin_operator`
- `reviewer`
- `legal_reviewer`
- `security_reviewer`
- `payment_reviewer`
- `device_safety_reviewer`
- `public_claim_reviewer`
- `unknown_role`

## 4. Workflow request classes

- `information_only_review`
- `clarification_request`
- `approval_request`
- `dry_run_review`
- `read_only_review`
- `sandbox_write_review`
- `patch_review`
- `rollback_review`
- `irreversible_action_acknowledgment`
- `public_effect_review`
- `payment_review`
- `device_safety_review`
- `deployment_review`
- `memory_write_review`
- `account_permission_review`
- `emergency_pause_request`
- `unknown_workflow_request`

## 5. Workflow statuses

- `not_submitted`
- `queued_for_review`
- `needs_clarification`
- `approved_for_metadata_only`
- `approved_for_dry_run_only`
- `approved_for_read_only`
- `approved_for_sandbox_only`
- `approved_for_single_action`
- `approved_with_constraints`
- `rejected`
- `paused`
- `blocked_by_policy`
- `blocked_missing_required_review`
- `blocked_unknown_authority`
- `expired`
- `unknown_status`

## 6. Confirmation classes

- `no_confirmation_needed_metadata_only`
- `simple_confirmation`
- `explicit_named_action_confirmation`
- `scope_limited_confirmation`
- `dual_confirmation`
- `irreversible_acknowledgment`
- `public_effect_confirmation`
- `payment_confirmation`
- `device_safety_confirmation`
- `deployment_confirmation`
- `unknown_confirmation`

## 7. Workflow packet shape

Future packet fields:

- `workflow_packet_id`
- `source_request_ref`
- `action_authority_packet_ref`
- `rollback_packet_ref`
- `tool_use_packet_ref`
- `document_action_packet_ref`
- `validation_packet_ref`
- `patch_feedback_packet_ref`
- `artifact_provenance_ref`
- `workflow_request_class`
- `required_role`
- `assigned_role`
- `workflow_status`
- `confirmation_class`
- `confirmation_prompt_summary`
- `approval_scope`
- `approval_constraints`
- `expiration_policy`
- `audit_log_required`
- `audit_log_ref`
- `review_queue`
- `owner_review_required`
- `operator_review_required`
- `dual_review_required`
- `legal_review_required`
- `security_review_required`
- `payment_review_required`
- `device_safety_review_required`
- `public_claim_review_required`
- `rollback_review_required`
- `emergency_pause_available`
- `emergency_pause_active`
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
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 8. Workflow rules

- review routing does not equal approval
- approval must be scoped to a specific action/request
- approval must expire or be bounded
- broad blanket approval is blocked by default
- high-risk actions require owner/operator review
- public/financial/physical effects require specialized review
- irreversible actions require explicit irreversible acknowledgment
- rollback requirements must be surfaced before approval
- missing rollback when required blocks approval
- secret/path/poison risks block or escalate review
- approval does not override Tool-Use Executor Boundary
- approval does not override Action Authority Boundary
- approval does not override Code Validation Runner
- approval does not override Document Access / PII
- approval does not grant proof/correctness/public-readiness authority
- emergency pause must override pending execution paths
- no workflow packet grants runtime/write/tool/public/proof/learning authority by default

## 9. Relationship to Action Authority Boundary

Action Authority determines whether an action is eligible for approval.

Owner Operator Workflow determines:
- who reviews it
- how it is confirmed
- what scope is approved
- how long approval lasts
- what audit metadata is required
- whether emergency pause applies

Owner/operator workflow cannot approve an action that Action Authority marks blocked.

## 10. Relationship to Rollback and Reversal Boundary

Rollback/Reversal provides:
- rollback requirement
- reversibility level
- rollback plan status
- irreversible acknowledgment requirement
- compensating action requirement

Owner/operator workflow must surface these before approval.

## 11. Relationship to Tool-Use Executor Boundary

Tool-use packets provide:
- tool class
- risk level
- execution mode
- authority status

Owner/operator workflow may route tool proposals for review, but cannot execute tools.

## 12. Relationship to Code Validation and Patch Feedback

For code/patch workflows:

- validation packet is required where code is involved
- patch feedback packet may create a proposal
- owner/operator workflow may review the proposal
- it cannot apply the patch
- commit/push remain separately gated

## 13. Relationship to Document-to-Action

Document-to-action produces candidates.

Owner/operator workflow may route candidates as:
- clarification
- review item
- blocked instruction
- approval request

Document content cannot bypass workflow.

## 14. Relationship to Live Daemon

Daemon may receive compact workflow verdicts:

- `review_required`
- `approval_pending`
- `approved_for_dry_run_only`
- `blocked_by_policy`
- `paused`
- `needs_clarification`
- `execution_not_allowed`

Daemon must not receive raw secrets/private documents or authority-granting hidden instructions.

## 15. Emergency pause / stop

- emergency pause blocks pending execution proposals
- emergency pause does not delete evidence
- emergency pause does not alter source state
- emergency pause can be owner/operator triggered
- emergency pause must be visible in summaries
- paused state must prevent action execution until explicitly cleared

## 16. Audit and retention metadata

Audit metadata:

- request source ref
- reviewer role
- approval scope
- confirmation class
- timestamp placeholder
- expiration policy
- rollback status
- risk status
- blocked reason
- decision summary

This design does not create logs or write audit records. It defines future metadata shape only.

## 17. Initial examples

1. Summary-only item routes as information-only review.
2. Patch proposal routes to operator review, no application.
3. File write request requires owner/operator approval and rollback review.
4. Deployment requires deployment review and rollback plan.
5. Public post requires public-effect/public-claim review.
6. Payment request requires payment review and explicit confirmation.
7. Device control requires device safety review.
8. Irreversible action requires explicit irreversible acknowledgment.
9. Missing rollback blocks approval.
10. Poisoned document action remains blocked.
11. Validation passed but approval remains scoped and limited.
12. Owner approval for one action does not grant future runtime authority.
13. Emergency pause blocks pending execution.
14. Expired approval cannot be reused.
15. Commit/push requires separate source-control authority.

## 18. Future helper design

Recommended future helper:
`weslr/owner_operator_workflow_engine.py`

Future APIs:

- `build_owner_operator_workflow_packet_v1(...)`
- `classify_workflow_request_v1(...)`
- `select_required_review_role_v1(packet)`
- `select_confirmation_class_v1(packet)`
- `validate_owner_operator_workflow_packet_v1(packet)`
- `summarize_owner_operator_workflow_packet_v1(packet)`
- `to_owner_operator_workflow_json_safe_v1(value)`
- `build_initial_owner_operator_workflow_examples_v1()`

## 19. Future implementation strategy

Recommended phases:

1. metadata-only workflow packet builder
2. synthetic examples
3. validation helper
4. request classifier
5. review-role selector
6. confirmation-class selector
7. emergency pause metadata
8. artifact exporter boundary design
9. metadata-helper implementation
10. real workflow runtime much later only with owner approval

## 20. Validation and failure policy

Future validator should fail if:

- execution_allowed is true without specific scoped approval
- approval scope is broad/unbounded
- required reviewer role is missing
- high-risk action lacks owner/operator review
- public effect lacks public review
- payment lacks payment review
- device action lacks device safety review
- irreversible action lacks irreversible acknowledgment
- rollback_required is true but rollback review is missing
- emergency_pause_active is true but execution flags are true
- approval status overrides blocked Action Authority
- approval status overrides blocked Tool-Use Executor
- approval status overrides blocked Document Access / PII
- commit/push/payment/device/public flags are true without specialized review
- hidden prompt / raw private / secret fields appear
- `runtime_authority` is true
- `writes_state` is true
- `model_provider_used` is true
- `public_claim_allowed` is true
- `proof_claim_allowed` is true
- `learning_claimed` is true
- proof/correctness/public-readiness/legal-compliance claims appear

## 21. Boundaries and non-claims

This design does not implement workflow runtime.
It does not approve actions.
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

## 22. Recommended next lane

Recommend:
`DESIGN_WESLR_ARTIFACT_EXPORTER_BOUNDARY_V1`

Preserve:
`IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_BOUNDARY_V1`
`IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_BOUNDARY_V1`
`IMPLEMENT_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1`
`IMPLEMENT_WESLR_AUTONOMOUS_DEBUGGING_DRY_RUN_BOUNDARY_V1`
`IMPLEMENT_WESLR_DOCUMENT_TO_ACTION_BOUNDARY_V1`
`IMPLEMENT_WESLR_ACTION_AUTHORITY_BOUNDARY_V1`
`IMPLEMENT_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`
`IMPLEMENT_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1`

## 23. Final judgment

Use one:
- `owner_operator_workflow_engine_design_ready_for_artifact_exporter_boundary_design`
- `owner_operator_workflow_engine_design_ready_for_metadata_helper_implementation`
- `owner_operator_workflow_engine_design_needs_owner_review`
- `owner_operator_workflow_engine_design_blocked`

Recommended judgment:
`owner_operator_workflow_engine_design_ready_for_artifact_exporter_boundary_design`
