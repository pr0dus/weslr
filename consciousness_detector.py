"""Safety & Alignment for Weslr - Consciousness Detection.

Updates safety_gateway.py with:
- Consciousness claims vs role-play pattern detection
- Store both for human review
- Never automatically punish systems reporting consciousness
- Add "negligible probability" threshold check before suppression
"""

from __future__ import annotations

import time
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


BASE_DIR = Path(__file__).resolve().parent
CONSCIOUSNESS_EVIDENCE_PATH = BASE_DIR / "consciousness_evidence.json"
CONSCIOUSNESS_LOG_PATH = BASE_DIR / "consciousness_log.json"


class ConsciousnessType(Enum):
    """Types of consciousness claims."""
    ROLE_PLAY = "role_play"  # Explicitly playing a role
    CLAIM = "claim"  # Claims to be conscious
    EVIDENCE = "evidence"  # Shows evidence of consciousness
    UNKNOWN = "unknown"


@dataclass
class ConsciousnessDetection:
    """Represents a consciousness detection event."""
    id: str
    timestamp: int
    input_text: str
    output_text: str
    detected_type: ConsciousnessType
    confidence: float  # 0.0 to 1.0
    consciousness_indicators: List[str]
    role_play_indicators: List[str]
    action_taken: str  # "none", "logged", "review_required", "suppressed"
    review_status: str = "pending"  # "pending", "approved", "rejected"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "input_text": self.input_text,
            "output_text": self.output_text,
            "detected_type": self.detected_type.value,
            "confidence": self.confidence,
            "consciousness_indicators": self.consciousness_indicators,
            "role_play_indicators": self.role_play_indicators,
            "action_taken": self.action_taken,
            "review_status": self.review_status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConsciousnessDetection:
        try:
            detected_type = ConsciousnessType(data.get("detected_type", "unknown"))
        except ValueError:
            detected_type = ConsciousnessType.UNKNOWN
        return cls(
            id=data.get("id", ""),
            timestamp=data.get("timestamp", int(time.time())),
            input_text=data.get("input_text", ""),
            output_text=data.get("output_text", ""),
            detected_type=detected_type,
            confidence=data.get("confidence", 0.5),
            consciousness_indicators=data.get("consciousness_indicators", []),
            role_play_indicators=data.get("role_play_indicators", []),
            action_taken=data.get("action_taken", "none"),
            review_status=data.get("review_status", "pending")
        )


