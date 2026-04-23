# THREAD_TRACKER_CANON_V1.md — WESLR Thread Tracker v1 Canonical Architecture

**Status:** CANONICAL — authoritative implementation reference
**Date:** 2026-04-21
**Classification:** SLICE 0 + SLICE 1 — storage + CLI + read-only metadata surface

---

## SECTION 1 — FILES CHANGED

| File | Role |
|------|------|
| `docs/THREAD_TRACKER_V1_DESIGN.md` | Design intent and linking rules |
| `docs/THREAD_TRACKER_CANON_V1.md` | **This document** — authoritative implementation reality |
| `weslr/thread_tracker.py` | Thread write/read authority (canonical) |
| `weslr/threads.json` | State truth — plain JSON, operator-readable at all times |
| `commands/thread.py` | Operator CLI surface |
| `sim.py` | Read-only `_thread_refs` integration surface (Slice 1) |
| `weslr/test_thread_tracker.py` | Behavioral contract tests for Slice 0 |
| `weslr/test_thread_read_surface.py` | Behavioral contract tests for Slice 1 |

No schema changes. No behavior changes. No new integrations.

---

## SECTION 2 — COMMANDS RUN

None. This pass is documentation-only.

---

## SECTION 3 — DOCUMENT SUMMARY

This document converts the current Thread Tracker implementation into protected canonical architecture. It defines what Thread Tracker is, what it is not, which files own what, the exact data model contract, write rules, read surface contract, safety and governance rules, forbidden drift, and future extension rules.

---

## SECTION 4 — PURPOSE

### What Thread Tracker Is

Thread Tracker provides **inspectable temporal continuity** — the ability to group related artifacts, questions, suggestions, and resolutions into explicit, named threads that the operator can see, audit, and control.

Specifically:

- **Linking:** Connects items to threads through explicit operator action or approved integration signals
- **State tracking:** Tracks whether a thread is `active`, `unresolved`, `resolved`, or `dormant`
- **Continuity exposure:** Makes visible the chain of events that led to a decision or artifact
- **Metadata-first:** Thread membership is surfaced as advisory metadata, never as hidden context injection

### What Thread Tracker Is NOT

- **Not a reasoning engine:** Thread Tracker does not infer motivations, implications, or causal chains. It records links, not meanings.
- **Not a routing authority:** Thread membership does not influence how requests are handled or routed.
- **Not a hidden context injector:** Thread content is never silently injected into artifact explanation, relevance scoring, or response generation.
- **Not an automatic linking engine:** Links are created only through explicit operator action or approved allow-listed signals.
- **Not a background scanner:** WESLR does not scan artifacts or questions for thread opportunities without an explicit operator request.

---

## SECTION 5 — CORE CONCEPTS

### Thread

**Definition:** A named, temporally ordered sequence of items that the operator or an approved integration has explicitly grouped together.

**Scope:** One thread tracks one unit of continuity — a project, a decision, a question chain, a problem-solving flow, or a named area of work.

**Boundaries:** A thread is not an entity. It does not have beliefs, goals, or opinions. It is a record of linkage. Thread links are independent of entity graph relationships. A thread can link items from different entities. An entity can appear across multiple threads.

### Thread Item

**Definition:** A discrete unit of content with an identifier, a type, and a timestamp, placed into a thread by explicit operator action or an approved integration signal.

**Types:**

| Type | Definition |
|------|-----------|
| `artifact` | An artifact from the artifact registry |
| `question` | A question from the open question registry |
| `suggestion` | A suggestion event (when accepted) |
| `resolution` | A resolution event (when a question is answered or deferred) |
| `note` | An operator annotation or context note |

**Boundaries:** A thread item is a reference, not a copy. The item's canonical state lives in its source registry.

### Thread State

**Definition:** The current operational status of a thread.

| State | Definition | Who Sets It |
|-------|-----------|-------------|
| `active` | Thread is in progress; new items may be added | Automatically on creation with ≥1 item |
| `unresolved` | Thread has a goal or question not yet answered | Operator explicitly via `thread set-state` |
| `resolved` | Thread's purpose has been fulfilled | Operator explicitly via `thread set-state` |
| `dormant` | Thread inactive for configured idle period | Operator confirmation required — never automatic |

**Boundaries:** State is a label applied by operator action. WESLR never autonomously sets state to `resolved` or `dormant`.

### Link Type

**Definition:** The authority under which an item was added to a thread.

