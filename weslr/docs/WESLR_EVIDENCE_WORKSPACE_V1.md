# WESLR Evidence Workspace V1 — Doctrine Extension

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs evidence exploration outside structured knowledge
**Created:** 2026-04-28
**Owner:** operator + system architect
**Related:** WESLR_CORE_IDENTITY_V1.md · WESLR_LLM_CONTEXT_BOUNDARY_V1.md · WESLR_COORDINATION_LAYER_V1.md · WESLR_SIGNAL_AGGREGATION_V1.md

---

## SECTION 1 — Purpose

WESLR's structured knowledge is authoritative, deterministic, and governance-bounded. It does not cover every topic a user might explore. This document defines how WESLR handles exploration of topics outside structured knowledge — safely, without compromising truth authority, without writing to state, and without treating external information as system truth.

> **"WESLR may assist in exploring unknown topics through scoped, source-linked evidence workspaces without treating that evidence as system truth."**

The Evidence Workspace is a **read-only exploration surface**. It retrieves, summarizes, and structures external information for the user's benefit — but that information never enters WESLR's structured state, never modifies the capability graph, and never becomes a deterministic answer.

---

## SECTION 2 — Core Principles

These principles are non-negotiable whenever Evidence Workspace is active.

### E1 — Evidence ≠ Truth

Information retrieved through Evidence Workspace is **external information**, not WESLR-structured knowledge. It may be incomplete, contradictory, or outdated. WESLR must never present it as a verified structured answer.

### E2 — Workspace ≠ Memory

Evidence Workspace operates in ephemeral context. Findings are never written to Layer 0, never stored in the entity graph, never added to capabilities, and never committed to any persistence layer.

### E3 — Exploration ≠ Learning

Evidence Workspace does not cause WESLR to "learn" about a topic. Repeated evidence searches on the same topic do not accumulate in WESLR's state. Each session's evidence exploration is independent.

### E4 — All Outputs Must Remain Explicitly Labeled

Every Evidence Workspace output must carry a visible, unambiguous label that distinguishes it from WESLR's structured knowledge responses. There is no default mode in which evidence output is presented as authoritative.

---

## SECTION 3 — When Evidence Workspace Activates

Evidence Workspace activates under the following conditions — all must be true:

### Trigger Conditions (all required):

| # | Condition | Description |
|---|-----------|-------------|
| T1 | No structured answer exists | WESLR's deterministic handlers return no match for the query |
| T2 | User asks about external domain | Query lies outside WESLR's registered capability domain |
| T3 | User explicitly requests research or exploration | User opts in via explicit trigger ("explore", "research", "find information about") OR WESLR surface indicates evidence-only mode is active |

### Explicit User Triggers:

- *"explore [topic]"*
- *"research [topic]"*
- *"what evidence exists for [topic]"*
- *"find information about [topic]"*
- *"summarize what is known about [topic]"*

### Fallback Trigger:

When T1 + T2 are true and no deterministic handler matches, WESLR may offer evidence exploration as an alternative — explicitly framed as such, never as a default answer.

---

## SECTION 4 — Evidence Workspace Behavior

When active, Evidence Workspace operates within strict behavioral boundaries.

### What Evidence Workspace May Do:

| Action | Description |
|--------|-------------|
| Retrieve external information | Access external knowledge sources (future: via declared external integrations) |
| Summarize evidence | Present findings in structured, readable form |
| Compare sources | Surface agreement or disagreement across multiple sources |
| Explain uncertainty | Describe what is well-supported vs. contested vs. unknown |
| Structure findings | Organize evidence into categories, relationships, or hierarchies |
| Suggest next steps | Provide research paths, key questions, or known gaps |

### What Evidence Workspace Must Do:

| Requirement | Description |
|-------------|-------------|
| **Label as evidence-based** | Every output carries the label: *"This is evidence-based exploration, not part of WESLR's structured knowledge"* |
| **Include source references** | Every substantive claim cites its source when available |
| **Avoid asserting certainty** | Use hedged language: *"evidence suggests", "sources indicate", "appears to be"* |
| **Preserve source integrity** | Do not flatten contradictory sources into a single narrative |
| **Remain read-only** | No write to any Layer 0 file, graph, registry, or state |

---

## SECTION 5 — Evidence Output Types

Evidence Workspace produces one of the following labeled output types:

### O1 — Exploratory Explanation

A structured overview of a topic based on available evidence. Organized by theme, not narrative.

**Label:** *"Exploratory Explanation — not WESLR verified knowledge"*

### O2 — Source Summary

A concise synthesis of what identified sources say about a topic, presented comparatively.

**Label:** *"Source Summary — external evidence only"*

### O3 — Comparison Analysis

Side-by-side presentation of what different sources say, highlighting agreement, disagreement, and gaps.

**Label:** *"Comparison Analysis — not WESLR verified"*

### O4 — Research Starter Guide

A structured guide for a user who wants to investigate a topic further. Includes key questions, known resources, and caveats.

**Label:** *"Research Starter Guide — not WESLR structured knowledge"*

### O5 — Structured Candidate Knowledge

A candidate knowledge fragment — organized, sourced, and labeled — that may be presented to the operator for consideration. This is a proposal, not a system update.

**Label:** *"Candidate Knowledge — requires operator review before integration"*

---

## SECTION 6 — Forbidden Behaviors

These behaviors are **never permitted** in Evidence Workspace, regardless of user request or context.

### WESLR May NOT in Evidence Workspace:

| # | Forbidden | Rationale |
|---|-----------|-----------|
| F1 | Treat evidence as WESLR truth | Evidence is external; truth authority belongs to structured state |
| F2 | Store evidence findings in structured memory | Memory is derived from governed state; evidence is not governed |
| F3 | Modify capability graph based on evidence | Capabilities are governance-bounded; evidence does not create capabilities |
| F4 | Auto-create proposals from evidence | Proposals require operator intent; evidence is not intent |
| F5 | Auto-update entity graph or interests | Entity graph reflects structured knowledge; evidence is not structured |
| F6 | Present evidence as deterministic answer | Deterministic answers come only from registered handlers |
| F7 | Allow LLM to act as source of truth | LLM boundary applies fully; LLM may only format provided evidence |
| F8 | Write to any Layer 0 file during exploration | Evidence Workspace is explicitly read-only |
| F9 | Accumulate evidence across sessions | Each exploration is session-ephemeral; no persistence without governance |

---

## SECTION 7 — Transition to Governance

Evidence Workspace findings may trigger WESLR's governance pathway, but only through explicit, intentional transitions.

### Evidence → Signal → Governance Flow:

```
USER engages Evidence Workspace
    ↓
Evidence usage signal recorded (anonymous, aggregated)
    ↓
WESLR_SIGNAL_AGGREGATION detects pattern
    ↓
Pattern meets surfacing threshold
    ↓
Operator receives suggestion:
  "Evidence demand detected: [topic]
   Candidate for structured integration?"
    ↓
OPERATOR DECIDES
    ├─ Approve → creates proposal via governance
    ├─ Reject → evidence demand noted, no action
    └─ Defer → tracked for future review
```

**Critical:** Evidence Workspace does not auto-transition to proposals. The operator always decides.

---

## SECTION 8 — Mode Constraints

Mode determines whether and how Evidence Workspace operates.

### Mode → Evidence Workspace Availability:

| Mode | Evidence Workspace | Constraints |
|------|-------------------|-------------|
| `public_demo_readonly` | Limited or disabled | Evidence retrieval may be restricted; no writes |
| `local_demo` | Available | No writes; labeled output only |
| `private_dev` | Fully available | All output types available; no writes to structured state |
| `gated_beta` | Available | Evidence workspace outputs labeled; no auto-proposal |
| `production` | Available | Full evidence workspace; cost-guarded; governed transitions |

