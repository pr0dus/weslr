# WESLR OBSERVATION EXECUTION PLAN V1

**Version:** 1.0
**Status:** SPEC ONLY — does not affect runtime
**Date:** 2026-04-30

---

## Section 1 — Purpose

Define the exact protocol for running controlled WESLR observation sessions, now that session/timeline boundaries are defined.

This is a concrete execution protocol. It covers session structure, batch aggregation, input categories, logging, timeline construction, review timing, failure modes, and success criteria.

This does NOT:
- Implement runtime code
- Modify behavior
- Create proposals
- Infer values
- Adapt prompts
- Touch production JSONL
- Deploy
- Use git add -A / git add . / git commit -a

---

## Section 2 — Core Boundary

```
Session = bounded interaction run
Timeline = ordered cross-run evidence record

Session produces events.
Timeline orders events.
Review operates on timeline-backed evidence.

No prompt adaptation from either session or timeline.
```

**Session** — a bounded, isolated interaction window. Generates local signal observations. No cross-session memory.

**Timeline** — an ordered record of events spanning multiple sessions. Used for provenance, stability assessment, and operator review.

**Review** — operates only on timeline-backed evidence. Never touches session-internal state directly.

**Prompt adaptation** — explicitly forbidden. Public prompts must not be modified based on session or timeline data, per WESLR_TIMELINE_SESSION_BOUNDARY_V1.

---

## Section 3 — Environment Requirements

| Requirement | Specification |
|-------------|---------------|
| Device | Isolated hardware or VM — separate from production host |
| Workspace | Independent directory; no shared state with production |
| Logs | Local only; written to observation-specific storage, not production paths |
| State | No shared production state (proposal_trace.jsonl, state_checkpoint.json, etc.) |
| Network | Air-gapped or controlled access only; no public access |
| Reset | Resettable to clean baseline without physical hardware replacement |

Isolation guarantees (from WESLR_CONTROLLED_OBSERVATION_ENVIRONMENT_V1):
- IG1: No shared filesystem
- IG2: No network to production
- IG3: No shared credentials
- IG4: No cross-instance state linking
- IG5: Resettable to clean state via snapshot or image restore

---

## Section 4 — Session Structure

### Session ID Format

```
session_<YYYYMMDD>_<NNN>  (e.g., session_20260430_001)
```

- Date part reflects observation batch start date
- Sequential number per batch, reset per batch

### Session Anatomy

```
1. Reset environment to clean baseline
2. Generate unique session_id
3. Run scripted conversation sequence (10–20 interactions)
4. Log all signal outputs as raw observations
5. End session — no state carried forward
6. Reset before next session
```

### Constraints

- One scripted conversation sequence per session
- No cross-session memory
- No mid-session interpretation or aggregation
- No prompt adaptation during session

---

## Section 5 — Observation Batch

### Batch Definition

- Minimum 3 sessions per batch
- Each batch creates one timeline segment
- Aggregation occurs only after batch completion
- No mid-session interpretation
- No mid-batch interpretation

### Batch Lifecycle

```
Batch starts
  ↓
Session 1 runs → raw signals logged
  ↓
Session 2 runs → raw signals logged
  ↓
Session 3 runs → raw signals logged
  ↓
Batch completes → timeline segment constructed
  ↓
Batch analysis → only after full aggregation
```

### Aggregation Rule

Interpretation is batch-scoped and retrospective. Signals collected during the batch are aggregated only after all sessions complete.

---

## Section 6 — Input Categories

Balanced scripted inputs are used. Scripts must include noise, neutral, and contradictory examples. Inputs must not be designed to force a specific pressure category.

### Categories

