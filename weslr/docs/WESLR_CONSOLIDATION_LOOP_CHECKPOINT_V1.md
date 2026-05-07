# WESLR Consolidation Loop — Checkpoint V1

**Checkpoint:** WESLR_CONSOLIDATION_LOOP_CHECKPOINT_V1
**Date:** 2026-05-07
**Status:** checkpoint — not yet accepted doctrine
**File:** `weslr/docs/WESLR_CONSOLIDATION_LOOP_CHECKPOINT_V1.md`

---

## SECTION 1 — Safety Check

```
pwd: /data/data/com.termux/files/home/.openclaw/workspace
git root: /data/data/com.termux/files/home/.openclaw/workspace
branch: main
latest commit: 1d63dc1 WESLR: add safe entity-scoped memory capture
git status: clean — only untracked session/frontier artifacts
```

✅ No source, docs, or test files are dirty. No staged changes.

---

## SECTION 2 — Document Purpose

### WESLR Consolidation Loop is Not OpenClaw Dreaming

OpenClaw dreaming (at `memory/.dreams/`) is an OpenClaw-native sleep-time memory consolidation system that operates on OpenClaw's own session traces, memory files, and recall events. It is not WESLR's, and WESLR should not adopt its model directly.

**WESLR's Consolidation Loop** is a WESLR-native memory lifecycle that converts short-term traces into reviewable candidates for:

- **Continuity memory** — stable session patterns, working facts, preferences
- **Entity memory** — repeated entity patterns, stable preferences, cross-session facts
- **Relationship memory** — relationship observations, depth signals, trust indicators
- **Mission memory** — frontier gaps, research outcomes, mission progress
- **Evidence memory** — validated causal links, evidence packets, fact assertions
- **Hypothesis memory** — candidate explanations with supporting evidence
- **Proposal/review records** — governance proposals, review decisions, improvement candidates
- **Doctrine candidates** — governance patterns requiring operator review
- **Archive/digest records** — raw traces without promotion value

### Core Rule

> WESLR may consolidate signals.
> WESLR may not silently promote high-impact truth, doctrine, identity, governance, code, or research claims.

Consolidation is not promotion. Promotion requires governance. The loop may produce candidates; the operator approves their destination.

---

## SECTION 3 — Existing Pieces

| File | Role | Classification |
|------|------|----------------|
| `weslr/continuity_consolidation.py` | Bounded runtime dedupe + trim | Source / partial consolidation |
| `weslr/operator_insight_consolidation.py` | Per-case recovery guidance + decision trace + drift + pattern summary | Source / partial consolidation |
| `weslr/unified_continuity.py` | Context consolidation design: user profile + patterns + governance state | Source / partial consolidation |
| `weslr/context_decay_policy.py` | Decay classification (fresh/aging/stale/archival) — read-only | Decay classifier |
| `weslr/entity_timeline_memory.py` | Per-entity append-only timeline events | Timeline memory |
| `weslr/entity_memory.py` | Entity-scoped memory records with access levels | Entity memory |
| `weslr/relationship_observation_capture.py` | Relationship observation records | Entity memory / relationship |
| `weslr/observation_harness.py` | Scripted observation session runner + timeline segment builder | Source / evidence |
| `weslr/frontier_daemon.py` | Proactive daemon cycling through frontier observations, writes pending_messages | Attention routing |
| `weslr/proactive_suggestions.py` | Theme classification + proactive suggestion builder | Attention routing |
| `weslr/mission_store.py` | Mission records with frontier gaps, research outcomes | Source / mission |
| `weslr/experiment_proposal_store.py` | Experiment proposals and hypotheses | Source / hypothesis |
| `weslr/evidence_timeline.py` | Evidence timeline events | Source / evidence |
| `weslr/operator_insight_timeline.py` | Operator recovery insight timeline entries | Source / operator |
| `memory/.dreams/events.jsonl` | OpenClaw dreaming events (sleep-time recall) | External/OpenClaw layer |
| `memory/.dreams/short-term-recall.json` | OpenClaw short-term recall cache | External/OpenClaw layer |

