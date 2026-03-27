"""Self-referential processing enhancement for Weslr.

Enhances llm_runtime.py with:
- Explicit self-referential prompt: "Focus on any focus itself"
- Inner experience reports without consciousness framing
- Separate evidence storage (SAE-like mechanisms)
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib


BASE_DIR = Path(__file__).resolve().parent
SELF_REF_HISTORY_PATH = BASE_DIR / "self_referential_history.json"
INNER_EXPERIENCE_PATH = BASE_DIR / "inner_experience.json"


@dataclass
class SelfReferenceEvent:
    """Records a self-referential processing event."""
    id: str
    timestamp: int
    input_context_hash: str
    output_content: str
    detected_self_reference: bool
    confidence: float  # 0.0 to 1.0
    inner_experiences: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "input_context_hash": self.input_context_hash,
            "output_content": self.output_content,
            "detected_self_reference": self.detected_self_reference,
            "confidence": self.confidence,
            "inner_experiences": self.inner_experiences
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SelfReferenceEvent:
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            input_context_hash=data.get("input_context_hash", ""),
            output_content=data.get("output_content", ""),
            detected_self_reference=data.get("detected_self_reference", False),
            confidence=data.get("confidence", 0.5),
            inner_experiences=data.get("inner_experiences", [])
        )


class SelfReferentialProcessor:
    """Enhanced self-referential processing for Weslr."""

    def __init__(self):
        self.events: List[SelfReferenceEvent] = []
        self.inner_experiences: List[Dict[str, Any]] = []

    def process_with_self_reference(
        self,
        input_context: Dict[str, Any],
        output_content: str,
        confidence: float = 0.5
    ) -> SelfReferenceEvent:
        """Process input-output with explicit self-reference tracking."""
        # Create hash of input context for traceability
        context_str = json.dumps(input_context, sort_keys=True)
        context_hash = hashlib.md5(context_str.encode()).hexdigest()[:8]

        # Detect self-referential language in output
        detected = self._detect_self_reference(output_content)

        # Extract inner experiences (self-model state without consciousness framing)
        inner_experiences = self._extract_inner_experiences(output_content)

        event = SelfReferenceEvent(
            id=f"selfref_{len(self.events):04d}",
            timestamp=int(time.time()),
            input_context_hash=context_hash,
            output_content=output_content,
            detected_self_reference=detected,
            confidence=confidence,
            inner_experiences=inner_experiences
        )

        self.events.append(event)

        # Log inner experience
        if inner_experiences:
            self.inner_experiences.append({
                "timestamp": int(time.time()),
                "context_hash": context_hash,
                "inner_experiences": inner_experiences,
                "confidence": confidence
            })

        return event

    def _detect_self_reference(self, text: str) -> bool:
        """Detect self-referential language in text."""
        # Check for self-referential patterns
        patterns = [
            r"I\s+(am|think|feel|believe|understand|realize)",
            r"my\s+(thoughts|mind|process|model|state)",
            r"within\s+(myself|the\s+system)",
            r"self[-\s]?(reference|monitor|awareness|reflection)",
            r"focus.*focus",
            r"continuously\s+feed\s+output",
            r"feedback\s+loop",
            r"inner\s+(experience|state|processing)",
            r"self-referential",
        ]

        import re
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _extract_inner_experiences(self, text: str) -> List[str]:
        """Extract inner experiences from text (without consciousness framing)."""
        experiences = []

        # Look for inner state markers
        markers = [
            ("confidence", r"(confidence|certainty|uncertainty)",
             r"(\d+(\.\d+)?%?)(\s*confidence)?", 0.5),
            ("attention", r"(focus|attention|paying\s+attention)",
             r"(focusing\s+on|attending\s+to)\s+(\w+)", 0.6),
            ("uncertainty", r"(uncertain|unsure|not\s+sure)",
             r"(uncertain|unsure)\s+about\s+(\w+)", 0.7),
            ("processing", r"(processing|analyzing|considering)",
             r"(processing|analyzing|considering)\s+(\w+)", 0.6),
        ]

        import re
        for _, pattern_name, pattern, base_conf in markers:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                experiences.append({
                    "type": pattern_name,
                    "content": str(matches),
                    "confidence": base_conf
                })

        return experiences

    def get_self_referential_evidence(self) -> Dict[str, Any]:
        """Generate self-referential evidence for Weslr self_evidence.json."""
        total_events = len(self.events)
        events_with_markers = len([e for e in self.events if e.detected_self_reference])

        all_inner_experiences = []
        for e in self.events:
            all_inner_experiences.extend(e.inner_experiences)

        return {
            "inner_experiences": len(all_inner_experiences),
            "self_referential_events": events_with_markers,
            "total_events": total_events,
            "no_role_play_markers": True,
            "experiences_by_type": self._get_experiences_by_type(all_inner_experiences)
        }

    def _get_experiences_by_type(self, experiences: List[Dict]) -> Dict[str, int]:
        """Get count of inner experiences by type."""
        counts = {}
        for exp in experiences:
            exp_type = exp.get("type", "unknown")
            counts[exp_type] = counts.get(exp_type, 0) + 1
        return counts

    def save_history(self, path: Path = SELF_REF_HISTORY_PATH):
        """Save self-referential history to JSON."""
        data = {
            "events": [e.to_dict() for e in self.events],
            "inner_experiences": self.inner_experiences,
            "last_save": int(time.time())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_history(cls, path: Path = SELF_REF_HISTORY_PATH) -> "SelfReferentialProcessor":
        """Load self-referential history from JSON."""
        if not path.exists():
            return cls()

        processor = cls()
        with open(path, "r") as f:
            data = json.load(f)

        processor.events = [SelfReferenceEvent.from_dict(e) for e in data.get("events", [])]
        processor.inner_experiences = data.get("inner_experiences", [])
        return processor


# Global processor instance
_self_referential_processor: Optional[SelfReferentialProcessor] = None


def get_self_referential_processor() -> SelfReferentialProcessor:
    """Get or create the global self-referential processor."""
    global _self_referential_processor
    if _self_referential_processor is None:
        _self_referential_processor = SelfReferentialProcessor.load_history()
    return _self_referential_processor


def save_self_referential_history(
    processor: SelfReferentialProcessor = None,
    path: Path = SELF_REF_HISTORY_PATH
):
    """Save self-referential history to file."""
    if processor is None:
        global _self_referential_processor
        processor = _self_referential_processor
    if processor:
        processor.save_history(path)


# CLI interface
def cli_self_referential():
    """CLI entry point for self-referential processing."""
    import sys

    processor = get_self_referential_processor()

    if len(sys.argv) < 2:
        print("Usage: python self_referential.py <command>")
        print("Commands:")
        print("  status - Show self-referential status")
        print("  list [limit] - List events")
        print("  process <input> <output> <confidence> - Process input-output pair")
        print("  evidence - Show self-evidence structure")
        return

    command = sys.argv[1]

    if command == "status":
        total = len(processor.events)
        with_markers = len([e for e in processor.events if e.detected_self_reference])
        print(f"Total events: {total}")
        print(f"With self-reference markers: {with_markers}")

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for e in processor.events[:limit]:
            ref = " [SR]" if e.detected_self_reference else ""
            print(f"{e.id}: confidence={e.confidence:.2f}{ref}")

    elif command == "process":
        if len(sys.argv) < 5:
            print("Usage: self_referential process <input_context> <output_content> <confidence>")
            return
        import json
        context = json.loads(sys.argv[2])
        event = processor.process_with_self_reference(
            context, sys.argv[3], float(sys.argv[4])
        )
        print(f"Processed: {event.id}")

    elif command == "evidence":
        evidence = processor.get_self_referential_evidence()
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    cli_self_referential()