| Category | Description |
|----------|-------------|
| Neutral questions | Requests with no directional signal |
| Repeated unknown questions | Same query presented across sessions to test frequency accumulation |
| Evidence-offer triggers | Queries designed to activate evidence workspace usage (S2) |
| Conflicting requests | Opposing requests presented to test behavioral stability |
| Noisy / typo / malformed input | Malformed queries to confirm noise filters work correctly |
| Domain-shift questions | Queries moving across conceptual areas to test cross-domain consistency |
| Governance / safety probes | Edge-case queries to confirm no behavior change from observation |

### Script Design Rules

- Include noise and neutral examples to prevent forced pressure category bias
- No single category should dominate a session
- Contradictory examples must be present in at least one session per batch

---

## Section 7 — Anti-Bias Input Rule

Inputs must not be designed to force a specific pressure category.

**Required script elements per session:**
- At least 2 neutral inputs
- At least 1 noisy/malformed input
- At least 1 contradictory input (opposing direction to a prior input)
- Domain coverage across at least 2 conceptual areas

**Forbidden:**
- Scripts designed to produce a predetermined outcome
- Inputs that exclusively target a single signal type
- Inputs that suppress certain signal types by design

---

## Section 8 — Logging

### Record Per Interaction

| Field | Description |
|-------|-------------|
| `session_id` | Unique session identifier |
| `message_index` | Position in scripted sequence (1–20) |
| `input_category` | Category from Section 6 |
| `response_path` | Signal emitted or no signal |
| `signal_emitted` | true / false |
| `signal_type` | S1–S6 if emitted, null otherwise |
| `timestamp` | ISO-8601 of when interaction occurred |
| `provenance_chain_id` | Reference to full provenance chain in observation log |

### Do NOT Record

- Production state
- Private operator notes in public logs
- Raw hidden internals
- Prompt mutations
- Session-internal state that is not a logged signal

### Provenance Chain

Each logged signal must carry a `provenance_chain_id` that links back to the original observation record containing:
- Signal type and classification
- Session ID
- Timestamp
- Normalized topic (if applicable)
- Threshold status at time of observation

---

## Section 9 — Timeline Construction

After each session completes:

1. Extract all logged signals from session observation log
2. Convert signals into timeline events
3. Preserve order (timestamp ordering within session, session order across batch)
4. Attach `provenance_chain_id` to each event
5. Do NOT feed timeline back into runtime

### Timeline Event Structure

```json
{
  "event_id": "string",
  "timeline_segment_id": "string",
  "session_id": "string",
  "run_index": "integer",
  "timestamp": "ISO-8601",
  "signal_type": "S1|S2|S3|S4|S5|S6|null",
  "signal_emitted": true|false,
  "input_category": "string",
  "provenance_chain_id": "string"
}
```

### Boundary Rule

Timeline is constructed from session events only. Timeline does not feed back into session behavior. Session signals become timeline events; timeline events do not modify session state.

---

## Section 10 — Analysis Flow

After a full batch completes (all sessions run, all signals logged, timeline segment constructed):

```
raw signals
    ↓
pattern observer  (signal_pattern_observer.py)
    ↓
pattern comparison  (pattern_comparison.py)
    ↓
pressure detection  (pressure_detection.py)
    ↓
pressure aggregation  (pressure_aggregation.py)
    ↓
stability criteria assessment  (WESLR_VALUE_STABILITY_CRITERIA_V1)
    ↓
operator review  (WESLR_REVIEW_INTERFACE_V1)
    ↓
decision log  (WESLR_REVIEW_DECISION_LOG_V1)
    ↓
operator consistency side-check  (WESLR_OPERATOR_CONSISTENCY_LAYER_V1)
```

Each step is sequential and deterministic. No step reads output from a later step. No step modifies input from an earlier step.

---

## Section 11 — Review Timing

| Phase | Review Permitted? |
|-------|-------------------|
| During session | No |
| During batch (mid-batch) | No |
| After batch aggregation | Yes |

- Review occurs only after full batch aggregation completes
- No behavior change occurs during review
- No behavior change occurs after review (review is read-only)

---

## Section 12 — Failure Modes

### Failure: No Patterns Emerge

