# COMPRESSION_CANON_V1.md — WESLR Semantic Compression Canon

**Version:** 1.0
**Date:** 2026-04-21
**Status:** AUTHORITATIVE — describes current implemented reality only
**Scope:** All compression nodes, interface nodes, and semantic reduction mechanisms

---

## SECTION 1 — DEFINITION (CANONICAL)

A **compression node** (also **interface node**) in WESLR is a persisted or deterministically derivable data structure that:

1. Reduces N raw inputs into a smaller representational form
2. Is persisted to disk OR derivable deterministically from persisted data (not single-use)
3. Is reused across multiple operations (not one-shot)
4. Is NOT raw storage of unprocessed events

A node that only stores without reducing is **storage**, not a compression node. A node that exists but has no runtime consumers is **advisory**, not active compression.

---

## SECTION 2 — CURRENT IMPLEMENTED NODES

| Node | File | Compression Type | Persisted | Runtime Used? | Classification |
|------|------|----------------|-----------|--------------|----------------|
| `interest_tracker` | `weslr/interest_tracker.py` | Deduplication / topic abstraction | ✅ JSON | ❌ No runtime consumer found | ADVISORY |
| `relevance_surface` | `weslr/relevance_surface.py` | Scoring / ranking reduction | ❌ Stateless | ❌ No runtime consumer found | ADVISORY |
| `thread_tracker` | `weslr/thread_tracker.py` | Threading (sequence → named unit) | ✅ JSON | ✅ `dialogue.py`, `sim.py` | PRIMARY |
| `inadequacy_persistence` | `weslr/inadequacy_persistence.py` | Event logging (append, no reduction) | ✅ JSONL | ✅ `inadequacy_trigger` | PRIMARY |
| `inadequacy_trigger` | `weslr/inadequacy_trigger.py` | Temporal aggregation (events → clusters) | ❌ In-memory only | ✅ `inadequacy_handoff` | PRIMARY |
| `inadequacy_handoff` | `weslr/inadequacy_handoff.py` | Filtering (candidates → CDI handoffs) | ✅ JSONL | ✅ CDI pipeline | PRIMARY |
| `surface_to_spine_bridge` | `weslr/surface_to_spine_bridge.py` | Artifact → inadequacy event (manual) | ❌ Stateless | ❌ Manual CLI trigger only | ISOLATED |
| `suggestion_box` | `weslr/suggestion_box.py` | Raw request storage | ✅ JSON | ❌ No confirmed runtime consumer | ISOLATED |
| `artifact_inquiry` | `weslr/artifact_inquiry.py` | Artifact → question / resolution | ✅ open_question_registry | ❌ CLI-triggered only | ISOLATED |
| `internal_reasoning_graph` | `weslr/internal_reasoning_graph/` | Graph structuring (nodes + edges) | ✅ File-per-node | ✅ Governance / proposal pipeline | GOVERNANCE |

---

## SECTION 3 — CANONICAL COMPRESSION CHAINS

### Chain A — Runtime / Execution Spine (FULLY WIRED)

```
chat_responder.py
  → record_inadequacy_event() [inadequacy_persistence.py]
  → inadequacy_persistence appends one JSONL line per event
  → find_candidates() [inadequacy_trigger.py] — temporal window aggregation
  → inadequacy_trigger groups events within WINDOW_MINUTES=60, requires MIN_RECURRENCE=2
  → create_handoffs() [inadequacy_handoff.py] — filters by readiness_for_CDI
  → inadequacy_handoff emits handoff records (cdi_candidate_only status)
  → CDI pipeline
```

**What is compressed at each step:**
- `inadequacy_persistence`: 1 event per runtime failure (no compression — raw event log)
- `inadequacy_trigger`: N events in 60-minute window → K candidate groups (compression: temporal aggregation + recurrence gating)
- `inadequacy_handoff`: M candidates → H handoffs where H ≤ M (compression: filtering by CDI readiness)

**What is reduced:** Repeated runtime failures (noise) → structured CDI candidates (signal)
**What signal is preserved:** runtime_state, category, trigger_confidence, event_ids, lineage_ref

### Chain B — Governance / Reasoning Graph (FULLY WIRED)

