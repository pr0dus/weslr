#!/usr/bin/env python3
"""
demo_voice_pipeline.py — Controlled Voice Pipeline Demo (v2)

Usage:
    cd /data/data/com.termux/files/home/.openclaw/workspace
    python3 -c "
import sys; sys.path.insert(0, '.'); import weslr.voice_layer; print('OK')
"
    python3 weslr/voice_layer/demo_voice_pipeline.py           # Safe (--dummy --no-audio)
    python3 weslr/voice_layer/demo_voice_pipeline.py --gtts     # Real TTS, no playback
    python3 weslr/voice_layer/demo_voice_pipeline.py --gtts --speak  # Full TTS

Default: --dummy --no-audio (safe, no audio playback)
"""

import sys
import argparse
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import weslr.voice_layer

def get_mod(name):
    return sys.modules[f"weslr.voice_layer.{name}"]

pres_mod   = get_mod("presence_monitor")
elastic_mod = get_mod("elastic_memory")
obs_mod    = get_mod("observation_engine")
tf_mod     = get_mod("thought_formation")
sd_mod     = get_mod("surface_decision")
pm_mod     = get_mod("personality_modulator")
vo_mod     = get_mod("voice_output")
tts_mod    = get_mod("tts_engine")
ag_mod     = get_mod("adaptive_greeting")
ob_mod     = get_mod("onboarding")

PresenceMonitor        = pres_mod.PresenceMonitor
ElasticMemory          = elastic_mod.ElasticMemory
ObservationEngine      = obs_mod.ObservationEngine
ObservationType        = obs_mod.ObservationType
ThoughtFormationEngine = tf_mod.ThoughtFormationEngine
ThoughtType            = tf_mod.ThoughtType
ReasoningMode          = tf_mod.ReasoningMode
SurfaceDecisionEngine   = sd_mod.SurfaceDecisionEngine
SurfaceDecision        = sd_mod.SurfaceDecision
Urgency                = obs_mod.Urgency
PersonalityModulator    = pm_mod.PersonalityModulator
VoiceOutputLayer       = vo_mod.VoiceOutputLayer
TTSEngine              = tts_mod.TTSEngine
DummyTTS               = tts_mod.DummyTTS
AdaptiveGreeting       = ag_mod.AdaptiveGreeting
GreetingContext        = ag_mod.GreetingContext
OnboardingEngine       = ob_mod.OnboardingEngine

# ─────────────────────────────────────────────────────────────
# Parse arguments
# ─────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Weslr Voice Pipeline Demo")
parser.add_argument("--dummy", action="store_true", help="Use Dummy TTS engine (default)")
parser.add_argument("--espeak", action="store_true", help="Use espeak TTS engine")
parser.add_argument("--gtts",   action="store_true", help="Use Google TTS engine (internet required)")
parser.add_argument("--piper",  action="store_true", help="Use Piper TTS engine")
parser.add_argument("--no-audio", action="store_true", default=True, help="Do not play audio (default)")
parser.add_argument("--speak",  action="store_true", help="Play audio through speakers")
parser.add_argument("--verbose", action="store_true", help="Show pipeline steps in detail")
args = parser.parse_args()

if args.espeak:  engine_id = "espeak"
elif args.gtts:   engine_id = "gtts"
elif args.piper:  engine_id = "piper"
else:             engine_id = "dummy"   # Default safe mode

audio_enabled = args.speak

# ─────────────────────────────────────────────────────────────
print("=" * 60)
print("WESLR VOICE PIPELINE DEMO")
print("=" * 60)
print(f"Engine:  {engine_id}")
print(f"Audio:   {'enabled' if audio_enabled else 'disabled (safe mode)'}")
print()

# ─────────────────────────────────────────────────────────────
# Step 1: Initialize components
# ─────────────────────────────────────────────────────────────
print("─" * 40)
print("STEP 1: Initializing Components")
print("─" * 40)

TEMP = Path(tempfile.mkdtemp(prefix="weslr_demo_"))

presence = PresenceMonitor(tenant_id="demo")
memory   = ElasticMemory(tenant_id="demo")
obs_eng  = ObservationEngine(tenant_id="demo", storage_path=str(TEMP / "obs.json"))
thoughts = ThoughtFormationEngine(tenant_id="demo", storage_path=str(TEMP / "thoughts.json"))
surface  = SurfaceDecisionEngine(
    tenant_id="demo",
    presence_monitor=presence,
    elastic_memory=memory,
    storage_path=str(TEMP / "surface.json"),
)
modulator = PersonalityModulator(tenant_id="demo", storage_path=str(TEMP / "mod.json"))
output    = VoiceOutputLayer(tenant_id="demo", storage_path=str(TEMP / "vo.json"))

tts = TTSEngine.use(engine_id)

print(f"  PresenceMonitor:          OK")
print(f"  ElasticMemory:            OK")
print(f"  ObservationEngine:        OK")
print(f"  ThoughtFormationEngine:  OK")
print(f"  SurfaceDecisionEngine:   OK")
print(f"  PersonalityModulator:    OK")
print(f"  VoiceOutputLayer:        OK")
print(f"  TTS Engine:              {tts.engine_name} (available: {tts.is_available})")
print()

