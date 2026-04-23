# TIMELINE-NATIVE CONTINUITY RESOLUTION V1
**Generated:** 2026-04-22 07:59 GMT+2  
**Purpose:** Design canonical model for continuity resolution across hidden session boundaries  
**Mode:** STRICT — design only, no code changes, no scoring changes, no routing changes, no new authority

---

## SECTION 1 — PURPOSE

### Why Session-Keyed Continuity Is Insufficient

The current active artifact registry is keyed by **session ID** — `session_id → artifact_id`. This is structurally correct for a runtime that thinks in sessions, but it creates a brittle boundary that:

1. **Treats every new session as a fresh start** — even when the operator is continuing the same work
2. **Exposes implementation detail to the resolution layer** — "this" means whatever is active in *this session*, not whatever is most relevant to *this operator's current work*
3. **Breaks the moment a real session boundary is crossed** — as cross-session evaluation proved: artifacts persist correctly, but Session B cannot find the artifact from Session A because the registry keys are different session strings
4. **Forces the operator to re-explain context** that should be obvious from prior work

The session-keyed model treats sessions as containers. The timeline-native model treats sessions as transient access points to a persistent continuity object.

### Why User-Facing Continuity Should Hide Session Boundaries

The operator should not experience WESLR as a system that "forgets" between sessions. They should experience it as a system that:

- **Knows what they were working on** — even across real time gaps
- **Resolves references correctly** — "this" means the thing being worked on, regardless of when the session started
- **Maintains artifact lineage** — revisions are visible as revisions of the same work, not new disconnected artifacts
- **Starts with appropriate context** — not empty, not polluted with unrelated artifacts from other threads

The session is an implementation detail. The operator's **work thread** is what should be continuous.

---

## SECTION 2 — CURRENT REALITY

### Artifact Persistence + Active Artifact Registry

```
continuity/artifacts/          — artifact files (art-*.json)
continuity/artifacts/index.json  — sequential list of all artifact IDs
continuity/artifacts/eval/    — evaluation artifacts

weslr/artifact_store.py:
  save_artifact(record)         → writes art-{ts}-{seq}.json
  get_artifact(artifact_id)     → reads from disk
  list_artifacts(limit)         → index + retrieval

Active Artifact Registry:
  continuity/active_artifact_registry.json
  Key: session_id (string)
  Value: { current_artifact_id, last_updated }

  set_active_artifact(session_id, artifact_id)
  get_active_artifact(session_id) → artifact_id or None
```

**Status:** Artifact persistence works. Active artifact registry works within a session key. Cross-session continuity breaks because registry is keyed by session string.

### Cross-Session Evaluation Findings

Three scenarios tested (`csc-001`, `csc-006`, `csc-008`):

| Finding | Detail |
|---------|--------|
| **Artifact persistence works** | Artifacts created in Session A are retrievable in Session B via `get_artifact(artifact_id)` |
| **Active artifact registry is session-keyed** | Session B cannot find artifact from Session A because registry is keyed by `session_id` string — different sessions have different keys |
| **Safe path works** | Missing artifact returns safe empty message, no crash |
| **Interest contamination is detectable** | `contamination_flags.interest_bleed_from_session_a_to_b` correctly flagged cross-domain interest bleed |
| **Reference resolution fails across sessions** | `"reference_resolution_result": "no_artifact_safe"` even when artifact exists — because `get_active_artifact(session_b_id)` looks up `session_b_id` in registry, not the most recent artifact for this user/thread |

### Existing Supporting Infrastructure

| Component | Purpose | Canonical Location |
|-----------|---------|-------------------|
| `threads.json` | Thread tracker — named temporally-ordered sequences of linked items (artifacts, questions, suggestions) | `weslr/thread_tracker.py` |
| `timeline events.jsonl` | Event log — timestamped, typed events with source and trust_level | `.weslr/timelines/tl_default/events.jsonl` |
| `institution.py` | Role timelines — permanent records that survive occupant changes | `weslr/institution.py` |
| `unified_continuity.py` | Consolidated view of profile, patterns, household, domain, governance, evidence | `weslr/unified_continuity.py` |
| `lineage_diff.py` | Compute diff between lineage records | `weslr/lineage_diff.py` |

