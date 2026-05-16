# WESLR First Owner-Approved Live Demotion Slice Design V1

Marker: WESLR_FIRST_OWNER_APPROVED_LIVE_DEMOTION_SLICE_DESIGN_V1

## Status

- Status: Design only
- No live chat replacement in this task
- No chat_responder.py edits in this task
- Owner approval required before implementation
- Plan helper first
- One branch only
- `safe_to_replace_live=false`
- `runtime_wiring=false`
- `live_runtime_output=false`
- rollback required
- Anti-drift rule
- Deterministic guardrails are allowed
- Deterministic answers are not core cognition

This document is WESLR_CANON_ALIGNMENT design documentation only. It does not implement a live demotion, does not change runtime behavior, does not edit `chat_responder.py`, does not wire ranked response runtime, does not replace any answer, does not call live `ChatResponder.respond_chat(...)`, does not call models/advisors/search, and does not create `.weslr` runtime state.

## 1. Purpose

This design defines the first possible owner-approved live demotion slice for WESLR: replacing exactly one low-risk canned ordinary helper branch, likely the `chat_responder_plan_helper`, with the unified response formation path in a future task.

This task is design only. There is no runtime change now. There is no `chat_responder.py` edit now. There is no live replacement now. Future implementation requires explicit owner approval by task name and must target one branch only: the plan helper.

The safe workflow remains:

```text
inspect
→ design
→ shadow/test
→ explicit owner approval
→ one tiny live slice
→ verify
→ rollback if bad
→ only then expand
```

A future live implementation must be rollback-ready before any edit is made.

## 2. Why plan helper first

Primary target:

- target branch: `chat_responder_plan_helper`
- approximate line range: `1787-1792`
- legacy surface: `chat_responder_topic_helper_ordinary`
- current behavior: fixed plan template / canned ordinary cognition
- selected shadow family: `ordinary_task_plan`
- quality label: `strongest_first_design_candidate`
- current legacy role: ordinary canned cognition

Reasons this is the first candidate:

- strongest match to the unified response formation ordinary-task plan path
- lowest safety risk among reviewed first-slice candidates
- easiest rollback
- least need for private/current/evidence context
- no direct writes observed
- no direct model/search risk
- no `.weslr` writes
- no high-stakes/identity/consciousness/protected boundary
- no direct tool execution or answer-selection arbitration requirement

The plan helper is the most natural candidate for a narrow live demotion because planning can be handled as ordinary task formation: meaning/state/capability/native frame → candidate family → self-check → bounded rendering. It is still not live-ready by this document; it is only the best design target.

## 3. Why not the others yet

The other reviewed branches remain future candidates only:

- email helper: clarification signal is good, but private-text/send-boundary risk makes it unsuitable as the first live slice.
- lunch helper: low stakes, but user preferences, timing, dietary/current context, and local situation can matter.
- workout helper: health/current condition, injury, intensity, and physical readiness can matter.
- code/bug helper: currently too generic and risks drift into solver execution, model/search use, or answer-selection arbitration.
- wife/partner/interpersonal helper: interpersonal sensitivity; not in the first slice.
- low-focus fallback and vague fallback: model-path/write-risk context and rescue behavior make them unsuitable here.

Explicitly excluded branches and surfaces:

- lunch helper except as a future later candidate
- workout helper except as a future later candidate
- email helper except as a future later candidate
- code/bug helper except as a future later candidate
- wife/partner/interpersonal helper
- low-focus fallback
- vague fallback
- model unavailable fallback
- model rescue path
- model-backed response path
- meaning-vector write-capable path
- memory capture / relationship capture paths
- limited Frontier identity/self/consciousness/system/benchmark responses
- limited ordinary-task renderer unless used only as non-live reference
- state-grounded self/system/memory answers
- official IQ/benchmark/certification boundaries
- protected/hidden prompt/answer-key boundaries
- evidence bridge/search/PubMed paths
- deterministic write-capable handlers
- deterministic external-search handlers
- staging arbiter raw-message logging
- status/command surfaces
- blocked-write guidance

This design must not demote guardrails, status surfaces, self/identity surfaces, high-stakes branches, memory/write paths, model/search paths, evidence paths, staging raw-log paths, or interpersonal branches.

## 4. Future implementation shape

This section defines a safe future shape only. It does not decide final code details and does not authorize implementation.

A future owner-approved implementation should likely:

1. create a feature flag or local constant initially disabled by default, for example:
   - `WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1=false`
2. route only the plan helper trigger through a narrow adapter.
3. build unified response formation shadow/live-safe candidate metadata.
4. preserve a fallback to the old canned plan helper.
5. attach metadata indicating:
   - `old_canned_path_shadowed=chat_responder_plan_helper`
   - `selected_candidate_family=ordinary_task_plan`
   - `canned_response_replaced=true` only after explicit owner approval in the implementation task
   - `safe_to_replace_live` remains false until a live task explicitly flips it under approval
6. avoid model/search/advisor calls.
7. avoid memory writes.
8. avoid `.weslr` state creation.
9. avoid raw private text storage.
10. avoid response generation from fixed prompt-specific scripts.
11. keep deterministic guardrails outside the demotion path.

The intended shape is a narrow bridge from the plan-helper trigger to the unified response formation path, not a new helper pile, not a broad router, and not a deterministic answer table.

## 5. Owner approval gate