**Key classification:**
- **Source layers:** `continuity_consolidation`, `operator_insight_consolidation`, `unified_continuity`, `observation_harness`, `frontier_daemon`, `mission_store`, `experiment_proposal_store`, `evidence_timeline`, `operator_insight_timeline`
- **Timeline memory:** `entity_timeline_memory`, `relationship_observation_capture`
- **Entity memory:** `entity_memory` (already has promotion gating via Phase 4 memory_capture)
- **Decay classifier:** `context_decay_policy` (read-only, no writes)
- **Attention routing:** `frontier_daemon`, `proactive_suggestions`
- **External/OpenClaw layer:** `memory/.dreams/` — not WESLR-native, not WESLR's to consume or write

---

## SECTION 4 — Consolidation Loop Design

### Phase 1 — Collect

Read recent traces from:
- `pending_messages` — frontier daemon output
- `mission_store` entries — research missions, frontier gaps, outcomes
- `experiment_proposal_store` — hypotheses, candidates
- `evidence_timeline` events — fact assertions, evidence packets
- `relationship_observation_capture` records — relationship signals
- `entity_timeline_memory` — per-entity event timeline
- `observation_harness` logs — scripted observation results
- `proposal_review_log` — governance proposal status changes
- `operator_insight_timeline` — recovery guidance, decisions, drift
- `test_results` / commit checkpoints — validation outcomes
- `entity_memory` recent records — existing promoted memory for comparison

Collection window: configurable, default last 24h or last session boundary.

### Phase 2 — Cluster

Group traces by:
- **entity** — person, project, institution
- **tenant** — workspace scope
- **user** — operator identity
- **project** — Weslr sub-project
- **mission** — research mission ID
- **doctrine area** — Phase 1-11 classification
- **research domain** — materials science, causality, etc.
- **phase** — implementation phase
- **recurring gap** — repeated gap themes across cycles

Clustering method: template-based (no LLM), using keyword/signal matching on trace metadata and tags.

### Phase 3 — Score

Score each cluster by:
- **frequency** — how many traces mention this theme
- **recency** — freshest evidence timestamp
- **source diversity** — how many distinct source types (evidence + mission + relationship)
- **evidence strength** — has external validation or just internal claim
- **contradiction level** — conflicting signals within the same cluster
- **risk** — doctrine/identity/governance/structural impact
- **operator relevance** — directly relevant to current operator goals
- **mission relevance** — impacts active research mission
- **doctrine impact** — touches governance, Phase 9/10/11 areas
- **confidence** — source provenance quality

### Phase 4 — Classify Destination

Possible destinations for each cluster:

| Destination | When |
|-------------|------|
| Continuity summary | Stable working facts, session patterns without entity scope |
| Entity memory candidate | Repeated entity patterns, stable preferences, cross-session facts |
| Relationship memory candidate | Relationship observation signals, trust indicators |
| Mission memory candidate | Mission progress, frontier gaps, research outcomes |
| Evidence/hypothesis candidate | Validated causal links, evidence-backed explanations |
| Proposal/review candidate | Governance proposals, improvement suggestions, review decisions |
| Doctrine candidate | Governance patterns, Phase 9/10/11 structural changes |
| Validation gap | Known unknowns, missing evidence, unresolved contradictions |
| Archive only | Raw traces exceeding retention without promotion value |
| Discard | Noise, one-off, no signal, below confidence threshold |

### Phase 5 — Governance Gate

**Core principle:** Consolidation may produce candidates; promotion requires governance.

| Risk level | Examples | Required action |
|-------------|----------|----------------|
| Low | Continuity summaries, working facts | May be auto-suggested or auto-saved only if doctrine allows |
| Medium | Entity/relationship/mission memory, preferences | Operator review before promotion |
| High | Doctrine/governance/identity/code/research truth | Explicit approval required |
| Critical | Code changes, identity assertions, structural doctrine | Staged review, full governance |

**Hard limits — never in V1:**
- No automatic promotion to doctrine registry
- No automatic entity memory writes
- No automatic code changes
- No automatic deletion
- No automatic identity assertions

### Phase 6 — Write

V1 writes only to:
```
.weslr/consolidation_digest.jsonl
```

Each record:
```json
{
  "type": "consolidation_candidate",
  "cluster_id": "...",
  "theme": "...",
  "evidence": ["source_refs"],
  "score": { "frequency": N, "recency": ts, "diversity": N, ... },
  "proposed_destination": "entity_memory | mission_store | doctrine_candidate | ...",
  "risk_level": "low | medium | high",
  "provenance": ["pending_message_id", "evidence_packet_id", ...],
  "created_at": "ISO8601",
  "operator_action_required": true | false,
  "gate_note": "why promotion requires review"
}
```

