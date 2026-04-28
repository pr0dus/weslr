# WESLR Signal Aggregation V1 — Doctrine Extension

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — governs cross-user pattern detection and demand aggregation
**Created:** 2026-04-28
**Owner:** operator + system architect
**Related:** WESLR_CORE_IDENTITY_V1.md · WESLR_COORDINATION_LAYER_V1.md · WESLR_OMNI_EXECUTION_MODEL_V1.md · WESLR_EVIDENCE_WORKSPACE_V1.md

---

## SECTION 1 — Purpose

WESLR evolves through governed, structured intelligence — not through passive accumulation of user inputs. This document defines how WESLR detects patterns across interactions without storing individual user data, and how those patterns may inform system development without compromising privacy, truth authority, or governance.

> **"WESLR evolves through aggregated, anonymized interaction patterns — not individual user inputs."**

Signal aggregation transforms raw interaction patterns into anonymous, threshold-gated signals. Signals suggest; they never directly cause changes. Every system modification remains under operator governance.

---

## SECTION 2 — Core Principles

These principles govern every aspect of signal aggregation.

### P1 — Aggregation Over Individuals

No individual user action is tracked or stored. Signals emerge only from patterns across multiple interactions, users, or sessions — never from a single prompt.

### P2 — Patterns Over Raw Data

WESLR stores pattern descriptors, not the prompts that generated them. A signal records that *"queries about solar panels are recurring"* — not what any individual user asked about solar panels.

### P3 — Signals Over Prompts

The unit of aggregation is the signal — a normalized, anonymized metric — not the raw user message. Signals are derived statistics; raw prompts are never written to signal storage.

### P4 — Thresholds Before Surfacing

Signals do not surface to the operator until explicit thresholds are met. Anonymous presence is not sufficient. A signal must be persistent, diverse, and significant before it is presented.

### P5 — Suggestion Not Action

Signals suggest; operators decide. A surfaced signal is an invitation to review, not an authorization to act. No signal directly modifies system behavior.

---

## SECTION 3 — Signal Types

Signals are derived from interaction patterns. The following signal types are defined:

### S1 — Repeated Unknown Query Signal

**Trigger:** The same or substantively similar query is made repeatedly with no structured answer available.

**Fields:**
- `topic_normalized`: stripped, lowercased topic identifier
- `query_template`: anonymized pattern (no raw prompts stored)
- `frequency_count`: number of occurrences
- `session_diversity`: count of distinct sessions/users
- `first_seen`: timestamp
- `last_seen`: timestamp
- `evidence_workspace_count`: how many times Evidence Workspace was used for this topic

**Surfacing threshold:** frequency >= 10, diversity >= 3 distinct sessions

---

### S2 — Evidence Workspace Usage Signal

**Trigger:** Evidence Workspace is activated for a topic.

**Fields:**
- `topic_normalized`: stripped, lowercased topic identifier
- `usage_count`: total Evidence Workspace activations
- `unique_sessions`: distinct sessions
- `last_used`: timestamp
- `average_session_depth`: average evidence interactions per session

**Surfacing threshold:** usage >= 5, diversity >= 2 distinct sessions

---

### S3 — Recurring Topic Cluster Signal

**Trigger:** Multiple related topics are queried together or in sequence, indicating a domain of interest.

**Fields:**
- `cluster_id`: anonymous identifier for the topic cluster
- `topics`: list of normalized topic identifiers in cluster
- `co_occurrence_count`: how often these topics appeared together
- `dominant_topic`: most frequent topic in cluster
- `session_diversity`: distinct sessions exhibiting cluster

**Surfacing threshold:** co_occurrence >= 5, diversity >= 2

---

### S4 — Frequent Fallback Trigger Signal

**Trigger:** The safe fallback response fires repeatedly for similar query types.

**Fields:**
- `fallback_type`: categorized fallback type
- `query_pattern`: anonymized query class (not raw prompt)
- `trigger_count`: number of fallbacks
- `distinct_sessions`: sessions where this fallback fired

**Surfacing threshold:** count >= 15, diversity >= 3

---

### S5 — Repeated Improvement Query Signal

**Trigger:** "How can you improve" or equivalent is queried repeatedly.

**Fields:**
- `query_type`: "improvement_query"
- `count`: number of occurrences
- `sessions`: distinct session count
- `last_seen`: timestamp

**Surfacing threshold:** count >= 5, diversity >= 2

---

### S6 — Entity Co-occurrence Emergent Signal

**Trigger:** Entity pairs co-occur in messages at statistically significant rates across sessions.

**Fields:**
- `entity_pair`: sorted lowercase pair (entity_a | entity_b)
- `pair_count`: co-occurrence count
- `session_diversity`: sessions observing this pair
- `first_seen`, `last_seen`: timestamps

**Surfacing threshold:** count >= 10, diversity >= 3

---

## SECTION 4 — Signal Representation

Every signal stored in WESLR signal storage must satisfy these constraints.

### Signals Must Contain:

