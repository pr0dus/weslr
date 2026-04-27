# WESLR Write Handler Protocol V1
**Generated:** 2026-04-27 20:03 GMT+2
**Scope:** Design document — DESIGN ONLY, no production changes

---

## 1. Current Write Path

### ISS_controlled_proposal_intake Flow

**Triggers:**
```
"convert iss suggestion "
"convert iss gap "
"create proposal from iss "
"turn iss gap "
```

**Normalization:**
- Strip trigger prefix → raw gap ID
- If `raw.startswith("gap.")` → `requested_gap_id = raw`, `proposal_id = raw[4:].strip()`
- Otherwise → `proposal_id = raw`, `requested_gap_id = "gap." + raw`

**Validation (pre-write):**
- Gap must exist in `load_iss_diagnostics(50)` as `type == "iss_gap_signal"`
- Match by `gap_id == requested_gap_id` OR `gap_id.endswith(proposal_id)`

**Write:**
```
record_proposal(proposal_id, {
    "summary": matched.get("summary", ""),
    "source": "ISS",
    "source_gap_id": matched.get("gap_id", ""),
    "severity": matched.get("severity", "medium"),
    "confidence": matched.get("confidence", "medium"),
    "suggested": True,
    "operator_requested_intake": True,
})
```

**JSONL file written:** `weslr/proposal_trace.jsonl`
**Fields written:** `type`, `proposal_id`, `content`, `timestamp`
**Validators invoked:** `_validate_proposal_created()` in `proposal_traceability.py`

**Output payload:**
```python
{
    "message": message,
    "response_text": "ISS suggestion '{proposal_id}' was converted...",
    "path": "ISS_controlled_proposal_intake",
    "_weslr_deterministic": True,
    "confidence": "high",
    "intake_result": {
        "created": True,
        "proposal_id": proposal_id,
        "source_gap_id": matched.get("gap_id", ""),
        "approval_status": "not_approved",
        "plan_created": False,
        "execution_allowed": False,
    },
}
```

### Validators Already Enforced

| Function | File | Enforced |
|---------|------|----------|
| `_validate_proposal_created` | `proposal_traceability.py` | proposal_id non-empty string, content is dict |
| `_validate_implementation_plan` | `implementation_planning.py` | `execution_allowed must be False`, `operator_approval_required must be True` |
| `_validate_iss_diagnostic_record` | `iss/diagnostic_records.py` | type, required fields |

---

## 2. Required Guarantees

### MUST-HAVE Rules

| # | Rule | Enforcement |
|---|------|-------------|
| G1 | No silent writes | Every write must be declared in `HANDLER_REGISTRY.write_paths` |
| G2 | Schema validated before write | Each write module has `_validate_*` called before `_write_event()` |
| G3 | Append-only enforced | All write functions use `open(..., "a")` — no `r+`, no `w` |
| G4 | `execution_allowed` always `False` | `_EXECUTION_ALLOWED = False` in `implementation_planning.py`; enforced by `_validate_implementation_plan` |
| G5 | Operator intent required | `ISS_controlled_proposal_intake` only triggers on explicit operator command; `operator_requested_intake: True` recorded |
| G6 | No write during read-only queries | Registry `read_only` flag + `dispatch_deterministic_handler` guard |
| G7 | `operator_approval_required: True` | Always set by `create_implementation_plan()`; enforced by validator |
| G8 | Write paths declared upfront | Registry entry `write_paths` field enumerates every file written |

---

## 3. Registry Extension Requirements

### New Registry Fields for Write Handlers

```python
HANDLER_REGISTRY = [
    {
        "id": "...",
        # --- existing fields ---
        "read_only": True,           # False for write handlers
        "writes": [],                # DEPRECATED: use write_paths below
        # --- new fields ---
        "write_paths": [
            "weslr/proposal_trace.jsonl",
            # "weslr/implementation_plans.jsonl",
        ],
        "requires_confirmation": True,   # True for state-changing writes
        "side_effects": ["proposal_created"],  # human-readable tag(s)
        "write_guard": "record_proposal",      # function name, or None
    }
]
```

### How Registry Prevents Undeclared Writes

1. **Pre-extraction audit:** Before any handler is extracted, all its write targets are enumerated and added to `write_paths`
2. **Audit script (Gate 2):** `release_gate_v1.py` `GATE 2` already scans staged files for undeclared JSONL writes — this gate must be extended to cross-check `write_paths` against actual file opens
3. **At runtime:** Write handlers are never called from `dispatch_deterministic_handler()` without a registry entry — the dispatch only routes read-only handlers. Write handlers remain inline until the protocol is fully implemented.

### How Write Handlers Are Isolated

- Write handlers **stay inline** in `interpretation.py` until all protocol requirements are met
- When extracted, they live in `weslr/write_handlers.py` (separate from `deterministic_handlers.py`)
- Write handler module has **no imports** from `deterministic_handlers.py`
- Each write handler is a pure function: `input → validated write → action result`

---

## 4. Formatter Extension

### Current State

`build_deterministic_response()` in `weslr/response_formatter.py` returns:
```python
{
    "message": ...,
    "path": ...,
    "response_text": ...,
    "confidence": ...,
    "suggested_mode": ...,
    # ... mode_analysis, suggestion_surface ...
}
```

