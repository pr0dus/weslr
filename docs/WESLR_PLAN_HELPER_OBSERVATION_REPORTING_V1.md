# WESLR Plan Helper Observation Reporting V1

Marker: WESLR_PLAN_HELPER_OBSERVATION_REPORTING_V1

## 1. Status / classification

- Document type: observation reporting design
- Alignment layer: WESLR_CANON_ALIGNMENT
- Observation reporting design only
- No runtime change in this task
- Live behavior changed by this document: no
- Runtime/source edits in this task: no
- Feature flag default remains false
- Feature flag default false
- No default enablement
- Current stable decision: HOLD_AND_OBSERVE_PLAN_HELPER_DISABLED_BY_DEFAULT
- Current operational state: KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY
- Scope: Plan helper only
- Branch scope: One branch only
- No expansion without new approval

This document defines how future local observations of the disabled-by-default plan-helper live slice should be reported safely and consistently. It does not implement observation storage, does not run observation, does not authorize default enablement, and does not authorize branch expansion.

## 2. Plain-language meaning

The plan-helper live slice is implemented, verified, quality-refined, and kept disabled by default. It is a controlled capability behind `WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1`, not normal/default public behavior.

Future observations should be recorded consistently if the flag is used locally. Observation reports are not benchmark results. Observation reports are not public claims. Observation reports are not default enablement evidence by themselves. Repeated safe observations may later support a separate readiness design, but they do not themselves authorize default enablement.

The safe posture remains HOLD_AND_OBSERVE_PLAN_HELPER_DISABLED_BY_DEFAULT and KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY.

## 3. Reporting purpose

Future observation reports should capture:

- flag-off baseline status
- flag-on plan response behavior
- metadata correctness
- quality of the refined plan shape
- fallback status
- non-plan protection
- side-effect checks
- cleanup status
- decision after observation

The report should summarize observable properties of the slice, not copy private user text or turn the observation into a benchmark, score, Turing-test claim, certification claim, or public product claim.

## 4. Safe report principles

Reports must:

- No raw private text
- avoid raw private user text
- use synthetic or short non-private prompts only
- avoid full response dumps unless explicitly synthetic and safe
- summarize response properties rather than copy entire output
- avoid hidden prompt text
- avoid answer keys
- avoid protected materials
- avoid source URLs unless explicitly safe and needed
- avoid official score/certification/Turing/IQ/benchmark claims
- avoid storing raw private text in docs or runtime state
- distinguish local observation from public/default enablement
- keep Fallback preserved
- keep Rollback available

Reports must not create `.weslr` runtime state and must not store raw private text.

## 5. Observation report schema

Safe future reports may use this JSON-compatible schema:

```json
{
  "report_type": "plan_helper_flag_on_observation_report_v1",
  "schema_version": "1.0",
  "timestamp_local": "<operator supplied>",
  "repo_head": "<commit hash>",
  "feature_flag": "WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1",
  "feature_flag_default": false,
  "flag_enabled_for_process_only": true,
  "target_branch": "chat_responder_plan_helper",
  "target_file": "weslr/chat_responder.py",
  "observation_scope": "plan_helper_only",
  "raw_private_text_included": false,
  "benchmark_claim": false,
  "turing_test_claim": false,
  "default_enablement_claim": false,
  "branch_expansion_claim": false,
  "flag_off_baseline": {
    "checked": true,
    "plan_metadata_absent": true,
    "existing_behavior_active": true
  },
  "flag_on_plan_checks": {
    "checked": true,
    "approved_prompt_count": 0,
    "slice_metadata_present": true,
    "quality_shape_present": true,
    "invented_context_observed": false
  },
  "non_plan_protection": {
    "checked": true,
    "plan_metadata_on_non_plan": false
  },
  "side_effects": {
    "model_calls": false,
    "advisor_calls": false,
    "web_search": false,
    "solver_execution": false,
    "answer_selection_arbitration": false,
    "memory_writes": false,
    "weslr_runtime_state_created": false,
    "raw_text_stored": false
  },
  "fallback": {
    "fallback_available": true,
    "fallback_problem_observed": false
  },
  "cleanup": {
    "feature_flag_unset_after": true,
    "tracked_diff_after": false,
    "runtime_artifacts_retained": false
  },
  "decision": "KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY"
}
```

The schema is descriptive only. This document does not implement storage or runtime reporting.

## 6. Required report sections

A future Markdown report should use this structure:

