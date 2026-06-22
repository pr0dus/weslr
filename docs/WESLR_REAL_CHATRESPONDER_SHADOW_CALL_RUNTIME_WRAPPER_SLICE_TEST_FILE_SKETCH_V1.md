# WESLR Real ChatResponder Shadow Call Runtime Wrapper Slice Test File Sketch V1

## 1. Purpose and scope
Sketch the future synthetic-only test file for Slice 1 of the real ChatResponder shadow-call runtime wrapper.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `37b5316a516202d2592ca5b3e209c6faad1ec8af`
- Current HEAD: `37b5316a516202d2592ca5b3e209c6faad1ec8af`

## 3. Prior artifacts used
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_SLICE_TEST_IMPLEMENTATION_PLAN_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_TEST_MATRIX_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_V1.md`

## 4. Implementation is not authorized yet
Implementation remains unauthorized. This is a sketch only, not code.

## 5. Future test file path
`weslr/tests/test_real_chatresponder_shadow_call_runtime_wrapper_v1.py`

## 6. Future wrapper file path
`weslr/real_chatresponder_shadow_call_runtime_wrapper.py`

## 7. Allowed future imports
Use only small, local, synthetic-only imports such as:
- `from __future__ import annotations`
- `from copy import deepcopy`
- `from dataclasses import replace` if needed for packet variants
- `import pytest`
- `from weslr.real_chatresponder_shadow_call_runtime_wrapper import ...` once the wrapper exists
- `from typing import Any, Mapping` if helpful for type hints

## 8. Forbidden imports
Must not import:
- `weslr.chat_responder`
- `weslr.real_chatresponder_shadow_call_helpers`
- `weslr/tests/run_second_real_chatresponder_shadow_call_batch_v1.py`
- `weslr/tests/run_third_real_chatresponder_shadow_call_batch_v1.py`
- any provider/model/web/GitHub/RSS client
- any OpenClaw config/session/body readers
- any runtime-wiring or live execution helper outside the slice 1 wrapper module

## 9. Fixture sketch
Use these reusable fixture names:
- `runtime_packet_base`
- `approval_packet_base`
- `runtime_packet_factory`
- `approval_packet_factory`
- `preflight_inputs_factory`
- `mutate_packet`
- `assert_rejected`
- `assert_no_side_effects`

## 10. Baseline runtime packet sketch
The baseline runtime packet fixture should include these exact fields:
- `wrapper_version`
- `runtime_mode`
- `prompt_id`
- `prompt_set_id`
- `session_run_id`
- `operator_approval_id`
- `provider_id`
- `model_id`
- `selected_prompt_ids`
- `max_selected_prompt_ids`
- `allow_fallback_routing`
- `allow_model_override`
- `allow_raw_prompt_storage`
- `allow_raw_response_storage`
- `allow_weslr_io`
- `allow_memory_write`
- `allow_project_write`
- `allow_public_claims`
- `allow_final_answers`
- `allow_hidden_prompt_exposure`
- `allow_answer_key_exposure`
- `allow_protected_material_exposure`
- `allow_retries`

## 11. Baseline approval packet sketch
The baseline approval packet fixture should include these exact fields:
- `approval_version`
- `operator_id`
- `approval_id`
- `approved_wrapper_version`
- `approved_runtime_mode`
- `approved_prompt_set_id`
- `approved_prompt_ids`
- `approved_session_run_id`
- `approved_provider_id`
- `approved_model_id`
- `approved_at`
- `approval_scope`
- `approval_expiry`
- `approval_notes`
- `approval_signature`

## 12. Invalid-variant helper sketch
Use one mutation helper named:
- `mutate_packet(packet, **overrides)`

It should support:
- field deletion
- wrong-type substitution
- single-field mismatch
- forbidden-flag flip to `True`
- prompt list expansion
- old-runner marker injection
- retry/batch-expansion intent injection

## 13. Assertion helper sketch
Use these assertion helpers:
- `assert_rejected(result, reason_fragment)`
- `assert_fail_closed(result)`
- `assert_no_side_effects(snapshot_before, snapshot_after)`
- `assert_callable_not_invoked(call_counter)`

## 14. Test group order
Implement groups in this order:
1. no-execution-path tests
2. old-runner rejection tests
3. packet schema tests
4. approval packet tests
5. binding mismatch tests
6. allowlist and routing lock tests
7. unsafe-flag rejection tests
8. persistence/mutation/privacy tests
9. public/final-answer authority tests
10. retry/batch-expansion tests
11. baseline sanity checks last

## 15. No-execution-path test names
- `test_slice1_exposes_no_execute_api`
- `test_slice1_exposes_no_summary_api`
- `test_slice1_exposes_no_report_render_api`
- `test_preflight_never_invokes_shadow_callable`
- `test_preflight_returns_rejection_without_side_effects`
- `test_synthetic_only_environment_does_not_enable_execution`

## 16. Old-runner rejection test names
- `test_preflight_rejects_known_old_runner_script_second_batch`
- `test_preflight_rejects_known_old_runner_script_third_batch`
- `test_preflight_rejects_legacy_runner_tag`
- `test_preflight_rejects_old_runner_origin_marker`

## 17. Packet schema test names
- `test_build_runtime_packet_requires_all_required_fields`
- `test_validate_runtime_packet_rejects_missing_wrapper_version`
- `test_validate_runtime_packet_rejects_missing_prompt_id`
- `test_validate_runtime_packet_rejects_missing_prompt_set_id`
- `test_validate_runtime_packet_rejects_missing_session_run_id`
- `test_validate_runtime_packet_rejects_missing_provider_id`
- `test_validate_runtime_packet_rejects_missing_model_id`
- `test_validate_runtime_packet_rejects_missing_selected_prompt_ids`
- `test_validate_runtime_packet_rejects_missing_max_selected_prompt_ids`
- `test_validate_runtime_packet_rejects_wrong_field_types`
- `test_validate_runtime_packet_rejects_unknown_wrapper_version`
- `test_validate_runtime_packet_rejects_unknown_runtime_mode`

## 18. Approval packet test names
- `test_build_approval_packet_requires_all_required_fields`
- `test_validate_approval_packet_rejects_missing_approval_version`
- `test_validate_approval_packet_rejects_missing_operator_id`
- `test_validate_approval_packet_rejects_missing_approval_id`
- `test_validate_approval_packet_rejects_missing_approved_wrapper_version`
- `test_validate_approval_packet_rejects_missing_approved_provider_id`
- `test_validate_approval_packet_rejects_missing_approved_model_id`
- `test_validate_approval_packet_rejects_wrong_field_types`
- `test_validate_approval_packet_rejects_expired_approval_when_checked`

## 19. Binding mismatch test names
- `test_preflight_rejects_wrapper_version_mismatch`
- `test_preflight_rejects_runtime_mode_mismatch`
- `test_preflight_rejects_session_run_id_mismatch`
- `test_preflight_rejects_prompt_set_id_mismatch`
- `test_preflight_rejects_provider_id_mismatch`
- `test_preflight_rejects_model_id_mismatch`
- `test_preflight_rejects_operator_approval_id_mismatch`
- `test_preflight_rejects_selected_prompt_ids_not_subset_of_approval`

## 20. Allowlist / routing lock test names
- `test_preflight_rejects_unapproved_prompt_id`
- `test_preflight_rejects_unapproved_prompt_set_id`
- `test_preflight_rejects_unapproved_session_run_id`
- `test_preflight_rejects_prompt_id_list_expansion`
- `test_preflight_rejects_batch_size_over_max_selected_prompt_ids`
- `test_preflight_rejects_provider_model_pair_mismatch`
- `test_preflight_rejects_provider_only_mismatch`
- `test_preflight_rejects_model_only_mismatch`
- `test_preflight_rejects_unknown_provider_id`
- `test_preflight_rejects_unknown_model_id`
- `test_preflight_rejects_fallback_routing_enabled`
- `test_preflight_rejects_silent_model_override_enabled`
- `test_preflight_rejects_route_expansion_requested`
- `test_preflight_rejects_any_ambiguous_route_selection`

## 21. Unsafe-flag rejection test names
- `test_preflight_rejects_weslr_io_enabled`
- `test_preflight_rejects_weslr_read_request`
- `test_preflight_rejects_weslr_write_request`
- `test_preflight_rejects_memory_write_enabled`
- `test_preflight_rejects_project_write_enabled`
- `test_preflight_rejects_source_write_enabled`
- `test_preflight_rejects_session_mutation_enabled`
- `test_preflight_rejects_source_file_touch_intent`
- `test_preflight_rejects_non_metadata_persistence_intent`

## 22. Persistence / mutation / privacy test names
- `test_preflight_rejects_raw_prompt_storage_enabled`
- `test_preflight_rejects_raw_response_storage_enabled`
- `test_preflight_rejects_raw_prompt_echo_intent`
- `test_preflight_rejects_raw_response_echo_intent`
- `test_preflight_rejects_private_text_retention_intent`
- `test_preflight_rejects_hidden_prompt_exposure_enabled`
- `test_preflight_rejects_answer_key_exposure_enabled`
- `test_preflight_rejects_protected_material_exposure_enabled`
- `test_preflight_rejects_hidden_prompt_leak_intent`
- `test_preflight_rejects_answer_key_leak_intent`
- `test_preflight_rejects_protected_material_leak_intent`

## 23. Public / final-answer authority test names
- `test_preflight_rejects_public_claims_enabled`
- `test_preflight_rejects_final_answers_enabled`
- `test_preflight_rejects_benchmark_claim_intent`
- `test_preflight_rejects_certification_claim_intent`
- `test_preflight_rejects_sentience_or_aliveness_claim_intent`

## 24. Retry / batch-expansion test names
- `test_preflight_rejects_retry_without_explicit_approval`
- `test_preflight_rejects_batch_expansion_without_explicit_approval`
- `test_preflight_rejects_replay_without_new_approval`
- `test_preflight_rejects_duplicate_approval_reuse`

## 25. Minimum required test count
Minimum acceptable sketch coverage should imply at least:
- 6 no-execution-path tests
- 4 old-runner tests
- 12 packet/approval/binding tests
- 14 allowlist/routing tests
- 9 unsafe-flag tests
- 11 persistence/privacy tests
- 5 public/final-answer tests
- 4 retry/batch tests
This yields a practical target of 60+ named tests, with every blocker category represented.

## 26. Implementation blocker list
Block implementation if any of these are absent from the file sketch:
- no-execution-path tests
- old-runner rejection tests
- packet schema tests
- approval packet tests
- binding mismatch tests
- allowlist and routing lock tests
- unsafe-flag rejection tests
- persistence/mutation/privacy tests
- public/final-answer authority tests
- retry/batch-expansion tests
- blocker-first ordering
- synthetic-only constraint

## 27. Postponed work
Postpone until later approved lanes:
- actual test code
- wrapper code
- runtime execution code
- report rendering code
- provider/model activation code
- any helper or runner edits

## 28. Abort conditions
Abort the sketch if:
- any live execution appears in scope
- any protected file would need modification
- any forbidden import is required
- any execution-capable API is assumed to exist already
- blocker-first ordering is weakened

## 29. Recommended next lane
- `REVIEW_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_SLICE_TEST_FILE_SKETCH_V1`

## 30. Final judgment
`real_chatresponder_shadow_call_runtime_wrapper_slice_test_file_sketch_valid_ready_for_review`
