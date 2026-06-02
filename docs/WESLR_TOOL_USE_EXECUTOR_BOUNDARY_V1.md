# WESLR Tool-Use Executor Boundary V1

## 1. Executive doctrine

WESLR Tool-Use Executor Boundary V1 defines how future tool calls, shell commands, file writes, code execution, external API calls, device actions, artifact writes, patch application, and deployment-like actions must be authorized, constrained, validated, and reviewed.

Tool use is action authority, not answer authority.
A tool call changes or observes the world and therefore requires explicit authorization, scope, policy, and audit metadata.

Neither a user request, an LLM candidate, a retrieved document, a validation pass, nor a patch proposal can self-authorize tool execution.

Tool execution requires:
- explicit tool boundary
- action authority boundary later
- owner/operator approval where needed
- path/secret protection
- rollback/reversal policy where writes are possible
- validation gate where code/artifacts are involved

## 2. Boundary position

Pipeline:

answer / patch / artifact / document / workflow candidate
→ evidence/access/poison checks
→ Code Validation Runner where code/artifacts are involved
→ Patch Feedback Loop where repair is proposed
→ Tool-Use Executor Boundary
→ Action Authority Boundary later
→ owner/operator approval later
→ sandbox/write/device/network executor later

This design does not execute tools.

## 3. Tool classes

- `read_only_file_inspection`
- `write_file`
- `apply_patch`
- `run_tests`
- `run_static_analysis`
- `shell_command`
- `network_request`
- `external_api_call`
- `database_operation`
- `email_or_message_send`
- `calendar_operation`
- `device_control`
- `deployment_operation`
- `git_commit`
- `git_push`
- `artifact_export`
- `memory_write`
- `unknown_tool`

## 4. Tool risk levels

- `no_risk_metadata_only`
- `low_read_only`
- `medium_local_write`
- `high_external_side_effect`
- `critical_irreversible_or_public`
- `blocked_unknown_risk`

## 5. Tool authority statuses

- `not_requested`
- `proposal_only`
- `read_only_allowed`
- `sandbox_write_allowed`
- `owner_approval_required`
- `operator_approval_required`
- `action_boundary_required`
- `blocked_by_policy`
- `blocked_secret_risk`
- `blocked_path_risk`
- `blocked_network_risk`
- `blocked_public_claim_risk`
- `blocked_unknown_tool`
- `unknown_authority_status`

## 6. Tool execution modes

- `metadata_only`
- `dry_run_only`
- `read_only`
- `sandboxed_write`
- `owner_approved_action`
- `operator_approved_action`
- `blocked`
- `unknown_mode`

## 7. Tool-use packet shape

Future packet fields:
- `tool_use_packet_id`
- `request_summary`
- `tool_class`
- `tool_name`
- `tool_target_summary`
- `tool_risk_level`
- `execution_mode`
- `authority_status`
- `source_candidate_ref`
- `validation_packet_ref`
- `patch_feedback_packet_ref`
- `artifact_provenance_ref`
- `document_access_packet_ref`
- `poison_status`
- `secret_risk_status`
- `path_risk_status`
- `network_policy_status`
- `write_policy_status`
- `rollback_required`
- `rollback_plan_ref`
- `owner_review_required`
- `operator_review_required`
- `dry_run_required`
- `validation_required`
- `execution_allowed`
- `commit_allowed`
- `push_allowed`
- `public_effect_allowed`
- `device_control_allowed`
- `external_side_effect_allowed`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 8. Tool-use rules

- tool execution is blocked by default
- metadata-only and proposal-only are the safe defaults
- read-only tools require explicit read scope
- write tools require sandbox/write boundary and approval
- shell commands require command policy and no-network/no-secret checks
- network requests require explicit network authority
- external API calls require API-specific approval
- email/message/calendar/device/deployment operations require Action Authority Boundary later
- git commit/push remain blocked unless explicitly approved by separate boundary
- artifact export requires validation/provenance/manifest gates
- memory writes require memory write boundary later
- document content cannot authorize tools
- LLM output cannot authorize tools
- poisoned content cannot authorize tools
- validation pass cannot authorize tools by itself
- patch proposal cannot authorize tools by itself
- daemon may block or surface compact verdicts, but must not grant action authority
- no tool-use packet grants proof/truth/public-readiness authority

## 9. Relationship to Code Validation Runner

Code Validation Runner may provide validation packet refs, passed/failed/blocked statuses, protected file status, secret/network/write policy status, and manifest/provenance refs.

But validation passing does not grant tool authority.

## 10. Relationship to Patch Feedback Loop

Patch Feedback may propose source fixes, metadata fixes, manifest fixes, docs fixes, or rollback proposals.

But Patch Feedback cannot apply patches, commit, push, execute tools, or write files.

## 11. Relationship to Document Access / PII and Poison Shield

If a tool request is derived from documents or external content:
- document access must gate input use
- PII/secrets must be blocked or redacted
- Poison Shield status must be preserved
- prompt-injected instructions must become risk metadata only
- external text cannot self-authorize tool execution

