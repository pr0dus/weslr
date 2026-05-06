"""
surface_decision.py - Surface decision engine for Weslr voice layer

Decides if/when/how a thought should be voiced to the human.
Orchestrates presence check + significance + timing + phrasing.

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from .thought_formation import Thought, ThoughtType, ThoughtConfidence, ReasoningMode
from typing import Any, Callable, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================

class SurfaceDecision(str, Enum):
    SPEAK_NOW = "speak_now"
    DEFER = "defer"
    SAVE_FOR_LATER = "save_for_later"
    DISMISS = "dismiss"


class DeferReason(str, Enum):
    HUMAN_BUSY = "human_busy"
    HUMAN_TIRED = "human_tired"
    HUMAN_ABSENT = "human_absent"
    LOW_SIGNIFICANCE = "low_significance"
    RECENT_SURFACE = "recent_surface"
    ALREADY_SURFACED = "already_surfaced"
    TOPIC_Dismissed = "topic_dismissed"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SurfaceDecisionResult:
    """Result of surface decision."""
    decision: str                      # SurfaceDecision value
    reason: str                        # Why this decision
    defer_until: Optional[str] = None   # ISO timestamp to reconsider
    phrasing_hints: Dict[str, Any] = field(default_factory=dict)  # Hints for personality_modulator
    urgency_override: bool = False      # Override deferral for high urgency
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "defer_until": self.defer_until,
            "phrasing_hints": self.phrasing_hints,
            "urgency_override": self.urgency_override,
        }


@dataclass
class PhrasingHints:
    """Hints for how to phrase the thought."""
    lead_with: str = "observation"      # "observation", "question", "offer"
    tone: str = "calm"                 # "calm", "urgent", "warm", "measured"
    include_context: bool = True
    max_statements: int = 3
    ask_before_elaborate: bool = False
    prefix: Optional[str] = None        # e.g., "I've been thinking..."
    suffix: Optional[str] = None         # e.g., "...if you're interested."


    def to_dict(self) -> Dict[str, Any]:
        return {
            "lead_with": self.lead_with,
            "tone": self.tone,
            "include_context": self.include_context,
            "max_statements": self.max_statements,
            "ask_before_elaborate": self.ask_before_elaborate,
            "prefix": self.prefix,
            "suffix": self.suffix,
        }


# ============================================================================
# SURFACE DECISION ENGINE
# ============================================================================


class SurfaceDecisionEngine:
    """
    Surface decision — decides if/when/how to voice a thought.
    
    This is the gatekeeper. A thought is formed but not yet spoken.
    This engine evaluates:
    - Is the human available? (defer if busy/tired/absent)
    - Is the significance high enough?
    - Has this been surfaced recently?
    - Is the timing right?
    - How should it be phrased?
    
    Key principle: Deference is paramount. Weslr would rather
    miss an opportunity to speak than interrupt something important.
    """

    def __init__(
        self,
        tenant_id: str,
        presence_monitor,  # PresenceMonitor instance
        elastic_memory,    # ElasticMemory instance
        storage_path: Optional[Path] = None,
        adaptive_threshold: bool = True,
    ):
        self.tenant_id = tenant_id
        self.presence_monitor = presence_monitor
        self.elastic_memory = elastic_memory
        self.storage_path = storage_path
        self._lock = threading.Lock()
        
        # Tracking for deferral decisions
        self._recent_surface_times: Dict[str, str] = {}  # thought_id → timestamp
        self._defer_counts: Dict[str, int] = {}           # thought_id → defer count
        
        # Thresholds
        self._min_significance = 0.35
        self._min_significance_urgent = 0.6
        self._defer_cooldown_minutes = 15
        self._max_defers_before_save = 3

        # Adaptive threshold settings
        self._adaptive_threshold = adaptive_threshold
        self._threshold_multiplier = 1.0

    def evaluate(
        self,
        thought,
        context: Optional[Dict[str, Any]] = None,
    ) -> SurfaceDecisionResult:
        """
        Evaluate whether a thought should be surfaced now.
        Returns SurfaceDecisionResult.
        """
        ctx = context or {}
        
        # 1. Check presence — most important
        defer_signal, defer_reason = self.presence_monitor.should_defer()
        if defer_signal:
            return self._defer(
                thought,
                defer_reason,
                defer_until=self._compute_defer_time(defer_reason),
            )
        
        # 2. Check significance (adaptive threshold)
        effective_threshold = self._get_adaptive_threshold()
        if thought.significance < effective_threshold:
            if thought.urgency in ("high", "critical"):
                pass  # Override for urgent
            else:
                return self._defer(
                    thought,
                    DeferReason.LOW_SIGNIFICANCE.value,
                    defer_until=self._compute_defer_time(DeferReason.LOW_SIGNIFICANCE.value),
                )
        
        # 3. Check recent surfacing
        if thought.id in self._recent_surface_times:
            last_surface = self._parse_timestamp(self._recent_surface_times[thought.id])
            if last_surface:
                minutes_since = (datetime.now(timezone.utc) - last_surface).total_seconds() / 60
                if minutes_since < self._defer_cooldown_minutes:
                    return self._defer(
                        thought,
                        DeferReason.RECENT_SURFACE.value,
                        defer_until=self._compute_defer_time(DeferReason.RECENT_SURFACE.value),
                    )
        
        # 4. Check if already surfaced (with attempts)
        if thought.surface_attempts >= 2:
            return self._defer(
                thought,
                DeferReason.ALREADY_SURFACED.value,
                defer_until=None,  # Save for later, don't retry
            )
        
        # 5. Check topic dismissal history
        topic_dismissed, confidence = self.elastic_memory.should_surface_topic(thought.content[:50])
        if not topic_dismissed and thought.significance < 0.7:
            return self._defer(
                thought,
                DeferReason.TOPIC_Dismissed.value,
                defer_until=self._compute_defer_time(DeferReason.TOPIC_Dismissed.value),
            )
        
        # 6. Evaluate phrasing hints based on presence state
        presence_state = self.presence_monitor.get_state()
        phrasing_hints = self._evaluate_phrasing(thought, presence_state)
        
        # 7. Special handling for arrival thoughts
        if thought.type == ThoughtType.OBSERVATION.value and "arrival" in str(thought.observation_ids):
            phrasing_hints.lead_with = "greeting"
            phrasing_hints.include_context = False
        
        # PASS — speak now
        return SurfaceDecisionResult(
            decision=SurfaceDecision.SPEAK_NOW.value,
            reason="conditions_met",
            phrasing_hints=phrasing_hints.to_dict(),
        )

    def _defer(
        self,
        thought,
        reason: str,
        defer_until: Optional[str] = None,
    ) -> SurfaceDecisionResult:
        """Generate deferral decision."""
        # Track defer count
        self._defer_counts[thought.id] = self._defer_counts.get(thought.id, 0) + 1
        
        # If too many defers, save for later
        if self._defer_counts[thought.id] >= self._max_defers_before_save:
            return SurfaceDecisionResult(
                decision=SurfaceDecision.SAVE_FOR_LATER.value,
                reason=reason,
                defer_until=None,
            )
        
        return SurfaceDecisionResult(
            decision=SurfaceDecision.DEFER.value,
            reason=reason,
            defer_until=defer_until,
        )

    def _compute_defer_time(self, reason: str) -> str:
        """Compute when to reconsider based on defer reason."""
        now = datetime.now(timezone.utc)
        
        # Base defer times by reason
        defer_minutes = {
            DeferReason.HUMAN_BUSY.value: 30,
            DeferReason.HUMAN_TIRED.value: 60,
            DeferReason.HUMAN_ABSENT.value: 120,
            DeferReason.LOW_SIGNIFICANCE.value: 45,
            DeferReason.RECENT_SURFACE.value: 15,
            DeferReason.ALREADY_SURFACED.value: 0,  # Don't re-retry
            DeferReason.TOPIC_Dismissed.value: 120,
        }
        
        minutes = defer_minutes.get(reason, 30)
        defer_time = now.replace(second=0, microsecond=0)
        
        return defer_time.isoformat().replace("+00:00", "Z")

    def _parse_timestamp(self, ts: str) -> Optional[datetime]:
        """Parse ISO timestamp."""
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None

    def _evaluate_phrasing(
        self,
        thought,
        presence_state,
    ) -> PhrasingHints:
        """Determine phrasing hints based on thought type and presence state."""
        hints = PhrasingHints()
        
        # Base tone on thought type and presence
        if thought.confidence == ThoughtConfidence.HIGH.value:
            hints.tone = "measured"
        elif thought.confidence == ThoughtConfidence.MEDIUM.value:
            hints.tone = "calm"
        elif thought.confidence == ThoughtConfidence.LOW.value:
            hints.tone = "careful"
        else:
            hints.tone = "speculative"
        
        # Urgency overrides tone
        if thought.urgency in ("high", "critical"):
            hints.tone = "controlled"
            hints.max_statements = 2
        
        # Availability affects phrasing
        if presence_state.availability == "tired":
            hints.max_statements = 1
            hints.ask_before_elaborate = True
            hints.lead_with = "brief"
        
        # Thought type determines lead
        if thought.type == ThoughtType.INSIGHT.value:
            hints.lead_with = "observation"
        elif thought.type == ThoughtType.QUESTION.value:
            hints.lead_with = "question"
        elif thought.type == ThoughtType.OFFER.value:
            hints.lead_with = "offer"
        elif thought.type == ThoughtType.CONCERN.value:
            hints.lead_with = "observation"
            hints.tone = "caring"
        elif thought.type == ThoughtType.FOLLOW_UP.value:
            hints.prefix = "Earlier you mentioned..."
        
        # High relationship depth → more warmth
        if self.elastic_memory.relationship.engagement_depth > 0.7:
            if hints.tone == "calm":
                hints.tone = "warm"
        
        return hints

    def on_surface_attempt(self, thought_id: str) -> None:
        """Record surface attempt time."""
        with self._lock:
            self._recent_surface_times[thought_id] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def on_surface_success(self, thought_id: str) -> None:
        """Record successful surface."""
        with self._lock:
            self._recent_surface_times[thought_id] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def get_pending_deferred(self) -> List[Dict[str, Any]]:
        """Get thoughts that were deferred and might be ready now."""
        now = datetime.now(timezone.utc).timestamp()
        pending = []
        
        # Check elastic memory follow-ups
        follow_ups = self.elastic_memory.get_follow_ups(max_results=3)
        for item in follow_ups:
            pending.append({
                "type": "follow_up",
                "content": item["content"],
                "priority": item["priority"],
            })
        
        return pending

    def _get_adaptive_threshold(self) -> float:
        """Compute adaptive significance threshold based on recent interaction history."""
        if not self._adaptive_threshold:
            return self._min_significance

        # Base threshold from weighted recent significance (7 days)
        base_threshold = self.elastic_memory.weighted_recent_significance(hours=168)

        
        # Get ignored/dismissed count in last 24h
        recent = self.elastic_memory.get_recent_interactions(hours=24)
        ignored_count = sum(1 for i in recent if i.human_reaction in ("ignored", "dismissed"))
        
        # Adjustment based on ignored interactions
        adjustment = 0.0
        if ignored_count > 3:
            adjustment = 0.15  # Human is ignoring us more → be more selective
        elif ignored_count < 1 and self.elastic_memory.relationship.engagement_depth > 0.7:
            adjustment = -0.10  # High engagement, no recent ignores → be more conversational
        
        # Combine base and multiplier
        threshold = base_threshold * self._threshold_multiplier + adjustment
        
        # Clamp to valid range
        return max(0.30, min(0.80, threshold))

    def set_surface_threshold(self, multiplier: float) -> None:
        """Adjust the threshold multiplier directly."""
        with self._lock:
            self._threshold_multiplier = max(0.5, min(2.0, multiplier))


# ============================================================================
# STORE
# ============================================================================

_surface_store: Dict[str, SurfaceDecisionEngine] = {}
_surface_lock = threading.Lock()


def get_surface_decision_engine(
    tenant_id: str,
    presence_monitor,
    elastic_memory,
    storage_path: Optional[Path] = None,
) -> SurfaceDecisionEngine:
    """Get or create surface decision engine. Thread-safe."""
    global _surface_store
    
    key = f"{tenant_id}"
    
    with _surface_lock:
        if key in _surface_store:
            return _surface_store[key]
    
    engine = SurfaceDecisionEngine(
        tenant_id=tenant_id,
        presence_monitor=presence_monitor,
        elastic_memory=elastic_memory,
        storage_path=storage_path,
    )
    with _surface_lock:
        _surface_store[key] = engine
    return engine