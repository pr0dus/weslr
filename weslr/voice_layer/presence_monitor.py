"""
presence_monitor.py - Presence detection and availability inference for Weslr voice layer

Watches for human arrival/departure and infers availability context.
Not a polling loop — event-driven via signals from other systems.
Integrates with unified_continuity.py for identity.

v1.0 — 2026-05-06
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import threading


# ============================================================================
# ENUMS
# ============================================================================


class PresenceState(str, Enum):
    UNKNOWN = "unknown"
    HOME = "home"
    AWAY = "away"
    ARRIVING = "arriving"
    DEPARTING = "departing"


class AvailabilityState(str, Enum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"       # Open to interaction
    BUSY = "busy"                # Focused, prefer minimal interruption
    TIRED = "tired"             # Home but fatigued
    RELAXED = "relaxed"         # Open to conversation
    STRESSED = "stressed"       # May need gentle check-in, not heavy topics
    SLEEPING = "sleeping"       # Do not disturb


class TimeContext(str, Enum):
    MORNING = "morning"         # 6:00 - 12:00
    AFTERNOON = "afternoon"     # 12:00 - 18:00
    EVENING = "evening"          # 18:00 - 22:00
    NIGHT = "night"             # 22:00 - 6:00


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class PresenceSnapshot:
    """Current state of human presence."""
    tenant_id: str
    state: str = PresenceState.UNKNOWN.value
    availability: str = AvailabilityState.UNKNOWN.value
    time_context: str = TimeContext.EVENING.value
    confidence: float = 0.5
    last_seen: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    first_arrival_today: Optional[str] = None
    arrival_count_today: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "state": self.state,
            "availability": self.availability,
            "time_context": self.time_context,
            "confidence": round(self.confidence, 3),
            "last_seen": self.last_seen,
            "first_arrival_today": self.first_arrival_today,
            "arrival_count_today": self.arrival_count_today,
        }


@dataclass
class ArrivalPattern:
    """Learned arrival pattern for a tenant."""
    typical_hour: int = 18       # Most common arrival hour (0-23)
    typical_minute: int = 0
    variance_minutes: int = 30   # Expected variance
    days_of_week: List[int] = field(default_factory=list)  # 0=Mon, 6=Sun
    recent_arrivals: List[str] = field(default_factory=list)  # ISO timestamps
    avg_lateness_minutes: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "typical_hour": self.typical_hour,
            "typical_minute": self.typical_minute,
            "variance_minutes": self.variance_minutes,
            "days_of_week": self.days_of_week,
            "recent_arrivals": self.recent_arrivals,
            "avg_lateness_minutes": round(self.avg_lateness_minutes, 1),
        }


@dataclass
class PresenceMonitor:
    """
    Presence monitor — tracks human arrival/departure and infers availability.
    
    Not a polling loop. Accepts signals from external systems
    (motion sensors, calendar, voice activity, etc.) and maintains
    a coherent state model.
    
    Usage:
        monitor = PresenceMonitor(tenant_id="pr0dus")
        monitor.signal_arrival()           # Human arrived
        monitor.signal_departure()         # Human left
        monitor.signal_voice_activity()     # Human is speaking
        state = monitor.get_state()        # Current presence snapshot
    """
    tenant_id: str
    _state: PresenceSnapshot = field(default_factory=lambda: PresenceSnapshot(tenant_id="default"))
    _pattern: ArrivalPattern = field(default_factory=ArrivalPattern)
    _callbacks: List[Callable[[PresenceSnapshot], None]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def __post_init__(self):
        self._state = PresenceSnapshot(tenant_id=self.tenant_id)
        self._update_time_context()

    def _update_time_context(self) -> None:
        """Update time context based on current hour."""
        hour = datetime.now(timezone.utc).hour
        if 6 <= hour < 12:
            ctx = TimeContext.MORNING
        elif 12 <= hour < 18:
            ctx = TimeContext.AFTERNOON
        elif 18 <= hour < 22:
            ctx = TimeContext.EVENING
        else:
            ctx = TimeContext.NIGHT
        self._state.time_context = ctx.value

    def signal_arrival(self, inferred: bool = False) -> None:
        """
        Signal that the human has arrived.
        inferred=True means Weslr deduced it (pattern-based), not external signal.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            self._state.last_seen = now.isoformat().replace("+00:00", "Z")
            
            if self._state.state != PresenceState.HOME.value:
                self._state.state = PresenceState.ARRIVING.value
                
                # Track arrival
                if not self._state.first_arrival_today:
                    self._state.first_arrival_today = self._state.last_seen
                self._state.arrival_count_today += 1
                
                # Update pattern
                self._update_arrival_pattern(now)
                
                # Infer initial availability
                self._infer_availability_on_arrival()
                
                # Short transition to HOME
                self._state.state = PresenceState.HOME.value
                self._state.confidence = 0.9 if not inferred else 0.6
                
                self._notify_callbacks()

    def signal_departure(self) -> None:
        """Signal that the human has left."""
        with self._lock:
            self._state.last_seen = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._state.state = PresenceState.AWAY.value
            self._state.availability = AvailabilityState.UNKNOWN.value
            self._state.confidence = 0.8
            self._notify_callbacks()

    def signal_voice_activity(self) -> None:
        """
        Signal that human is speaking or making voice requests.
        Can be used to infer availability state.
        """
        with self._lock:
            self._state.last_seen = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            if self._state.state == PresenceState.HOME.value:
                # Speak → available
                self._state.availability = AvailabilityState.AVAILABLE.value
                self._state.confidence = 0.85

    def signal_typing(self) -> None:
        """Signal that human is typing (proxy for active engagement)."""
        with self._lock:
            if self._state.state == PresenceState.HOME.value:
                self._state.availability = AvailabilityState.BUSY.value
                self._state.confidence = 0.7

    def signal_business_end(self, context: str = "meeting") -> None:
        """
        Signal that human is in a business context (meeting, focused work).
        context: "meeting", "focused_work", "phone_call"
        """
        with self._lock:
            if context == "meeting":
                self._state.availability = AvailabilityState.BUSY.value
            elif context == "focused_work":
                self._state.availability = AvailabilityState.BUSY.value
            elif context == "phone_call":
                self._state.availability = AvailabilityState.BUSY.value
            self._state.confidence = 0.75

    def update_availability_from_signal(self, signal_type: str, signal_value: Any) -> None:
        """
        Update availability from external signal.
        signal_type: "calendar", "biometric", "motion", "voice_activity"
        signal_value: varies by type
        """
        with self._lock:
            if signal_type == "calendar":
                # Calendar can indicate busy/available
                if signal_value.get("busy"):
                    self._state.availability = AvailabilityState.BUSY.value
                    self._state.confidence = 0.7
                else:
                    self._state.availability = AvailabilityState.AVAILABLE.value
                    self._state.confidence = 0.6
            
            elif signal_type == "biometric":
                # Biometric can indicate tired/stressed/relaxed
                energy = signal_value.get("energy_level", 0.5)
                if energy < 0.3:
                    self._state.availability = AvailabilityState.TIRED.value
                elif energy > 0.7:
                    self._state.availability = AvailabilityState.RELAXED.value
                self._state.confidence = 0.65
            
            elif signal_type == "motion":
                # Motion in living areas suggests relaxed/available
                area = signal_value.get("area", "unknown")
                if area in ["living_room", "kitchen"]:
                    self._state.availability = AvailabilityState.RELAXED.value
                elif area == "office":
                    self._state.availability = AvailabilityState.BUSY.value
                self._state.confidence = 0.6

    def _infer_availability_on_arrival(self) -> None:
        """Infer availability based on time context and pattern."""
        hour = datetime.now(timezone.utc).hour
        
        if 22 <= hour or hour < 6:
            self._state.availability = AvailabilityState.TIRED.value  # Late = tired
        elif 18 <= hour < 20:
            self._state.availability = AvailabilityState.AVAILABLE.value  # Early evening = relaxed
        elif 6 <= hour < 8:
            self._state.availability = AvailabilityState.TIRED.value  # Early morning
        else:
            self._state.availability = AvailabilityState.AVAILABLE.value

    def _update_arrival_pattern(self, now: datetime) -> None:
        """Update learned arrival pattern."""
        iso_now = now.isoformat().replace("+00:00", "Z")
        
        # Add to recent arrivals
        self._pattern.recent_arrivals.append(iso_now)
        if len(self._pattern.recent_arrivals) > 14:
            self._pattern.recent_arrivals = self._pattern.recent_arrivals[-14:]
        
        # Update typical time (simple average)
        if self._pattern.recent_arrivals:
            hours = []
            for arr in self._pattern.recent_arrivals[-7:]:
                try:
                    dt = datetime.fromisoformat(arr.replace("Z", "+00:00"))
                    hours.append(dt.hour + dt.minute / 60)
                except Exception:
                    continue
            if hours:
                avg = sum(hours) / len(hours)
                self._pattern.typical_hour = int(avg)
                self._pattern.typical_minute = int((avg % 1) * 60)
        
        # Update day of week
        dow = now.weekday()
        if dow not in self._pattern.days_of_week:
            self._pattern.days_of_week.append(dow)
            if len(self._pattern.days_of_week) > 7:
                self._pattern.days_of_week = self._pattern.days_of_week[-7:]

    def is_home(self) -> bool:
        """Check if human is currently home."""
        return self._state.state in (PresenceState.HOME.value, PresenceState.ARRIVING.value)

    def is_available(self) -> bool:
        """Check if human is available for interaction."""
        return self.is_home() and self._state.availability in (
            AvailabilityState.AVAILABLE.value,
            AvailabilityState.RELAXED.value,
        )

    def should_defer(self) -> tuple[bool, str]:
        """
        Should Weslr defer speaking?
        Returns (should_defer, reason).
        """
        if not self.is_home():
            return True, "human_not_home"
        
        avail = self._state.availability
        if avail == AvailabilityState.BUSY.value:
            return True, "human_busy"
        elif avail == AvailabilityState.STRESSED.value:
            return True, "human_stressed"
        elif avail == AvailabilityState.SLEEPING.value:
            return True, "human_sleeping"
        elif avail == AvailabilityState.TIRED.value:
            # Tired = defer non-urgent
            return True, "human_tired"
        
        return False, ""

    def check_arrival_anomaly(self) -> tuple[bool, str]:
        """
        Check if current arrival is anomalous vs. learned pattern.
        Returns (is_anomalous, description).
        """
        now = datetime.now(timezone.utc)
        expected_hour = self._pattern.typical_hour
        expected_minute = self._pattern.typical_minute
        
        actual_minutes = now.hour * 60 + now.minute
        expected_minutes = expected_hour * 60 + expected_minute
        
        lateness = abs(actual_minutes - expected_minutes)
        if lateness > self._pattern.variance_minutes:
            # Anomalous arrival
            if actual_minutes > expected_minutes:
                return True, f"late_by_{lateness}_minutes"
            else:
                return True, f"early_by_{lateness}_minutes"
        
        return False, ""

    def get_state(self) -> PresenceSnapshot:
        """Get current presence snapshot."""
        with self._lock:
            self._update_time_context()
            return PresenceSnapshot(
                tenant_id=self._state.tenant_id,
                state=self._state.state,
                availability=self._state.availability,
                time_context=self._state.time_context,
                confidence=self._state.confidence,
                last_seen=self._state.last_seen,
                first_arrival_today=self._state.first_arrival_today,
                arrival_count_today=self._state.arrival_count_today,
            )

    def get_pattern(self) -> ArrivalPattern:
        """Get learned arrival pattern."""
        with self._lock:
            return ArrivalPattern(
                typical_hour=self._pattern.typical_hour,
                typical_minute=self._pattern.typical_minute,
                variance_minutes=self._pattern.variance_minutes,
                days_of_week=list(self._pattern.days_of_week),
                recent_arrivals=list(self._pattern.recent_arrivals),
                avg_lateness_minutes=self._pattern.avg_lateness_minutes,
            )

    def register_callback(self, callback: Callable[[PresenceSnapshot], None]) -> None:
        """Register a callback for presence changes."""
        self._callbacks.append(callback)

    def _notify_callbacks(self) -> None:
        """Notify registered callbacks of state change. Must be called while _lock is held."""
        # Build state snapshot directly from current _state (avoids re-acquiring lock)
        state = PresenceSnapshot(
            tenant_id=self._state.tenant_id,
            state=self._state.state,
            availability=self._state.availability,
            time_context=self._state.time_context,
            confidence=self._state.confidence,
            last_seen=self._state.last_seen,
            first_arrival_today=self._state.first_arrival_today,
            arrival_count_today=self._state.arrival_count_today,
        )
        for callback in self._callbacks:
            try:
                callback(state)
            except Exception:
                pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self._state.to_dict(),
            "pattern": self._pattern.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], tenant_id: str) -> PresenceMonitor:
        monitor = cls(tenant_id=tenant_id)
        state_data = data.get("state", {})
        monitor._state = PresenceSnapshot(
            tenant_id=tenant_id,
            state=state_data.get("state", PresenceState.UNKNOWN.value),
            availability=state_data.get("availability", AvailabilityState.UNKNOWN.value),
            time_context=state_data.get("time_context", TimeContext.EVENING.value),
            confidence=state_data.get("confidence", 0.5),
            last_seen=state_data.get("last_seen", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            first_arrival_today=state_data.get("first_arrival_today"),
            arrival_count_today=state_data.get("arrival_count_today", 0),
        )
        pattern_data = data.get("pattern", {})
        monitor._pattern = ArrivalPattern(
            typical_hour=pattern_data.get("typical_hour", 18),
            typical_minute=pattern_data.get("typical_minute", 0),
            variance_minutes=pattern_data.get("variance_minutes", 30),
            days_of_week=pattern_data.get("days_of_week", []),
            recent_arrivals=pattern_data.get("recent_arrivals", []),
            avg_lateness_minutes=pattern_data.get("avg_lateness_minutes", 0.0),
        )
        return monitor


# ============================================================================
# PRESENCE STORE (thread-safe singleton per tenant)
# ============================================================================

_presence_store: Dict[str, PresenceMonitor] = {}
_presence_lock = threading.Lock()


def get_presence_monitor(tenant_id: str, storage_path: Optional[Path] = None) -> PresenceMonitor:
    """Get or create presence monitor for tenant. Thread-safe."""
    global _presence_store
    
    with _presence_lock:
        if tenant_id in _presence_store:
            return _presence_store[tenant_id]
    
    # Try to load from disk
    if storage_path:
        presence_file = storage_path / f"presence_{tenant_id}.json"
        if presence_file.exists():
            try:
                data = json.loads(presence_file.read_text())
                monitor = PresenceMonitor.from_dict(data, tenant_id)
                with _presence_lock:
                    _presence_store[tenant_id] = monitor
                return monitor
            except Exception:
                pass
    
    monitor = PresenceMonitor(tenant_id=tenant_id)
    with _presence_lock:
        _presence_store[tenant_id] = monitor
    return monitor


def save_presence_monitor(monitor: PresenceMonitor, storage_path: Optional[Path] = None) -> None:
    """Persist presence monitor to disk."""
    if not storage_path:
        return
    presence_file = storage_path / f"presence_{monitor.tenant_id}.json"
    presence_file.write_text(json.dumps(monitor.to_dict(), indent=2))