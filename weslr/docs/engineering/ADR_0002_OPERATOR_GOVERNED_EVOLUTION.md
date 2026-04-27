# ADR-0002: Operator-Governed Evolution

**Status:** Accepted
**Date:** 2026-04-27
**Deciders:** pr0dus (operator)

---

## Context

WESLR makes decisions about what to propose, what plans to create, what diagnostics to run. These decisions have real consequences for the operator's entity intelligence system. There must be a clear authority boundary: the system recommends, the operator decides.

The system has a natural tendency to propose more, suggest more, "learn" from feedback. Without an explicit governance boundary, these tendencies can result in:
- Proposals created without operator intent
- Plans modified or deleted without operator awareness
- Learning fields appearing in responses without disclosure
- State checkpoint modified silently

---

## Decision

**All system changes require explicit operator approval. The operator is the authority.**

Specific rules:

1. **No autonomous proposal creation** — proposals are created only when the operator explicitly requests it (via `accept gap`, `create proposal from gap`) or when the operator directly commands a proposal ("make proposal..."). The system may not create proposals unprompted.

2. **No autonomous plan modification** — implementation plans are created, accepted, rejected, or deferred only via explicit operator commands. The system tracks state but does not change plan status autonomously.

3. **No silent mutation of `_CAPABILITIES`** — the capabilities map is a static reference document. It is read-only at runtime. Any code that attempts to mutate it must raise an error.

4. **No hidden learning fields** — fields that represent learned or inferred state must not appear in response payloads without being labeled as such. The operator must always know what is static vs. inferred.

5. **No execution without confirmation** — any write operation to a JSONL file must be confirmation-gated or explicitly operator-authorized. No silent appends.

6. **Response text does not imply autonomy** — responses must not use "I decided", "I chose", "I think", "I feel", or any language that implies the system has judgment independent of operator input.

---

## Consequences

**Positive:**
- The operator retains full authority over the system
- Audit trail is complete because all changes are operator-authorized
- Trust is maintained because nothing happens that the operator didn't approve
- System state is always traceable to an operator decision

**Negative:**
- Requires operator engagement for every system change
- Some automation potential is left on the table until governance is formalized
- Confirmation fatigue could set in if every small action requires approval

**Neutral:**
- Proposals, plans, and diagnostics still run through the system
- The system still observes, probes, and reports
- Only the authority boundary is different

---

## Alternatives Considered

**Alternative 1: Opt-in autonomous with global kill switch**
Build execution capabilities and provide a global kill switch the operator can flip. Risk: the kill switch may not stop all execution paths in time. Also, a kill switch assumes the operator knows when to use it, which requires understanding the system's execution surface.

**Alternative 2: Confidence-threshold autonomy**
Allow the system to act autonomously when its confidence is high enough. Risk: confidence is currently undifferentiated (all deterministic handlers return `confidence: high`). Before this can work, the confidence semantics must be formalized across at least three types: handler-match confidence, factual-read confidence, and recommendation confidence. This is a future phase item, not a day-one decision.

**Alternative 3: Learn-from-feedback without disclosure**
Enable the system to silently update internal state based on feedback. Risk: the operator loses visibility into what the system has "learned" and how it has changed. This violates the institutional continuity requirement that system state is always traceable to an explicit source.

---

## Reversal Conditions

This ADR should not be reversed. Operator authority is a foundational governance constraint that applies across all WESLR operational phases.

If the operator explicitly decides to enable autonomous execution in a specific subsystem, that subsystem's write operations must still go through:
1. Explicit operator opt-in per subsystem
2. A formal approval workflow (not just a confirmation prompt)
3. A schema-enforced write declaration in the handler registry

Even if execution is enabled, all responses must still avoid implying autonomous judgment.

---

*ADR-0002 — Operator-Governed Evolution — Accepted 2026-04-27*
