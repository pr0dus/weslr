# WESLR_USER_TIMELINE_MEMORY_V1

**File:** `weslr/user_timeline_memory.py`
**Test:** `weslr/tests/test_user_timeline_memory_v1.py`
**Status:** `IMPLEMENTED EXPERIMENTAL / NOT WIRED TO CHAT`
**Authority:** `user_timeline_memory`

---

## Purpose

First minimal Jarvis-like memory experiment for WESLR.
Append-only user timeline that stores short session summary events.
Gives WESLR the first safe building block for *"I remember what we talked about last time"*.

---

## What It Does

- Stores short, human-authored session summary events in `.weslr/timelines/user_<user_id>/events.jsonl`
- Explicit write only — no automatic runtime call, no chat injection
- Reads and surfaces prior summaries as a continuity note

---

## What It Does NOT Do

- ❌ Does NOT store raw prompts
- ❌ Does NOT store full transcripts
- ❌ Does NOT execute actions
- ❌ Does NOT inject into `/chat`
- ❌ Does NOT implement wake word
- ❌ Does NOT implement reminders/toggles
- ❌ Does NOT call external services (Ollama, HTTP, etc.)
- ❌ Does NOT store hidden learning signals
- ❌ Does NOT modify existing JSONL governance logs

---

## Path Structure

```
.weslr/timelines/user_<normalized_user_id>/events.jsonl
```

Each line is a JSON object with `record_type: "user_session_summary_event_v1"`.

---

## Core Functions

| Function | Description |
|---|---|
| `normalize_user_id(user_id)` | Lowercase, safe filename chars, default `"default_user"` |
| `get_user_timeline_path(user_id, base_dir)` | Returns `.weslr/timelines/user_<id>/events.jsonl` |
| `build_session_summary_event(user_id, summary, source, tags)` | Builds event dict; validates summary |
| `append_session_summary(user_id, summary, source, tags, base_dir)` | Appends one JSONL line; creates dir |
| `load_recent_session_summaries(user_id, limit, base_dir)` | Reads latest N events; skips malformed lines |
| `build_continuity_note(user_id, limit, base_dir)` | Builds human-readable note from summaries |

---

## Event Schema

```json
{
  "record_type": "user_session_summary_event_v1",
  "user_id": "pr0dus",
  "summary": "Completed Jarvis gap assessment — voice I/O, context, proactivity gaps identified",
  "source": "manual",
  "tags": ["jarvis", "gap-assessment"],
  "timestamp": "2026-05-02T14:20:00Z",
  "authority": "user_timeline_memory",
  "automatic_action": false,
  "raw_prompt_stored": false,
  "hidden_learning": false
}
```

---

## Continuity Note Schema

```json
{
  "record_type": "user_continuity_note_v1",
  "user_id": "pr0dus",
  "message": "Last time, we were working on Completed Jarvis gap assessment | Earlier: Phase 1 entity graph complete",
  "events_used": 2,
  "authority": "user_timeline_memory",
  "automatic_action": false,
  "hidden_learning": false
}
```

---

## Rules (Strict)

1. Summary required, max 1000 chars
2. Source must be one of: `manual`, `voice`, `chat`, `operator`
3. `raw_prompt_stored`, `hidden_learning`, `automatic_action` are always `false`
4. No external calls — no Ollama, no HTTP requests
5. Additive only — does not modify existing JSONL governance logs
6. Directory created on demand, never auto-created at import time

---

## Future Roadmap

- **Entity timelines**: extend to store entity interactions over time
- **Chat injection**: surface continuity note at session start (opt-in)
- **Voice summary**: accept voice dictation as summary source
- **Proactive suggestions**: surface timeline-based recommendations via heartbeat

---

## Experiments Not Yet Wired

This module is complete and tested but NOT wired into:
- `/chat` — no automatic continuity note injection
- heartbeat — no proactive surfacing yet
- voice gateway — voice summary not connected
- execution layer — no action triggers

All future wiring requires explicit operator approval and additive-only changes.