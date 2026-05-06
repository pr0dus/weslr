"""
voice_layer — Weslr Elastic Voice Layer

Transforms Weslr from a reactive command system into an ambient intelligence
with a voice — wise, calm, Gandalf + Optimus Prime blend.

Modules:
- personality_profile.json — voice character definition (wise, calm, baritone with bass)
- elastic_memory.py — interaction memory with recency weighting and learning
- presence_monitor.py — human presence detection and availability inference
- adaptive_greeting.py — probabilistic greeting generator
- observation_engine.py — monitors data streams, triggers thought formation
- thought_formation.py — orchestrates existing reasoning toward natural speech
- surface_decision.py — decides if/when/how to voice a thought
- personality_modulator.py — shapes delivery based on personality + relationship
- voice_output.py — TTS integration layer
- tts_engine.py — unified TTS interface with multiple backend support
- onboarding.py — tenant onboarding system with TTS selection

Architecture:
    personality_profile.json → presence_monitor → elastic_memory
                                   ↓
                              observation_engine → thought_formation
                                                             ↓
                                                        surface_decision
                                                             ↓
                                              personality_modulator → voice_output
                                                             ↓
                                                         tts_engine
                                                             ↓
                                                         onboarding

Usage:
    from weslr.voice_layer import (
        PresenceMonitor, ElasticMemory, AdaptiveGreeting,
        ObservationEngine, ThoughtFormationEngine,
        SurfaceDecisionEngine, PersonalityModulator, VoiceOutputLayer,
        TTSEngine, OnboardingEngine,
    )

    # Onboarding (first time setup)
    onboarding = OnboardingEngine(tenant_id="pr0dus")
    state = onboarding.start()
    options = onboarding.execute_step(2, {})  # Get TTS options
    onboarding.execute_step(3, {"tts_engine": "piper"})
    final_config = onboarding.execute_step(6, {})

    # Runtime
    tts = TTSEngine.detect()  # Auto-detect best available
    presence = PresenceMonitor(tenant_id="pr0dus")
    memory = ElasticMemory(tenant_id="pr0dus")
    engine = ObservationEngine(tenant_id="pr0dus")
    thoughts = ThoughtFormationEngine(tenant_id="pr0dus")
    surface = SurfaceDecisionEngine(tenant_id="pr0dus", presence_monitor=presence, elastic_memory=memory)
    modulator = PersonalityModulator(tenant_id="pr0dus")
    output = VoiceOutputLayer(tenant_id="pr0dus")

    # Signal arrival
    presence.signal_arrival()
    engine.signal_arrival_observation(lateness_minutes=25)
    
    # Process observation → thought → surface → modulate → TTS
    observations = engine.get_unprocessed_observations()
    new_thoughts = thoughts.process_observations(observations, reasoning_context)
    for thought in new_thoughts:
        decision = surface.evaluate(thought)
        if decision.decision == "speak_now":
            mod = modulator.modulate(thought.content, decision.phrasing_hints)
            formatted = modulator.format_thought(thought.content, mod)
            voice_params = modulator.get_voice_parameters(mod)
            final = output.output(formatted, voice_params, mod.to_dict(), thought.id)
            
            # Convert to speech
            tts_result = tts.speak(final.text, voice_id="en_US-lessac-medium.onnx")

v1.0 — 2026-05-06
"""

from __future__ import annotations

from .elastic_memory import (
    ElasticMemory,
    InteractionRecord,
    RelationshipState,
    get_elastic_memory,
    save_elastic_memory,
)

from .presence_monitor import (
    PresenceMonitor,
    PresenceState,
    AvailabilityState,
    TimeContext,
    PresenceSnapshot,
    ArrivalPattern,
    get_presence_monitor,
    save_presence_monitor,
)

from .adaptive_greeting import (
    AdaptiveGreeting,
    GreetingContext,
    load_profile,
)

from .observation_engine import (
    ObservationEngine,
    Observation,
    ObservationType,
    ObservationFilter,
    Urgency,
    get_observation_engine,
)

from .thought_formation import (
    ThoughtFormationEngine,
    Thought,
    ThoughtType,
    ThoughtConfidence,
    ReasoningMode,
    ReasoningContext,
    get_thought_formation_engine,
    generate_arrival_thought,
)

from .surface_decision import (
    SurfaceDecisionEngine,
    SurfaceDecisionResult,
    PhrasingHints,
    SurfaceDecision,
    DeferReason,
    get_surface_decision_engine,
)

from .personality_modulator import (
    PersonalityModulator,
    DeliveryModulation,
)

from .voice_output import (
    VoiceOutputLayer,
    VoiceOutput,
    elevenlabs_output,
    system_tts_output,
    get_voice_output,
)

from .tts_engine import (
    TTSEngine,
    TTSEngineBase,
    TTSResult,
    EspeakTTS,
    PiperTTS,
    CoquiTTS,
    DummyTTS,
)

from .onboarding import (
    OnboardingEngine,
    OnboardingState,
    OnboardingConfig,
    OnboardingStep,
    TTSInstallOption,
    OSType,
    OnboardingStage,
    get_onboarding_engine,
)

from .voice_config import (
    VoiceConfig,
    VoiceConfig,
    load_voice_config,
    save_voice_config,
)

from .ambient_loop import (
    AmbientPresenceLoop,
    MeaningfulChange,
    LoopResult,
)

from .local_bridge import (
    send_to_weslr,
    stt_bridge,
)

__all__ = [
    # Elastic memory
    "ElasticMemory",
    "InteractionRecord",
    "RelationshipState",
    "get_elastic_memory",
    "save_elastic_memory",
    # Presence
    "PresenceMonitor",
    "PresenceState",
    "AvailabilityState",
    "TimeContext",
    "PresenceSnapshot",
    "ArrivalPattern",
    "get_presence_monitor",
    "save_presence_monitor",
    # Greeting
    "AdaptiveGreeting",
    "GreetingContext",
    "load_profile",
    # Observation
    "ObservationEngine",
    "Observation",
    "ObservationType",
    "ObservationFilter",
    "Urgency",
    "get_observation_engine",
    # Thought formation
    "ThoughtFormationEngine",
    "Thought",
    "ThoughtType",
    "ThoughtConfidence",
    "ReasoningMode",
    "ReasoningContext",
    "get_thought_formation_engine",
    # Surface decision
    "SurfaceDecisionEngine",
    "SurfaceDecisionResult",
    "PhrasingHints",
    "SurfaceDecision",
    "DeferReason",
    "get_surface_decision_engine",
    # Personality
    "PersonalityModulator",
    "DeliveryModulation",
    # Voice output
    "VoiceOutputLayer",
    "VoiceOutput",
    "elevenlabs_output",
    "system_tts_output",
    "get_voice_output",
    # TTS
    "TTSEngine",
    "TTSEngineBase",
    "TTSResult",
    "EspeakTTS",
    "PiperTTS",
    "CoquiTTS",
    "DummyTTS",
    # Onboarding
    "OnboardingEngine",
    "OnboardingState",
    "OnboardingConfig",
    "OnboardingStep",
    "TTSInstallOption",
    "OSType",
    "OnboardingStage",
    "get_onboarding_engine",
    # Voice config (Phase 3)
    "VoiceConfig",
    "load_voice_config",
    "save_voice_config",
    # Ambient loop (Phase 3)
    "AmbientPresenceLoop",
    "MeaningfulChange",
    "LoopResult",
    # Local bridge (Phase 4)
    "send_to_weslr",
    "stt_bridge",
]