| Field | Type | Description |
|-------|------|-------------|
| `signal_id` | string | Unique anonymous identifier |
| `signal_type` | enum | One of S1–S6 defined above |
| `topic_normalized` | string | Anonymized, stripped topic identifier |
| `frequency_count` | int | Raw occurrence count |
| `session_diversity` | int | Count of distinct sessions |
| `growth_trend` | enum | growing / stable / fading |
| `first_seen` | timestamp | When first observed |
| `last_seen` | timestamp | Most recent observation |
| `confidence` | float | Statistical confidence (0–1) |

### Signals Must NOT Contain:

| Forbidden | Rationale |
|-----------|-----------|
| Raw user prompts | Individual inputs are never stored |
| User identifiers | Anonymous by design |
| Session content | Only metadata, not content |
| Private data | No PII, no personal context |
| IP addresses | Not collected |
| Raw query text | Only anonymized patterns |

---

## SECTION 5 — Pattern Detection

WESLR's pattern detection operates on anonymized signal data only.

### Detection Mechanisms:

**D1 — Topic Normalization**
Raw query text is normalized (lowercased, stripped, stopwords removed) before signal creation. The normalized form is the signal's topic identifier. The original text is never stored.

**D2 — Anonymized Aggregation**
Signals are aggregated across sessions without linking to specific users, IPs, or identities. The session identifier used in signal storage is a local anonymous token — not traceable to a user.

**D3 — Diversity Gating**
A signal cannot surface based on a single session or user. Diversity thresholds (minimum distinct sessions) ensure no individual can disproportionately trigger a surfacing.

**D4 — Growth Classification**
Each signal's trajectory is classified:
- `growing`: last_seen within 7 days, count increasing
- `stable`: last_seen within 30 days, count flat
- `fading`: last_seen > 30 days ago, or count declining

### Pattern Grouping:

Signals may be grouped into higher-level patterns:

| Group | Composed Of | Purpose |
|-------|-------------|---------|
| Topic clusters | S1 signals with related topic_normalized | Identify domain-level demand |
| Capability gaps | S1 + S4 signals | Surface where WESLR repeatedly fails to answer |
| Evidence demand | S2 signals | Identify topics users explore via Evidence Workspace |
| Evolution interest | S5 signals | Identify users exploring WESLR self-improvement |

---

## SECTION 6 — Threshold Logic

Surfacing is gated by explicit thresholds. No signal surfaces to the operator until all thresholds for its type are met.

### Surfacing Requirements (all must be true):

| # | Requirement | Purpose |
|---|-------------|---------|
| T1 | Frequency threshold met | Signal is not a one-time event |
| T2 | Diversity threshold met | Signal is not generated by a single user |
| T3 | Persistence confirmed | Signal has been observed over time, not just in one burst |
| T4 | Growth trend not fading | Signal is active, not declining |
| T5 | No counter-signal | There is no contradictory signal (e.g., satisfaction signal) |

### No Single-User Trigger Rule:

**Critical:** No signal may surface based primarily on a single session or user, regardless of frequency. Diversity thresholds exist specifically to prevent one user's behavior from generating a surfaced signal.

### Threshold Override:

No threshold may be overridden by code, LLM, or automated process. Thresholds may only be adjusted by explicit operator decision via governance.

---

## SECTION 7 — Operator Surface

When thresholds are met, WESLR may surface a signal to the operator as a suggestion.

### Surfaced Signal Presentation:

```
═══════════════════════════════════════
SIGNAL: Repeated Unknown Query
Topic: solar_panel_optimization
───────────────────────────────────────
Frequency:     14 occurrences
Sessions:      4 distinct
Trend:         growing
Confidence:    0.82
Evidence WS:   3 uses
───────────────────────────────────────
WESLR has repeatedly received queries
about solar_panel_optimization with
no structured answer available.
Evidence Workspace was used 3 times
for related exploration.
═══════════════════════════════════════

Suggestion:
"Topic 'solar_panel_optimization' shows
recurring demand with no structured
capability. Consider creating a
proposal to add structured knowledge."

[CREATE PROPOSAL]  [DISMISS]  [SCHEDULE REVIEW]
```

### What Surfaced Signals Produce:

| User Action | Result |
|-------------|--------|
| Create proposal | Routes through governance → normal proposal flow |
| Dismiss | Signal remains tracked; will resurface if thresholds met again |
| Schedule review | Defers surfacing; signal continues accumulating |

### What Surfaced Signals Do NOT Produce:

| Action | Why Forbidden |
|--------|--------------|
| Direct system modification | Always requires operator approval |
| Automatic proposal creation | Proposals require intentional operator action |
| Capability addition | Capabilities are governed |
| Evidence Workspace activation | Not triggered by signals |

---

## SECTION 8 — Relationship to Evidence Workspace

Evidence Workspace and Signal Aggregation are complementary: Evidence Workspace generates signals; Signal Aggregation transforms signals into surfaced suggestions.

### Evidence Workspace → Signal Flow:

