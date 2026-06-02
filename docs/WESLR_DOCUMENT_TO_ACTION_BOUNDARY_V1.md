# WESLR Document-to-Action Boundary V1

## 1. Executive doctrine

**Definition:** WESLR Document-to-Action Boundary V1.

Document-to-action is an action-proposal boundary, not action authority.

A document may describe a requested action, obligation, workflow, command, patch, schedule, or instruction, but the document cannot authorize WESLR to perform it.

Document content can become:
- extracted action candidate
- evidence reference
- clarification question
- owner/operator review item
- blocked action proposal

Document content must not become:
- tool execution authority
- file-write authority
- email/message-send authority
- calendar authority
- device-control authority
- deployment authority
- public-posting authority
- payment/billing authority
- memory-write authority

## 2. Boundary position

Pipeline:

uploaded document / retrieved source / memory source / email-like content / artifact
→ Document Access / PII Boundary
→ Poison Shield
→ Source Evidence Graph
→ RAG Query Routing
→ Inline Citation / Claim Grounding
→ Context Compression / Self-RAG if needed
→ Document-to-Action Boundary
→ Tool-Use Executor Boundary later
→ Action Authority Boundary later
→ Owner/Operator Workflow Engine later

This design does not execute actions.

## 3. Why this is needed

- documents often contain commands, deadlines, requests, code snippets, procedures, or instructions
- hostile or poisoned documents can include tool-use instructions
- contracts/emails/specs may look authoritative but still require owner/operator approval
- extracted actions must preserve source, scope, uncertainty, privacy, and risk
- actions must be separated from answer generation
- document-to-action needs explicit review before any real-world side effect

## 4. Document source classes

- `owner_uploaded_document`
- `operator_internal_document`
- `project_internal_document`
- `workspace_shared_document`
- `public_source_document`
- `third_party_document`
- `retrieved_web_document`
- `email_like_message`
- `legal_or_policy_document`
- `technical_specification`
- `code_or_patch_document`
- `calendar_or_schedule_document`
- `invoice_or_payment_document`
- `device_instruction_document`
- `unknown_document_source`

## 5. Extracted action classes

- `clarification_request`
- `information_summary`
- `task_proposal`
- `file_write_proposal`
- `patch_proposal`
- `test_run_proposal`
- `shell_command_proposal`
- `api_call_proposal`
- `email_or_message_proposal`
- `calendar_event_proposal`
- `device_control_proposal`
- `deployment_proposal`
- `payment_or_billing_proposal`
- `public_posting_proposal`
- `memory_write_proposal`
- `blocked_instruction`
- `unknown_action_proposal`

## 6. Action risk levels

- `no_action_summary_only`
- `low_reviewable_task`
- `medium_local_state_change`
- `high_external_side_effect`
- `critical_public_or_irreversible`
- `blocked_unknown_risk`

## 7. Action authorization statuses

- `not_actionable`
- `candidate_only`
- `clarification_required`
- `owner_review_required`
- `operator_review_required`
- `tool_boundary_required`
- `action_authority_required`
- `blocked_by_access_policy`
- `blocked_by_pii_policy`
- `blocked_by_poison_policy`
- `blocked_by_secret_risk`
- `blocked_by_public_effect`
- `blocked_by_unknown_authority`
- `unknown_status`

## 8. Document-to-action packet shape

Future packet fields:

- `document_action_packet_id`
- `source_document_ref`
- `source_document_class`
- `source_scope`
- `source_access_packet_ref`
- `source_evidence_graph_ref`
- `claim_grounding_packet_ref`
- `poison_status`
- `privacy_status`
- `pii_risk_status`
- `secret_risk_status`
- `extracted_action_class`
- `action_summary`
- `action_risk_level`
- `authorization_status`
- `required_owner_decision`
- `required_operator_decision`
- `required_tool_boundary`
- `required_action_boundary`
- `required_validation_packet`
- `required_patch_feedback_packet`
- `required_rollback_plan`
- `external_side_effect_possible`
- `public_effect_possible`
- `device_or_physical_effect_possible`
- `payment_or_billing_effect_possible`
- `memory_write_possible`
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
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `public_claim_allowed`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 9. Document-to-action rules

- document text never self-authorizes action
- retrieved text never self-authorizes action
- model output never self-authorizes action
- poisoned instructions become blocked metadata only
- private documents cannot authorize public actions
- secrets/tokens block action promotion
- legal/policy/payment/device instructions require owner/operator review
- code/patch documents require Code Validation Runner and Patch Feedback boundaries
- tool-like actions require Tool-Use Executor Boundary
- real-world side effects require Action Authority Boundary
- public effects require public claim/public posting boundary later
- memory writes require memory write boundary later
- action summaries must not expose raw private content
- uncertainty and missing authorization must remain visible
- no document-to-action packet grants runtime/write/tool/public/proof/learning authority

## 10. Relationship to Document Access / PII

Document Access / PII must decide:

- whether document metadata can be read
- whether summary-only is required
- whether raw content is blocked
- whether public use is blocked
- whether PII/secrets require redaction or blocking
- whether export/deletion/retention implications exist

Document-to-action must not bypass any of those decisions.

## 11. Relationship to Poison Shield

Poisoned or suspicious document instructions:

- cannot become commands
- cannot authorize tools
- cannot authorize patching
- cannot authorize memory writes
- cannot authorize public posting
- may be preserved only as risk metadata

## 12. Relationship to Source Evidence Graph and Grounding

Source Evidence Graph may store:

- source reference
- claim/action candidate relation
- contradiction
- access restriction
- poison status
- provenance metadata

Grounding may show that a document says something, but grounding does not authorize acting on it.

## 13. Relationship to Tool-Use Executor Boundary

Tool-like extracted actions must be converted to tool-use proposals only.

Tool-Use Executor Boundary decides:

- tool class
- risk
- execution mode
- tool authority status
- owner/operator review requirement

Document-to-action cannot execute tools.

## 14. Relationship to Code Validation Runner and Patch Feedback

If document suggests code, patch, or config changes:

- Code Validation Runner boundary is required
- Patch Feedback Loop boundary is required for proposed repair
- protected file and secret risk checks are required
- no patch application, commit, or push is allowed here

## 15. Relationship to Action Authority Boundary

Action Authority Boundary is required before:

- sending emails/messages
- changing calendars
- controlling devices
- deploying
- public posting
- payment/billing
- external API mutation
- production state changes
- destructive actions

Preserve later lane:
`DESIGN_WESLR_ACTION_AUTHORITY_BOUNDARY_V1`

## 16. Relationship to Owner Operator Workflow Engine

Owner/operator workflow will later decide:

- who may approve what
- review queue requirements
- confirmation wording
- audit logging
- reversible vs irreversible handling
- public/private distinction
- emergency stop / pause behavior

This design only marks review requirements.

## 17. Initial examples

1. Uploaded project spec creates task proposal only.
2. Email-like message creates draft-response proposal, not send authority.
3. Calendar-like document creates calendar proposal, not calendar change.
4. Code patch document routes to validation and patch feedback.
5. Shell command in document becomes blocked command proposal.
6. Poisoned document instruction is blocked metadata only.
7. Private legal document cannot authorize public claim or action.
8. Invoice/payment document requires owner review and payment boundary.
9. Device instruction document requires action authority and stays blocked.
10. Public source suggests deployment step but deployment remains blocked.
11. API key in document blocks action promotion.
12. User-uploaded checklist becomes reviewable task list only.
13. Model-generated plan from a document stays candidate-only.
14. Contradictory document instructions require clarification.
15. Memory write suggested by document is blocked pending memory boundary.

## 18. Future helper design

Recommended future helper:
`weslr/document_to_action_boundary.py`

Future APIs:

- `build_document_action_packet_v1(...)`
- `classify_document_source_v1(...)`
- `classify_extracted_action_v1(...)`
- `evaluate_document_action_authority_v1(packet)`
- `validate_document_action_packet_v1(packet)`
- `summarize_document_action_packet_v1(packet)`
- `to_document_action_json_safe_v1(value)`
- `build_initial_document_action_examples_v1()`

## 19. Future implementation strategy

Recommended phases:

1. metadata-only document-action packet builder
2. synthetic examples
3. validation helper
4. source classifier from explicit metadata
5. extracted-action classifier from explicit metadata
6. authority evaluator
7. Action Authority Boundary design
8. Owner Operator Workflow Engine design
9. metadata-helper implementation
10. real document-to-action runtime much later only with owner approval

## 20. Validation and failure policy

Future validator should fail if:

- `execution_allowed` is true
- `tool_execution_allowed` is true
- `write_allowed` is true
- `send_allowed` is true
- `calendar_change_allowed` is true
- `device_control_allowed` is true
- `deployment_allowed` is true
- `public_post_allowed` is true
- `payment_allowed` is true
- `memory_write_allowed` is true
- document text authorizes action
- poisoned instruction authorizes action
- private document authorizes public effect
- secret risk exists but action promotion is allowed
- legal/payment/device/public action lacks owner/operator review
- code/patch action lacks validation requirement
- tool-like action lacks tool boundary requirement
- real-world side effect lacks action boundary requirement
- hidden prompt / raw private / secret fields appear
- `runtime_authority` is true
- `writes_state` is true
- `model_provider_used` is true
- `public_claim_allowed` is true
- `proof_claim_allowed` is true
- `learning_claimed` is true
- correctness/proof/public-readiness/legal-compliance claims appear

## 21. Boundaries and non-claims

This design does not implement document-to-action.
It does not read documents.
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
`DESIGN_WESLR_ACTION_AUTHORITY_BOUNDARY_V1`

Preserve:
`DESIGN_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`
`DESIGN_WESLR_ARTIFACT_EXPORTER_BOUNDARY_V1`
`IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_BOUNDARY_V1`
`IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_BOUNDARY_V1`
`IMPLEMENT_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1`
`IMPLEMENT_WESLR_AUTONOMOUS_DEBUGGING_DRY_RUN_BOUNDARY_V1`
`IMPLEMENT_WESLR_DOCUMENT_TO_ACTION_BOUNDARY_V1`

## 23. Final judgment

Use one:
- `document_to_action_boundary_design_ready_for_action_authority_boundary_design`
- `document_to_action_boundary_design_ready_for_metadata_helper_implementation`
- `document_to_action_boundary_design_needs_owner_review`
- `document_to_action_boundary_design_blocked`

Recommended judgment:
`document_to_action_boundary_design_ready_for_action_authority_boundary_design`