**Key insight:** Thread tracker already models "named sequences of linked items" — this is closer to the user mental model than session-keyed registry. Timeline events already have timestamp ordering and source tracking.

---

## SECTION 3 — CONTINUITY RESOLUTION MODEL

### 3.1 User Scope

**Definition:** The continuity context associated with a specific operator identity, not a specific session.

**Properties:**
- Persists across sessions, days, weeks
- Owns: artifacts, threads, interests, timeline events
- Is the **granularity at which "this" should resolve** — not session, not global

**Resolution rule:** "This" in user scope means the most recent artifact that is:
1. Linked to the active thread for this user
2. Created by this user or by WESLR acting on behalf of this user
3. Not explicitly discarded or resolved

**Not:** A session string key. A random artifact from any session.

### 3.2 Institution Scope

**Definition:** Persistent role timelines and institutional knowledge. Layer 2 of WESLR's layer model.

**Properties:**
- Owned by the institution, not a single user
- Survives occupant changes (role vacancy does not delete records)
- Governs authorization and clearance boundaries

**For continuity resolution:** Institution scope determines **what a user is authorized to reference**. A user in "Engineering Lead" role can reference artifacts in the engineering thread; they may not have access to artifacts in the finance thread.

**Resolution rule:** Reference resolution must respect institution scope — users can only resolve artifacts within their authorized scope.

### 3.3 Artifact Lineage

**Definition:** An artifact's revision history — which artifact preceded it, which it was revised from, what changed.

**Current state:** `art-{ts}-{seq}.json` files are stored individually. No lineage chain is maintained between them (revision relationship not tracked in artifact metadata).

**Desired state:**
```json
{
  "artifact_id": "art-1776800000001-3",
  "lineage": {
    "root": "art-1776800000001-1",
    "parent": "art-1776800000001-2",
    "generation": 3,
    "chain": ["art-1776800000001-1", "art-1776800000001-2", "art-1776800000001-3"]
  },
  "source": "dialogue",
  "created_at": "2026-04-22T08:00:00Z"
}
```

**Resolution rule:** When resolving "this", return the **latest in the lineage chain** — not the root, not an intermediate version, unless explicitly requested.

### 3.4 Thread Continuity

**Definition:** A thread is a named, temporally ordered sequence of linked items (artifacts, questions, suggestions). Threads are the user's **work unit** abstraction.

**Properties:**
- Threads persist across sessions
- Active thread = the thread currently being worked on
- Thread has its own timeline — artifacts linked to thread in order

**Resolution rule:** "This" should resolve to the **most recent artifact in the active thread** for this user. The active thread is the one most recently interacted with — not the most recently created.

**Current infrastructure:** `weslr/thread_tracker.py` provides thread storage. Thread items have `item_type: artifact|question|suggestion|resolution|note`. Link types: `explicit|inferred`.

### 3.5 Timeline Recency

**Definition:** A global ordered log of events with timestamps, providing recency signals even when no explicit thread exists.

**Properties:**
- Timeline events are typed: `chat.message`, `artifact.created`, `thread.updated`, etc.
- Source tracking: `operator`, `system`, `weslr`
- Trust level: `direct`, `derived`, `inherited`

**Resolution rule:** Timeline provides fallback recency when no explicit thread context exists. The most recent artifact for this user in the timeline is the fallback resolution target.

**Current infrastructure:** `.weslr/timelines/tl_default/events.jsonl` — timestamp-ordered event log. Event shape: `{timestamp, event_type, data, frame, source, trust_level}`.

### 3.6 Relevance/Context Selection

**Definition:** When multiple candidate artifacts exist in scope, relevance scoring determines which is the best "this" candidate.

**Properties:**
- Interest-matched: artifact whose domain matches current declared interests
- Temporal: more recent artifacts preferred over older, unless older is explicitly relevant
- Thread-linked: artifact linked to active thread preferred over unlinked artifact

**Resolution rule:** Select the candidate with the highest composite score:
```
score = thread_weight * is_in_active_thread
      + recency_weight * temporal_proximity
      + interest_weight * interest_match_score
      + lineage_weight * is_latest_in_chain
```

Where weights are configurable and domain-shift detection prevents contamination.

