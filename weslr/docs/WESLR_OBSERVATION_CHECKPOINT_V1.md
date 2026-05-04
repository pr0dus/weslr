# WESLR Observation Checkpoint V1

**Created:** 2026-05-04
**Status:** checkpoint (not accepted doctrine)
**Registry reference:** `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`

---

## Purpose

This checkpoint records WESLR's current self-observation and improvement-preparation pipeline.

It documents current system state. It does not automatically promote the pipeline to accepted doctrine. It identifies canon candidates and open questions.

---

## Current Pipeline

The pipeline is: **observe → detect → propose → review**. Nothing in this pipeline directly mutates public behavior.

```
[Public /chat interaction]
         │
         ▼
┌─────────────────────────────┐
│  Contract Observation       │ ← appends to contract_observations.jsonl
│  (metadata only, no PII)    │   no behavior change
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Contract Insufficiency      │ ← reads observation window
│  Detector                    │   writes to contract_insufficiency_log.jsonl
│                              │   no behavior change
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Contract Improvement        │ ← reads proposal-ready insufficiency records
│  Proposal Bridge             │   appends to contract_proposal_review_log.jsonl
│                              │   no behavior change
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Review Interface /          │ ← read-only inspection surfaces
│  Workplace Review Surface    │   operator reviews pending proposals
└─────────────────────────────┘
         │
         ▼
   [Operator governance action] ← nothing happens automatically
```

No stage in this pipeline changes routing, contract definitions, or response behavior.

---

## Component Map

### 1. Contract Observation

| Property | Value |
|----------|-------|
| File | `weslr/contract_observation.py` |
| Role | Passive observer of `/chat` response contract outcomes |
| State file | `weslr/contract_observations.jsonl` (append-only) |
| Safety property | Metadata-only. `raw_prompt_stored: false`, `pii_stored: false`, `behavior_change_allowed: false` |
| Current status | Active, 310 lines |

**What it stores:** `reply_shape`, `interaction_frame`, `turn_type`, `response_path`, `signal_type`, `source`, `safe_to_record`, `session_id_hash` (hashed, not raw).

**What it excludes:** Raw prompts, user messages, PII, session tokens, LLM outputs.

### 2. Contract Insufficiency Detector

| Property | Value |
|----------|-------|
| File | `weslr/contract_insufficiency_detector.py` |
| Role | Scans observation windows for stable repeating weakness patterns |
| State file | `weslr/contract_insufficiency_log.jsonl` (append-only) |
| Safety property | Read-only from observation file. Never writes to production truth files. |
| Current status | Active, 271 lines |

**Detection logic:**
- IC1: Same contract fires ≥3 times in window
- IC4: Frame is `entry` or `unknown` AND signal is `None` or `S4`
- Pattern types: `weak_entry_repetition`, `fallback_repetition`
- `proposal_ready` flag set when all criteria met

**Thresholds (flexible detail):**
- `DEFAULT_WINDOW_SIZE = 50`
- `DEFAULT_MIN_RECORDS = 10`
- `DEFAULT_STABILITY_THRESHOLD = 3`
- `IC1_MIN_OCCURRENCES = 3`

### 3. Contract Improvement Proposal Bridge

| Property | Value |
|----------|-------|
| File | `weslr/contract_improvement_proposal_bridge.py` |
| Role | Converts proposal-ready insufficiency records → operator-reviewable proposal records |
| State file | `weslr/contract_proposal_review_log.jsonl` (append-only) |
| Safety property | PII-scanned. Deduplicates. `automatic_change: false`. Does not write to `proposal_trace.jsonl` or `implementation_plans.jsonl`. |
| Current status | Active, 299 lines |

**Proposal ID format:** `CP-{date}-{counter:03d}` (per-run, display-only)
**Deduplication key:** `(pattern_type, contract, response_path, stable_across_checks)`

### 4. Proposal Review Log

| Property | Value |
|----------|-------|
| File | `weslr/contract_proposal_review_log.jsonl` |
| Role | Append-only log of proposals awaiting operator review |
| State file | `contract_proposal_review_log.jsonl` |
| Safety property | Append-only. `proposal_status: pending_review`. No auto-approval. |
| Current status | Active, 1 record present |

