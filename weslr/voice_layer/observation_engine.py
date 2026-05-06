"""
observation_engine.py - Observation monitoring for Weslr voice layer

Continuously monitors data streams and detects notable events
that should trigger thought formation. Event-driven, not polling.

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


class ObservationType(str, Enum):
    # Presence
    ARRIVAL = "arrival"
    DEPARTURE = "departure"
    AVAILABILITY_CHANGE = "availability_change"
    
    # Patterns
    TEMPORAL_ANOMALY = "temporal_anomaly"      # Something unusual over time
    PATTERN_BREAK = "pattern_break"           # Broken learned pattern
    TREND_DETECTED = "trend_detected"          # New trend forming
    
    # Data
    DATA_SIGNIFICANT = "data_significant"       # New significant data point
    THRESHOLD_BREACH = "threshold_breach"       # Data crossed threshold
    CORRELATION_FOUND = "correlation_found"     # Unexpected correlation
    
    # Memory
    FOLLOW_UP_READY = "follow_up_ready"          # Something to follow up on
    UNRESOLVED_THREAD = "unresolved_thread"     # Topic raised but not concluded
    INSIGHT_PENDING = "insight_pending"         # Weslr has something to share
    
    # External
    CALENDAR_EVENT = "calendar_event"
    ENVIRONMENT_CHANGE = "environment_change"


class Urgency(str, Enum):
    LOW = "low"           # Can wait, non-urgent
    NORMAL = "normal"    # Normal priority
    ELEVATED = "elevated" # Should address soon
    HIGH = "high"         # Important, don't defer
    CRITICAL = "critical" # Immediate attention needed


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Observation:
    """
    A single observation — something Weslr noticed that may become a thought.
    """
    id: str
    timestamp: str
    type: str                    # ObservationType value
    source: str                 # Which module/source generated this
    content: str                 # Natural language description of what was observed
    significance: float          # 0.0-1.0, how important is this
    urgency: str                 # Urgency value
    context: Dict[str, Any]      # Additional context data
    processed: bool = False      # Has this been fed to thought formation
    thoughts_generated: List[str] = field(default_factory=list)  # IDs of thoughts produced
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type,
            "source": self.source,
            "content": self.content,
            "significance": round(self.significance, 3),
            "urgency": self.urgency,
            "context": self.context,
            "processed": self.processed,
            "thoughts_generated": self.thoughts_generated,
        }


@dataclass
class ObservationFilter:
    """
    Filter criteria for observation relevance.
    """
    min_significance: float = 0.3
    urgency_threshold: str = Urgency.NORMAL.value
    types_whitelist: Optional[List[str]] = None   # None = all types allowed
    types_blacklist: Optional[List[str]] = None   # Types to exclude


# ============================================================================
# OBSERVATION ENGINE
# ============================================================================


class ObservationEngine:
    """
    Observation engine — monitors data streams and surfaces notable observations.
    
    NOT a polling loop. Driven by:
    - External signals via signal_observation()
    - Callbacks from other modules (presence, temporal_reasoning, etc.)
    - Deliberate queries from thought_formation
    
    Key principles:
    - Events flow IN, observations surface OUT
    - Each observation is weighted by significance and urgency
    - Observations feed thought_formation, not the other way around
    """

    def __init__(self, tenant_id: str, storage_path: Optional[Path] = None):
        self.tenant_id = tenant_id
        self.storage_path = storage_path
        self._observations: List[Observation] = []
        self._callbacks: List[Callable[[Observation], None]] = []
        self._lock = threading.Lock()
        self._observation_counter = 0
        
        # Observers can register interest in specific observation types
        self._type_subscribers: Dict[str, List[Callable[[Observation], None]]] = {}

    def signal_observation(
        self,
        obs_type: str,
        source: str,
        content: str,
        significance: float = 0.5,
        urgency: str = Urgency.NORMAL.value,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Signal a new observation from any source.
        Returns observation ID.
        """
        with self._lock:
            self._observation_counter += 1
            obs_id = f"obs_{self._observation_counter:06d}_{int(datetime.now(timezone.utc).timestamp())}"
            
            observation = Observation(
                id=obs_id,
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                type=obs_type,
                source=source,
                content=content,
                significance=significance,
                urgency=urgency,
                context=context or {},
            )
            
            self._observations.append(observation)
            self._notify_subscribers(observation)
            self._notify_callbacks(observation)
            
            # Prune old observations
            self._prune_observations()
            
            return obs_id

    def signal_arrival_observation(self, inferred: bool = False, lateness_minutes: int = 0) -> str:
        """Signal human arrival."""
        if inferred and lateness_minutes > 15:
            content = f"Human arrived {lateness_minutes} minutes later than usual."
            significance = 0.6
            urgency = Urgency.NORMAL.value
        else:
            content = "Human arrived home."
            significance = 0.4
            urgency = Urgency.NORMAL.value
        
        return self.signal_observation(
            obs_type=ObservationType.ARRIVAL.value,
            source="presence_monitor",
            content=content,
            significance=significance,
            urgency=urgency,
            context={"inferred": inferred, "lateness_minutes": lateness_minutes},
        )

    def signal_temporal_anomaly(
        self,
        description: str,
        domain: str,
        significance: float = 0.7,
    ) -> str:
        """Signal a temporal anomaly — something unusual over time."""
        return self.signal_observation(
            obs_type=ObservationType.TEMPORAL_ANOMALY.value,
            source="temporal_reasoning",
            content=description,
            significance=significance,
            urgency=Urgency.NORMAL.value,
            context={"domain": domain},
        )

    def signal_pattern_break(
        self,
        pattern_type: str,
        description: str,
        significance: float = 0.6,
    ) -> str:
        """Signal a broken learned pattern."""
        return self.signal_observation(
            obs_type=ObservationType.PATTERN_BREAK.value,
            source="presence_monitor",
            content=description,
            significance=significance,
            urgency=Urgency.NORMAL.value,
            context={"pattern_type": pattern_type},
        )

    def signal_data_significant(
        self,
        data_description: str,
        source_module: str,
        significance: float = 0.7,
        urgency: str = Urgency.NORMAL.value,
    ) -> str:
        """Signal significant new data from scientific modules."""
        return self.signal_observation(
            obs_type=ObservationType.DATA_SIGNIFICANT.value,
            source=source_module,
            content=data_description,
            significance=significance,
            urgency=urgency,
            context={"module": source_module},
        )

    def signal_correlation_found(
        self,
        correlation_description: str,
        domains: List[str],
        significance: float = 0.8,
    ) -> str:
        """Signal unexpected correlation across domains (transfer_analogy output)."""
        return self.signal_observation(
            obs_type=ObservationType.CORRELATION_FOUND.value,
            source="transfer_analogy",
            content=correlation_description,
            significance=significance,
            urgency=Urgency.ELEVATED.value,
            context={"domains": domains},
        )

    def signal_insight_pending(
        self,
        insight_description: str,
        source_module: str,
        significance: float = 0.6,
    ) -> str:
        """Signal that Weslr has something to share (from follow-up or unresolved thread)."""
        return self.signal_observation(
            obs_type=ObservationType.INSIGHT_PENDING.value,
            source=source_module,
            content=insight_description,
            significance=significance,
            urgency=Urgency.NORMAL.value,
            context={"module": source_module},
        )

    def register_callback(self, callback: Callable[[Observation], None]) -> None:
        """Register callback for all observations."""
        self._callbacks.append(callback)

    def register_type_subscriber(
        self,
        obs_type: str,
        callback: Callable[[Observation], None],
    ) -> None:
        """Register callback for specific observation type."""
        if obs_type not in self._type_subscribers:
            self._type_subscribers[obs_type] = []
        self._type_subscribers[obs_type].append(callback)

    def _notify_subscribers(self, observation: Observation) -> None:
        """Notify type-specific subscribers."""
        if observation.type in self._type_subscribers:
            for callback in self._type_subscribers[observation.type]:
                try:
                    callback(observation)
                except Exception:
                    pass

    def _notify_callbacks(self, observation: Observation) -> None:
        """Notify general callbacks."""
        for callback in self._callbacks:
            try:
                callback(observation)
            except Exception:
                pass

    def get_unprocessed_observations(
        self,
        filter_criteria: Optional[ObservationFilter] = None,
        limit: int = 20,
    ) -> List[Observation]:
        """Get observations that haven't been processed by thought formation."""
        with self._lock:
            unprocessed = [o for o in self._observations if not o.processed]
        
        # Apply filter
        if filter_criteria:
            unprocessed = self._apply_filter(unprocessed, filter_criteria)
        
        # Sort by significance descending, then timestamp descending
        unprocessed.sort(key=lambda x: (x.significance, x.timestamp), reverse=True)
        
        return unprocessed[:limit]

    def mark_processed(self, observation_ids: List[str]) -> None:
        """Mark observations as processed by thought formation."""
        with self._lock:
            for obs in self._observations:
                if obs.id in observation_ids:
                    obs.processed = True

    def add_thought_generated(self, observation_id: str, thought_id: str) -> None:
        """Link a thought ID to an observation."""
        with self._lock:
            for obs in self._observations:
                if obs.id == observation_id:
                    obs.thoughts_generated.append(thought_id)
                    break

    def _apply_filter(self, observations: List[Observation], filter_criteria: ObservationFilter) -> List[Observation]:
        """Apply filter criteria to observations."""
        result = []
        for obs in observations:
            # Significance filter
            if obs.significance < filter_criteria.min_significance:
                continue
            
            # Type whitelist
            if filter_criteria.types_whitelist and obs.type not in filter_criteria.types_whitelist:
                continue
            
            # Type blacklist
            if filter_criteria.types_blacklist and obs.type in filter_criteria.types_blacklist:
                continue
            
            result.append(obs)
        
        return result

    def _prune_observations(self) -> None:
        """Prune old observations beyond limit."""
        if len(self._observations) > 500:
            # Keep most recent 300 + highest significance
            by_sig = sorted(self._observations, key=lambda x: x.significance, reverse=True)
            self._observations = by_sig[:300]

    def get_observation_summary(self) -> Dict[str, Any]:
        """Get summary of recent observations."""
        with self._lock:
            recent = [o for o in self._observations[-50:] if not o.processed]
            
            by_type: Dict[str, int] = {}
            for obs in recent:
                by_type[obs.type] = by_type.get(obs.type, 0) + 1
            
            return {
                "total_observations": len(self._observations),
                "unprocessed": len([o for o in self._observations if not o.processed]),
                "recent_by_type": by_type,
                "avg_significance": sum(o.significance for o in self._observations[-50:]) / min(50, len(self._observations)) if self._observations else 0,
            }

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "tenant_id": self.tenant_id,
                "observation_count": self._observation_counter,
                "observations": [o.to_dict() for o in self._observations[-100:]],
            }


# ============================================================================
# OBSERVATION STORE (thread-safe singleton per tenant)
# ============================================================================

_observation_store: Dict[str, ObservationEngine] = {}
_observation_lock = threading.Lock()


def get_observation_engine(tenant_id: str, storage_path: Optional[Path] = None) -> ObservationEngine:
    """Get or create observation engine for tenant. Thread-safe."""
    global _observation_store
    
    with _observation_lock:
        if tenant_id in _observation_store:
            return _observation_store[tenant_id]
    
    engine = ObservationEngine(tenant_id=tenant_id, storage_path=storage_path)
    with _observation_lock:
        _observation_store[tenant_id] = engine
    return engine