"""Explanation mode/knob selector - Human-Adaptive Explanation v1"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ExplanationKnobs:
    depth: float = 0.5
    technicality: float = 0.5
    pacing: str = "normal"  # slow|normal|fast
    directness: float = 0.5
    structure_looseness: float = 0.5
    uncertainty_plain: bool = True


@dataclass
class ExplanationPreferenceState:
    depth: float = 0.5
    technicality: float = 0.5
    pacing: str = "normal"
    directness: float = 0.5
    structure_looseness: float = 0.5
    uncertainty_plain: bool = True
    has_explicit: bool = False


class ExplanationModeSelector:
    def __init__(self, persona: str = "general", domain: str = "general"):
        self.persona = persona
        self.domain = domain
        self.session_pref = ExplanationPreferenceState()

    def apply_overrides(self, overrides: Dict[str, Any]) -> None:
        if not overrides:
            return
        self.session_pref.has_explicit = True
        for key, val in self._override_to_knobs(overrides).items():
            setattr(self.session_pref, key, val)

    def reset_overrides(self) -> None:
        self.session_pref = ExplanationPreferenceState()

    def select_knobs(
        self,
        overrides: Dict[str, Any] | None,
        signals: Dict[str, Any] | None = None,
    ) -> ExplanationKnobs:
        base = self._persona_defaults()
        base = self._domain_adjust(base)
        if self.session_pref.has_explicit:
            base = self._merge_knobs(base, self.session_pref.__dict__)
        if overrides:
            base = self._merge_knobs(base, self._override_to_knobs(overrides))
        if signals and signals.get("ambiguity", 0) > 0.6:
            base["uncertainty_plain"] = True
            base["directness"] = max(base.get("directness", 0.5), 0.5)
            base["structure_looseness"] = min(base.get("structure_looseness", 0.5), 0.6)
        return ExplanationKnobs(**base)

    def _domain_adjust(self, knobs: Dict[str, Any]) -> Dict[str, Any]:
        d = (self.domain or "").lower()
        adjusted = dict(knobs)
        if "technical" in d:
            adjusted["technicality"] = max(adjusted.get("technicality", 0.5), 0.7)
            adjusted["depth"] = max(adjusted.get("depth", 0.5), 0.6)
            adjusted["structure_looseness"] = min(adjusted.get("structure_looseness", 0.5), 0.5)
        elif "educational" in d:
            adjusted["technicality"] = min(adjusted.get("technicality", 0.5), 0.5)
            adjusted["pacing"] = "slow" if adjusted.get("pacing") == "slow" else "normal"
            adjusted["structure_looseness"] = max(adjusted.get("structure_looseness", 0.5), 0.5)
        elif "support" in d or "non-technical" in d:
            adjusted["technicality"] = min(adjusted.get("technicality", 0.5), 0.4)
            adjusted["pacing"] = "slow"
            adjusted["directness"] = max(adjusted.get("directness", 0.5), 0.5)
        return adjusted

    def _persona_defaults(self) -> Dict[str, Any]:
        p = self.persona.lower()
        if p in ["engineer", "technical operator"]:
            return {
                "depth": 0.7,
                "technicality": 0.8,
                "pacing": "normal",
                "directness": 0.7,
                "structure_looseness": 0.3,
                "uncertainty_plain": True,
            }
        if p == "teacher":
            return {
                "depth": 0.6,
                "technicality": 0.4,
                "pacing": "normal",
                "directness": 0.6,
                "structure_looseness": 0.4,
                "uncertainty_plain": True,
            }
        if p in ["child", "elderly"]:
            return {
                "depth": 0.4,
                "technicality": 0.2,
                "pacing": "slow",
                "directness": 0.5,
                "structure_looseness": 0.5,
                "uncertainty_plain": True,
            }
        return {
            "depth": 0.5,
            "technicality": 0.5,
            "pacing": "normal",
            "directness": 0.5,
            "structure_looseness": 0.5,
            "uncertainty_plain": True,
        }

    def _override_to_knobs(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        knobs = {}
        for k, v in overrides.items():
            key = k.lower()
            if key == "be shorter":
                knobs.update({"depth": 0.3, "structure_looseness": 0.6, "pacing": "fast", "directness": 0.7})
            elif key == "be more technical":
                knobs.update({"technicality": 0.8, "depth": 0.7, "directness": 0.7, "structure_looseness": 0.3})
            elif key == "explain simply":
                knobs.update({"depth": 0.4, "technicality": 0.3, "pacing": "normal", "directness": 0.5, "structure_looseness": 0.6})
            elif key == "less formal":
                knobs.update({"structure_looseness": 0.7, "directness": max(knobs.get("directness", 0.5), 0.5), "technicality": 0.4})
            elif key == "be more direct":
                knobs.update({"directness": 0.8, "structure_looseness": max(knobs.get("structure_looseness", 0.4), 0.4)})
            elif key == "slower" or key == "slower / clearer":
                knobs.update({"pacing": "slow", "structure_looseness": 0.4})
            elif key == "more detail":
                knobs.update({"depth": 0.8, "technicality": max(knobs.get("technicality", 0.5), 0.6), "pacing": "slow", "structure_looseness": 0.4})
        return knobs

    def _merge_knobs(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(base)
        for k, v in overlay.items():
            if k in merged and v is not None:
                merged[k] = v
        return merged
