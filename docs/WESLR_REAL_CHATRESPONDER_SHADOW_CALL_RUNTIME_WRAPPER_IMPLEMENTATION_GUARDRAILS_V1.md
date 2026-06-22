# WESLR Real ChatResponder Shadow Call Runtime Wrapper Implementation Guardrails V1

## 1. Purpose and scope
Define what must be true before any future implementation of the real ChatResponder shadow-call runtime wrapper can be approved.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `044b1a1350a9426d5189e6696a4584e53196fc99`
- Current HEAD: `044b1a1350a9426d5189e6696a4584e53196fc99`

## 3. Prior artifacts used
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_BOUNDARY_REVIEW_V1.md`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_HELPERS_AND_REPORT_RUNNERS_REVIEW_V1.md`
- `docs/WESLR_RUNTIME_ADJACENT_SHADOW_CALL_SCRIPTS_REVIEW_V1.md`
- Operator-reported test-plan checkpoint: `real_chatresponder_shadow_call_runtime_wrapper_test_plan_valid_ready_for_implementation_design_review` (not found as a local committed report artifact)

## 4. Operator-reported test-plan checkpoint status
The checkpoint was reported in-chat, but no committed local report artifact was found. Treat it as a signal, not as independently persisted evidence.

## 5. Implementation is not authorized yet
Implementation is not authorized yet. The wrapper remains design-only and quarantined until the approved test boundary and operator approval are both in place.

## 6. Allowed future files
A future implementation may touch only:
- `weslr/real_chatresponder_shadow_call_runtime_wrapper.py`
- `weslr/tests/test_real_chatresponder_shadow_call_runtime_wrapper_v1.py`
- one future implementation-report doc dedicated to that slice, if separately approved

## 7. Forbidden files
Must remain untouched unless separately approved:
- `weslr/chat_responder.py`
- `weslr/main.py`
- repo-root `main.py`
- `dialogue.py`
- `chat_ui.py`
- `weslr/real_chatresponder_shadow_call_helpers.py`
- `weslr/tests/run_second_real_chatresponder_shadow_call_batch_v1.py`
- `weslr/tests/run_third_real_chatresponder_shadow_call_batch_v1.py`

## 8. Future module API boundary
Allowed future API should remain the design-specified wrapper API only:
- runtime packet builders/validators
- approval packet builders/validators
- preflight
- execution
- safe summary rendering
No extra runtime entrypoints should be added.

## 9. Future test boundary
Future tests must be written first or alongside implementation and must cover:
- fail-closed behavior
- approval binding
- prompt/session/provider/model allowlists
- fallback and override blocking
- no-persistence/no-mutation
- privacy and raw-retention blocking
- old-runner rejection
- safe report rendering
- approval expiry/single-use/replay rejection
- retry/batch-expansion rejection

## 10. Feature flag / default-off policy
If a feature flag exists, it must default to false. Any runtime-enable flag must be explicit, narrow, and unambiguous.

## 11. Synthetic-only test policy
If an environment variable is used for local testing, it may only enable synthetic or mock-only tests. Recommended shape:
- `WESLR_REAL_CHATRESPONDER_SHADOW_CALL_SYNTHETIC_ONLY=1`
This must never enable live execution.

## 12. Real execution block policy
Real execution is blocked by default through layered gates:
- no default enablement
- no live execution without explicit operator approval
- no execution without exact approval/runtime binding
- no execution from old runner scripts
- no execution unless preflight passes

## 13. Old runner rejection policy
Old runner scripts must not invoke the wrapper directly. Any attempt from the known batch runners should be rejected during preflight and covered by tests.

## 14. Provider/model routing lock policy
The wrapper must bind one exact provider and one exact model. No substitution, no silent override, and no route expansion are allowed.

## 15. No-fallback policy
Fallback routing must be disabled by default and rejected unless a future explicit approval model is separately designed and approved. The baseline design should keep fallback off.

## 16. No-override policy
Silent model override is forbidden. Any model/provider mismatch is a hard failure.

## 17. No `.weslr` IO policy
No `.weslr` reads or writes are allowed in the future wrapper path.

## 18. No persistence / mutation policy
The wrapper must not write source files, project state, memory state, or session state beyond approved in-memory run metadata. No raw persistence is permitted.

## 19. Raw-retention / privacy policy
No raw prompt storage, no raw response storage, no hidden prompt exposure, no answer-key exposure, and no protected-material exposure are allowed.

## 20. Public-claim / final-answer denial policy
The wrapper must deny public claims, final-answer authority, benchmark/certification claims, and sentience/aliveness claims.

## 21. Report-safe output policy
Any future reports must render only derived metadata: counts, labels, allowlist decisions, and rejection reasons. Raw prompt/response text must never be emitted.

## 22. Required validation commands
Before any implementation commit, run:
- `git diff --check`
- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`

## 23. Required protected-file quiet checks
Also confirm unchanged:
- `git diff --quiet HEAD -- weslr/chat_responder.py`
- `git diff --quiet HEAD -- weslr/main.py`
- `git diff --quiet HEAD -- main.py`
- `git diff --quiet HEAD -- dialogue.py`
- `git diff --quiet HEAD -- chat_ui.py`

## 24. First implementation slice recommendation
Start with the smallest safe slice:
- packet schemas
- validators
- preflight rejection paths
- synthetic-only tests
- no execution path

## 25. Postponed work
Postpone until a later approved lane:
- live ChatResponder execution
- any runtime integration
- any old-runner wiring
- any report writer beyond safe metadata docs
- any provider/provider-routing activation

## 26. Abort conditions
Abort implementation if any of these occur:
- missing or stale approval binding
- missing exact prompt/session/provider/model allowlists
- fallback or silent override appears
- `.weslr` IO appears
- memory/project/session/source mutation appears
- raw retention or protected exposure appears
- public claim or final-answer authority appears
- old runner invocation path appears
- validation gates fail

## 27. Recommended next lane
- `DESIGN_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_IMPLEMENTATION_SLICE_V1`

## 28. Final judgment
`real_chatresponder_shadow_call_runtime_wrapper_guardrails_valid_ready_for_review`
