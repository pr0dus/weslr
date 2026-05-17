# WESLR First Live Slice Process Canon V1

Marker: WESLR_FIRST_LIVE_SLICE_PROCESS_CANON_V1

## 1. Status / canon classification

- Document type: process canon
- Alignment layer: WESLR_CANON_ALIGNMENT
- Process canon only
- No runtime change in this task
- Live behavior changed by this document: no
- Runtime/source edits in this task: no
- Current verified decision: KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY
- Feature flag default false
- No default enablement
- No expansion without new approval

This document canonizes the First verified owner-approved live behavior slice. It records the process that safely moved WESLR from review/design loops into one tiny, reversible, owner-approved live slice.

## 2. Plain-language meaning

WESLR completed its first owner-approved live behavior slice. The slice targets Plan helper only, on One branch only: `chat_responder_plan_helper` in `weslr/chat_responder.py`.

The capability remains disabled by default. It is a controlled capability, not broad live chat replacement. It proves the safe process can work, but it does not authorize expansion, default enablement, or replacement of other branches.

The current verified posture is KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY. Feature flag default false remains the rule for this slice.

## 3. Chapter timeline

Design to live slice process:

1. Unified response formation canon existed and established one future response-formation path.
2. Canned helper branch inventory identified risky fixed ordinary cognition in legacy helper branches.
3. First canned-helper demotion slice design narrowed candidate branches.
4. Shadow scenarios were created for low-risk ordinary helper branches.
5. Scenario output review ranked plan first.
6. Owner-approved live demotion design locked Plan helper only.
7. Pre-live plan created future diff, tests, fallback, rollback, feature flag, and metadata boundaries.
8. Pre-live refinement added exact approval marker schema, metadata-is-not-approval rule, exact rollback commands, exact diff boundaries, and exact future tests.
9. Owner gave the exact approval marker: APPROVE_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1.
10. Implementation task: IMPLEMENT_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1.
11. Live slice implemented at commit `3ab2607`.
12. Verification discovered ordinary-task preemption.
13. Routing refinement at commit `076cefb` fixed flag-on normal runtime reachability.
14. Final verification decided: KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY.
15. OCC context alignment recorded latest state at commit `5b48b96`.

## 4. Why this process matters

This process avoids circling by converting review into a tiny reversible live slice. It avoids unsafe broad runtime replacement. It preserves owner governance. It proves WESLR can move from doctrine to behavior without treating one successful slice as permission to replace the system.

Deterministic guardrails are allowed. Deterministic answers are not core cognition.

This chapter also preserves the difference between:

- design/canon
- helper/test source
- live runtime behavior
- OCC context alignment

Canon does not equal runtime. Helper/test source does not equal public behavior. OCC context alignment does not equal WESLR runtime behavior. Live behavior requires explicit runtime/source changes, owner approval, tests, release gates, and verification.

## 5. Canonized process template

### A. Branch inventory

Future live-slice work must first identify the exact branch. It must classify the branch as one of:

- ordinary cognition
- guardrail
- status
- high-risk
- write path
- model path

Guardrail, status, self, write, search, model, and interpersonal branches must be rejected unless separately justified, scoped, and approved.

### B. Shadow scenario harness

Shadow scenario harnesses must be:

- in-memory
- no live calls
- no final answer authority
- no raw private text
- no model/search/advisor calls

### C. Output review helpers

Output review helpers may provide qualitative labels and branch readiness. They must not create scoring, benchmark claims, official claims, or live approval. They must not imply live readiness by metadata alone.

### D. Pre-live plan

A pre-live plan must document:

- target file/branch
- future diff metadata
- future test metadata
- fallback
- rollback
- feature flag default false
- owner approval gate

### E. Pre-live refinement

Pre-live refinement must add:

- exact approval marker
- metadata-is-not-approval rule
- exact rollback commands
- exact diff boundaries
- exact future tests

### F. Owner approval

Owner approval requires an exact marker. Approval is branch-specific. Approval does not authorize expansion. Approval does not imply default enablement.

### G. Implementation

Implementation must remain:

- one branch only
- feature flag default false
- Fallback preserved
- no model/search/advisor/memory/.weslr/raw-text paths
- no solver/arbitration
- covered by tests and release gates

### H. Post-live verification

Post-live verification must check:

- flag off behavior
- flag on behavior
- fallback
- non-branch protection
- side effects
- quality judgment
- keep/refine/rollback decision

### I. Context alignment

After the chapter, update context only if needed and distinguish:

- OCC_CONTEXT_ALIGNMENT
- WESLR_CANON_ALIGNMENT
- WESLR_RUNTIME_CHANGE

## 6. Canonized approval marker rule

Owner approval must be exact. The approval marker must name the target slice. The implementation task must declare `WESLR_RUNTIME_CHANGE live behavior`. Metadata is not approval. Approval is not reusable for other branches. Approval does not imply default enablement. Approval does not imply expansion.

Historical marker:

```text
APPROVE_WESLR_PLAN_HELPER_LIVE_DEMOTION_SLICE_V1
```

## 7. Canonized feature flag rule

First live slices should default false unless separately approved. A disabled-by-default capability is not default public behavior. Flag-on verification is required before enablement. Default enablement requires a separate owner approval, design, implementation, rollback, and verification path.

Feature flag default false is a release posture, not a temporary inconvenience.

## 8. Canonized rollback rule

Rollback must be planned before implementation. Rollback must include:

- fast flag rollback
- git rollback
- focused tests after rollback
- release gate after rollback
- release check after rollback

Expansion is blocked until rollback remains proven.

Rollback available is part of live-slice readiness. A slice without rollback is not ready for live implementation.

## 9. Canonized anti-expansion rule

Anti-drift rule: the First verified owner-approved live behavior slice does not authorize email/lunch/workout/code expansion.

No branch expansion is allowed without new inventory, design, approval, implementation, and verification.

No guardrail/status/self/write/model/search/interpersonal branch demotion is authorized under this process unless separately approved and scoped.

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
- context alignment commit: `5b48b96`
- decision: KEEP_AS_DISABLED_BY_DEFAULT_CAPABILITY
- expansion: no
- default enablement: no
- One branch only
- Plan helper only
- Fallback preserved
- Rollback available

## 11. What remains blocked

The following remain blocked:

- default enablement
- branch expansion
- email/lunch/workout/code demotion
- self/identity/consciousness branch replacement
- guardrail/status replacement
- evidence/search branch changes
- memory/write path changes
- model/advisor/search calls
- broad router replacement
- official certification/benchmark claims
- Turing-test/public intelligence claims
- voice wiring
- UI/staging/main changes

## 12. Recommended next lane

Preferred next lane, non-expansion:

```text
DESIGN_WESLR_PLAN_HELPER_FLAG_ON_LOCAL_OBSERVATION_V1
```

Alternative, also non-expansion:

```text
REVIEW_WESLR_FIRST_LIVE_SLICE_CANON_NO_IMPLEMENTATION
```

Do not expand to email, lunch, workout, or code yet. Do not enable the feature flag by default yet.

## 13. Safety statement

This is WESLR_CANON_ALIGNMENT process canon only. No runtime source behavior is changed by this document. No live WESLR behavior changed by this document. No `chat_responder.py` edit is authorized here. No broad release gate weakening is authorized here.
