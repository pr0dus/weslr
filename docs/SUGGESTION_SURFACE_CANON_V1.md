# SUGGESTION_SURFACE_CANON_V1.md — WESLR Suggestion Surface Canonical Architecture

**Status:** SEALED — Chapter v1
**Date:** 2026-04-20
**Supersedes:** None (new canonical document)

---

## PURPOSE

The suggestion surface translates WESLR's relevance observations into structured, operator-facing metadata. It exists to make relevant signals visible through normal interaction surfaces — reducing dependence on dedicated dashboards and placing discovery in the flow of work.

### What it IS

- An **exposure layer**: surfaces WESLR observations in a controlled, human-readable form
- A **translation layer**: converts relevance scores and match reasons into optional next-step suggestions
- An **advisory system**: never commands, never routes, never decides
- An **inspectable artifact**: embedded in `explain_item` output, readable by operator or tooling

### What it is NOT

- Not a decision engine — does not commit WESLR to any action
- Not an execution engine — does not call write functions, does not modify state
- Not a routing authority — may not influence which handler processes a request
- Not a background notification system — suggestions appear only when `explain_item` is called
- Not an auto-write path — no suggestion object causes a database or registry write

---

## CORE CONCEPTS

### Suggestion Surface

The mechanism by which WESLR exposes structured optional-action metadata to the operator. Currently implemented as a field (`_suggestions`) in the `explain_item` return dictionary.

**Scope:** One call to `explain_item` → one `_suggestions` list.
**Boundaries:** Suggestions exist only for the duration of the response. There is no persistent suggestion queue, no background thread, and no push mechanism.

---

### Suggestion Object

A single structured record returned as part of `_suggestions`. Each object represents one discrete optional action WESLR is flagging for operator consideration.

**Scope:** One suggestion = one interest-triggered optional action.
**Boundaries:** A suggestion object has no side effects. It is a data structure, not a function call.

---

### Suggestion Type

A string discriminator identifying the category of action suggested. Type determines the semantics of the suggestion and shapes what the operator is being asked to approve.

**Current canonical type:** `interest_occurrence`
**Boundaries:** Type is a label only. It does not trigger special handling, does not bypass approval, and does not alter cooldown behavior.

---

### Structured Action

The `action` field within a suggestion object. Contains a machine-readable action descriptor — a command name plus parameters — that could be used to fulfill the suggestion if the operator approves.

**Scope:** Encodes what WESLR would do if explicitly authorized.
**Boundaries:** The structured action is a proposal. It is never auto-executed. `requires_approval: true` is the mandatory default for all consequential actions.

---

### Cooldown

A per-suggestion suppression window that prevents the same suggestion from re-surfacing within a configured time period. Cooldown is tracked in memory only — not persisted to disk.

**Scope:** `interest_id + item_id + suggestion_type` → 12-hour suppression window.
**Boundaries:** Cooldown suppresses surfacing only. It does not change eligibility, does not alter relevance scores, and does not affect any other suggestion type or interest.

---

### Approval Requirement

The invariant that consequential actions require explicit operator authorization before execution. The `requires_approval` field in the `action` descriptor must always be `true` for `interest_occurrence` suggestions. This is not a configurable option — it is a structural constraint.

**Scope:** Applies to all suggestion types currently defined.
**Boundaries:** Approval is not bypassed under any circumstance in the canonical implementation. Silent execution is forbidden.

---

## SOURCE OF TRUTH

### Authoritative Implementation Files

| File | Role |
|------|------|
| `sim.py` | Current suggestion integration surface. Contains `_derive_suggestions()` and `_derive_relevant_interests()`. Adds `_suggestions` and `_relevant_interests` to `explain_item` output. |
| `weslr/relevance_surface.py` | Read-only relevance input source. `query_relevant_interests()` derives relevance scores from tracked interests. No writes. |
| `weslr/interest_tracker.py` | Write authority for the interest registry. `create_interest()`, `add_occurrence()`, and all state-modifying functions live here. Suggestions never call these directly. |
| `weslr/test_relevance_suggestions.py` | Behavioral contract tests. Encode the expected behavior of the suggestion surface — what may surface, what must never happen, and how cooldown behaves. |

### Write Authority Boundary

```
sim.py (suggestion surface)
    ↓ surfaces metadata only, never writes
weslr/interest_tracker.py (write authority)
    ↓ is the only module permitted to modify interests.json
    ↓ suggestions call interest_tracker functions ONLY when operator explicitly approves
```

**Invariant:** `sim.py` may surface suggestions. `sim.py` may not mutate interest state. No suggestion object, cooldown mechanism, or future extension may bypass this boundary.

