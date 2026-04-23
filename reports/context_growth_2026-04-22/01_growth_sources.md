# Context Growth Sources — Ranked

## Ranked List (strongest to weakest suspected growth contribution)

### 1. Chat History (session JSONL) — STRONGEST GROWTH SOURCE
- **Current active session:** `55a1f787-ce89-4c63-bade-978cd58112fc.jsonl` → 266,571 bytes (~267KB) and growing
- This is the **primary ongoing context growth driver**
- Every message pair adds to this file
- Sessions are stored as JSONL, appended on every exchange
- Old session files in `/agents/main/sessions/` total **~214MB** of historical data

### 2. MEMORY.md — STATIC BUT LARGE
- 17,330 bytes (~17KB) injected at every bootstrap
- Loaded once at startup, not continuously
- Does NOT grow during sessions
- Already truncated 30% in bootstrap injection — original is much larger
- Verdict: **startup cost only, not ongoing growth**

### 3. Session-Memory Hook — MODERATE ONGOING
- `hooks.internal.entries.session-memory.enabled: true`
- Reads session context on heartbeats (~every 30 min)
- Likely aggregates session state summaries
- Can grow if session state accumulates new fields over time
- Risk: moderate — may inject redundant state on each heartbeat

### 4. HEARTBEAT.md — MINIMAL
- Only contains comments (empty, no tasks)
- Even if populated, would inject at heartbeat intervals only
- **Current state: effectively zero burden**

### 5. Workspace State Files (dashboard_history.json, continuation_notes.json)
- `dashboard_history.json`: 59,609 bytes — large but mostly static
- `continuation_notes.json`: 37,046 bytes — narrative/continuity notes
- `state_core.json`: 14,570 bytes — session state snapshot
- These are referenced but not necessarily fully injected into context
- **Assessment: moderate bootstrap cost, not strong ongoing growth**

### 6. Skills Snapshot in sessions.json
- `sessions.json` contains full skills snapshot for the active session
- Skills list (~11 skills) is injected as part of session bootstrap
- Small fixed cost, does not grow

---

## Startup-Only vs. Ongoing-Growth Classification

| Source | Type | Growth? |
|--------|------|--------|
| MEMORY.md | Startup | No (static) |
| HEARTBEAT.md | Both | No (currently empty) |
| Skills snapshot | Startup | No (fixed size) |
| session-memory hook | Ongoing | Yes (heartbeat-triggered) |
| Chat history (JSONL) | Ongoing | Yes (per message) |
| dashboard_history.json | Startup | No (mostly static) |
| continuation_notes.json | Startup | No (manually updated) |

---

## Strongest Suspected Source of Long-Session Bloat

**Chat history (session JSONL)** — every message pair appended to the active session file. In a long session with many exchanges, this grows linearly and is always in context scope for the current session. This is the most likely cause of progressive context pressure over hours of use.