| Link Type | Definition | Authority |
|-----------|-----------|-----------|
| `explicit` | Created by direct operator action | Operator only |
| `inferred` | Created by an approved integration signal | Canon-approved integration only |

**Boundaries:** `inferred` links require a defined allow-listed signal. No semantic or relevance-based inference is permitted in v1.

### Thread Read Surface

**Definition:** The canonical surface through which WESLR components (currently `sim.py` via `explain_item()`) access thread membership for an item.

**Current surface:** `_thread_refs` — an advisory metadata field returned by `sim._get_thread_refs()`, populated by calling `thread_tracker.get_threads_for_item()`.

**Boundaries:** The read surface is metadata-only. `_thread_refs` does not influence routing, wording, ranking, scoring, or any decision.

---

## SECTION 6 — SOURCE OF TRUTH

### Authoritative Files

| File | Authority |
|------|-----------|
| `weslr/thread_tracker.py` | Thread write/read authority. All mutations to `threads.json` must go through this module. |
| `weslr/threads.json` | State truth. Plain JSON, operator-readable and editable at any time. |
| `commands/thread.py` | Operator CLI surface. Calls `thread_tracker.py` functions exclusively. |
| `sim.py` | Read-only `_thread_refs` integration. Calls `thread_tracker.get_threads_for_item()` only. |
| `weslr/test_thread_tracker.py` | Behavioral contract tests for Slice 0 (storage + API). |
| `weslr/test_thread_read_surface.py` | Behavioral contract tests for Slice 1 (read surface). |

### Authority Rules

1. **Only `thread_tracker.py` may mutate `threads.json`.** No other module writes threads directly.
2. **`sim.py` may read thread references only.** It calls `thread_tracker.get_threads_for_item()` for advisory metadata. It may not create threads, add items, set state, or otherwise mutate `threads.json`.
3. **`commands/thread.py` drives all operator CLI actions** by calling `thread_tracker.py` functions. Operators may also edit `threads.json` directly.
4. **Tests are the behavioral contract.** `test_thread_tracker.py` and `test_thread_read_surface.py` define what the implementation must do. They must continue to pass.

---

## SECTION 7 — DATA MODEL CONTRACT

### Thread Object Schema

```json
{
  "id": "thr-<8-hex>",
  "name": "<string, max 100 chars>",
  "created_at": "<ISO8601>",
  "updated_at": "<ISO8601>",
  "state": "active | unresolved | resolved | dormant",
  "tags": ["<string>"],
  "items": [/* ThreadItem objects, max 200 */]
}
```

### Thread Item Object Schema

```json
{
  "item_id": "<string>",
  "item_type": "artifact | question | suggestion | resolution | note",
  "link_type": "explicit | inferred",
  "added_by": "operator | integration:<name>",
  "added_at": "<ISO8601>",
  "note": "<string, max 500 chars>"
}
```

### Allowed States

`active`, `unresolved`, `resolved`, `dormant` — no others.

### Allowed Link Types

`explicit`, `inferred` — no others.

### Allowed Item Types

`artifact`, `question`, `suggestion`, `resolution`, `note` — no others.

### Bounds

| Rule | Limit | Behavior at Limit |
|------|-------|-------------------|
| Max threads | 100 | Oldest dormant threads pruned; operator notified; `create_thread` returns `None` if still at capacity |
| Max items per thread | 200 | Oldest item dropped (FIFO); new item appended |
| Thread name length | 100 chars | Truncated at 100 |
| Thread note length | 500 chars | Truncated at 500 |
| Tags per thread | 10 | Excess tags silently discarded |

### Required Fields

| Field | Required | Type |
|-------|----------|------|
| `id` | Yes | string |
| `name` | Yes | string |
| `created_at` | Yes | ISO8601 string |
| `updated_at` | Yes | ISO8601 string |
| `state` | Yes | enum string |
| `items` | Yes | list (may be empty) |
| `added_by` | Yes (on item) | string |
| `link_type` | Yes (on item) | enum string |

### Invariants

1. Every thread has a unique `id`.
2. `updated_at` is updated on every mutation (item add, state change).
3. `added_at` on every item is set at item creation time.
4. No anonymous items — every item has `added_by` set.
5. `threads.json` is always valid JSON (empty `{"threads": []}` on first run).

---

## SECTION 8 — WRITE RULES

### Allowed Write Operations

