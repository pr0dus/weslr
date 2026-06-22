# WESLR Real ChatResponder Shadow Call Runtime Wrapper Slice Test Implementation Plan V1

## 1. Purpose and scope
Define the implementation plan for the future Slice 1 test file only: synthetic-only tests for schema validation and fail-closed preflight rejection.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `c5a588054326d94146a63f31715d2f2d7cfcb460`
- Current HEAD: `c5a588054326d94146a63f31715d2f2d7cfcb460`

## 3. Prior artifacts used
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_TEST_MATRIX_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_GUARDRAILS_V1.md`

## 4. Implementation is not authorized yet
Implementation remains unauthorized. This plan defines test-file structure and order for a future approved slice.

## 5. Test implementation objective
Implement the slice 1 test file as a synthetic-only harness that proves packet validation and preflight are fail-closed and execution-free.

## 6. Future test file path
`weslr/tests/test_real_chatresponder_shadow_call_runtime_wrapper_v1.py`

## 7. Test file structure
Use a single test module with grouped sections in this order:
1. shared synthetic fixtures
2. packet schema tests
3. approval packet tests
4. binding mismatch tests
5. allowlist and routing lock tests
6. rejection-path tests for unsafe flags
7. old-runner rejection tests
8. no-execution-path tests
9. minimal positive baseline validations if still needed for fixture sanity

## 8. Synthetic fixture plan
Use reusable fixtures only; no live calls.
- `runtime_packet_base`
- `approval_packet_base`
- `make_runtime_packet(**overrides)`
- `make_approval_packet(**overrides)`
- `make_preflight_inputs(runtime_overrides=None, approval_overrides=None)`
- `mutate_packet(packet, **overrides)` helper for invalid variants
- optional `assert_rejected(result, reason_fragment)` helper

## 9. Baseline runtime packet fixture
A valid baseline runtime packet fixture should include:
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
- all unsafe toggles set false
- `allow_retries` set false
- any old-runner markers absent

## 10. Baseline approval packet fixture
A valid baseline approval packet fixture should include:
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

## 11. Invalid-variant helper plan
Use a single mutation helper to derive invalid cases from the valid baseline fixtures:
- remove a field
- set wrong type
- change one ID to mismatch
- flip a forbidden flag to true
- add an old-runner tag/origin marker
- expand prompt sets beyond approval
- add retry or batch-expansion intent
This keeps tests compact and consistent.

## 12. Test group ordering
Implement groups in blocker-first order:
1. no-execution-path tests
2. old-runner rejection tests
3. packet schema tests
4. approval packet tests
5. binding mismatch tests
6. allowlist and routing lock tests
7. unsafe-flag rejection tests
8. mutation/privacy rejection tests
9. baseline sanity tests

## 13. Blocker-first strategy
Tests that prove the slice cannot execute must come before any broader rejection coverage.
That means:
- prove no execute/report APIs exist in Slice 1
- prove preflight never invokes a callable
- prove old-runner origins reject
Only then fill out the rest of the matrix.

## 14. Packet schema test implementation plan
Implement tests that:
- confirm valid packet passes validation
- each required field missing causes rejection
- wrong-type fields reject
- unknown wrapper/runtime versions reject
- runtime packet validation is fail-closed on malformed input

## 15. Approval packet test implementation plan
Implement tests that:
- confirm valid approval packet passes validation
- missing approval fields reject
- wrong-type approval fields reject
- expired approval rejects when checked
- approval metadata must match the runtime packet exactly

## 16. Binding mismatch test implementation plan
Implement tests that change one field at a time and assert rejection:
- wrapper version
- runtime mode
- session/run ID
- prompt set ID
- provider ID
- model ID
- operator approval ID
- selected prompt IDs not included in approval

## 17. Prompt/session/provider/model allowlist test implementation plan
Implement tests that prove:
- unapproved prompt IDs reject
- unapproved prompt set IDs reject
- unapproved session/run IDs reject
- provider/model pair must match exactly
- batch size cannot exceed the approved max
- list expansion is rejected

## 18. Fallback / override rejection test implementation plan
Implement tests that prove any of the following rejects:
- fallback routing enabled
- silent model override enabled
- ambiguous route selection
- route expansion requested

## 19. `.weslr` IO rejection test implementation plan
Implement tests that prove any `.weslr` access intent rejects:
- read
- write
- IO-enabled flag

## 20. Persistence / mutation rejection test implementation plan
Implement tests that reject intents for:
- memory writes
- project writes
- source writes
- session mutation beyond metadata
- source-file touch intent
- any non-metadata persistence path

## 21. Raw-retention / privacy rejection test implementation plan
Implement tests that reject:
- raw prompt storage
- raw response storage
- raw prompt echo intent
- raw response echo intent
- private text retention intent

## 22. Hidden / answer-key / protected-material rejection test implementation plan
Implement tests that reject:
- hidden prompt exposure
- answer-key exposure
- protected-material exposure
- leak intents for each of the above

## 23. Public-claim / final-answer rejection test implementation plan
Implement tests that reject:
- public claims
- final answers
- benchmark claims
- certification claims
- sentience/aliveness claims

## 24. Retry / batch expansion rejection test implementation plan
Implement tests that reject:
- retry without explicit approval
- batch expansion without explicit approval
- replay without new approval
- duplicate approval reuse

## 25. Old-runner rejection test implementation plan
Implement tests that reject known legacy origins and markers:
- second batch runner origin
- third batch runner origin
- legacy runner tag
- old-runner origin marker

## 26. No-execution-path test implementation plan
Implement tests that prove:
- slice 1 exposes no execute API
- slice 1 exposes no summary API
- slice 1 exposes no report-render API
- preflight never invokes a supplied callable
- rejection occurs without side effects
- synthetic-only environment cannot enable execution

## 27. Minimum test count and category coverage
Minimum acceptable implementation coverage:
- at least one dedicated test per category in the matrix
- every category in the matrix represented
- all no-execution-path tests present
- every unsafe toggle covered at least once
- old-runner rejection covered at least once
Practical target: 30+ focused tests, with one or more per matrix row, to avoid category gaps.

## 28. Implementation order
Safest order:
1. no-execution-path tests
2. old-runner rejection tests
3. packet schema tests
4. approval packet tests
5. binding mismatch tests
6. allowlist/routing lock tests
7. unsafe flag rejection tests
8. privacy/mutation tests
9. claim/authority rejection tests
10. retry/batch-expansion tests
11. any baseline sanity checks last

## 29. Postponed work
Postpone until later approved lanes:
- wrapper implementation
- execution helpers
- summary/report rendering helpers
- provider-routing activation
- live runtime wiring
- old-runner integration changes

## 30. Abort conditions
Abort the plan if:
- any test implies live execution
- the test file would need protected-file changes
- the test file would require helper/runtime implementation first
- any execution-capable API is introduced into Slice 1
- blocker-first ordering is violated
- synthetic-only constraints are not enforceable

## 31. Recommended next lane
- `DESIGN_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_SLICE_TEST_FILE_SKETCH_V1`

## 32. Final judgment
`real_chatresponder_shadow_call_runtime_wrapper_slice_test_implementation_plan_valid_ready_for_review`
