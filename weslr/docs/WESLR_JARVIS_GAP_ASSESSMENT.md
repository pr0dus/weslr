# WESLR vs. Jarvis — Capability Gap Assessment

**Date:** 2026-05-02
**Reviewer:** OCC
**Based on:** `weslr/` source tree, commit `484d259`

---

## 1. Voice I/O — Speech-to-Text and Text-to-Speech

**Status: 🚧 Partial**

`weslr/voice_gateway.py` implements the voice gateway (Phase 1A, ~460 lines):
- **STT:** Shim-only. Browser sends `{"type": "transcript"}` JSON in Phase 1A. Real whisper-cli integration is scaffolded (`stt_transcribe()`, whisper.cpp path detection, ffmpeg normalization) but is optional and falls back silently if binaries are missing.
- **TTS:** Not server-side. Browser uses Web Speech API (`speechSynthesis`). WESLR sends `should_speak: true` in response JSON; the browser decides and executes.
- **Transport:** WebSocket on port 8778 (`ws://host:port/ws/voice`), started via `start_voice_gateway()` in a daemon thread.
- **Timeline logging:** `log_voice_event()` writes `voice.message` events to `.weslr/timelines/<timeline_id>/events.jsonl`.

**Verdict:** Voice in/out is scaffolded but relies on browser-side STT/TTS in Phase 1A. Real server-side STT (whisper) is optional/experimental. No wake word, no continuous listening, no VAD (voice activity detection).

---

## 2. Persistent Context Across Sessions

**Status: ❌ Not implemented**

- No `human_memories/` directory exists in the workspace.
- `unified_continuity.py` (518 lines) and `unified_operator_context.py` (386 lines) track system state and operator context, but no mechanism loads a previous conversation's content into the current session context.
- `capability_welcome_surface.py` (442 lines) generates surface text but does not fetch or inject prior session data.
- The `memory/` directory contains session logs, but there is no code that reads yesterday's memory and makes it available to interpretation as rolling context.
- WESLR's session startup reads `SOUL.md`, `USER.md`, and daily memory files — but this is OpenClaw-level bootstrap, not WESLR-specific persistent user memory. The system knows *about* the user from `USER.md` but does not remember *what the user said* in prior conversations beyond what is in daily logs.

**Verdict:** No human-long-term memory store. No session-summary injection into `/chat`. Each `/chat` request is handled in isolation from prior conversational content.

---

## 2b. Timeline-Based Entity Memory (Person / Institution)

**Status: 🚧 Partial — infrastructure exists, not used for human/entity memory**

WESLR already has timeline infrastructure in `.weslr/timelines/`:
- `tl_default/events.jsonl` — voice event log from `voice_gateway.py`
- `timeline_resolution.py` (520 lines) — manages **active threads per user_id**, links artifacts to threads, resolves active artifact per user, checks continuity (`has_continuity()`, `get_continuity_status()`)
- `memory_tiers/l0_identity.json`, `l1_operating.json`, `l2_session.json` — WESLR's own identity/operating/session state tiers

However, this timeline system is used for **WESLR's own artifact and thread continuity** — not for storing a human's model of an external person or institution. The pattern you're describing (a timeline per person/institution that records what was said, what matters, what happened) is not implemented.

**What exists:** Thread registry per user, active artifact resolution, continuity checks.

**What's missing:** Timeline-per-entity for external persons/institutions, event ingestion from `/chat` turns into entity timelines, query by entity name.

**This is a design direction, not a gap in the existing system.** Timelines are a better model than a flat `human_memories/` store — and the existing infrastructure (`timeline_resolution.py`) provides the primitives (thread registry, per-user active thread, continuity status). The missing piece is entity timeline creation and event routing into those timelines.

---

## 3. Proactive Suggestions

**Status: 🚧 Partial**

- `capability_suggestion.py` (store + state machine) and `suggestion_bridge.py` exist — these can surface suggestions, but only in response to user-triggered queries.
- `artificial_analysis_index.py` (AAI) ranks attention items and produces alerts (e.g., `"AAI ALERT: {level_4_count} critical attention item(s) require immediate operator review"` — line 367), but these appear only as in-channel text responses, not as unprompted proactive nudges.
- No background loop or cron job triggers suggestion surfacing without an inbound user message.
- No mechanism like "I noticed you often ask about X, would you like me to…" exists.

