# WESLR Multi-Graph Memory V1 — Doctrine

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs WESLR graph and memory design
**Created:** 2026-04-28
**Owner:** operator + system architect

---

## SECTION 1 — Purpose

WESLR tracks intelligence as **structured graphs** — not raw text, not embeddings, not weights. Graphs represent relationships between entities, capabilities, gaps, proposals, and plans. They are derived views of tracked state, not the state itself.

This document defines how WESLR's multi-graph memory system is structured, what it tracks, what it may never do, and the rules that govern it.

---

## SECTION 2 — Graph Types

WESLR maintains multiple specialized graphs:

### Entity Graph
**Purpose:** Tracks real-world entities referenced in WESLR's operation.

**Nodes:** People, projects, tools, concepts, organizations.
**Edges:** Relationships: `created_by`, `solves`, `depends_on`, `tracks`, `relates_to`.
**Source:** Extracted from trace events, proposals, plans.
**Truth source:** `proposal_trace.jsonl` — entity provenance traceable to source event.

### Capability Graph
**Purpose:** Tracks what WESLR can do, what it has done, and what it cannot yet do.

**Nodes:** Capabilities (handlers, probes, interfaces).
**Edges:** `enables`, `depends_on`, `realizes`, `supersedes`.
**Source:** Handler registry + ISS probe results + implementation plans.
**Truth source:** `handler_registry` + `iss_diagnostics.jsonl`.

### Gap Graph
**Purpose:** Tracks known deficiencies, missing capabilities, and unintegrated proposals.

**Nodes:** Gaps (capability gaps, integration gaps, knowledge gaps).
**Edges:** `blocks`, `related_to`, `superseded_by`.
**Source:** ISS gap signals, failed route counts, operator-reported gaps.
**Truth source:** `iss_diagnostics.jsonl` — gap records.

### Proposal Graph
**Purpose:** Tracks the evolution of ideas through governance.

**Nodes:** Proposals.
**Edges:** `addresses`, `depends_on`, `precedes`, `approves`.
**Source:** `proposal_trace.jsonl`.
**Truth source:** `proposal_trace.jsonl` — immutable audit trail.

### Memory Graph (Operator Only)
**Purpose:** Long-term operator-accessible memory from curated sources.

**Nodes:** Curated facts, decisions, context.
**Edges:** `context_for`, `supports`, `contradicts`.
**Source:** Operator-written entries + approved proposal summaries.
**Truth source:** Operator curation + governance.

**Forbidden graph type:** ❌ User-learned memory graphs — WESLR does not build user profiles or learn from public interactions.

---

## SECTION 3 — Graph Rules

**All graphs must follow:**

| Rule | Rationale |
|------|-----------|
| All graph nodes traceable to source event | No floating facts without provenance |
| All edge additions traceable to proposal trace | Every relationship change is governed |
| Graphs are derived views, not truth sources | Layer 0 (JSONL files) remains source of truth |
| No graph may be mutated by LLM directly | LLM is downstream; graphs are structured state |
| No user input stored in graphs without governance | User input is signal, not memory |
| Operator-only graphs inaccessible in public mode | Security boundary |

---

## SECTION 4 — Multi-Graph Constraints

| Constraint | Rationale |
|------------|-----------|
| No graph merges without operator review | Merging graphs risks losing provenance |
| No cross-graph inference without explicit handler | Cross-graph reasoning requires registered logic |
| No graph updates without trace entry | Audit trail must reflect every change |
| No graph stored as primary truth | JSONL files are ground truth; graphs are views |
| No graph structure changes without governance proposal | Schema evolution governed same as features |

---

## SECTION 5 — Graph Derivation Rules

Graphs are **derived** from Layer 0 (JSONL files) through deterministic computation:

```
proposal_trace.jsonl  →  Entity Graph (extraction + linking)
                       →  Proposal Graph (node/edge extraction)
iss_diagnostics.jsonl →  Gap Graph (gap signals + probes)
                       →  Capability Graph (probe results + handler registry)
```

**Rules:**
- Derivation is deterministic: same source file → same graph (reproducible)
- Derivation is registered: only registered handlers can derive graphs
- Derivation is traceable: each derivation run is logged
- No derivation from user input: user content is not a graph source

---

## SECTION 6 — Forbidden Memory Behaviors

These are architecturally forbidden — no implementation, no exceptions:

| Forbidden | Reason |
|-----------|--------|
| User input stored in any graph | Violates learning boundary; poisoning risk |
| Raw prompts written to graph nodes | Privacy + safety violation |
| LLM generating graph structure | Graphs must be derived from governed state |
| Autonomous graph mutation | All mutations go through proposal trace |
| Hidden learning from user sessions | User sessions produce signals only |
| Cross-session memory without operator review | Continuity is governed, not automatic |
| User preference profiles built from interaction history | Violates public learning boundary |

---

## SECTION 7 — Future-Proof Constraints

| Constraint | Rationale |
|------------|-----------|
| Any new graph type requires a governance proposal | New graph types affect reasoning; must be reviewed |
| Graph schema changes go through same proposal flow as features | Schema is state; changes require traceability |
| Graphs may not be the primary write target | Writes always go to Layer 0; graphs are derived |
| External data entering graphs must route through ISS intake | External data is treated like any other new information |

---

## SECTION 8 — Verdict

**WESLR_MULTI_GRAPH_MEMORY_V1_DEFINED**

WESLR maintains five specialized graphs (Entity, Capability, Gap, Proposal, Memory). All are derived from Layer 0 JSONL files. Graphs are views, not truth. No graph may be mutated by LLM or user input. All graph changes trace to proposal records.
