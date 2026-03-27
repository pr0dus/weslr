"""Introspection monitoring for Weslr self-model.

Tracks internal state perturbations, confidence signals, and unexpected thoughts
before generating text. Provides traceable introspection evidence.
"""

from __future__ import annotations

import time
import json
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

# Base directory for introspection storage
BASE_DIR = Path(__file__).resolve().parent
INTROSPECTION_HISTORY_PATH = BASE_DIR / "introspection_history.json"
SELF_EVIDENCE_PATH = BASE_DIR / "self_evidence.json"


class PerturbationType(Enum):
    """Types of internal state perturbations."""
    UNEXPECTED_RESPONSE = "unexpected_response"
    CONFIDENCE_DROP = "confidence_drop"
    CREATIVITY_SPIKE = "creativity_spike"
    MEMORY_GAP = "memory_gap"
    PATTERN_BREAK = "pattern_break"
    CONTEXT_MISMATCH = "context_mismatch"
    EMOTIONAL_SURGE = "emotional_surge"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    UNKNOWN = "unknown"


@dataclass
class Perturbation:
    """Represents an internal state perturbation."""
    id: str
    timestamp: int
    type: PerturbationType
    severity: float  # 0.0 to 1.0
    context: Dict[str, Any]  # Context of the perturbation
    detected_at: int = field(default_factory=int)
    resolution: Optional[str] = None
    resolution_time: Optional[int] = None

    def __post_init__(self):
        if not hasattr(self, 'detected_at'):
            self.detected_at = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "type": self.type.value,
            "severity": self.severity,
            "context": self.context,
            "detected_at": self.detected_at,
            "resolution": self.resolution,
            "resolution_time": self.resolution_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Perturbation:
        perturbation_type = data.get("type", "unknown")
        if isinstance(perturbation_type, str):
            try:
                pt = PerturbationType(perturbation_type)
            except ValueError:
                pt = PerturbationType.UNKNOWN
        else:
            pt = perturbation_type
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            type=pt,
            severity=data.get("severity", 0.5),
            context=data.get("context", {}),
            detected_at=data.get("detected_at", int(time.time())),
            resolution=data.get("resolution"),
            resolution_time=data.get("resolution_time")
        )

    def resolve(self, resolution: str):
        """Mark perturbation as resolved."""
        self.resolution = resolution
        self.resolution_time = int(time.time())


@dataclass
class ConfidenceSignal:
    """Represents a confidence signal in self-decision."""
    id: str
    timestamp: int
    context: str  # What decision was this for?
    estimated_confidence: float  # 0.0 to 1.0
    actual_outcome_confidence: Optional[float] = None  # After feedback
    deviation: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "context": self.context,
            "estimated_confidence": self.confidence,
            "actual_outcome_confidence": self.actual_outcome_confidence,
            "deviation": self.deviation
        }

    @property
    def confidence(self) -> float:
        return self.estimated_confidence

    @confidence.setter
    def confidence(self, val: float):
        self.estimated_confidence = val

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConfidenceSignal:
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            context=data.get("context", ""),
            estimated_confidence=data.get("estimated_confidence", 0.5),
            actual_outcome_confidence=data.get("actual_outcome_confidence"),
            deviation=data.get("deviation")
        )


@dataclass
class IntrospectionEvent:
    """A complete introspection event with multiple signals."""
    id: str
    timestamp: int
    perturbations: List[Perturbation]
    confidence_signals: List[ConfidenceSignal]
    self_referential_markers: List[str]  # Self-referential processing detected

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "perturbations": [p.to_dict() for p in self.perturbations],
            "confidence_signals": [c.to_dict() for c in self.confidence_signals],
            "self_referential_markers": self.self_referential_markers
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> IntrospectionEvent:
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            perturbations=[Perturbation.from_dict(p) for p in data.get("perturbations", [])],
            confidence_signals=[ConfidenceSignal.from_dict(c) for c in data.get("confidence_signals", [])],
            self_referential_markers=data.get("self_referential_markers", [])
        )


