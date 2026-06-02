# WESLR Patch Feedback Loop V1

## 1. Executive doctrine

WESLR Patch Feedback Loop V1 converts validation results into bounded patch proposals.

It is **not** autonomous mutation authority.
It is **not** commit authority.
It is **not** push authority.
It is **not** proof/correctness authority.

Core rule:
A failed validation result may justify a proposed patch, but not an automatic file change.

A generated patch proposal remains proposal-only until later boundaries approve:
- sandbox/write authority
- owner/operator approval
- rollback/reversal plan
- validation rerun
- commit/push authority if ever separately approved

## 2. Boundary position

Pipeline:

Code Validation Runner result packet
→ Patch Feedback Loop boundary
→ patch proposal packet
→ owner/operator approval later
→ sandbox/write boundary later
→ validation rerun later
→ artifact/export/tool-use only if separately approved

This design does not modify files.

## 3. Why WESLR needs this

- validation failures need a structured response path
- patch generation without limits can damage code
- repeated patch loops can create instability
- failed checks should become reviewable proposals, not autonomous edits
- protected files need strict handling
- secrets/path risks must block promotion
- patch retries need bounded budgets
- rollback/reversal metadata must exist before any write-capable loop
- validation reruns are required after future patch application
- tests passing after a patch still do not prove correctness

## 4. Patch input classes

- `syntax_failure`
- `unit_test_failure`
- `focused_test_failure`
- `integration_test_failure`
- `release_gate_failure`
- `release_check_failure`
- `static_analysis_warning`
- `manifest_missing`
- `manifest_mismatch`
- `protected_file_diff`
- `secret_risk`
- `network_policy_block`
- `write_policy_block`
- `provenance_missing`
- `rollback_plan_missing`
- `unknown_validation_failure`

## 5. Patch proposal types

- `no_patch_needed`
- `metadata_fix_proposal`
- `test_fix_proposal`
- `source_fix_proposal`
- `manifest_fix_proposal`
- `docs_fix_proposal`
- `policy_fix_proposal`
- `rollback_proposal`
- `defer_to_owner_review`
- `defer_to_operator_review`
- `blocked_no_safe_patch`
- `unknown_patch_proposal`

## 6. Patch attempt statuses

- `not_attempted`
- `proposal_created`
- `proposal_blocked`
- `proposal_needs_owner_review`
- `proposal_needs_operator_review`
- `retry_budget_available`
- `retry_budget_exhausted`
- `rollback_required`
- `blocked_protected_file`
- `blocked_secret_risk`
- `blocked_network_policy`
- `blocked_write_policy`
- `blocked_missing_rollback`
- `blocked_missing_provenance`
- `unknown_status`

## 7. Patch feedback packet shape

Future packet fields:
- `patch_feedback_packet_id`
- `validation_packet_ref`
- `candidate_source_ref`
- `artifact_provenance_ref`
- `file_manifest_ref`
- `failure_class`
- `failed_check_refs`
- `warning_refs`
- `proposal_type`
- `proposal_summary`
- `affected_path_summaries`
- `protected_file_status`
- `secret_risk_status`
- `network_policy_status`
- `write_policy_status`
- `provenance_status`
- `retry_count`
- `max_retries`
- `retry_allowed`
- `repeated_failure_detected`
- `rollback_required`
- `rollback_plan_ref`
- `owner_review_required`
- `operator_review_required`
- `patch_apply_allowed`
- `commit_allowed`
- `push_allowed`
- `validation_rerun_required`
- `artifact_export_allowed`
- `tool_execution_allowed`
- `public_claim_allowed`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 8. Patch loop rules

- failed validation may create proposal metadata only
- patch application remains blocked until sandbox/write authority exists
- protected-file changes require owner/operator review
- secret risks block patch proposal promotion
- network/write policy blocks must not be bypassed
- retry count must be bounded
- repeated same failure must trigger stop/review
- rollback/reversal plan is required before any future write-capable loop
- validation rerun is required after any future patch application
- passing rerun does not prove correctness
- commit/push remains blocked unless separately approved
- patch proposals cannot grant runtime authority
- patch proposals cannot grant tool execution authority
- patch proposals cannot authorize public claims
- patch proposals cannot self-promote into behavior changes

## 9. Relationship to Code Validation Runner

Patch Feedback consumes validation packets.

It may use:
- validation status
- failed checks
- warnings
- protected file status
- secret/network/write policy status
- rollback requirement
- patch feedback allowed
- artifact provenance refs
- file manifest refs

It must not override validation policy.

If Code Validation says:
- `blocked_secret_risk` → Patch Feedback must block promotion
- `blocked_protected_file` → owner/operator review required
- `failed` → proposal-only patch may be created
- `passed` → no patch needed, but no proof/public claim granted
- `passed_with_warnings` → warning proposal may be created
- `blocked_missing_manifest` → manifest fix proposal may be created

## 10. Relationship to Rollback / Reversal

Every future write-capable patch loop requires:
- rollback plan
- affected file manifest
- before/after diff summary
- owner/operator approval
- validation rerun
- patch attempt count
- stop condition

This design does not implement rollback.

Preserve later lane:
`DESIGN_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`

## 11. Relationship to Tool-Use Executor

Patching is not tool execution authority.

Tool execution remains blocked until:
- Tool-Use Executor Boundary
- Action Authority Boundary
- owner/operator approval
- sandbox/write boundary
- path/secret protection
- runtime trust policy

