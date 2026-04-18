# WESLR System Readiness Audit — 2026-04-18

## SECTION 1 — WORKING DEFINITION

A working WESLR means:
- Server starts and serves HTTP + WebSocket endpoints ✅
- `/chat` produces meaningful, context-aware responses (not just template fallbacks) ❌
- Voice pipeline transcribes and responds end-to-end ❌ (no live mic test, but code path exists)
- Shared WS transport demultiplexes binary + JSON on one connection ✅
- Satellite UI renders and accepts input ✅
- Internal capability routing (time/status/health) works via WESLR's own modules ✅
- Cross-path architectural coherence: HTTP /chat and WS path converge on same function ✅
- No single-layer failure breaks the whole system ✅
- System is safe to continue building on (governance in place) ✅

**Bottom line:** WESLR runtime works. WESLR intelligence is partial.

---

## SECTION 2 — LAYER EVALUATION

### A) Runtime / Serving
**Status:** ✅ WORKING
**Evidence:** `{"healthy": true, "version": "0.8.0", "uptime_s": 407}` on port 8001. Voice WS on port 8778. Satellite UI at `/satellite`.
**Confidence:** High. Stable process, clean startup, no crashes.
**Limitations:** `initialized: false` and `provider_available: false` — failsafe not bootstrapped, no external LLM.

---

### B) Canonical /chat — Internal Routing
**Status:** ✅ WORKING FOR SYSTEM FACTS, ❌ BROKEN FOR GENERAL REASONING
**Evidence:**
- `"what time is it"` → `"It is 23:51 local time (Europe/Berlin)."` ✅
- `"what is your system status"` → `"I am initialized. LLM provider: embedded."` ✅
- `"are you healthy"` → `"Running in GUIDED mode. All systems operational."` ✅
- `"tell me a short story about the moon"` → `"I'm here. Say something simple..."` ❌
- Regression tests: 9/9 pass ✅
**Confidence:** High for system facts. Low for general reasoning.
**Limitations:** All non-system prompts fall through to `_get_language_module().simple_response()` — no LLM reasoning for general questions. `provider_available: false` means no external LLM is connected. The "embedded" provider appears to be the template/shim response.

---

### C) Voice Pipeline
**Status:** ⚠️ PARTIALLY VALIDATED
**Evidence:** Phase 1A-1F tests confirm binary audio path, ffmpeg WAV normalization, whisper-cli STT, TTS response, timeline events all work. `stt_transcribe()` uses real whisper-cli. E2E tests passed for Phase 1A-1D.
**Confidence:** Code path validated. Live mic not tested in this session.
**Limitations:** No live microphone test in this session. Voice response quality depends on whisper-cli model (ggml-base.bin, 147MB).

---

### D) WS Shared Transport (Phase 2)
**Status:** ✅ WORKING
**Evidence:** Port 8778 open. `chat_text` frame added. Demux validated (binary WAV → JSON text → binary → JSON text, all on one connection).
**Confidence:** High. Phase 2.1 test confirmed demux.
**Limitations:** `chat_text` response quality limited by same LLM issue as /chat.

---

### E) Satellite/Demo UI
**Status:** ✅ WORKING
**Evidence:** `curl /satellite` returns HTML. Labels updated to Phase 2. Text input sends `chat_text` frame. TTS rendering active.
**Confidence:** High.
**Limitations:** No interactive demo tested (requires browser).

---

### F) Internal Capability Routing
**Status:** ✅ WORKING (for the 5 capabilities wired)
**Evidence:** time, status, health, capability (status path), greeting — all route to internal modules. 9 regression tests pass.
**Confidence:** High for wired capabilities.
**Limitations:** ~30+ capabilities identified in audit, only 5 are `/chat`-wired. Gap analysis documents the delta.

---

### G) Cross-Path Architectural Coherence
**Status:** ✅ STRUCTURALLY COHERENT, ⚠️ FUNCTIONALLY INCOMPLETE
**Evidence:** HTTP `/chat`, WS `chat_text`, WS `transcript` all converge on `build_communicator_message_payload()` via `weslr_chat()`. Phase 2 confirmed one shared connection for both binary and JSON. Dialogue.py has rich internal routing (introspection, valence, entity graph, consciousness, internal docs) that the sim.py CLI path does not use.
**Confidence:** High for structure. Low for completeness.
**Limitations:** Two paths (`build_communicator_message` in sim.py vs `build_communicator_message_payload` in dialogue.py) have asymmetric capability integration. research_context promotion is Step 1 of 5 migration steps.

