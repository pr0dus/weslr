"""
ambient_loop.py — Elastic Ambient Presence Loop for Weslr Voice Layer

This is the background presence loop that lets WESLR speak autonomously.
It is NOT a cron job. It is NOT a rule engine.
It is a weighted, structural decision layer on top of the existing pipeline.

Core principle:
  The loop detects meaningful presence changes and converts them to
  observations → candidate thoughts → surface decisions.
  It does NOT bypass the cognition pipeline.
  It does NOT hard-code greetings or responses.
  SurfaceDecisionEngine decides if/when to speak.

Correct:
  presence_change → observation → candidate → weighted_surface_decision
  → personality_modulation → voice_output → TTS

Wrong:
  if arrival: speak("Good morning.")  ← hard-coded greeting

The loop should feel:
  - organic, not mechanical
  - weighted, not rule-based
  - adaptive, not scripted
  - interruptible at any time

Author: pr0dus / Weslr
v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
import threading
import time as time_module
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports — do NOT pull in heavy Weslr modules
from .presence_monitor import PresenceMonitor, AvailabilityState, TimeContext
from .observation_engine import ObservationEngine, ObservationType, Urgency
from .thought_formation import ThoughtFormationEngine, ReasoningMode, Thought
from .surface_decision import SurfaceDecisionEngine, SurfaceDecision
from .personality_modulator import PersonalityModulator, DeliveryModulation
from .voice_output import VoiceOutputLayer
from .tts_engine import TTSEngine, TTSResult
from .elastic_memory import ElasticMemory
from .adaptive_greeting import AdaptiveGreeting, GreetingContext
from .voice_config import VoiceConfig, load_voice_config


# ============================================================================
# MeaningfulChange — what the loop detects
# ============================================================================

@dataclass
class MeaningfulChange:
    """A presence change that may warrant a WESLR response."""
    change_type: str          # "first_arrival_today", "return_after_absence", "late_arrival", "departure", "system_startup"
    timestamp: str
    arrival_count_today: int
    is_anomaly: bool
    anomaly_description: str
    context_snapshot: Dict[str, Any]


# ============================================================================
# LoopResult — what tick_once() returns
# ============================================================================

@dataclass
class LoopResult:
    """Result of one loop tick."""
    tick_id: str
    timestamp: str
    changes_detected: List[MeaningfulChange]
    thoughts_generated: int
    decisions_made: int
    utterances_considered: int
    utterances_approved: int
    utterances_made: int      # actually spoken
    muted: bool               # was muted at tick time
    quiet_hours: bool         # was in quiet hours at tick time
    speaking_allowed: bool
    duration_ms: float
    error: Optional[str] = None


# ============================================================================
# AmbientPresenceLoop
# ============================================================================

class AmbientPresenceLoop:
    """
    Background presence loop for WESLR ambient voice.

    Does NOT run a fixed schedule. Runs when meaningful changes occur
    or on a slow ticker to catch context shifts.

    Key design:
    - tick_once() does one cycle — fast, testable
    - run_forever() calls tick_once() repeatedly with a configurable interval
    - start()/stop() manage a background thread
    - All speaking decisions go through SurfaceDecisionEngine
    - Audio playback is controlled by VoiceConfig

    The loop is intentionally simple. Complexity lives in the pipeline.
    """

    DEFAULT_TICK_INTERVAL_SECONDS = 30
    FIRST_ARRIVAL_THRESHOLD_MINUTES = 30  # first arrival within 30min of midnight = first of day
    ANOMALY_LATENESS_THRESHOLD_MINUTES = 60  # arrival >60min later than usual

    def __init__(
        self,
        tenant_id: str,
        tick_interval_seconds: int = DEFAULT_TICK_INTERVAL_SECONDS,
        weslr_home: Optional[Path] = None,
    ):
        self.tenant_id = tenant_id
        self.tick_interval = tick_interval_seconds

        # Storage paths
        self._weslr_home = weslr_home or Path.home() / ".weslr"
        self._presence_path = str(self._weslr_home / "presence.json")
        self._obs_path = str(self._weslr_home / "observations.json")
        self._thoughts_path = str(self._weslr_home / "thoughts.json")
        self._surface_path = str(self._weslr_home / "surface.json")
        self._memory_path = str(self._weslr_home / "elastic_memory.json")
        self._greeting_path = str(self._weslr_home / "greeting.json")

        # Config
        self._config: Optional[VoiceConfig] = None

        # State
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_speak_time: Optional[datetime] = None
        self._arrivals_today = 0
        self._first_arrival_of_day_done = False
        self._last_presence_state: Optional[str] = None

        # Pipeline components (lazy init)
        self._presence: Optional[PresenceMonitor] = None
        self._obs_eng: Optional[ObservationEngine] = None
        self._thoughts: Optional[ThoughtFormationEngine] = None
        self._surface: Optional[SurfaceDecisionEngine] = None
        self._output: Optional[VoiceOutputLayer] = None
        self._tts: Optional[TTSEngine] = None
        self._memory: Optional[ElasticMemory] = None
        self._greeting: Optional[AdaptiveGreeting] = None

        # Bookkeeping
        self._tick_count = 0
        self._utterances_made = 0
        self._pending_important_thoughts: List[Thought] = []

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def running(self) -> bool:
        return self._running

    @property
    def utterances_made(self) -> int:
        return self._utterances_made

    # ── Component init (lazy) ──────────────────────────────────────────────

    def _init_components(self) -> None:
        """Lazily initialize pipeline components."""
        if self._presence is not None:
            return
        self._presence = PresenceMonitor(tenant_id=self.tenant_id)
        self._obs_eng = ObservationEngine(
            tenant_id=self.tenant_id,
            storage_path=self._obs_path,
        )
        self._thoughts = ThoughtFormationEngine(
            tenant_id=self.tenant_id,
            storage_path=self._thoughts_path,
        )
        # SurfaceDecisionEngine needs presence + memory
        self._memory = ElasticMemory(tenant_id=self.tenant_id)
        self._surface = SurfaceDecisionEngine(
            tenant_id=self.tenant_id,
            presence_monitor=self._presence,
            elastic_memory=self._memory,
            storage_path=self._surface_path,
        )
        self._mod: Optional[PersonalityModulator] = None
        self._mod = PersonalityModulator(tenant_id=self.tenant_id)
        self._output = VoiceOutputLayer(tenant_id=self.tenant_id)
        self._greeting = AdaptiveGreeting(tenant_id=self.tenant_id)
        # TTS engine — use detected engine or config preference
        config = self._get_config()
        preferred = getattr(config, "selected_engine", "gtts")
        self._tts = TTSEngine.use(preferred) if preferred != "auto" else TTSEngine.detect()

    def _get_config(self) -> VoiceConfig:
        if self._config is None:
            self._config = load_voice_config()
        return self._config

    # ── Presence change detection ───────────────────────────────────────────

    def _detect_changes(self) -> List[MeaningfulChange]:
        """Detect meaningful presence changes since last tick."""
        changes: List[MeaningfulChange] = []
        state = self._presence.get_state()
        now = datetime.now(timezone.utc).isoformat()

        # Departure detection
        if self._last_presence_state == "home" and state.state == "away":
            changes.append(MeaningfulChange(
                change_type="departure",
                timestamp=now,
                arrival_count_today=self._arrivals_today,
                is_anomaly=False,
                anomaly_description="",
                context_snapshot={"state": state.state, "availability": state.availability},
            ))

        # Arrival detection
        elif self._last_presence_state in ("away", "unknown") and state.state == "home":
            self._arrivals_today += 1

            # First arrival of the day?
            is_first_today = self._arrivals_today == 1

            # Anomaly detection (late arrival)
            is_anomaly = False
            anomaly_desc = ""
            if state.availability == "tired" or state.availability == "stressed":
                is_anomaly = True
                anomaly_desc = f"Arrived in {state.availability} state"

            change_type = "first_arrival_today" if is_first_today else "return_after_absence"

            changes.append(MeaningfulChange(
                change_type=change_type,
                timestamp=now,
                arrival_count_today=self._arrivals_today,
                is_anomaly=is_anomaly,
                anomaly_description=anomaly_desc,
                context_snapshot={
                    "state": state.state,
                    "availability": state.availability,
                    "time_context": state.time_context,
                    "confidence": state.confidence,
                    "relationship_depth": state.relationship_depth,
                },
            ))

        # System startup / WESLR online for first time today
        elif self._last_presence_state is None and state.state == "home":
            self._arrivals_today += 1
            changes.append(MeaningfulChange(
                change_type="system_startup",
                timestamp=now,
                arrival_count_today=self._arrivals_today,
                is_anomaly=False,
                anomaly_description="",
                context_snapshot={
                    "state": state.state,
                    "availability": state.availability,
                    "time_context": state.time_context,
                },
            ))

        self._last_presence_state = state.state
        return changes

    # ── Pipeline run ────────────────────────────────────────────────────────

    def _run_pipeline_for_change(
        self,
        change: MeaningfulChange,
    ) -> List[tuple]:
        """
        Run the cognition pipeline for a meaningful change.
        Returns list of (thought, decision, voice_output) tuples that were approved.
        """
        config = self._get_config()
        if not config.autonomous_speaking_allowed():
            return []

        # Create observation from change
        obs_type = ObservationType.ARRIVAL
        if change.change_type == "departure":
            obs_type = ObservationType.DEPARTURE

        obs_id = self._obs_eng.add_observation(
            observation_type=obs_type.value if hasattr(obs_type, 'value') else obs_type,
            source="ambient_loop",
            content=f"WESLR ambient: {change.change_type}",
            significance=0.5,
            urgency=Urgency.LOW,
            metadata=change.context_snapshot,
        )

        # Get unprocessed observations
        unprocessed = self._obs_eng.get_unprocessed_observations()

        # Reasoning context from change
        reasoning_ctx = {
            "confidence_boost": 1.2 if change.is_anomaly else 1.0,
            "rel_avail": change.context_snapshot.get("availability", "available"),
            "change_type": change.change_type,
            "is_first_arrival_today": change.change_type == "first_arrival_today",
        }

        # Generate candidate thoughts
        candidates = self._thoughts.process_observations(unprocessed, reasoning_ctx)

        # Evaluate each candidate through surface decision
        approved = []
        for ct in candidates:
            decision = self._surface.evaluate(ct)
            if decision.decision == SurfaceDecision.SPEAK_NOW.value or decision.decision == "speak_now":
                # Personality modulation
                dm = self._mod.modulate(
                    ct.content,
                    decision.phrasing_hints or {},
                    relationship_depth=change.context_snapshot.get("relationship_depth", 0.5),
                )
                formatted = self._mod.format_thought(ct.content, dm)
                vp = self._mod.get_voice_parameters(dm)
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
                vo = self._output.output(formatted, vp, mod_dict, thought_id=ct.id)
                approved.append((ct, decision, vo))

        # Check pending thoughts on arrival
        if change.change_type in ("first_arrival_today", "return_after_absence", "system_startup"):
            pending_approved = self._surface_pending_thoughts()
            approved.extend(pending_approved)

        return approved

    def _surface_pending_thoughts(self) -> List[tuple]:
        """Run pending high-significance thoughts through surface decision."""
        high_sig_pending = [
            t for t in self._pending_important_thoughts
            if t.significance >= 0.7
        ]
        approved = []
        for thought in high_sig_pending:
            decision = self._surface.evaluate(thought)
            if decision.decision == SurfaceDecision.SPEAK_NOW.value or decision.decision == "speak_now":
                dm = self._mod.modulate(
                    thought.content,
                    decision.phrasing_hints or {},
                    relationship_depth=0.5,
                )
                formatted = self._mod.format_thought(thought.content, dm)
                vp = self._mod.get_voice_parameters(dm)
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
                vo = self._output.output(formatted, vp, mod_dict, thought_id=thought.id)
                approved.append((thought, decision, vo))
                # Remove from pending after surfacing
                self._pending_important_thoughts.remove(thought)
        return approved

    def _speak(self, text: str) -> TTSResult:
        """Generate and optionally play audio. Returns TTSResult."""
        result = self._tts.speak(text)
        if result.success and result.audio_data:
            # Try to play audio if playback is enabled
            config = self._get_config()
            if config.audio_playback_allowed():
                played = self._try_playback(result.audio_data)
                # played flag not stored in TTSResult — handled locally
            else:
                pass
        return result

    def _try_playback(self, audio_data: bytes) -> bool:
        """
        Try to play audio on Termux/Android.
        Backends tried in order: termux-media-player, mpv, ffplay.
        Returns True if playback succeeded, False otherwise.
        """
        import subprocess
        import tempfile

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        backends = [
            ("termux-media-player", ["termux-media-player", "play", temp_path]),
            ("mpv", ["mpv", "--no-video", temp_path]),
            ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_path]),
        ]

        for name, cmd in backends:
            try:
                proc = subprocess.run(cmd, capture_output=True, timeout=10)
                if proc.returncode == 0:
                    Path(temp_path).unlink(missing_ok=True)
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
        return False

    # ── tick_once — core loop body ─────────────────────────────────────────

    def tick_once(self) -> LoopResult:
        """
        Run one loop cycle.
        Fast, synchronous, testable.
        Returns LoopResult with all decisions made.
        """
        import time
        t0 = time.time()
        tick_id = f"tick_{self._tick_count}_{int(t0 * 1000)}"
        self._tick_count += 1

        self._init_components()

        config = self._get_config()
        changes: List[MeaningfulChange] = []
        utterances_considered = 0
        utterances_approved = 0
        utterances_made = 0
        error: Optional[str] = None

        try:
            # Check if loop should run at all
            if not config.ambient_loop_enabled:
                return LoopResult(
                    tick_id=tick_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    changes_detected=[],
                    thoughts_generated=0,
                    decisions_made=0,
                    utterances_considered=0,
                    utterances_approved=0,
                    utterances_made=0,
                    muted=config.is_muted(),
                    quiet_hours=config.is_in_quiet_hours(),
                    speaking_allowed=config.speaking_allowed(),
                    duration_ms=(time.time() - t0) * 1000,
                )

            # Detect presence changes
            changes = self._detect_changes()

            # Process each meaningful change
            all_approved = []
            for change in changes:
                approved = self._run_pipeline_for_change(change)
                all_approved.extend(approved)
                utterances_considered += 1

            utterances_approved = len(all_approved)

            # Speak approved outputs
            if all_approved and config.speaking_allowed():
                # Cooldown check with adaptive multiplier
                effective_cooldown = config.cooldown_minutes * self._memory.get_cooldown_multiplier()
                if self._last_speak_time:
                    elapsed = (datetime.now(timezone.utc) - self._last_speak_time).total_seconds() / 60
                    if elapsed < effective_cooldown:
                        # Skip — too soon since last utterance
                        self._memory.record_outcome("ignored")
                        return LoopResult(
                            tick_id=tick_id,
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            changes_detected=changes,
                            thoughts_generated=len(all_approved),
                            decisions_made=utterances_considered,
                            utterances_considered=utterances_considered,
                            utterances_approved=utterances_approved,
                            utterances_made=0,
                            muted=config.is_muted(),
                            quiet_hours=config.is_in_quiet_hours(),
                            speaking_allowed=config.speaking_allowed(),
                            duration_ms=(time.time() - t0) * 1000,
                        )

                # Actually speak
                for ct, decision, vo in all_approved:
                    result = self._speak(vo.text)
                    if result.success:
                        utterances_made += 1
                        self._last_speak_time = datetime.now(timezone.utc)
                        self._utterances_made += 1
                        self._memory.record_outcome("spoken")

                        # Record in elastic memory
                        self._memory.record(
                            interaction_type="weslr_utterance",
                            content_summary=vo.text[:100],
                            human_reaction="",
                            context_tags=["ambient_utterance", ct.type],
                            significance=ct.significance if hasattr(ct, 'significance') else 0.5,
                        )

        except Exception as e:
            error = str(e)

        return LoopResult(
            tick_id=tick_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            changes_detected=changes,
            thoughts_generated=utterances_approved,
            decisions_made=utterances_considered,
            utterances_considered=utterances_considered,
            utterances_approved=utterances_approved,
            utterances_made=utterances_made,
            muted=config.is_muted(),
            quiet_hours=config.is_in_quiet_hours(),
            speaking_allowed=config.speaking_allowed(),
            duration_ms=(time.time() - t0) * 1000,
            error=error,
        )

    # ── Background loop ────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background loop in a thread."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop_body, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background loop gracefully."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def _loop_body(self) -> None:
        """Internal loop body run in background thread."""
        while not self._stop_event.is_set():
            self.tick_once()
            self._stop_event.wait(timeout=self.tick_interval)

    def run_forever(self, tick_interval: Optional[int] = None) -> None:
        """
        Run the loop in the current thread until stopped.
        Use stop() from another thread to exit.
        """
        if tick_interval is not None:
            self.tick_interval = tick_interval
        self._running = True
        while not self._stop_event.is_set():
            self.tick_once()
            self._stop_event.wait(timeout=self.tick_interval)
        self._running = False

    # ── Status ────────────────────────────────────────────────────────────

    def add_pending_thought(self, thought: Thought) -> None:
        """"Queue a high-significance thought for later surfacing."""
        self._pending_important_thoughts.append(thought)

    def get_pending_count(self) -> int:
        """Return number of pending important thoughts."""
        return len(self._pending_important_thoughts)
        """Return current loop status."""
        config = self._get_config()
        return {
            "running": self._running,
            "tick_count": self._tick_count,
            "utterances_made": self._utterances_made,
            "arrivals_today": self._arrivals_today,
            "last_speak_time": self._last_speak_time.isoformat() if self._last_speak_time else None,
            "last_presence_state": self._last_presence_state,
            "config": config.status(),
        }
