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
| Persistent cross-session memory | ❌ Not implemented | None — no `human_memories/`, no session summary injection |
| Proactive suggestions | 🚧 Partial | `capability_suggestion.py`, `suggestion_bridge.py`, `artificial_analysis_index.py` — infrastructure exists, no unprompted trigger |
| Action execution | ❌ Not implemented | `write_handlers.py` — trace-only, `execution_allowed=False` everywhere |
| Ambient listening / wake word | ❌ Not implemented | No always-on listener, no VAD, no wake-word loop |
| Within-session coreference | ❌ Not implemented | No `interpret_human_turn`, no cross-turn context, no antecedent resolution |
| Everyday NL command routing | ❌ Not implemented | All 30+ handlers are WESLR self-queries; zero external world handlers |

---

## Recommendation

### Single most impactful next step: **Add session summary injection into `/chat` (Area 2)**

Persistent cross-session memory — knowing what the user said *yesterday* — is the single feature that most directly makes WESLR feel like a continuity agent rather than a stateless responder. Without it, every conversation starts from scratch regardless of what was discussed before.

**What this requires:**
1. A `session_summaries/` store (or reuse `memory/` with a naming convention) where each completed session writes a one-paragraph summary.
2. At `/chat` request time, load the last N session summaries and inject them as prefix context before routing.
3. Optionally: a lightweight "what did we discuss last time?" surface that the welcome surface can reference.

This change is low-risk (read-side only, no execution), high-impact (makes every interaction feel continuity-aware), and directly enables the "remember that conversation we had" experience Jarvis has.

Everything else on the Jarvis path — wake word, ambient listening, action execution — requires either additional infrastructure (audio pipeline, external action registry with safety guards) or architectural decisions (execution_allowed policy) that go beyond what can be lightly added. Session summary injection is the highest-leverage, lowest-risk starting point.