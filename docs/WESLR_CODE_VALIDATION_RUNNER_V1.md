# WESLR Code Validation Runner V1

## 1. Executive doctrine

WESLR Code Validation Runner V1 is a verification boundary for generated code, patches, artifacts, manifests, tests, and validation results before promotion.

It is **not** proof of correctness.
It is **not** public-readiness authority.
It is **not** tool-use authority.

Core rule:
A patch or artifact cannot be promoted merely because it was generated; it needs validation metadata, explicit scope, and owner/operator policy.

## 2. Boundary position

Pipeline:

artifact/code candidate
→ file manifest / provenance metadata
→ document access / poison checks if source-derived
→ Code Validation Runner boundary
→ validation result packet
→ Patch Feedback Loop later
→ Artifact Exporter later
→ Tool-Use Executor later only if approved

This design does not execute code.

## 3. Validation targets

- `python_module`
- `python_test`
- `markdown_doc`
- `json_artifact`
- `yaml_config`
- `html_css_js_static_site`
- `shell_script`
- `patch_diff`
- `file_manifest`
- `artifact_bundle`
- `unknown_target`

## 4. Validation modes

- `syntax_only`
- `unit_tests`
- `focused_tests`
- `integration_tests`
- `release_gate`
- `release_check`
- `static_analysis`
- `manifest_consistency`
- `provenance_check`
- `protected_file_diff_check`
- `secret_scan_metadata_only`
- `no_network_policy_check`
- `no_write_policy_check`
- `unknown_validation_mode`

## 5. Validation result statuses

- `not_run`
- `passed`
- `passed_with_warnings`
- `failed`
- `blocked_by_policy`
- `blocked_missing_runner`
- `blocked_missing_manifest`
- `blocked_protected_file`
- `blocked_secret_risk`
- `blocked_network_risk`
- `blocked_unknown_target`
- `unknown_status`

## 6. Validation packet shape

Future packet fields:
- `validation_packet_id`
- `target_id`
- `target_type`
- `target_path_summary`
- `candidate_source_ref`
- `artifact_provenance_ref`
- `file_manifest_ref`
- `validation_modes_requested`
- `validation_modes_completed`
- `validation_status`
- `validation_summary`
- `test_result_refs`
- `failed_check_refs`
- `warning_refs`
- `protected_file_diff_status`
- `secret_risk_status`
- `network_policy_status`
- `write_policy_status`
- `rollback_required`
- `patch_feedback_allowed`
- `artifact_export_allowed`
- `tool_execution_allowed`
- `public_claim_allowed`
- `owner_review_required`
- `operator_review_required`
- `recommended_next_check`
- `runtime_authority`
- `writes_state`
- `model_provider_used`
- `proof_claim_allowed`
- `learning_claimed`
- `safe_metadata`

## 7. Validation rules

- generated code must be validated before promotion
- passing tests do not prove correctness
- failed validation may create patch proposal metadata later, not automatic mutation
- protected-file changes require explicit boundary and approval
- secrets/tokens must block promotion
- network-requiring validation requires separate approval
- write-capable validation requires separate sandbox boundary
- validation results must link to artifact provenance
- missing manifest should block export/promotion
- public claims require later public claim lifecycle
- tool execution remains blocked

## 8. Relationship to Patch Feedback Loop

Validation results may feed:
- patch proposal
- retry count
- failure class
- rollback need
- owner/operator review

This design does not implement patching.

## 9. Relationship to Tool-Use Executor

Tool execution must not happen just because validation passed.

Tool execution requires:
- Tool-Use Executor Boundary
- Action Authority Boundary
- owner/operator approval
- trust level / surface policy

## 10. Relationship to Artifact Provenance

Validation packet must preserve:
- artifact provenance ref
- generator/source ref
- manifest ref
- changed file summary
- test/check refs

## 11. Relationship to Document Access / PII and Poison Shield

If candidate code came from documents, retrieved sources, or external content:
- document access must gate input use
- poison status must be preserved
- secrets must block validation promotion
- private source content must not leak into validation summary

## 12. Relationship to Batch A

Batch A evidence/grounding can support why a candidate exists.
Batch A does not authorize code promotion or tool execution.

## 13. Initial examples

1. Python module syntax passes but public claim remains blocked.
2. Python tests fail and patch feedback is allowed as proposal-only.
3. Protected file diff blocks promotion.
4. Secret/API key risk blocks validation promotion.
5. Missing manifest blocks artifact export.
6. Markdown doc passes policy check but no proof claim allowed.
7. Static site files pass validation but deployment remains blocked.
8. Shell script blocked by command execution policy.
9. Network-requiring validation blocked without approval.
10. Release gate/check passes but runtime wiring remains blocked.

## 14. Future helper design

Recommended future helper:
`weslr/code_validation_runner_boundary.py`

Future APIs:
- `build_code_validation_packet_v1(...)`
- `classify_validation_target_v1(...)`
- `select_validation_modes_v1(...)`
- `evaluate_validation_result_v1(packet)`
- `validate_code_validation_packet_v1(packet)`
- `summarize_code_validation_packet_v1(packet)`
- `to_code_validation_json_safe_v1(value)`
- `build_initial_code_validation_examples_v1()`

## 15. Future implementation strategy

Recommended phases:
1. metadata-only validation packet builder
2. synthetic examples
3. validation helper
4. target classifier
5. validation-mode selector
6. protected-file policy checks from metadata
7. secret/network/write policy checks from metadata
8. patch feedback loop design
9. artifact exporter boundary design
10. real runner boundary later with explicit approval

## 16. Boundaries and non-claims

This design does not implement a runner.
It does not execute code.
It does not run tests.
It does not call shell commands.
It does not call models/providers.
It does not write memory.
It does not write `.weslr`.
It does not authorize patching.
It does not authorize tool execution.
It does not authorize runtime wiring.
It does not authorize public claims.
It does not claim proof, correctness, security certification, production readiness, public readiness, AGI, consciousness, sentience, or Turing success.

## 17. Recommended next lane

`DESIGN_WESLR_PATCH_FEEDBACK_LOOP_V1`

Preserve:
`IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_BOUNDARY_V1`

## 18. Final judgment

`code_validation_runner_design_ready_for_patch_feedback_loop_design`

## Final report
- repo: `/data/data/com.termux/files/home/weslr-pr47-clean`
- branch: `master`
- start HEAD: `3df895b19eaea31f15d5ccc6152905b8a89fead1`
- end HEAD: `3df895b19eaea31f15d5ccc6152905b8a89fead1`
- commit hash: pending
- doc created: `docs/WESLR_CODE_VALIDATION_RUNNER_V1.md`
- key design capture: validation is a gate, not proof; promotion requires provenance, manifest, policy, and owner/operator controls
- validation results: `git diff --check` pending; release gate/check not needed for report-only change unless required by workflow; protected-file diff checks pending
- protected files untouched: `weslr/chat_responder.py`, `weslr/main.py`, `dialogue.py`, `chat_ui.py`
- final judgment: `code_validation_runner_design_ready_for_patch_feedback_loop_design`
- recommended next lane: `DESIGN_WESLR_PATCH_FEEDBACK_LOOP_V1`
