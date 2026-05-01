# WESLR Artificial Analysis Index Canon V1

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — inspection only, no implementation
**Date:** 2026-05-01
**Owner:** operator + system architect

---

## SECTION 1 — Purpose

The Artificial Analysis Index (AAI) is a global operator-attention filter that ranks, sorts, deduplicates, suppresses, and summarizes signals from across the WESLR system.

**Core statement:**

> *"AAI ranks attention. It does not decide truth."*

AAI exists to reduce operator burden — not to exercise authority. It is a sorting and surfacing layer, not a decision layer. Every AAI classification is a recommendation about where operator attention should go; none of them is an authorization to act.

Operator approval remains required for all high-impact transitions. AAI does not replace governance. It filters the volume.

---

## SECTION 2 — Scope

AAI applies **globally** across WESLR, not only to contract observation. As additional inspection layers are added (ISS diagnostics, write handlers, evidence workspace, signal aggregation, deployment handoffs, operator consistency), AAI provides a unified attention-routing framework for all of them.

**Initial scope (Pass 1):**
- `/chat` response path
- Public signal capture
- Contract observation layer
- Contract insufficiency detector
- Contract proposal review bridge
- Read-only review interface

**Future scope (Pass N):**
- ISS diagnostics
- Proposal traceability (`proposal_trace.jsonl`)
- Implementation plans
- Write handlers
- Public readiness gates
- Controlled exposure observation window
- Deployment / OCW handoff
- Frontend / UI internal flags
- OmniChat response surface
- Evidence workspace
- Signal aggregation (S1–S6 surfacing thresholds)
- Operator consistency diagnostics

---

## SECTION 3 — Attention Levels

AAI classifies every signal into one of five attention levels:

| Level | Name | Meaning |
|-------|------|---------|
| **0** | `suppress` | Noise — no operator awareness required, no tracking needed |
| **1** | `track` | Silent tracking — logged internally, never surfaced unless systemic anomaly detected |
| **2** | `summary` | Periodic summary — included in operator digest/summary on a schedule |
| **3** | `ask` | Ask operator — surfaced at next operator interaction, not urgent |
| **4** | `interrupt` | Urgent interruption — operator is interrupted immediately, no delay |

Level 4 (urgent interruption) is reserved for genuinely critical signals: safety violations, PII leakage, truth authority compromise, or governance breach. **No level-4 signals were identified in Pass 1.**

---

## SECTION 4 — Permitted AAI Operations

AAI may perform the following operations automatically, without operator approval:

| Operation | Description |
|-----------|-------------|
| **Sort** | Group signals by source, type, or pattern |
| **Rank** | Order signals by attention level |
| **Deduplicate** | Collapse duplicate signals from the same source |
| **Suppress** | Drop level-0 signals from any surface or summary |
| **Summarize** | Aggregate level-1 and level-2 signals into digest format |
| **Route** | Direct level-3 signals to the appropriate operator surface at appropriate time |
| **Count** | Tally signal frequency and diversity for threshold comparisons |

These are all attention-management operations. None of them changes WESLR state, truth, contracts, governance, or external behavior.

---

## SECTION 5 — Forbidden AAI Operations

AAI may **NOT** perform the following, under any circumstances:

| Forbidden | Rationale |
|-----------|-----------|
| Approve a proposal | Proposals require explicit operator authorization |
| Modify a response contract | Contracts are truth-governed; AAI has no authority here |
| Change system state or truth | State transitions require operator approval via governance |
| Write to production truth files | `proposal_trace.jsonl`, `implementation_plans.jsonl`, entity graph, etc. |
| Change governance rules | Governance is operator-defined; AAI does not govern |
| Trigger external actions | External actions (email, API calls, deployments) require operator gate |
| Auto-transition proposal status | Status changes require operator review and explicit action |
| Override operator decisions | AAI ranks; operator decides |
| Interpret truth or authority | AAI does not assess correctness — only attention weight |

**Core invariant:** AAI is a filter, not an authority. It observes and ranks; it never authorizes.

---

## SECTION 6 — Operator Approval Requirements

Operator approval remains required for:

| Category | Example |
|----------|--------|
| Contract modifications | Adding, removing, or changing response contracts |
| Proposal decisions | Approving or rejecting `contract_proposal_review_v1` records |
| State changes | Adding entities, modifying capability graph, changing mode |
| Governance changes | Modifying WESLR_CORE_IDENTITY_V1, layered architecture, or coordination rules |
| External actions | OCW deployment, external API calls, user exposure changes |
| High-impact transitions | Any change that affects truth authority, safety, or operator trust |

AAI may surface and recommend; operator authorization is always required for anything beyond attention management.

---

## SECTION 7 — Pass 1 Classification Table

Based on `WESLR_OPERATOR_ATTENTION_INVENTORY_V1.md` Pass 1 inspection:

