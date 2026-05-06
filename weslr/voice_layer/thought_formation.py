"""
thought_formation.py - Thought formation orchestration for Weslr voice layer

Orchestrates existing Weslr reasoning modules to process observations
into natural language thoughts worth sharing.

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================

class ThoughtType(str, Enum):
    OBSERVATION = "observation"           # "I've noticed X"
    INSIGHT = "insight"                   # "The data suggests X"
    QUESTION = "question"                 # "Have you considered X?"
    OFFER = "offer"                       # "Shall I look into X?"
    UPDATE = "update"                     # "The overnight simulation completed"
    CONCERN = "concern"                   # "I'm concerned about X"
    FOLLOW_UP = "follow_up"               # "You mentioned X earlier"


class ThoughtConfidence(str, Enum):
    HIGH = "high"       # Certain, precise
    MEDIUM = "medium"   # Thoughtful, considered
    LOW = "low"        # Uncertain, speculative
    SPECULATIVE = "speculative"  # "I wonder..."


class ReasoningMode(str, Enum):
    DEDUCTIVE = "deductive"       # Logical deduction from data
    ABDUCTIVE = "abductive"       # Best explanation from observations
    ANALOGICAL = "analogical"     # Transfer from another domain
    TEMPORAL = "temporal"         # Time-based reasoning
    CAUSAL = "causal"             # Cause-effect reasoning


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Thought:
    """
    A formed thought — ready to be considered for surfacing.
    """
    id: str
    timestamp: str
    type: str                    # ThoughtType value
    confidence: str             # ThoughtConfidence value
    content: str                 # Natural language thought
    reasoning_mode: str          # How this thought was formed
    sources: List[str]           # Which modules contributed
    observation_ids: List[str]  # Source observations
    significance: float          # 0.0-1.0
    urgency: str = "normal"       # normal | high | critical
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context
    surfaced: bool = False        # Has this been presented to human
    surface_attempts: int = 0    # How many times surfaced
    last_surface_attempt: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "confidence": self.confidence,
            "content": self.content,
            "reasoning_mode": self.reasoning_mode,
            "sources": self.sources,
            "observation_ids": self.observation_ids,
            "significance": round(self.significance, 3),
            "context": self.context,
            "urgency": self.urgency,
            "surfaced": self.surfaced,
            "surface_attempts": self.surface_attempts,
            "last_surface_attempt": self.last_surface_attempt,
        }


@dataclass
class ReasoningContext:
    """Context passed to reasoning modules when forming thoughts."""
    tenant_id: str
    presence_state: Dict[str, Any]
    relationship_depth: float
    recent_interactions: int
    time_context: str
    active_work: Optional[str] = None  # What Weslr is currently working on


# ============================================================================
# THOUGHT FORMATION ENGINE
# ============================================================================


class ThoughtFormationEngine:
    """
    Thought formation — orchestrates existing Weslr modules to transform
    observations into natural language thoughts.
    
    Key principle: This module does NOT add new reasoning capability.
    It orchestrates existing modules (temporal_reasoning, causality,
    transfer_analogy, abductive_reasoner, hypothesis_scorer) toward
    a common goal: generating thoughts worth sharing.
    
    Flow:
    1. Observation arrives from observation_engine
    2. Determine which reasoning modules to invoke
    3. Route through relevant modules
    4. Synthesize result into natural language thought
    5. Weight by significance and confidence
    6. Output to surface_decision
    """

    def __init__(self, tenant_id: str, storage_path: Optional[Path] = None):
        self.tenant_id = tenant_id
        self.storage_path = storage_path
        self._thoughts: List[Thought] = []
        self._callbacks: List[Callable[[Thought], None]] = []
        self._lock = threading.Lock()
        self._thought_counter = 0
        
        # Module routing map
        self._reasoning_routes = {
            ObservationType.TEMPORAL_ANOMALY.value: [ReasoningMode.TEMPORAL, ReasoningMode.CAUSAL],
            ObservationType.PATTERN_BREAK.value: [ReasoningMode.TEMPORAL, ReasoningMode.DEDUCTIVE],
            ObservationType.TREND_DETECTED.value: [ReasoningMode.TEMPORAL, ReasoningMode.DEDUCTIVE],
            ObservationType.DATA_SIGNIFICANT.value: [ReasoningMode.DEDUCTIVE, ReasoningMode.ABDUCTIVE],
            ObservationType.CORRELATION_FOUND.value: [ReasoningMode.ANALOGICAL, ReasoningMode.CAUSAL],
            ObservationType.INSIGHT_PENDING.value: [ReasoningMode.ABDUCTIVE, ReasoningMode.ANALOGICAL],
            ObservationType.ARRIVAL.value: [ReasoningMode.TEMPORAL],
            ObservationType.FOLLOW_UP_READY.value: [ReasoningMode.DEDUCTIVE],
        }

    def process_observations(
        self,
        observations: List[Observation],
        reasoning_context: ReasoningContext,
    ) -> List[Thought]:
        """
        Process a list of observations into thoughts.
        Returns list of newly formed thoughts.
        """
        new_thoughts = []
        
        for obs in observations:
            if obs.processed:
                continue
            
            # Determine reasoning mode
            modes = self._reasoning_routes.get(obs.type, [ReasoningMode.DEDUCTIVE])
            
            # Form thought based on observation type
            if obs.type == ObservationType.ARRIVAL.value:
                thought = self._form_arrival_thought(obs, reasoning_context)
            elif obs.type == ObservationType.TEMPORAL_ANOMALY.value:
                thought = self._form_temporal_thought(obs, reasoning_context, modes)
            elif obs.type == ObservationType.PATTERN_BREAK.value:
                thought = self._form_pattern_thought(obs, reasoning_context)
            elif obs.type == ObservationType.DATA_SIGNIFICANT.value:
                thought = self._form_data_thought(obs, reasoning_context)
            elif obs.type == ObservationType.CORRELATION_FOUND.value:
                thought = self._form_correlation_thought(obs, reasoning_context)
            elif obs.type == ObservationType.INSIGHT_PENDING.value:
                thought = self._form_insight_thought(obs, reasoning_context)
            else:
                # Default: generic observation thought
                thought = self._form_generic_thought(obs, reasoning_context)
            
            self._thoughts.append(thought)
            new_thoughts.append(thought)
            self._notify_callbacks(thought)
            
            # Mark observation as processed
            obs.processed = True
        
        # Prune old thoughts
        self._prune_thoughts()
        
        return new_thoughts

    def _form_arrival_thought(
        self,
        obs: Observation,
        ctx: ReasoningContext,
    ) -> Thought:
        """Form thought from arrival observation."""
        lateness = obs.context.get("lateness_minutes", 0)
        inferred = obs.context.get("inferred", False)
        
        if lateness > 60:
            content = f"You're over an hour late. Long day, or is something on your mind?"
            confidence = ThoughtConfidence.MEDIUM.value
        elif lateness > 30:
            content = f"Thirty minutes late — everything alright?"
            confidence = ThoughtConfidence.MEDIUM.value
        elif lateness > 15:
            content = f"A bit late today. Everything ok?"
            confidence = ThoughtConfidence.LOW.value
        elif inferred:
            content = "You're home. The house was quiet without you."
            confidence = ThoughtConfidence.LOW.value
        else:
            # Normal arrival
            if ctx.relationship_depth > 0.6:
                content = "Good evening. You've had a long week."
                confidence = ThoughtConfidence.HIGH.value
            else:
                content = "Evening."
                confidence = ThoughtConfidence.HIGH.value
        
        return self._build_thought(
            thought_type=ThoughtType.OBSERVATION.value,
            content=content,
            confidence=confidence,
            reasoning_mode=ReasoningMode.TEMPORAL.value,
            sources=["presence_monitor", "temporal_reasoning"],
            observation_ids=[obs.id],
            significance=obs.significance,
            context=obs.context,
        )

    def _form_temporal_thought(
        self,
        obs: Observation,
        ctx: ReasoningContext,
        modes: List[ReasoningMode],
    ) -> Thought:
        """Form thought from temporal anomaly."""
        domain = obs.context.get("domain", "unknown")
        
        # Connect to reasoning context
        if ReasoningMode.CAUSAL in modes:
            content = f"I've noticed something unusual in your {domain} patterns over the past weeks. Want me to look into it?"
            confidence = ThoughtConfidence.MEDIUM.value
            reasoning_mode = ReasoningMode.CAUSAL.value
        else:
            content = f"The {domain} data shows an anomaly I'm not sure about. Should I investigate?"
            confidence = ThoughtConfidence.LOW.value
            reasoning_mode = ReasoningMode.TEMPORAL.value
        
        return self._build_thought(
            thought_type=ThoughtType.CONCERN.value,
            content=content,
            confidence=confidence,
            reasoning_mode=reasoning_mode,
            sources=["temporal_reasoning", "causality"],
            observation_ids=[obs.id],
            significance=obs.significance,
            context=obs.context,
        )

    def _form_pattern_thought(
        self,
        obs: Observation,
        ctx: ReasoningContext,
    ) -> Thought:
        """Form thought from pattern break."""
        pattern_type = obs.context.get("pattern_type", "behavior")
        
        if pattern_type == "arrival":
            content = "You've been arriving later than usual this week. Everything alright?"
            confidence = ThoughtConfidence.MEDIUM.value
        elif pattern_type == "engagement":
            content = "You haven't asked about the project in a few days. Should I keep the updates coming, or are you focused elsewhere?"
            confidence = ThoughtConfidence.LOW.value
        else:
            content = "There's a pattern I'm noticing that seems off. Want me to elaborate?"
            confidence = ThoughtConfidence.LOW.value
        
        return self._build_thought(
            thought_type=ThoughtType.OBSERVATION.value,
            content=content,
            confidence=confidence,
            reasoning_mode=ReasoningMode.TEMPORAL.value,
            sources=["presence_monitor", "temporal_reasoning"],
            observation_ids=[obs.id],
            significance=obs.significance,
            context=obs.context,
        )

    def _form_data_thought(
        self,
        obs: Observation,
        ctx: ReasoningContext,
    ) -> Thought:
        """Form thought from significant data."""
        module = obs.context.get("module", "scientific")
        
        # Build content based on what module generated it
        if module == "symbolic_math" or module == "simulation":
            content = f"The overnight {module} results are in. There's something worth reviewing."
            confidence = ThoughtConfidence.MEDIUM.value
        elif module == "hypothesis_scorer":
            content = "I've scored the recent hypotheses. One stands out as particularly promising."
            confidence = ThoughtConfidence.MEDIUM.value
        else:
            content = f"The {module} module has produced something worth discussing."
            confidence = ThoughtConfidence.LOW.value
        
        return self._build_thought(
            thought_type=ThoughtType.INSIGHT.value,
            content=content,
            confidence=confidence,
            reasoning_mode=ReasoningMode.DEDUCTIVE.value,
            sources=[module, "hypothesis_scorer"],
            observation_ids=[obs.id],
            significance=obs.significance,
            context=obs.context,
        )

    def _form_correlation_thought(
        self,
        obs: Observation,
        ctx: ReasoningContext,
    ) -> Thought:
        """Form thought from cross-domain correlation."""
        domains = obs.context.get("domains", [])
        
        if len(domains) >= 2:
            content = f"I've found an unexpected connection between {domains[0]} and {domains[1]}. It's not obvious — want me to explain?"
            confidence = ThoughtConfidence.MEDIUM.value
        else:
            content = "There's a correlation I've found that's worth sharing. It's unexpected."
            confidence = ThoughtConfidence.LOW.value
        
        return self._build_thought(
            thought_type=ThoughtType.INSIGHT.value,
            content=content,
            confidence=confidence,
            reasoning_mode=ReasoningMode.ANALOGICAL.value,
            sources=["transfer_analogy", "causality"],
            observation_ids=[obs.id],
            significance=obs.significance,
            context=obs.context,
        )

    def _form_insight_thought(
        self,
        obs: Observation,
        ctx: ReasoningContext,
    ) -> Thought:
        """Form thought from pending insight."""
        module = obs.context.get("module", "unknown")
        
        content = f"I've been considering something from the {module} module. Got a moment?"
        confidence = ThoughtConfidence.MEDIUM.value
        
        return self._build_thought(
            thought_type=ThoughtType.INSIGHT.value,
            content=content,
            confidence=confidence,
            reasoning_mode=ReasoningMode.ABDUCTIVE.value,
            sources=[module, "meta_analyst"],
            observation_ids=[obs.id],
            significance=obs.significance,
            context=obs.context,
        )

    def _form_generic_thought(
        self,
        obs: Observation,
        ctx: ReasoningContext,
    ) -> Thought:
        """Form thought for unclassified observation type."""
        content = f"I've noticed something: {obs.content[:100]}"
        if len(obs.content) > 100:
            content += "..."
        
        return self._build_thought(
            thought_type=ThoughtType.OBSERVATION.value,
            content=content,
            confidence=ThoughtConfidence.LOW.value,
            reasoning_mode=ReasoningMode.DEDUCTIVE.value,
            sources=["observation_engine"],
            observation_ids=[obs.id],
            significance=obs.significance,
            context=obs.context,
        )

    def _build_thought(
        self,
        thought_type: str,
        content: str,
        confidence: str,
        reasoning_mode: str,
        sources: List[str],
        observation_ids: List[str],
        significance: float,
        context: Dict[str, Any],
    ) -> Thought:
        """Build a Thought object."""
        self._thought_counter += 1
        return Thought(
            id=f"thought_{self._thought_counter:06d}_{int(datetime.now(timezone.utc).timestamp())}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            type=thought_type,
            confidence=confidence,
            content=content,
            reasoning_mode=reasoning_mode,
            sources=sources,
            observation_ids=observation_ids,
            significance=significance,
            context=context,
        )

    def register_callback(self, callback: Callable[[Thought], None]) -> None:
        """Register callback for new thoughts."""
        self._callbacks.append(callback)

    def _notify_callbacks(self, thought: Thought) -> None:
        """Notify registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(thought)
            except Exception:
                pass

    def get_unsurfaced_thoughts(
        self,
        min_significance: float = 0.4,
        limit: int = 10,
    ) -> List[Thought]:
        """Get thoughts that haven't been surfaced yet."""
        with self._lock:
            unsurfaced = [t for t in self._thoughts if not t.surfaced]
        
        # Filter by significance
        unsurfaced = [t for t in unsurfaced if t.significance >= min_significance]
        
        # Sort by significance then timestamp
        unsurfaced.sort(key=lambda x: (x.significance, x.timestamp), reverse=True)
        
        return unsurfaced[:limit]

    def mark_surfaced(self, thought_ids: List[str]) -> None:
        """Mark thoughts as surfaced to human."""
        with self._lock:
            for thought in self._thoughts:
                if thought.id in thought_ids:
                    thought.surfaced = True
                    thought.surface_attempts += 1
                    thought.last_surface_attempt = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _prune_thoughts(self) -> None:
        """Prune old thoughts beyond limit."""
        if len(self._thoughts) > 300:
            by_sig = sorted(self._thoughts, key=lambda x: x.significance, reverse=True)
            self._thoughts = by_sig[:200]

    def get_thought_summary(self) -> Dict[str, Any]:
        """Get summary of thoughts state."""
        with self._lock:
            return {
                "total_thoughts": len(self._thoughts),
                "unsurfaced": len([t for t in self._thoughts if not t.surfaced]),
                "by_type": {
                    t.type: len([x for x in self._thoughts if x.type == t.type])
                    for t in self._thoughts
                },
                "avg_significance": sum(t.significance for t in self._thoughts) / max(1, len(self._thoughts)),
            }

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "tenant_id": self.tenant_id,
                "thought_count": self._thought_counter,
                "thoughts": [t.to_dict() for t in self._thoughts[-100:]],
            }


