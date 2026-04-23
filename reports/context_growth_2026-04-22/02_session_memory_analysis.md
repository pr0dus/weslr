# Session-Memory Analysis

## What Is session-memory?

The `session-memory` hook (`hooks.internal.entries.session-memory`) is an internal OpenClaw hook that reads session context and makes it available during the session. It is enabled by default and triggers on heartbeats.

## Session-Memory Role

- Loads session context on heartbeat intervals (~every 30 minutes)
- Provides continuity between messages within a session
- Aggregates session state: active threads, recent decisions, narrative markers
- Exposes state from `continuity/latest.json`, `continuity/metrics.json`, and similar files

## Duplication Risk

**HIGH duplication risk:**
- Session-memory likely re-injects information already present in:
  - `continuity/latest.json` (1,178 bytes)
  - `continuity/metrics.json` (274 bytes)
  - `continuity/history.json` (77 bytes)
  - `narrative_state` fields from state_core
- These files are small and static — session-memory may just be re-serializing them on each heartbeat
- If the hook reads these files and injects them as context text, it adds redundant context repeatedly

## Growth Risk

- Session-memory itself does not grow — it reads static files
- However, `continuity/latest.json` and `state_core.json` can accumulate new fields over sessions
- If these files are being written to by other parts of the system (self-mod, agents, etc.), each heartbeat could see an ever-growing state payload
- Current state: small files, minimal growth risk right now

## Verdict: Safe to Leave On For Now

- Session-memory overhead is low (small JSON files, heartbeat-triggered)
- Disabling it could break continuity features without clear benefit
- The duplication concern is speculative — needs code-level inspection to confirm
- **Not the primary context growth driver based on current file sizes**
