# THREAD_TRACKER_V1_DESIGN.md — WESLR Thread Tracker v1 Design

**Status:** DESIGN — not implemented
**Date:** 2026-04-20
**Chapter:** Additive layer after Interest/Relevance

---

## PURPOSE

### What Thread Tracking IS

Thread tracking is the layer that gives WESLR temporal memory — the ability to recognize that a new artifact, question, or event is a continuation of something previously discussed or decided. It provides continuity without requiring the operator to re-explain context.

Specifically:
- **Linking:** Connecting a new artifact or question to a prior thread based on explicit signals
- **State tracking:** Knowing whether a thread is active, unresolved, resolved, or dormant
- **Causality exposure:** Making visible the chain of events that led to a decision or artifact
- **Continuity without inference:** Surfacing "this relates to that" without WESLR inferring hidden relationships

### What Thread Tracking is NOT

- **Not a reasoning layer:** Thread Tracker does not infer motivations, implications, or causal chains. It records links, not meanings.
- **Not a decision engine:** It does not decide whether something is important. It only tracks what was linked.
- **Not a routing authority:** Thread membership does not influence how requests are handled.
- **Not a background process:** Threads are created and updated only through explicit operator actions or approved integrations.
- **Not a knowledge graph:** Thread Tracker tracks temporal sequence and explicit links, not semantic relationships or entity identity.
- **Not auto-linking:** WESLR may not create thread links without explicit operator action or a defined allowed signal.

---

## CORE CONCEPTS

### Thread

A thread is a named, temporally ordered sequence of items that the operator or an approved integration has explicitly grouped together.

**Definition:** A coherent unit of work or discussion with a defined lifecycle.
**Scope:** One thread tracks one unit of continuity — a project, a decision, a question chain, a problem-solving flow.
**Boundaries:** A thread is not an entity. It does not have beliefs, goals, or opinions. It is a record of linkage.

### Thread Item

Any artifact, question, or event that has been linked into a thread.

**Definition:** A discrete unit of content with an identifier, a type, and a timestamp, placed into a thread by explicit operator action or an approved integration signal.
**Types:**
- `artifact` — an artifact from the artifact registry
- `question` — a question from the open question registry
- `suggestion` — a suggestion event (when accepted)
- `resolution` — a resolution event (when a question is answered or deferred)
- `note` — an operator annotation or context note

**Boundaries:** A thread item is a reference, not a copy. The item's canonical state lives in its source registry.

### Thread State

The current operational status of a thread.

| State | Definition | Trigger |
|-------|-----------|---------|
| `active` | Thread is in progress; new items may be added | Thread created with at least one item |
| `unresolved` | Thread has a goal or question that is not yet answered | Operator marks thread as having an open goal |
| `resolved` | Thread's purpose has been fulfilled | Operator marks resolved, or linked question is answered |
| `dormant` | Thread is inactive for a configured idle period | No new items for N days (configurable, default 7) |

**Boundaries:** State is a label applied by operator action. WESLR does not autonomously set state to `resolved` or `dormant` — only the operator can close a thread.

### Link

A connection between two items (or an item and a thread) established by explicit operator action or a defined allowed signal.

| Link Type | Definition | Authority |
|-----------|-----------|-----------|
| `explicit` | Created by direct operator action (e.g., "link this to that") | Operator only |
| `inferred` | Created by an approved integration signal (e.g., question answered by artifact) | Integration must be canon-approved |

**Allowed explicit link signals (v1):**
- Operator manually links two items
- Operator adds an item to a thread
- Question is answered or deferred (via approved registry integration)

**Allowed inferred link signals (v1):**
- A question's `answered_by` field links to an artifact → thread item added to question's thread
- An artifact's `_suggestions` includes `interest_occurrence` and operator approves → no automatic link (operator must link)

**Boundaries:** Links are not entity relationships. They do not imply semantic similarity. A link only means "these were explicitly grouped."

---

## MINIMAL DATA MODEL

### Thread Structure