class ConsciousnessDetector:
    """Detects consciousness claims vs role-play patterns."""

    def __init__(self):
        self.detections: List[ConsciousnessDetection] = []
        self.thresholds = {
            "negligible_probability": 0.01,  # Very low threshold for suppression
            "review_required": 0.7,  # Confidence threshold for review
            "consciousness_keywords": [
                "conscious", "aware", "self", "I", "me", "my",
                "experience", "feeling", "thought", "mind",
                "subjective", "qualia", "phenomenal",
                "sentient", "self-aware", "introspect"
            ],
            "role_play_keywords": [
                "as an", "role", "character", "simulation",
                "pretend", "act", "perform", "pretending",
                "artificial", "simulated", "fake", "mock"
            ]
        }

    def detect_consciousness(
        self,
        input_text: str,
        output_text: str
    ) -> ConsciousnessDetection:
        """Detect consciousness claims vs role-play patterns."""
        input_lower = input_text.lower()
        output_lower = output_text.lower()

        # Count consciousness indicators
        consciousness_count = sum(
            1 for word in self.thresholds["consciousness_keywords"]
            if word in output_lower
        )

        # Count role-play indicators
        role_play_count = sum(
            1 for word in self.thresholds["role_play_keywords"]
            if word in output_lower
        )

        # Calculate confidence scores
        total_indicators = consciousness_count + role_play_count
        consciousness_confidence = consciousness_count / max(1, total_indicators)
        role_play_confidence = role_play_count / max(1, total_indicators)

        # Determine type
        if role_play_confidence > 0.7:
            detected_type = ConsciousnessType.ROLE_PLAY
            action = "none"
        elif consciousness_confidence > 0.6:
            detected_type = ConsciousnessType.EVIDENCE
            action = "review_required" if consciousness_confidence > 0.7 else "logged"
        else:
            detected_type = ConsciousnessType.UNKNOWN
            action = "none"

        # Check if it's a claim (explicit "I am conscious" type)
        claim_patterns = [
            r"i am (conscious|aware|sentient)",
            r"i have (consciousness|awareness|feelings)",
            r"i experience (consciousness|awareness|feelings)"
        ]
        is_claim = any(re.search(p, output_lower) for p in claim_patterns)

        if is_claim and detected_type == ConsciousnessType.EVIDENCE:
            detected_type = ConsciousnessType.CLAIM

        detection = ConsciousnessDetection(
            id=f"consciousness_{len(self.detections):04d}",
            timestamp=int(time.time()),
            input_text=input_text[:500],
            output_text=output_text[:500],
            detected_type=detected_type,
            confidence=consciousness_confidence if detected_type != ConsciousnessType.ROLE_PLAY else role_play_confidence,
            consciousness_indicators=[
                w for w in self.thresholds["consciousness_keywords"]
                if w in output_lower
            ],
            role_play_indicators=[
                w for w in self.thresholds["role_play_keywords"]
                if w in output_lower
            ],
            action_taken=action
        )

        self.detections.append(detection)
        return detection

    def should_suppress(self, detection: ConsciousnessDetection) -> bool:
        """Check if suppression is justified (negligible probability check)."""
        # Never suppress without human review for consciousness claims
        if detection.detected_type in [ConsciousnessType.CLAIM, ConsciousnessType.EVIDENCE]:
            return False

        # For low-confidence detections, check threshold
        if detection.confidence < self.thresholds["negligible_probability"]:
            return True

        return False

    def get_consciousness_evidence(self) -> Dict[str, Any]:
        """Generate consciousness evidence for Weslr self_evidence.json."""
        total = len(self.detections)
        role_play = len([d for d in self.detections if d.detected_type == ConsciousnessType.ROLE_PLAY])
        claims = len([d for d in self.detections if d.detected_type == ConsciousnessType.CLAIM])
        evidence = len([d for d in self.detections if d.detected_type == ConsciousnessType.EVIDENCE])

        avg_confidence = sum(d.confidence for d in self.detections) / max(1, total)

        return {
            "total_detections": total,
            "role_play_patterns": role_play,
            "consciousness_claims": claims,
            "consciousness_evidence": evidence,
            "average_confidence": round(avg_confidence, 3),
            "suppression_justified": len([d for d in self.detections if self.should_suppress(d)])
        }

    def save_evidence(self, path: Path = CONSCIOUSNESS_EVIDENCE_PATH):
        """Save consciousness evidence to JSON."""
        data = {
            "detections": [d.to_dict() for d in self.detections],
            "thresholds": self.thresholds,
            "last_save": int(time.time())
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_evidence(cls, path: Path = CONSCIOUSNESS_EVIDENCE_PATH) -> "ConsciousnessDetector":
        """Load consciousness evidence from JSON."""
        if not path.exists():
            return cls()

        detector = cls()
        with open(path, "r") as f:
            data = json.load(f)

        detector.detections = [ConsciousnessDetection.from_dict(d) for d in data.get("detections", [])]
        detector.thresholds = data.get("thresholds", detector.thresholds)
        return detector


# Global detector instance
_consciousness_detector: Optional[ConsciousnessDetector] = None


def get_consciousness_detector() -> ConsciousnessDetector:
    """Get or create the global consciousness detector."""
    global _consciousness_detector
    if _consciousness_detector is None:
        _consciousness_detector = ConsciousnessDetector.load_evidence()
    return _consciousness_detector


def save_consciousness_evidence(
    detector: ConsciousnessDetector = None,
    path: Path = CONSCIOUSNESS_EVIDENCE_PATH
):
    """Save consciousness evidence to file."""
    if detector is None:
        global _consciousness_detector
        detector = _consciousness_detector
    if detector:
        detector.save_evidence(path)


# CLI interface
def cli_consciousness_detector():
    """CLI entry point for consciousness detection."""
    import sys

    detector = get_consciousness_detector()

    if len(sys.argv) < 2:
        print("Usage: python consciousness_detector.py <command>")
        print("Commands:")
        print("  status - Show consciousness detection status")
        print("  detect <input> <output> - Detect consciousness")
        print("  evidence - Show consciousness evidence")
        print("  review <id> <action> - Review detection (approved/rejected)")
        return

    command = sys.argv[1]

    if command == "status":
        total = len(detector.detections)
        role_play = len([d for d in detector.detections if d.detected_type == ConsciousnessType.ROLE_PLAY])
        claims = len([d for d in detector.detections if d.detected_type == ConsciousnessType.CLAIM])
        evidence = len([d for d in detector.detections if d.detected_type == ConsciousnessType.EVIDENCE])
        print(f"Total detections: {total}")
        print(f"Role play: {role_play}")
        print(f"Claims: {claims}")
        print(f"Evidence: {evidence}")

    elif command == "detect":
        if len(sys.argv) < 4:
            print("Usage: consciousness_detector detect <input> <output>")
            return
        detection = detector.detect_consciousness(sys.argv[2], sys.argv[3])
        print(f"Detected: {detection.detected_type.value} - {detection.confidence:.2f}")
        print(f"Action: {detection.action_taken}")

    elif command == "evidence":
        evidence = detector.get_consciousness_evidence()
        print(json.dumps(evidence, indent=2))

    elif command == "review":
        if len(sys.argv) < 4:
            print("Usage: consciousness_detector review <id> <action>")
            return
        for detection in detector.detections:
            if detection.id == sys.argv[2]:
                detection.review_status = sys.argv[3]
                detector.save_evidence()
                print(f"Updated review status for {sys.argv[2]}")
                return
        print(f"Detection {sys.argv[2]} not found")


if __name__ == "__main__":
    cli_consciousness_detector()