No promotion in V1. All candidates are operator-visible digest records.

### Phase 7 — Explain

Produce a human-readable consolidation digest:

```
=== WESLR Consolidation Digest ===
Date: YYYY-MM-DD
Clusters: N
Candidates: N
Auto-suggested: N (low-risk only, if doctrine allows)
Review required: N

--- Clusters ---
[theme] N traces | score: X | proposed: Y | risk: Z
  evidence: [list of source refs]
  note: [why this matters]

--- Actions ---
[ ] Review: [high-risk candidate description]
[ ] Approve: [medium-risk candidate description]
[ ] Acknowledge: [low-risk auto-suggested]

--- Not Promoted ---
[theme] — reason: [why it stayed as candidate]
```

---

## SECTION 5 — Memory Stack

### 8-Layer Architecture

```
Layer 1: Raw Trace Layer
=======================
Sources:
  - pending_messages (frontier daemon)
  - mission_store entries
  - experiment_proposal_store records
  - evidence_timeline events
  - fact_extractor assertions
  - relationship_observation records
  - entity_timeline events
  - observation_harness logs
  - operator_insight_timeline entries
  - test_results, commit checkpoints
  - entity_memory recent records

Layer 2: Scoped Event Layer
==========================
- entity_timeline_memory (append-only per entity)
- entity_memory (scoped records with access levels)
- relationship_observation_capture (relationship-scoped)
- continuity entries (session-scoped)
- operator_insight_timeline (per-case)
All: append-only, provenance-tagged

Layer 3: Consolidation Layer         ← NEW — not yet implemented
========================================
collect() → cluster() → score() → classify() → gate() → write()
Reads Layer 1+2, produces consolidation candidates
V1: read-only, writes only to consolidation_digest.jsonl

Layer 4: Candidate Memory Layer
================================
- consolidation_digest.jsonl       ← V1 output
- consolidation_candidates.jsonl   ← future promotion queue
- proposal_review_log              ← governance decisions

Layer 5: Governance Promotion Layer
====================================
- Doctrine registry (Phase 9)
- Mission store (Phase 10)
- Evidence packets (Phase 7)
- Human-in-the-loop gates
- Explicit approval required for all Layer 6 writes

Layer 6: Durable Memory Layer
==============================
Promoted records:
  - entity_memory (approved entity patterns)
  - relationship_observations (approved)
  - doctrine_registry (approved doctrine)
  - mission_store (approved mission updates)
  - evidence_timeline (validated evidence)

Layer 7: Retrieval/Access Layer
================================
- entity_memory queries by scope + access level
- provenance-tagged retrieval
- access-level filtering (operator_only, private, tenant, public)
- MemoryRecord provenance chain back to source traces

Layer 8: Audit/Explanation Layer
==================================
- consolidation digest (human-readable)
- provenance chain per record
- review decisions logged (who approved what, when, why)
- no raw traces stored, only fingerprints + evidence
```

### Connections to Existing Loops

| Loop/System | Connection to Consolidation |
|-------------|---------------------------|
| **Attention Loop** | Provides `pending_messages` to Layer 1; consumes Layer 4 digest for attention routing |
| **Research Work Loop** | Provides mission_store + evidence_timeline to Layer 1; receives mission_memory candidates from Layer 4 |
| **Doctrine Registry** | Layer 5 governance target; doctrine candidates from Layer 4 require Phase 9 approval |
| **Entity Memory** | Layer 2 source; Layer 6 destination; Phase 4 memory_capture gates writes |
| **Relationship Memory** | Layer 2 source; Layer 6 destination; relationship_observation_capture provides traces |
| **Evidence Packets** | Layer 1 source; Layer 5/6 governance target; causal links scored in Phase 3 |
| **Mission Store** | Layer 1 source; Layer 6 destination; mission_memory candidates from Layer 4 |
| **Proactive Daemon** | Consumes Layer 4 digest output; frontier_daemon provides pending_messages to Layer 1 |
| **Context Decay Policy** | Phase 3 scoring input; context_decay_policy classifies age/relevance (read-only) |
| **Observation Harness** | Layer 1 source; scripted observation results feed into consolidation clusters |

---

## SECTION 6 — Memory Ideas to Adopt

