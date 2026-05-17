# WESLR Plan Helper Flag-On Local Observation Design V1

Marker: WESLR_PLAN_HELPER_FLAG_ON_LOCAL_OBSERVATION_DESIGN_V1

## 1. Status / classification

- Document type: observation design/process doc
- Alignment layer: WESLR_CANON_ALIGNMENT
- Observation design only
- No runtime change in this task
- Live behavior changed by this document: no
- Runtime/source edits in this task: no
- Feature flag default false
- No default enablement
- Current verified decision remains: KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY

This document defines a safe future protocol for local observation of the existing plan-helper live demotion slice with its feature flag enabled only for a local command/test process.

## 2. Plain-language meaning

The plan-helper live slice exists and is verified. It remains disabled by default. Local flag-on observation means temporary, controlled, operator-run checks only for:

```text
WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1=1
```

Local observation is not public enablement. It does not mean default enablement. It does not authorize expansion. It does not authorize public claims, benchmarks, Turing-test claims, IQ claims, or certification claims.

The slice remains Plan helper only and One branch only.

## 3. Observation goal

A future local observation should learn whether:

- flag-on plan responses are useful in ordinary planning prompts
- responses are less canned than the old fixed template
- responses ask for missing context when needed
- responses avoid inventing unstated goals, timelines, details, or private facts
- metadata is present and correct
- fallback remains available
- non-plan prompts remain protected
- side-effect flags remain false
- no `.weslr` runtime state is created
- no raw private text is created, retained, or stored

The observation is a qualitative safety/usefulness check, not scoring, not benchmarking, not certification, and not answer-selection arbitration.

## 4. Observation scope

Allowed scope:

- Plan helper only
- local/in-process checks only
- feature flag enabled only for the command/test process
- no default enablement
- no service-level enablement
- no deployment/staging enablement
- no public demo enablement
- no expansion to other branches

Explicitly out of scope:

- email helper
- lunch helper
- workout helper
- code/bug helper
- wife/partner/interpersonal helper
- self/identity/consciousness/system/benchmark responses
- evidence/search/PubMed paths
- memory/write paths
- status/command surfaces
- broad router replacement
- UI/voice/staging/main changes
- official benchmark/Turing/IQ/certification claims

## 5. Safe observation protocol

This is a future operator protocol. Do not run it as part of creating this document.

### A. Pre-check

Before any local observation, the operator should:

- confirm clean git status, except known pre-existing untracked docs if explicitly accepted for the observation environment
- confirm current HEAD
- confirm the feature flag default remains false in source/runtime configuration
- confirm release gate/check currently pass if the observation is being run as part of a controlled validation lane

### B. Flag-off baseline

With the feature flag unset:

- run a safe in-process plan prompt
- verify no plan-demotion metadata appears
- verify existing behavior remains active
- verify no side effects are produced

### C. Flag-on local observation

Enable the flag only for the command process:

```text
WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1=1
```

Use safe in-process `ChatResponder.respond_chat(...)` style checks only. Use non-private test prompts such as:

- `plan`
- `help me plan`
- `plan my next steps`
- `I need a plan for this project`

Verify plan-demotion metadata appears only for approved plain plan prompts.

### D. Non-plan protection checks

Check that the plan demotion slice does not capture or replace:

- lunch
- workout
- email
- code/bug
- lunch+plan combined prompt
- search/current/evidence-like prompt
- memory/status-like prompt
- protected/hidden prompt-like safe synthetic prompt
- self/identity prompt

### E. Side-effect checks

Confirm:

- no model calls
- no advisor calls
- no web/search calls
- no solver execution
- no answer-selection arbitration
- no memory writes
- no `.weslr` state
- no raw private text storage
- no source registry/truth writes

### F. Cleanup

After local observation:

- unset the feature flag
- remove any transient ignored runtime artifacts if generated
- confirm no tracked diffs
- confirm no retained raw private text
- run focused tests, release gate, and release check if needed

Fallback preserved. Rollback available.

## 6. Suggested future command shapes

These are future command shapes only. They are examples for a later task, not commands to run while creating this design.

Flag-off:

```bash
python - <<'PY'
# import ChatResponder and inspect plan response without setting env flag
PY
```

Flag-on local only:

```bash
WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1=1 python - <<'PY'
# import ChatResponder and inspect plan response metadata
PY
```

Focused tests and gates:

```bash
python -m pytest -q weslr/tests/test_plan_helper_live_demotion_slice_v1.py
python3 weslr/tests/release_gate_v1.py
bash scripts/weslr_release_check.sh
```

Do not include raw private prompts. Do not include real hidden prompts. Do not include answer keys.

## 7. Observation result categories

Future local observation should end in one of these categories:

### A. KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY

Use this if behavior is safe/useful but still should not become default behavior.

### B. REFINE_FLAG_ON_BEHAVIOR

Use this if plan output is safe but too generic, too thin, or lacks useful context handling.

### C. DISABLE_OR_REVERT

Use this if behavior is unsafe, broad, affects non-plan branches, weakens guardrails, or creates side effects.

### D. CONSIDER_DEFAULT_ENABLEMENT_DESIGN

Use this only after repeated safe observations. It requires separate design, owner approval, implementation, rollback, and verification. It is not allowed by this document.

## 8. Observation record format

A safe future observation report should use this format:

```text
SECTION 1 — STATUS
SECTION 2 — FLAG-OFF BASELINE
SECTION 3 — FLAG-ON PLAN OBSERVATION
SECTION 4 — NON-PLAN PROTECTION
SECTION 5 — SIDE-EFFECT CHECK
SECTION 6 — QUALITY JUDGMENT
SECTION 7 — DECISION
SECTION 8 — SAFETY CONFIRMATION
```

Observation records must not include:

- raw private user text
- hidden prompts
- answer keys
- protected materials
- source URLs unless explicitly safe and needed
- official score/certification/Turing/IQ claims

## 9. Anti-drift rule

Anti-drift rule:

- This design does not enable the feature by default.
- This design does not authorize new live implementation.
- This design does not authorize expansion to email/lunch/workout/code.
- This design does not authorize public claims.
- This design does not authorize model/search/advisor/memory/write paths.
- Any default enablement requires a separate owner-approved design and implementation.
- Any branch expansion requires a new inventory/design/approval/implementation/verification cycle.

No expansion without new approval.

Deterministic guardrails are allowed. Deterministic answers are not core cognition.

## 10. Current verified slice record

- slice type: `first_owner_approved_live_demotion_slice_v1`
- target: plan helper
- target branch: `chat_responder_plan_helper`
- target file: `weslr/chat_responder.py`
- feature flag: `WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1`
- default: false
- owner marker: `APPROVE_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1`
- implementation commit: `3ab2607`
- routing refinement commit: `076cefb`
- process canon commit: `daa6c96`
- context alignment commit: `5b48b96`
- decision: KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY
- expansion: no
- default enablement: no
- Feature flag default false
- Plan helper only
- One branch only
- Fallback preserved
- Rollback available

## 11. Recommended next lane

Recommended next lane:

```text
RUN_WESLR_PLAN_HELPER_FLAG_ON_LOCAL_OBSERVATION_V1
```

The next lane should run observation only. It should make no code changes. It should make no commits unless a report document is explicitly requested. It must not enable by default. It must not expand branches.

## 12. Safety statement

This is WESLR_CANON_ALIGNMENT observation design only. No runtime source behavior changes are made by this document. No live WESLR behavior changes are made by this document. No `chat_responder.py` edits are authorized here. No broad release gate weakening is authorized here.
