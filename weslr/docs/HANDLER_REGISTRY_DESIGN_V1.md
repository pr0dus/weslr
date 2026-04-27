# WESLR Handler Registry Design — V1

---

## SECTION 1 — Purpose

`interpretation.py` is a 1971-line monolith. Its dispatch mechanism is implicit: a chain of `if any(lowered.startswith(t) for t in _X_triggers)` blocks, each evaluated in order. This creates three structural problems:

1. **No central visibility** — every handler is invisible to every other handler. Adding a new trigger requires searching the entire file to check for accidental shadowing.

2. **Implicit fallthrough** — if no trigger matches, the function proceeds to base turn-type assessment. There is no "not found" response for deterministic queries.

3. **Trigger-order fragility** — adding a new trigger in the wrong position can silently shadow an existing handler. `"plan "` vs `"plan probe "` is a known conflict that has survived multiple additions.

The handler registry is a design for a future `weslr/deterministic_handlers.py` module that makes dispatch explicit, order-safe, and auditable.

---

## SECTION 2 — Current Handler Inventory

All handlers in `interpretation.py` (line numbers indicate trigger definition location):

### C1 — Self Description
- **Triggers:** `"who are you"`, `"what are you"`
- **Path:** `self_description`
- **Read/Write:** read-only
- **Files read:** none (static)
- **Files written:** none
- **Shadow risk:** low — unique phrases

### C2 — Capabilities
- **Triggers:** `"what can you do"`, `"your capabilities"`, `"what are your capabilities"`, `"what can't you do"`, `"what are you missing"`, `"what are your limitations"`, `"what can you not do"`
- **Path:** `capability_list`
- **Read/Write:** read-only
- **Files read:** `_CAPABILITIES` dict (static)
- **Files written:** none
- **Shadow risk:** low — specific phrases

### C3 — Capability Gaps
- **Triggers:** `"how can you improve"`, `"what could be added"`, `"what are possible improvements"`, `"can you add intelligence layers"`, `"how can you become better"`
- **Path:** `capability_gaps`
- **Read/Write:** read-only
- **Files read:** `_CAPABILITIES`, `operator_feedback_log.jsonl`
- **Files written:** none
- **Shadow risk:** low

### C4/C5 — Proposal Creation / Prioritization
- **Triggers:** `"make proposal"`, `"create proposal"`, `"suggest"`, etc. (via `rank_capability_proposals`)
- **Path:** `capability_proposal_ranked`
- **Read/Write:** write (via `create_implementation_plan`, `record_implementation_plan`)
- **Files read:** `proposal_trace.jsonl`, `operator_feedback_log.jsonl`
- **Files written:** `implementation_plans.jsonl`
- **Shadow risk:** medium — overlaps with generic "plan" trigger

### C6 — Proposal Approval / Rejection
- **Triggers:** `"accept proposal "`, `"reject proposal "`, `"modify proposal "`, `"defer proposal "`
- **Path:** `operator_feedback_decision`
- **Read/Write:** write (via `record_decision`)
- **Files read:** `proposal_trace.jsonl`
- **Files written:** `proposal_trace.jsonl`
- **Shadow risk:** medium — overlapping `proposal_id` parsing with C4/C5

### C8Q — Plan Query
- **Triggers:** `"show plan"`, `"show plans"`, `"list plans"`, `"plan status"`, `"what plans exist"`
- **Path:** `C8_plan_query_single`
- **Read/Write:** read-only
- **Files read:** `implementation_plans.jsonl`, `proposal_trace.jsonl`
- **Files written:** none
- **Shadow risk:** high — `"plan "` is very generic, overlaps with `"plan probe "` (priority conflict)

### ISSQ — Diagnostics Query
- **Triggers:** `"show diagnostics"`, `"show iss diagnostics"`, `"list diagnostics"`
- **Path:** `ISS_query_gaps`
- **Read/Write:** read-only
- **Files read:** `iss_diagnostic_records.jsonl`
- **Files written:** none
- **Shadow risk:** low

### Operator Overview
- **Triggers:** `"show system overview"`, `"show system status"`, `"system status"`, `"operator overview"`
- **Path:** `operator_overview`
- **Read/Write:** read-only
- **Files read:** `iss_diagnostic_records.jsonl`
- **Files written:** none
- **Shadow risk:** low

