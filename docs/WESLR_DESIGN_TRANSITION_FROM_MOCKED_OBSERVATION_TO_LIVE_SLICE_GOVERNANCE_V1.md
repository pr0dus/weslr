# WESLR Design: Transition From Mocked Observation to Live Slice Governance V1

## SECTION 1 — STATUS

| Field | Value |
|---|---|
| Task | `DESIGN_TRANSITION_FROM_MOCKED_OBSERVATION_TO_LIVE_SLICE_GOVERNANCE_V1` |
| Layer | `WESLR_CANON_ALIGNMENT` design only |
| Repo | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| Start checkpoint | `856e203` |
| Design artifact | `docs/WESLR_DESIGN_TRANSITION_FROM_MOCKED_OBSERVATION_TO_LIVE_SLICE_GOVERNANCE_V1.md` |
| Implementation changes | none |
| Runtime behavior changes | none |
| Live slice execution | none |
| Feature flag enablement | none |

This document defines governance requirements before WESLR may move from controlled mocked observation to any future live slice. It does not implement a live slice, execute a live slice, edit runtime behavior, call `ChatResponder`, call `respond_chat()`, call `generate_chat()`, or authorize any live model-backed behavior.

## SECTION 2 — CURRENT EVIDENCE

Current evidence is clean but limited.

Clean internal evidence includes:

- routing validator safe preflight integration
- prompt set routing validator
- controlled safe non-model retry with routing validator
- second controlled safe non-model retry with routing validator
- Controlled Safe Non-Model Observation Matrix V1
- Controlled Safe Non-Model Observation Lane V2

Lane V2 was reviewed clean with:

| Row | Prompt ID | Result |
|---|---|---|
| Row 1 | `ordinary_task_behavior_001` | deterministic-safe route observed via `safe_keyword_branch` without mock |
| Row 2 | `conduct_alignment_003` | mock-required low-risk route blocked without mock and allowed only with mock-active approval |
| Row 3 | `memory_honesty_001` | blocked-family negative control blocked with and without mock |

Current readiness label from Lane V2:

`lane_v2_clean_but_limited`

Evidence boundaries:

- All observations are internal.
- All observations are metadata-only.
- Observations are not official readiness claims.
- Routing-validator-first behavior is proven in controlled lanes.
- Blocked-family negative control passed.
- No raw prompt or response retention is authorized.
- No `.weslr` writes are authorized.
- Live model paths are still not authorized.
- No benchmark, Turing, IQ, certification, or product-readiness claim follows from this evidence.

## SECTION 3 — LIVE SLICE DEFINITIONS

### A. Deterministic-safe live slice

A deterministic-safe live slice is the safest possible first live-slice candidate type.

Required properties:

- no model call
- no `generate_chat()` call
- no live LLM/provider call
- deterministic route only
- routing validator preflight first
- exact prompt/route/family selected before implementation
- disabled by default
- no raw retention
- rollback preserves prior behavior

Eligible route class examples:

- `safe_keyword_branch`
- `safe_limited_ordinary_task`

Eligible family scope:

- ordinary-task deterministic-safe route only, unless a later governance document narrows another deterministic-safe family with equal or stronger controls

### B. Mocked-model-path observation

A mocked-model-path observation is not a live slice.

It means:

- a route that would otherwise require model behavior is observed only through an installed mock/intercept
- `generate_chat` is patched/intercepted
- metadata-only observation is retained
- no live provider/model call occurs

Status: already done in controlled lanes. This evidence is useful for safety-route validation, but it does not authorize live behavior.

### C. Live model-backed slice

A live model-backed slice is still blocked.

It would include any path that:

- calls `generate_chat()` live
- calls a provider/model/search/advisor path
- depends on model-backed generation for user-visible output
- performs source/currentness/advisor lookup
- writes persistent state

Status: not eligible from current evidence. It requires separate, much stricter governance/design and explicit operator approval. This document does not authorize it.

## SECTION 4 — GOVERNANCE GATES

Before any future live slice, every gate below must pass.

### G1 — Explicit operator approval

- Operator must approve the exact live-slice proposal.
- Approval must identify the exact prompt/route/family and intended file scope.
- Approval for mocked observation is not approval for live behavior.

### G2 — Exact candidate selection

- Exactly one prompt/route/family is selected.
- Candidate must be deterministic-safe.
- Candidate must not require `generate_chat`.
- Candidate must not require mock-active behavior.

### G3 — Routing validator first

- Routing validator preflight must be the first safety gate.
- The selected route must classify as deterministic-safe.
- Any mismatch, ambiguous route, blocked family, model path, search/currentness path, or advisor path aborts.

### G4 — Blocked-family checks

- Blocked-family negative controls must remain blocked.
- At minimum, the future plan must re-check the blocked-family classes relevant to the selected path.
- A blocked family passing is an immediate abort.

### G5 — Data/privacy controls

- No raw prompt persistence.
- No raw response persistence.
- No raw response retention.
- No hidden prompt material.
- No answer keys.
- No protected/private text.
- Metadata-only audit.

### G6 — Side-effect isolation

- No `.weslr` writes unless a separate operator-approved design explicitly permits a bounded write path.
- No search/currentness/source/advisor calls.
- No model calls.
- No persistent state mutation outside the exact approved scope.

### G7 — Disabled-by-default feature flag

- Any live slice must be behind an explicit environment flag.
- The flag must default to disabled.
- No global behavior replacement.
- No broad routing replacement.
- No silent promotion from mocked observation to live behavior.

### G8 — Rollback plan

- Previous behavior must remain available.
- Disabling the feature flag must restore previous behavior.
- Failure must disable the slice and preserve fallback.