---

## OUTPUT CONTRACT

### Canonical `_suggestions` Metadata Contract

When `explain_item(item_id)` is called for an artifact, the return dictionary includes:

```python
{
    "type": "artifact",
    "id": item_id,
    # ... existing fields ...
    "_relevant_interests": [<scored interest>, ...],  # from _derive_relevant_interests()
    "_suggestions": [<suggestion object>, ...],      # from _derive_suggestions()
}
```

### Suggestion Object Shape

```python
{
    "type": "interest_occurrence",          # str: suggestion category
    "message": "...",                       # str: human-readable suggestion text
    "confidence": 0.45,                     # float: 0.0–1.0, derived from relevance score
    "reasons": ["matched tag: governance"], # list[str]: match reasons from relevance surface
    "action": {                             # dict: structured action descriptor
        "command": "record_occurrence",     # str: canonical command name
        "interest_id": "<id>",              # str: target interest identifier
        "interest_name": "<name>",          # str: target interest name
        "item_id": "<id or title>",         # str: artifact that triggered the suggestion
        "requires_approval": True,           # bool: MUST be True — not optional
    },
}
```

### Field Semantics

| Field | Required | Type | Semantics |
|-------|----------|------|-----------|
| `type` | Yes | string | Suggestion category discriminator. Currently `interest_occurrence`. |
| `message` | Yes | string | Natural language description of the suggested action. Operator-facing. |
| `confidence` | Yes | float | Relevance-derived confidence. Advisory only — not authority, not probability. |
| `reasons` | Yes | list[string] | Match reasons from the relevance surface. Provides evidence trail. |
| `action.command` | Yes | string | Canonical command name that would fulfill the suggestion. |
| `action.interest_id` | Yes | string | Identifier of the interest this suggestion relates to. |
| `action.interest_name` | Yes | string | Display name of the interest this suggestion relates to. |
| `action.item_id` | Yes | string | Identifier of the artifact that triggered the suggestion. |
| `action.requires_approval` | Yes | boolean | **Must be `True`**. Consequential actions require operator authorization. |

### Empty / No-Suggestion Behavior

When no relevant interests are found or all matched interests score zero:

```python
"_suggestions": []     # Empty list, not None
```

An empty list is the correct, expected state. It is not an error. The `_relevant_interests` field may also be `[]` in this case.

---

## CURRENT ALLOWED SUGGESTION TYPE

### `interest_occurrence`

**Definition:** A suggestion that the operator approve recording an occurrence of a tracked interest against the current artifact.

**When it may surface:**
- `explain_item()` is called for an artifact
- At least one tracked interest has a positive relevance score (after `has_signal` gate)
- No active cooldown entry exists for `interest_id + item_id + "interest_occurrence"`
- The relevance score derives from at least one eligible signal (tag match, name match, tag-in-text, display_name match)

**What it may suggest:**
- That the operator consider recording an occurrence via the `record_occurrence` command
- Message references the interest by display name
- Reasons field includes the relevance match reasons

**What it may NEVER do:**
- Auto-create an occurrence — operator must approve
- Auto-create an interest — separate `create_interest` flow, not suggested
- Write to `interests.json` — `add_occurrence()` is called only on explicit operator approval
- Trigger on interests with no eligible signal — recency and occurrence count alone cannot surface this suggestion
- Surface more than once per `interest_id + item_id` within 12 hours

---

## COOLDOWN CONTRACT

### Current Cooldown Law

**Definition:** A time-bounded suppression mechanism that prevents the same `interest_occurrence` suggestion from re-surfacing within 12 hours for the same `interest_id + item_id` combination.

### Characteristics

| Property | Value |
|----------|-------|
| Scope key | `interest_id:item_id:interest_occurrence` |
| Duration | 12 hours (43,200 seconds) |
| Storage | In-memory only (`_derive_suggestions._cooldown_store` dict) |
| Persistence | None — lost on process restart |
| Effect | Suppresses suggestion surfacing only |
| Effect on eligibility | None — same interest remains eligible for scoring |

### Cooldown Does NOT Alter

- **Eligibility:** An interest with an active cooldown entry is still scored normally. Cooldown only suppresses the output of a suggestion, not the underlying relevance signal.
- **Truth:** Cooldown does not change interest state, relevance scores, or match reasons.
- **Authority:** Cooldown does not grant WESLR any additional authority. It is a UX suppression mechanism, not a permission grant.

### Cooldown Boundary