### State Checkpoint
- **Triggers:** `"checkpoint"`, `"arch status"`, `"show layers"`, `"architecture status"`, `"show architecture"`
- **Path:** `state_checkpoint_query`
- **Read/Write:** read-only
- **Files read:** `state_checkpoint.py` (static)
- **Files written:** none
- **Shadow risk:** low

### Proposal Explanation
- **Triggers:** `"why is "`, `"explain proposal "`, `"why prioritize "`
- **Path:** `proposal_explanation`
- **Read/Write:** read-only
- **Files read:** `proposal_trace.jsonl`, `implementation_plans.jsonl`
- **Files written:** none
- **Shadow risk:** low

### Plan Explanation
- **Triggers:** `"why does plan "`, `"explain plan "`, `"why was plan "`
- **Path:** `plan_explanation`
- **Read/Write:** read-only
- **Files read:** `proposal_trace.jsonl`, `implementation_plans.jsonl`, `iss_diagnostic_records.jsonl`
- **Files written:** none
- **Shadow risk:** medium — `"why does "` could theoretically overlap with a future `"why does proposal "` if added carelessly

### ISS Intake Conversion
- **Triggers:** `"accept gap "`, `"convert gap "`, `"create proposal from gap "`
- **Path:** `ISS_controlled_proposal_intake`
- **Read/Write:** write (via `record_proposal`, `record_implementation_plan`)
- **Files read:** `iss_diagnostic_records.jsonl`
- **Files written:** `proposal_trace.jsonl`, `implementation_plans.jsonl`
- **Shadow risk:** low

### ISS Intake Query
- **Triggers:** `"show iss gaps"`, `"show gaps"`, `"list iss gaps"`, `"iss status"`, `"what iss gaps"`
- **Path:** `ISS_intake_query`
- **Read/Write:** read-only
- **Files read:** `iss_diagnostic_records.jsonl`
- **Files written:** none
- **Shadow risk:** low — `"show gaps"` shared with `show diagnostics` but handled separately

### ISS Probe Registry Query
- **Triggers:** `"show iss probes"`, `"show probe registry"`, `"list probes"`, `"what can iss check"`
- **Path:** `ISS_probe_registry_query`
- **Read/Write:** read-only
- **Files read:** none (from `get_probe_registry()`)
- **Files written:** none
- **Shadow risk:** very low — unique trigger prefixes

### ISS Probe Planning
- **Triggers:** `"plan probe "`, `"how would you check "`
- **Path:** `ISS_probe_plan`
- **Read/Write:** read-only
- **Files read:** `get_probe_registry()` (static)
- **Files written:** none
- **Shadow risk:** high — `"plan "` is prefix of `"plan probe "`, so generic `"plan "` handler must be evaluated AFTER `"plan probe "` (current order: 1704 before 1022 is correct)

### ISS Probe Execution
- **Triggers:** `"execute probe "`
- **Path:** `ISS_probe_execution`
- **Read/Write:** write (via `execute_probe_simulated` → appends to `iss_diagnostic_records.jsonl`)
- **Files read:** `get_probe_registry()`
- **Files written:** `iss_diagnostic_records.jsonl` (1 record per confirmed execution)
- **Shadow risk:** medium — `"execute"` could overlap with a future `"explain execution"` or similar

### Shadow Risk Summary

| Handler | Shadow Risk | Cause |
|---|---|---|
| `ISS_probe_plan` | **HIGH** | `"plan "` prefix of `"plan probe "` |
| `C8_plan_query_single` | **HIGH** | `"plan "` overlaps with `"plan probe "` |
| `ISS_probe_execution` | **MEDIUM** | `"execute "` generic |
| `proposal_explanation` | **MEDIUM** | `"why "` generic could overlap |
| All others | **LOW** | Specific enough |

---

## SECTION 3 — Registry Shape

Each handler entry is a dict:

```python
{
    "id": "iss_probe_registry_query",        # unique identifier
    "path": "ISS_probe_registry_query",      # deterministic path (matches response contract)
    "triggers": [                             # list of trigger strings
        "show iss probes",
        "show probe registry",
        "list probes",
        "what can iss check",
    ],
    "match_type": "prefix",                  # how to match: "prefix" | "exact" | "contains"
    "priority": 50,                          # higher = evaluated first; 1-100
    "handler_fn": "handle_iss_probe_registry",  # name of handler function in deterministic_handlers.py
    "read_only": True,                       # True = no file writes
    "writes": [],                            # list of files written (empty if read_only)
    "requires_confirmation": False,          # True = block until confirmed
    "category": "iss",                       # core | proposal | plan | iss | operator | explanation
}
```

