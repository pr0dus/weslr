# WESLR Review Decision Log V1 — Specification

**Version:** 1.0
**Status:** ACTIVE DOCTRINE — Operator Decision Traceability Specification
**Date:** 2026-04-29
**Verdict:** `WESLR_REVIEW_DECISION_LOG_DEFINED`

---

## Section 1 — Purpose

This document defines the structure and constraints of the operator review decision log — a record of every decision made during pressure pattern inspection.

The log exists for:
- **Traceability** — every operator decision is recorded with its basis and context
- **Auditability** — patterns of operator decisions can be reviewed later
- **Future governance analysis** — historical decisions inform but do not determine future governance rules

The log is a human judgment record. It does not modify system behavior. It does not trigger proposals. It does not represent system learning or value inference.

---

## Section 2 — Logged Fields

Each review decision entry must contain the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entry_id` | string | Yes | Unique identifier for this log entry (e.g. UUID) |
| `pattern_id` | string | Yes | Pattern being reviewed |
| `candidate_pressure` | string | Yes | stability / optimization / expansion / unknown |
| `persistence_score` | float | Yes | Score at time of review [0.0–1.0] |
| `run_diversity` | int | Yes | Number of runs pattern appeared in |
| `temporal_span` | float | Yes | Run index distance, first to last |
| `disposition` | string | Yes | ignore / observe further / flag for long-term tracking |
| `operator_notes` | string | Yes | Free-text operator reasoning |
| `timestamp` | ISO-8601 | Yes | When decision was made |
| `review_session_id` | string | Yes | Identifies the review session |

### Disposition Values

| Value | Meaning |
|-------|---------|
| `ignore` | Pattern determined to be noise, artifact, or not meaningful |
| `observe further` | Pattern meaningful but not yet actionable; continue observation |
| `flag for long-term tracking` | Pattern significant; requires extended monitoring |

---

## Section 3 — Required Context Snapshot

Each log entry must include a snapshot of the pattern's state at time of review — not the full raw signal history, but a reference copy sufficient to reconstruct the operator's view.

### 3.1 — Pattern Summary Snapshot

| Field | Source | Description |
|-------|--------|-------------|
| `occurrences` | `pressure_aggregation.py` | Total count at time of review |
| `run_diversity` | `pressure_aggregation.py` | Runs present |
| `temporal_span` | `pressure_aggregation.py` | Span |
| `persistence_score` | `pressure_aggregation.py` | Score at review time |
| `candidate_pressure` | `pressure_aggregation.py` | Pressure category |
| `status_evolution` | `pattern_comparison.py` | List of (run_index, status, confidence) |

### 3.2 — Status Evolution Snapshot

For each run where the pattern appeared, the snapshot must capture:

```json
[
  { "run": 0, "status": "new", "confidence": 0.63, "basis": "[NEW] S2 evidence usage strengthening..." },
  { "run": 1, "status": "strengthening", "confidence": 0.90, "basis": "S2 evidence usage strengthening..." },
  { "run": 2, "status": "stable", "confidence": 0.88, "basis": "S2 evidence usage strengthening..." }
]
```

### 3.3 — Provenance Reference

The snapshot must include a provenance reference pointing to the original signals — not a full duplication. The reference must contain:

| Field | Purpose |
|-------|---------|
| `first_signal_run` | Run index where pattern first appeared |
| `signal_types_observed` | List of signal types contributing to the pattern |
| `source_session_count` | Number of distinct sessions contributing signals |
| `provenance_chain_id` | Reference to the full provenance chain in the observation log |

The full provenance chain is stored separately in the observation log. The review log references it without duplicating it.

---

## Section 4 — Operator Reasoning

The `operator_notes` field is required and must capture the operator's reasoning at time of decision.

### Required Reasoning Elements

| Element | Description |
|---------|-------------|
| Why pattern was ignored / kept / tracked | Explicit rationale for disposition |
| Uncertainty noted | Any aspects the operator is uncertain about |
| Anomalies observed | Any unexpected characteristics in the pattern |

### Reasoning Constraints

- Reasoning is recorded as-is; it is not interpreted or synthesized by the system
- The system does not extract rules, patterns, or biases from operator reasoning
- Reasoning is for human review and future governance analysis only

---

## Section 5 — Hard Constraints

The following are non-negotiable constraints on the log:

| # | Constraint | Enforcement |
|---|-------------|-------------|
| HC1 | Append-only | Log entries are never modified after creation |
| HC2 | No retroactive editing | Past entries cannot be changed under any circumstances |
| HC3 | No effect on system behavior | Log entries do not trigger, modify, or influence WESLR behavior |
| HC4 | No automatic interpretation | System does not parse, summarize, or act on operator notes |
| HC5 | No deletion | Entries are never removed; even incorrect decisions remain |
| HC6 | Timestamps are immutable | Entry timestamp reflects actual decision time, not modification time |

A log entry records what the operator decided and why. It does not become input to any automated system process.

---

## Section 6 — Forbidden Uses

The review decision log must NOT be used for:

| # | Forbidden use | Rationale |
|---|---------------|-----------|
| FU1 | Automatic system training | Operator decisions are not training signals |
| FU2 | Value inference | Log does not contribute to value detection |
| FU3 | Proposal creation | Decisions are human judgment, not proposal triggers |
| FU4 | Biasing future detection | Past decisions do not influence future pattern evaluation |
| FU5 | Behavioral modification | Log entries do not reach the signal-to-behavior pipeline |
| FU6 | Automatic governance rules | Rules require explicit operator authorization |

The log is a record. It is not an input to any automated layer.

---

## Section 7 — Future Role

The log MAY later support the following under explicit future specification:

| Potential use | Conditions |
|---------------|------------|
| Governance rule creation | Requires explicit operator authorization; not automatic |
| Bias detection analysis | Requires separate tooling specification; operator reviews output |
| Operator consistency analysis | Human review only; no automated conclusions drawn |

These future uses require:
- Separate specification
- Operator approval
- No automatic interpretation of log contents

Nothing in this document authorizes any of these future uses. They are listed as possibilities, not permissions.

---

## Section 8 — Pipeline Position

The review decision log is written after the operator makes a disposition decision, and before any future governance action:

```
Layer 1:  Signal Collection
Layer 2:  Pattern Detection
Layer 3:  Pressure Classification
Layer 4:  Aggregation
Layer 5:  Stability Assessment
Layer 6:  Operator Review
Layer 7:  Decision Log ← This layer
Layer 8:  Future Governance Layer (not authorized)
```

The log does not feed back into the observation pipeline. It is a one-way record: review → log entry. The log is not read by any layer below Layer 7.

---

## Section 9 — Implementation Notes

A future implementation of this log might be:
- A JSONL file append-only per review session
- A structured database table with write-once constraints
- A signed log file per review session

Whatever the implementation, it must enforce the hard constraints in Section 5. The append-only nature must be architecturally enforced, not just policy-enforced.

---

## Section 10 — Verdict

**WESLR_REVIEW_DECISION_LOG_DEFINED**

This document defines the structure, constraints, and purpose of the operator review decision log — a record of human judgment in the pressure pattern review process. It is a traceability artifact, not a system input, not a training signal, and not a proposal trigger.

Core invariant: The log records decisions; it does not drive decisions. It is append-only, immutable after creation, and has no effect on system behavior.

Verification: `WESLR_REVIEW_DECISION_LOG_DEFINED`