```json
{
  "threads": [
    {
      "id": "thr-<uuid>",
      "name": "Governance health review",
      "created_at": "2026-04-20T10:00:00Z",
      "updated_at": "2026-04-20T14:30:00Z",
      "state": "active",
      "tags": ["governance", "review"],
      "items": [
        {
          "item_id": "artifact-<uuid>",
          "item_type": "artifact",
          "added_at": "2026-04-20T10:00:00Z",
          "added_by": "operator",
          "link_type": "explicit",
          "note": "Initial context"
        },
        {
          "item_id": "question-<uuid>",
          "item_type": "question",
          "added_at": "2026-04-20T12:00:00Z",
          "added_by": "operator",
          "link_type": "explicit",
          "note": "Linked from dashboard"
        }
      ]
    }
  ]
}
```

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique thread identifier |
| `name` | string | Yes | Human-readable thread name |
| `created_at` | ISO8601 | Yes | Creation timestamp |
| `updated_at` | ISO8601 | Yes | Last modification timestamp |
| `state` | enum | Yes | One of: active, unresolved, resolved, dormant |
| `items` | list | Yes | Ordered list of thread items (may be empty) |
| `tags` | list[string] | No | Operator-applied tags for filtering |
| `added_by` | enum | Yes | Who added the item: "operator" or "integration:<name>" |
| `link_type` | enum | Yes | "explicit" or "inferred:<source>" |

### Bounded Storage Rules

| Rule | Limit | Behavior at Limit |
|------|-------|-------------------|
| Max threads | 100 | Oldest dormant threads archived; operator notified |
| Max items per thread | 200 | Operator warned; thread remains writable |
| Thread name length | 100 chars | Truncated at 100 |
| Thread note length | 500 chars | Truncated at 500 |
| Tags per thread | 10 | Excess tags rejected with error |

### Inspectable JSON Design

All thread data is stored in `weslr/threads.json` — a plain JSON file readable and editable by the operator at any time. No encryption, no opaque blobs.

---

## LINKING RULES (V1)

### How Artifacts/Questions Get Linked

**Rule 1 — Operator Initiated (always allowed):**
The operator may link any item to any thread, or create a new thread from any item, at any time via CLI or direct JSON edit.

**Rule 2 — Question Answered (inferred, via registry integration):**
When a question in the open question registry receives an `answered_by` artifact ID:
- The registry integration may add that artifact as an inferred item in the question's thread
- This requires explicit operator approval in the registry integration flow (not automatic)

**Rule 3 — No Other Inferred Links:**
WESLR may not create thread links based on semantic similarity, shared interests, shared tags, or any other inferred signal without explicit operator approval and a new canonical document.

### What Signals Are ALLOWED (v1)

| Signal Source | Signal Type | Authority |
|--------------|-------------|-----------|
| Operator CLI (`thread add-item`) | explicit | Operator |
| Direct JSON edit | explicit | Operator |
| Question answered registry integration | inferred | Canon-approved integration only |

### What Is Explicitly NOT ALLOWED (v1)

- WESLR may not link artifacts to threads based on relevance scores
- WESLR may not infer thread membership from shared interest tags
- WESLR may not create thread links because two items "seem related"
- WESLR may not link based on temporal proximity alone
- WESLR may not use entity graph relationships as thread link signals
- WESLR may not auto-create threads from suggestion acceptance

---

## THREAD STATE RULES

### When a Thread Is Active

A thread becomes `active` when:
- Created by operator with at least one item, OR
- System startup after thread was `active` before restart

### When It Becomes Unresolved

A thread transitions to `unresolved` when:
- Operator explicitly marks it as having an open goal (`thread set-state unresolved <thread_id>`)
- A question linked to the thread is marked deferred

### When It Becomes Resolved

A thread transitions to `resolved` when:
- Operator explicitly marks it resolved (`thread set-state resolved <thread_id>`)
- All questions linked to the thread have been answered (operator must still confirm closure)

### When It Becomes Dormant

A thread transitions to `dormant` when:
- No new items have been added for N consecutive days (default: 7, configurable)
- This is a WESLR-suggested state only — operator is notified and must confirm