class IntrospectionMonitor:
    """Monitors self-model for perturbations and confidence signals."""

    def __init__(self):
        self.perturbations: List[Perturbation] = []
        self.confidence_signals: List[ConfidenceSignal] = []
        self.introspection_history: List[IntrospectionEvent] = []
        self.introspection_enabled = True
        self.perturbation_threshold = 0.7  # Severity threshold for alerts
        self.deviation_threshold = 0.3  # Confidence deviation threshold

    # --- Perturbation Detection ---

    def detect_perturbation(
        self,
        perturbation_type: PerturbationType,
        context: Dict[str, Any],
        severity: float = 0.5
    ) -> Perturbation:
        """Detect and record a perturbation."""
        perturbation = Perturbation(
            id=hashlib.md5(f"{time.time()}_{perturbation_type.value}".encode()).hexdigest()[:8],
            timestamp=int(time.time()),
            type=perturbation_type,
            severity=severity,
            context=context
        )
        self.perturbations.append(perturbation)
        return perturbation

    def record_confidence_signal(
        self,
        context: str,
        estimated_confidence: float,
        actual_outcome_confidence: Optional[float] = None
    ) -> ConfidenceSignal:
        """Record a confidence signal."""
        signal = ConfidenceSignal(
            id=hashlib.md5(f"{time.time()}_{context}".encode()).hexdigest()[:8],
            timestamp=int(time.time()),
            context=context,
            estimated_confidence=estimated_confidence,
            actual_outcome_confidence=actual_outcome_confidence
        )
        if actual_outcome_confidence is not None:
            signal.deviation = abs(estimated_confidence - actual_outcome_confidence)
        self.confidence_signals.append(signal)
        return signal

    # --- Self-Referential Processing Detection ---

    def detect_self_referential_processing(self, prompt: str, response: str) -> List[str]:
        """Detect self-referential processing in response."""
        markers = []

        # Check for self-referential language
        self_patterns = [
            r"I\s+(am|think|feel|believe|understand|realize)",
            r"my\s+(thoughts|mind|process|model|state)",
            r"within\s+(myself|the\s+system)",
            r"self[-\s]?(reference|monitor|awareness|reflection)",
        ]

        for pattern in self_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                markers.append(f"pattern:{pattern.split('(')[0].strip()}")

        # Check for awareness of internal state
        internal_state_markers = [
            "confidence", "uncertainty", "knowledge", "limits", "boundary",
            "state", "perturbation", "introspection"
        ]
        for marker in internal_state_markers:
            if marker in response.lower():
                markers.append(f"internal:{marker}")
                break

        return markers

    # --- Main Processing ---

    def process_introspection(
        self,
        input_text: str,
        response: str,
        confidence_estimate: float = 0.5
    ) -> IntrospectionEvent:
        """Process introspection for an input-output pair."""
        perturbations = []
        confidence_signals = []
        self_markers = []

        # Detect perturbations based on response characteristics
        if confidence_estimate < 0.3:
            perturbations.append(
                self.detect_perturbation(
                    PerturbationType.CONFIDENCE_DROP,
                    {"input": input_text[:50], "confidence": confidence_estimate}
                )
            )

        if len(response) > 500:  # Very long response
            perturbations.append(
                self.detect_perturbation(
                    PerturbationType.CREATIVITY_SPIKE,
                    {"response_length": len(response)}
                )
            )

        # Detect self-referential processing
        self_markers = self.detect_self_referential_processing(input_text, response)

        # Record confidence signal
        signal = self.record_confidence_signal(
            context=input_text[:100],
            estimated_confidence=confidence_estimate
        )
        confidence_signals.append(signal)

        # Create introspection event
        event = IntrospectionEvent(
            id=hashlib.md5(f"{time.time()}_{input_text[:20]}".encode()).hexdigest()[:8],
            timestamp=int(time.time()),
            perturbations=perturbations,
            confidence_signals=confidence_signals,
            self_referential_markers=self_markers
        )

        self.introspection_history.append(event)
        return event

    # --- History and Persistence ---

    def get_perturbations(self, since_timestamp: int = 0) -> List[Perturbation]:
        """Get perturbations since a timestamp."""
        return [p for p in self.perturbations if p.timestamp >= since_timestamp]

    def get_unresolved_perturbations(self) -> List[Perturbation]:
        """Get unresolved perturbations."""
        return [p for p in self.perturbations if p.resolution is None]

    def get_confidence_signals(self, since_timestamp: int = 0) -> List[ConfidenceSignal]:
        """Get confidence signals since a timestamp."""
        return [s for s in self.confidence_signals if s.timestamp >= since_timestamp]

    def save_history(self, path: Path = INTROSPECTION_HISTORY_PATH):
        """Save introspection history to JSON."""
        data = {
            "perturbations": [p.to_dict() for p in self.perturbations],
            "confidence_signals": [s.to_dict() for s in self.confidence_signals],
            "introspection_history": [e.to_dict() for e in self.introspection_history],
            "introspection_enabled": self.introspection_enabled,
            "last_save": int(time.time())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_history(cls, path: Path = INTROSPECTION_HISTORY_PATH) -> "IntrospectionMonitor":
        """Load introspection history from JSON."""
        if not path.exists():
            return cls()

        monitor = cls()
        with open(path, "r") as f:
            data = json.load(f)

        monitor.perturbations = [Perturbation.from_dict(p) for p in data.get("perturbations", [])]
        monitor.confidence_signals = [ConfidenceSignal.from_dict(c) for c in data.get("confidence_signals", [])]
        monitor.introspection_history = [IntrospectionEvent.from_dict(e) for e in data.get("introspection_history", [])]
        monitor.introspection_enabled = data.get("introspection_enabled", True)
        return monitor

    def get_self_evidence(self) -> Dict[str, Any]:
        """Generate self-evidence structure for Weslr."""
        return {
            "introspection": {
                "detected_perturbations": len(self.get_unresolved_perturbations()),
                "resolved_perturbations": len([p for p in self.perturbations if p.resolution]),
                "total_perturbations": len(self.perturbations),
                "confidence_signals": len(self.confidence_signals),
                "high_severity_perturbations": len([p for p in self.perturbations if p.severity >= 0.8])
            },
            "confidence_tracking": {
                "avg_confidence": sum(s.confidence for s in self.confidence_signals) / max(1, len(self.confidence_signals)),
                "confidence_deviation": sum(s.deviation or 0 for s in self.confidence_signals) / max(1, len(self.confidence_signals)),
                "total_signales": len(self.confidence_signals)
            },
            "self_referential": {
                "total_events": len(self.introspection_history),
                "events_with_markers": len([e for e in self.introspection_history if e.self_referential_markers]),
                "markers_detected": list(set(
                    m for e in self.introspection_history for m in e.self_referential_markers
                ))
            },
            "timestamps": {
                "first_event": min((e.timestamp for e in self.introspection_history), default=0),
                "last_event": max((e.timestamp for e in self.introspection_history), default=0)
            }
        }


# Global monitor instance
_introspection_monitor: Optional[IntrospectionMonitor] = None


def get_introspection_monitor() -> IntrospectionMonitor:
    """Get or create the global introspection monitor."""
    global _introspection_monitor
    if _introspection_monitor is None:
        _introspection_monitor = IntrospectionMonitor.load_history()
    return _introspection_monitor


def save_introspection_history(
    monitor: IntrospectionMonitor = None,
    path: Path = INTROSPECTION_HISTORY_PATH
):
    """Save introspection history to file."""
    if monitor is None:
        global _introspection_monitor
        monitor = _introspection_monitor
    if monitor:
        monitor.save_history(path)


# CLI interface
def cli_introspect():
    """CLI entry point for introspection monitoring."""
    import sys

    monitor = get_introspection_monitor()

    if len(sys.argv) < 2:
        print("Usage: python introspection.py <command>")
        print("Commands:")
        print("  status - Show current introspection status")
        print("  list [limit] - List perturbations")
        print("  resolve <id> - Mark perturbation as resolved")
        print("  evidence - Show self-evidence structure")
        return

    command = sys.argv[1]

    if command == "status":
        unresolved = monitor.get_unresolved_perturbations()
        print(f"Perturbations: {len(unresolved)} unresolved")
        print(f"Confidence signals: {len(monitor.confidence_signals)} total")
        print(f"Self-referential events: {len(monitor.introspection_history)}")

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        perturbations = monitor.perturbations[:limit]
        for p in perturbations:
            status = "RESOLVED" if p.resolution else "UNRESOLVED"
            print(f"{p.id}: {p.type.value} ({p.severity:.2f}) - {status}")

    elif command == "resolve":
        if len(sys.argv) < 3:
            print("Usage: introspection resolve <perturbation_id>")
            return
        for p in monitor.perturbations:
            if p.id == sys.argv[2]:
                p.resolve("manually resolved via CLI")
                monitor.save_history()
                print(f"✓ Resolved perturbation {sys.argv[2]}")
                return
        print(f"Perturbation {sys.argv[2]} not found")

    elif command == "evidence":
        evidence = monitor.get_self_evidence()
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    cli_introspect()
