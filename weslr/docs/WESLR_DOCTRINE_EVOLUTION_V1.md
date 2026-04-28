# WESLR Doctrine Evolution V1 — System

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs how WESLR's own doctrine evolves
**Created:** 2026-04-28
**Owner:** operator + system architect

---

## SECTION 1 — Purpose

WESLR evolves not only code, but **doctrine**.

Bugs and inconsistencies are treated as signals of missing or incomplete doctrine — not as local mistakes to be patched in isolation. When a problem appears, the first question is never "how do we fix this?" It is "what doctrine gap allowed this, and what should the doctrine say?"

This document defines the system by which WESLR's own architectural doctrine changes. It is a meta-doctrine: the rules for changing the rules.

---

## SECTION 2 — Core Principle

> **"If a problem appears in one place, it is a doctrine gap, not a local bug."**

A localized bug is an implementation error in code that conforms to doctrine. A systemic issue is a doctrine error — a gap, ambiguity, or missing constraint in the documented architecture that allowed the bug to exist without detection.

The principle:
- Bugs are found in code.
- Gaps are found in doctrine.
- Fixing a bug without closing the gap means the next similar bug will go undetected.

---

## SECTION 3 — Evolution Flow

When any issue is observed — during testing, auditing, or runtime — the following flow applies:

```
OBSERVE ISSUE
    ↓
CLASSIFY (bug vs systemic)
    ├─ Bug: local implementation error
    │       → fix implementation, done
    │
    └─ Systemic: doctrine gap, ambiguity, or missing constraint
            → draft doctrine update
            → operator review + approval
            → version doctrine document
            → enforce doctrine globally
            → align all affected implementations
            → validate
```

**Rule:** Systemic issues always produce a doctrine update. The fix is not complete until the doctrine is updated.

---

## SECTION 4 — Doctrine vs Implementation

| # | Doctrine | Implementation |
|---|----------|----------------|
| 1 | Defines truth | Must conform to doctrine |
| 2 | Is versioned and audited | Is tested against doctrine |
| 3 | Changes only through governance | Never defines doctrine |
| 4 | Operator-owned | OCC enforces |
| 5 | Immutable until formally updated | Must not contradict doctrine |

**Hard rule:** Implementation may never define doctrine. If implementation and doctrine disagree, the implementation is wrong — until the doctrine is formally updated through governance.

---

## SECTION 5 — Enforcement Rules

These rules apply to every systemic fix:

| # | Rule | Rationale |
|---|------|-----------|
| E1 | **No patching without doctrine alignment** | A patch that is not grounded in doctrine is a local fix with unknown systemic effects |
| E2 | **No silent behavior changes** | Any behavior change must be declared, documented, and traced |
| E3 | **No partial fixes that contradict doctrine** | A fix that resolves one instance but creates a new doctrine violation is worse than no fix |
| E4 | **All systemic issues require doctrine update** | The gap must be closed at the source, not just the symptom |
| E5 | **Doctrine must precede enforcement** | The rule must exist in doctrine before code is required to enforce it |
| E6 | **Affected implementations must all be aligned** | Doctrine update propagates to all affected code, not just the most visible instance |

---

## SECTION 6 — Examples

### Example 1: Read Path Purity (Hidden Writes)

**Issue:** `record_interest_signal()` wrote to `interest_tracker.json` even in `public_demo_readonly` mode — the declared "read-only" mode had a hidden write path.

**Classification:** Systemic — the issue existed because doctrine had no explicit rule stating that read-only modes must have zero write side effects.

**Doctrine update:** `WESLR_LAYERED_ARCHITECTURE_V1.md` — Layer 2 (Coordination) must enforce zero writes in declared read-only modes. Any write path that fires during a read-only mode is a doctrine violation, not just a bug.

**Enforcement:** All mode-gated functions must check mode before performing any write operation. The mode check is a doctrine enforcement point, not a feature.

**Aligned code:** `interpret_human_turn()` now has an early-return guard in `record_interest_signal()` when mode is `public_demo_readonly`.

---

### Example 2: Proposal Trace Pollution

**Issue:** `rank_capability_proposals()` called `record_proposal()` on every candidate proposal, polluting `proposal_trace.jsonl` with unvetted entries.

**Classification:** Systemic — the issue existed because no doctrine rule distinguished between governance-bound proposal creation (ISS intake, operator action) and ad-hoc proposal recording.

**Doctrine update:** `WESLR_COORDINATION_LAYER_V1.md` — Only operator-triggered or ISS-intake-triggered operations may write to `proposal_trace.jsonl`. Ranking, analysis, and interest tracking are explicitly read-only operations.

**Enforcement:** Proposal records may only be created through declared write handlers with a `write_guard`. Functions that return proposals as response payloads must not independently write them to the trace.

**Aligned code:** `rank_capability_proposals()` loop removed; proposals returned as response payload only.

---

### Example 3: Interest Tracking Violation

**Issue:** Interest signals were written silently on every turn, including in `public_demo_readonly`, without mode check, without registry entry, and without governance.

**Classification:** Systemic — interest tracking was implemented as a side-effect without a doctrine-defined write path, violating the principle that all writes must be declared, traceable, and mode-aware.

**Doctrine update:** `WESLR_MULTI_GRAPH_MEMORY_V1.md` — Any operational signal that persists across sessions is a write operation and must be treated as such. Interest signals are observable aggregates; they are not permitted to write to disk in read-only modes.

**Enforcement:** Write-gated functions must check mode before persisting any state. Undeclared write targets are forbidden.

**Aligned code:** `record_interest_signal()` returns early in `public_demo_readonly`; no writes occur.

---

## SECTION 7 — Interaction with Governance

Doctrine updates are subject to the same governance as all WESLR changes:

| Property | Requirement |
|----------|-------------|
| **Operator approval** | All doctrine updates require explicit operator review |
| **Versioning** | Each doctrine doc has a version number; updates increment the version |
| **Reversibility** | If a doctrine update causes unintended effects, it can be reverted via GitHub history |
| **Audit trail** | Every doctrine change is a committed document with a git hash |
| **Propagation** | Doctrine change triggers an implementation alignment pass |

**Doctrine update process:**
1. Draft new doctrine text (OCC or operator)
2. Operator reviews and approves
3. OCC commits updated doctrine document
4. OCC performs implementation alignment pass (fix code to match new doctrine)
5. OCC runs validation (release gate + public readiness)
6. OCC pushes with commit referencing the doctrine change

---

## SECTION 8 — Future Use

A mature doctrine evolution system enables:

| Capability | How |
|------------|-----|
| **Safe self-analysis** | OCC can audit its own code against doctrine without operator intervention |
| **Structured improvement** | Every improvement proposal routes through doctrine first, implementation second |
| **Controlled evolution without chaos** | Changes are anchored in documented principles, not impulse |
| **Traceable drift detection** | When code diverges from doctrine, the gap is visible and addressable |
| **Self-referential governance** | OCC can surface its own doctrine gaps as proposals for operator review |

The goal is not to prevent change — it is to ensure that change is always traceable to a documented principle, reviewed by the operator, and enforceable in code.

---

## SECTION 9 — Verdict

**WESLR_DOCTRINE_EVOLUTION_DEFINED**

This document establishes the meta-system for how WESLR's own architectural doctrine evolves. Key principle: systemic issues are doctrine gaps, not local bugs. Fixing the doctrine precedes fixing the code.

Doctrina est veritas; implementatio sequitur.