| Operation | Authority |
|-----------|-----------|
| Create thread | Operator CLI (`thread create`) or direct JSON edit |
| Add item to thread | Operator CLI (`thread add-item`) or direct JSON edit |
| Set thread state | Operator CLI (`thread set-state`) only |
| Remove thread | Operator CLI (no dedicated command; direct JSON edit) |
| Prune oldest items on item limit | `thread_tracker.py` internal (FIFO eviction) |
| Prune dormant threads on thread limit | `thread_tracker.py` internal |

### Forbidden Write Operations

| Forbidden | Reason |
|-----------|--------|
| Automatic linking based on relevance scores | Would constitute hidden context injection |
| Automatic linking based on semantic similarity | Not in v1 scope — requires explicit approval |
| Background thread creation | Violates metadata-first principle |
| Silent thread mutation from `explain_item` | `sim.py` read-only surface contract |
| Thread state changes without explicit action | State is operator-controlled only |
| Any write from outside `thread_tracker.py` | Authority boundary |
| Auto-closure (`resolved` or `dormant` set automatically) | Operator must confirm closure |

### Write Authority Boundary

```
Operator ──CLI──► commands/thread.py ──calls──► weslr/thread_tracker.py ──writes──► weslr/threads.json
Operator ──direct JSON edit────────────────────────────────────────────────────────► weslr/threads.json
sim.py ──read only (get_threads_for_item)────────────────────────────────────────► weslr/threads.json
```

Only the leftmost two paths are valid for writes. Direct JSON edit by operator is always valid.

---

## SECTION 9 — READ SURFACE CONTRACT

### `_thread_refs` Metadata Contract

When `sim.explain_item()` is called for an artifact, it attaches `_thread_refs` — a list of thread reference summaries for all threads containing that artifact's item ID.

### Exact Field Shape

```json
"_thread_refs": [
  {
    "thread_id": "thr-xxxxxxxx",
    "thread_name": "Governance health review",
    "state": "active",
    "link_type": "explicit",
    "added_by": "operator",
    "added_at": "2026-04-20T10:00:00Z",
    "item_id": "artifact-001"
  }
]
```

### Empty Behavior

If the item is in no threads: `_thread_refs` is absent (key not present) or an empty list `[]` — both are valid. Callers must handle both.

### Read-Only Guarantee

`_get_thread_refs()` in `sim.py` calls `thread_tracker.get_threads_for_item()` — a read-only function that never mutates `threads.json`.

Contract confirmed by `test_thread_read_surface.py`:
- `test_thread_refs_no_writes` — `_get_thread_refs` does not write to `threads.json`
- `test_thread_refs_does_not_create_threads` — never creates a thread
- `test_thread_refs_does_not_add_items` — never adds items to any thread

### Exact-Match Item ID Rule

`_thread_refs` uses **exact string match** on `item_id`. Different item types with the same base ID are separate items. There is no fuzzy matching, no substring matching, no type coercion.

### Advisory-Only Invariant

`_thread_refs` is **advisory metadata only**. Its presence, absence, or content does not:
- Change how WESLR scores or ranks artifacts
- Influence routing decisions
- Alter relevance surface scores
- Modify suggestion surfacing behavior
- Affect any internal decision or generation logic

Thread membership is informational — a historical record of linkage. It is never a signal for WESLR reasoning.

---

## SECTION 10 — SAFETY AND GOVERNANCE RULES

### 1. No Auto-Linking

Thread links are created only by operator action or a defined allow-listed signal. No hidden inference from relevance, similarity, shared tags, temporal proximity, or any unapproved signal.

### 2. No Hidden Mutation

Thread data is stored in plain JSON. All changes through `thread_tracker.py` are timestamped with `added_by` and `link_type`. No silent edits. Operators can audit by reading `threads.json` directly.

### 3. No Routing Influence

Thread membership does not affect how WESLR routes requests, selects handlers, or generates responses. `_thread_refs` is advisory only.

### 4. No Automatic Closure

WESLR may suggest resolving or closing a thread. It may not do so automatically. Only the operator can mark a thread `resolved` or `dormant`.

### 5. Reversibility

All changes can be undone by operator command or direct JSON edit. No irreversible operations. `threads.json` is always valid JSON and human-editable.

### 6. No Reasoning Inference

Thread Tracker does not infer why items are linked. It records that they are linked. The operator provides meaning.

### 7. No Entity Coupling

