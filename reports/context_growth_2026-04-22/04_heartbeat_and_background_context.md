# Heartbeat / Background Context Analysis

## Heartbeat Configuration

- `HEARTBEAT.md` is **empty** (comments only) — currently no task list
- `hooks.internal.entries.session-memory.enabled: true` — session-memory runs on heartbeats
- Heartbeat interval: ~30 minutes (OpenClaw default)

## What Happens on Each Heartbeat

1. Agent receives a heartbeat poll
2. Agent reads `HEARTBEAT.md` — if empty, returns `HEARTBEAT_OK`
3. If `HEARTBEAT.md` has tasks, agent processes them
4. `session-memory` hook reads session context files and injects

## Current Burden Assessment

| Component | Burden | Notes |
|-----------|--------|-------|
| HEARTBEAT.md | **Zero** | Empty file — no task processing |
| session-memory hook | **Low-Medium** | Small JSON reads on heartbeat |
| Skills snapshot refresh | **Zero** | Fixed at session start |

## Is Heartbeat a Major Context Growth Cause?

**No.** Based on current evidence:

1. `HEARTBEAT.md` is empty — heartbeat currently does minimal work
2. `session-memory` reads small JSON files (~1-2KB total) on each heartbeat
3. Even if heartbeat ran 10 times, the added context is negligible compared to:
   - Session chat history (267KB and growing)
   - MEMORY.md (17KB, once)
   - Bootstrap file injection

## Verdict

- Heartbeat burden is **mostly harmless** in the current configuration
- If `HEARTBEAT.md` were populated with many tasks, burden could increase
- But with an empty HEARTBEAT.md, heartbeat is not the context growth driver

## Is This a Meaningful Problem?

**No.** Heartbeat is not meaningfully contributing to context growth in the current state.