### 5. Review Interface

| Property | Value |
|----------|-------|
| File | `weslr/review_interface.py` |
| Role | Read-only inspection layer for proposal review records |
| State file | Reads `contract_proposal_review_log.jsonl` |
| Safety property | Read-only. No writes. Exposes structured summary. |
| Current status | Active, 222 lines |

### 6. Workplace Review Surface

| Property | Value |
|----------|-------|
| File | `weslr/workplace_review_surface.py` |
| Role | Aggregates experiment proposals, proactive suggestions, timeline context |
| State file | Reads `experiment_proposal_store`, `user_timeline_memory` |
| Safety property | Read-only. No writes. No behavior change. |
| Current status | Active, 271 lines |

### 7. Workplace Chat Bridge

| Property | Value |
|----------|-------|
| File | `weslr/workplace_chat_bridge.py` |
| Role | Intercepts `/workplace overview` queries; returns build_workplace_text() |
| State file | None (reads other surfaces) |
| Safety property | Read-only. Authority: `read_only_workplace`. No writes. |
| Current status | Active, 201 lines |

**Note:** `_INCLUDE_GENERATED_SUGGESTIONS = True` — experiment proposal generator is hardcoded into workplace responses (operator toggle not yet available).

### 8. Public Signal Store

| Property | Value |
|----------|-------|
| File | `weslr/public_signal_store.py` |
| Role | Append-only storage for safe public signal records |
| State file | `weslr/public_signals.jsonl` |
| Safety property | Isolated from production truth. No PII. No raw prompts. No behavior change. |
| Current status | Active, 210 lines |

### 9. JSONL Archiver

| Property | Value |
|----------|-------|
| File | `weslr/jsonl_archiver.py` |
| Role | Dry-run archiver: classifies JSONL files, creates `.archive/` copies with SHA256, never deletes originals |
| State file | Creates `.archive/` directory with compressed + plaintext copies |
| Safety property | Copy-only. Never deletes. Protected files never archived. |
| Current status | Active, 230 lines |

---

## Safety Properties

| Property | Status |
|----------|--------|
| Metadata-only observation | ✅ — no raw prompt storage |
| PII exclusion | ✅ — pattern check rejects email, URL, IP, phone patterns |
| Append-only state files | ✅ — no truncate, overwrite, or delete by pipeline |
| No direct behavior mutation | ✅ — `behavior_change_allowed: false` on all records |
| No LLM for observation/detection | ✅ — deterministic pattern matching only |
| Proposal records are reviewable, not executable | ✅ — `automatic_change: false`, `pending_review` status |
| Source/state files separate from doctrine | ✅ — JSONL files are operational state, not doctrine |
| Thresholds are implementation detail | ✅ — not frozen as canon |

---

## Canon Candidates

These are **identified as candidates**, not yet accepted doctrine:

### 1. WESLR may observe its own public interaction patterns using privacy-safe metadata.

**Evidence:** `contract_observation.py` docstring + `safe_to_record: true` flag. `public_signal_store.py` separately captures anonymous operational signals.

### 2. Observation must not directly mutate public behavior.

**Evidence:** `behavior_change_allowed: false` on all observation records. Live data confirms. No module in the pipeline writes to contracts or routing.

### 3. Insufficiency detection must create proposal/review candidates, not automatic changes.

**Evidence:** `proposal_ready` flag only triggers logging to review log. `automatic_change: false` on all proposal records.

### 4. Public contract changes require governance.

**Evidence:** Proposal records are `pending_review`. No module reads review log to change contracts.

### 5. Weakness detection must be evidence-based and inspectable.

**Evidence:** Insufficiency records store `occurrence_count`, `frame_distribution`, `signal_type_distribution`, `stable_across_checks`. Observable and auditable.

### 6. Review records must preserve provenance.

**Evidence:** `contract_proposal_review_log.jsonl` records `pattern_type`, `contract`, `response_path`, `evidence_summary`, `generated_at`.