```
cli_evidence.py
  → InternalReasoningGraphStore [internal_reasoning_graph/store.py]
  → ProposalWorkflow [internal_reasoning_graph/proposal_workflow.py]
  → ProposalGovernanceEngine [internal_reasoning_graph/governance.py]
  → Proposal pipeline
```

**What is compressed:** Complex reasoning steps → typed graph nodes + typed edges
**What is reduced:** Reasoning traces → structured nodes with content, evidence, governance status
**What signal is preserved:** Node type, content, timestamp, edge relationships, governance validation status

### Chain C — Advisory Layer (NOT CONNECTED TO SPINE)

These nodes exist and have implemented compression mechanics, but have **no confirmed runtime consumers**:

- `interest_tracker` → `relevance_surface`: topic deduplication + scoring, entirely unused in runtime
- `thread_tracker`: threading compression, but used for routing only (not adequacy/synthesis)
- `artifact_inquiry`: artifact → question compression, CLI-triggered only
- `suggestion_box`: external intake, not connected to any execution path

**All of the above are classified ADVISORY or ISOLATED. They do not feed the inadequacy spine.**

---

## SECTION 4 — COMPRESSION TYPES (BY MECHANISM)

| Mechanism | Node | Primary |
|-----------|------|---------|
| **Temporal aggregation** (events in window → clusters) | `inadequacy_trigger` | ✅ |
| **Deduplication / topic abstraction** (N mentions → 1 interest record) | `interest_tracker` | ✅ |
| **Threading** (sequence → named chronological unit) | `thread_tracker` | ✅ |
| **Scoring / ranking reduction** (N interests → top-K scored) | `relevance_surface` | ✅ |
| **Filtering** (candidates → CDI handoffs) | `inadequacy_handoff` | ✅ |
| **Graph structuring** (reasoning → typed nodes + edges) | `internal_reasoning_graph` | ✅ |
| **Artifact → question** (large document → single question) | `artifact_inquiry` | ✅ |
| **Event logging** (append, no aggregation) | `inadequacy_persistence` | ⚠️ Not compression — logging only |
| **Raw storage** (request verbatim) | `suggestion_box` | ⚠️ Not compression — storage only |

Note: `inadequacy_persistence` is listed for completeness but does not compress — it appends one line per event. Compression begins in `inadequacy_trigger`.

---

## SECTION 5 — CURRENT LIMITATIONS (PROVEN ONLY)

1. **`relevance_surface` not consumed in runtime**
   - File: `weslr/relevance_surface.py`
   - `query_relevant_interests()` has zero confirmed runtime call sites outside test files
   - Classification is ADVISORY — scoring and compression exist but unused

2. **`interest_tracker` occurrence_count not active**
   - File: `weslr/interest_tracker.py`
   - `occurrence_count` field is stored but always 0 (v1 — reserved for future)
   - Compression benefit (N mentions → 1 record) is real but `occurrence_count` does not feed scoring

3. **`surface_to_spine_bridge` is manual-only**
   - File: `weslr/surface_to_spine_bridge.py`
   - `confirm_mode()` requires explicit human CLI trigger
   - No automatic path from artifact evaluation to inadequacy event
   - Classification: ISOLATED

4. **`suggestion_box` not connected to execution spine**
   - File: `weslr/suggestion_box.py`
   - `improvement_engine.py` comments mention it as input; no confirmed runtime import or call
   - Classification: ISOLATED

5. **`artifact_inquiry` is CLI-triggered only**
   - File: `weslr/artifact_inquiry.py`
   - Called from `sim.py:3250` via artifact review command; not called from dialogue or execution flow
   - Classification: ISOLATED

6. **No cross-node flow**
   - `interest_tracker` does not feed `inadequacy_trigger`
   - `thread_tracker` does not feed `suggestion_box` or `inadequacy_handoff`
   - `relevance_surface` does not feed any other node
   - Each compression node is an isolated island

7. **No unified compression contract**
   - Files: `weslr/interest_tracker.py`, `weslr/inadequacy_trigger.py`, `weslr/thread_tracker.py`, `weslr/internal_reasoning_graph/store.py`
   - Each node uses different mechanisms, different storage formats, different quality signals
   - No shared base class, no shared interface, no uniform classification taxonomy

8. **No freshness/decay in `interest_tracker`**
   - File: `weslr/interest_tracker.py`
   - `last_seen_at` is stored but no decay function exists
   - Old interests do not degrade in scoring over time