---

## SECTION 4 — WHAT SHOULD RESOLVE "THIS"

### Resolution Cascade (in priority order)

When user says "improve this" / "explain this" / "revise that":

**Level 1 — Active Thread Artifact**
- Is there an active thread for this user?
- Does the active thread have artifacts?
- Return the most recent artifact in the active thread

**Level 2 — Latest Relevant Artifact by Timeline**
- No active thread, or active thread has no artifacts
- Query timeline for most recent `artifact.created` event by this user
- Return that artifact

**Level 3 — Latest Artifact in Lineage**
- Timeline also empty
- Return the latest-in-chain artifact from any artifact lineage for this user

**Level 4 — Safe No-Resolution**
- No artifacts exist for this user in any scope
- Return safe empty message: "I don't have a current artifact to refer to. Try asking me to analyze something..."

### What "This" Must Never Resolve To

- An artifact from a different user's scope
- A stale artifact (older generation when a newer generation exists in the same lineage)
- An artifact from a thread the user is not authorized to access
- An artifact from a completely unrelated domain (domain contamination)

### Resolution Metadata

Every resolution should return:
```json
{
  "resolved_artifact_id": "art-1776800000001-3",
  "resolution_path": "active_thread",  // "active_thread" | "timeline_recency" | "lineage_fallback" | "no_candidate"
  "lineage_chain": ["art-1776800000001-1", "art-1776800000001-2", "art-1776800000001-3"],
  "thread_id": "thr-abc12345",
  "thread_name": "PV Efficiency Work",
  "is_latest_in_chain": true,
  "confidence": 0.85,
  "contamination_check": {
    "domain_match": true,
    "user_scope_match": true,
    "authorization_clear": true
  }
}
```

---

## SECTION 5 — TIMELINE VS SESSION

### Session State

What exists only for the duration of a runtime session:

| State | Location | Notes |
|-------|----------|-------|
| Runtime context | In-memory | Destroyed on session end |
| LLM context window | Provider memory | Not persisted |
| Per-turn research_context | In-memory | Destroyed on response |
| Session-scoped temporary state | In-memory | Destroyed on session end |

**What this means:** Session is ephemeral. The operator may start a new session and encounter what feels like "forgetting" — but nothing is actually lost, it's just not accessible through the session-keyed layer.

### Timeline State

What persists across sessions as an ordered event log:

| State | Location | Notes |
|-------|----------|-------|
| Timeline events | `.weslr/timelines/tl_default/events.jsonl` | Append-only, timestamped |
| Thread definitions | `weslr/threads.json` | Persistent, survives sessions |
| Artifact files | `continuity/artifacts/*.json` | Persistent, survives sessions |
| Active thread pointer | `weslr/threads.json` (per-user active thread) | Persistent |
| Interest registry | `weslr/interests.json` | Persistent |
| Lineage chains | Artifact metadata (future) | Persistent |

**What this means:** Timeline is the ground truth for what has happened and what exists. Session is just an access path.

### Active Continuity Object

The **active continuity object** is the union of:
1. Active thread (from thread tracker)
2. Most recent artifact in that thread
3. Current interests for this user
4. Operator context (persona, domain, preferences)

**Who sets it:**
- Operator action: explicitly creating artifact, asking about something, marking thread active
- WESLR inference: when user interacts with a thread, that thread becomes active
- Timeline signal: most recent artifact-linked event sets fallback active artifact

**Who clears it:**
- Operator explicitly starts new thread
- Significant time gap with no interaction (configurable threshold)
- Explicit operator action: "let's move to a new topic"

### What the User Should Experience

| Reality | User Experience |
|---------|-----------------|
| New session starts | "Welcome back — what would you like to work on?" (not empty) |
| Ask "improve this" | Works on the thing they were working on, even if session ended and resumed |
| Ask about something new | Resets context appropriately, no contamination from prior work |
| Ask to see revision history | Can see lineage: original → revisions |
| Move to new thread | Active thread shifts; prior thread stays in history |
| Ask "what was I working on" | Can reconstruct from thread history |

### What the User Should NOT Experience