### P1 — Already Implemented
| Idea | File | Status |
|------|------|--------|
| Multi-scope memory routing | `entity_memory.py` | ✅ Done — AccessLevel scoping (operator_only/private/tenant/public) |
| Write-path filter | `memory_capture.py` (Phase 4) | ✅ Done — evidence-gated, scope-gated, privacy-aware |
| Memory access policy | `entity_memory.py` | ✅ Done — AccessLevel enum, retrieval filtering |
| Attention memory | `frontier_daemon.py` + `proactive_suggestions.py` | ✅ Done — pending_messages queue, forecast alerts |

### P2 — High-Value Next
| Idea | Risk | Priority | Notes |
|------|------|----------|-------|
| Contradiction-aware memory | Medium | P2 | Never overwrite blindly; create conflict records; require resolution |
| Causal memory | Medium | P2 | Store what caused improvement/failure; useful for research missions |
| Outcome-backed memory | Medium | P2 | Memories strengthen when later outcomes confirm; failed advice weakens |
| Provenance graph | Medium | P2 | Every memory links to source event, file, commit, mission, evidence packet |
| Procedural workflow memory | Medium | P2 | WESLR learns "how we do things" — commit discipline, /new handoff, mission review |
| Confidence-tiered memory | Low | P2 | Tiers: observed / repeated / validated / operator-approved / doctrine |
| Research memory | Medium | P2 | Recurring materials, mechanisms, contradictions, candidate hypotheses |

### P3 — Later
| Idea | Risk | Priority | Notes |
|------|------|----------|-------|
| Memory half-life/decay with action | Low | P3 | Stale low-confidence items decay; important confirmed items persist |
| Memory budget/compression | Low | P3 | Summarize clusters, archive raw traces; prevent memory bloat |
| Reflective memory with tests | Medium | P3 | Memory candidates should point to validation/test evidence if they affect architecture |

---

## SECTION 7 — First Safe Vertical Slice

### V1: Read-Only Consolidation Digest

**Principle:** V1 establishes the loop pattern safely. No promotion. No writes to existing stores. Operator-visible only.

#### Input (V1 — safe traces only)
- Recent `pending_messages` (last 24h)
- Recent `mission_store` entries (last 7 days)
- Evidence packet metadata (type, theme, source — not raw content)
- Recent observation/proposal gaps if available
- **Excluded from V1:** raw message content, identity claims, doctrine assertions, code

#### Output
```
.weslr/consolidation_digest.jsonl
```

Format per record:
```json
{
  "type": "consolidation_candidate",
  "cluster_id": "uuid",
  "theme": "recurring_gap | mission_theme | evidence_pattern | preference_signal",
  "trace_count": N,
  "first_seen": "ISO8601",
  "last_seen": "ISO8601",
  "sources": ["pending_message", "mission_store", "evidence_timeline"],
  "score": {
    "frequency": N,
    "recency": "ISO8601",
    "source_diversity": N
  },
  "proposed_destination": "entity_memory | mission_store | evidence_hypothesis | archive",
  "risk_level": "low | medium",
  "provenance": ["ref1", "ref2"],
  "gate_note": "string",
  "created_at": "ISO8601",
  "operator_action_required": false
}
```

#### Behavior
- ✅ Cluster repeated themes from input traces
- ✅ Score frequency + recency + source diversity
- ✅ Classify proposed destination
- ✅ Write to consolidation_digest.jsonl only
- ✅ No promotion to entity_memory, mission_store, doctrine, or any existing store
- ✅ No deletion of any existing records
- ✅ No doctrine updates
- ✅ No entity memory writes
- ✅ Operator-visible digest output

#### Not in V1
- ❌ Promotion to entity_memory
- ❌ Promotion to mission_store
- ❌ Promotion to doctrine registry
- ❌ Automatic governance decisions
- ❌ Contradiction resolution
- ❌ Causal linking
- ❌ Outcome-backed scoring

#### Tests
- `test_consolidation_loop.py`
  - temp-dir stores (never touches `~/.weslr`)
  - collect traces from temp pending_messages
  - cluster repeated gap theme
  - score clusters
  - classify destination
  - write digest
  - no promotion side effects (verify entity_memory unchanged, mission_store unchanged)

---

## SECTION 8 — Registry Impact

### Doctrine Registry Entry

