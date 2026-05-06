# Weslr Voice Layer

Elastic ambient voice presence for Weslr — wise, calm, Gandalf + Optimus Prime blend.

---

## Overview

The voice layer transforms Weslr from a reactive command system into an **ambient intelligence with a voice**. It runs silently in the background, watches for meaningful presence changes, and speaks only when the weighted cognition pipeline decides it's appropriate.

It is **not** a notification bot, a cron reminder, or a hard-coded greeting machine. It is an elastic, autonomous, weighted presence that learns when speaking is welcome.

**Default behavior: WESLR SPEAKS.** The user must explicitly disable voice, not enable it.

---

## Architecture

```
presence_monitor      ← signals: arrival / departure / availability change
       ↓
observation_engine   ← structured events → Observation[]
       ↓
thought_formation   ← Observation[] → Thought[] (candidate utterances)
       ↓
surface_decision    ← Thought → SurfaceDecisionResult (speak_now / defer / dismiss)
       ↓
personality_modulator ← shapes tone, warmth, pace, verbosity
       ↓
voice_output        ← final text + voice parameters
       ↓
tts_engine          ← gTTS / Piper / espeak → audio
       ↓
audio_playback      ← termux-media-player / mpv / ffplay (best-effort)
```

**Key principle:** No module bypasses the pipeline. Every WESLR utterance goes through observation → thought → surface decision → personality → voice output.

---

## Modules

| Module | Role |
|--------|------|
| `presence_monitor.py` | Tracks human arrival/departure/availability. Event-driven via signals. |
| `observation_engine.py` | Converts signals into structured `Observation` records with significance and urgency. |
| `thought_formation.py` | Generates candidate `Thought` utterances from observations. |
| `surface_decision.py` | Weighted gatekeeper: `speak_now` / `defer` / `dismiss`. Decisions are elastic, not rule-based. |
| `personality_modulator.py` | Shapes delivery: tone, warmth, pace, pauses, prefix/suffix. |
| `voice_output.py` | Final output preparation with voice parameters. |
| `tts_engine.py` | Unified TTS interface: gTTS (Android default), Piper, espeak, Dummy. |
| `adaptive_greeting.py` | Context-aware greeting generator — not a script, weighted selection. |
| `elastic_memory.py` | Interaction memory with recency weighting and relationship learning. |
| `onboarding.py` | First-run setup: platform detection, TTS selection, config generation. |
| `voice_config.py` | Permission and preference layer. Controls whether WESLR may speak. |
| `ambient_loop.py` | Background presence loop. Drives the pipeline from presence signals. |

---

## Voice Pipeline

```
Observation → CandidateThought → SurfaceDecision → PersonalityModulator → VoiceOutput → TTS
```

### Running the Pipeline Manually

```bash
python3 weslr/voice_layer/demo_voice_pipeline.py
```

Output (example):
```
STEP 2: Observation — [arrival] source=presence_monitor content=Human arrived home.
STEP 3: Thought Formation — [observation] conf=low, sig=0.4
STEP 4: Surface Decision — decision=defer (low significance)
STEP 5: Personality Modulation + Voice Output
STEP 6: TTS Generation — PIPELINE VERIFIED
```

### Flags

```bash
python3 weslr/voice_layer/demo_voice_pipeline.py --dummy --no-audio   # safe test mode
python3 weslr/voice_layer/demo_voice_pipeline.py --gtts               # real audio on Android
python3 weslr/voice_layer/demo_voice_pipeline.py --gtts --speak       # play audio
```

---

## Ambient Loop

The `AmbientPresenceLoop` is the background process that lets WESLR speak autonomously throughout the day.

**It is not a cron job.** It watches for meaningful presence changes and routes them through the cognition pipeline. WESLR may speak, defer, or stay silent — the pipeline decides.

### Entry Point

```bash
python3 weslr/voice_layer/run_ambient.py                    # loop forever, audio ON
python3 weslr/voice_layer/run_ambient.py --once            # one tick, safe
python3 weslr/voice_layer/run_ambient.py --once --text-only # one tick, audio suppressed
python3 weslr/voice_layer/run_ambient.py --status          # show loop status
python3 weslr/voice_layer/run_ambient.py --daemon           # background daemon
python3 weslr/voice_layer/run_ambient.py --voice-off        # disable voice master switch
python3 weslr/voice_layer/run_ambient.py --voice-on         # re-enable voice
python3 weslr/voice_layer/run_ambient.py --mute 60          # mute for N minutes
```

### What the Loop Detects

- First presence of the day
- Return after absence
- Departure
- System startup / WESLR coming online
- Unusual arrival patterns (tired, stressed)

### What the Loop Does NOT Do

- Speak every N seconds
- Greet every arrival mechanically
- Bypass the observation → thought → decision pipeline
- Use fixed greeting scripts

---

## Voice Control CLI

```bash
python3 weslr/voice_layer/cli_voice.py status
python3 weslr/voice_layer/cli_voice.py on              # enable voice
python3 weslr/voice_layer/cli_voice.py off             # disable voice
python3 weslr/voice_layer/cli_voice.py mute 60        # mute for N minutes
python3 weslr/voice_layer/cli_voice.py unmute          # unmute
python3 weslr/voice_layer/cli_voice.py text-only on    # text-only mode
python3 weslr/voice_layer/cli_voice.py text-only off   # back to voice
python3 weslr/voice_layer/cli_voice.py autonomous off  # disable proactive speech
python3 weslr/voice_layer/cli_voice.py autonomous on   # re-enable
python3 weslr/voice_layer/cli_voice.py quiet-hours set 22:00 07:00
python3 weslr/voice_layer/cli_voice.py quiet-hours on
python3 weslr/voice_layer/cli_voice.py quiet-hours off
python3 weslr/voice_layer/cli_voice.py engine gtts      # set TTS engine
python3 weslr/voice_layer/cli_voice.py cooldown 15     # minutes between utterances
```