**Priority guidelines:**
- 90-100: exact matches (e.g., `"accept proposal "`)
- 70-89: specific prefixes with no overlap risk (e.g., `"plan probe "`)
- 50-69: generic prefixes with known overlap (e.g., `"plan "`)
- 10-49: low-priority fallback handlers

**Registry as a list sorted by priority descending.** Dispatch walks the list in order and returns the first matching handler.

---

## SECTION 4 — Ordering Rules

1. **Exact matches before prefix matches** — `"show iss probes"` (exact) before `"show"` (prefix)

2. **Specific prefix before generic prefix** — `"plan probe "` (priority 85) before `"plan "` (priority 50) before `"show"` (priority 30)

3. **Write handlers after read-only** — unless operator explicitly commands a write, read-only handlers take precedence. This prevents accidental writes when a query string happens to contain a write trigger.

4. **`"execute probe "` before explanation handlers** — `"execute probe why is X"` must match execution first, not explanation of proposal X.

5. **`"plan probe "` before generic `"plan "`** — known ordering constraint, must be enforced by priority values.

6. **No handler may be skipped** — if a trigger matches multiple handlers by priority error, the registry must either reject the duplicate or surface a conflict at import time, not silently pick one.

---

## SECTION 5 — Safety Rules

1. **Every handler must declare `read_only` and `writes`** — the registry enforces that no handler may write a file it does not declare. If `read_only=False` and `writes=[]`, this is a validation error at import time.

2. **All deterministic handlers must set `_weslr_deterministic=True`** — enforced by the formatter wrapper, not by individual handlers.

3. **`requires_confirmation=True` handlers block without operator confirmation** — they return a confirmation-gate response, never auto-proceed.

4. **No handler may modify `_CAPABILITIES`** — `_CAPABILITIES` is read-only data. Any handler that attempts to mutate it raises a `RegistrySecurityError` at runtime.

5. **`_CAPABILITIES` staleness check** — on import, `weslr/deterministic_handlers.py` should log a warning if `ISS: False` in `_CAPABILITIES` but `iss_probe_registry` handler exists (indicating the capability map is stale, not that the handler is wrong).

6. **Handler ID uniqueness** — duplicates are a build-time error, not a runtime warning.

7. **No silent fallback** — if no handler matches, the dispatcher must return a structured "no handler found" response with a path like `no_handler_match` rather than falling through invisibly.

---

## SECTION 6 — First Extraction Candidate

**Recommended first extraction: `ISS_probe_registry_query`**

Rationale:
- Already migrated to `response_formatter` (confirmed working)
- Fully read-only — no write declarations needed
- Simple payload — only `probe_registry` and `probe_count`
- Triggers are unique — no overlap risk
- No conditionals in response construction
- Handler function is ~10 lines

**Second extraction candidate: `ISS_probe_plan`**

Rationale:
- Also migrated to `response_formatter`
- Two branches (found / not found) but both use the same formatter call
- Still fully read-only
- Triggers include `"plan probe "` which has a known priority conflict — the registry enforces priority, not the inline handler ordering

**Do not extract further until the first two are validated with the full test matrix.**

---

## SECTION 7 — Migration Plan

**Step 1: Create `weslr/deterministic_handlers.py`**

```python
from weslr.response_formatter import build_deterministic_response
from weslr.iss.probe_registry import get_probe_registry

HANDLER_REGISTRY = []  # sorted by priority desc

def handle_iss_probe_registry(message: str, lowered: str) -> dict:
    probes = get_probe_registry()
    return build_deterministic_response(
        message=message,
        path="ISS_probe_registry_query",
        response_text="ISS has " + str(len(probes)) + " defined probe stubs. Execution allowed: False for all.",
        payload={"probe_registry": probes, "probe_count": len(probes)},
        confidence="high",
        suggested_mode="observe",
    )

# Register it
HANDLER_REGISTRY.append({
    "id": "iss_probe_registry_query",
    "path": "ISS_probe_registry_query",
    "triggers": ["show iss probes", "show probe registry", "list probes", "what can iss check"],
    "match_type": "prefix",
    "priority": 80,
    "handler_fn": "handle_iss_probe_registry",
    "read_only": True,
    "writes": [],
    "requires_confirmation": False,
    "category": "iss",
})
```

