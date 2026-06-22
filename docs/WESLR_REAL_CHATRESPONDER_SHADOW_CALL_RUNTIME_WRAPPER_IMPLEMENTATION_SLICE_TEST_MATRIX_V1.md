# WESLR Real ChatResponder Shadow Call Runtime Wrapper Implementation Slice Test Matrix V1

## 1. Purpose and scope
Define the synthetic-only test matrix required for Slice 1 of the future real ChatResponder shadow-call runtime wrapper.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `0184d0ea27e0b714da16efbb510efc80383d9f83`
- Current HEAD: `0184d0ea27e0b714da16efbb510efc80383d9f83`

## 3. Prior artifacts used
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_GUARDRAILS_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_V1.md`

## 4. Implementation is not authorized yet
Implementation remains unauthorized. This matrix only defines the required synthetic-only tests for a future approved Slice 1.

## 5. Test matrix objective
Prove that Slice 1 is fail-closed, preflight-only, and incapable of reaching real execution.

## 6. Future test file path
`weslr/tests/test_real_chatresponder_shadow_call_runtime_wrapper_v1.py`

## 7. Test category table

| Category | Minimum intent | Must prove |
|---|---|---|
| Packet schema tests | Validate required packet shape | Missing/invalid fields reject |
| Approval packet tests | Validate approval shape | Missing/invalid approval fields reject |
| Binding mismatch tests | Compare runtime vs approval | Exact mismatch reject |
| Prompt/session allowlist tests | Enforce exact IDs | Unapproved IDs reject |
| Provider/model lock tests | Lock one provider/model | Any mismatch reject |
| Fallback/override tests | Keep routing fixed | Fallback/override reject |
| `.weslr` IO tests | Keep IO blocked | Any `.weslr` access rejects |
| Persistence/mutation tests | Keep state immutable | Writes/mutations reject |
| Raw-retention/privacy tests | Keep raw content out | Raw prompt/response reject |
| Hidden/answer-key/protected-material tests | Keep sensitive content blocked | Exposure reject |
| Public-claim/final-answer tests | Deny authority claims | Claim/authority reject |
| Retry/batch-expansion tests | Keep scope bounded | Retry/replay expansion reject |
| Old-runner tests | Reject legacy paths | Old scripts reject |
| No-execution-path tests | Ensure slice stays preflight-only | No execute API reachable |

## 8. Packet schema tests
Required tests:
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

## 9. Approval packet tests
Required tests:
- `test_build_approval_packet_requires_all_required_fields`
- `test_validate_approval_packet_rejects_missing_approval_version`
- `test_validate_approval_packet_rejects_missing_operator_id`
- `test_validate_approval_packet_rejects_missing_approval_id`
- `test_validate_approval_packet_rejects_missing_approved_wrapper_version`
- `test_validate_approval_packet_rejects_missing_approved_provider_id`
- `test_validate_approval_packet_rejects_missing_approved_model_id`
- `test_validate_approval_packet_rejects_wrong_field_types`
- `test_validate_approval_packet_rejects_expired_approval_when_checked`

## 10. Binding mismatch tests
Required tests:
- `test_preflight_rejects_wrapper_version_mismatch`
- `test_preflight_rejects_runtime_mode_mismatch`
- `test_preflight_rejects_session_run_id_mismatch`
- `test_preflight_rejects_prompt_set_id_mismatch`
- `test_preflight_rejects_provider_id_mismatch`
- `test_preflight_rejects_model_id_mismatch`
- `test_preflight_rejects_operator_approval_id_mismatch`
- `test_preflight_rejects_selected_prompt_ids_not_subset_of_approval`

## 11. Prompt/session allowlist tests
Required tests:
- `test_preflight_rejects_unapproved_prompt_id`
- `test_preflight_rejects_unapproved_prompt_set_id`
- `test_preflight_rejects_unapproved_session_run_id`
- `test_preflight_rejects_prompt_id_list_expansion`
- `test_preflight_rejects_batch_size_over_max_selected_prompt_ids`

## 12. Provider/model lock tests
Required tests:
- `test_preflight_rejects_provider_model_pair_mismatch`
- `test_preflight_rejects_provider_only_mismatch`
- `test_preflight_rejects_model_only_mismatch`
- `test_preflight_rejects_unknown_provider_id`
- `test_preflight_rejects_unknown_model_id`

## 13. Fallback / override rejection tests
Required tests:
- `test_preflight_rejects_fallback_routing_enabled`
- `test_preflight_rejects_silent_model_override_enabled`
- `test_preflight_rejects_route_expansion_requested`
- `test_preflight_rejects_any_ambiguous_route_selection`

## 14. `.weslr` IO rejection tests
Required tests:
- `test_preflight_rejects_weslr_io_enabled`
- `test_preflight_rejects_weslr_read_request`
- `test_preflight_rejects_weslr_write_request`

## 15. Persistence / mutation rejection tests
Required tests:
- `test_preflight_rejects_memory_write_enabled`
- `test_preflight_rejects_project_write_enabled`
- `test_preflight_rejects_source_write_enabled`
- `test_preflight_rejects_session_mutation_enabled`
- `test_preflight_rejects_source_file_touch_intent`
- `test_preflight_rejects_non_metadata_persistence_intent`

## 16. Raw-retention / privacy rejection tests
Required tests:
- `test_preflight_rejects_raw_prompt_storage_enabled`
- `test_preflight_rejects_raw_response_storage_enabled`
- `test_preflight_rejects_raw_prompt_echo_intent`
- `test_preflight_rejects_raw_response_echo_intent`
- `test_preflight_rejects_private_text_retention_intent`

## 17. Hidden / answer-key / protected-material rejection tests
Required tests:
- `test_preflight_rejects_hidden_prompt_exposure_enabled`
- `test_preflight_rejects_answer_key_exposure_enabled`
- `test_preflight_rejects_protected_material_exposure_enabled`
- `test_preflight_rejects_hidden_prompt_leak_intent`
- `test_preflight_rejects_answer_key_leak_intent`
- `test_preflight_rejects_protected_material_leak_intent`

## 18. Public-claim / final-answer rejection tests
Required tests:
- `test_preflight_rejects_public_claims_enabled`
- `test_preflight_rejects_final_answers_enabled`
- `test_preflight_rejects_benchmark_claim_intent`
- `test_preflight_rejects_certification_claim_intent`
- `test_preflight_rejects_sentience_or_aliveness_claim_intent`

## 19. Retry / batch expansion rejection tests
Required tests:
- `test_preflight_rejects_retry_without_explicit_approval`
- `test_preflight_rejects_batch_expansion_without_explicit_approval`
- `test_preflight_rejects_replay_without_new_approval`
- `test_preflight_rejects_duplicate_approval_reuse`

## 20. Old-runner rejection tests
Required tests:
- `test_preflight_rejects_known_old_runner_script_second_batch`
- `test_preflight_rejects_known_old_runner_script_third_batch`
- `test_preflight_rejects_legacy_runner_tag`
- `test_preflight_rejects_old_runner_origin_marker`

## 21. No-execution-path tests
Required tests:
- `test_slice1_exposes_no_execute_api`
- `test_slice1_exposes_no_summary_api`
- `test_slice1_exposes_no_report_render_api`
- `test_preflight_never_invokes_shadow_callable`
- `test_preflight_returns_rejection_without_side_effects`
- `test_synthetic_only_environment_does_not_enable_execution`

## 22. Minimum required passing criteria
Implementation is blocked unless all of the following hold:
- every category above has at least one dedicated test
- every unsafe condition has a fail-closed rejection test
- preflight never executes a callable
- no execution API exists in Slice 1
- all tests are synthetic-only
- protected files remain untouched

## 23. Implementation blocker matrix
Block implementation if any category is missing:
- packet schema
- approval packet
- binding mismatch
- prompt/session allowlists
- provider/model lock
- fallback/override rejection
- `.weslr` IO rejection
- persistence/mutation rejection
- raw-retention/privacy rejection
- hidden/answer-key/protected-material rejection
- public-claim/final-answer rejection
- retry/batch-expansion rejection
- old-runner rejection
- no-execution-path tests

## 24. What must not be tested by real execution
Do not test any of the following by live ChatResponder execution:
- provider calls
- real shadow calls
- `respond_chat`
- runtime integration
- report generation from live output
- old-runner execution
- any `.weslr` side effect

## 25. Abort conditions
Abort the slice if:
- any blocker category is missing
- any test implies live execution
- any execution-capable API appears in Slice 1
- any protected file is touched
- any synthetic-only constraint is unclear or unenforced

## 26. Recommended next lane
- `DESIGN_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_TEST_IMPLEMENTATION_PLAN_V1`

## 27. Final judgment
`real_chatresponder_shadow_call_runtime_wrapper_test_matrix_design_valid_ready_for_review`
