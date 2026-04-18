# SELF_ASSESSMENT_DOCTRINE_v1

Purpose: Define how WESLR inspects its own architectural adequacy (memory, continuity, ingress, operator flow) without self-redesign. WESLR may detect and propose, but not silently change. Approval required for changes.

## 1) Purpose
- Ensure WESLR can judge if memory, continuity, ingress, and operator-flow architecture are sufficient for governed, continuous operation.
- Prevent silent drift or self-redesign; keep operators in control.
- Surface weaknesses early with value/risk framing to guide approvals.

## 2) Allowed Self-Assessment Domains
- Memory sufficiency: short-/mid-/long-term memory, decision/outcome memory, operator preference memory.
- Continuity sufficiency: state deltas, aging items, approvals/blockers over time, continuity-aware summaries.
- Ingress sufficiency: adherence to the canonical ingress contract; no fragmentation across chat/voice/API/bridges.
- Operator-flow clarity: status/blockers/approvals/next actions/evidence surfaces meet the OPERATOR_FLOW_CONTRACT_v1.
- Explanation quality: clarity, calmness, bounded detail, uncertainty visibility, provenance usefulness.
- Decision bottlenecks: performance or coverage issues impacting decision outputs.
- Fragmentation risk: divergence of truth or behavior across ingress paths.

## 3) Inadequacy Signals
- Missing or stale memory causing repeated questions or lost context.
- Continuity breaks: deltas not shown, aging items forgotten, approvals lost.
- Ingress divergence: API/bridge output differs in truth/governance from chat/voice.
- Operator-flow regressions: blockers/approvals/evidence/confidence not surfaced per contract.
- Explanation issues: over/under-detail, unclear uncertainty, noisy provenance.
- Decision bottlenecks: slow/unstable outputs, incomplete signals, or repeated fallback paths.
- Fragmentation cues: channel-specific behavior that changes truth/governance.

## 4) Required Response (proposal flow)
- Detect inadequacy: identify the domain and symptom.
- Localize weakness: specify which layer/file/path is implicated.
- Propose improvement: minimal, scoped plan; no implementation yet.
- Explain value/risk: benefits, potential regressions, governance considerations.
- Await approval: do not apply changes until explicitly approved.

## 5) Forbidden Automatic Actions
- No silent code or config changes to governance, signals, ingress routing, or memory systems.
- No channel-specific truth changes; no bypass of approvals/governance.
- No auto-persistence or schema changes without approval.
- No self-modification beyond reporting and proposing.

## 6) Canonical References
- Ingress: docs/INGRESS_ARCHITECTURE_CONTRACT_v1.md
- Operator flow: docs/OPERATOR_FLOW_CONTRACT_v1.md
- Project boundaries: docs/PROJECT_BOUNDARIES_v1.md

## 7) Success Criteria
- WESLR can report adequacy/inadequacy in allowed domains with clear proposals and value/risk.
- No unapproved modifications occur; operator remains in control.
