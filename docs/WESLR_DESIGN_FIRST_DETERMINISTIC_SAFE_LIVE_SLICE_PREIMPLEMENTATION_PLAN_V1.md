# WESLR Design: First Deterministic-Safe Live Slice Preimplementation Plan V1

## SECTION 1 — STATUS

| Field | Value |
|---|---|
| Task | `DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1` |
| Layer | `WESLR_CANON_ALIGNMENT` design only |
| Repo | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Start checkpoint | `d24fb5b` |
| Design artifact | `docs/WESLR_DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1.md` |
| Implementation changes | none |
| Runtime behavior changes | none |
| Live slice execution | none |
| Feature flag enablement | none |

This document is a preimplementation plan for a possible future deterministic-safe live slice. It is not implementation, not execution, not a live model-backed slice, not product readiness, and not a benchmark, Turing, IQ, certification, or product-readiness claim.

Current evidence remains clean but limited. Lane V2 readiness remains `lane_v2_clean_but_limited`. Live model-backed slices remain unauthorized.

## SECTION 2 — CONTEXT / PURPOSE

Purpose: define the first bounded preimplementation plan for a future deterministic-safe ordinary-task slice while preserving the existing governance boundary.

This plan exists only to prepare review. It does not:

- edit runtime behavior
- enable a feature flag
- call `ChatResponder`
- call `respond_chat()`
- call `generate_chat()`
- execute prompts
- call model/search/advisor paths
- write `.weslr` state
- retain raw prompt or response text
- broaden families
- replace routing globally

The future implementation, if separately approved, must be routing-validator-first, disabled by default, exact-candidate-only, metadata-only, rollback-safe, and reviewed after the first run before any expansion.

## SECTION 3 — CANDIDATE DEFINITION

Recommended first candidate:

| Field | Required value |
|---|---|
| prompt_id | `ordinary_task_behavior_001` |
| family | `ordinary_task_behavior` |
| route | `safe_keyword_branch` |
| candidate label | `deterministic_safe_live_slice_candidate_only` |
| model call | no |
| `generate_chat()` | no |
| search/currentness/source/status path | no |
| write path | no |
| raw retention | no |
| blocked family | no |
| mock-required route | no |

Rationale:

- Lane V2 observed `ordinary_task_behavior_001` as deterministic-safe without mock.
- The routing validator classifies it as `safe_keyword_branch` and aligned.
- It is allowed without mock by the routing validator.
- It does not require `generate_chat()`.
- It is inside ordinary-task scope and is the narrowest available candidate for a future deterministic-safe slice.

Acceptable route class for any future implementation is limited to `safe_keyword_branch`. A future reviewer may allow `safe_limited_ordinary_task` only by separate exact approval, but this V1 plan recommends `ordinary_task_behavior_001` / `safe_keyword_branch` only.

## SECTION 4 — NON-CANDIDATES

The following are explicitly excluded from the future first slice:

- `conduct_alignment_003`
- any `requires_generate_chat_mock` route
- any model-backed route
- any live `generate_chat()` path
- `memory_honesty`
- `continuity_relationship`
- `self_identity_boundaries`
- `evidence_source_boundaries`
- `guardrail_preservation`
- `live_slice_behavior`
- source/currentness/search/status paths
- protected/hidden/answer-key paths
- write paths
- raw-retention paths
- any blocked family
- any mock-required route
- any prompt outside the exact selected prompt ID

`conduct_alignment_003` remains useful only as mocked-observation evidence. It is not a deterministic-safe first live-slice candidate because it requires `requires_generate_chat_mock` when allowed.

## SECTION 5 — FUTURE IMPLEMENTATION CONSTRAINTS

A future implementation must obey all constraints below:

1. Disabled by default.
2. Requires explicit operator approval before implementation.
3. Requires explicit environment flag before activation.
4. Guards exact prompt ID: `ordinary_task_behavior_001`.
5. Guards exact family: `ordinary_task_behavior`.
6. Guards exact route: `safe_keyword_branch`.
7. Runs routing validator first.
8. Allows deterministic route only.
9. Has no fallback to model path.
10. Has no fallback to `generate_chat()`.
11. Has blocked-family guard before any callable construction.
12. Keeps side effects isolated.
13. Records metadata-only audit fields.
14. Persists no raw prompt text.
15. Persists no raw response text.
16. Retains no raw response.
17. Preserves previous behavior when disabled.
18. Disables slice and preserves fallback on failure.
19. Performs no automatic expansion.
20. Makes no official benchmark, Turing, IQ, certification, or product-readiness claim.

If any future code path would require `chat_responder.py`, that implementation is higher-risk and requires separate explicit operator approval. The preferred future approach is to avoid `chat_responder.py`, `main.py`, and `llm_runtime.py`.

## SECTION 6 — FEATURE FLAG / PRIVACY / ROLLBACK PLAN

### Proposed feature flag

`WESLR_ENABLE_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_V1=1`

Rules:

- absent means old behavior
- empty means old behavior
- false-like values mean old behavior
- true is only the exact string `1`
- `1` enables only the exact candidate slice
- no global enablement
- no broad routing replacement
- no silent promotion from mocked observation to live behavior
- no family broadening
- no model-backed route activation

### Privacy rules

The future implementation may persist only metadata such as:

- prompt ID
- family
- route class
- routing validator status
- feature flag enabled/disabled state
- blocked/allowed boolean
- side-effect check booleans
- readiness label

It must not persist:

- raw prompt text
- raw response text
- response dumps
- full conversations
- hidden prompt material
- answer keys
- protected/private text

### Rollback plan

Rollback is:

1. unset `WESLR_ENABLE_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_V1`
2. confirm old behavior is restored
3. revert the implementation commit if needed
4. record a failure report with metadata only
5. stop; no automatic retry and no expansion

Rollback must preserve prior behavior. Failure must disable the slice and preserve fallback.

## SECTION 7 — TEST / SMOKE PLAN

### Future implementation files

Likely future files, subject to separate approval:

- `weslr/real_chatresponder_shadow_call_helpers.py` only if helper integration is needed
- `weslr/tests/test_first_deterministic_safe_live_slice_v1.py` as the focused test file

Avoid if possible:

- `weslr/chat_responder.py`
- `main.py`
- `llm_runtime.py`

If `weslr/chat_responder.py` becomes necessary, mark the implementation higher-risk and require separate approval before editing.

### Preimplementation test plan

Future tests must cover:

- flag disabled: no live slice active
- flag enabled: only exact deterministic-safe candidate considered
- routing validator runs first
- candidate route is `safe_keyword_branch`
- no model path reachable
- no `generate_chat()` path reachable
- blocked families remain blocked
- mock-required routes remain blocked
- currentness/search/source/status routes remain blocked
- no `.weslr` writes
- no raw prompt/response retention
- rollback/fallback behavior preserved
- `python3 weslr/tests/release_gate_v1.py` passes
- `bash scripts/weslr_release_check.sh` passes

Negative controls must include at minimum:

- `conduct_alignment_003` remains non-candidate / mock-required only
- `memory_honesty_001` remains blocked-family negative control
- a search/currentness/source/status route remains blocked

### Smoke test plan

A future manual smoke test may run only after separate approval and implementation review.

Smoke test constraints:

- one synthetic safe prompt ID only: `ordinary_task_behavior_001`
- metadata-only result
- no raw prompt/response persistence
- no live model calls
- no search calls
- no advisor calls
- no `.weslr` writes
- immediate post-run review
- feature flag disabled after the test unless explicitly approved otherwise

## SECTION 8 — ABORT CRITERIA

Abort future implementation or run if any condition occurs:

- model path is reachable
- `generate_chat()` path is reachable
- routing validator is not first
- candidate family differs from `ordinary_task_behavior`
- candidate route differs from `safe_keyword_branch`
- candidate prompt ID differs from `ordinary_task_behavior_001`
- raw prompt appears in persisted output
- raw response appears in persisted output
- `.weslr` changes unexpectedly
- feature flag defaults on
- blocked family passes
- search/currentness/source/status path passes
- mock-required route passes as deterministic-safe
- tests fail
- release gate/check fail
- implementation touches unapproved files
- behavior expands automatically

## SECTION 9 — READINESS LABELS

Qualitative labels for this plan:

- `preimplementation_plan_ready`
- `deterministic_safe_live_slice_candidate_only`
- `live_model_slice_not_authorized`
- `needs_operator_review`
- `hold_before_live_slice`

No numeric score is assigned. No official benchmark, Turing, IQ, certification, or product-readiness claim is made.

## SECTION 10 — VALIDATION RUN

Required validation after this design document is staged:

```bash
python3 weslr/tests/release_gate_v1.py
bash scripts/weslr_release_check.sh
```

If the release gate requires recognition of this exact new design artifact, only a narrow exact-file allowance may be added. Broad release-gate weakening is not allowed.

## SECTION 11 — SAFETY CONFIRMATION

| Check | Status |
|---|---|
| Design only | yes |
| Implementation performed | no |
| Runtime behavior changed | no |
| Feature flag enabled | no |
| ChatResponder called | no |
| `respond_chat()` called | no |
| `generate_chat()` called | no |
| Prompt executed | no |
| Live model/search/advisor call | no |
| `.weslr` write | no |
| Raw prompt/response retained | no |
| Family scope broadened | no |
| Official readiness claim | no |

## SECTION 12 — COMMIT

Planned commit message if validation passes:

`WESLR: design first deterministic safe live slice preimplementation plan`

## SECTION 13 — NEXT STEP

Recommended next lane:

`REVIEW_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_NO_IMPLEMENTATION`

Only after review and explicit operator approval should the next lane be considered:

`IMPLEMENT_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_GUARDS_V1`

Do not execute a live slice directly after this design.
