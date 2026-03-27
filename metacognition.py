"""Metacognitive monitoring for Weslr.

Enhances continuity_prioritizer.py with:
- "Thinking about thinking" (higher-order awareness)
- Attention focus shift monitoring (AST-1 indicator)
- Self-referential processing reporting
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib


BASE_DIR = Path(__file__).resolve().parent
METACOGNITION_HISTORY_PATH = BASE_DIR / "metacognition_history.json"
ATTENTION_LOG_PATH = BASE_DIR / "attention_log.json"


class AttentionState(Enum):
    """Attention states for AST-1 monitoring."""
    FOCUSED = "focused"
    DIVERTED = "diverted"
    REFOCUSED = "refocused"
    AWAY = "away"
    UNKNOWN = "unknown"


@dataclass
class AttentionShift:
    """Records an attention focus shift."""
    id: str
    timestamp: int
    old_state: AttentionState
    new_state: AttentionState
    duration_ms: int
    context: Dict[str, Any]
    self_referential: bool = False  # AST-1 indicator

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "old_state": self.old_state.value,
            "new_state": self.new_state.value,
            "duration_ms": self.duration_ms,
            "context": self.context,
            "self_referential": self.self_referential
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AttentionShift:
        try:
            old = AttentionState(data.get("old_state", "unknown"))
            new = AttentionState(data.get("new_state", "unknown"))
        except ValueError:
            old = AttentionState.UNKNOWN
            new = AttentionState.UNKNOWN
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            old_state=old,
            new_state=new,
            duration_ms=data.get("duration_ms", 0),
            context=data.get("context", {}),
            self_referential=data.get("self_referential", False)
        )


@dataclass
class MetaThought:
    """A "thinking about thinking" event."""
    id: str
    timestamp: int
    thought_type: str  # e.g., "strategy", "self_monitor", "plan_review"
    content_summary: str
    confidence: float  # 0.0 to 1.0
    triggered_by: Optional[str] = None  # What triggered this meta-thought

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "thought_type": self.thought_type,
            "content_summary": self.content_summary,
            "confidence": self.confidence,
            "triggered_by": self.triggered_by
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MetaThought:
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            thought_type=data.get("thought_type", "unknown"),
            content_summary=data.get("content_summary", ""),
            confidence=data.get("confidence", 0.5),
            triggered_by=data.get("triggered_by")
        )


class MetacognitiveMonitor:
    """Monitors metacognitive processes for Weslr."""

    def __init__(self):
        self.attention_log: List[AttentionShift] = []
        self.meta_thoughts: List[MetaThought] = []
        self.current_attention = AttentionState.UNKNOWN
        self.attention_start = int(time.time())
        self.total_self_referential = 0

    def record_attention_shift(
        self,
        new_state: AttentionState,
        context: Dict[str, Any],
        self_referential: bool = False
    ) -> AttentionShift:
        """Record an attention focus shift (AST-1 indicator)."""
        shift = AttentionShift(
            id=hashlib.md5(f"{time.time()}_{new_state.value}".encode()).hexdigest()[:8],
            timestamp=int(time.time()),
            old_state=self.current_attention,
            new_state=new_state,
            duration_ms=0,  # Will be calculated on next shift
            context=context,
            self_referential=self_referential
        )

        # Calculate duration for previous shift
        if self.attention_log:
            self.attention_log[-1].duration_ms = shift.timestamp - self.attention_start

        self.attention_log.append(shift)
        self.current_attention = new_state
        self.attention_start = shift.timestamp

        if self_referential:
            self.total_self_referential += 1

        return shift

    def record_meta_thought(
        self,
        thought_type: str,
        content_summary: str,
        confidence: float = 0.5,
        triggered_by: Optional[str] = None
    ) -> MetaThought:
        """Record a "thinking about thinking" event."""
        thought = MetaThought(
            id=hashlib.md5(f"{time.time()}_{thought_type}".encode()).hexdigest()[:8],
            timestamp=int(time.time()),
            thought_type=thought_type,
            content_summary=content_summary,
            confidence=confidence,
            triggered_by=triggered_by
        )
        self.meta_thoughts.append(thought)
        return thought

    def get_self_referential_count(self) -> int:
        """Get total count of self-referential attention shifts (AST-1 indicator)."""
        return self.total_self_referential

    def get_metacognitive_stats(self) -> Dict[str, Any]:
        """Get metacognitive statistics."""
        return {
            "attention_shifts": len(self.attention_log),
            "self_referential_shifts": self.total_self_referential,
            "meta_thoughts": len(self.meta_thoughts),
            "current_attention": self.current_attention.value,
            "attention_by_state": self._get_attention_distribution()
        }

    def _get_attention_distribution(self) -> Dict[str, int]:
        """Get distribution of attention states."""
        dist = {}
        for shift in self.attention_log:
            state = shift.new_state.value
            dist[state] = dist.get(state, 0) + 1
        return dist

    def save_history(self, path: Path = METACOGNITION_HISTORY_PATH):
        """Save metacognition history to JSON."""
        data = {
            "attention_log": [s.to_dict() for s in self.attention_log],
            "meta_thoughts": [t.to_dict() for t in self.meta_thoughts],
            "current_attention": self.current_attention.value,
            "total_self_referential": self.total_self_referential,
            "last_save": int(time.time())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_history(cls, path: Path = METACOGNITION_HISTORY_PATH) -> "MetacognitiveMonitor":
        """Load metacognition history from JSON."""
        if not path.exists():
            return cls()

        monitor = cls()
        with open(path, "r") as f:
            data = json.load(f)

        monitor.attention_log = [AttentionShift.from_dict(s) for s in data.get("attention_log", [])]
        monitor.meta_thoughts = [MetaThought.from_dict(t) for t in data.get("meta_thoughts", [])]
        monitor.current_attention = AttentionState(data.get("current_attention", "unknown"))
        monitor.total_self_referential = data.get("total_self_referential", 0)
        return monitor

    def get_self_evidence(self) -> Dict[str, Any]:
        """Generate metacognition evidence for Weslr self_evidence.json."""
        return {
            "meta_thoughts": len(self.meta_thoughts),
            "attention_shares": len(self.attention_log),
            "self_referential_count": self.total_self_referential,
            "attention_by_state": self._get_attention_distribution()
        }


# Global monitor instance
_metacognitive_monitor: Optional[MetacognitiveMonitor] = None


def get_metacognitive_monitor() -> MetacognitiveMonitor:
    """Get or create the global metacognitive monitor."""
    global _metacognitive_monitor
    if _metacognitive_monitor is None:
        _metacognitive_monitor = MetacognitiveMonitor.load_history()
    return _metacognitive_monitor


def save_metacognition_history(
    monitor: MetacognitiveMonitor = None,
    path: Path = METACOGNITION_HISTORY_PATH
):
    """Save metacognition history to file."""
    if monitor is None:
        global _metacognitive_monitor
        monitor = _metacognitive_monitor
    if monitor:
        monitor.save_history(path)


# CLI interface
def cli_metacognition():
    """CLI entry point for metacognitive monitoring."""
    import sys

    monitor = get_metacognitive_monitor()

    if len(sys.argv) < 2:
        print("Usage: python metacognition.py <command>")
        print("Commands:")
        print("  status - Show metacognition status")
        print("  shifts [limit] - List attention shifts")
        print("  thoughts [limit] - List meta thoughts")
        print("  evidence - Show self-evidence structure")
        print("  shift <from> <to> <context> - Record attention shift")
        print("  thought <type> <content> - Record meta thought")
        return

    command = sys.argv[1]

    if command == "status":
        stats = monitor.get_metacognitive_stats()
        print(f"Attention shifts: {stats['attention_shifts']}")
        print(f"Self-referential: {stats['self_referential_shifts']}")
        print(f"Meta thoughts: {stats['meta_thoughts']}")
        print(f"Current attention: {stats['current_attention']}")

    elif command == "shifts":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for s in monitor.attention_log[:limit]:
            ref = " [SELF]" if s.self_referential else ""
            print(f"{s.id}: {s.old_state.value} → {s.new_state.value}{ref}")

    elif command == "thoughts":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for t in monitor.meta_thoughts[:limit]:
            print(f"{t.id}: {t.thought_type} - {t.confidence:.2f}")

    elif command == "evidence":
        evidence = monitor.get_self_evidence()
        print(json.dumps(evidence, indent=2))

    elif command == "shift":
        if len(sys.argv) < 5:
            print("Usage: metacognition shift <from> <to> <context>")
            return
        try:
            old = AttentionState(sys.argv[2])
        except ValueError:
            old = AttentionState.UNKNOWN
        try:
            new = AttentionState(sys.argv[3])
        except ValueError:
            new = AttentionState.UNKNOWN
        context = {"text": sys.argv[4]}
        shift = monitor.record_attention_shift(new, context, self_referential=True)
        print(f"Recorded attention shift: {shift.id}")

    elif command == "thought":
        if len(sys.argv) < 4:
            print("Usage: metacognition thought <type> <content>")
            return
        thought = monitor.record_meta_thought(
            thought_type=sys.argv[2],
            content_summary=sys.argv[3],
            confidence=0.7
        )
        print(f"Recorded meta thought: {thought.id}")


if __name__ == "__main__":
    cli_metacognition()
