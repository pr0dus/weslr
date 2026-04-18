"""Human-Adaptive Explanation Responder v1

Integrates the mode selector into a responder pipeline with session-level
preference state. Presentation-layer adaptation only (truth/governance preserved).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .explanation_mode_selector import ExplanationModeSelector


@dataclass
class Response:
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ExplanationSession:
    """Maintains session-level explanation preferences and applies overrides."""

    def __init__(self, persona: str = "general", domain: str = "general"):
        self.selector = ExplanationModeSelector(persona=persona, domain=domain)

    def reset(self):
        self.selector.reset_overrides()

    def apply_user_overrides(self, overrides: Dict[str, Any]):
        """Apply explicit user overrides; persists for session."""
        self.selector.apply_overrides(overrides or {})

    def render(self, content: str, overrides: Optional[Dict[str, Any]] = None, signals: Optional[Dict[str, Any]] = None) -> Response:
        """Render content with adaptive knobs; returns Response with provenance.

        Truth is preserved; only presentation (wording/structure) changes.
        """
        signals = signals or {}
        knobs = self.selector.select_knobs(overrides or {}, signals)
        rendered = self._format_with_knobs(content, knobs, signals)
        meta = {
            "explanation_knobs": {
                "depth": knobs.depth,
                "technicality": knobs.technicality,
                "pacing": knobs.pacing,
                "directness": knobs.directness,
                "structure_looseness": knobs.structure_looseness,
                "uncertainty_plain": knobs.uncertainty_plain,
            },
            "truth_preserved": True,
            "governance_changed": False,
        }
        return Response(content=rendered, metadata=meta)

    def _format_with_knobs(self, content: str, knobs, signals: Dict[str, Any]) -> str:
        """Apply simple, safe formatting based on knobs."""
        confidence = signals.get("confidence")
        ambiguity = signals.get("ambiguity")

        if knobs.directness >= 0.7:
            lead = "Finding: "
        elif knobs.structure_looseness >= 0.6:
            lead = "It looks like "
        else:
            lead = "We see that "

        main = content
        if knobs.technicality >= 0.7:
            main = f"signal: {content}"
        elif knobs.technicality <= 0.3:
            main = content.replace("module", "part", 1)

        if knobs.depth >= 0.75:
            detail = " Detail: recommend confirming with logs/tests."
        elif knobs.depth <= 0.4:
            detail = ""
        else:
            detail = " Suggested: confirm with logs/tests."

        if confidence is not None:
            if knobs.uncertainty_plain:
                conf_text = f" (confidence ~{confidence:.2f})"
            else:
                conf_text = f" (signal strength ~{confidence:.2f})"
        else:
            conf_text = ""

        amb_text = ""
        if ambiguity is not None and ambiguity > 0.6:
            amb_text = " Signals are ambiguous; consider clarifying or gathering more data."

        if knobs.pacing == "fast":
            sep = " "
        elif knobs.pacing == "slow":
            sep = "\n"
        else:
            sep = " "

        rendered = f"{lead}{main}{conf_text}.{sep}{detail}{amb_text}".strip()
        return rendered