**Step 2: Create dispatcher function**

```python
def dispatch(message: str, lowered: str) -> dict:
    for entry in HANDLER_REGISTRY:
        for trigger in entry["triggers"]:
            if entry["match_type"] == "prefix" and lowered.startswith(trigger):
                fn = globals()[entry["handler_fn"]]
                return fn(message, lowered)
            elif entry["match_type"] == "exact" and lowered == trigger:
                fn = globals()[entry["handler_fn"]]
                return fn(message, lowered)
    return {"message": message, "response_text": "No handler matched.", "path": "no_handler_match", "_weslr_deterministic": True, "confidence": "low"}
```

**Step 3: Run existing tests — confirm output identical before committing to extraction**

**Step 4: After ISS probe registry and plan are extracted and tested, stop and rescan** — evaluate whether the remaining handlers need extraction or if the registry is sufficient as design documentation.

---

## SECTION 8 — Test Matrix

Required test inputs for all handlers before and after extraction:

| Handler | Path | Test Inputs |
|---|---|---|
| C1 self-description | `self_description` | "who are you", "what are you" |
| C2 capabilities | `capability_list` | "what can you do", "what can't you do" |
| C3 capability gaps | `capability_gaps` | "how can you improve", "what could be added" |
| C4/C5 proposals | `capability_proposal_ranked` | "make proposal fix routing", "create proposal for X" |
| C6 approval/reject | `operator_feedback_decision` | "accept proposal X", "reject proposal Y" |
| C8Q plan query | `C8_plan_query_single` | "show plans", "list plans", "plan status" |
| ISSQ diagnostics | `ISS_query_gaps` | "show diagnostics", "show iss diagnostics" |
| operator overview | `operator_overview` | "show system overview", "system status" |
| state checkpoint | `state_checkpoint_query` | "checkpoint", "arch status", "show layers" |
| proposal explanation | `proposal_explanation` | "why is proposal X", "explain proposal Y" |
| plan explanation | `plan_explanation` | "why does plan Z exist", "explain plan plan.X" |
| ISS intake conversion | `ISS_controlled_proposal_intake` | "accept gap gap.X", "convert gap gap.Y" |
| ISS intake query | `ISS_intake_query` | "show iss gaps", "show gaps", "iss status" |
| ISS probe registry | `ISS_probe_registry_query` | "show iss probes", "show probe registry", "list probes", "what can iss check" |
| ISS probe planning | `ISS_probe_plan` | "plan probe probe.front_door.chat", "how would you check probe.X", "plan probe unknown" |
| ISS probe execution | `ISS_probe_execution` | "execute probe X", "execute probe X confirm" |
| No handler match | `no_handler_match` | "tell me about solar panels", "random unrelated input" |

**For each test:** compare `path`, `_weslr_deterministic`, `confidence`, `response_text`, and relevant payload fields before and after extraction. Must be byte-identical.

---

## SECTION 9 — Non-Goals

The registry is **not**:
- A full rewrite of `interpretation.py`
- A plugin/extension system with dynamic loading
- A replacement for the core turn-type assessment
- A mechanism for adding real probe execution
- A way to change response text or behavior
- A migration of all handlers at once

The registry is a **dispatch refactor only** — making trigger ordering explicit, auditable, and conflict-checkable without changing what any handler does.

---

## SECTION 10 — Verdict

**HANDLER_REGISTRY_DESIGN_CONFIRMED**

Design solidifies:
- Priority-based sorted registry with explicit `match_type`
- Safety rules enforced at import time (no silent writes, no `_CAPABILITIES` mutation)
- First extraction: `ISS_probe_registry_query` → `ISS_probe_plan` → stop and rescan
- No handler reordering until tests confirm identical output
- Test matrix covers all 18 handler paths including no-match case

---

*Document version: 1.0*
*Design status: canonical reference*
*Next step: create weslr/deterministic_handlers.py skeleton after RESPONSE_FORMATTER_V1 confirmed*