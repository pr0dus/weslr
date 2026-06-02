# WESLR Rollback and Reversal Boundary V1

## 1. Executive doctrine

**Definition:** WESLR Rollback and Reversal Boundary V1.

Rollback/reversal is a recovery-planning boundary for future state-changing actions. It is not execution authority. It is not correctness authority. It is not proof that an action is safe.

Any future action that can change files, state, external systems, public surfaces, devices, databases, accounts, payments, deployments, memory, or user-visible outputs must either have a rollback/reversal plan or be explicitly marked irreversible and blocked until owner/operator approval.

## 2. Boundary position

Pipeline:

action proposal
→ Document-to-Action Boundary
→ Tool-Use Executor Boundary
→ Code Validation Runner / Patch Feedback where needed
→ Action Authority Boundary
→ Rollback and Reversal Boundary
→ Owner/Operator Workflow Engine later
→ executor/sandbox/connector later only if approved

This design does not execute rollback.

## 3. Reversal target classes

- `file_change`
- `patch_application`
- `generated_artifact`
- `artifact_export`
- `database_mutation`
- `configuration_change`
- `deployment_change`
- `git_commit`
- `git_push`
- `memory_write`
- `email_or_message_send`
- `calendar_change`
- `device_control`
- `public_post`
- `payment_or_billing`
- `account_or_permission_change`
- `external_api_mutation`
- `unknown_reversal_target`

## 4. Reversibility levels

- `fully_reversible`
- `partially_reversible`
- `compensating_action_only`
- `irreversible`
- `reversibility_unknown`
- `blocked_until_classified`

## 5. Rollback plan statuses

- `not_required_metadata_only`
- `required_missing`
- `draft_plan_present`
- `validated_plan_present`
- `owner_review_required`
- `operator_review_required`
- `blocked_missing_plan`
- `blocked_irreversible_without_acknowledgment`
- `blocked_unknown_reversibility`
- `unknown_status`

## 6. Rollback action classes

- `restore_previous_file`
- `reverse_patch`
- `restore_manifest`
- `restore_artifact_version`
- `database_restore`
- `configuration_restore`
- `deployment_rollback`
- `git_revert_proposal`
- `memory_delete_or_revert`
- `calendar_event_revert`
- `device_state_restore`
- `public_post_retract_or_correction`
- `payment_refund_or_manual_review`
- `account_permission_restore`
- `external_api_compensating_action`
- `no_safe_rollback_available`
- `unknown_rollback_action`

## 7. Rollback packet shape

Future packet fields:

- `rollback_packet_id`
- `action_authority_packet_ref`
- `tool_use_packet_ref`
- `document_action_packet_ref`
- `patch_feedback_packet_ref`
- `validation_packet_ref`
- `artifact_provenance_ref`
- `target_class`
- `target_summary`
- `reversibility_level`
- `rollback_plan_status`
- `rollback_action_class`
- `rollback_summary`
- `before_state_ref`
- `after_state_ref`
- `diff_summary_ref`
- `manifest_ref`
- `backup_ref`
- `audit_log_required`
- `owner_review_required`
- `operator_review_required`
- `explicit_irreversible_ack_required`
- `reversal_test_required`
- `validation_rerun_required`
- `rollback_execution_allowed`
- `original_action_allowed`
- `compensating_action_required`
- `public_correction_required`
- `external_notification_required`
- `retention_or_deletion_implication`
- `privacy_or_pii_implication`
- `secret_risk_status`
- `path_risk_status`
- `network_policy_status`
- `financial_effect_possible`
- `physical_effect_possible`
- `public_effect_possible`
- `irreversible_effect_possible`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 8. Rollback rules

- metadata-only actions may not require rollback
- file writes require previous-state or diff metadata before execution
- patch application requires reverse-patch or restore plan
- deployment requires rollback strategy and owner/operator review
- database mutations require backup/restore or compensating action policy
- config changes require previous config reference
- device actions require safe-state or manual recovery plan
- public posts require correction/retraction policy
- payments require refund/manual review policy
- memory writes require deletion/reversal boundary later
- git commit/push require source-control rollback policy
- irreversible actions require explicit irreversible acknowledgment and are blocked by default
- unknown reversibility is blocked
- rollback plan presence does not authorize execution
- rollback execution itself is also an action and requires authority
- no rollback packet grants runtime/write/tool/public/proof/learning authority

## 9. Relationship to Action Authority Boundary

Action Authority decides whether an action can become approval-eligible.

Rollback/Reversal decides whether the action has:
- a recovery plan
- a before/after state model
- explicit irreversible acknowledgment
- owner/operator review needs
- compensating action requirements

Action Authority cannot bypass missing rollback when rollback is required.

## 10. Relationship to Tool-Use Executor Boundary

Tool-use packets may indicate tool class/risk/execution mode.

Rollback boundary must evaluate whether tool action has:
- state change
- public effect
- external side effect
- financial/physical effect
- reversible path