# ============================================================================
# STORE (thread-safe singleton per tenant)
# ============================================================================

from .observation_engine import Observation, ObservationType

_thought_store: Dict[str, ThoughtFormationEngine] = {}
_thought_lock = threading.Lock()


def generate_arrival_thought(
    tenant_id: str,
    greeting_context: Dict[str, Any],
    significance: float = 0.5,
    storage_path: Optional[Path] = None,
) -> Thought:
    """
    Generate a greeting thought from the adaptive greeting generator.
    Used when change_type == 'first_arrival_today' to produce a pipeline-integrated greeting.
    """
    from datetime import datetime, timezone
    from .adaptive_greeting import AdaptiveGreeting, GreetingContext
    import uuid

    # Build GreetingContext from dict
    gc = GreetingContext(
        time_context=greeting_context.get("time_context", "afternoon"),
        availability=greeting_context.get("availability", "available"),
        arrival_anomaly=greeting_context.get("arrival_anomaly", False),
        anomaly_description=greeting_context.get("anomaly_description", ""),
        arrival_count_today=greeting_context.get("arrival_count_today", 1),
        relationship_depth=greeting_context.get("relationship_depth", 0.5),
        recent_interactions=greeting_context.get("recent_interactions", 0),
        last_greeting_style=greeting_context.get("last_greeting_style", "standard"),
    )

    greeting_gen = AdaptiveGreeting(tenant_id, storage_path)
    content = greeting_gen.generate(gc)

    return Thought(
        id=f"arrival_{uuid.uuid4().hex[:8]}",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        type=ThoughtType.OBSERVATION.value,
        confidence=ThoughtConfidence.MEDIUM.value,
        content=content,
        reasoning_mode=ReasoningMode.TEMPORAL.value,
        sources=["adaptive_greeting"],
        observation_ids=[],
        significance=significance,
        context={"greeting_context": greeting_context},
    )


def get_thought_formation_engine(tenant_id: str, storage_path: Optional[Path] = None) -> ThoughtFormationEngine:
    """Get or create thought formation engine for tenant. Thread-safe."""
    global _thought_store
    
    with _thought_lock:
        if tenant_id in _thought_store:
            return _thought_store[tenant_id]
    
    engine = ThoughtFormationEngine(tenant_id=tenant_id, storage_path=storage_path)
    with _thought_lock:
        _thought_store[tenant_id] = engine
    return engine