---

### H) Legacy/Dormant Risk
**Status:** ⚠️ MANAGEABLE BUT VISIBLE
**Evidence:** `get_current_year()` (sim.py:87) has zero call sites. `adaptive_guidance.py` has test file but no main path integration. `capability_intake.py` dormant. `background_analysis/` directory exists but no `/chat` integration. Governance modules (change_proposals, cdi_proposal_builder) are operator-only.
**Confidence:** Medium.
**Limitations:** Accumulated dormant code creates confusion about what is active vs legacy. Clean separation needed.

---

### I) Buildability / Safety to Continue Development
**Status:** ✅ SAFE TO CONTINUE
**Evidence:** Clear phase structure (Phase 1 voice, Phase 2 text-chat). Regression tests in place. Docs updated. Governance exists. No safety-critical bugs observed in runtime behavior.
**Confidence:** High.
**Limitations:** Must not mistake "some things work" for "system works" — the LLM reasoning gap is the main blocker for general usefulness.

---

## SECTION 3 — VERDICT

**WESLR works partially.**

It works as an entity intelligence platform with governed self-assessment, working internal routing for time/status/health, a functional voice pipeline, and a coherent shared WebSocket transport. Its structural foundations are sound — the phase architecture, regression tests, boundary docs, and internal routing are all real and validated.

It does not yet work as a general reasoning assistant because the LLM integration is not active (`provider_available: false`). Non-system questions receive template fallbacks, not genuine reasoning. The gap between "system fact responses work" and "general conversation works" is large and fundamental.

**Strongest argument it works:** `curl "what time is it"` returns a real clock value — not a generic fallback. That response proves the internal routing chain, datetime module, `/chat` handler, and response pipeline are all connected and working together. The 9-pass regression suite pins this.

**Strongest argument it is incomplete:** A user who asks "tell me a short story about the moon" gets `"I'm here. Say something simple..."` — the same generic fallback as a greeting. WESLR has the infrastructure for intelligence but lacks the intelligence engine for general reasoning. This is not a wiring problem; it is a missing dependency (no external LLM active).

---

## SECTION 4 — READINESS SCORE

| Dimension | Score | Notes |
|---|---|---|
| **Runtime validity** | 85/100 | Server healthy, ports 8001/8778 open, no crashes. `initialized: false` is a flag, not a blocker. |
| **Interaction validity** | 75/100 | System fact routing works (time/status/health/greeting). General reasoning broken (LLM unavailable). 9/9 regression tests pass. |
| **Capability integration** | 55/100 | 5 capabilities reliably /chat-wired out of ~30 identified. Gap analysis documents delta. Two-path asymmetry still present. |
| **Architectural coherence** | 70/100 | Shared WS transport works. HTTP + WS converge on same function. Research context added. Two-path divergence understood, not yet resolved. |
| **Trustworthiness for development** | 80/100 | Governance in place. Regression tests. Phase structure clear. Docs updated. No safety-critical bugs observed. |
| **TOTAL** | **73/100** | Functional core, incomplete intelligence layer |

**Reading:** 73/100 means "functional prototype with verified working parts, limited general-purpose capability."

---

## SECTION 5 — MAIN BOTTLENECK

**The LLM reasoning layer is not active.**

`provider_available: false` means no external LLM is connected. Every `/chat` prompt that doesn't match an internal routing pattern falls through to `_get_language_module().simple_response()` — a static template, not reasoning. This is not a wiring problem; the routing infrastructure is correct. The problem is that the reasoning engine itself is not running.

This is the single bottleneck: without an active LLM, WESLR can answer "what time is it?" but cannot reason about "explain quantum entanglement to me" or generate a coherent short story.

---

## SECTION 6 — EXACT_NEXT_STEP

Activate the LLM provider (Groq or local Ollama) so non-system `/chat` prompts receive genuine reasoning responses instead of `simple_response()` fallbacks, while preserving all existing internal routing for time/status/health/capability/system questions.

This is the single change that transforms WESLR from "working infrastructure with template responses" to "working intelligence with genuine reasoning."