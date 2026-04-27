# ADR-0004: Handler Registry and Response Formatter

**Status:** Accepted
**Date:** 2026-04-27
**Deciders:** pr0dus (operator)

---

## Context

`interpretation.py` is a 1927-line monolith containing all deterministic query handlers, turn-type assessment, capability scoring, feedback logging, and interest tracking. The dispatch mechanism is implicit: a chain of `if any(lowered.startswith(t) for t in _X_triggers)` blocks evaluated in relative line order. This creates three structural problems:

1. **No central visibility** — every handler is invisible to every other handler. Adding a new trigger requires searching the entire file to check for accidental shadowing.

2. **Trigger-order fragility** — the `"plan probe "` vs `"plan "` conflict is a known example. Adding a new trigger in the wrong position can silently shadow an existing handler without any error or warning.

3. **Response field inconsistency** — each handler builds its own response dict. Some handlers use `build_deterministic_response`, others build directly. Fields like `_weslr_deterministic`, `confidence`, `suggested_mode`, `mode_analysis`, `mode_suggestion`, and `suggestion_surface` are applied inconsistently.

---

## Decision

**Extract deterministic query handlers into a registry and standardize all handler responses through a single formatter function.**

### Handler Registry

A registry module (`weslr/deterministic_handlers.py`) contains:
- `HANDLER_REGISTRY` — a list of handler entry dicts
- Each entry declares: `id`, `path`, `triggers`, `match_type`, `priority`, `handler_fn`, `read_only`, `writes`, `requires_confirmation`, `category`
- `dispatch_deterministic_handler(message, lowered)` sorts entries by priority descending and returns the first matching handler's result

Priority ordering rules:
- Exact matches before prefix matches
- Specific prefix before generic prefix
- Write handlers after read-only handlers
- `"plan probe "` (priority 85) before generic `"plan "` (priority 50)
- `"execute probe "` before explanation handlers

### Response Formatter

All deterministic handler responses use `build_deterministic_response()` from `weslr/response_formatter.py`:
```python
build_deterministic_response(
    message=message,
    path=path,
    response_text=response_text,
    payload=payload,          # optional
    confidence=confidence,     # default "high"
    suggested_mode=mode,       # optional
)
```

The formatter returns the full canonical response skeleton. Handlers call it instead of building the dict directly. Optional fields (`payload`, `suggested_mode`) are merged in, not overwritten.

---

## Consequences

**Positive:**
- Dispatch order is explicit and auditable — priority values make ordering decisions visible at a glance
- No accidental handler shadowing — a registry entry with conflicting triggers would be visible during code review
- Response field consistency — all migrated handlers return the same fields in the same structure
- Easy to add new handlers — add an entry to `HANDLER_REGISTRY` and a handler function; no need to find the right insertion point in interpretation.py
- Extraction is incremental — handlers can be migrated one at a time without changing the overall structure

**Negative:**
- Two-call dispatch — the dispatch function is called, which calls the handler function; one extra hop
- Handler function must be in the same module as the registry or registered explicitly
- Priority numbers are somewhat arbitrary — requires discipline to keep priority values meaningful as the registry grows

**Neutral:**
- interpretation.py is still a monolith in many ways — the registry only handles deterministic queries, not the full interpretation pipeline
- Not all handlers are migrated yet — the current registry has 2 entries; more will follow

---

## Alternatives Considered

**Alternative 1: Full rewrite of interpretation.py**
Replace the entire file with a handler registry and separate modules for each subsystem. Risk: too large a change for the current phase. The extraction approach is incremental and can be validated at each step.

**Alternative 2: Use a decorator-based registry**
Python decorators (`@handler`) applied to handler functions that register themselves. Risk: decorators add complexity and magical registration behavior. A static registry dict is more explicit and easier to audit.

**Alternative 3: Leave interpretation.py as-is and document handler ordering**
Document the implicit ordering in a reference document. Risk: ordering is enforced only by convention, which degrades over time as new handlers are added in the wrong place. The registry makes ordering a property of the data.

---

## Reversal Conditions

This ADR should not be reversed once a third handler is migrated. The registry pattern is established and incremental migration is the correct approach.

Reversal considerations if the approach proves unworkable:
- If a handler cannot be extracted because it has too many dependencies on interpretation.py's local state — address those dependencies first before extraction
- If the registry grows to a size where simple list-sort is too slow — consider indexing by first-character, but this is not a near-term concern

---

*ADR-0004 — Handler Registry and Response Formatter — Accepted 2026-04-27*
