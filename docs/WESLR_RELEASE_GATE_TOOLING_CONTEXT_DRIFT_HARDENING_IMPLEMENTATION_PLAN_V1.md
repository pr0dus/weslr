# WESLR Release Gate Tooling Context Drift Hardening Implementation Plan V1

## Purpose

Plan the future implementation of release-gate tooling-context drift hardening without changing release-gate behavior yet.

This lane is plan-only. It does not implement hardening, alter runtime behavior, edit public docs, or change deployment.

## Basis

- Design: `docs/WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_V1.md`
- Review: `docs/WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_REVIEW_V1.md`
- Review judgment: `release_gate_tooling_context_drift_hardening_design_valid_ready_for_implementation_plan`

## Why the plan exists

- Read-only audit found no executable OCC/OpenClaw runtime contamination.
- Protected runtime comment/docstring references were cleaned and reviewed.
- Public-doc tooling references were cleaned and reviewed.
- Internal-context doctrine drift was compressed and reviewed.
- Release-gate policy risk was not urgent, but optional hardening is useful to prevent recurrence.
- Existing exact-file allowance patterns remained narrow.

## Current boundary

- OCC/OpenClaw remains execution tooling only.
- OCC/OpenClaw is not WESLR runtime, deployment, identity, product, or authority.
- Valid workflow provenance must remain provenance, not identity or authority.
- The plan must preserve exact-file allowlists and prevent broad allowlist drift.

## Implementation target

Likely primary file:
- `weslr/tests/release_gate_v1.py`

Possible supporting future test file if needed:
- `weslr/tests/test_release_gate_tooling_context_drift_v1.py`

No runtime files. No public docs. No context files unless a later implementation explicitly needs exact-file fixture changes.

## Staged implementation slices

### Slice 1 — `IMPLEMENT_RELEASE_GATE_BROAD_ALLOWLIST_DETECTOR_V1`
Purpose:
- detect and reject broad wildcard/pattern allowlists such as `docs/*`, `weslr/*`, `tests/*`
- detect broad regex/pattern allowances for tooling references
- preserve exact-file allowances

### Slice 2 — `IMPLEMENT_RELEASE_GATE_PROTECTED_RUNTIME_TOOLING_REFERENCE_SCAN_V1`
Purpose:
- scan protected runtime files:
  - `weslr/chat_responder.py`
  - `weslr/main.py`
  - `dialogue.py`
  - `chat_ui.py`
- reject OCC/OpenClaw/Nova/ChatGPT/.openclaw references unless an exact reviewed exception exists

### Slice 3 — `IMPLEMENT_RELEASE_GATE_PUBLIC_DOC_TOOLING_REFERENCE_GUARD_V1`
Purpose:
- scan public-facing/public-doc-style docs for OCC/OpenClaw/.openclaw references
- allow only exact internal/admin docs with boundary markers

### Slice 4 — `IMPLEMENT_RELEASE_GATE_CONTEXT_DOCTRINE_REPETITION_WARNING_V1`
Purpose:
- scan `AGENTS.md`, `IDENTITY.md`, `MEMORY.md`
- warn or fail if repeated tooling-context blocks exceed threshold
- allow a concise canonical separation statement

### Slice 5 — `IMPLEMENT_RELEASE_GATE_MARKER_AND_PROVENANCE_RULES_V1`
Purpose:
- require boundary markers when tooling references appear in allowed docs
- preserve valid provenance while blocking identity/authority drift

## Safest first slice

Recommended first implementation slice: Slice 1.

Reason:
- it is narrow and release-gate-local
- it protects future changes without scanning content too aggressively
- it blocks the highest-risk future failure mode: broad allowlist drift

## Future release-gate behavior constraints

- This plan does not change release-gate behavior yet.
- Implementation must be staged and reviewed.
- Any future gate edits must remain exact-file scoped unless a separate reviewed design says otherwise.
- The gate must not become a broad allowlist engine.

## Future test plan

- broad `docs/*` allowlist rejected
- broad `weslr/*` allowlist rejected
- broad `tests/*` allowlist rejected
- broad regex/wildcard allowance rejected
- exact-file design doc allowance accepted
- exact-file review doc allowance accepted
- exact-file release-gate file allowance accepted when scoped
- protected runtime `OpenClaw` reference rejected
- protected runtime `.openclaw` path rejected
- public doc OCC/OpenClaw product wording rejected
- internal/admin doc with boundary marker accepted
- internal/admin doc without boundary marker rejected or warned
- canonical separation wording accepted
- OCC/OpenClaw identity/authority wording rejected
- hidden prompt / answer-key / protected-material checks remain unchanged
- current valid repository state still passes

## Per-slice validation

For each slice, run:
- `python3 weslr/tests/release_gate_v1.py`
- targeted pytest for new release-gate tests if created
- `bash scripts/weslr_release_check.sh`
- `git diff --check`
- protected-file diff checks
- confirm no public docs changed
- confirm no runtime files changed

## Failure behavior

- fail closed on broad allowlists
- fail closed on protected runtime tooling references
- warn-or-fail on context-doctrine repetition only if explicitly decided in the slice design
- emit clear error messages naming the offending file and pattern
- do not auto-repair from release gate

## Boundaries

- do not rewrite docs
- do not edit runtime code
- do not edit OCC workspace
- do not call model/provider/search/advisor
- do not read or write `.weslr`
- do not promote behavior packs
- do not make public claims

## Risks / followups

- over-hardening could block valid governance docs
- under-hardening could allow doctrine drift to return
- exact-file allowlists could grow too large without review
- context docs can accumulate repeated provenance again
- public-doc classification may need a registry
- release-gate complexity could obscure intent
- implementation must be staged and reviewed carefully

## Expected final judgment

`release_gate_tooling_context_drift_hardening_implementation_plan_ready_for_review`
