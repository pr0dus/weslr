# WESLR OCC/WESLR Separation and Contamination Hardening V1

## Purpose

This document defines a separation policy between WESLR and OCC/OpenClaw and records a future hardening plan for workflow-reference contamination discovered in read-only audit.

It is design-only. It does not change runtime behavior, public docs, or existing governance context.

## Separation policy

- OCC/OpenClaw is execution tooling only.
- OCC/OpenClaw is not WESLR deployment.
- OCC/OpenClaw is not part of WESLR runtime.
- OCC/OpenClaw is not part of WESLR identity.
- OCC/OpenClaw has no authority inside WESLR.
- ChatGPT/Nova/OCC workflow references are provenance only unless explicitly approved otherwise.
- WESLR must remain understandable and operable without assuming OCC/OpenClaw exists.

## Contamination classes

### 1. `safe_workflow_provenance`
- Internal review/history notes.
- No runtime implication.
- No public/product claim.
- Explicitly says OCC is tooling only.

### 2. `acceptable_internal_governance_note`
- Internal governance reference.
- Explicitly separates WESLR from OCC.
- Not imported by runtime.
- Not used as behavior doctrine.

### 3. `risky_doctrine_drift`
- Repeated context blocks that may become doctrine.
- Identity/governance docs that blur tooling with system identity.
- Wording that future agents could treat as authority.

### 4. `unsafe_runtime_contamination`
- Runtime/source dependency.
- Imports or config requiring OCC/OpenClaw.
- Chat/routing/UI/memory behavior depending on OCC.
- Prompt/identity logic granting OCC authority.

### 5. `public_claim_risk`
- Public-facing docs or website docs implying OCC is part of WESLR product/deployment.
- Customer/tester confusion risk.

### 6. `release_gate_policy_risk`
- Broad allowlists because of workflow docs.
- Broad docs/source/test pattern allowances.
- Weakening protected-file checks.
- Weakening safety checks.

## Target end state

- Runtime source contains no OCC/OpenClaw/Nova/ChatGPT workflow references unless narrowly justified and non-executable.
- Protected files should not contain tooling-provenance comments unless explicitly approved.
- Public-facing docs should not mention OCC/OpenClaw unless the document is clearly internal/admin-only.
- Internal docs may mention OCC/OpenClaw only as workflow provenance with clear separation language.
- Release gate should continue exact-file allowlists only.
- Future agents must not infer OCC is part of WESLR.

## Future cleanup lanes

### Lane A — `REPAIR_WESLR_PROTECTED_RUNTIME_TOOLING_REFERENCE_CLEANUP_V1`
Purpose: remove or quarantine non-executable OCC/OpenClaw/Claude/ChatGPT workflow comments from protected runtime source, especially:
- `weslr/chat_responder.py:6-7`
- `weslr/chat_responder.py:1920-1921`

Rules:
- exact-line/comment/docstring cleanup only
- no behavior change
- no runtime logic change
- protected-file edit allowed only for this narrow cleanup lane
- validate with tests and protected diff review

### Lane B — `REPAIR_WESLR_PUBLIC_DOC_TOOLING_REFERENCE_CLEANUP_V1`
Purpose: classify and clean public-facing docs that mention OpenClaw/OCC paths or workflow artifacts.

Candidate docs:
- `docs/WESLR-HEALTH.md`
- `docs/UPLOAD-INSTRUCTIONS.md`
- `docs/QUICK-UPLOAD-GUIDE.md`
- `docs/HEADLESS_DEPLOYMENT_BOOTSTRAP_GUIDE_v1.md`
- `docs/PHASE-1-CHAT-CONTROL-IMPLEMENTATION.md`
- `docs/FRONT_DOOR_BRIDGE_CONTRACT_v1.md`
- `docs/CURRENT_RUNTIME_STATE_SNAPSHOT_v1.md`

Rules:
- no public claim drift
- separate internal admin docs from public docs
- do not delete history blindly
- preserve operational facts in internal-only form if needed

### Lane C — `REPAIR_WESLR_INTERNAL_CONTEXT_TOOLING_DOCTRINE_DRIFT_V1`
Purpose: reduce repeated OCC/OpenClaw context blocks in:
- `AGENTS.md`
- `IDENTITY.md`
- `MEMORY.md`

Rules:
- preserve clear OCC/WESLR separation
- reduce doctrine-like repetition
- do not erase valid provenance
- do not turn OCC into WESLR identity
- no runtime behavior edits

### Lane D — `DESIGN_WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_V1`
Purpose: design optional release-gate hardening against broad tooling-context drift.

Rules:
- exact-file allowlists remain allowed
- broad pattern allowlists remain disallowed
- protected-file safety checks remain strict
- no urgent issue found, so design-only unless later approved

## Priority order

1. Protected runtime-source comment/docstring cleanup design/repair first.
2. Public-doc classification/cleanup second.
3. Internal context doctrine-drift compression third.
4. Optional release-gate hardening fourth.

## Validation requirements for future cleanup

- `git diff --check`
- protected-file focused diff review
- no runtime logic changes
- no imports/dependencies added
- no tests weakened
- release gate
- release check
- targeted tests if runtime-protected file comments are touched
- grep scan after cleanup for OCC/OpenClaw/Nova/ChatGPT references
- classification table before and after cleanup

## Strict non-goals

- do not erase all provenance
- do not deny that OCC was used as build tool
- do not rewrite history deceptively
- do not make WESLR depend on OCC
- do not remove safety context that prevents OCC/WESLR confusion
- do not edit runtime behavior
- do not edit public website behavior
- do not promote behavior packs
- do not change deployment

## Expected final judgment

`occ_weslr_separation_contamination_hardening_design_ready_for_review`
