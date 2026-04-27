# WESLR Schema Contracts — V1

**Document version:** 1.0
**Status:** canonical reference
**Created:** 2026-04-27

---

## SECTION 1 — Purpose

WESLR manages state across five JSONL data files and one static registry. No canonical schema currently formalizes the shape of records written to these files or the structure of the handler registry entries.

This document establishes explicit schema contracts:
- **What shape each record type has**
- **Which fields are required vs optional**
- **Which fields have enumerated allowed values**
- **Which rules are hard constraints vs soft guidelines**

This is documentation-only. Enforcement via validators is a future phase.

---

## SECTION 2 — Live vs Future Rule

Every schema in this document is classified as:

- **LIVE_OBSERVED** — the current code already writes/returns records in exactly this shape. The schema documents existing behavior. No drift from code is expected.
- **FUTURE_ENFORCED** — the schema defines intended shape that is not yet validated on write. Code may produce records that deviate from this shape. Enforcement planned for a later phase.

---

## SECTION 3 — proposal_created Schema

**Source:** `weslr/proposal_traceability.py` → `record_proposal()`
**Status:** LIVE_OBSERVED
**File:** `weslr/proposal_trace.jsonl`

### Record Shape

```json
{
  "type": "proposal_created",
  "proposal_id": "string",
  "content": {
    "summary": "string (optional)",
    "details": "string (optional)",
    "source": "string (optional)",
    "source_gap_id": "string (optional)",
    "severity": "string (optional)",
    "confidence": "string (optional)",
    "suggested": "string (optional)",
    "operator_requested_intake": "boolean (optional)"
  },
  "timestamp": "float (Unix epoch seconds)"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `type` | **Yes** | string | Must be `"proposal_created"` |
| `proposal_id` | **Yes** | string | Non-empty string |
| `content` | **Yes** | dict | May be empty dict `{}` |
| `timestamp` | **Yes** | float | Positive Unix timestamp |

### content Field Keys (known)

| Key | Required | Type | Notes |
|---|---|---|---|
| `summary` | No | string | Short description |
| `details` | No | string | Extended description |
| `source` | No | string | `"ISS"` when created from ISS intake |
| `source_gap_id` | No | string | Gap ID that triggered proposal creation |
| `severity` | No | string | e.g., `"medium"`, `"high"` |
| `confidence` | No | string | e.g., `"high"`, `"medium"`, `"low"` |
| `suggested` | No | string | Free text |
| `operator_requested_intake` | No | boolean | True when operator explicitly requested |

### Known Data Anomalies

- Some legacy records have `source_gap_ids: null` (array with null element) instead of absent field. This is a data cleanliness issue; not a schema violation per se but indicates inconsistent field population.
- `content` can be an empty dict `{}` — no required fields inside content.

---

## SECTION 4 — proposal_decision Schema

**Source:** `weslr/proposal_traceability.py` → `record_decision()`
**Status:** LIVE_OBSERVED
**File:** `weslr/proposal_trace.jsonl`

### Record Shape

```json
{
  "type": "proposal_decision",
  "proposal_id": "string",
  "decision": "string",
  "timestamp": "float (Unix epoch seconds)"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `type` | **Yes** | string | Must be `"proposal_decision"` |
| `proposal_id` | **Yes** | string | Non-empty string |
| `decision` | **Yes** | string | Known values: `"accepted"`, `"rejected"`, `"deferred"` |
| `timestamp` | **Yes** | float | Positive Unix timestamp |

### Decision Values (enumerated)

```
accepted | rejected | deferred
```

Other values have been observed in historical data (e.g., `"proposed"`). These are accepted as-is but not canonical for new records.

---

## SECTION 5 — implementation_plan Schema

**Source:** `weslr/implementation_planning.py` → `create_implementation_plan()`
**Status:** LIVE_OBSERVED (write), FUTURE_ENFORCED (validation not yet on write)
**File:** `weslr/implementation_plans.jsonl`

### Record Shape

```json
{
  "type": "implementation_plan",
  "plan_id": "string",
  "proposal_id": "string",
  "status": "string",
  "execution_allowed": "boolean",
  "created_at": "float (Unix epoch seconds)",
  "decision_timestamp": "float (optional)",
  "trace_reference": {
    "proposal_created": "float (nullable)",
    "proposal_decision": "float (nullable)"
  },
  "proposal_summary": "string",
  "proposal_score": "float (optional)",
  "proposal_tier": "string (optional)",
  "steps": [
    {
      "order": "integer",
      "title": "string",
      "kind": "string",
      "allowed": "boolean"
    }
  ],
  "risks": "list (empty in current phase)",
  "rollback_notes": "list (empty in current phase)",
  "operator_approval_required": "boolean"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `type` | **Yes** | string | Must be `"implementation_plan"` |
| `plan_id` | **Yes** | string | Format: `plan-{proposal_id}-{int(timestamp)}` |
| `proposal_id` | **Yes** | string | Non-empty |
| `status` | **Yes** | string | Current value: `"planned"` |
| `execution_allowed` | **Yes** | boolean | **Must be `false`** — hard rule in current phase |
| `created_at` | **Yes** | float | Positive Unix timestamp |
| `decision_timestamp` | No | float | Nullable |
| `trace_reference` | No | dict | `proposal_created` nullable, `proposal_decision` nullable |
| `proposal_summary` | **Yes** | string | From `content.summary` or `content.proposal` |
| `proposal_score` | No | float | From `content.score`, default 0.0 |
| `proposal_tier` | No | string | From `content.tier`, default `"medium"` |
| `steps` | **Yes** | list | At least one step |
| `risks` | **Yes** | list | Always `[]` in current phase |
| `rollback_notes` | **Yes** | list | Always `[]` in current phase |
| `operator_approval_required` | **Yes** | boolean | Always `true` in current phase |

### Hard Rules

1. **`execution_allowed` must be `false`** — `_EXECUTION_ALLOWED = False` is hardcoded at module level. No code path sets it to `true`. Enforcement: if a record with `execution_allowed: true` is written, it must be rejected before appending to JSONL.

2. **`plan_id` format** — `plan-{proposal_id}-{int(time.time())}`. The timestamp segment must be a valid Unix integer.

3. **`steps` must not be empty** — an empty step list indicates an incomplete plan.

---

## SECTION 6 — iss_probe_result Schema

**Source:** `weslr/iss/diagnostic_records.py` → `make_probe_result()`
**Status:** LIVE_OBSERVED
**File:** `weslr/iss/iss_diagnostic_records.jsonl`

### Record Shape

```json
{
  "type": "iss_probe_result",
  "probe_id": "string",
  "target": "string",
  "status": "string (enumerated)",
  "evidence": "dict",
  "confidence": "string",
  "timestamp": "float (Unix epoch seconds)"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `type` | **Yes** | string | Must be `"iss_probe_result"` |
| `probe_id` | **Yes** | string | Must match a probe_id in probe_registry |
| `target` | **Yes** | string | Path or identifier being probed |
| `status` | **Yes** | string | **Must be one of:** `"ok"`, `"degraded"`, `"missing"`, `"unknown"` |
| `evidence` | **Yes** | dict | May be empty `{}` |
| `confidence` | **Yes** | string | e.g., `"high"`, `"medium"`, `"low"` |
| `timestamp` | **Yes** | float | Positive Unix timestamp |

### Status Values (enumerated)

```
ok | degraded | missing | unknown
```

Any other status value raises `ValueError` at construction time — enforced by `_ALLOWED_PROBE_STATUS` guard.

---

## SECTION 7 — iss_gap_signal Schema

**Source:** `weslr/iss/diagnostic_records.py` → `make_gap_signal()`
**Status:** LIVE_OBSERVED
**File:** `weslr/iss/iss_diagnostic_records.jsonl`

### Record Shape

```json
{
  "type": "iss_gap_signal",
  "gap_id": "string",
  "source_probe_id": "string",
  "summary": "string",
  "severity": "string (enumerated)",
  "evidence": "dict",
  "confidence": "string",
  "timestamp": "float (Unix epoch seconds)"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `type` | **Yes** | string | Must be `"iss_gap_signal"` |
| `gap_id` | **Yes** | string | Format: `gap.{source}.{descriptor}` |
| `source_probe_id` | **Yes** | string | Probe that generated this gap signal |
| `summary` | **Yes** | string | Human-readable gap description |
| `severity` | **Yes** | string | **Must be one of:** `"low"`, `"medium"`, `"high"` |
| `evidence` | **Yes** | dict | May be empty `{}` |
| `confidence` | **Yes** | string | e.g., `"high"`, `"medium"`, `"low"` |
| `timestamp` | **Yes** | float | Positive Unix timestamp |

### Severity Values (enumerated)

```
low | medium | high
```

Any other severity value raises `ValueError` at construction time — enforced by `_ALLOWED_GAP_SEVERITY` guard.

---

## SECTION 8 — probe_definition Schema

**Source:** `weslr/iss/probe_registry.py` → `get_probe_registry()`
**Status:** LIVE_OBSERVED
**File:** in-memory registry (no JSONL)

### Record Shape

```json
{
  "probe_id": "string",
  "target": "string",
  "category": "string",
  "status": "string",
  "execution_allowed": "boolean",
  "description": "string"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `probe_id` | **Yes** | string | Dot-namespaced: `probe.{category}.{descriptor}` |
| `target` | **Yes** | string | File path or logical target |
| `category` | **Yes** | string | Routing category for the probe |
| `status` | **Yes** | string | Current value: `"defined"` |
| `execution_allowed` | **Yes** | boolean | **Must be `false`** — hard rule |
| `description` | **Yes** | string | Human-readable purpose statement |

### Hard Rule

**`execution_allowed` must be `false`** for every probe in the registry. All probes are declarative stubs. No probe in the registry may have `execution_allowed: true`.

### Registry Entries (current)

```
probe.front_door.chat     — routing category
probe.trace.proposals    — traceability category
probe.plans.non_executing — planning category
probe.iss.diagnostics   — diagnostics category
```

---

## SECTION 9 — probe_plan Schema

**Source:** `weslr/iss/probe_planning.py` → `create_probe_plan()`
**Status:** LIVE_OBSERVED
**File:** in-memory only (returned as payload, not persisted)

### Record Shape

```json
{
  "type": "probe_plan",
  "probe_id": "string",
  "target": "string",
  "steps": ["string"],
  "execution_allowed": "boolean",
  "operator_approval_required": "boolean"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `type` | **Yes** | string | Must be `"probe_plan"` |
| `probe_id` | **Yes** | string | From source probe definition |
| `target` | **Yes** | string | From source probe definition |
| `steps` | **Yes** | list of strings | Always 4 steps: locate, validate, inspect, report |
| `execution_allowed` | **Yes** | boolean | Always `false` |
| `operator_approval_required` | **Yes** | boolean | Always `true` |

---

## SECTION 10 — simulated_probe_execution Schema

**Source:** `weslr/iss/probe_execution.py` → `execute_probe_simulated()`
**Status:** LIVE_OBSERVED
**File:** writes to `iss_diagnostic_records.jsonl` (produces `iss_probe_result` records)

### Return Shape

```json
{
  "type": "iss_probe_result",
  "probe_id": "string",
  "target": "string",
  "status": "ok",
  "evidence": {
    "mode": "simulated",
    "probe_id": "string",
    "note": "No real commands, filesystem inspection, or network access were performed."
  },
  "confidence": "medium",
  "timestamp": "float (Unix epoch seconds)"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `type` | **Yes** | string | Always `"iss_probe_result"` |
| `probe_id` | **Yes** | string | From source probe |
| `target` | **Yes** | string | From source probe |
| `status` | **Yes** | string | Always `"ok"` in simulated execution |
| `evidence` | **Yes** | dict | Always contains `mode: "simulated"` |
| `confidence` | **Yes** | string | Always `"medium"` in simulated execution |
| `timestamp` | **Yes** | float | Positive Unix timestamp |

### Hard Rule

**Simulated execution never performs real I/O.** `execute_probe_simulated` must not call subprocess, os.system, pathlib inspection of actual files, or network access. This is architecturally enforced.

---

## SECTION 11 — deterministic_handler_registry_entry Schema

**Source:** `weslr/deterministic_handlers.py`
**Status:** LIVE_OBSERVED
**File:** `weslr/deterministic_handlers.py` (in-memory registry)

### Record Shape

```json
{
  "id": "string",
  "path": "string",
  "triggers": ["string"],
  "match_type": "string",
  "priority": "integer",
  "handler_fn": "string",
  "read_only": "boolean",
  "writes": ["string"],
  "requires_confirmation": "boolean",
  "category": "string"
}
```

### Field Rules

| Field | Required | Type | Rule |
|---|---|---|---|
| `id` | **Yes** | string | Globally unique identifier |
| `path` | **Yes** | string | Matches response contract path label |
| `triggers` | **Yes** | list of strings | Non-empty list of prefix strings |
| `match_type` | **Yes** | string | Current value: `"prefix"` only |
| `priority` | **Yes** | integer | 1–100, higher = evaluated first |
| `handler_fn` | **Yes** | string | Name of handler function in same module |
| `read_only` | **Yes** | boolean | `true` for read-only handlers |
| `writes` | **Yes** | list of strings | Empty list `[]` if read_only=true |
| `requires_confirmation` | **Yes** | boolean | `false` unless confirmation-gated |
| `category` | **Yes** | string | e.g., `"iss"`, `"plan"`, `"proposal"` |

### Priority Guidelines

| Range | Use |
|---|---|
| 90–100 | Exact match handlers |
| 70–89 | Specific prefixes without overlap risk |
| 50–69 | Generic prefixes with known overlap |
| 10–49 | Low-priority fallback handlers |

### Registry Entries (current)

```
[priority 85] iss_probe_plan          — iss category
[priority 80] iss_probe_registry_query — iss category
```

---

## SECTION 12 — Append-Only JSONL Rules

All WESLR JSONL files are **append-only logs**. The following rules apply permanently:

### Core Rules

1. **No rewriting** — once a line is written, it is never modified or deleted.
2. **No deletion** — no line is ever removed from a JSONL file.
3. **No truncation** — files grow indefinitely; `load_*` functions use `limit` to read only the last N lines.

### Malformed Line Future Handling

**Current behavior:** `load_trace()`, `load_implementation_plans()`, and `load_iss_diagnostics()` read lines and call `json.loads()` directly. A single malformed line crashes the entire load.

**Future enforcement (Phase 2):** Line-level error isolation:
```python
records = []
for i, line in enumerate(lines):
    try:
        records.append(json.loads(line))
    except json.JSONDecodeError:
        continue  # skip malformed line, log warning
return records[-limit:]
```

### Future Line-Level Isolation Rules

- A malformed line must never crash the load function.
- A malformed line must be skipped silently (not surfaced to operator).
- A warning should be logged for auditing purposes.
- Isolated malformed lines must not prevent subsequent valid lines from loading.

---

## SECTION 13 — Forbidden Schema Drift

The following are explicitly forbidden unless a governance review approves them:

### Absolute Forbiddances

1. **Missing `type` field** — every JSONL record must have a `type` field. Records without `type` are malformed and must not be written.

2. **`execution_allowed: true` without governance** — no record may have `execution_allowed: true` until a formal operator approval workflow exists. This is a hard system rule.

3. **Unregistered write handlers** — any handler that writes to a JSONL file must be declared in `HANDLER_REGISTRY` with `read_only: false` and `writes: [filename]`. Undeclared writes are forbidden.

4. **Silent mutation of `_CAPABILITIES`** — `_CAPABILITIES` is read-only at runtime. Any code that attempts to mutate it outside of explicit update workflows must raise an error.

5. **Hidden learning fields** — fields that represent learned or inferred state must not appear in response payloads without being labeled as such. The operator must always know what is static vs. inferred.

6. **`confidence` field without type context** — `confidence` may not appear in a response without it being clear whether it represents handler-match confidence, factual-read confidence, or recommendation confidence. (This is a style guide; enforcement is optional.)

---

## SECTION 14 — Future Enforcement Plan

**Phase 1 (now — documentation only):** This document. No code changes. Establishes canonical shapes.

**Phase 2 (later):** Lightweight validation helpers in each module:
```python
# Example pattern for proposal_traceability.py
def record_proposal(proposal_id: str, content: dict):
    if not proposal_id or not isinstance(proposal_id, str):
        raise ValueError(f"proposal_id must be a non-empty string, got {proposal_id!r}")
    if not isinstance(content, dict):
        raise ValueError(f"content must be a dict, got {type(content).__name__}")
    _write_event({...})
```

**Phase 3 (later):** Validate on write only — validators run at record creation time, not at read time. Read-time validation (skip-malformed-line isolation) is Phase 4.

**Phase 4 (later):** JSONL integrity isolation on read — per-line try/except so one malformed line doesn't crash the load.

**Phase 5 (later):** JSON schema files in `weslr/schemas/` — machine-readable schemas for all record types. Use `jsonschema` library for validation on write.

---

## SECTION 15 — Uncertain / Unresolved Fields

The following fields have ambiguous or partially-defined semantics:

| Field | Uncertainty |
|---|---|
| `content` in proposal_created | No required sub-fields — an empty `{}` is valid. This means proposals have no guaranteed minimum information content. |
| `confidence` in probe results | Used in both `iss_probe_result` and `iss_gap_signal` records. No enumerated set defined. Current values: `"high"`, `"medium"`, `"low"` but no enforcement. |
| `severity` in iss_gap_signal | Enumerated as low/medium/high but `make_gap_signal()` defaults to `"medium"` — no guidance on when to use which level. |
| `proposal_score` in implementation_plan | Float 0.0–1.0 but no documented scale — unclear whether 0.5 is "average" or what threshold constitutes "high priority." |
| `proposal_tier` in implementation_plan | Free string defaulting to `"medium"` but no enumerated set. |

---

*Document version: 1.0*
*Status: canonical reference*
*Next step: lightweight validation helpers in Phase 2, then JSON schema files*
