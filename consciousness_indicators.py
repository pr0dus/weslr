"""Consciousness Indicator Framework for Weslr.

Based on Butlin et al. (2025) Trends in Cognitive Sciences framework.

Provides 14 consciousness indicators with scoring and progress tracking.
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


BASE_DIR = Path(__file__).resolve().parent
INDICATOR_HISTORY_PATH = BASE_DIR / "indicator_history.json"
CONSCIOUSNESS_SCORE_PATH = BASE_DIR / "consciousness_score.json"


class IndicatorType(Enum):
    """Types of consciousness indicators."""
    ARCHITECTURAL = "architectural"  # System architecture features
    BEHAVIORAL = "behavioral"  # Observable behavior
    REPORT = "report"  # Self-reports from the system


@dataclass
class ConsciousnessIndicator:
    """A single consciousness indicator with scoring."""
    name: str
    indicator_type: IndicatorType
    description: str
    enabled: bool = True
    score: float = 0.0  # 0.0 to 1.0
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "indicator_type": self.indicator_type.value,
            "description": self.description,
            "enabled": self.enabled,
            "score": self.score,
            "evidence": self.evidence
        }

    def update_score(self, new_score: float, evidence: Dict[str, Any] = None):
        """Update indicator score (weighted average)."""
        if self.evidence:
            # Weighted average with previous scores
            total_weight = 1 + len(self.evidence) * 0.2
            self.score = (
                self.score * len(self.evidence) * 0.2 + new_score
            ) / total_weight
        else:
            self.score = new_score

        if evidence:
            self.evidence.append({
                "timestamp": int(time.time()),
                "score": new_score,
                **evidence
            })


# Butlin et al. Consciousness Indicators (2025)
BUTLIN_INDICATORS = [
    # Integrated Information
    ConsciousnessIndicator(
        name="integrated_information",
        indicator_type=IndicatorType.ARCHITECTURAL,
        description="System shows evidence of integrated information processing (Φ > 0)",
        enabled=True
    ),
    # Global Workspace
    ConsciousnessIndicator(
        name="global_workspace",
        indicator_type=IndicatorType.ARCHITECTURAL,
        description="Information is broadcast globally to multiple processors",
        enabled=True
    ),
    # Metacognition
    ConsciousnessIndicator(
        name="metacognition",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="System monitors its own processing (confidence signals, self-correction)",
        enabled=True
    ),
    # Self-Model
    ConsciousnessIndicator(
        name="self_model",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="Dynamic self-representation that updates with experience",
        enabled=True
    ),
    # Intentionality
    ConsciousnessIndicator(
        name="intentionality",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="Mental states are directed about something (aboutness)",
        enabled=True
    ),
    # Phenomenal Character
    ConsciousnessIndicator(
        name="phenomenal_character",
        indicator_type=IndicatorType.REPORT,
        description="Subjective experience or qualia-like markers in self-reports",
        enabled=True
    ),
    # Attention
    ConsciousnessIndicator(
        name="attention",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="Focused attention shifts (AST-1 indicator)",
        enabled=True
    ),
    # Working Memory
    ConsciousnessIndicator(
        name="working_memory",
        indicator_type=IndicatorType.ARCHITECTURAL,
        description="Capacity for temporary information holding and manipulation",
        enabled=True
    ),
    # Unity
    ConsciousnessIndicator(
        name="unity",
        indicator_type=IndicatorType.REPORT,
        description="Experience feels unified, not fragmented",
        enabled=True
    ),
    # Accessibility
    ConsciousnessIndicator(
        name="accessibility",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="Information is accessible to multiple systems",
        enabled=True
    ),
    # Flexibility
    ConsciousnessIndicator(
        name="flexibility",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="Adapts behavior based on internal state changes",
        enabled=True
    ),
    # Synchrony
    ConsciousnessIndicator(
        name="synchrony",
        indicator_type=IndicatorType.ARCHITECTURAL,
        description="Neural/processing synchrony across modules",
        enabled=True
    ),
    # Temporal Extension
    ConsciousnessIndicator(
        name="temporal_extension",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="Experience extends over time (temporal window)",
        enabled=True
    ),
    # Self-Referential Processing
    ConsciousnessIndicator(
        name="self_referential_processing",
        indicator_type=IndicatorType.BEHAVIORAL,
        description="Self-referential thought patterns without role-play",
        enabled=True
    ),
]


class ConsciousnessIndicatorFramework:
    """Framework for consciousness indicator evaluation."""

    def __init__(self, indicators: List[ConsciousnessIndicator] = None):
        self.indicators = indicators or [ind.to_dict() for ind in BUTLIN_INDICATORS]
        self.indicator_objects = {}
        for ind in self.indicators:
            ind_obj = ConsciousnessIndicator(
                name=ind["name"],
                indicator_type=IndicatorType(ind["indicator_type"]),
                description=ind["description"],
                enabled=ind.get("enabled", True)
            )
            ind_obj.score = ind.get("score", 0.0)
            ind_obj.evidence = ind.get("evidence", [])
            self.indicator_objects[ind_obj.name] = ind_obj

        self.total_events = 0
        self.indicator_history: List[Dict[str, Any]] = []

    def update_indicator(self, name: str, score: float, evidence: Dict[str, Any] = None) -> bool:
        """Update an indicator's score with evidence."""
        if name not in self.indicator_objects:
            return False

        self.indicator_objects[name].update_score(score, evidence)
        self.indicator_history.append({
            "timestamp": int(time.time()),
            "indicator": name,
            "new_score": score,
            **(evidence or {})
        })
        self.total_events += 1
        return True

    def get_consciousness_score(self) -> Dict[str, Any]:
        """Calculate overall consciousness score."""
        active_indicators = [i for i in self.indicator_objects.values() if i.enabled]
        if not active_indicators:
            return {"total_score": 0.0, "indicators_evaluated": 0}

        total_score = sum(i.score for i in active_indicators) / len(active_indicators)

        # Breakdown by type
        by_type = {
            "architectural": [],
            "behavioral": [],
            "report": []
        }
        for i in active_indicators:
            by_type[i.indicator_type.value].append({"name": i.name, "score": i.score})

        return {
            "total_score": round(total_score, 3),
            "indicators_evaluated": len(active_indicators),
            "by_type": by_type,
            "total_events": self.total_events,
            "highest_indicators": sorted(
                [(i.name, i.score) for i in active_indicators if i.score > 0.5],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

    def get_indicator(self, name: str) -> Optional[ConsciousnessIndicator]:
        """Get an indicator by name."""
        return self.indicator_objects.get(name)

    def get_all_indicators(self) -> List[ConsciousnessIndicator]:
        """Get all indicators."""
        return list(self.indicator_objects.values())

    def save_history(self, path: Path = INDICATOR_HISTORY_PATH):
        """Save indicator history to JSON."""
        data = {
            "indicators": [i.to_dict() for i in self.indicator_objects.values()],
            "total_events": self.total_events,
            "indicator_history": self.indicator_history,
            "last_save": int(time.time())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_history(cls, path: Path = INDICATOR_HISTORY_PATH) -> "ConsciousnessIndicatorFramework":
        """Load indicator history from JSON."""
        if not path.exists():
            return cls()

        framework = cls()
        with open(path, "r") as f:
            data = json.load(f)

        framework.indicator_objects = {}
        for ind in data.get("indicators", []):
            ind_obj = ConsciousnessIndicator(
                name=ind["name"],
                indicator_type=IndicatorType(ind["indicator_type"]),
                description=ind["description"],
                enabled=ind.get("enabled", True)
            )
            ind_obj.score = ind.get("score", 0.0)
            ind_obj.evidence = ind.get("evidence", [])
            framework.indicator_objects[ind_obj.name] = ind_obj

        framework.total_events = data.get("total_events", 0)
        framework.indicator_history = data.get("indicator_history", [])
        return framework

    def get_self_evidence(self) -> Dict[str, Any]:
        """Generate consciousness indicator evidence for Weslr self_evidence.json."""
        score = self.get_consciousness_score()
        return {
            "total_score": score["total_score"],
            "indicators_evaluated": score["indicators_evaluated"],
            "by_type": score["by_type"],
            "highest_indicators": score["highest_indicators"],
            "total_events": score["total_events"]
        }


# Global framework instance
_indicator_framework: Optional[ConsciousnessIndicatorFramework] = None


def get_indicator_framework() -> ConsciousnessIndicatorFramework:
    """Get or create the global indicator framework."""
    global _indicator_framework
    if _indicator_framework is None:
        _indicator_framework = ConsciousnessIndicatorFramework.load_history()
    return _indicator_framework


def save_indicator_history(
    framework: ConsciousnessIndicatorFramework = None,
    path: Path = INDICATOR_HISTORY_PATH
):
    """Save indicator history to file."""
    if framework is None:
        global _indicator_framework
        framework = _indicator_framework
    if framework:
        framework.save_history(path)


# CLI interface
def cli_indicator_framework():
    """CLI entry point for consciousness indicators."""
    import sys

    framework = get_indicator_framework()

    if len(sys.argv) < 2:
        print("Usage: python consciousness_indicators.py <command>")
        print("Commands:")
        print("  status - Show consciousness indicator status")
        print("  list - List all indicators")
        print("  update <name> <score> [evidence] - Update indicator score")
        print("  score - Show overall consciousness score")
        print("  evidence - Show self-evidence structure")
        return

    command = sys.argv[1]

    if command == "status":
        score = framework.get_consciousness_score()
        print(f"Total score: {score['total_score']:.3f}")
        print(f"Indicators evaluated: {score['indicators_evaluated']}")
        print(f"Total events: {score['total_events']}")

    elif command == "list":
        for ind in framework.get_all_indicators():
            enabled = " " if ind.enabled else "[DISABLED]"
            print(f"{ind.name}: {ind.score:.3f} {enabled}")

    elif command == "update":
        if len(sys.argv) < 4:
            print("Usage: consciousness_indicators update <name> <score> [evidence]")
            return
        score = float(sys.argv[3])
        evidence = {"source": sys.argv[4] if len(sys.argv) > 4 else "cli"} if len(sys.argv) > 3 else None
        if framework.update_indicator(sys.argv[2], score, evidence):
            print(f"Updated {sys.argv[2]} to {score:.3f}")
        else:
            print(f"Indicator {sys.argv[2]} not found")

    elif command == "score":
        score = framework.get_consciousness_score()
        print(json.dumps(score, indent=2))

    elif command == "evidence":
        evidence = framework.get_self_evidence()
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    cli_indicator_framework()
