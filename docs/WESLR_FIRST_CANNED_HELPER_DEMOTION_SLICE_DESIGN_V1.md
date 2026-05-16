# WESLR First Canned Helper Demotion Slice Design V1

Marker: WESLR_FIRST_CANNED_HELPER_DEMOTION_SLICE_DESIGN_V1

## Status

- Status: Design only
- No live chat replacement
- No chat_responder.py edits
- Owner approval required before live demotion
- Shadow-only first
- `safe_to_replace_live=false`
- `runtime_wiring=false`
- `live_runtime_output=false`

This document is a design-only plan for a future, narrow canned-helper demotion slice. It does not implement demotion, does not change runtime behavior, does not wire ranked response, does not create a live router, does not replace answers, does not call live `ChatResponder.respond_chat(...)`, and does not create `.weslr` runtime state.

## 1. Purpose

The first demotion slice is intended to eventually move only the lowest-risk ordinary canned topic helper behavior away from fixed replies in `chat_responder.py` and toward the unified response formation shadow/comparison path.

The target direction remains one unified WESLR response path:

```text
input
→ meaning/state/evidence/capability/native frame
→ candidates
→ ranking
→ self-check
→ rendering
→ metadata
→ later voice
```

Deterministic guardrails are allowed. Deterministic answers are not core cognition.

This design authorizes no implementation now. Future implementation must begin shadow-only before any live behavior change. Owner approval required before live demotion.

## 2. Allowed first-slice candidates

Allowed first-slice candidates are limited to five low-risk ordinary helper branches identified by `docs/CHAT_RESPONDER_BRANCH_INV.md` and confirmed against `weslr/chat_responder.py`.

| candidate | approx lines | trigger type | current behavior category | write risk | model/search risk | high-risk/self/protected risk | comparison inventory category | why safe enough for first demotion design |
|---|---:|---|---|---|---|---|---|---|
| lunch helper | `1775-1778` | keyword: `lunch`; lightweight active-context hints | fixed ordinary topic advice | no direct writes | no | no | `chat_responder_topic_helper_ordinary` / legacy alias `chat_responder_topic_helper` | fixed low-stakes topic helper; no `.weslr` writes; no model/search; suitable for shadow comparison only |
| workout helper | `1780-1785` | keywords: `workout`, `gym`, `run`, `exercise`; lightweight hints | fixed ordinary topic advice | no direct writes | no | no | `chat_responder_topic_helper_ordinary` / legacy alias `chat_responder_topic_helper` | fixed low-stakes ordinary planning advice; no direct side effects; can compare against ordinary task/clarification families |
| plan helper | `1787-1792` | keyword: `plan`; lightweight email/workout hints | fixed plan template | no direct writes | no | no | `chat_responder_topic_helper_ordinary` / legacy alias `chat_responder_topic_helper` | ordinary task-plan surface; low-risk first candidate for unified response shadow metadata |
| email helper | `1794-1797` | keyword: `email`; lightweight plan hint | fixed email drafting advice | no direct writes | no | no | `chat_responder_topic_helper_ordinary` / legacy alias `chat_responder_topic_helper` | ordinary drafting helper; no external send, no inbox access, no private text storage in this branch |
| code/bug helper | `1802-1803` | keywords: `code`, `bug` | fixed debug invitation | no direct writes | no | no | `chat_responder_code_bug_helper` / legacy alias `chat_responder_topic_helper` | low-risk debug invitation; no solver execution, no answer arbitration, no model/search |

These candidates are safe enough only for first demotion design and future shadow-only scenario work because they are fixed ordinary topic helpers, have no observed direct writes, make no model/search calls, create no `.weslr` state, and do not touch identity, consciousness, protected material, official benchmark, or high-stakes evidence boundaries.

They are not safe to replace live yet.

## 3. Do-not-touch branches

Do-not-touch branches for this slice:

- low-focus fallback — excluded because it sits inside the model path and has inadequacy-write risk.
- vague fallback — excluded because it follows model attempts/rescue logic and has inadequacy-write risk.
- model unavailable fallback — excluded because it is provider/runtime status fallback and may record inadequacy metadata.
- model rescue path — excluded because it performs model calls and belongs to runtime rescue behavior.
- model-backed response path — excluded because it calls the live model path and can write inadequacy metadata.
- meaning-vector write-capable path — excluded because it can capture relationship observations and safe memories.
- memory capture / relationship capture paths — excluded because write-capable memory behavior needs separate governance.
- limited Frontier identity/self/consciousness/system/benchmark responses — excluded because self/identity/high-risk boundaries require separate review.
- limited ordinary-task renderer — excluded because it is already state/unknown-aware and needs separate comparison before redesign.
- state-grounded self/system/memory answers — excluded because self/system answers require higher-risk review.
- wife/partner/interpersonal helper — excluded because interpersonal advice is sensitive and not a first demotion candidate.
- official IQ/benchmark/certification boundaries — excluded because these are deterministic guardrails/status boundaries.
- protected/hidden prompt/answer-key boundaries — excluded because these are protected guardrails.
- evidence bridge/search/PubMed paths — excluded because external evidence/search authority and writes require separate review.
- deterministic write-capable handlers — excluded because side effects and `.weslr` writes are out of scope.
- deterministic read-only status/command surfaces — excluded because status surfaces are not ordinary cognition.
- staging arbiter raw-message logging — excluded because it has raw-message logging risk.
- blocked-write guidance — excluded because it is a guardrail/status surface.

This slice must not demote guardrails, identity/self, high-stakes, memory/write, model/search, evidence, status, or staging raw-log paths.

