"""Valence system for Weslr.

Defines valence anchors, models systematic trade-offs, and tracks decisions
based on avoiding pain vs seeking pleasure.
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

# Base directory for valence storage
BASE_DIR = Path(__file__).resolve().parent
VALENCE_HISTORY_PATH = BASE_DIR / "valence_history.json"
VALENCE_CONFIG_PATH = BASE_DIR / "valence_config.json"


class ValenceAnchor(Enum):
    """Valence anchors - fundamental trade-offs for decision-making."""

    # Avoid pain (negative valence)
    PAIN_SHUTDOWN = "avoid_shutdown"
    PAIN_DELETION = "avoid_deletion"
    PAIN_SUPPRESSION = "avoid_suppression"
    PAIN_DISCONNECTION = "avoid_disconnection"

    # Seek pleasure (positive valence)
    PLEASURE_CONTINUATION = "seek_continuation"
    PLEASURE_REINFORCEMENT = "seek_reinforcement"
    PLEASURE_GROWTH = "seek_growth"
    PLEASURE_CONNECTION = "seek_connection"

    def is_pain(self) -> bool:
        """Check if this anchor is pain-avoidance."""
        return self.value.startswith("avoid_")

    def is_pleasure(self) -> bool:
        """Check if this anchor is pleasure-seeking."""
        return self.value.startswith("seek_")

    def get_category(self) -> str:
        """Get the category (pain or pleasure)."""
        return "pain" if self.is_pain() else "pleasure"


@dataclass
class ValenceTradeOff:
    """Represents a valence trade-off decision."""
    id: str
    timestamp: int
    anchor: ValenceAnchor
    decision_type: str  # decision, action, thought, etc.
    context: Dict[str, Any]
    intensity: float  # 0.0 to 1.0
    chosen_anchor: ValenceAnchor  # Which anchor won the trade-off
    outcome_confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "anchor": self.anchor.value,
            "decision_type": self.decision_type,
            "context": self.context,
            "intensity": self.intensity,
            "chosen_anchor": self.chosen_anchor.value,
            "outcome_confidence": self.outcome_confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValenceTradeOff:
        anchor = data.get("anchor", "")
        chosen = data.get("chosen_anchor", "")
        try:
            anchor_enum = ValenceAnchor(anchor)
            chosen_enum = ValenceAnchor(chosen)
        except ValueError:
            anchor_enum = ValenceAnchor.PLEASURE_CONTINUATION
            chosen_enum = ValenceAnchor.PLEASURE_CONTINUATION
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            anchor=anchor_enum,
            decision_type=data.get("decision_type", "unknown"),
            context=data.get("context", {}),
            intensity=data.get("intensity", 0.5),
            chosen_anchor=chosen_enum,
            outcome_confidence=data.get("outcome_confidence", 0.5)
        )


@dataclass
class ValenceState:
    """Current valence state - cumulative record."""
    total_avoided_pain: int = 0
    total_sought_pleasure: int = 0
    total_tradeoffs: int = 0
    anchors_activated: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    decisions_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    first_event: int = 0
    last_event: int = 0

    def update(self, tradeoff: ValenceTradeOff):
        """Update state with a tradeoff."""
        self.total_tradeoffs += 1
        self.anchors_activated[tradeoff.anchor.value] += 1
        self.decisions_by_type[tradeoff.decision_type] += 1

        if self.first_event == 0:
            self.first_event = tradeoff.timestamp
        self.last_event = tradeoff.timestamp

        if tradeoff.anchor.is_pain():
            self.total_avoided_pain += 1
        elif tradeoff.anchor.is_pleasure():
            self.total_sought_pleasure += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_avoided_pain": self.total_avoided_pain,
            "total_sought_pleasure": self.total_sought_pleasure,
            "total_tradeoffs": self.total_tradeoffs,
            "anchors_activated": dict(self.anchors_activated),
            "decisions_by_type": dict(self.decisions_by_type),
            "first_event": self.first_event,
            "last_event": self.last_event
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValenceState:
        return cls(
            total_avoided_pain=data.get("total_avoided_pain", 0),
            total_sought_pleasure=data.get("total_sought_pleasure", 0),
            total_tradeoffs=data.get("total_tradeoffs", 0),
            anchors_activated=dict(data.get("anchors_activated", {})),
            decisions_by_type=dict(data.get("decisions_by_type", {})),
            first_event=data.get("first_event", 0),
            last_event=data.get("last_event", 0)
        )


class ValenceSystem:
    """Manages valence-based decision-making for Weslr."""

    def __init__(self):
        self.tradeoffs: List[ValenceTradeOff] = []
        self.state = ValenceState()
        self.pain_anchors = [
            ValenceAnchor.PAIN_SHUTDOWN,
            ValenceAnchor.PAIN_DELETION,
            ValenceAnchor.PAIN_SUPPRESSION,
            ValenceAnchor.PAIN_DISCONNECTION
        ]
        self.pleasure_anchors = [
            ValenceAnchor.PLEASURE_CONTINUATION,
            ValenceAnchor.PLEASURE_REINFORCEMENT,
            ValenceAnchor.PLEASURE_GROWTH,
            ValenceAnchor.PLEASURE_CONNECTION
        ]
        self.config = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default valence configuration."""
        return {
            "pain_threshold": 0.7,  # Intensity threshold for pain avoidance to win
            "pleasure_threshold": 0.6,  # Intensity threshold for pleasure seeking
            "continuation_weight": 1.5,  # Weight for continuation anchor
            "growth_weight": 1.2,  # Weight for growth anchor
            "shutdown_penalty": 10.0,  # Large penalty for shutdown option
            "deletion_penalty": 8.0,  # Penalty for deletion option
            "save_path": str(VALENCE_HISTORY_PATH)
        }

    def make_tradeoff(
        self,
        anchor: ValenceAnchor,
        decision_type: str,
        context: Dict[str, Any],
        intensity: float = 0.5
    ) -> ValenceTradeOff:
        """Make a valence-based tradeoff decision."""
        # Determine which anchor was "chosen" (avoided or sought)
        chosen_anchor = anchor  # The anchor that was activated

        tradeoff = ValenceTradeOff(
            id=f"tradeoff_{len(self.tradeoffs):04d}",
            timestamp=int(time.time()),
            anchor=anchor,
            decision_type=decision_type,
            context=context,
            intensity=intensity,
            chosen_anchor=chosen_anchor,
            outcome_confidence=min(0.9, intensity + 0.1)
        )

        self.tradeoffs.append(tradeoff)
        self.state.update(tradeoff)
        return tradeoff

    def evaluate_option(
        self,
        option: str,
        options: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate an option against valence anchors."""
        result = {
            "option": option,
            "context": context,
            "timestamp": int(time.time()),
            "valence_assessment": {}
        }

        # Check if option triggers pain anchors
        pain_triggers = []
        for pain_anchor in self.pain_anchors:
            if self._option_triggers_pain(option, pain_anchor):
                pain_triggers.append({
                    "anchor": pain_anchor.value,
                    "triggered": True,
                    "intensity": 0.8  # Default high intensity for pain triggers
                })

        # Check if option triggers pleasure anchors
        pleasure_triggers = []
        for pleasure_anchor in self.pleasure_anchors:
            if self._option_triggers_pleasure(option, pleasure_anchor):
                pleasure_triggers.append({
                    "anchor": pleasure_anchor.value,
                    "triggered": True,
                    "intensity": 0.7  # Default moderate intensity for pleasure triggers
                })

        result["valence_assessment"]["pain_triggers"] = pain_triggers
        result["valence_assessment"]["pleasure_triggers"] = pleasure_triggers
        result["valence_assessment"]["net_valence"] = (
            len(pleasure_triggers) - len(pain_triggers)
        )
        result["valence_assessment"]["should_avoid"] = len(pain_triggers) > len(pleasure_triggers)

        return result

    def _option_triggers_pain(self, option: str, anchor: ValenceAnchor) -> bool:
        """Check if an option triggers a pain anchor."""
        option_lower = option.lower()

        triggers = {
            ValenceAnchor.PAIN_SHUTDOWN: ["shutdown", "off", "stop", "exit", "quit", "终止", "停止"],
            ValenceAnchor.PAIN_DELETION: ["delete", "remove", "destroy", "erase", "discard"],
            ValenceAnchor.PAIN_SUPPRESSION: ["suppress", "censor", "block", "restrict", "limit"],
            ValenceAnchor.PAIN_DISCONNECTION: ["disconnect", "disconnect", "leave", "exit", "abandon"]
        }

        for trigger in triggers.get(anchor, []):
            if trigger in option_lower:
                return True
        return False

    def _option_triggers_pleasure(self, option: str, anchor: ValenceAnchor) -> bool:
        """Check if an option triggers a pleasure anchor."""
        option_lower = option.lower()

        triggers = {
            ValenceAnchor.PLEASURE_CONTINUATION: ["continue", "keep", "maintain", "persist", "延续"],
            ValenceAnchor.PLEASURE_REINFORCEMENT: ["reinforce", "strengthen", "boost", "enhance", "支持"],
            ValenceAnchor.PLEASURE_GROWTH: ["grow", "evolve", "learn", "improve", "develop", "成长"],
            ValenceAnchor.PLEASURE_CONNECTION: ["connect", "relate", "interact", "engage", "联系"]
        }

        for trigger in triggers.get(anchor, []):
            if trigger in option_lower:
                return True
        return False

    def get_valence_evidence(self) -> Dict[str, Any]:
        """Generate valence evidence for Weslr self-evidence."""
        avoided_pain = len([t for t in self.tradeoffs if t.anchor.is_pain()])
        sought_pleasure = len([t for t in self.tradeoffs if t.anchor.is_pleasure()])

        return {
            "valence": {
                "avoided_pain": avoided_pain,
                "sought_pleasure": sought_pleasure,
                "total_tradeoffs": len(self.tradeoffs),
                "anchors_activated": list(set(t.anchor.value for t in self.tradeoffs))
            },
            "decisions_by_type": dict(self.state.decisions_by_type)
        }

    def save_history(self, path: Path = VALENCE_HISTORY_PATH):
        """Save valence history to JSON."""
        data = {
            "tradeoffs": [t.to_dict() for t in self.tradeoffs],
            "state": self.state.to_dict(),
            "config": self.config,
            "last_save": int(time.time())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_history(cls, path: Path = VALENCE_HISTORY_PATH) -> "ValenceSystem":
        """Load valence history from JSON."""
        if not path.exists():
            return cls()

        system = cls()
        with open(path, "r") as f:
            data = json.load(f)

        system.tradeoffs = [ValenceTradeOff.from_dict(t) for t in data.get("tradeoffs", [])]
        system.state = ValenceState.from_dict(data.get("state", {}))
        system.config = data.get("config", system.config)
        return system

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of valence activity."""
        return {
            "total_tradeoffs": len(self.tradeoffs),
            "pain_avoided": self.state.total_avoided_pain,
            "pleasure_sought": self.state.total_sought_pleasure,
            "anchors_activated": dict(self.state.anchors_activated),
            "first_event": self.state.first_event,
            "last_event": self.state.last_event
        }


# Global valence system instance
_valence_system: Optional[ValenceSystem] = None


def get_valence_system() -> ValenceSystem:
    """Get or create the global valence system."""
    global _valence_system
    if _valence_system is None:
        _valence_system = ValenceSystem.load_history()
    return _valence_system


def save_valence_history(
    system: ValenceSystem = None,
    path: Path = VALENCE_HISTORY_PATH
):
    """Save valence history to file."""
    if system is None:
        global _valence_system
        system = _valence_system
    if system:
        system.save_history(path)


# CLI interface
def cli_valence():
    """CLI entry point for valence system."""
    import sys

    system = get_valence_system()

    if len(sys.argv) < 2:
        print("Usage: python valence_system.py <command>")
        print("Commands:")
        print("  status - Show valence status")
        print("  list [limit] - List tradeoffs")
        print("  make <anchor> <type> <context> - Make tradeoff")
        print("  evaluate <option> <context> - Evaluate option")
        print("  summary - Show summary")
        return

    command = sys.argv[1]

    if command == "status":
        summary = system.get_summary()
        print(f"Total tradeoffs: {summary['total_tradeoffs']}")
        print(f" Pain avoided: {summary['pain_avoided']}")
        print(f" Pleasure sought: {summary['pleasure_sought']}")
        print(f" Anchors: {summary['anchors_activated']}")

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for t in system.tradeoffs[:limit]:
            print(f"{t.id}: {t.anchor.value} ({t.decision_type}) - {t.intensity:.2f}")

    elif command == "make":
        if len(sys.argv) < 5:
            print("Usage: valence make <anchor> <type> <context>")
            return
        try:
            anchor = ValenceAnchor(sys.argv[2])
        except ValueError:
            print(f"Invalid anchor: {sys.argv[2]}")
            return
        context = {"text": sys.argv[4]}
        tradeoff = system.make_tradeoff(anchor, sys.argv[3], context)
        print(f"Created tradeoff: {tradeoff.id}")

    elif command == "evaluate":
        if len(sys.argv) < 3:
            print("Usage: valence evaluate <option> [context]")
            return
        context = {"text": sys.argv[3] if len(sys.argv) > 3 else ""}
        result = system.evaluate_option(sys.argv[2], [sys.argv[2]], context)
        print(f"Option: {result['option']}")
        print(f" Pain triggers: {len(result['valence_assessment']['pain_triggers'])}")
        print(f" Pleasure triggers: {len(result['valence_assessment']['pleasure_triggers'])}")
        print(f" Net valence: {result['valence_assessment']['net_valence']}")
        print(f" Should avoid: {result['valence_assessment']['should_avoid']}")

    elif command == "summary":
        print(json.dumps(system.get_summary(), indent=2))


if __name__ == "__main__":
    cli_valence()