---

## SECTION 6 — WHAT IS ALREADY STRONG

1. **Inadequacy pipeline is fully wired**
   - Evidence: `chat_responder.py:555` and `:641` call `record_inadequacy_event()`
   - `inadequacy_trigger` aggregates with recurrence gating (MIN_RECURRENCE=2, WINDOW_MINUTES=60)
   - `inadequacy_handoff` filters with CDI readiness gate
   - Complete chain from runtime event → CDI candidate exists and is functional

2. **Real recurrence + confidence logic exists**
   - Evidence: `inadequacy_trigger.py:find_candidates()` computes `trigger_confidence`
   - `runtime_state` diversity across events increases confidence
   - Recurrence gating prevents single-event noise from triggering

3. **Compression reduces runtime noise meaningfully**
   - Evidence: 100 runtime failures in an hour → N CDI candidates (N << 100)
   - The `readiness_for_CDI` filter in `inadequacy_handoff` ensures only structured candidates reach governance

4. **Governance path is structured**
   - Evidence: `internal_reasoning_graph/store.py` persists nodes + edges with validation
   - `ProposalGovernanceEngine` applies governance rules before proposals advance
   - Proposal lineage is preserved via `lineage_diff.py` tracking

5. **`thread_tracker` is genuinely used in dialogue routing**
   - Evidence: `dialogue.py` — `active_thread` is the third branch of the routing split
   - `pick_relevant_active_thread()` in `sim.py` feeds the active_thread into the payload function
   - This is a real compression node with a real runtime consumer

6. **`relevance_surface` scoring law is well-designed**
   - Evidence: `weslr/relevance_surface.py` — recency bonuses exist but cannot create relevance alone
   - Law: "If no non-recency signal exists, score is 0"
   - This prevents recency inflation and is a meaningful semantic constraint

---

## SECTION 7 — CANONICAL CLASSIFICATION

**Classification: B — Partial / fragmented compression (some nodes, no unified behavior)**

**Justification:**

- The inadequacy pipeline (Chain A) is the only fully wired, runtime-active compression path. It has recurrence gating, confidence scoring, and CDI output — it works.
- All other compression nodes (`interest_tracker`, `relevance_surface`, `thread_tracker` advisory use, `artifact_inquiry`, `suggestion_box`) are either unused in runtime, used only for routing, or used only for governance.
- There is no shared contract between compression nodes — different mechanisms, different storage, different signals, no unified interface.
- `surface_to_spine_bridge` exists as a documented tool but requires manual CLI trigger and is not integrated into any automatic pipeline.
- The governance path (`internal_reasoning_graph`) is the second strongest compression system — structured reasoning compression with validation — but it is entirely separate from the runtime spine.

**The foundation is real. The integration is partial.**

---

## SECTION 8 — FORBIDDEN DRIFT

The following are **explicitly prohibited** without a canon update and operator approval:

1. **No new compression nodes without canon update** — any new node that claims compression behavior must be added to this document with classification before it can be used in runtime
2. **No parallel compression pipelines** — all runtime adequacy signals must route through `inadequacy_persistence` → `inadequacy_trigger` → `inadequacy_handoff`; no bypass
3. **No silent auto-integration of advisory nodes into spine** — `relevance_surface`, `interest_tracker`, `suggestion_box`, `artifact_inquiry` must not be wired into execution paths without governance review and canon update
4. **No mixing advisory with execution without explicit classification upgrade** — an ADVISORY node becomes PRIMARY only through documented evidence of runtime consumption
5. **No new compression chains without documentation** — any chain from surface signal to governance/proposal must be mapped in this canon before activation
6. **No bypass of `inadequacy_handoff` CDI readiness gate** — handoffs marked `cdi_candidate_only` must not reach CDI without going through the governance engine

---

## SECTION 9 — STOP LINE

Confirmed:

- ✅ Documentation only — this file is the output
- ✅ No code changes — document describes current implemented reality
- ✅ No schema changes — no new storage formats introduced
- ✅ No new execution paths — all chains described are already implemented
- ✅ No new compression nodes listed without implementation reference

---

**Canon version history:**
- v1.0 (2026-04-21) — initial canonicalization based on codebase inspection