**Verdict:** Suggestion infrastructure exists (suggestion store, AAI ranking, surface bridge) but there is no trigger pathway for *unprompted* delivery. Suggestions only appear when explicitly requested or when bundled with a response.

---

## 4. Action Execution Beyond Proposal Creation

**Status: ❌ Not implemented (all writes are trace-only, no execution)**

- `write_handlers.py` has exactly **one** handler: `handle_iss_controlled_proposal_intake()` — converts an ISS gap to a traced proposal in `proposal_trace.jsonl`. It explicitly does **not** execute anything, approve plans, or change system state beyond logging.
- `deterministic_handlers.py` is entirely **read-only**. Every handler builds a response from existing data. `execution_allowed` is explicitly `False` across all handlers.
- `state_checkpoint` confirms: `execution_allowed: False` in the checkpoint system.
- No email sender, no reminder setter, no light toggle, no HTTP action executor, no cron job creator.
- No execution registry or action manifest exists.

**Verdict:** WESLR is strictly a proposal-and-observation system. It can log trace events, but cannot perform external actions. This is an intentional design choice, not a gap waiting to be filled carelessly — but it means Jarvis-style "I'll handle that for you" is not possible in the current architecture.

---

## 5. Ambient Listening / Wake Word

**Status: ❌ Not implemented**

- `voice_gateway.py` requires a browser to connect to its WebSocket. It does not listen on its own.
- No wake-word detection loop (e.g., "Hey WESLR"). No audio threshold trigger. No background audio capture outside of an active WebSocket connection.
- No VAD (voice activity detection) — browser sends audio only when the user explicitly starts a voice session.

**Verdict:** Ambient listening requires a fundamentally different architecture (always-on audio listener, not a connection-initiated gateway). Not present.

---

## 6. Contextual Understanding — Within-Session Coreference

**Status: ❌ Not implemented**

- `capability_router.py` (248 lines) routes user messages to capability paths. No cross-turn context retention mechanism.
- No `interpret_human_turn` function found in the WESLR Python source.
- No coreference resolution ("that thing we talked about"), no antecedent tracking, no within-session rolling context.
- `unified_continuity.py` does not appear to maintain turn-level conversation state.

**Verdict:** Within-session multi-turn understanding is not implemented at the WESLR layer. OpenClaw may handle this at the session level (context window), but WESLR-specific coreference and explicit context chaining is absent.

---

## 7. Natural Language Command Routing (Everyday Actions)

**Status: ❌ Not implemented**

- `deterministic_handlers.py` has 30+ handlers, but all are scoped to WESLR internal queries: `show diagnostics`, `show gaps`, `explain plan`, `what is WESLR`, `how does WESLR improve`, etc.
- No handlers for: `"remind me to buy milk"`, `"what's on my calendar"`, `"turn on the lights"`, `"send an email"`, `"set a timer"`.
- The handlers are about WESLR itself, not about interfacing with the user's world.
- `iss/probe_registry.py` and `iss/probe_planning.py` exist but are internal diagnostic probes, not external action handlers.

**Verdict:** All handlers answer questions *about* WESLR's state. Zero handlers for real-world everyday tasks.

---

## Summary Table

| Area | Status | Key Files |
|------|--------|-----------|
| Voice I/O (STT/TTS) | 🚧 Partial | `voice_gateway.py` — Phase 1A shim, browser-dependent TTS |
| Persistent cross-session memory | ❌ Not implemented | None — no session summary injection into `/chat` |
| Timeline-based entity memory | 🚧 Partial design direction | `timeline_resolution.py` — threads for WESLR artifacts, not external entity histories |
| Proactive suggestions | 🚧 Partial | `capability_suggestion.py`, `suggestion_bridge.py`, `artificial_analysis_index.py` — infrastructure exists, no unprompted trigger |
| Action execution | ❌ Not implemented | `write_handlers.py` — trace-only, `execution_allowed=False` everywhere |
| Ambient listening / wake word | ❌ Not implemented | No always-on listener, no VAD, no wake-word loop |
| Within-session coreference | ❌ Not implemented | No cross-turn context, no antecedent resolution |
| Everyday NL command routing | ❌ Not implemented | All 30+ handlers are WESLR self-queries; zero external world handlers |

