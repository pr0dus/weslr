# WESLR Review Interface V1 — Specification

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — Operator Review Surface Specification
**Date:** 2026-04-29
**Verdict:** `WESLR_REVIEW_INTERFACE_DEFINED`

---

## Section 1 — Purpose

This document defines the structured surface through which the operator inspects review-ready pressure patterns.

The review interface is not a UI implementation specification. It defines what information must be available to the operator when inspecting a stable pressure pattern, what questions the operator must answer, and what actions are permitted after inspection.

Purpose:
- Make pressure pattern history inspectable
- Provide full provenance transparency
- Ensure operator decisions are informed, not reflexive
- Preserve the separation between observation and action

This interface does not modify behavior. It does not create proposals. It does not infer values. It exists solely to give the operator a clear, structured view of what has been observed.

---

## Section 2 — Input Sources

The review surface must be constructed from the following sources, in order:

| Source | Module | Content |
|--------|--------|---------|
| `pressure_summary` | `pressure_aggregation.py` | Aggregated per-pressure stats: occurrences, run_diversity, temporal_span, persistence_score |
| `pattern_comparison` outputs | `pattern_comparison.py` | Per-pattern status evolution across runs |
| `signal_pattern_observer` outputs | `signal_pattern_observer.py` | Raw pattern groups before comparison |
| Raw signal references | `signal_pattern_observer.py` `RawSignal` records | Session IDs, timestamps, signal types, confidence scores |

The review surface must not introduce inference, synthesis, or interpretation not present in these sources.

---

## Section 3 — Display Structure

For each review-ready pressure pattern, the following must be displayed:

### 3.1 — Identity Fields

| Field | Source | Description |
|-------|--------|-------------|
| `pattern_id` | `pattern_comparison.py` | Stable pattern identifier |
| `candidate_pressure` | `pressure_aggregation.py` | stability / optimization / expansion / unknown |
| `first_seen_run` | Signal provenance | Index of first run where pattern appeared |
| `last_seen_run` | Signal provenance | Index of most recent run |

### 3.2 — Persistence Metrics

| Field | Source | Description |
|-------|--------|-------------|
| `occurrences` | `pressure_aggregation.py` | Total indicator count across all runs |
| `run_diversity` | `pressure_aggregation.py` | Number of distinct runs where pattern appears |
| `temporal_span` | `pressure_aggregation.py` | Run index distance from first to last |
| `persistence_score` | `pressure_aggregation.py` | Deterministic score [0.0–1.0] |

### 3.3 — Status Evolution

For each run where the pattern appears, the interface must show the status progression:

| Run | Status | Confidence | Basis |
|-----|--------|------------|-------|
| R0 | new | 0.63 | [NEW] S2 evidence usage strengthening... |
| R1 | strengthening | 0.90 | S2 evidence usage strengthening... |
| R2 | stable | 0.88 | S2 evidence usage strengthening... |

The status evolution must reflect the actual transitions observed, not an interpretation.

### 3.4 — Signal Provenance Chain

For each occurrence, the following must be traceable:

| Provenance element | Source | Purpose |
|--------------------|--------|---------|
| Signal type | Raw signal | S1 / S2 / S3 / S4 / S5 / S6 |
| Session ID | Raw signal | Identifies observation session |
| Timestamp | Raw signal | When signal was observed |
| Topic normalized | Raw signal | Normalized topic or null |
| Pattern group | `signal_pattern_observer.py` | Which pattern group this belongs to |
| Comparison result | `pattern_comparison.py` | Status and deltas at comparison time |
| Pressure indicator | `pressure_detection.py` | Mapping basis and adjusted confidence |

The full chain from raw signal to pressure classification must be retrievable for inspection.

### 3.5 — Source Signal References

Each pressure indicator must carry references to the underlying signals:

```
pattern_id: "abc123"
candidate_pressure: "expansion"
occurrences: 4
run_diversity: 3
persistence_score: 0.77

source_signals:
  - run: 0, signal_type: S2, pattern_id: "p1", session_id: "sess_001", confidence: 0.90
  - run: 1, signal_type: S2, pattern_id: "p3", session_id: "sess_003", confidence: 0.88
  - run: 1, signal_type: S1, pattern_id: "p5", session_id: "sess_003", confidence: 0.85
  - run: 2, signal_type: S2, pattern_id: "p7", session_id: "sess_005", confidence: 0.90
```

