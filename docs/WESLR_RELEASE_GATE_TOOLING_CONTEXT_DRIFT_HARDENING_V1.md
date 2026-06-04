# WESLR Release Gate Tooling Context Drift Hardening V1

## Purpose

Design a future release-gate hardening layer that prevents tooling-context drift from becoming WESLR runtime, public-product, identity, authority, or broad-allowlist doctrine.

This lane is design-only. It does not change release-gate behavior, runtime behavior, public docs, or deployment.

## Why this lane exists

- Read-only audit found no executable OCC/OpenClaw runtime contamination.
- Protected runtime comment/docstring references were cleaned and reviewed.
- Public-doc tooling references were cleaned and reviewed.
- Internal-context doctrine drift was compressed and reviewed.
- Release-gate policy risk was not urgent, but optional hardening is useful to prevent recurrence.
- Existing exact-file allowance patterns remained narrow; this design preserves that.

## Current boundary

- OCC/OpenClaw is execution tooling only.
- OCC/OpenClaw is not WESLR runtime, deployment, identity, product, or authority.
- ChatGPT/Nova/OCC workflow references are provenance only unless explicitly approved otherwise.
- Valid workflow provenance must not become WESLR identity or authority.

## Future hardening goals

1. Prevent broad `docs/*`, `weslr/*`, or `tests/*` allowlists for tooling-context references.
2. Preserve exact-file allowlists for reviewed governance/design/review/result docs.
3. Detect OCC/OpenClaw/Nova/ChatGPT references in protected runtime files.
4. Detect OCC/OpenClaw/.openclaw references in public-facing docs unless explicitly internal/admin-only.
5. Detect repeated tooling-context blocks that could become doctrine drift.
6. Keep release-gate exceptions narrow, explicit, and reviewable.
7. Prevent weakening hidden prompt, answer-key, protected-material, runtime, and safety checks.
8. Preserve valid workflow provenance without turning it into WESLR identity.

## Future forbidden release-gate patterns

- broad `docs/*` allowlist for tooling references
- broad `weslr/*` source allowlist for tooling references
- broad `tests/*` allowlist for tooling references
- wildcard allowances for OCC/OpenClaw/Nova/ChatGPT references
- weakening protected-file checks
- weakening runtime source checks
- weakening public-doc/product-claim checks
- weakening hidden prompt / answer-key / protected-material checks
- allowing `.openclaw` paths in runtime source
- allowing OCC/OpenClaw as runtime/deployment/identity/product/authority language

## Future allowed release-gate patterns

- exact-file allowlists for reviewed design/review/result docs
- exact-file allowlists for known internal admin docs with boundary language
- exact-file allowlists for cleanup review docs
- exact-file allowlists for release-gate test files when scoped and reviewed
- exact-match marker requirements in allowed docs
- line-count or occurrence-count checks where feasible
- classification tags for allowed references:
  - `safe_workflow_provenance`
  - `acceptable_internal_governance_note`

## Candidate future checks

### 1. Protected runtime scan
Block OCC/OpenClaw/Nova/ChatGPT/.openclaw references in:
- `weslr/chat_responder.py`
- `weslr/main.py`
- `dialogue.py`
- `chat_ui.py`

unless an exact, reviewed exception exists.

### 2. Public-doc scan
Block OCC/OpenClaw/.openclaw references in public-facing docs unless the doc is explicitly internal/admin-only.

### 3. Context-doctrine scan
Flag repeated OCC/OpenClaw blocks in:
- `AGENTS.md`
- `IDENTITY.md`
- `MEMORY.md`

Allow a concise canonical separation statement.

### 4. Release-gate allowance scan
- Detect broad wildcard/pattern allowances.
- Require exact-file entries.

### 5. Marker scan
If a doc mentions OCC/OpenClaw, require boundary language such as:
- `execution tooling only`
- `not WESLR runtime`
- `not WESLR deployment`
- `not WESLR identity`
- `not WESLR authority`

### 6. Public claim scan
Block wording that implies OCC/OpenClaw is WESLR product or deployment.

### 7. Provenance preservation scan
Allow historical/provenance docs only with boundary language.

## Implementation phases

1. Design and review only.
2. Map existing release-gate structure.
3. Implement protected runtime tooling-reference check.
4. Implement broad-allowlist detector.
5. Implement public-doc tooling-reference guard.
6. Implement context-doctrine repetition warning.
7. Review.
8. Context alignment if implementation is accepted.

## Future tests

- broad docs allowlist rejected
- broad source allowlist rejected
- broad tests allowlist rejected
- exact-file doc allowlist accepted
- protected runtime OCC/OpenClaw reference rejected
- public doc OCC/OpenClaw product wording rejected
- internal doc with boundary marker accepted
- internal doc without boundary marker rejected or warned
- `.openclaw` path in runtime source rejected
- OCC/OpenClaw identity/authority wording rejected
- canonical separation wording accepted
- no weakening of hidden prompt / answer-key / protected-material checks
- release gate still passes current valid repository state

## Non-goals

- do not erase all provenance
- do not ban reviewed internal governance docs
- do not ban exact-file allowances
- do not rewrite history
- do not make release gate impossible to update
- do not add runtime behavior
- do not edit public docs in this lane
- do not edit protected source in this lane
- do not alter deployment

## Risks / followups

- over-hardening could block valid governance docs
- under-hardening could allow doctrine drift to return
- exact-file allowlists could grow too large without review
- context docs can accumulate repeated provenance again
- public-doc classification may need a registry
- release-gate complexity could obscure intent
- implementation must be staged and reviewed carefully

## Expected final judgment

`release_gate_tooling_context_drift_hardening_design_ready_for_review`