---

## Configuration

Settings persist at `~/.weslr/voice_config.json`.

### Defaults

| Setting | Default | Description |
|---------|---------|-------------|
| `voice_enabled` | `true` | Master switch |
| `audio_playback_enabled` | `true` | Play audio through speakers |
| `autonomous_speaking_enabled` | `true` | WESLR initiates speech |
| `ambient_loop_enabled` | `true` | Background presence loop |
| `text_only` | `false` | Suppress audio, keep processing |
| `quiet_hours_enabled` | `true` | Quiet hours active |
| `quiet_hours_start` | `22:00` | Quiet hours start |
| `quiet_hours_end` | `07:00` | Quiet hours end |
| `selected_engine` | `gtts` | TTS engine |
| `cooldown_minutes` | `15` | Min minutes between utterances |
| `first_arrival_greeting_enabled` | `true` | Greet first arrival of day |

### Permission Hierarchy

`speaking_allowed()` returns `True` only when ALL of these are true:
1. `voice_enabled = true`
2. `text_only = false`
3. Not muted
4. Not within quiet hours

---

## TTS Engines

| Engine | Platform | Quality | Cost |
|--------|----------|---------|------|
| **gTTS** | Android (Termux), any internet-connected host | Good | Free |
| Piper | Linux (arm64 cross-compiled) | Very good, local | Free |
| espeak | All platforms | Fair | Free |
| Dummy | Testing | No audio | Free |

Detection order: `gtts → piper → espeak → dummy`

On Android/Termux, gTTS is auto-detected and used by default.

### Installing Playback Support

Audio playback requires a media player on Termux:

```bash
pkg install mpv
```

If no player is available, gTTS generates MP3 correctly but playback degrades gracefully (no crash).

---

## Surface Decision — Weighted Elastic Model

`SurfaceDecisionEngine` is the gatekeeper. Decisions are **weighted, not rule-based**.

Factors considered:
- `confidence` — how certain is the thought?
- `significance` — does it matter enough to interrupt?
- `novelty` — is this a repetition?
- `relationship_depth` — does the relationship support initiative?
- `timing_naturalness` — is this a good moment?
- `interruption_cost` — is the user busy?
- `sensitivity_penalty` — could this be awkward?

The output is a `SurfaceDecision` enum value:
- `speak_now` — approved, proceed
- `defer` — not now, reconsider later
- `save_for_later` — store for future surfacing
- `dismiss` — discard

---

## Adaptive Surface Decision (Phase 4)

SurfaceDecisionEngine uses **weighted adaptive thresholds**, not fixed ones. Before evaluating a thought, it computes effective_threshold from live data:

- weighted_recent_significance(168h) from ElasticMemory — relationship quality over 7 days
- get_ignored_count_24h() — if >3 ignored in 24h, threshold +0.15 (WESLR speaks less)
- Relationship depth — if engagement depth >0.7 and few interactions, threshold -0.10
- Clamped to [0.30, 0.80]



## Cooldown Decay (Phase 4)

Every WESLR utterance has a cooldown. The multiplier scales with user behavior:



Multiplier range: 1.0x - 3.0x. Effective cooldown = config.cooldown_minutes x memory.get_cooldown_multiplier().

## Pending Thought Surfacing (Phase 4)

High-significance thoughts can be queued and delivered when the user returns:



On next arrival, pending thoughts with significance >= 0.7 are run through SurfaceDecisionEngine. If speak_now, they surface before the arrival greeting.

## TTS Playback Detection (Phase 4)



Also available via OnboardingEngine.test_tts_playback(engine_name) — generates a test phrase and returns audio size, duration, and success status.

## Anti-Repetition Greetings (Phase 4)

AdaptiveGreeting tracks the last 3 greeting word prefixes and avoids repeating the same prefix within 24h. Count recent greetings: greeting.get_recent_greeting_count().

## Tests

```bash
# Syntax check all 18 files
python3 -m py_compile weslr/voice_layer/*.py

# Full test suite (13 tests)
python3 weslr/voice_layer/test_voice_pipeline.py

# Ambient loop — one tick, safe
python3 weslr/voice_layer/run_ambient.py --once --text-only

# Ambient loop — one tick, audio ON
python3 weslr/voice_layer/run_ambient.py --once

# Status
python3 weslr/voice_layer/run_ambient.py --status
```

---

## Phase Roadmap

| Phase | Status | Contents |
|-------|--------|---------|
| Phase 1 | ✅ | Core pipeline modules (presence, observation, thought, surface decision, personality, voice output, TTS) |
| Phase 2 | ✅ | Validation, gTTS integration, onboarding, adaptive greeting |
| Phase 2.5 | ✅ | Test fixes, API corrections, demo pipeline |
| Phase 3 | ✅ | Ambient loop, voice config, CLI, `--text-only`, `--voice-off`, quiet hours |
| Phase 4 | ✅ | Relationship depth → surface thresholds, cooldown decay, pending thought surfacing, playback detection, greeting pipeline integration |
| Phase 5 | 🔲 | Microphone / always-listening (requires explicit platform consent) |

---

## Design Principles

1. **Elastic over mechanical** — decisions are weighted, not matched
2. **Structural over rule-based** — pipeline decides, not `if arrival: speak()`
3. **User override always** — any behavior can be disabled or muted
4. **Graceful degradation** — no crash when playback fails; gTTS works without internet at generation time
5. **Ambient by default** — voice is ON unless the user turns it off
6. **No self-modification** — WESLR doesn't change its own behavior permanently from one interaction