```
User activates Evidence Workspace for [topic]
    ↓
Evidence Workspace usage signal recorded (S2)
    ↓
(topic_normalized, usage_count, diversity, last_used)
    ↓
Signal Aggregation tracks S2 over time
    ↓
Thresholds met (usage >= 5, diversity >= 2)
    ↓
Operator receives surfacing:
"Evidence demand detected: [topic]"
    ↓
Operator decides: create proposal? dismiss? defer?
```

### Signal Aggregation → Evidence Workspace Feedback:

If a topic surfaces via S1/S2 signals and a proposal is approved:

```
Proposal approved → Implementation → Structured capability added
    ↓
Topic now has structured answer
    ↓
Evidence Workspace usage for that topic should decline
    ↓
S2 signal for that topic should trend toward fading
```

This creates a natural feedback loop: signals drive capability expansion; capability expansion reduces evidence demand signals.

---

## SECTION 9 — Governance Interaction

Signal Aggregation interacts with WESLR governance as follows:

### What Signals Cannot Do:

| Forbidden | Why |
|-----------|-----|
| Write proposals directly | Proposals require operator intent |
| Change system behavior | Behavior changes require governance |
| Modify memory | Memory is derived from governed state |
| Auto-create capabilities | Capabilities are approval-bounded |
| Bypass mode restrictions | Mode controls signal accumulation |
| Trigger LLM responses | Signals are internal metrics, not triggers |
| Access raw user input | Signal storage receives only anonymized metrics |

### What Signals Can Only Do:

```
Signal meets surfacing threshold
    ↓
WESLR presents suggestion to operator
    ↓
OPERATOR CHOOSES:
    ├─ Create proposal → governance flow (normal)
    ├─ Dismiss → signal stays, will retry after more accumulation
    └─ Adjust threshold → operator governance action
```

**Rule:** Signals are strictly suggestion-level. No signal may cause a direct state change.

---

## SECTION 10 — Privacy Guarantees

Signal Aggregation is designed for privacy by architecture, not by policy.

### Guarantees:

| # | Guarantee | Implementation |
|---|-----------|----------------|
| G1 | No user identity tracking | Signal storage uses anonymous session tokens; no user IDs |
| G2 | No raw message storage | Raw prompts are never written to signal storage |
| G3 | Only anonymized metrics | Signal fields are statistical, not descriptive |
| G4 | Append-only signal logs | Signals are added; historical signals are preserved for trend analysis |
| G5 | No cross-session linking | Sessions are not linked; each signal aggregation is independent |
| G6 | No PII collection | No names, emails, IPs, or personal context enters signal storage |
| G7 | Local-only signal storage | Signals stored on WESLR host; not transmitted externally |

### Auditability:

All signal storage is append-only and inspectable by the operator. Signal data structures are documented in this doctrine — not hidden or encrypted from the operator.

---

## SECTION 11 — Future Expansion

Signal Aggregation supports future expansion in these directions:

| Expansion | Precondition |
|-----------|--------------|
| Demand-driven capability building | Signals inform proposal prioritization; operator still approves |
| Dataset generation (governed) | Aggregated anonymized signals may form training datasets for domain-specific WESLR adapters; operator approval required |
| Scientific workflows | WESLR as research tool: signals track domain research demand; Evidence Workspace supports exploration |
| Domain specialization | Signals may indicate demand for domain-specific adapters; governed proposal required before integration |
| Multi-WESLR federation | Cross-instance signal sharing; requires explicit operator configuration; privacy-preserving aggregation protocol |
| Predictive capability planning | Signals inform roadmap prioritization; no automatic capability creation |

**Constraint:** Future expansions must not weaken privacy guarantees, remove operator governance, or allow signals to directly modify state.

---

## SECTION 12 — Cross-Doctrine Alignment

| Document | Alignment |
|----------|-----------|
| WESLR_CORE_IDENTITY_V1.md | Signal Aggregation is consistent with identity: WESLR does not "learn from users" in the traditional sense; evolution is governed, anonymized, and operator-approved |
| WESLR_COORDINATION_LAYER_V1.md | Signals route through Layer 2; surfacing is a Layer 2 operation; no automatic write bypasses governance |
| WESLR_OMNI_EXECUTION_MODEL_V1.md | Signal generation uses the same failure-route tracking already defined; no new tracking mechanisms |
| WESLR_EVIDENCE_WORKSPACE_V1.md | Evidence Workspace explicitly generates S2 signals; the two documents form a complete feedback loop |
| WESLR_LLM_CONTEXT_BOUNDARY_V1.md | Signals do not enter LLM context; surfacing presents operator suggestions, not LLM-generated content |

---

## SECTION 13 — Verdict

**WESLR_SIGNAL_AGGREGATION_DEFINED**

Signal Aggregation enables WESLR to detect meaningful patterns across interactions without storing individual user data, without bypassing governance, and without compromising truth authority. Signals are anonymized, threshold-gated suggestions — they inform operator decisions but never cause direct system changes.

Core invariant: Signals suggest; operators decide. No aggregation pathway allows a user pattern to directly modify WESLR state.