No implementation may begin until all of the following conditions are met:

- owner explicitly approves the live slice task by name.
- implementation prompt says `WESLR_RUNTIME_CHANGE live behavior`.
- branch target is exactly `chat_responder_plan_helper`.
- rollback commands are included before edit.
- no unrelated files are changed.
- tests are added first or alongside implementation.
- release gate passes.
- release check passes.
- manual smoke test plan is defined.
- fallback path is preserved.
- no model/search/advisor calls are introduced.
- no memory writes are introduced.
- no raw private text storage is introduced.
- no `.weslr` runtime state is introduced.
- no broad runtime replacement is introduced.

If any approval condition is missing, the live slice must not be implemented.

## 6. Future implementation phases

### Phase 0 — current design

- Write this document only.
- No behavior change.
- No runtime/source edit.
- No live chat replacement.

### Phase 1 — pre-live implementation plan

- Inspect the exact plan helper branch.
- Produce an exact diff plan.
- Define rollback commands.
- Define tests.
- Owner approval required before edit.

### Phase 2 — owner-approved one-branch implementation

- Modify only the plan helper branch.
- Keep feature flag disabled or safe default unless owner explicitly approves enabling.
- Route the plan trigger through the unified response formation path.
- Preserve fallback to old canned behavior.
- Touch no other branch.

### Phase 3 — validation

- Focused tests.
- Canned helper comparison tests.
- Unified response formation shadow tests.
- Release gate.
- Release check.
- Manual smoke tests.

### Phase 4 — rollback or keep

- If output is worse, revert the commit or disable the feature flag.
- If output is better, keep the plan branch only.
- No expansion without a new review, new design, and new owner approval.

## 7. Future tests required before live implementation

A future implementation must include tests for:

- plan prompt no longer uses the fixed canned template when the feature is enabled.
- fallback remains available when the feature is disabled or formation fails.
- only the plan branch is affected.
- lunch/workout/email/code remain unchanged.
- guardrails remain unchanged.
- self/identity/protected/official boundaries remain unchanged.
- no model/search/advisor calls occur.
- no memory writes occur.
- no `.weslr` state is created.
- no raw private text is stored.
- metadata includes `old_canned_path_shadowed`.
- metadata includes `selected_candidate_family=ordinary_task_plan` or a safe clarification family.
- rollback path is documented.

Tests should assert properties and metadata, not exact prompt-response scripts.

## 8. Future smoke tests

Safe manual smoke tests for a future owner-approved implementation:

- “help me make a plan”
- “plan my next steps”
- “I need a plan for this project”
- compare old branch fallback vs new formation path.
- ensure output asks a clarifying question when context is missing.
- ensure output does not invent context.
- ensure no model/search/memory write occurs.
- ensure non-plan prompts are unchanged.

Do not run these smoke tests during this design task.

## 9. Future metadata contract

Future live slice metadata should include this shape:

```json
{
  "slice_type": "first_owner_approved_live_demotion_slice_v1",
  "target_branch": "chat_responder_plan_helper",
  "old_canned_path_shadowed": "chat_responder_plan_helper",
  "selected_candidate_family": "ordinary_task_plan",
  "fallback_available": true,
  "owner_approved": true,
  "feature_flag": "WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1",
  "canned_response_replaced": false,
  "safe_to_replace_live": false,
  "runtime_wiring": false,
  "live_runtime_output": false,
  "model_calls": false,
  "advisor_calls": false,
  "web_search": false,
  "solver_execution": false,
  "answer_selection_arbitration": false,
  "raw_text_stored": false,
  "memory_writes": false,
  "weslr_runtime_state_created": false
}
```

In this design document, `canned_response_replaced=false`, `runtime_wiring=false`, and `live_runtime_output=false` remain mandatory. Future implementation must not treat this metadata contract as permission to replace live behavior.

## 10. Rollback design

Future rollback requirements:

- identify changed files before live edit.
- save current commit hash.
- include `git diff --stat` before commit.
- include `git diff` before commit.
- rollback option 1: turn feature flag off.
- rollback option 2: `git revert <live-slice-commit>`.
- rollback option 3: restore the old plan helper branch if needed.
- verify rollback with focused tests and smoke tests.
- no expansion until rollback is verified.

Rollback must be treated as part of the design, not as an afterthought.

## 11. Anti-drift rule

Anti-drift rule:

Any future implementation under this design that touches anything beyond the plan helper branch violates the design.

Any future implementation that touches guardrails, identity/self, high-stakes, memory/write, model/search, evidence, status, staging raw-log, or interpersonal branches violates the design.

Any future implementation without explicit owner approval violates the design.

Any future implementation that removes fallback/rollback violates the design.

Any future implementation that enables broad response replacement violates the design.

Any future implementation that treats qualitative rank order as scoring, benchmark evaluation, live readiness, or final answer authority violates the design.

## 12. Recommended next task

Recommended next task:

`IMPLEMENT_WESLR_PLAN_HELPER_DEMOTION_PRELIVE_TESTS_AND_DIFF_PLAN_V1`

This next task is still pre-live. It should produce tests and an exact diff plan first. It should not change live behavior unless the owner explicitly approves a separate implementation task. It should not edit `chat_responder.py` unless the owner approves implementation in that separate task.

The likely implementation lane is plan-helper first, one branch only, owner-approved, rollback-ready, with release gate and release check required before keeping any change.