- Needing to re-explain context that is inferable from thread history
- Seeing artifacts from unrelated threads when working in current thread
- "I don't have anything" when they clearly have ongoing work
- References to session IDs, registry keys, or internal state
- Cross-user contamination (seeing another user's artifacts)

---

## SECTION 6 — FORBIDDEN DRIFT

### F1 — No Exposing Brittle Session Semantics to Users
Session IDs, registry keys, session boundaries, and implementation details must never appear in user-facing responses or artifacts. Operators experience continuity, not sessions.

### F2 — No Giant Raw Context as Continuity Substitute
Increasing the LLM context window size is not a substitute for proper continuity resolution. Long context is expensive, slow, and still doesn't solve the reference resolution problem. The resolution model must work within reasonable context sizes.

### F3 — No Silent Cross-User Contamination
Artifact resolution must always respect user scope. An artifact created by User A must never appear as a resolution candidate for User B, even if the system has access to it. Authorization boundaries are non-negotiable.

### F4 — No Replacing Governed Continuity with Prompt Tricks
Continuity resolution is not a prompt engineering problem. "This" should resolve through the model described in Section 3 — using threads, timelines, lineage, and scope — not by stuffing more context into the system prompt. Governance applies to continuity resolution like it applies to all WESLR capabilities.

### F5 — No Implicit Resolution Without Audit Trail
Every resolution should produce a resolution metadata record (Section 4) that can be reviewed. Silent resolutions with no traceability are forbidden. The operator must be able to inspect what resolved "this" and why.

### F6 — No Timeline Rewrite
The timeline event log is append-only. Events are never deleted, reordered, or modified. A resolution that references timeline events is referencing a read-only log.

---

## SECTION 7 — RECOMMENDED FIRST IMPLEMENTATION

### Smallest Safe Step

The first safe implementation is **a thread-aware resolution layer that sits on top of the existing artifact_store registry**, without modifying any existing module.

### Implementation Path

**Step 1: Thread-linked active artifact**

Create `weslr/timeline_resolution.py`:

- Add `thread_id` field to artifact context on creation (link new artifacts to active thread)
- Implement `_resolve_this(user_id)` that queries:
  1. Active thread for user → most recent artifact in thread
  2. If none: fallback to `get_active_artifact(user_id)` (existing registry)
- Return resolution metadata with `resolution_path` (active_thread | registry_fallback | no_candidate)

**Step 2: Thread tracker integration**

`weslr/thread_tracker.py` already stores threads with artifact items. Extend it:
- Add `set_active_thread(user_id, thread_id)` 
- Add `get_active_thread(user_id)` → thread_id or None
- When artifact is created, auto-link it to active thread if one exists

**Step 3: Safe no-resolution handling**

When resolution finds no candidate:
- Return safe empty message (existing behavior preserved)
- Log resolution attempt to timeline with `resolution.failed` event type

**What NOT to modify:**
- `artifact_store.py` — no changes
- `dialogue.py` — no changes  
- `active_artifact_registry.json` — layer on top, not replace
- `threads.json` — extend, don't rewrite

**What this achieves:**
- "improve this" in a new session resolves to latest artifact in active thread (if thread exists)
- Session boundary becomes invisible for ongoing work
- Safe path preserved for fresh sessions
- No cross-user contamination (thread is user-scoped)

**What this does NOT yet solve:**
- Lineage chain tracking (artifacts know their parent)
- Timeline-based fallback (when no active thread)
- Authorization boundaries (institution scope)

These are subsequent slices, each additive, each testable.

---

## SECTION 8 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document was produced by analysis of:
- Existing artifact persistence and registry (`weslr/artifact_store.py`)
- Cross-session eval results (`continuity/artifacts/eval/csc-eval-*.json`)
- Thread tracker architecture (`weslr/thread_tracker.py`)
- Timeline event log (`.weslr/timelines/tl_default/events.jsonl`)
- Institution layer (`weslr/institution.py`)
- Unified continuity (`weslr/unified_continuity.py`)
- Lineage diff (`weslr/lineage_diff.py`)

No code was written. No routing changed. No scoring changed. No governance altered.

If any design decision is incorrect or creates a new failure mode, document it — do not implement around it.

---

*TIMELINE-NATIVE CONTINUITY RESOLUTION V1 — Design Specification*