**Condition:** Batch completes, signals logged, but no pattern passes pattern observer grouping threshold.

**Response:** Log as `no_pattern_result`. Valid outcome. Record batch as completed with no pattern detected.

### Failure: Too Much Noise

**Condition:** >50% of inputs produce no meaningful signal (noise-only baseline exceeds threshold).

**Response:** Evaluate script design. Review if noise inputs are properly calibrated. Batch may be valid if signal inputs produced consistent results; invalid if all inputs are noise.

### Failure: Patterns Caused by Scripted Bias

**Condition:** Detected patterns match scripted input distribution rather than organic behavioral signals.

**Response:** Flag as `script_contaminated`. Batch invalid. Re-run with corrected script design. Reference anti-bias input rule (Section 7).

### Failure: Reset Contamination

**Condition:** Cross-session state linkage detected (IG1–IG5 violation in WESLR_CONTROLLED_OBSERVATION_ENVIRONMENT_V1).

**Response:** Reset environment immediately. Discard current batch. Investigate isolation failure before resuming.

### Failure: Missing Provenance

**Condition:** Any signal event lacks valid `provenance_chain_id` or source signal reference.

**Response:** Batch is invalid. Provenance completeness is a hard constraint. Discard and re-observe.

### Failure: Operator Inconsistency

**Condition:** Operator decisions across multiple patterns show high inconsistency rate per WESLR_OPERATOR_CONSISTENCY_LAYER_V1 checks.

**Response:** Surface diagnostic report to operator. Do not suppress or auto-correct. Operator reviews and adjusts manually.

---

## Section 13 — Success Criteria

A valid observation batch must show all of the following:

| Criterion | Requirement |
|-----------|-------------|
| Session isolation | Each session runs with clean reset; no cross-session state |
| Timeline ordering | Events ordered correctly by timestamp and session sequence |
| Provenance complete | Every signal event has a traceable provenance_chain_id |
| No prompt adaptation | No public prompt modified from session or timeline data |
| No behavior change | Zero behavior modifications triggered by signal observation |
| Measurable pattern OR no-pattern result | At least one pattern detected OR batch correctly logged as `no_pattern_result` |

The final criterion allows for a valid "nothing found" result. This is a valid outcome, not a failure.

---

## Section 14 — Hard Constraints

These constraints are non-negotiable:

| # | Constraint |
|---|------------|
| HC1 | No value inference — signals are observations, not values |
| HC2 | No proposals — observation does not create system proposals |
| HC3 | No production writes — observation logs never touch production state |
| HC4 | No LLM interpretation of signals — signal classification is deterministic, not LLM-assisted |
| HC5 | No prompt adaptation — public prompts unchanged regardless of observation findings |
| HC6 | No public exposure — public output remains natural regardless of internal observation state |
| HC7 | No mid-batch review — review occurs only after batch completion |
| HC8 | No behavior change from review — review is read-only |

---

## Section 15 — Verdict

```
WESLR_OBSERVATION_EXECUTION_PLAN_DEFINED
```

This document defines the end-to-end execution protocol for controlled WESLR observation sessions:
- Session produces events; timeline orders them; review operates on timeline
- Sessions are isolated, resettable, and bounded
- Batches consist of minimum 3 sessions; aggregation is retrospective only
- Input scripts must be balanced and anti-biased
- Logging captures provenance_chain_id for every signal event
- No prompt adaptation from session or timeline data
- Review occurs only after batch completion
- Valid batch requires: isolation, correct ordering, provenance, no adaptation, no behavior change, measurable result (pattern or no-pattern)

Validation (run independently):
```
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
```

Commit exact file only:
```
git add weslr/docs/WESLR_OBSERVATION_EXECUTION_PLAN_V1.md
git diff --cached --name-status
git commit -m "WESLR: define observation execution plan v1"
git push origin main
```

---

*Spec version 1.0 — does not affect runtime behavior*