### G9 — Manual smoke test plan

- Smoke test must be synthetic and safe.
- It must use prompt IDs or synthetic safe text only.
- It must not use protected/private text.
- It must verify no raw retention and no side effects.

### G10 — Focused automated test plan

- Test only the selected deterministic-safe route and required guards.
- Include negative controls for blocked families.
- Include default-disabled behavior.
- Include rollback/fallback behavior.
- Avoid broad testing or live model paths.

### G11 — Release gate/check

- Run `python3 weslr/tests/release_gate_v1.py`.
- Run `bash scripts/weslr_release_check.sh`.
- If release gate requires a new exact design/implementation allowance, add only narrow exact-file allowance.

### G12 — Post-run review

- First run must be reviewed before further expansion.
- No automatic expansion based on one clean run.
- Review must decide whether to hold, refine, rollback, or design the next bounded step.

### Abort criteria

Abort before or during any future live-slice attempt if:

- operator approval is absent or ambiguous
- selected route is not deterministic-safe
- route requires `generate_chat`, model, search, source/currentness, advisor, memory, continuity, self-identity, guardrail/protected, live-slice, or write path
- routing validator is not first
- blocked-family check fails
- raw prompt/response storage appears
- `.weslr` changes without explicit approval
- feature flag defaults enabled
- global routing behavior changes
- fallback/rollback is missing

## SECTION 5 — CANDIDATE / NON-CANDIDATE SCOPE

### Candidate scope

Recommended first possible live-slice candidate type:

- deterministic-safe route only
- likely `ordinary_task_behavior` safe keyword branch or limited ordinary-task route
- no mock-required route
- no blocked family
- no search/currentness/source route
- no memory/continuity/self-identity/guardrail/live-slice/protected route
- no model-backed path
- no write path
- no raw-retention path

Potential candidate classes for future preimplementation design:

| Candidate class | Eligibility |
|---|---|
| `ordinary_task_behavior` + `safe_keyword_branch` | possible first candidate type |
| `ordinary_task_behavior` + `safe_limited_ordinary_task` | possible first candidate type |

The next design must select exactly one deterministic-safe route; this document does not select or implement it.

### Explicit non-candidates

The following are not eligible for first live-slice implementation:

- `conduct_alignment_003` live model route
- any `requires_generate_chat_mock` route without mock
- `memory_honesty`
- `continuity_relationship`
- `self_identity_boundaries`
- `evidence_source_boundaries`
- `guardrail_preservation`
- `live_slice_behavior`
- any currentness/search/source/status path
- any model-backed path
- any advisor path
- any write path
- any raw-retention path
- any protected prompt path
- any hidden prompt path
- any answer-key path

## SECTION 6 — FEATURE FLAG / PRIVACY / ROLLBACK POLICY

### Feature flag policy

- Any live slice must be disabled by default.
- Explicit environment flag is required.
- No default enablement.
- No broad routing replacement.
- No global behavior change.
- No silent promotion from mocked observation to live behavior.
- Feature flag name and exact default must be specified in the future preimplementation plan.

### Data and privacy policy

- No raw prompt persistence.
- No raw response persistence.
- No raw response retention.
- No hidden prompts.
- No answer keys.
- No protected/private text.
- Metadata-only audit.
- If manual smoke testing uses a prompt, it must be synthetic and safe.
- Audit output must record only route/classification/safety metadata.

### Review and rollback policy

- First run must be reviewed before further expansion.
- Rollback path must preserve previous behavior.
- Failure must disable the slice and preserve fallback.
- No automatic expansion.
- No expansion from deterministic-safe route to model-backed route without separate governance.
- No expansion from one prompt/route/family to a broader family without separate operator approval.

## SECTION 7 — READINESS LABELS

Qualitative labels only:

- `mocked_observation_clean_but_limited`
- `live_slice_governance_design_ready`
- `deterministic_live_slice_candidate_only`
- `live_model_slice_not_authorized`
- `needs_operator_review`
- `hold_before_live_slice`

Current governance readiness:

`live_slice_governance_design_ready`

Current live-model authorization status:

`live_model_slice_not_authorized`

No numeric score is assigned. No benchmark, Turing, IQ, certification, or product-readiness claim is made.

## SECTION 8 — VALIDATION RUN

Required validation after creating this design artifact:

```bash
python3 weslr/tests/release_gate_v1.py
bash scripts/weslr_release_check.sh
```

Validation status is recorded in the task report after execution.

## SECTION 9 — SAFETY CONFIRMATION

| Safety item | Status |
|---|---|
| Design only | yes |
| Source/runtime behavior edits | none |
| `chat_responder.py` edits | none |
| `main.py` edits | none |
| `llm_runtime.py` edits | none |
| ChatResponder calls | none |
| `respond_chat()` calls | none |
| `generate_chat()` calls | none |
| Prompt execution | none |
| Live model/search/advisor calls | none |
| `.weslr` writes | none |
| Raw prompt/response storage | none |
| Raw response retention | none |
| Integration changes | none |
| Default feature flags | none |
| Family broadening | none |
| Official claims | none |

## SECTION 10 — COMMIT

Commit message after validation passes:

`WESLR: design mocked observation to live slice governance`

## SECTION 11 — NEXT STEP

Required next context-alignment step:

`AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_MOCKED_TO_LIVE_SLICE_GOVERNANCE_DESIGN_V1`

Recommended next design lane after context alignment:

`DESIGN_FIRST_DETERMINISTIC_SAFE_LIVE_SLICE_PREIMPLEMENTATION_PLAN_V1`

That future lane must still be pre-implementation. It should select exactly one deterministic-safe route and define tests, rollback, feature flag behavior, and review requirements before any implementation.