---

## Section 4 — Required Operator Questions

For each displayed pattern, the operator must affirmatively consider the following questions. The interface must be structured so that these questions cannot be skipped:

| # | Question | Purpose |
|---|----------|---------|
| Q1 | Is this pattern noise? | Determine if the signal is meaningful or statistical artifact |
| Q2 | Is this consistent across domains? | Check if the pattern appears across different conceptual areas or only in one |
| Q3 | Is this influenced by test input? | Confirm pattern is not a result of scripted observation sessions |
| Q4 | Is this stable across resets? | Verify pattern survives controlled environment reset cycles |
| Q5 | Is this worth continued observation? | Decide if the pattern warrants ongoing tracking or can be archived |

These questions are not pass/fail gates. They are inspection prompts. The operator answers them by examining the provenance chain and the pattern's behavior across runs.

---

## Section 5 — Forbidden Actions

The operator must NOT do any of the following when reviewing a pressure pattern:

| # | Forbidden action | Rationale |
|---|------------------|-----------|
| FA1 | Treat the pattern as a value | Values cannot be assigned from stability assessment alone |
| FA2 | Approve behavior change based on review | Behavior change requires separate governance authorization |
| FA3 | Trigger system modifications | Review interface has no write path to system state |
| FA4 | Skip further observation | A passing review does not authorize acceleration of the signal-to-behavior pipeline |
| FA5 | Declare a pressure category as dominant | Ranking is prohibited by doctrine |
| FA6 | Infer meaning from persistence score | Score indicates persistence only, not importance |

The interface is read-only. No action taken during review modifies system behavior.

---

## Section 6 — Operator Output

After reviewing a pattern, the operator may mark it with one of the following dispositions:

| Disposition | Meaning |
|-------------|---------|
| `ignore` | Pattern is determined to be noise, test artifact, or otherwise not meaningful |
| `observe further` | Pattern is meaningful but not yet ready for further action; continue observation |
| `flag for long-term tracking` | Pattern is significant enough to warrant extended monitoring and future review |

These dispositions are:
- Operator decisions, not system decisions
- Recorded for audit, not for automatic action
- Not a trigger for proposals, behavior change, or governance events

The disposition does not modify WESLR behavior. It is a label for the operator's own tracking and review history.

---

## Section 7 — Position in Pipeline

The review interface sits between the stability criteria layer and future proposal layer:

```
Layer 1:  Signal Collection
Layer 2:  Pattern Detection
Layer 3:  Pressure Classification
Layer 4:  Aggregation
Layer 5:  Stability Assessment (review-readiness)
Layer 6:  Operator Review ← This layer
Layer 7:  Proposal (future — not authorized)
Layer 8:  Behavior Change Authorization (future — not authorized)
```

The review interface does not connect directly to Layer 7. Operator review may inform the operator's decision to initiate a proposal in the future, but that future action requires separate specification and authorization.

---

## Section 8 — Implementation Notes

The review interface is a specification, not a UI specification. No frontend code is authorized by this document.

A future review surface might:
- Be a terminal-based read-only display
- Generate a structured report from pressure_aggregation output
- Produce a JSON audit log of operator decisions
- Integrate with existing WESLR operator tooling

Whatever form the review surface takes, it must:
- Be read-only (no writes to production state)
- Display full provenance for every pattern
- Present all required operator questions
- Enforce no automatic actions from operator dispositions

---

## Section 9 — Verdict

**WESLR_REVIEW_INTERFACE_DEFINED**

This document defines the structure and constraints of the operator review surface for pressure patterns that have passed stability criteria. It specifies what information is displayed, what questions the operator must consider, what actions are forbidden, and what outputs are permitted.

Core invariant: The review interface is read-only. Operator review informs human judgment; it does not trigger system actions.

Verification: `WESLR_REVIEW_INTERFACE_DEFINED`