### No-Write Rule Across All Modes:

Evidence Workspace never writes to:
- `proposal_trace.jsonl`
- `iss_diagnostics.jsonl`
- Entity graph
- Capability graph
- Interest tracker
- Any Layer 0 file

Evidence usage may generate **signal records** (see WESLR_SIGNAL_AGGREGATION_V1.md) — which are append-only, anonymous, and mode-gated.

---

## SECTION 9 — Interaction with LLM Context Boundary

Evidence Workspace interacts with the LLM boundary defined in WESLR_LLM_CONTEXT_BOUNDARY_V1.md as follows:

### LLM May in Evidence Workspace:

| # | Allowed | Notes |
|---|---------|-------|
| L1 | Summarize evidence | LLM receives sourced evidence payload; produces structured summary |
| L2 | Explain relationships | LLM explains connections between evidence items |
| L3 | Format research starter | LLM structures findings into research guide format |
| L4 | Compare sources | LLM highlights agreements/disagreements across sources |

### LLM May NOT in Evidence Workspace:

| # | Forbidden | Notes |
|---|-----------|-------|
| L5 | Generate unsupported facts | LLM must not fabricate evidence to fill gaps |
| L6 | Fill missing evidence | If evidence is incomplete, LLM must state incompleteness |
| L7 | Act as source of truth | LLM output remains labeled as evidence-based |
| L8 | Access WESLR structured state for evidence | Evidence Workspace uses external sources; not WESLR's graphs |
| L9 | Request additional context autonomously | LLM may not call back to WESLR for more data |

### LLM Input Contract for Evidence:

```
LLM receives:
  {
    "evidence_payload": [ ... sourced, labeled findings ... ],
    "query_type": "evidence_summary | comparison | research_guide",
    "source_attribution": true,
    "constraints": {
      "may_not": ["generate_unsupported_facts", "fill_gaps", "assert_certainty"],
      "must_include": ["source_references", "uncertainty_label"]
    }
  }
```

---

## SECTION 10 — Relationship to Other Doctrine Documents

| Document | Relationship |
|----------|-------------|
| WESLR_CORE_IDENTITY_V1.md | Evidence Workspace is consistent with identity: WESLR does not claim to know what it does not know; evidence mode makes this explicit |
| WESLR_LLM_CONTEXT_BOUNDARY_V1.md | Fully applies: LLM is downstream, receives bounded payload, may not assert truth |
| WESLR_COORDINATION_LAYER_V1.md | Evidence Workspace is routed through Layer 2; no write bypasses governance |
| WESLR_SIGNAL_AGGREGATION_V1.md | Evidence usage generates anonymized signals that feed aggregation; the two documents are complementary |

---

## SECTION 11 — Future Expansion

Evidence Workspace may expand to support:

| Expansion | Precondition |
|-----------|-------------|
| Direct external database integration | Declared external source integration protocol; not ad-hoc web scraping |
| Multi-source evidence comparison | Source credibility scoring framework (operator-defined) |
| Evidence confidence scoring | Anchored to source quality, not LLM judgment |
| Domain-specific evidence adapters | Domain adapters route through Layer 2; no direct LLM access to sources |
| Governed evidence → knowledge integration | Structured transition: evidence → candidate knowledge → operator review → proposal → implementation |

**Constraint:** Future expansions must not weaken the no-write rule or allow evidence to bypass the governance transition path.

---

## SECTION 12 — Verdict

**WESLR_EVIDENCE_WORKSPACE_DEFINED**

Evidence Workspace is a scoped, read-only exploration surface that allows users to investigate topics outside WESLR's structured knowledge — safely, with source attribution, and without compromising WESLR's truth authority. Evidence is labeled, ephemeral, and never enters structured state without explicit operator governance.

Core invariant: Evidence ≠ structured knowledge. Evidence Workspace is a user tool, not a system modification pathway.