### 7. Operational state must not be confused with doctrine.

**Evidence:** JSONL files are state. Doctrine files are in `weslr/docs/`. Registry tracks the distinction.

---

## Flexible Implementation Details

The following are **not canon** and may evolve without changing doctrine:

- `DEFAULT_WINDOW_SIZE = 50` — observation window size
- `DEFAULT_STABILITY_THRESHOLD = 3` — number of stable checks required
- `DEFAULT_MIN_RECORDS = 10` — minimum observations to run detection
- IC1/IC4 criteria — exact insufficiency conditions
- `CP-{date}-{n}` — proposal ID format
- `contract_observations.jsonl` / `contract_insufficiency_log.jsonl` / `contract_proposal_review_log.jsonl` — exact filenames
- `weak_entry_repetition`, `fallback_repetition` — exact pattern type names
- Exact review record JSON schema
- Workplace text formatting and wording
- PII pattern list — extendable but operational
- JSONL archiver policy list
- Whether `_INCLUDE_GENERATED_SUGGESTIONS` is hardcoded True

---

## Open Questions

1. **What happens after a proposal is reviewed?** — `contract_proposal_review_log.jsonl` has `pending_review` records but nothing reads back to progress them. No `approved`/`rejected`/`deferred` write path exists.

2. **What operator action changes a proposal status?** — The review interface is read-only. No write path for operator decisions has been defined.

3. **Should approved proposals create implementation plans automatically?** — Would require connecting review log to `proposal_trace.jsonl` / `implementation_plans.jsonl`, which is currently a separate pipeline.

4. **Should approved proposals ever modify response contracts directly?** — Current design is explicit operator action only. If auto-change is desired, it would require a new governance surface.

5. **Should workplace suggestions require an operator toggle?** — `_INCLUDE_GENERATED_SUGGESTIONS = True` is hardcoded. No user-level control exists.

6. **How should observation records be archived long-term?** — JSONL archiver can batch-archive but no policy for when/why archives happen.

7. **What is the promotion path from checkpoint to accepted doctrine?** — Not yet defined. Observation pipeline has canon candidates but no gate for promotion.

---

## Relationship to Doctrine Registry

**Phase 9** — `accepted_doctrine`
- File: `weslr/docs/WESLR_PHASE_9_ADVANCED_REASONING_DOCTRINE_V1.md`
- Registry: `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`

**Phase 10** — `accepted_doctrine`
- File: `weslr/docs/WESLR_PHASE_10_COLLABORATION_DOCTRINE_V1.md`
- Registry: `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`

**Observation Pipeline** — `checkpoint` (this document)
- File: `weslr/docs/WESLR_OBSERVATION_CHECKPOINT_V1.md`
- Registry: `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` (updated in this task)

Phase 9 and Phase 10 are stable doctrine. The observation pipeline is checkpoint — promising architecture but not yet promoted.

---

## Non-Canon Items

Explicitly **not canon**:

- Exact thresholds (`window=50`, `stability=3`, `min_records=10`)
- Exact JSONL filenames
- Current proposal ID format (`CP-{date}-{n}`)
- Current detector pattern list (`weak_entry_repetition`, `fallback_repetition`)
- Exact JSONL schema (field names and nesting)
- Exact workplace text formatting and wording
- Exact PII pattern list
- Current test counts
- `_INCLUDE_GENERATED_SUGGESTIONS = True` behavior
- Exact archiver policy list

---

## Recommended Next Step

**C) Define proposal review lifecycle**

The most critical open question is: after an operator reviews a `pending_review` proposal, what happens? The pipeline generates review records but has no write path for outcomes. Before promoting any observation canon candidates, the review lifecycle must be defined:

- Does review produce `approved` / `rejected` / `deferred` status?
- Does approved proposal trigger an implementation plan?
- Does anything connect back to contract definitions?

This is the gap that blocks the pipeline from being doctrine — it can observe, detect, and propose, but cannot yet close the loop.

---

_Last updated: 2026-05-04_
_Status: checkpoint (not accepted doctrine)_