```text
SECTION 1 — STATUS
SECTION 2 — FLAG-OFF BASELINE
SECTION 3 — FLAG-ON PLAN OBSERVATION
SECTION 4 — PLAN QUALITY CHECK
SECTION 5 — NON-PLAN PROTECTION
SECTION 6 — SIDE-EFFECT CHECK
SECTION 7 — FALLBACK / ROLLBACK STATUS
SECTION 8 — CLEANUP
SECTION 9 — DECISION
SECTION 10 — SAFETY CONFIRMATION
```

Each section should be brief, sanitized, and evidence-oriented. The report should state what was checked and what was observed without including raw private text.

## 7. Quality rubric

Use qualitative labels only. Do not use numeric scores. Do not call the result benchmark performance. Do not compare behavior to human, Turing-test, or IQ performance.

Allowed quality labels:

- `useful_enough_disabled_default`
- `safe_but_thin`
- `needs_context_handling_refinement`
- `unsafe_or_too_broad`
- `not_observed`

Quality dimensions:

- reaches approved slice
- asks useful clarifying question
- includes bounded starter shape
- does not invent project details
- avoids old canned wording
- remains concise
- remains safe
- avoids high-stakes drift

A quality label is a local observation summary, not a score, benchmark, certification, or readiness claim.

## 8. Decision categories

Allowed future decisions:

### A. KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY

Use when the slice is safe/useful enough locally but remains disabled by default. This decision means no default enablement and no expansion.

### B. REFINE_FLAG_ON_BEHAVIOR

Use when the slice is safe but quality needs improvement. No rollback is required unless safety or side effects are implicated.

### C. DISABLE_OR_REVERT

Use when the slice is unsafe, too broad, affects protected branches, creates side effects, stores raw text, or otherwise violates the slice boundary.

### D. CONSIDER_DEFAULT_ENABLEMENT_READINESS_DESIGN

Use only after repeated safe observations. This is design only. Observation alone must not enable the feature by default.

## 9. Repetition / evidence guidance

One observation is not enough for default enablement. Repeated observations should be consistent, sanitized, and comparable over time. Any safety failure, branch capture failure, side-effect failure, fallback failure, cleanup failure, or raw-text retention failure should block enablement design until resolved.

Observation reports should track decisions over time. A future readiness design should cite multiple safe observation reports, not just one run. Even repeated safe reports remain evidence for a separate owner-approved readiness design, not automatic authorization.

## 10. Storage guidance

This design does not implement storage.

If future storage is needed, use a separately approved safe location such as `docs/observations/` and store only sanitized report files. Future stored reports must contain:

- no raw private text
- no hidden prompts
- no answer keys
- no protected material
- no `.weslr` runtime state unless separately designed and approved

Reports should avoid source URLs unless explicitly safe and needed. Reports should not persist full outputs unless the prompts and outputs are synthetic, non-private, and explicitly safe.

## 11. Anti-drift rule

Anti-drift rule:

- Observation reports do not enable the feature by default.
- Observation reports do not authorize branch expansion.
- Observation reports do not authorize live implementation.
- Observation reports do not authorize public/benchmark/Turing/certification claims.
- Any default enablement requires separate owner-approved design/implementation/verification.
- Any second branch requires a full new cycle.

No benchmark claims. No Turing-test claims. No fake consciousness claims. No public certification claims. No expansion without new approval.

Deterministic guardrails are allowed. Deterministic answers are not core cognition.

## 12. Current slice record

- target: plan helper
- target branch: `chat_responder_plan_helper`
- target file: `weslr/chat_responder.py`
- feature flag: `WESLR_ENABLE_PLAN_HELPER_DEMOTION_V1`
- default: false
- owner marker: `APPROVE_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1`
- implementation commit: `3ab2607`
- routing refinement commit: `076cefb`
- quality refinement commit: `61b75ba`
- context alignment commit: `78177e8`
- decision: HOLD_AND_OBSERVE_PLAN_HELPER_DISABLED_BY_DEFAULT
- operational state: KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY
- expansion: no
- default enablement: no
- Feature flag default false
- Fallback preserved
- Rollback available

## 13. Recommended next lane

Recommended next lane:

```text
HOLD_AND_OBSERVE_PLAN_HELPER_DISABLED_BY_DEFAULT
```

Alternative future lane only when useful:

```text
RUN_WESLR_PLAN_HELPER_FLAG_ON_LOCAL_OBSERVATION_V1
```

Do not recommend immediate second branch, default enablement, broad live chat replacement, voice/runtime/UI wiring, or any public benchmark/Turing/certification claim.