Cooldown is scoped to `interest_id + item_id + suggestion_type`. This means:
- Same interest, same artifact → suppressed after first surfacing
- Same interest, different artifact → NOT suppressed
- Different interest, same artifact → NOT suppressed
- Different suggestion type → NOT suppressed

---

## SAFETY AND GOVERNANCE RULES

1. **Advisory-only:** Suggestions are metadata. They describe what *could* be done, not what *should* be done or what *will* be done. WESLR never acts on a suggestion without explicit operator approval.

2. **requires_approval is structural:** For `interest_occurrence`, `action.requires_approval` must be `True`. This is not advisory guidance — it is a mandatory invariant. No implementation path may produce an `interest_occurrence` suggestion with `requires_approval: False`.

3. **No auto-execution:** No suggestion object, regardless of confidence or type, is ever auto-executed. The suggestion surface produces data. Operator authorization produces action.

4. **No write authority delegation:** Suggestions may not call `create_interest()`, `add_occurrence()`, or any other function in `interest_tracker.py`. The operator approves; WESLR executes only on explicit instruction after approval.

5. **No routing influence:** Suggestions and their metadata (confidence, reasons, type) may not influence how WESLR routes requests, selects handlers, or формирует responses outside the `_suggestions` field itself.

6. **No ranking or wording influence:** Suggestion presence, absence, or confidence may not alter how WESLR explains, ranks, or presents artifacts in any context other than the suggestion metadata itself.

7. **Inspectability:** All suggestion objects are readable by the operator at all times. There is no hidden suggestion suppression, no shadow filtering, and no undocumented removal.

8. **Reversibility:** The suggestion surface is additive. Removing `_suggestions` from the `explain_item` return dict does not alter any underlying system behavior. All suggestion-related logic can be disabled by omitting the suggestion field without affecting interests, relevance scores, or artifact metadata.

---

## FORBIDDEN DRIFT

The following are explicitly prohibited as future changes unless a new canonical document supersedes this one:

- **Turning suggestions into silent actions:** No suggestion may automatically trigger a state change without operator approval in the loop.
- **Background push notifications:** Suggestions may not be delivered through a background notification channel, push message, or async alert without explicit operator opt-in configuration.
- **Persistent cooldown without approval:** Cooldown state may not be written to disk, stored in a database, or shared across processes without explicit operator approval and a new canonical document.
- **Suggestions influencing routing:** No suggestion metadata may be used to select or bias handler selection, agent routing, or response strategy.
- **Direct writes from suggestion surface:** `_derive_suggestions()` or any future suggestion derivation function may not call any function that modifies `interests.json` or any registry.
- **Dashboard lifecycle assumptions:** Assumptions about operator dashboard access, polling intervals, or notification pull may not be baked into the suggestion surface. Suggestions must work through normal interaction surfaces.
- **Confidence as authority:** Suggestion `confidence` may not be used as a decision threshold, routing gate, or action trigger. It is advisory metadata only.
- **Silent suggestion filtering:** Suggestions may not be suppressed based on internal heuristics without the suppression being documented and the filtered suggestion being visible in inspection.

---

## FUTURE EXTENSION RULES

Allowed future directions (all require explicit operator approval and a new or updated canonical document):

| Extension | Requirement |
|-----------|-------------|
| Additional suggestion types | New canonical document defining type, contract, cooldown, and governance |
| Persistent suggestion queues | Operator-approved persistence design; cooldown state survives restart |
| Voice surfacing | Explicit operator configuration; no auto-enabling |
| Richer trigger logic | Must not create interests or write to registries |
| Cooldown persistence | Must be operator-approved; must not alter eligibility semantics |
| Thread-based suggestions | Must not assume thread continuity without explicit thread model |
| Suggestion acceptance/denial history | Read audit trail only; may not influence future suggestions without operator approval |

### Invariants for All Extensions

Every future extension must preserve:
1. **Advisory-only nature** — no auto-action without operator in the loop
2. **Write authority boundaries** — suggestion surface never writes to registries
3. **Inspectability** — all suggestions and suppression reasons visible to operator
4. **Reversibility** — extension can be disabled without breaking core behavior
5. **No routing influence** — suggestion metadata never biases handler selection

---

## STOP LINE

**Confirmed:**
- Documentation only ✅
- No production code changes ✅
- No schema changes ✅
- No behavior changes ✅
- No new integration points ✅
- No implementation of voice, persistence, or new signals ✅
- Canon document created: `docs/SUGGESTION_SURFACE_CANON_V1.md` ✅

**This document is sealed against unauthorized drift. Changes require explicit operator approval and a new or updated canonical document.**
