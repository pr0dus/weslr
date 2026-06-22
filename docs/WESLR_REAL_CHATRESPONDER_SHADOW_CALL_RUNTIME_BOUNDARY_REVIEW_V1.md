# WESLR Real ChatResponder Shadow Call Runtime Boundary Review V1

## 1. Purpose and scope
Define the runtime boundary required before any real ChatResponder shadow-call execution, and decide how the helper/runner path should be handled until then.

## 2. Repo root, branch, start HEAD, current HEAD
- Repo root: `/data/data/com.termux/files/home/weslr-pr47-clean`
- Branch: `occ-discovery-doctrine-implementation-20260613`
- Start HEAD: `5634d0fc3fbd5f90b088d20137393d30bd1d6f1f`
- Current HEAD: `5634d0fc3fbd5f90b088d20137393d30bd1d6f1f`

## 3. Files reviewed
- `weslr/real_chatresponder_shadow_call_helpers.py`
- `weslr/tests/run_second_real_chatresponder_shadow_call_batch_v1.py`
- `weslr/tests/run_third_real_chatresponder_shadow_call_batch_v1.py`
- `docs/WESLR_REAL_CHATRESPONDER_SHADOW_CALL_HELPERS_AND_REPORT_RUNNERS_REVIEW_V1.md`
- `docs/WESLR_RUNTIME_ADJACENT_SHADOW_CALL_SCRIPTS_REVIEW_V1.md`
- `docs/WESLR_CONTROLLED_SOURCE_ACCESS_ADAPTER_AND_RUNTIME_ADJACENCY_REVIEW_V1.md`

## 4. Protected-file status
Protected files were not changed:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `main.py`
- `dialogue.py`
- `chat_ui.py`

## 5. Runtime path summary
The helper module is not purely metadata-only. It contains a reachable runtime path through `__import__("weslr.chat_responder", fromlist=["ChatResponder"])`, `ChatResponder()` instantiation, and `respond_chat(prompt_text)` inside `build_safe_injected_callable_v1()`. The runner scripts depend on that helper and set `real_call_authorized=True`, so they remain runtime-adjacent and quarantined.

## 6. Why `real_call_authorized=True` is insufficient alone
`real_call_authorized=True` only opens the path past one preflight gate. It does not guarantee safety, containment, or approval. By itself it does not ensure prompt allowlisting, operator signoff, routing lock-down, no persistence, no raw retention, or no public-claim/final-answer authority.

## 7. Required operator gates
Before any real ChatResponder call, require:
- explicit operator approval
- exact prompt-set allowlist
- exact session/run ID binding
- explicit lane name/version
- explicit execution window or one-shot approval token

## 8. Required technical gates
Before any real ChatResponder call, require:
- no provider/model fallback
- no ambiguous route selection
- no indirect mock bypass
- no hidden ChatResponder path outside the approved wrapper
- no execution unless the approved runtime wrapper is the only entrypoint

## 9. Required privacy gates
Before any real ChatResponder call, require:
- no hidden prompt exposure
- no answer-key exposure
- no protected-material exposure
- no raw private text retention
- no raw prompt/response echoing outside the approved boundary

## 10. Required no-persistence gates
Before any real ChatResponder call, require:
- no `.weslr` IO
- no source-file writes
- no project-state writes
- no memory writes
- no session-state mutation
- no unapproved report output beyond the designated artifact path, if any

## 11. Required no-runtime-mutation gates
Before any real ChatResponder call, require:
- no runtime state mutation outside the approved lane
- no feature-flag mutation
- no default-enablement changes
- no branch-expansion side effects
- no invisible cross-call state

## 12. Required no-public-claim/final-answer gates
Before any real ChatResponder call, require:
- no public claims
- no final-answer authority
- no certification/sentience/aliveness claims
- no official evaluation claims

## 13. Required provider/model routing gates
Before any real ChatResponder call, require:
- exact provider/model binding
- no fallback routing
- no silent model override
- no implicit reroute to another provider
- no live provider activation unless the approved wrapper explicitly permits it

## 14. Required prompt/session allowlist gates
Before any real ChatResponder call, require:
- exact prompt ID allowlist
- exact session/run ID allowlist
- exact runner script version allowlist
- no unlisted prompt families
- no unlisted retries or batch expansion

## 15. Required evidence/output containment gates
Before any real ChatResponder call, require:
- raw outputs contained only to the approved in-memory result object
- no raw transcript retention
- no private output echo in docs unless explicitly approved
- no answer-key material in summaries
- no protected source material in rendered reports

## 16. Quarantine decision for helper
The helper should stay quarantined until a formal runtime boundary wrapper exists and is approved. The current module is too execution-capable to be treated as a normal metadata-only helper.

## 17. Quarantine decision for runner scripts
The two runner scripts should remain untracked and quarantined. They are runtime-adjacent by design and should not be adopted into the helper lane.

## 18. Whether module split is recommended later
Yes. A future split is recommended:
- one metadata-only module for preflight, classification, and report-safe helpers
- one runtime-capable module for the explicitly approved real ChatResponder execution path

## 19. Whether controlled source access adapter helper adoption is blocked
No. The controlled source access adapter helper remains separately adoptable. This runtime-capable path should not block it.

## 20. Recommended next lane
- `DESIGN_WESLR_REAL_CHATRESPONDER_SHADOW_CALL_RUNTIME_WRAPPER_V1`

## 21. Final judgment
`real_chatresponder_shadow_call_runtime_boundary_valid_quarantine_required`
