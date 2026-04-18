# VOICE_SYSTEM_STANDARD_V1 — WESLR Voice System Contract

## 1. Purpose

This document defines the authoritative voice system architecture for WESLR.
It locks the v1 technical decisions, sets scope boundaries, and defines the
evolution path. All voice system development must conform to this document.
Changes require an operator-approved update to this file.

---

## 2. Decision Lock — V1

These decisions are final for v1. Do not revisit without operator approval.

| Decision | Choice | Rationale |
|---|---|
| STT | **`whisper-cli`** (local subprocess, `ggml-base.bin`) | Zero cloud cost. Runs offline. ffmpeg pre-normalizes any browser audio format to 16kHz mono WAV before transcription. |
| TTS | **Web Speech API** (browser-native) | Zero setup. Works immediately. No server infrastructure. |
| Transport | **WebSocket** — shared for binary audio + JSON text-chat | One connection carries both binary audio frames and JSON `chat_text`/`chat_text_response` frames. Text chat reuses the same `/chat` logic as HTTP. |
| Interaction model | **Push-to-talk** | Primary v1. Human presses button to speak, releases to send. Wake word is v2+. |
| Text input | **`chat_text` frame** over same WS connection | Typing sends `{"type":"chat_text","text":"..."}` — reuses WESLR `/chat` logic. |
| Latency target | **4-7 seconds** end-to-end | Realistic for browser + local STT + WESLR /chat. |

### Why Not coqui-ai XTTS / Silero VAD Yet

These are the right long-term choices but are not v1:
- **coqui-ai XTTS** requires GPU for real-time synthesis. Adds infrastructure complexity before voice is validated.
- **Silero VAD** is excellent for turn detection but adds complexity. PTT handles turn detection in v1.

**Whisper.cpp** is now in production (Phase 1C): `whisper-cli` runs locally as a subprocess with `ggml-base.bin`. ffmpeg pre-normalizes browser audio (OGG/WebM) to 16kHz mono WAV before transcription. No cloud API required.

Web Speech API is the browser-native TTS that works *today*. XTTS and Silero VAD are v2 upgrade candidates.

---

## 3. License and Dependency Awareness

### Active External Dependencies

| Dependency | Type | Risk | Mitigation |
|---|---|---|---|
| **whisper-cli** (local) | STT (via ffmpeg + ggml-base.bin) | No cloud dependency. Offline-capable. | Cloud STT only if local STT fails. |
| **Web Speech API** | Browser-native TTS | Inconsistent across browsers (Chrome best, Safari limited) | XTTS local fallback in v2 |

### Future Dependencies (v2+)

| Dependency | Type | Status |
|---|---|---|
| **coqui-ai XTTS** | Local TTS | Not in scope v1. Requires GPU. MIT license. |
| **Silero VAD** | Local VAD | Not in scope v1. Apache 2.0 license. |
| **Whisper.cpp** | Local STT fallback | Not in scope v1. MIT license. |

No commercial licenses required for v1 components.

### GPU Requirements — V1 vs Future

One of the practical benefits of the v1 decision lock is that **GPU is not required**.

| Component | V1 Approach | Local GPU needed? |
|---|---|---|
| **LLM (WESLR reasoning)** | API-based (Groq/cloud) | No |
| **STT (speech-to-text)** | whisper-cli + ggml-base.bin (local) | No |
| **TTS (text-to-speech)** | Web Speech API (browser) | No |
| **Voice Gateway** | Python WebSocket server | No |
| **Future local TTS (coqui-ai XTTS)** | Local inference | **Yes — GPU strongly recommended, CPU acceptable with quantize=q8_0** |
| **Future local VAD (Silero)** | Local inference | **No — runs on CPU or WebAssembly** |

**What this means for the WESLR server:** A standard VPS or Termux device with no GPU is sufficient to run the full v1 voice system. The voice gateway and WESLR itself do not need a GPU.

**When GPU becomes relevant:** Only when coqui-ai XTTS becomes the primary TTS engine (v2). XTTS with `--quantize q8_0` on a modern CPU (4+ cores) produces acceptable quality without a GPU, but a GPU significantly improves synthesis speed.

**Storage note:** Groq Whisper requires an API key and sends audio to Groq's servers. If privacy of voice data is a concern, the local Whisper.cpp fallback (v2) addresses this without GPU requirements.

---

## 4. Latency Roadmap

```
V1 — 4–7s round-trip (acceptable)
  └── whisper-cli STT (local) + Web Speech API + /chat on cloud LLM
       Best case: 3s. Worst case: 10s.

V2 — 2–4s round-trip (optimization)
  └── whisper-cli with ggml-tiny.en.bin (77MB, faster) + coqui-ai XTTS local
       Best case: 1.5s. Worst case: 5s.

V3 — <2s round-trip (advanced streaming)
  └── Silero VAD (no button needed) + partial transcript streaming
       + coqui-ai XTTS streaming + WESLR /chat with streaming inference
       Best case: <1s. Worst case: 3s.
```

**The 4–7s target is acceptable because:**
- WESLR's responses are typically short (1-3 sentences)
- Short responses synthesize in <1s via Web Speech API
- The human is driving or hands-busy — millisecond latency is not the UX constraint
- Operator can always fall back to text

---

## 5. Architecture Direction

### Server-First Voice System

