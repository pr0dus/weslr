# WESLR Real ChatResponder Shadow Call Runtime Wrapper Implementation Slice V1

## 1. Purpose and scope
Define the smallest safe first implementation slice for the future real ChatResponder shadow-call runtime wrapper.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `fc86ac3c1f09b7ace63d9afb27eb4832736c4ced`
- Current HEAD: `fc86ac3c1f09b7ace63d9afb27eb4832736c4ced`

## 3. Prior artifacts used
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_GUARDRAILS_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_BOUNDARY_REVIEW_V1.md`

## 4. Implementation is not authorized yet
Implementation remains unauthorized. This slice defines what a future implementation may contain, not what may be executed now.

## 5. Slice 1 objective
Implement only the schema and preflight rejection surface needed to prove fail-closed behavior with synthetic-only tests.

## 6. Allowed future files
A future implementation slice may touch only:
- `weslr/real_chatresponder_shadow_call_runtime_wrapper.py`
- `weslr/tests/test_real_chatresponder_shadow_call_runtime_wrapper_v1.py`
- one future implementation-report doc, if separately approved

## 7. Forbidden files
Must remain untouched:
- `weslr/chat_responder.py`
- `weslr/main.py`
- repo-root `main.py`
- `dialogue.py`
- `chat_ui.py`
- `weslr/real_chatresponder_shadow_call_helpers.py`
- `weslr/tests/run_second_real_chatresponder_shadow_call_batch_v1.py`
- `weslr/tests/run_third_real_chatresponder_shadow_call_batch_v1.py`

## 8. Slice 1 allowed APIs
Allow only these future APIs in slice 1:
- `build_real_chatresponder_shadow_call_runtime_packet_v1(...)`
- `validate_real_chatresponder_shadow_call_runtime_packet_v1(packet)`
- `build_real_chatresponder_shadow_call_approval_packet_v1(...)`
- `validate_real_chatresponder_shadow_call_approval_packet_v1(packet)`
- `preflight_real_chatresponder_shadow_call_runtime_v1(runtime_packet, approval_packet)`

## 9. APIs postponed
Postpone to later slices:
- `execute_real_chatresponder_shadow_call_runtime_v1(...)`
- `summarize_real_chatresponder_shadow_call_runtime_result_v1(...)`
- `render_real_chatresponder_shadow_call_runtime_report_v1(...)`
- any direct runtime execution helper
- any provider/provider-routing activation logic

## 10. Runtime packet shape
The runtime packet should include at least:
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

## 11. Approval packet shape
The approval packet should include at least:
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

## 12. Validation / preflight behavior
Validation functions must:
- check required fields
- reject missing/unknown/invalid types
- reject mismatched versions
- reject unapproved prompt IDs or prompt sets
- reject provider/model mismatches
- reject any enabled unsafe flag
- return fail-closed results only

Preflight must:
- compare runtime packet and approval packet exactly
- reject any mismatch
- reject if the approved wrapper version does not match
- reject if the runtime mode is not approved
- reject if any allowed flag is not in the safe state
- never execute anything

## 13. Fail-closed rejection matrix
Reject by default when any of the following are present:
- wrapper/version mismatch
- operator approval mismatch
- prompt ID mismatch
- prompt set mismatch
- session/run ID mismatch
- provider/model mismatch
- fallback enabled
- silent override possible
- `.weslr` IO enabled
- memory write enabled
- project write enabled
- source write enabled
- session mutation enabled beyond in-memory metadata
- raw prompt retention enabled
- raw response retention enabled
- hidden prompt exposure enabled
- answer-key exposure enabled
- protected-material exposure enabled
- public claims enabled
- final-answer authority enabled
- retry/batch expansion enabled without separate approval
- old runner path detected

## 14. Old runner rejection behavior
Preflight must hard-reject any attempt that originates from or is explicitly tagged as the old runner scripts. The known batch scripts must not be able to reach a future execution path.

## 15. Provider/model lock behavior
Slice 1 must encode one exact provider and one exact model as approved inputs. Any difference is rejected.

## 16. No-fallback / no-override behavior
Fallback routing must remain disabled. Silent model override must be impossible in the slice 1 surface and rejected by validation.

## 17. No `.weslr` IO behavior
The slice must not read or write `.weslr`. Any packet field or flag implying such access is rejected.

## 18. No persistence / mutation behavior
Reject any request implying source writes, project writes, memory writes, session writes, or persistence beyond in-memory metadata objects used for preflight bookkeeping.

## 19. Raw-retention / privacy behavior
Reject raw prompt storage, raw response storage, hidden prompt exposure, answer-key exposure, and protected-material exposure.

## 20. Public-claim / final-answer denial behavior
Reject any packet or approval state that allows public claims, final-answer authority, certification claims, benchmark claims, or sentience/aliveness claims.

## 21. Synthetic-only test plan
Slice 1 tests must be synthetic-only and cover:
- field schema validation
- exact approval binding
- prompt/session/provider/model mismatch rejection
- fallback rejection
- silent override rejection
- `.weslr` IO rejection
- no persistence/mutation rejection
- raw-retention/privacy rejection
- public-claim/final-answer rejection
- old-runner rejection
- no execution path present

## 22. Minimum passing criteria
Slice 1 is acceptable only if:
- validators are fail-closed
- preflight returns rejection without execution
- synthetic-only tests cover every rejection category above
- no execution-capable path exists yet
- no protected files are touched

## 23. Abort conditions
Abort slice 1 implementation if any of the following appear:
- any live execution path
- any direct ChatResponder call
- any provider/model fallback
- any `.weslr` IO
- any raw retention
- any mutation path beyond in-memory metadata
- any protected-file touch
- any old-runner bypass path

## 24. Recommended next lane
- `DESIGN_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_TEST_MATRIX_V1`

## 25. Final judgment
`real_chatresponder_shadow_call_runtime_wrapper_implementation_slice_design_valid_ready_for_review`