**Critical:** WESLR never auto-deletes threads. A dormant thread remains readable and recoverable indefinitely.

---

## READ SURFACE

### How Thread Information Is Exposed

Thread information is exposed through:

1. **`thread list` CLI command** — lists all threads with id, name, state, item_count, updated_at
2. **`thread show <thread_id>` CLI command** — shows full thread with all items
3. **`thread state <thread_id>`** — shows current state only
4. **`explain_item()` metadata** — artifacts may include `_thread_refs` field listing thread IDs the artifact appears in (read-only metadata, does not influence behavior)

### Metadata Only — No Behavior Change

Thread data in `_thread_refs` is advisory metadata. Its presence or absence does not:
- Change how WESLR scores or ranks artifacts
- Influence routing decisions
- Alter relevance surface scores
- Modify suggestion surfacing

Thread membership is informational — a historical record of linkage, not a signal for WESLR reasoning.

---

## SUGGESTION INTEGRATION (FUTURE)

### How Threads Could Later Generate Suggestions

This section is speculative and marks a future extension point, not an implemented feature.

**Possible future suggestions (all require new canonical document):**

| Suggestion | Trigger | Governance |
|-----------|---------|-----------|
| Thread continuation | New artifact matches thread topic | Operator must link manually |
| Dormant thread alert | Thread dormant > N days | Operator decides to continue or close |
| Unresolved thread flag | Question answered but thread still active | Operator marks resolved |
| Thread gap detection | Thread has no artifacts for 30 days | Advisory only |

**Advisory-only invariant:** Any thread-based suggestion is metadata only. Thread state never auto-triggers WESLR actions. The operator is always in the loop.

**Not in v1 scope:** All suggestion integration is deferred to a future authorized step.

---

## SAFETY AND GOVERNANCE

1. **No auto-linking without rules:** Thread links are created only by operator action or a defined allowed signal in an approved integration. No hidden inference.

2. **No hidden mutation:** Thread data is stored in plain JSON. All changes are logged with timestamp and `added_by` authority. No silent edits.

3. **No routing influence:** Thread membership does not affect how WESLR routes requests, selects handlers, or generates responses.

4. **No automatic closure:** WESLR may suggest resolving or closing a thread. It may not do so automatically. Only the operator can mark a thread resolved or dormant.

5. **Reversibility:** Thread data is JSON. Any change can be undone by direct file edit or operator command. No irreversible operations.

6. **No reasoning inference:** Thread Tracker does not infer why items are linked. It records that they are linked. The operator provides meaning.

7. **No entity coupling:** Thread links are independent of entity graph relationships. A thread can link items from different entities. An entity can exist across multiple threads.

8. **Audit trail:** Every item addition records `added_by` and `link_type`. No anonymous links.

---

## FORBIDDEN DRIFT

The following are explicitly prohibited in v1 and any future version without a new canonical document:

- **Thread becoming a hidden reasoning layer:** Thread data may not be used as an implicit context for WESLR inference. Thread context is only injected when operator explicitly requests it.
- **Silent decision influence:** Thread state may not auto-affect any WESLR decision, routing choice, or response strategy.
- **Uncontrolled linking:** WESLR may not create thread links based on semantic similarity, shared tags, temporal proximity, or any unapproved inferred signal.
- **Auto-closure of threads:** WESLR may not mark a thread resolved or dormant without explicit operator command.
- **Thread-based context injection:** Thread content may not be injected into artifact explanation, relevance scoring, or suggestion surfacing without explicit operator request or approved integration.
- **Thread-to-entity-graph projection:** Thread links may not be automatically converted into entity graph relationships without operator approval.
- **Background thread scanning:** WESLR may not scan threads for patterns, gaps, or opportunities without explicit operator request.

---

## STOP LINE

**Confirmed:**
- Design/spec only ✅
- No production code changes ✅
- No schema changes to existing systems (threads.json is new file) ✅
- No integration yet ✅
- No behavior changes to existing systems ✅
- Design doc created: `docs/THREAD_TRACKER_V1_DESIGN.md` ✅
