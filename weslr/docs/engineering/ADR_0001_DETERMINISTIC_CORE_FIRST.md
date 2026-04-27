# ADR-0001: Deterministic Core First

**Status:** Accepted
**Date:** 2026-04-27
**Deciders:** pr0dus (operator)

---

## Context

WESLR is a governed entity intelligence system built on OpenClaw. It has a natural tendency to grow execution capabilities — probes that check files, plans that propose actions, learning layers that modify behavior. There is pressure from the system itself to add more capable, more autonomous behaviors.

The question is: what should the foundation look like before any autonomous execution paths are added?

---

## Decision

**Build WESLR as a deterministic query system first.** All operator-facing functionality operates in read-only mode or confirmation-gated write mode. Before any execution capability is added, the system must have:

1. A complete entity graph with provenance-tracked relationships
2. An ISS diagnostic subsystem that observes but never executes
3. A proposal traceability log with an append-only audit trail
4. A handler registry with explicit priority ordering
5. A response formatter that ensures field consistency

**Probe execution** is simulated-only. The probe subsystem describes what checking a target would look like but never actually performs system I/O, subprocess calls, or network access.

**Implementation plans** are declarative. The system can describe what a plan would do but never executes plan steps.

**Proposal decisions** require explicit operator approval. No proposal is acted upon without an explicit accepted/rejected/deferred decision from the operator.

---

## Consequences

**Positive:**
- Operator trust is established because nothing happens without approval
- The audit trail is clean because all state changes are explicit and recorded
- Regression testing is simpler because execution paths are isolated
- The system is easier to reason about because "non-executing" is the default
- Handler dispatch is explicit and auditable

**Negative:**
- Some operations that could be automated require more operator effort
- Confirmation-gated paths can feel slower than direct execution
- The system cannot self-correct without operator involvement

**Neutral:**
- Probe stubs exist but probe execution is simulated; this is the correct initial state
- Plans are created but not executed; this is the correct initial state
- Proposals are tracked but not auto-actioned; this is the correct initial state

---

## Alternatives Considered

**Alternative 1: Execution-capable from day one**
Build the system with full execution capabilities and use operator governance to restrict usage. Risk: once execution exists, governance must be perfect to prevent misuse. Governance failures are harder to detect because execution "works" and failures are subtle.

**Alternative 2: Fully autonomous with human review**
Build the system to act autonomously and review outputs after execution. Risk: autonomous actions can be irreversible before review occurs. In a JSONL append-only system this is mitigated but execution traces can still have real-world effects.

**Alternative 3: Query-only forever**
Build WESLR purely as a query system and never add execution. Risk: underestimates operator intent. The governance model explicitly supports operator-controlled execution paths in later phases.

---

## Reversal Conditions

This ADR may be reconsidered when:
- A formal operator approval workflow exists that can gate real execution
- The probe stub registry has complete coverage of all WESLR subsystems
- The proposal traceability system has demonstrated stability over 30+ days of operation
- The handler registry has been validated for all deterministic query paths
- The response formatter has been adopted by all handler paths

When this ADR is reversed, ADR-0002 (Operator-Governed Evolution) remains in effect — operator governance is not bypassed.

---

*ADR-0001 — Deterministic Core First — Accepted 2026-04-27*
