# WESLR Real ChatResponder Shadow Call Runtime Wrapper V1

## 1. Purpose and scope
Design a future fail-closed runtime wrapper required before any real ChatResponder shadow-call execution.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `3eacbb0cc9836a344563847ca7017392033c0ee1`
- Current HEAD: `3eacbb0cc9836a344563847ca7017392033c0ee1`

## 3. Prior reports used
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_BOUNDARY_REVIEW_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_HELPERS_AND_REPORT_RUNNERS_REVIEW_V1.md`
- `docs/WESLR_RUNTIME_ADJACENT_SHADOW_CALL_SCRIPTS_REVIEW_V1.md`
- `docs/WESLR_CONTROLLED_SOURCE_ACCESS_ADAPTER_AND_RUNTIME_ADJACENCY_REVIEW_V1.md`

## 4. Problem statement
The current helper path is runtime-capable and quarantined. `real_call_authorized=True` is not enough by itself. A separate wrapper boundary is required before any real ChatResponder call can occur.

## 5. Runtime wrapper objective
Create a single approved entrypoint that gates execution, binds identity, locks routing, prevents retention/mutation, and emits only safe metadata for reports.

## 6. Non-goals
- No implementation now
- No direct ChatResponder execution now
- No model/provider fallback logic
- No `.weslr` IO now
- No project/memory/session mutation now
- No public claims or final-answer authority now

## 7. Required future module path
`weslr/real_chatresponder_shadow_call_runtime_wrapper.py`

## 8. Required future test path
`weslr/tests/test_real_chatresponder_shadow_call_runtime_wrapper_v1.py`

## 9. Proposed API
Suggested wrapper API:
- `build_real_chatresponder_shadow_call_runtime_packet_v1(...)`
- `validate_real_chatresponder_shadow_call_runtime_packet_v1(packet)`
- `build_real_chatresponder_shadow_call_approval_packet_v1(...)`
- `validate_real_chatresponder_shadow_call_approval_packet_v1(packet)`
- `preflight_real_chatresponder_shadow_call_runtime_v1(runtime_packet, approval_packet)`
- `execute_real_chatresponder_shadow_call_runtime_v1(runtime_packet, approval_packet, *, shadow_callable=None)`
- `summarize_real_chatresponder_shadow_call_runtime_result_v1(result)`
- `render_real_chatresponder_shadow_call_runtime_report_v1(result)`

## 10. Required input packet fields
Required runtime packet fields should include:
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
- `allow_fallback_routing` = false
- `allow_model_override` = false
- `allow_raw_prompt_storage` = false
- `allow_raw_response_storage` = false
- `allow_weslr_io` = false
- `allow_memory_write` = false
- `allow_project_write` = false
- `allow_public_claims` = false
- `allow_final_answers` = false
- `allow_hidden_prompt_exposure` = false
- `allow_answer_key_exposure` = false
- `allow_protected_material_exposure` = false
- `allow_retries` = false unless explicitly approved

## 11. Required approval packet fields
Required approval packet fields should include:
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
- `approval_signature` or equivalent operator attestation token

## 12. Required runtime guard fields
Required guard fields should include:
- `real_call_authorized`
- `prompt_allowlist_enforced`
- `prompt_set_allowlist_enforced`
- `session_run_binding_enforced`
- `wrapper_version_binding_enforced`
- `provider_model_binding_enforced`
- `fallback_routing_disabled`
- `model_override_disabled`
- `raw_prompt_storage_disabled`
- `raw_response_storage_disabled`
- `weslr_io_disabled`
- `memory_write_disabled`
- `project_write_disabled`
- `public_claims_disabled`
- `final_answers_disabled`
- `hidden_prompt_exposure_disabled`
- `answer_key_exposure_disabled`
- `protected_material_exposure_disabled`
- `retry_disabled_without_approval`
- `batch_expansion_disabled`

## 13. Fail-closed validation rules
- Missing required field => reject
- Unknown wrapper version => reject
- Any unapproved prompt ID => reject
- Any mismatch between runtime packet and approval packet => reject
- Any fallback enabled => reject
- Any model override enabled => reject
- Any output-retention flag enabled => reject
- Any mutation flag enabled => reject
- Any public-claim/final-answer flag enabled => reject
- Any hidden/answer-key/protected-material exposure flag enabled => reject
- Any old runner script invocation path => reject

## 14. Operator approval rules
- Explicit operator approval is mandatory.
- Approval must bind the exact wrapper version, prompt set, prompt IDs, session/run ID, provider, and model.
- Approval must expire and be single-use unless reapproved.

## 15. Provider/model routing lock rules
- Exactly one provider and one model must be bound.
- No fallback routing.
- No silent override.
- No routing expansion.
- No provider/model substitution after preflight.

## 16. No-fallback rules
- Fallback disabled by default.
- Any fallback candidate list is rejected unless explicitly approved and locked, but the default design should keep fallback off.
- Any ambiguous route is blocked.

## 17. Prompt/session allowlist rules
- Prompt IDs must match an exact allowlist.
- Prompt sets must match an exact allowlist.
- Session/run ID must match exactly.
- No batch growth beyond the approved set.
- No retry or replay unless separately approved.

## 18. Privacy and raw-retention rules
- No raw prompt storage.
- No raw response storage.
- No hidden prompt exposure.
- No answer-key exposure.
- No protected-material exposure.
- Any raw/private content in the response path must be blocked from report rendering.

## 19. No-persistence rules
- No `.weslr` IO.
- No source-file writes.
- No project-state writes.
- No memory writes.
- No session-state mutation except approved in-memory run metadata.
- No unapproved report output outside the designated artifact path.

## 20. No-mutation rules
- No runtime-state mutation beyond the approved wrapper bookkeeping.
- No feature-flag mutation.
- No default enablement changes.
- No branch expansion.
- No cross-run hidden state.

## 21. Public-claim / final-answer denial rules
- No public claims.
- No final-answer authority.
- No certification, sentience, aliveness, or benchmark claims.
- No official evaluation claims beyond safe metadata summaries.

## 22. Output containment rules
- Runtime output must remain in-memory and sanitized.
- Only derived metadata may be passed to report rendering.
- Raw text must never be echoed into report output.
- Any unsafe metadata should be converted to a blocked/omitted summary.

## 23. Report-safe rendering rules
- Render only bounded summaries, counts, labels, and block reasons.
- Never render raw prompts or raw responses.
- Never render hidden prompts, answer keys, protected material, or private session bodies.
- Include explicit boundary-status sections in the report.

## 24. Old helper split recommendation
Yes. Split later into:
- a metadata-only preflight/helper module
- a runtime-capable wrapper module with explicit operator approval
This separation will reduce accidental execution risk.

## 25. Old runner script quarantine recommendation
Keep the old runner scripts quarantined and untracked. They should not call the future wrapper directly unless they are rewritten and explicitly approved for that exact runtime lane.

## 26. Future tests required
- exact allowlist enforcement tests
- exact wrapper/session/provider/model binding tests
- fallback-disabled tests
- raw-retention blocked tests
- no-mutation blocked tests
- no-public-claim/final-answer blocked tests
- report-safe rendering tests
- old-runner rejection tests
- approval-expiry and single-use approval tests
- mismatch/replay/retry rejection tests

## 27. Abort conditions
Abort execution if any of the following occur:
- wrapper version mismatch
- approval mismatch or expiry
- prompt/session/provider/model mismatch
- fallback routing attempt
- raw retention or mutation attempt
- hidden prompt/answer-key/protected-material exposure
- public claim or final-answer attempt
- invocation from a non-approved old runner path

## 28. Validation plan
Future implementation should pass:
- wrapper-specific unit tests
- `git diff --check`
- release gate
- release check
- protected-file quiet diff checks

## 29. Recommended next lane
- `REVIEW_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_TEST_PLAN_V1`

## 30. Final judgment
`real_chatresponder_shadow_call_runtime_wrapper_design_valid_ready_for_review`
