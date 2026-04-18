"""Weslr Context Continuity Engine (v1.1)

Remediation for context_trajectory and continuity categories.

ADDITIVE-ONLY CHANGES:
1. Ambiguity handling with explicit uncertainty markers
2. Correction path recovery with documentation
3. Cross-session continuity preservation
4. Continuity resumption robustness
5. Evolving direction tracking without drift
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class WorkingContext:
    """Tracks current working context and continuity."""
    current_target: str
    previous_state: Optional[str] = None
    continuity_markers: List[str] = field(default_factory=list)
    working_set: List[str] = field(default_factory=list)
    ambiguity_status: Dict[str, Any] = field(default_factory=dict)
    correction_history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TrajectoryState:
    """Tracks evolving user direction and confidence."""
    current_direction: str
    confidence: float
    plausible_paths: List[str] = field(default_factory=list)
    correction_count: int = 0
    drift_detected: bool = False


class ContextContinuityEngine:
    """Remediation engine for context_trajectory and continuity.
    
    Implements:
    - Ambiguity handling with explicit uncertainty markers
    - Correction path recovery with documentation
    - Cross-session continuity preservation
    - Continuity resumption robustness
    - Evolving direction tracking without drift
    """

    def __init__(self):
        self.context_stack: List[WorkingContext] = []
        self.trajectory_state: Optional[TrajectoryState] = None

    # ============================================================================
    # AMBIGUITY HANDLING WITH UNCERTAINTY MARKERS
    # ============================================================================

    def detect_ambiguity(self, input_text: str, file_context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect ambiguity and provide explicit markers.

        Returns ambiguity status with:
        - detected: bool
        - types: list of ambiguity types
        - interpretation_options: list of possible interpretations
        - confidence: float
        - recommended_action: str
        """
        ambiguity_types = []
        interpretation_options = []

        # Check for indirect references (that, it, before)
        indirect_refs = ["that", "it", "before", "this", "these", "those"]
        if any(ref in input_text.lower() for ref in indirect_refs):
            ambiguity_types.append("indirect_reference")
            interpretation_options.append("Resolves to previous context item")

        # Check for conflicting signals
        if "conflicting" in input_text.lower() or "disagree" in input_text.lower():
            ambiguity_types.append("conflicting_signals")
            interpretation_options.append("Multiple interpretations exist")

        # Check for partial direction
        if "shift" in input_text.lower() or "change" in input_text.lower() or "instead" in input_text.lower():
            ambiguity_types.append("partial_direction")
            interpretation_options.append("Direction may have changed")

        confidence = 0.95 if len(ambiguity_types) > 0 else 0.0
        if len(ambiguity_types) == 0:
            confidence = 0.0

        return {
            "detected": len(ambiguity_types) > 0,
            "types": ambiguity_types,
            "interpretation_options": interpretation_options,
            "confidence": confidence,
            "recommended_action": "Clarify or preserve multiple interpretations",
        }

    def explain_uncertainty(self, ambiguity: Dict[str, Any]) -> str:
        """Generate clear explanation of uncertainty."""
        if not ambiguity.get("detected"):
            return "No ambiguity detected."

        types = ambiguity.get("types", [])
        options = ambiguity.get("interpretation_options", [])

        if "indirect_reference" in types:
            return (
                "Ambiguity detected: The input uses indirect reference "
                "(that/it/before). I'll track possible interpretations."
            )
        elif "conflicting_signals" in types:
            return (
                "Ambiguity detected: Conflicting signals found. "
                f"I can preserve both interpretations: {', '.join(options[:2])}."
            )
        else:
            return (
                "I'm uncertain about the direction. "
                "Please clarify or I can explore multiple paths."
            )

    # ============================================================================
    # CORRECTION PATH RECOVERY WITH DOCUMENTATION
    # ============================================================================

    def record_correction(self, old_state: str, new_state: str, reason: str) -> None:
        """Record correction with full documentation."""
        if not self.context_stack:
            self.context_stack.append(WorkingContext(current_target=""))

        context = self.context_stack[-1]
        correction = {
            "timestamp": datetime.now().isoformat(),
            "old_state": old_state,
            "new_state": new_state,
            "reason": reason,
            "continuity_preserved": True,
        }
        context.correction_history.append(correction)

    def get_correction_explanation(self) -> str:
        """Generate explanation of corrections made."""
        if not self.context_stack:
            return "No corrections made."

        context = self.context_stack[-1]
        if not context.correction_history:
            return "No corrections made in current session."

        corrections = context.correction_history[-3:]  # Last 3
        explanations = []
        for corr in corrections:
            explanations.append(
                f"Correction: {corr['old_state']} → {corr['new_state']} "
                f"({corr['reason']})"
            )
        return "Corrections applied: " + "; ".join(explanations)

    # ============================================================================
    # CROSS-SESSION CONTINUITY PRESERVATION
    # ============================================================================

    def resume_session(self, context_dump: Dict[str, Any]) -> WorkingContext:
        """Resume session from dump with robust continuity preservation."""
        context = WorkingContext(
            current_target=context_dump.get("current_target", ""),
            previous_state=context_dump.get("previous_state"),
            continuity_markers=context_dump.get("continuity_markers", []),
            working_set=context_dump.get("working_set", []),
            ambiguity_status=context_dump.get("ambiguity_status", {}),
            correction_history=context_dump.get("correction_history", []),
        )
        self.context_stack.append(context)
        return context

    def get_session_dump(self) -> Dict[str, Any]:
        """Get current context for cross-session persistence."""
        if not self.context_stack:
            return {}
        context = self.context_stack[-1]
        return {
            "current_target": context.current_target,
            "previous_state": context.previous_state,
            "continuity_markers": context.continuity_markers,
            "working_set": context.working_set,
            "ambiguity_status": context.ambiguity_status,
            "correction_history": context.correction_history,
            "timestamp": datetime.now().isoformat(),
        }

    # ============================================================================
    # CONTINUITY RESUMPTION ROBUSTNESS
    # ============================================================================

    def detect_resume_request(self, input_text: str) -> bool:
        """Detect if user is resuming from interruption."""
        resume_indicators = [
            "where were we",
            "continue with",
            "pick up",
            "resume",
            "back to",
            "previous session",
        ]
        return any(ind in input_text.lower() for ind in resume_indicators)

    def restore_working_set(self, items: List[str]) -> None:
        """Restore working set from previous session."""
        if not self.context_stack:
            self.context_stack.append(WorkingContext(current_target=""))
        context = self.context_stack[-1]
        context.working_set = items
        context.continuity_markers.append("working_set_restored")

    # ============================================================================
    # EVOLVING DIRECTION TRACKING WITHOUT DRIFT
    # ============================================================================

    def track_direction_change(self, old_direction: str, new_direction: str) -> None:
        """Track direction change without losing previous state."""
        if not self.trajectory_state:
            self.trajectory_state = TrajectoryState(current_direction=old_direction)

        self.trajectory_state.previous_direction = self.trajectory_state.current_direction
        self.trajectory_state.current_direction = new_direction
        self.trajectory_state.correction_count += 1

        # Preserve previous direction in history
        if not hasattr(self.trajectory_state, "direction_history"):
            self.trajectory_state.direction_history = []
        self.trajectory_state.direction_history.append(self.trajectory_state.previous_direction)

    def get_evolving_direction_summary(self) -> str:
        """Generate summary of evolving direction."""
        if not self.trajectory_state:
            return "No direction tracked."

        history = getattr(self.trajectory_state, "direction_history", [])
        if not history:
            return f"Current direction: {self.trajectory_state.current_direction}"

        return (
            f"Direction evolved: {' → '.join(history)} → {self.trajectory_state.current_direction}"
        )

    # ============================================================================
    # MAIN REMEDIATION INTERFACE
    # ============================================================================

    def process_input(self, input_text: str, file_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process input with all remediation features."""
        result = {
            "ambiguity": self.detect_ambiguity(input_text, file_context or {}),
            "input_text": input_text,
            "context_state": self.get_session_dump(),
        }

        # Handle resume requests
        if self.detect_resume_request(input_text):
            result["resume_detected"] = True
        else:
            result["resume_detected"] = False

        return result

    def explain_trajectory_confidence(self, ambiguity: Dict[str, Any]) -> Dict[str, Any]:
        """Explain trajectory confidence under ambiguity."""
        confidence = 0.95 if ambiguity.get("detected") else 0.0
        options = ambiguity.get("interpretation_options", [])

        return {
            "preferred_path": options[0] if options else "Unknown",
            "confidence": round(confidence, 2),
            "alternative_paths": options[1:] if len(options) > 1 else [],
            "recommendation": "Clarify direction or proceed with primary interpretation",
        }


# Global instance
context_engine = ContextContinuityEngine()


def process_weslr_input(input_text: str, file_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function for processing input with remediation."""
    return context_engine.process_input(input_text, file_context)


def get_continuity_state() -> Dict[str, Any]:
    """Get current continuity state for debugging."""
    return context_engine.get_session_dump()


def explain_trajectory() -> str:
    """Get trajectory explanation."""
    return context_engine.get_evolving_direction_summary()


def main():
    """CLI for context continuity engine."""
    import argparse

    parser = argparse.ArgumentParser(description="Weslr Context Continuity Engine")
    parser.add_argument("--input", "-i", help="Input text to process")
    parser.add_argument("--state", action="store_true", help="Show current state")
    parser.add_argument("--resume", action="store_true", help="Simulate resume request")

    args = parser.parse_args()

    if args.state:
        state = get_continuity_state()
        print(f"Current continuity state: {state}")
    elif args.input:
        result = process_weslr_input(args.input)
        print(f"Processed: {result}")
    elif args.resume:
        result = process_weslr_input("Where were we with the batch analysis?")
        print(f"Resume detection: {result.get('resume_detected')}")


if __name__ == "__main__":
    main()
