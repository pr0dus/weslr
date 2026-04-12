# COGNITIVE_DIALOGUE_INTERFACE_v1

**Scope:** Contract-first definition for the Cognitive Dialogue Interface (CDI). No runtime changes yet. Wave 3 item 1. Keeps governance and approval gating intact; no autonomous self-change.

## SECTION 1 — PURPOSE
- Enable operators to discuss reasoning quality with WESLR.
- Surface inadequacy findings (from adequacy/lineage/reflection).
- Explain why an answer/proposal was weak, with evidence references.
- Present bounded self-improvement proposals (proposal-only) with lineage.
- Allow operator approve/deny/refine in dialogue.
- Preserve lineage and evidence references throughout.

## SECTION 2 — DIALOGUE FLOW (CANONICAL)
weak output detected → adequacy finding → dialogue explanation → bounded improvement proposal → operator response (approve/deny/refine) → approval gate → (if approved) self-change proposal only (no auto-activation) → record lineage/rollback.

## SECTION 3 — SAFETY BOUNDARIES
- No autonomous self-change or cognition rewrite.
- No routing mutation; no automatic activation.
- No silent changes; approval-gated only.
- No governance/rollback bypass; lineage recorded for proposals.

## SECTION 4 — IMPLEMENTATION NOTES (FUTURE)
- Runtime helper will be added in a later step; not in this contract.
- Dialogue should consume adequacy findings and lineage refs; render operator-visible context.
- Approval hooks must route through existing governed self-improvement flow.

## SECTION 5 — NEXT STEP
- Implement CDI runtime helper + tests under this contract (no routing/UI yet), keeping Wave 1/2 frozen and transcript validation parked.