### Extension for Write Handlers

```python
def build_write_response(
    message: str,
    path: str,
    action_performed: str,        # e.g. "proposal_created"
    affected_ids: list[str],       # e.g. ["iss.not_integrated"]
    response_text: str,
    confidence: str = "high",
    suggested_mode: str = "observe",
    write_confirmed: bool = True,  # always True for successful writes
    extra: dict = None,
) -> dict:
    result = build_deterministic_response(
        message=message,
        path=path,
        response_text=response_text,
        confidence=confidence,
        suggested_mode=suggested_mode,
    )
    result["action_performed"] = action_performed
    result["affected_ids"] = affected_ids
    result["write_confirmed"] = write_confirmed
    if extra:
        result.update(extra)
    return result
```

### Semantic Difference

| Handler Type | Returns | Example |
|---|---|---|
| **Read handler** | `build_deterministic_response()` | `{..., "plans": [...], "iss_intake_count": 17}` |
| **Write handler** | `build_write_response()` | `{..., "action_performed": "proposal_created", "affected_ids": ["iss.not_integrated"], "write_confirmed": True}` |

The distinction is **explicit**: callers always know whether a response contains data (`read`) or a confirmed action (`write`).

---

## 5. Failure Modes

| Failure Mode | Root Cause | Prevention |
|---|---|---|
| Double writes | `record_proposal()` called twice for same trigger | Idempotency check: query trace for existing `proposal_created` with same `proposal_id` + `source_gap_id` before writing |
| Invalid schema write | `proposal_id` is empty or `content` not dict | `_validate_proposal_created()` raises `ValueError` before `_write_event()` — **already enforced** |
| Missing `proposal_id` | Normalization returns empty string | Explicit `if not raw: return {..., "reason": "missing_id"}` guard — **already enforced** |
| `execution_allowed=True` accidentally set | Developer error in plan creation | `_validate_implementation_plan()` raises if `execution_allowed is not False` — **already enforced** |
| Write triggered by wrong intent | Registry overlap or trigger collision | Trigger overlap scan before each extraction; `write_paths` must be declared before extraction |
| Append-only violated | `_write_event` uses `"w"` instead of `"a"` | Code review + gate script checks file open mode via AST analysis of staged write modules |

---

## 6. Extraction Readiness Criteria

Checklist before any write handler is extracted:

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Schema enforcement active (`_validate_*` functions exist) | ✅ Done — `proposal_traceability.py`, `implementation_planning.py` |
| 2 | Read-side validation active (`_validate_*_read` functions exist) | ✅ Done — all three modules have read validators |
| 3 | Registry supports `write_paths`, `requires_confirmation`, `side_effects`, `write_guard` fields | ❌ Not yet — requires `WRITE_HANDLER_PROTOCOL_V1.md` adoption |
| 4 | Formatter supports `build_write_response()` | ❌ Not yet — requires extension |
| 5 | Tests include write isolation checks | ❌ Not yet — requires new test cases |
| 6 | Gate script cross-checks `write_paths` against actual file operations | ❌ Not yet |
| 7 | `execution_allowed` validator fires on any `True` value | ✅ Done — `_validate_implementation_plan()` |
| 8 | Idempotency check for duplicate proposals | ❌ Not yet |
| 9 | Append-only enforced in all write modules | ⚠️ Partially — documented convention, not yet audited |

**Criteria 3–6 must be completed before any write handler extraction.**

---

## 7. Recommendation

**B) Extend registry first, then formatter**

### Reasoning

| Option | Verdict | Reason |
|--------|---------|--------|
| A) Proceed to write-handler extraction | ❌ | Registry and formatter must be ready first; extraction without protocol = undeclared writes |
| **B) Extend registry first** | ✅ | Registry is the contract — defining `write_paths`, `side_effects`, `requires_confirmation` first creates the enforcement surface for all subsequent work |
| C) Extend formatter first | ⚠️ | Formatter depends on knowing what write handlers will return; registry defines the schema |

**Sequence:**
1. **Registry** — add `write_paths`, `requires_confirmation`, `side_effects`, `write_guard` fields; add Gate 2 extension to audit `write_paths`
2. **Formatter** — add `build_write_response()` alongside `build_deterministic_response()`
3. **Idempotency** — add duplicate-proposal check to `record_proposal()`
4. **Write handler extraction** — `ISS_controlled_proposal_intake` only after all above are done

---

## 8. Validation

```
==================================================
WESLR Release Gate V1
==================================================

GATE 1: test harness passed

GATE 2: no files staged — nothing to check

GATE 3: no execution_allowed=True in production weslr/*.py

GATE 4: no OpenClaw core or TIA C# in staged scope

==================================================
WESLR_RELEASE_GATE_V1_OK
```

**No production changes made in this session.**

---

## 9. Summary

| Item | Status |
|------|--------|
| ISS_controlled_proposal_intake write path documented | ✅ |
| All validators enumerated | ✅ |
| Append-only guarantee documented | ✅ |
| Registry extension fields defined | ✅ |
| Formatter extension defined | ✅ |
| Failure modes + preventions listed | ✅ |
| Extraction readiness checklist | ✅ (3 of 9 complete) |
| Recommendation | B — Extend registry first |
| Production code modified | ❌ Design only |