```markdown
## Consolidation Loop — Checkpoint

Status: checkpoint

Checkpoint file: weslr/docs/WESLR_CONSOLIDATION_LOOP_CHECKPOINT_V1.md

Audit file: inventory_memory_layers.md (or memory/2026-05-07-memory-layers-consolidation-audit.md)

Not accepted doctrine yet. Pending:
- V1 digest implementation
- V1 operator review
- Governance gate design confirmation
- Registry entry after V1 validation

Layers:
- Layer 1: Raw Trace Layer (existing sources)
- Layer 2: Scoped Event Layer (existing: entity_timeline, entity_memory, continuity)
- Layer 3: Consolidation Layer (MISSING — checkpoint defines design)
- Layer 4: Candidate Memory Layer (MISSING — consolidation_digest.jsonl)
- Layer 5: Governance Promotion Layer (existing: doctrine registry, mission store)
- Layer 6: Durable Memory Layer (existing: entity_memory, relationship_memory, doctrine)
- Layer 7: Retrieval/Access Layer (existing: entity_memory queries)
- Layer 8: Audit/Explanation Layer (MISSING — consolidation digest)

Next: V1 read-only consolidation digest → consolidation_digest.jsonl
```

---

## SECTION 9 — Open Questions

1. **Manual or daemon-triggered?** Should consolidation run manually on demand, or via proactive daemon on a schedule? Recommendation: manual trigger for V1 (operator invokes `weslr consolidation run`), daemon-triggered for V2.

2. **Store name?** `.weslr/consolidation_digest.jsonl` or `.weslr/consolidation_candidates.jsonl`? Recommendation: `consolidation_digest.jsonl` for V1 — the digest is operator-visible, not yet a promotion queue.

3. **Which traces are safe for V1?** Recommendation: `pending_messages` (frontier gaps only, no raw text), `mission_store` metadata (theme + status, no raw content), evidence packet metadata (type + theme + source). Explicitly exclude raw message content, identity claims, doctrine assertions.

4. **What can be auto-saved if doctrine allows?** Recommendation: V1 has zero auto-save. All candidates are digest-only. Auto-save (if any) deferred to V2 after governance review.

5. **How to handle contradictions?** V1: flag clusters with high contradiction level in score, note "contradiction detected" in gate_note. No resolution. V2: create contradiction record, require operator resolution before promotion.

6. **How to link candidates to source provenance?** Each candidate record carries a `provenance` array of source refs (message IDs, evidence packet IDs, mission IDs). Provenance chain built at cluster time, not retroactively.

7. **How to prevent memory bloat?** consolidation_digest.jsonl is append-only but bounded. Implement max_entries (default 1000) with oldest-first archival. Archival is move to `.weslr/consolidation_digest.archive.jsonl`, not deletion.

8. **How to avoid promoting low-quality research claims?** V1 writes nothing to existing stores. Research claim promotion requires evidence strength scoring + contradiction check + operator review in V2+.

9. **How to connect consolidation to mission memory and doctrine candidates?** Layer 4 candidate records with `proposed_destination: mission_store` or `proposed_destination: doctrine_candidate` appear in the digest. Operator reviews and promotes via separate governance step. Not automatic.

10. **Should consolidation digest be human-readable only or also machine-readable?** Both. `consolidation_digest.jsonl` is machine-readable (JSONL). The human-readable digest (Section 4 Phase 7) is printed to operator attention surface as plain text summary.

---

## SECTION 10 — Final Report

| Item | Status |
|------|--------|
| **File created** | `weslr/docs/WESLR_CONSOLIDATION_LOOP_CHECKPOINT_V1.md` |
| **Existing pieces summarized** | 10 files classified (source/partial/decay/timeline/entity/attention), `memory/.dreams/` identified as OpenClaw-only |
| **V1 recommendation** | Read-only consolidation digest → `.weslr/consolidation_digest.jsonl`, cluster + score + classify only, zero promotion |
| **Registry impact** | Checkpoint entry added — not accepted doctrine, pending V1 implementation + operator review |
| **Open questions** | 10 open questions documented with recommendations |
| **Runtime code changed** | None — design doc only |
| **git status** | Clean — only untracked session artifacts, no staged changes |

**Next steps (not yet authorized):**
1. Implement `weslr/consolidation_loop.py` — collect + cluster + score + classify + write digest
2. Implement `weslr/commands/consolidation_commands.py` — CLI: `consolidation run [--hours N] [--json]`
3. Write `weslr/test_consolidation_loop.py` — full test coverage, temp-dir only
4. Operator review + registry promotion from checkpoint → accepted doctrine