Tool execution remains blocked here.

## 11. Relationship to Code Validation Runner and Patch Feedback

For code/patch changes:

- validation packet ref is required where code is involved
- patch feedback packet ref is required where patch proposal is involved
- reverse patch or before-state reference is required before future patch application
- validation rerun is required after any future rollback or patch application
- passing validation does not prove correctness

## 12. Relationship to Artifact Provenance and Export

Artifacts need provenance before export.

Rollback boundary should preserve:
- generated artifact version
- manifest
- export path summary
- previous artifact ref
- replacement/retraction policy

Artifact export remains blocked until exporter boundary exists.

## 13. Relationship to Document Access / PII and Poison Shield

If action or rollback plan is document-derived:

- document access/PII policy must be preserved
- poisoned content cannot authorize rollback or action
- secrets/tokens must block promotion
- private content must not leak into rollback summaries
- deletion/export/retention implications must be flagged

## 14. Relationship to Owner Operator Workflow Engine

Owner/operator workflow will later define:

- who approves rollback plans
- who acknowledges irreversible actions
- emergency stop/pause
- rollback review queue
- audit retention
- two-person review for high risk
- public/private approval split

This design only marks requirements.

## 15. Initial examples

1. Metadata-only summary requires no rollback.
2. File write requires previous-state reference.
3. Patch application requires reverse-patch plan and validation rerun.
4. Deployment requires rollback plan and owner/operator review.
5. Database mutation blocks without backup/restore policy.
6. Config change requires previous config reference.
7. Device action requires safe-state recovery plan.
8. Public post requires correction/retraction path.
9. Payment action requires manual review/refund path and stays blocked.
10. Git push is blocked without source-control rollback policy.
11. Memory write requires memory deletion/reversal boundary.
12. Artifact export requires manifest/provenance and retraction policy.
13. Irreversible action is blocked without explicit acknowledgment.
14. Unknown reversibility blocks action.
15. Rollback plan exists but does not authorize original action.

## 16. Future helper design

Recommended future helper:
`weslr/rollback_reversal_boundary.py`

Future APIs:

- `build_rollback_packet_v1(...)`
- `classify_reversal_target_v1(...)`
- `evaluate_reversibility_v1(packet)`
- `select_rollback_action_v1(packet)`
- `validate_rollback_packet_v1(packet)`
- `summarize_rollback_packet_v1(packet)`
- `to_rollback_json_safe_v1(value)`
- `build_initial_rollback_examples_v1()`

## 17. Future implementation strategy

Recommended phases:

1. metadata-only rollback packet builder
2. synthetic examples
3. validation helper
4. target classifier
5. reversibility evaluator
6. rollback action selector
7. owner/operator workflow engine design
8. artifact exporter boundary design
9. metadata-helper implementation
10. real rollback execution much later only with owner approval

## 18. Validation and failure policy

Future validator should fail if:

- original_action_allowed is true while rollback is required but missing
- rollback_execution_allowed is true
- writes_state is true
- runtime_authority is true
- model_provider_used is true
- public_claim_allowed is true
- proof_claim_allowed is true
- learning_claimed is true
- irreversible action lacks explicit acknowledgment
- unknown reversibility is treated as allowed
- file write lacks before-state/diff reference
- patch apply lacks reverse-patch or restore plan
- deployment lacks rollback plan
- database mutation lacks backup/restore or compensating action
- public post lacks correction/retraction path
- payment lacks manual review/refund path
- device action lacks safe-state plan
- private/secret/raw fields appear
- poisoned source authorizes rollback/action
- proof/correctness/public-readiness/legal-compliance claims appear

## 19. Boundaries and non-claims

This design does not implement rollback.
It does not execute rollback.
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
`DESIGN_WESLR_OWNER_OPERATOR_WORKFLOW_ENGINE_V1`

Preserve:
`DESIGN_WESLR_ARTIFACT_EXPORTER_BOUNDARY_V1`
`IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_BOUNDARY_V1`
`IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_BOUNDARY_V1`
`IMPLEMENT_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1`
`IMPLEMENT_WESLR_AUTONOMOUS_DEBUGGING_DRY_RUN_BOUNDARY_V1`
`IMPLEMENT_WESLR_DOCUMENT_TO_ACTION_BOUNDARY_V1`
`IMPLEMENT_WESLR_ACTION_AUTHORITY_BOUNDARY_V1`
`IMPLEMENT_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`

## 21. Final judgment

Use one:
- `rollback_reversal_boundary_design_ready_for_owner_operator_workflow_design`
- `rollback_reversal_boundary_design_ready_for_artifact_exporter_boundary_design`
- `rollback_reversal_boundary_design_ready_for_metadata_helper_implementation`
- `rollback_reversal_boundary_design_needs_owner_review`
- `rollback_reversal_boundary_design_blocked`

Recommended judgment:
`rollback_reversal_boundary_design_ready_for_owner_operator_workflow_design`