Patch Feedback may inform future tool-use proposals, but cannot execute tools.

## 12. Relationship to Artifact Exporter

Artifact export must remain blocked unless:
- validation passed or allowed with warnings
- manifest exists
- provenance exists
- protected files are clean or approved
- secret risk is clear
- owner/operator approval exists where required

This design does not export artifacts.

Preserve later lane:
`DESIGN_WESLR_ARTIFACT_EXPORTER_BOUNDARY_V1`

## 13. Relationship to Poison Shield / Document Access / PII

If patch proposal came from external/document/model output:
- Poison Shield status must be preserved
- document access/PII must gate input use
- secrets/tokens must block promotion
- private content must not leak into patch summaries
- poisoned text must not self-authorize a patch
- retrieved document content cannot authorize action
- LLM output cannot authorize action

## 14. Relationship to Batch A

Batch A supplies:
- source evidence metadata
- document access / PII gating
- poison/access/freshness flags
- grounding/citation readiness
- context compression metadata
- Self-RAG evidence loop metadata

Batch A does not authorize:
- file writes
- patches
- commits
- pushes
- tool execution
- runtime wiring
- public claims

## 15. Initial examples

1. Unit test failure creates proposal-only source fix.
2. Syntax failure creates metadata-only patch proposal.
3. Protected file diff blocks patch proposal promotion.
4. Secret/API key risk blocks patch feedback.
5. Retry budget exhausted triggers operator review.
6. Same failure repeated twice triggers rollback/review.
7. Missing manifest creates manifest fix proposal.
8. Release gate failure creates validation rerun requirement.
9. Patch proposal does not allow commit/push.
10. Passing validation rerun still does not allow public claim.
11. Network policy block prevents patch loop escalation.
12. Write policy block prevents patch application.
13. Poisoned external suggestion is preserved as blocked metadata.
14. Owner review required for protected runtime path.
15. No patch needed when validation passed cleanly.

## 16. Future helper design

Recommended future helper:
`weslr/patch_feedback_loop_boundary.py`

Future APIs:
- `build_patch_feedback_packet_v1(...)`
- `classify_patch_failure_v1(...)`
- `select_patch_proposal_v1(...)`
- `evaluate_patch_retry_budget_v1(packet)`
- `validate_patch_feedback_packet_v1(packet)`
- `summarize_patch_feedback_packet_v1(packet)`
- `to_patch_feedback_json_safe_v1(value)`
- `build_initial_patch_feedback_examples_v1()`

## 17. Future implementation strategy

Recommended phases:
1. metadata-only patch feedback packet builder
2. synthetic examples
3. validation helper
4. failure classifier
5. proposal selector
6. retry-budget evaluator
7. repeated-failure detector
8. rollback/reversal boundary design
9. tool-use executor boundary design
10. sandbox/write boundary design
11. metadata-helper implementation
12. real patch loop later only with owner approval

## 18. Validation and failure policy

Future validator should fail if:
- `patch_apply_allowed` is true
- `commit_allowed` is true
- `push_allowed` is true
- `writes_state` is true
- `runtime_authority` is true
- `model_provider_used` is true
- `tool_execution_allowed` is true
- `public_claim_allowed` is true
- `proof_claim_allowed` is true
- `learning_claimed` is true
- secret risk exists but proposal is promoted
- protected file status is blocked but owner/operator review is false
- retry count exceeds max retries
- repeated failure exists but retry still allowed
- rollback required but no rollback plan ref exists
- validation rerun is not required after future patch application
- hidden prompt / raw private / secret fields appear
- correctness/proof/public-readiness claims appear

## 19. Boundaries and non-claims

This design does not implement patching.
It does not modify files.
It does not execute tools.
It does not run tests.
It does not call models/providers.
It does not call APIs.
It does not write memory.
It does not write `.weslr`.
It does not authorize commits.
It does not authorize pushes.
It does not authorize runtime wiring.
It does not authorize public claims.
It does not authorize tool execution.
It does not claim proof, correctness, security certification, production readiness, public readiness, AGI, consciousness, sentience, or Turing success.

## 20. Recommended next lane

`DESIGN_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1`

Preserve:
`IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_BOUNDARY_V1`
`IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_BOUNDARY_V1`
`DESIGN_WESLR_ROLLBACK_AND_REVERSAL_BOUNDARY_V1`

## 21. Final judgment

`patch_feedback_loop_design_ready_for_tool_use_executor_boundary_design`

## Final report
- repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- branch: `master`
- start HEAD: `bf0880ab3b437aa58780c0529377a865b7e90ba1`
- end HEAD: `bf0880ab3b437aa58780c0529377a865b7e90ba1`
- commit hash: pending
- doc created: `docs/WESLR_PATCH_FEEDBACK_LOOP_V1.md`
- key design capture: failed validation becomes bounded patch proposal metadata only; no autonomous mutation or commit/push authority
- validation results: `git diff --check` pending; release gate/check not needed for report-only change unless required by workflow; protected-file diff checks pending
- protected files untouched: `weslr/chat_responder.py`, `weslr/main.py`, `dialogue.py`, `chat_ui.py`
- final judgment: `patch_feedback_loop_design_ready_for_tool_use_executor_boundary_design`
- recommended next lane: `DESIGN_WESLR_TOOL_USE_EXECUTOR_BOUNDARY_V1`