| Source | AAI Level | Classification | Rationale |
|--------|------------|----------------|-----------|
| `/chat` response path | **1** | `track` | Normal operational signal; fallback/blocked_write/rate_limited paths are expected in public mode; silent tracking sufficient |
| Public signal capture | **1** | `track` | Append failures are acceptable; track failure rate to detect systemic issues; no surfacing unless anomalous |
| Contract observation — stored records | **0** | `suppress` | Individual records are operational noise (31 records); no action unless systemic spike |
| Contract observation — validation failures | **0** | `suppress` | Internal record-level failures; do not affect user experience; silent drop is correct |
| Contract insufficiency detector | **2** | `summary` | `proposal_ready` patterns belong in periodic operator digest; pattern type and occurrence count are sufficient |
| Contract proposal review bridge | **3** | `ask` | New `contract_proposal_review_v1` records should surface to operator at next interaction; `generated > 0` triggers surfacing |
| Review interface — pending reviews | **2** | `summary` | Pending review count and by-pattern breakdown belongs in periodic summary; operator chooses when to review |

**Summary of Pass 1:**
- No level-4 (urgent interruption) sources identified
- No level-3 (ask) urgent sources — bridge proposals are `ask` but not interrupt
- 1 level-3 source: contract proposal review bridge (new proposals generated)
- 2 level-2 sources: insufficiency detector, review interface (periodic summary)
- 2 level-1 sources: /chat path, public signal capture (silent tracking)
- 2 level-0 sources: contract observation records, validation failures (noise suppression)

---

## SECTION 8 — AAI and Future Passes

Each subsequent Operator Attention Inventory pass will extend AAI's classification scope.

**Expected future classifications:**

| Pass | Area | Expected AAI Level |
|------|------|--------------------|
| N+1 | ISS diagnostics | 2–3 (probe results, gap signals) |
| N+1 | Proposal traceability | 2 (proposal lifecycle); 4 if PII leak |
| N+1 | Write handlers | 3–4 (state changes require operator gate) |
| N+1 | Public readiness gates | 2–4 (gates pass/fail may be urgent) |
| N+2 | Deployment / OCW handoff | 3 (commit validation failures) |
| N+2 | Evidence workspace | 2–3 (human review triggers) |
| N+2 | Signal aggregation | 2–3 (surfacing thresholds) |
| N+3 | Operator consistency | 2 (diagnostic; human-focused, not system-action) |
| N+3 | Frontend / UI | 1–2 (internal flags; mostly suppress) |

AAI level for each source will be confirmed in the relevant inventory pass.

---

## SECTION 9 — AAI Design Principles

| Principle | Description |
|-----------|-------------|
| **Noise suppression first** | Level-0 signals should never reach the operator. Suppress early. |
| **Silent tracking for operational signals** | Level-1 signals log internally; surface only if anomaly threshold crossed. |
| **Periodic summary for structured review** | Level-2 signals accumulate and appear in scheduled digest; not per-occurrence. |
| **Ask for decisions** | Level-3 signals require operator input before any further action; no automatic progression. |
| **Interrupt only for critical failures** | Level-4 signals are safety/privacy/truth events; everything else can wait. |
| **No false urgency** | AAI should never manufacture urgency. If a signal is not genuinely critical, it is not level 4. |
| **Operator burden reduction, not elimination** | AAI filters volume; it does not remove the operator from the loop for anything that matters. |

---

## SECTION 10 — Relationship to Governance

AAI and governance operate at different layers:

```
GOVERNANCE          ← operator authorization, contract changes, state transitions
AAI                 ← attention filtering, ranking, surfacing, suppression
signal sources      ← what is observed
```

AAI is downstream of governance decisions — it filters governance-relevant signals, but governance decisions are not made by AAI.

- AAI surfaces a level-3 proposal → operator reviews → operator approves/rejects via governance
- AAI surfaces a level-2 summary → operator notes → no immediate action required
- AAI suppresses level-0 noise → never reaches operator → no governance interaction

---

## SECTION 11 — Future AAI Expansion

AAI may expand to support:

| Expansion | Precondition |
|-----------|-------------|
| Cross-source correlation | Requires stable AAI classification across at least 3 passes |
| Anomaly threshold auto-tuning | Requires baseline volume data from ≥ 2 weeks of operation |
| Scheduled digest generation | AAI summary output is formatted for operator digest delivery |
| Multi-source deduplication | Handles same pattern appearing across different signal sources |
| AAI confidence scoring | Flags signals where classification confidence is low (operator review recommended) |

**Constraint:** AAI expansions must not introduce new decision authority, bypass governance, or enable automatic state changes.

---

## SECTION 12 — Verdict

**WESLR_ARTIFICIAL_ANALYSIS_INDEX_CANON_V1_DEFINED**

AAI is a global operator-attention filter. It ranks, sorts, suppresses, tracks, summarizes, and routes signals from across the WESLR system. It does not decide truth, authorize changes, modify state, or override operator decisions.

Core invariant: *AAI ranks attention. It does not decide truth.*

Initial scope covers Pass 1 sources only. Future passes extend AAI classification to ISS, write handlers, public readiness, deployment, UI, evidence workspace, signal aggregation, and operator consistency.

Operator approval remains required for all high-impact transitions. AAI reduces burden; it does not eliminate the operator from the loop.

---

*No implementation. No runtime changes. No tests modified. Doctrine only.*