```
[Browser / Phone]          [WESLR Server]              [External]
       │                         │                           │
       │ WebSocket (binary + JSON)                           │
       │ ───────────────────────► │                           │
       │                         ▼                           │
       │                  [Voice Gateway]                    │
       │                         │                           │
       │                         ├──► whisper-cli STT       │
       │                         │    (ffmpeg WAV normalize) │
       │                         │                           │
       │                         ├──► /chat (text + WS)     │
       │                         │                           │
       │  ◄───────────────────────│                           │
       │   JSON voice response    │                           │
       │   or chat_text_response │                           │
       │                         ▼                           │
       │                  [Timeline Logger]                  │
       │                  .weslr/timelines/                  │
```

**Core principle:** WESLR is the intelligence. The browser/phone is a terminal — it captures audio and plays back audio. All reasoning, transcription, and synthesis happens on the server.

**Phone / browser as dumb client only:**
- No local AI processing
- No local STT or TTS in v1 (Web Speech API is browser-native)
- Client role: mic → raw audio → WebSocket → receive response → TTS playback
- Client role (Phase 2): text → `chat_text` JSON frame → WebSocket → receive response → TTS playback

---

## 6. Scope Boundaries — V1

### Phase 2 — Shared Text+Voice WS Transport (Implemented)

One shared WebSocket connection carries both binary audio and JSON text-chat frames.

**Supported WS frame types:**

Client → Server (binary):
- Raw `ArrayBuffer` (MediaRecorder output) — browser sends OGG/WebM audio directly. Server runs ffmpeg → WAV → whisper-cli.

Client → Server (JSON):
- `{"type": "chat_text", "text": "..."}` — typed text from Satellite UI or any WS client. Reuses `/chat` logic via `weslr_chat()`.
- `{"type": "start"}` — begin voice turn (existing)
- `{"type": "transcript", "text": "...", ...}` — legacy shim transcript frame (existing)
- `{"type": "end"}` — end voice turn (existing)

Server → Client (JSON):
- `{"type": "ready", "connection_id": "..."}` — connection established
- `{"type": "response", "text": "...", "should_speak": bool}` — voice transcript response (binary path)
- `{"type": "chat_text_response", "text": "...", "source": "..."}` — text-chat response (Phase 2)
- `{"type": "error", "message": "..."}` — bounded error, does not break session

**Shared `/chat` routing:** HTTP `/chat`, WS `transcript`, and WS `chat_text` all call the same `weslr_chat()` function. Internal capability routing (time, status, health, capability) applies equally across all three entrypoints.

**Validated demux (Phase 2.1):** JSON text frame → binary WAV frame → JSON text frame on one connection — all three steps confirmed working with no interference.

**UI exposure:** Satellite UI (`/satellite`) uses the shared WS connection for both text input (`chat_text`) and microphone (`binary ArrayBuffer`). Same `ws://host:8778` endpoint.

## 6. Scope Boundaries — V1

These are **explicitly not in scope** for v1. Do not build them.

| Not included | Reason | Future phase |
|---|---|---|
| **Wake word** | Adds infrastructure. PTT is simpler and more reliable. | v2 |
| **Speaker diarization** | Requires diarization model. Not needed for single-operator use. | v2+ |
| **Anti-spoofing / ASVspoof** | ASV detection model adds weight. `trust_level: unverified` on all voice is sufficient for v1. | v3 |
| **AI voice auditing** | Research product. Not a v1 concern. | v4 |
| **Local STT (Whisper.cpp)** | GPU or 2× real-time CPU. Not needed until Groq cost becomes an issue. | v2 |
| **Local TTS (coqui-ai XTTS)** | GPU required. Web Speech API is sufficient for v1 quality needs. | v2 |
| **Real-time VAD (Silero)** | PTT handles turn detection without additional model. | v2 |
| **Multi-speaker support** | Single operator is v1 use case. | v2+ |
| **Mobile native app** | Browser is sufficient. Native app is v3+. | v3 |
| **Voice cloning** | Fine for personalization but adds ethical complexity. | v4+ |

---

## 7. Event Architecture

Voice inputs produce the same event structure as text, with modality-specific fields:

```json
{
  "event_type": "voice.message",
  "channel": "voice",
  "data": {
    "transcription": "string",
    "language": "en",
    "confidence": 0.94,
    "duration_s": 2.3,
    "turn_id": "string",
    "stt_provider": "shim" (text-injection) or "whisper-cli" (real STT, Phase 1C+)
  },
  "frame": "string",
  "source": "operator",
  "trust_level": "operator_verified",
  "metadata": {
    "tts_used": false,
    "response_message_id": "string"
  }
}
```

Voice events use the same `timeline_id` as text events. The `channel` field differentiates modality. Trust behavior: v1 = all authenticated voice sessions are `operator_verified`. Future trust levels require speaker verification.

---

## 8. Evolution Rules

Future voice improvements must follow these rules:

1. **Update this document first.** No voice feature ships before this document is updated to reflect it.
2. **Maintain WESLR compatibility.** Voice must integrate via the existing event/timeline/trust architecture — not bypass it.
3. **Preserve the server-first principle.** No local AI on the client unless explicitly approved.
4. **Latency is a feature.** Every phase improvement should target the latency roadmap above.
5. **Trust is additive.** New trust levels (speaker_verified, synthetic_suspected) must be added to the charter, not just to the code.
6. **No breaking changes to the event schema** without a schema migration strategy.

---

## 9. Related Documents

- `docs/REPO_HYGIENE_STANDARD_V1.md` — .weslr/ boundary contract
- `docs/UI_SATELLITE_STANDARD_V1.md` — Satellite UI contract
- `docs/APPROVAL_GATED_SELF_IMPROVEMENT_LOOP_V1.md` — Self-modification governance
- `.weslr/charter.json` — Charter (trust levels, principles)
- `RELEASES.md` — Version history and rollback map

---

_Evolves when operator approves a new voice phase. Do not edit without operator approval._