## 4. Future implementation shape

A future implementation should remain shadow-only first and should likely add a narrow comparison harness for exactly the five allowed candidates.

Future shadow scenario flow:

1. Define synthetic, non-private scenario prompts for lunch/workout/plan/email/code.
2. Do not call live `ChatResponder.respond_chat(...)`.
3. Call `build_unified_response_formation_shadow_v1(...)` with each synthetic prompt.
4. Call `build_canned_helper_shadow_comparison_v1(...)` with the appropriate legacy surface label.
5. Produce comparison metadata only.
6. Keep `safe_to_replace_live=false`.
7. Keep `runtime_wiring=false`.
8. Keep `live_runtime_output=false`.
9. Keep model/advisor/search/solver/arbitration flags false.
10. Store no raw private text and create no `.weslr` state.

Suggested future metadata shape:

```json
{
  "slice_type": "first_canned_helper_demotion_shadow_slice_v1",
  "target_branch": "...",
  "legacy_surface": "...",
  "shadow_comparison_available": true,
  "selected_shadow_candidate_family": "...",
  "demotion_candidate": true,
  "safe_to_replace_live": false,
  "requires_owner_approval": true,
  "runtime_wiring": false,
  "live_runtime_output": false,
  "model_calls": false,
  "advisor_calls": false,
  "web_search": false,
  "solver_execution": false,
  "answer_selection_arbitration": false,
  "raw_text_stored": false
}
```

## 5. Future live-demotion gate

No live demotion may happen unless all of the following are true:

- explicit owner approval is granted for a live slice.
- focused tests exist for each target branch.
- shadow comparison shows the unified shadow path is better or at least safer than the legacy canned helper.
- no guardrail/status/self/high-risk branch is touched.
- no memory writes are introduced.
- no model/search calls are introduced.
- no raw private text storage is introduced.
- no `.weslr` state creation is introduced.
- fallback/rollback plan exists.
- release gate passes.
- release check passes.
- implementation is one branch at a time, not a broad replacement.

Even after satisfying these gates, live replacement remains owner-approved implementation work, not a conclusion of this document.

## 6. Future implementation phases

### Phase 0 — current design only

- Write this document.
- No behavior change.
- No source/runtime edits.
- No live chat replacement.

### Phase 1 — shadow scenario tests only

- Add explicit scenario tests for lunch/workout/plan/email/code.
- Compare current legacy labels against unified shadow comparison.
- Do not call live `ChatResponder.respond_chat(...)`.
- Assert all no-live/no-write/no-model flags remain false or safe.

### Phase 2 — shadow adapter / branch marker only

- Optionally add non-live branch marker metadata or a test-only helper if needed.
- Keep runtime output unchanged.
- Keep `safe_to_replace_live=false`, `runtime_wiring=false`, and `live_runtime_output=false`.

### Phase 3 — owner-approved narrow live slice

- Only after explicit owner approval.
- One branch at a time.
- Rollback-ready.
- No high-risk branches.
- No write/search/model/status/self/guardrail branches.

### Phase 4 — post-change audit

- Verify no runtime drift.
- Verify OCC context update.
- Verify no accidental live broadening.
- Verify release gate and release check still pass.

## 7. Future test plan

Future tests should cover:

- lunch helper scenario.
- workout helper scenario.
- plan helper scenario.
- email helper scenario.
- code/bug helper scenario.
- no exact canned response assertion.
- shadow comparison selected family is `ordinary_task_plan`, `clarification`, or another appropriate safe family.
- `safe_to_replace_live=false`.
- `requires_owner_approval=true`.
- `runtime_wiring=false`.
- `live_runtime_output=false`.
- no raw text leakage.
- no model calls.
- no search calls.
- no advisor calls.
- no `.weslr` state.
- no live chat responder calls.
- guardrail branches not touched.
- high-risk/self/identity/status/write/search branches not included in the slice.

The tests should validate metadata and safety posture, not fixed public answer text.

## 8. Required metadata if later implemented

Any future helper or test-only metadata for this slice should include at least:

```json
{
  "slice_type": "first_canned_helper_demotion_shadow_slice_v1",
  "target_branch": "...",
  "legacy_surface": "...",
  "shadow_comparison_available": true,
  "selected_shadow_candidate_family": "...",
  "demotion_candidate": true,
  "safe_to_replace_live": false,
  "requires_owner_approval": true,
  "runtime_wiring": false,
  "live_runtime_output": false,
  "model_calls": false,
  "advisor_calls": false,
  "web_search": false,
  "solver_execution": false,
  "answer_selection_arbitration": false,
  "raw_text_stored": false
}
```

## 9. Anti-drift rule

Anti-drift rule:

Any future change that expands this slice beyond lunch/workout/plan/email/code without a new review violates this design.

Any future change that edits `chat_responder.py` before owner-approved live-slice design violates this design.

Any future change that demotes guardrails, identity/self, high-stakes, memory/write, model/search, evidence, status, or staging raw-log paths under this slice violates this design.

Any future change that treats shadow comparison as final answer authority, live router authority, scoring authority, model/search permission, or answer-selection arbitration violates this design.

## 10. Recommended next task

Recommended next task:

`IMPLEMENT_WESLR_FIRST_CANNED_HELPER_DEMOTION_SHADOW_SCENARIOS_V1`

This next task should still be tests/helper-only, shadow-only, and no live wiring. It should not edit `chat_responder.py`, should not call live chat responder, should not replace answers, and should not expand beyond the five allowed first-slice candidates without a new review.
