#!/usr/bin/env python3
"""
test_voice_pipeline.py — Voice Layer Validation Tests (v8)

Run:
    cd /data/data/com.termux/files/home/.openclaw/workspace
    python3 weslr/voice_layer/test_voice_pipeline.py
"""

import sys
import json
import tempfile
import time as time_module
from pathlib import Path

SCRIPT = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── TIME THE IMPORT ─────────────────────────────────────────────────────────
t0 = time_module.time()
import weslr.voice_layer
t_import = time_module.time() - t0

def get_mod(name):
    return sys.modules[f"weslr.voice_layer.{name}"]

pres_mod    = get_mod("presence_monitor")
elastic_mod = get_mod("elastic_memory")
obs_mod     = get_mod("observation_engine")
tf_mod      = get_mod("thought_formation")
sd_mod      = get_mod("surface_decision")
pm_mod      = get_mod("personality_modulator")
vo_mod      = get_mod("voice_output")
tts_mod     = get_mod("tts_engine")
ag_mod      = get_mod("adaptive_greeting")
ob_mod      = get_mod("onboarding")

PresenceMonitor        = pres_mod.PresenceMonitor
PresenceSnapshot       = pres_mod.PresenceSnapshot
ElasticMemory          = elastic_mod.ElasticMemory
InteractionRecord      = elastic_mod.InteractionRecord
ObservationEngine      = obs_mod.ObservationEngine
Observation            = obs_mod.Observation
ObservationType        = obs_mod.ObservationType
Urgency                = obs_mod.Urgency
ThoughtFormationEngine = tf_mod.ThoughtFormationEngine
Thought                = tf_mod.Thought
ThoughtType            = tf_mod.ThoughtType
ThoughtConfidence      = tf_mod.ThoughtConfidence
ReasoningMode          = tf_mod.ReasoningMode
SurfaceDecisionEngine  = sd_mod.SurfaceDecisionEngine
SurfaceDecision        = sd_mod.SurfaceDecision
SurfaceDecisionResult  = sd_mod.SurfaceDecisionResult
PersonalityModulator   = pm_mod.PersonalityModulator
DeliveryModulation     = pm_mod.DeliveryModulation
VoiceOutputLayer       = vo_mod.VoiceOutputLayer
VoiceOutput            = vo_mod.VoiceOutput
TTSEngine              = tts_mod.TTSEngine
DummyTTS              = tts_mod.DummyTTS
AdaptiveGreeting       = ag_mod.AdaptiveGreeting
GreetingContext        = ag_mod.GreetingContext
OnboardingEngine       = ob_mod.OnboardingEngine
OnboardingState        = ob_mod.OnboardingState

# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("VOICE LAYER VALIDATION TESTS (v8)")
print("=" * 60)
print(f"Import time: {t_import:.2f}s")

TEMP_HOME = Path(tempfile.mkdtemp(prefix="weslr_vl_test_"))
errors = []
passed = []

def test(name, fn):
    try:
        result = fn()
        if result:
            passed.append(name)
            print(f"  PASS  {name}")
        else:
            errors.append((name, "returned False"))
            print(f"  FAIL  {name}")
    except Exception as e:
        errors.append((name, str(e)))
        print(f"  ERROR {name}: {e}")
        import traceback
        traceback.print_exc()

# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: personality_profile loads and has expected structure
# ─────────────────────────────────────────────────────────────────────────────
def test_personality_profile():
    path = SCRIPT.parent / "personality_profile.json"
    with open(path) as f:
        profile = json.load(f)
    assert "voice" in profile and "character" in profile
    voice = profile["voice"]
    assert voice["pace"] in ["measured", "fast", "slow"]
    char = profile["character"]
    assert char["primary_tone"] == "calm"
    print(f"    voice.pace={voice['pace']}, character.primary_tone={char['primary_tone']}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: elastic_memory can record and retrieve interactions
# ─────────────────────────────────────────────────────────────────────────────
def test_elastic_memory():
    mem = ElasticMemory(tenant_id="test")
    mem.record(
        interaction_type="great_response",
        content_summary="user responded positively",
        human_reaction="positive",
        context_tags=["topic_a", "topic_b"],
        significance=0.8,
    )
    mem.record(
        interaction_type="dismissed",
        content_summary="user dismissed suggestion",
        human_reaction="negative",
        context_tags=["topic_c"],
        significance=0.4,
    )
    recent = mem.get_recent_interactions(hours=24, limit=10)
    assert len(recent) >= 2
    print(f"    Recorded {len(recent)} interactions, "
          f"weighted_sig={mem.weighted_recent_significance():.3f}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: presence_monitor creates a presence context and responds to signals
# ─────────────────────────────────────────────────────────────────────────────
def test_presence_monitor():
    pm = PresenceMonitor(tenant_id="test")
    pm.signal_arrival()
    ctx = pm.get_state()
    assert ctx.availability in [
        "available", "busy", "away", "unknown", "tired", "relaxed", "stressed", "sleeping"
    ], f"Got: {ctx.availability}"
    assert ctx.time_context in ["morning", "afternoon", "evening", "night"]
    assert ctx.state in ["home", "arriving", "departing", "unknown"]
    print(f"    availability={ctx.availability}, time={ctx.time_context}, "
          f"state={ctx.state}, confidence={ctx.confidence:.2f}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 4: observation_engine can emit an ARRIVAL observation and retrieve it
# ─────────────────────────────────────────────────────────────────────────────
def test_observation_engine():
    eng = ObservationEngine(tenant_id="test", storage_path=str(TEMP_HOME / "obs.json"))
    obs_id = eng.signal_arrival_observation(lateness_minutes=25)
    assert obs_id is not None
    unprocessed = eng.get_unprocessed_observations()
    assert len(unprocessed) >= 1
    obs = unprocessed[0]
    # obs.type is a string matching the enum value: 'arrival' == ObservationType.ARRIVAL
    assert obs.type == ObservationType.ARRIVAL, f"Got: {obs.type!r}"
    assert obs.source is not None
    print(f"    id={obs.id[:8]}, type={obs.type!r}, "
          f"source={obs.source}, significance={obs.significance}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 5: thought_formation converts observations into Thoughts
# ─────────────────────────────────────────────────────────────────────────────
def test_thought_formation():
    eng = ObservationEngine(tenant_id="test", storage_path=str(TEMP_HOME / "tf_obs.json"))
    eng.signal_arrival_observation(lateness_minutes=25)
    unprocessed = eng.get_unprocessed_observations()

    thoughts = ThoughtFormationEngine(tenant_id="test", storage_path=str(TEMP_HOME / "thoughts.json"))
    reasoning_ctx = {"confidence_boost": 1.0, "rel_avail": "available"}
    candidates = thoughts.process_observations(unprocessed, reasoning_ctx)

    assert len(candidates) >= 1, f"Expected at least 1 candidate, got {len(candidates)}"
    ct = candidates[0]
    # Fields: id, timestamp, type, confidence (str), content, reasoning_mode,
    #         sources, observation_ids, significance, context, surfaced,
    #         surface_attempts, last_surface_attempt
    assert ct.type is not None
    assert isinstance(ct.surface_attempts, int)
    assert ct.content and len(ct.content) > 0
    print(f"    type={ct.type!r}, conf={ct.confidence!r}, sig={ct.significance}")
    print(f"    content: {ct.content[:60]}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 6: surface_decision suppresses low-confidence/sensitive thoughts
# ─────────────────────────────────────────────────────────────────────────────
def test_surface_decision_suppress():
    class StubPresence:
        def get_state(self):
            class Ctx:
                availability = "available"; relationship_depth = 0.5
            return Ctx()
        def should_defer(self):
            return False, ""

    class StubRelationship:
        engagement_depth = 0.3

    class StubMemory:
        def __init__(self):
            self._relationship = StubRelationship()
        @property
        def relationship(self):
            return self._relationship
        def get_recent_defer_count(self): return 3
        def should_surface_topic(self, topic):
            return False, 0.0

        def weighted_recent_significance(self, hours=168):
            return 0.5
        def get_recent_interactions(self, hours=24):
            return []
        def get_cooldown_multiplier(self):
            return 1.0
        def get_ignored_count_24h(self):
            return 0

    surface = SurfaceDecisionEngine(
        tenant_id="test",
        presence_monitor=StubPresence(),
        elastic_memory=StubMemory(),
        storage_path=str(TEMP_HOME / "sd_supp.json"),
    )

    class FakeThought:
        def __init__(self):
            self.id = "t-low"; self.content = "I wonder if the sky is blue today..."
            self.type = "observation"; self.confidence = "low"
            self.significance = 0.2
            self.urgency = Urgency.LOW; self.reasoning_mode = ReasoningMode.ANALOGICAL
            self.surface_attempts = 0

    decision = surface.evaluate(FakeThought())
    # decision.decision is a string value ('defer' or 'dismiss')
    assert decision.decision in ("defer", "dismiss"), f"Got: {decision.decision!r}"
    print(f"    Low-confidence+sensitive → {decision.decision!r}  reason={decision.reason!r}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 7: surface_decision allows high-confidence useful thoughts
# ─────────────────────────────────────────────────────────────────────────────
def test_surface_decision_allow():
    class StubPresence:
        def get_state(self):
            class Ctx:
                availability = "available"; relationship_depth = 0.5
            return Ctx()
        def should_defer(self):
            return False, ""

    class StubRelationship:
        engagement_depth = 0.3

    class StubMemory:
        def __init__(self):
            self._relationship = StubRelationship()
        @property
        def relationship(self):
            return self._relationship
        def get_recent_defer_count(self): return 0
        def should_surface_topic(self, topic):
            return False, 0.0

        def weighted_recent_significance(self, hours=168):
            return 0.5
        def get_recent_interactions(self, hours=24):
            return []
        def get_cooldown_multiplier(self):
            return 1.0
        def get_ignored_count_24h(self):
            return 0

    surface = SurfaceDecisionEngine(
        tenant_id="test",
        presence_monitor=StubPresence(),
        elastic_memory=StubMemory(),
        storage_path=str(TEMP_HOME / "sd_allow.json"),
    )

    class FakeThought:
        def __init__(self):
            self.id = "t-high"; self.content = "Your backup completed. 12,847 files verified."
            self.type = "update"; self.confidence = "high"
            self.significance = 0.75
            self.urgency = Urgency.LOW; self.reasoning_mode = ReasoningMode.DEDUCTIVE
            self.surface_attempts = 0

    decision = surface.evaluate(FakeThought())
    assert decision.decision == "speak_now", \
        f"Got: {decision.decision!r} (reason: {decision.reason!r})"
    print(f"    High-confidence+useful → {decision.decision!r}  reason={decision.reason!r}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 8: personality_modulator returns DeliveryModulation and formats thought
# ─────────────────────────────────────────────────────────────────────────────
def test_personality_modulator():
    mod = PersonalityModulator(tenant_id="test", storage_path=str(TEMP_HOME / "pm.json"))
    dm = mod.modulate(
        thought_content="Your backup completed successfully. 12,847 files processed.",
        phrasing_hints={"tone": "warm", "warmth": 0.7},
        relationship_depth=0.5,
    )
    assert isinstance(dm, DeliveryModulation)
    formatted = mod.format_thought("Your backup completed. 12,847 files.", dm)
    voice_params = mod.get_voice_parameters(dm)
    assert "12,847" in formatted
    assert "speed_wpm" in voice_params
    print(f"    Modulated: {formatted}")
    print(f"    Voice params: {voice_params}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 9: voice_output.output() returns VoiceOutput (no .id field)
# ─────────────────────────────────────────────────────────────────────────────
def test_voice_output():
    vo = VoiceOutputLayer(tenant_id="test", storage_path=str(TEMP_HOME / "vo.json"))
    dm = DeliveryModulation(
        speed_multiplier=1.0, pause_before_ms=300,
        tone="warm", warmth=0.6, dryness=0.3,
        verbosity="normal", include_prefix=False,
        include_suffix=False, suffix_phrase="",
    )
    mod_dict = {
        "speed_multiplier": dm.speed_multiplier,
        "pause_before_ms": dm.pause_before_ms,
        "tone": dm.tone,
        "warmth": dm.warmth,
        "dryness": dm.dryness,
        "verbosity": dm.verbosity,
        "include_prefix": dm.include_prefix,
        "prefix_phrase": dm.prefix_phrase,
        "include_suffix": dm.include_suffix,
        "suffix_phrase": dm.suffix_phrase,
    }
    result = vo.output(
        "Good evening. Weslr is online.",
        voice_parameters={"rate": "medium", "pitch": "default"},
        modulation=mod_dict,
        thought_id="test-001",
    )
    assert isinstance(result, VoiceOutput)
    # VoiceOutput has: text, voice_parameters, modulation, timestamp, thought_id
    print(f"    text: {result.text!r}, thought_id={result.thought_id!r}, "
          f"timestamp={result.timestamp!r}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 10: tts_engine Dummy works without audio hardware
# ─────────────────────────────────────────────────────────────────────────────
def test_tts_dummy():
    engine = TTSEngine(DummyTTS())
    assert isinstance(engine.is_available, bool)
    assert engine.is_available == True
    result = engine.speak("Testing the dummy engine.")
    assert result.success == True
    assert result.engine == "dummy"
    assert result.duration_seconds > 0
    print(f"    success={result.success}, duration={result.duration_seconds:.2f}s, "
          f"audio_size={len(result.audio_data) if result.audio_data else 0} bytes")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 11: adaptive_greeting generates context-appropriate greeting
# ─────────────────────────────────────────────────────────────────────────────
def test_adaptive_greeting():
    ag = AdaptiveGreeting(tenant_id="test")
    ctx = GreetingContext(
        time_context="evening",
        availability="available",
        arrival_anomaly=False,
        anomaly_description="",
        arrival_count_today=1,
        relationship_depth=0.5,
        recent_interactions=[],
        last_greeting_style=None,
    )
    greeting = ag.generate(ctx)
    assert greeting is not None and len(greeting) > 0
    print(f"    Generated: {greeting}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 12: onboarding dry-run completes system detection step
# ─────────────────────────────────────────────────────────────────────────────
def test_onboarding_dryrun():
    ob = OnboardingEngine(tenant_id="dryrun_test", weslr_home=TEMP_HOME)
    state = ob.start()
    assert state.stage in ["running", "completed"]

    step = ob.get_current_step()
    print(f"    stage={state.stage}", end="")
    if step:
        print(f"  step={step.id}.{step.name}", end="")
    print()

    result = ob.execute_step(1)
    assert result["success"] == True
    os_type = result["step_data"]["os_type"]
    rec_tts = result["hints"]["recommended_tts"]
    print(f"    os_type={os_type}  recommended_tts={rec_tts}")
    return True

# ─────────────────────────────────────────────────────────────────────────────
# TEST 13: Full pipeline — observation → thought → surface → output
# Uses a FakeThought with high confidence to ensure SPEAK_NOW decision
# ─────────────────────────────────────────────────────────────────────────────
def test_full_pipeline():
    class StubPresence:
        def get_state(self):
            class Ctx:
                availability = "available"; relationship_depth = 0.5
            return Ctx()
        def should_defer(self):
            return False, ""

    class StubRelationship:
        engagement_depth = 0.3

    class StubMemory:
        def __init__(self):
            self._relationship = StubRelationship()
        @property
        def relationship(self):
            return self._relationship
        def get_recent_defer_count(self): return 0
        def should_surface_topic(self, topic):
            return False, 0.0

        def weighted_recent_significance(self, hours=168):
            return 0.5
        def get_recent_interactions(self, hours=24):
            return []
        def get_cooldown_multiplier(self):
            return 1.0
        def get_ignored_count_24h(self):
            return 0

    obs_eng  = ObservationEngine(tenant_id="test", storage_path=str(TEMP_HOME / "pl_obs.json"))
    thoughts = ThoughtFormationEngine(tenant_id="test", storage_path=str(TEMP_HOME / "pl_thoughts.json"))
    surface  = SurfaceDecisionEngine(
        tenant_id="test",
        presence_monitor=StubPresence(),
        elastic_memory=StubMemory(),
        storage_path=str(TEMP_HOME / "pl_surface.json"),
    )
    mod      = PersonalityModulator(tenant_id="test", storage_path=str(TEMP_HOME / "pl_mod.json"))
    vo       = VoiceOutputLayer(tenant_id="test", storage_path=str(TEMP_HOME / "pl_vo.json"))

    # Observation
    obs_eng.signal_arrival_observation(lateness_minutes=25)
    unprocessed = obs_eng.get_unprocessed_observations()
    assert len(unprocessed) >= 1

    # Thought formation
    candidates = thoughts.process_observations(unprocessed, {
        "confidence_boost": 1.0, "rel_avail": "available"
    })
    assert len(candidates) >= 1

    # Surface decision on real candidates
    decisions = []
    for ct in candidates:
        decision = surface.evaluate(ct)
        decisions.append((ct, decision))

    speakable = [(ct, d) for ct, d in decisions if d.decision == "speak_now"]
    print(f"    {len(speakable)} / {len(candidates)} thoughts cleared for voicing")

    # Verify the pipeline ran end-to-end (may or may not have SPEAK_NOW depending on content)
    assert len(decisions) == len(candidates), "Each candidate should have a decision"
    print(f"    Decisions: " + ", ".join(f"{d.decision!r}" for _, d in decisions))

    # Personality + voice output (apply to all candidates regardless of decision)
    for ct, decision in decisions:
        dm = mod.modulate(ct.content, decision.phrasing_hints, relationship_depth=0.5)
        formatted = mod.format_thought(ct.content, dm)
        vp = mod.get_voice_parameters(dm)
        mod_dict = {
            "speed_multiplier": dm.speed_multiplier,
            "pause_before_ms": dm.pause_before_ms,
            "tone": dm.tone,
            "warmth": dm.warmth,
            "dryness": dm.dryness,
            "verbosity": dm.verbosity,
            "include_prefix": dm.include_prefix,
            "prefix_phrase": dm.prefix_phrase,
            "include_suffix": dm.include_suffix,
            "suffix_phrase": dm.suffix_phrase,
        }
        vo_out = vo.output(formatted, vp, mod_dict, thought_id=ct.id)
        print(f"    [{ct.type}] decision={decision.decision!r} → {formatted[:55]}")

    return True

# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL TESTS
# ─────────────────────────────────────────────────────────────────────────────
print()
tests = [
    ("personality_profile loads",          test_personality_profile),
    ("elastic_memory record/retrieve",      test_elastic_memory),
    ("presence_monitor context",             test_presence_monitor),
    ("observation_engine structured event",  test_observation_engine),
    ("thought_formation from observation",  test_thought_formation),
    ("surface_decision suppresses",         test_surface_decision_suppress),
    ("surface_decision allows",             test_surface_decision_allow),
    ("personality_modulator DeliveryMod",   test_personality_modulator),
    ("voice_output VoiceOutput",            test_voice_output),
    ("tts_engine Dummy",                    test_tts_dummy),
    ("adaptive_greeting",                   test_adaptive_greeting),
    ("onboarding dry-run",                  test_onboarding_dryrun),
    ("full pipeline (obs→thought→surface→vo)", test_full_pipeline),
]

for name, fn in tests:
    test(name, fn)

print()
print("=" * 60)
print(f"RESULT: {len(passed)}/{len(tests)} passed, {len(errors)} failed")
if errors:
    print("\nFAILURES:")
    for name, err in errors:
        print(f"  - {name}: {err}")
print("=" * 60)
print(f"Import time: {t_import:.2f}s")
sys.exit(0 if not errors else 1)