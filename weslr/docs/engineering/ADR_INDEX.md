# WESLR Architecture Decision Records — Index

**Status:** active
**Version:** 1.0

---

## ADR Registry

| ADR | Title | Status | Date |
|---|---|---|---|
| ADR-0001 | Deterministic Core First | Accepted | 2026-04-27 |
| ADR-0002 | Operator-Governed Evolution | Accepted | 2026-04-27 |
| ADR-0003 | Append-Only State Logs | Accepted | 2026-04-27 |
| ADR-0004 | Handler Registry and Response Formatter | Accepted | 2026-04-27 |

---

## Summary

**ADR-0001 — Deterministic Core First**
Build WESLR as a deterministic query system before adding any autonomous execution paths. All operator-facing functionality operates in read-only or confirmation-gated mode. This establishes trust and provides a stable foundation.

**ADR-0002 — Operator-Governed Evolution**
All system changes require explicit operator approval. No autonomous state changes, no learned behaviors that aren't explicitly declared, no hidden learning fields in responses. The operator is the authority.

**ADR-0003 — Append-Only State Logs**
All state-changing events are written to append-only JSONL logs. Records are never modified or deleted. This provides a complete audit trail and enables reconstruction of system state at any point in time.

**ADR-0004 — Handler Registry and Response Formatter**
Extract deterministic query handlers into a registry with explicit priority ordering and standardize all handler responses through a single formatter function. This eliminates implicit dispatch ordering and ensures field consistency.

---

## Adding New ADRs

When a new architectural decision is made:
1. Create `ADR_NNNN_title.md` in this directory
2. Fill in all ADR sections (Status, Context, Decision, Consequences, Alternatives, Reversal)
3. Add entry to this index
4. Commit with message: `docs: add ADR-NNNN title`

## Non-Goals

These ADRs do not cover:
- Specific feature specifications (use project specs for that)
- Team structure or process (use separate documents)
- Performance targets (tracked separately)
- Security hardening (separate hardening guide planned)

---

*Version: 1.0 — all 4 foundational ADRs accepted*