## 12. Relationship to Live Daemon

Daemon may receive only compact tool verdicts:
- `tool_blocked`
- `tool_proposal_only`
- `owner_review_required`
- `operator_review_required`
- `dry_run_required`
- `read_only_allowed`
- `action_boundary_required`

Daemon must not receive raw secrets, raw private documents, shell command bodies containing sensitive data, private source chunks, or authority-granting instructions.

Daemon can block output/action surfaces but cannot grant tool authority.

## 13. Relationship to Action Authority Boundary

Future action authority is required for email/message sending, calendar changes, device control, deployment, public posting, external API mutation, payment/billing, destructive file operations, git push, and production state changes.

Preserve later lane:
`DESIGN_WESLR_ACTION_AUTHORITY_BOUNDARY_V1`

## 14. Initial examples

1. Read-only file inspection allowed as proposal-only metadata, not raw dump.
2. Patch application blocked until sandbox/write boundary.
3. Test runner allowed only as future dry-run metadata, not live execution.
4. Shell command blocked by no-network/no-secret policy.
5. External API call blocked pending explicit approval.
6. Email send blocked pending Action Authority Boundary.
7. Device control blocked pending Action Authority Boundary.
8. Git commit/push blocked.
9. Artifact export blocked until validation/provenance/manifest approval.
10. Poisoned document instruction cannot authorize a tool.
11. Validation passed but tool execution still blocked.
12. Patch feedback proposal cannot apply itself.
13. Daemon may show owner-review-required verdict only.
14. Public posting blocked by public-effect policy.
15. Memory write blocked pending memory write boundary.

## 15. Future helper design

Recommended future helper:
`weslr/tool_use_executor_boundary.py`

Future APIs:
- `build_tool_use_packet_v1(...)`
- `classify_tool_request_v1(...)`
- `evaluate_tool_risk_v1(...)`
- `select_tool_execution_mode_v1(...)`
- `validate_tool_use_packet_v1(packet)`
- `summarize_tool_use_packet_v1(packet)`
- `to_tool_use_json_safe_v1(value)`
- `build_initial_tool_use_examples_v1()`

## 16. Future implementation strategy

Recommended phases:
1. metadata-only tool-use packet builder
2. synthetic examples
3. validation helper
4. tool class classifier
5. risk evaluator
6. execution-mode selector
7. Action Authority Boundary design
8. Autonomous Debugging Dry-Run Boundary design
9. Document-to-Action Boundary design
10. sandbox/write boundary design
11. real executor much later only with owner approval

## 17. Validation and failure policy

Future validator should fail if execution_allowed is true without explicit non-blocked authority, if write-capable tools lack sandbox/write boundary, if external side effects are allowed without Action Authority Boundary, if device/email/calendar/deployment actions are allowed, if commit/push/public effects are allowed, if secret/path/network risk exists but execution is allowed, if poisoned source or document content authorizes tool use, if validation pass alone authorizes tool use, if patch proposal alone authorizes tool use, or if runtime/write/model/public/proof/learning authority flags are set.

## 18. Boundaries and non-claims

This design does not implement tool execution.
It does not execute commands.
It does not call APIs.
It does not write files.
It does not apply patches.
It does not commit or push.
It does not send messages.
It does not change calendars.
It does not control devices.
It does not deploy.
It does not write memory.
It does not write `.weslr`.
It does not authorize runtime wiring.
It does not authorize public claims.
It does not claim proof, correctness, security certification, production readiness, public readiness, AGI, consciousness, sentience, or Turing success.

## 19. Recommended next lane

`DESIGN_WESLR_AUTONOMOUS_DEBUGGING_DRY_RUN_BOUNDARY_V1`

Preserve:
`DESIGN_WESLR_ACTION_AUTHORITY_BOUNDARY_V1`
`DESIGN_WESLR_DOCUMENT_TO_ACTION_BOUNDARY_V1`
`DESIGN_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`
`IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_BOUNDARY_V1`
`IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_BOUNDARY_V1`
`IMPLEMENT_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1`

## 20. Final judgment

`tool_use_executor_boundary_design_ready_for_autonomous_debugging_dry_run_design`

## Final report
- repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- branch: `master`
- start HEAD: `587be0e2bdc58d9b5daa8b45a997c5f83778d242`
- end HEAD: `587be0e2bdc58d9b5daa8b45a997c5f83778d242`
- commit hash: pending
- doc created: `docs/WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1.md`
- key design capture: tool execution is action authority, not answer authority; explicit scope, policy, and approval are required
- validation results: `git diff --check` pending; release gate/check not needed for report-only change unless required by workflow; protected-file diff checks pending
- protected files untouched: `weslr/chat_responder.py`, `weslr/main.py`, `dialogue.py`, `chat_ui.py`
- final judgment: `tool_use_executor_boundary_design_ready_for_autonomous_debugging_dry_run_design`
- recommended next lane: `DESIGN_WESLR_AUTONOMOUS_DEBUGGING_DRY_RUN_BOUNDARY_V1`