---

## Recommendation

### Single most impactful next step: **Entity timeline infrastructure (Area 2 + 2b combined)**

The session summary idea and the timeline-per-entity idea are actually the same underlying need: continuity across sessions with structured recall. The right implementation path:

1. **Use existing `timeline_resolution.py` primitives** — thread registry, per-user active thread, `has_continuity()`, `get_continuity_status()`. These are designed for exactly this.
2. **Create entity timelines** — for each person/institution the user mentions, a timeline under `.weslr/timelines/<entity_id>/events.jsonl` that records what was said, what matters, the relationship state.
3. **Session summary as a special case** — each session produces a summary event that gets appended to the user's own entity timeline (or a special `tl_user_<user_id>`).
4. **Injection at `/chat` time** — load the last N events from the relevant entity timeline(s) and prepend as context before routing.

This makes session continuity and entity memory the same system, built on proven timeline infrastructure rather than a flat summary store. Timelines scale better (you can query a specific person's timeline, not just "the last session") and already have the resolution logic (`timeline_resolution.py`).

Everything else on the Jarvis path — wake word, ambient, action execution — requires additional infrastructure or explicit policy decisions. Entity timelines using existing primitives is the highest-leverage starting point.
---

## 8. Doctrine Findings — What's Allowed vs. Forbidden for Action Execution

**Status: 📜 Doctrine defined, code not implemented for Jarvis-style actions**

**Allowed (by doctrine):**
- `execution_allowed: False` is the system-wide default — writes blocked unless explicit handler enables them
- `write_handlers.py` has exactly one write handler: `handle_iss_controlled_proposal_intake()` → traces ISS gaps to `proposal_trace.jsonl`
- Signal aggregation may surface operator suggestions — not system-executed
- Evidence workspace activated by operator opt-in — read-only exploration only
- Capability suggestions via `suggestion_bridge.py` — only when requested or bundled

**Forbidden (by doctrine):**
- No automatic external action execution (email, calendar, reminders, HTTP calls)
- No direct capability modification without operator-approved proposal
- No raw user input stored or used as learning signal
- No LLM-driven policy decisions
- No signal-triggered direct state modification
- No dynamic threshold adjustment without operator governance
- No cross-session user linking in signal aggregation

**Gap:** Doctrine explicitly blocks action execution. Jarvis-style "I'll handle that for you" is not a missing feature — it is forbidden by design. Enabling it requires: (1) new execution policy doctrine, (2) operator-authorized write handlers per action class, (3) governance wiring. Not a small task.

---

## 9. Signal Pipeline Inventory

**Status: 🚧 Infrastructure exists, pipeline partially wired**

### 9a. Signal Aggregation (WESLR_SIGNAL_AGGREGATION_V1.md — active doctrine)

Signal types: S1 (repeated unknown), S2 (evidence usage), S3 (topic cluster), S4 (frequent fallback), S5 (improvement query), S6 (entity co-occurrence)

Pipeline: user query → interpretation → policy_engine → no handler match → S1; evidence mode → S2; fallback → S4. Signals accumulate → threshold check → surfacing to operator if met.

**Verdict:** S1/S2/S4 recorded. Surfacing trigger (cron + deliver) not wired to any channel.

### 9b. AAI (Artificial Analysis Index) — `artificial_analysis_index.py`

Produces severity-ranked alerts. `level_4_count > 0` → `"AAI ALERT: {level_4_count} critical attention item(s) require immediate operator review"`.

Pipeline: artifacts + attention items → AAI scoring → composite_summary in response → operator alert if level_4_count > 0.

**Verdict:** AAI alerts only in `/chat` response. No separate delivery channel.

### 9c. Insufficiency Patterns — `insufficiency.py`, ISS probes

Pipeline: no handler match → iss.probe_registry → iss.probe_planning → handle_iss_controlled_proposal_intake() → proposal_trace.jsonl.

**Verdict:** ISS writes to `proposal_trace.jsonl`. No readback into proactive surfacing.

### 9d. What Could Connect Them

Missing for proactivity: background daemon that reads signal store, delivery channel (webchat push), operator opt-in, throttle logic.

---

## 10. Artifact Taxonomy

**Status: ✅ All four defined**

| File | Purpose | Read By |
|------|---------|---------|
| `proposal_trace.jsonl` | ISS gaps → proposals | Governance surface, iss/probe_registry |
| `contract_observations.jsonl` | Contract violations | artificial_analysis_index.py, AAI scoring |
| `public_signals.jsonl` | Operator-visible surfacing signals | Operator dashboard (future) |
| `iss_diagnostic_records.jsonl` | ISS probe diagnostics | ISS probe registry, probe planning |

Key distinction: `proposal_trace.jsonl` = internal governance; `public_signals.jsonl` = operator-facing surfacing; `contract_observations.jsonl` = AAI feed (not directly surfaced); `iss_diagnostic_records.jsonl` = probe metadata.

**Verdict:** All four written. None read back into response path.

---

## 11. Proactivity Infrastructure — Daemon vs. On-Request

**Status: 🚧 Partial daemon, no proactive triggers**

### Currently daemon/background:
- `voice_gateway.py` — WebSocket on port 8778, daemon thread
- `unified_continuity.py` — in-memory checkpoint monitor
- OpenClaw heartbeat (HEARTBEAT.md, not WESLR-specific)

### On-request only (requires `/chat`):
- All deterministic handlers, policy engine, interpretation engine
- AAI alerting, signal aggregation, suggestion surface
- ISS probes

### What proactive daemon needs:
1. Signal monitor — periodic read of `public_signals.jsonl`
2. AAI periodic scan — outside `/chat`
3. Delivery channel — webchat push without inbound message
4. Throttle — max N messages/hour
5. Operator opt-in

**Verdict:** No proactive daemon. All WESLR intelligence reactive. Feasible to build on existing signal infrastructure.

---

## Summary Table (updated)

| Area | Status | Key Files | Note |
|------|--------|-----------|------|
| Voice I/O (STT/TTS) | 🚧 Partial | `voice_gateway.py` | Phase 1A shim; browser TTS |
| Persistent cross-session memory | ❌ Not implemented | None | Doctrine allows; code doesn't build yet |
| Timeline-based entity memory | 🚧 Partial | `timeline_resolution.py` | Threads/artifacts exist; entity timelines unwired |
| Proactive suggestions | 🚧 Partial | `capability_suggestion.py` | On-request only; no daemon |
| Action execution | ❌ Not implemented | `write_handlers.py` | Forbidden by doctrine |
| Ambient listening / wake word | ❌ Not implemented | None | Requires always-on audio |
| Within-session coreference | ❌ Not implemented | None | OpenClaw handles context; WESLR has no coreference |
| Everyday NL command routing | ❌ Not implemented | All handlers WESLR self-queries | Doctrine allows expansion; none for external actions |
| Doctrine (allowed/forbidden) | 📜 Defined | Multiple WESLR_*_V1.md | Action execution forbidden by design |
| Signal pipeline | 🚧 Partial | insufficiency.py, AAI, signal store | No proactive surfacing daemon |
| Artifact taxonomy | ✅ Defined | 4 JSONL files | All written; none read back |
| Proactivity infrastructure | 🚧 Partial | `voice_gateway.py` daemon only | Reactive only; proactive daemon missing |

---

## Recommendation (updated)

### Priority 1: Entity Timeline Infrastructure

Combine Area 2 + 2b using `timeline_resolution.py` primitives:
1. Thread registry + per-user active thread + continuity status (exists)
2. Entity timelines under `.weslr/timelines/<entity_id>/events.jsonl`
3. Session summary → user's entity timeline
4. Session start: load last N events → prepend as rolling context
5. Query by entity name → entity-specific history

Uses proven infrastructure, adds doctrine-permitted feature, makes WESLR feel like it knows you.

### Priority 2: Proactivity (if desired)

1. Signal monitor cron job (reads `public_signals.jsonl`)
2. Wire surfacing to webchat via `message` tool
3. Operator throttle/opt-in config
4. Keep operator-facing only to avoid doctrine conflicts

### Priority 3: Action execution (requires explicit operator decision)

1. New execution policy doctrine
2. Operator authorizes `execution_allowed: True` per action class
3. Write handlers with approval gates per action type
4. Governance design task first, implementation second

---

*Assessment expanded: 2026-05-02 17:24 UTC*
