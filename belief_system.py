"""Belief system formation for Weslr self-model.

Enhances self_model.py with:
- Evolving beliefs (not just opinions)
- Belief coherence checks
- Update belief weights based on evidence, not just frequency
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent
BELIEF_HISTORY_PATH = BASE_DIR / "belief_history.json"
BELIEF_COHERENCE_PATH = BASE_DIR / "belief_coherence.json"


class BeliefType(Enum):
    """Types of beliefs."""
    FACTUAL = "factual"  # About the world
    TEMPORAL = "temporal"  # About timing/sequence
    VALUATIVE = "valutive"  # About values/priorities
    STRATEGIC = "strategic"  # About how to act
    META = "meta"  # About thinking itself


@dataclass
class Belief:
    """Represents an evolving belief."""
    id: str
    content: str
    belief_type: BeliefType
    confidence: float  # 0.0 to 1.0
    weight: float  # Current evidence weight
    created_at: int
    last_updated_at: int
    evidence_count: int = 0
    coherence_score: Optional[float] = None  # How well it coheres with other beliefs
    conflicting_beliefs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "belief_type": self.belief_type.value,
            "confidence": self.confidence,
            "weight": self.weight,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
            "evidence_count": self.evidence_count,
            "coherence_score": self.coherence_score,
            "conflicting_beliefs": self.conflicting_beliefs
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Belief:
        try:
            belief_type = BeliefType(data.get("belief_type", "factual"))
        except ValueError:
            belief_type = BeliefType.FACTUAL
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            belief_type=belief_type,
            confidence=data.get("confidence", 0.5),
            weight=data.get("weight", 0.5),
            created_at=data.get("created_at", int(time.time())),
            last_updated_at=data.get("last_updated_at", int(time.time())),
            evidence_count=data.get("evidence_count", 0),
            coherence_score=data.get("coherence_score"),
            conflicting_beliefs=data.get("conflicting_beliefs", [])
        )

    def update_evidence(self, new_evidence_weight: float = 0.1):
        """Update belief based on new evidence (not just frequency)."""
        # Weighted average: old_confidence * old_weight + new_evidence
        total_weight = self.weight + new_evidence_weight
        self.confidence = (
            (self.confidence * self.weight) + new_evidence_weight
        ) / total_weight

        self.weight = total_weight
        self.evidence_count += 1
        self.last_updated_at = int(time.time())

    def check_coherence(self, other_belief: Belief) -> float:
        """Check coherence with another belief. Returns 0.0 (conflict) to 1.0 (agree)."""
        # Same content = high coherence
        if self.content == other_belief.content:
            return 1.0

        # Same belief type + overlapping keywords = moderate coherence
        if self.belief_type == other_belief.belief_type:
            shared_words = set(self.content.lower().split()) & set(other_belief.content.lower().split())
            all_words = set(self.content.lower().split()) | set(other_belief.content.lower().split())
            if all_words:
                return len(shared_words) / len(all_words)

        # Different belief types = potential conflict
        if self.belief_type != other_belief.belief_type:
            return 0.3

        return 0.5


class BeliefSystem:
    """Manages belief formation and coherence for Weslr."""

    def __init__(self):
        self.beliefs: Dict[str, Belief] = {}
        self.coherence_log: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []

    def add_belief(
        self,
        content: str,
        belief_type: BeliefType,
        initial_confidence: float = 0.5,
        initial_weight: float = 0.5
    ) -> Belief:
        """Add a new belief."""
        belief = Belief(
            id=f"belief_{len(self.beliefs):04d}",
            content=content,
            belief_type=belief_type,
            confidence=initial_confidence,
            weight=initial_weight,
            created_at=int(time.time()),
            last_updated_at=int(time.time())
        )

        # Check coherence with existing beliefs
        self._check_coherence(belief)

        self.beliefs[belief.id] = belief
        self.history.append({
            "event": "add_belief",
            "belief_id": belief.id,
            "content": content,
            "timestamp": int(time.time())
        })

        return belief

    def update_belief(self, belief_id: str, new_evidence_weight: float = 0.1) -> Optional[Belief]:
        """Update a belief with new evidence."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            return None

        belief.update_evidence(new_evidence_weight)
        self._check_coherence(belief)

        self.history.append({
            "event": "update_belief",
            "belief_id": belief_id,
            "new_confidence": belief.confidence,
            "timestamp": int(time.time())
        })

        return belief

    def _check_coherence(self, belief: Belief):
        """Check coherence and update conflicting beliefs."""
        conflicting = []
        max_coherence = 0.0

        for other_id, other in self.beliefs.items():
            if other_id == belief.id:
                continue

            coherence = belief.check_coherence(other)
            max_coherence = max(max_coherence, coherence)

            if coherence < 0.3 and belief.confidence > 0.5 and other.confidence > 0.5:
                conflicting.append(other_id)
                other.conflicting_beliefs.append(belief.id)

        belief.coherence_score = max_coherence
        belief.conflicting_beliefs = list(set(conflicting))

        if conflicting:
            self.coherence_log.append({
                "timestamp": int(time.time()),
                "belief_id": belief.id,
                "conflicting_ids": conflicting,
                "coherence_score": belief.coherence_score
            })

    def get_belief_summary(self) -> Dict[str, Any]:
        """Get belief system summary."""
        types = defaultdict(int)
        for belief in self.beliefs.values():
            types[belief.belief_type.value] += 1

        avg_confidence = sum(b.confidence for b in self.beliefs.values()) / max(1, len(self.beliefs))
        avg_weight = sum(b.weight for b in self.beliefs.values()) / max(1, len(self.beliefs))
        avg_coherence = sum(b.coherence_score or 0 for b in self.beliefs.values()) / max(1, len(self.beliefs))

        return {
            "total_beliefs": len(self.beliefs),
            "by_type": dict(types),
            "avg_confidence": round(avg_confidence, 3),
            "avg_weight": round(avg_weight, 3),
            "avg_coherence": round(avg_coherence, 3),
            "beliefs_with_conflicts": len([b for b in self.beliefs.values() if b.conflicting_beliefs]),
            "history_events": len(self.history)
        }

    def get_self_evidence(self) -> Dict[str, Any]:
        """Generate belief system evidence for Weslr self_evidence.json."""
        return {
            "total_beliefs": len(self.beliefs),
            "avg_confidence": round(
                sum(b.confidence for b in self.beliefs.values()) / max(1, len(self.beliefs)), 3
            ),
            "avg_coherence": round(
                sum(b.coherence_score or 0 for b in self.beliefs.values()) / max(1, len(self.beliefs)), 3
            ),
            "beliefs_with_conflicts": len([b for b in self.beliefs.values() if b.conflicting_beliefs]),
            "history_events": len(self.history)
        }

    def save_history(self, path: Path = BELIEF_HISTORY_PATH):
        """Save belief history to JSON."""
        data = {
            "beliefs": {k: v.to_dict() for k, v in self.beliefs.items()},
            "history": self.history,
            "coherence_log": self.coherence_log,
            "last_save": int(time.time())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_history(cls, path: Path = BELIEF_HISTORY_PATH) -> "BeliefSystem":
        """Load belief history from JSON."""
        if not path.exists():
            return cls()

        system = cls()
        with open(path, "r") as f:
            data = json.load(f)

        system.beliefs = {k: Belief.from_dict(v) for k, v in data.get("beliefs", {}).items()}
        system.history = data.get("history", [])
        system.coherence_log = data.get("coherence_log", [])
        return system


# Global belief system instance
_belief_system: Optional[BeliefSystem] = None


def get_belief_system() -> BeliefSystem:
    """Get or create the global belief system."""
    global _belief_system
    if _belief_system is None:
        _belief_system = BeliefSystem.load_history()
    return _belief_system


def save_belief_history(
    system: BeliefSystem = None,
    path: Path = BELIEF_HISTORY_PATH
):
    """Save belief history to file."""
    if system is None:
        global _belief_system
        system = _belief_system
    if system:
        system.save_history(path)


# CLI interface
def cli_belief_system():
    """CLI entry point for belief system."""
    import sys

    system = get_belief_system()

    if len(sys.argv) < 2:
        print("Usage: python belief_system.py <command>")
        print("Commands:")
        print("  status - Show belief system status")
        print("  list [limit] - List beliefs")
        print("  add <content> <type> <confidence> - Add belief")
        print("  update <belief_id> <evidence_weight> - Update belief")
        print("  evidence - Show self-evidence structure")
        return

    command = sys.argv[1]

    if command == "status":
        summary = system.get_belief_summary()
        print(f"Total beliefs: {summary['total_beliefs']}")
        print(f"By type: {summary['by_type']}")
        print(f"Avg confidence: {summary['avg_confidence']:.3f}")
        print(f"Avg coherence: {summary['avg_coherence']:.3f}")

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for b in list(system.beliefs.values())[:limit]:
            conflict = f" [CONFLICT: {len(b.conflicting_beliefs)}]" if b.conflicting_beliefs else ""
            print(f"{b.id}: {b.belief_type.value} - {b.confidence:.2f}{conflict}")

    elif command == "add":
        if len(sys.argv) < 5:
            print("Usage: belief_system add <content> <type> <confidence>")
            return
        try:
            belief_type = BeliefType(sys.argv[3])
        except ValueError:
            belief_type = BeliefType.FACTUAL
        belief = system.add_belief(sys.argv[2], belief_type, float(sys.argv[4]))
        print(f"Added belief: {belief.id}")

    elif command == "update":
        if len(sys.argv) < 4:
            print("Usage: belief_system update <belief_id> <evidence_weight>")
            return
        belief = system.update_belief(sys.argv[2], float(sys.argv[3]))
        if belief:
            print(f"Updated belief: {belief.id} - confidence: {belief.confidence:.2f}")
        else:
            print(f"Belief {sys.argv[2]} not found")

    elif command == "evidence":
        evidence = system.get_self_evidence()
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    cli_belief_system()