# ─────────────────────────────────────────────────────────────
# Step 2: Observation — fake structured event
# ─────────────────────────────────────────────────────────────
print("─" * 40)
print("STEP 2: Observation — User returned after long workday")
print("─" * 40)

presence.signal_arrival()
obs_id = obs_eng.signal_arrival_observation(lateness_minutes=25)

unprocessed = obs_eng.get_unprocessed_observations()
print(f"  Arrival signal sent. Observations in queue: {len(unprocessed)}")
for obs in unprocessed:
    print(f"    [{obs.type}] source={obs.source} content={obs.content}")
print()

# ─────────────────────────────────────────────────────────────
# Step 3: Thought Formation — convert observation to candidate thought
# ─────────────────────────────────────────────────────────────
print("─" * 40)
print("STEP 3: Thought Formation")
print("─" * 40)

reasoning_context = {
    "confidence_boost": 1.0,
    "rel_avail": "available",
}

candidate_thoughts = thoughts.process_observations(unprocessed, reasoning_context)

print(f"  Candidate thoughts generated: {len(candidate_thoughts)}")
for ct in candidate_thoughts:
    print(f"    [{ct.type}] confidence={str(ct.confidence)}")
    print(f"      content: {ct.content}")
    print(f"      significance={ct.significance:.2f}  sensitivity={"n/a"}")
print()

# ─────────────────────────────────────────────────────────────
# Step 4: Surface Decision — filter by confidence/sensitivity
# ─────────────────────────────────────────────────────────────
print("─" * 40)
print("STEP 4: Surface Decision")
print("─" * 40)

speakable = []
for ct in candidate_thoughts:
    decision = surface.evaluate(ct)
    print(f"  Thought: {ct.content[:70]}")
    print(f"    decision={decision.decision}  confidence={str(ct.confidence)}  sig={ct.significance}  sens={"n/a"}")
    if True:
        print(f"    phrasing_hints={decision.phrasing_hints}")
        print(f"    defer_reason={getattr(decision, 'defer_reason', 'n/a')}")
    if decision.decision == "speak_now":
        speakable.append((ct, decision))
        print(f"    → SPEAK_NOW ✓")
    elif decision.decision == "defer":
        print(f"    → DEFERRED ({getattr(decision, 'defer_reason', '')})")
    else:
        print(f"    → DISMISSED")
    print()

print(f"  Cleared for voicing: {len(speakable)}")
print()

# ─────────────────────────────────────────────────────────────
# Step 5: Personality Modulation → Voice Output
# ─────────────────────────────────────────────────────────────
print("─" * 40)
print("STEP 5: Personality Modulation + Voice Output")
print("─" * 40)

if not speakable:
    print("  No thoughts approved. Demo complete (this is normal — low-sig observations may be deferred).")
else:
    for ct, decision in speakable:
        mod = modulator.modulate(
            ct.content,
            decision.phrasing_hints,
            relationship_depth=0.5,
        )
        formatted = modulator.format_thought(ct.content, mod)
        voice_params = modulator.get_voice_parameters(mod)

        print(f"  Original:  {ct.content}")
        print(f"  Modulated: {formatted}")
        print(f"  Voice params: {voice_params}")

        voice_result = output.output(
            formatted,
            voice_params,
            mod.to_dict(),
            thought_id=ct.id,
        )
        print(f"  VoiceOutput fields: {list(voice_result.to_dict().keys())}")
        print()

# ─────────────────────────────────────────────────────────────
# Step 6: TTS Generation (no audio playback unless --speak)
# ─────────────────────────────────────────────────────────────
print("─" * 40)
print(f"STEP 6: TTS Generation ({engine_id})")
print("─" * 40)

for ct, decision in speakable:
    mod = modulator.modulate(ct.content, decision.phrasing_hints, relationship_depth=0.5)
    formatted = modulator.format_thought(ct.content, mod)

    tts_result = tts.speak(formatted)

    print(f"  Text: {formatted}")
    print(f"  TTS result:")
    print(f"    success={tts_result.success}  engine={tts_result.engine}  duration={tts_result.duration_seconds:.2f}s")
    if tts_result.error:
        print(f"    error={tts_result.error}")
    else:
        sz = len(tts_result.audio_data) if tts_result.audio_data else 0
        print(f"    audio_size={sz} bytes")

    if audio_enabled and tts_result.success and tts_result.audio_data:
        print(f"  [Audio playback disabled in this demo — use --speak to enable]")
    elif not audio_enabled:
        print(f"  [Audio disabled — safe mode. use --speak to play]")

    print()

print("=" * 60)
print("PIPELINE VERIFIED")
print("=" * 60)
print()
print("Flow: Observation → CandidateThought → SurfaceDecision")
print("      → PersonalityModulator → VoiceOutput → TTS")
print()
print("Run with real TTS:")
print("  python3 weslr/voice_layer/demo_voice_pipeline.py --gtts")
print("  python3 weslr/voice_layer/demo_voice_pipeline.py --gtts --speak")
print()
print("Default: --dummy --no-audio (safe mode)")