Thread links are independent of entity graph relationships. A thread can span multiple entities. An entity can appear across multiple threads. Thread links may not be automatically converted into entity graph relationships.

### 8. Audit Trail

Every item addition records `added_by` and `link_type`. No anonymous links. Every mutation updates `updated_at`.

### 9. Inspectability

`weslr/threads.json` is always human-readable. `thread list`, `thread show`, `thread state` commands provide CLI access to all thread state.

### 10. Test Contract

`test_thread_tracker.py` and `test_thread_read_surface.py` are the behavioral contract. They must continue to pass for any implementation change. Any behavioral change requires updating the tests first.

---

## SECTION 11 — FORBIDDEN DRIFT

The following changes are **explicitly prohibited** in v1 and any future version without a new canonical document:

| Forbidden Change | Reason |
|-----------------|--------|
| Semantic or similarity-based linking without explicit approval | Would make Thread Tracker a hidden reasoning layer |
| Thread-based routing influence | Violates advisory-only read surface contract |
| Hidden thread context injection into explanation, relevance, or suggestion surfaces | Violates metadata-first principle |
| Background thread scanning for patterns, gaps, or opportunities | Violates explicit-action requirement |
| Direct writes to `threads.json` from any module other than `thread_tracker.py` | Breaks authority boundary |
| Automatic resolution or closure of threads | Only operator may close threads |
| Thread-to-entity graph projection without operator approval | Breaks entity/thread independence |
| Use of `_thread_refs` for ranking, scoring, or routing decisions | Violates advisory-only invariant |
| Auto-promotion of items to threads based on relevance scores | Not in v1 scope |
| Storing thread links in entity graph without explicit operator action | Separate system — requires separate canonical |
| Fuzzy or substring matching for `_thread_refs` item lookup | Exact-match is the defined contract |
| Mutation of thread state by any process outside operator control | State is operator-controlled only |

---

## SECTION 12 — FUTURE EXTENSION RULES

The following are **allowed future directions** — but all require explicit approval via a new canonical document before implementation:

| Extension | Governance Requirement |
|-----------|----------------------|
| Linking suggestions surfaced to operator for approval | New canonical document required |
| Inferred linking under strict allow-list (e.g., question answered registry integration) | New canonical document required; integration must be explicitly approved |
| Thread-aware suggestion surfacing (advisory only, not routing) | New canonical document required |
| Thread resolution suggestions (operator decides whether to close) | New canonical document required |
| Dormant thread surfacing (alert, not auto-state-change) | New canonical document required |
| Thread history views (timeline of items in a thread) | Likely low-risk — governance review still required |
| Thread-based search or filtering of artifacts | New canonical document required |
| Cross-thread item deduplication alerts | New canonical document required |

### Required Properties for All Future Extensions

All future extensions must preserve:

- **Metadata-first exposure:** Thread information is surfaced as visible metadata, never as hidden context
- **Explicit write authority:** Writes always go through `thread_tracker.py`; no direct mutations
- **Advisory-only read surfaces:** `_thread_refs` and any future read surface are informational, never decision-influencing
- **Inspectability:** All thread data remains human-readable in `threads.json`
- **Reversibility:** All changes remain operator-undoable via CLI or direct JSON edit
- **Test coverage:** Any new behavior must be covered by tests before or alongside implementation
- **Governance surface:** No automatic behavior; operator always confirms or decides

---

## SECTION 13 — SLICE MAPPING

| Slice | Description | Status |
|-------|-------------|--------|
| Slice 0 | Storage layer (`thread_tracker.py`) + CLI (`commands/thread.py`) + `threads.json` | ✅ Implemented + validated |
| Slice 1 | Read-only `_thread_refs` metadata surface in `sim.explain_item()` | ✅ Implemented + validated |

Future slices (not yet approved):
- Slice 2: Linking suggestions
- Slice 3: Inferred linking under allow-list
- Slice 4: Thread-aware suggestion surfacing

---

## SECTION 14 — STOP LINE

**Confirmed:**

- Documentation only ✅
- No production code changes ✅
- No schema changes ✅
- No behavior changes ✅
- No new integrations ✅
- No linking suggestions ✅
- No inferred linking expansion ✅
- No automatic linking ✅
- No auto-closure ✅

**Canonical document created:** `docs/THREAD_TRACKER_CANON_V1.md` ✅

**Stop. Do not implement linking suggestions. Do not add inferred linking. Do not modify production code.**
