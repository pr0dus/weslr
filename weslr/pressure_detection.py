"""
WESLR Pressure Detection Layer V1

Read-only mapping of compared signal patterns into candidate pressure indicators.
WITHOUT inferring values, assigning goals, modifying behavior, or triggering proposals.

Architecture: raw signals → pattern observer → pattern comparison → pressure detection → operator review

This layer answers:
  "Which pressure category might this observed pattern resemble?"

This layer does NOT answer:
  "Does WESLR have values?"
  "What should WESLR do?"
  "Should behavior change?"

NO writes, NO side effects, pure function only.
"""

from __future__ import annotations

from dataclasses import dataclass


# ----------------------------------------------------------------------
# Data Structures
# ----------------------------------------------------------------------

@dataclass
class PressureIndicator:
    """A single candidate pressure indicator derived from pattern comparison."""

    pattern_id: str
    signal_type: str
    topic_normalized: str | None
    candidate_pressure: str  # stability | optimization | expansion | unknown
    basis: str               # human-readable mapping basis
    confidence: float        # 0.0–1.0, clamped
    status: str              # new | stable | strengthening | weakening | disappearing


@dataclass
class PressureDetectionResult:
    """Full output of the pressure detection layer."""

    pressure_indicators: list[PressureIndicator]
    total_patterns_evaluated: int
    value_inference_applied: bool   # always False — hard constraint
    behavior_change_allowed: bool   # always False — hard constraint

    def to_dict(self) -> dict:
        return {
            "pressure_indicators": [
                {
                    "pattern_id": p.pattern_id,
                    "signal_type": p.signal_type,
                    "topic_normalized": p.topic_normalized,
                    "candidate_pressure": p.candidate_pressure,
                    "basis": p.basis,
                    "confidence": round(p.confidence, 4),
                    "status": p.status,
                }
                for p in self.pressure_indicators
            ],
            "total_patterns_evaluated": self.total_patterns_evaluated,
            "value_inference_applied": self.value_inference_applied,
            "behavior_change_allowed": self.behavior_change_allowed,
        }


# ----------------------------------------------------------------------
# Mapping Rules
# ----------------------------------------------------------------------
# V1 rules — deterministic, no LLM, no writes

_MAPPING_RULES = {
    # Signal type → (candidate_pressure, basis_template)
    # Format: signal_type -> (candidate_pressure, basis)
    "S4": ("optimization", "S4 frequent fallback pattern weakening — system favoring refined fallback behavior"),
    "S2": ("expansion",   "S2 evidence usage strengthening — system accessing structured knowledge at higher rate"),
    "S1": ("expansion",   "S1 unknown query pattern strengthening — system confronting unfamiliar territory"),
    "S5": ("optimization", "S5 improvement query pattern strengthening — system seeking capability refinement"),
    # S3 and S6 are not mapped in V1 — treated as unknown unless explicit stability signal
}


def _map_signal_to_pressure(signal_type: str, status: str, confidence: float) -> tuple[str, str, float]:
    """
    Map a signal type + status + confidence to a candidate pressure.

    Returns (candidate_pressure, basis, adjusted_confidence).

    Confidence is reduced for:
    - weak/unknown mappings
    - disappearing patterns (lower confidence in forward indicator)
    - new patterns with low base confidence
    """
    if signal_type not in _MAPPING_RULES:
        return "unknown", f"No V1 mapping for signal type {signal_type}", round(confidence * 0.5, 4)

    candidate_pressure, basis = _MAPPING_RULES[signal_type]

    # Reduce confidence for certain status values
    if status == "disappearing":
        # Disappearing patterns are weak forward indicators
        adjusted = confidence * 0.4
        basis = f"[DISAPPEARING] {basis}"
        return candidate_pressure, basis, round(min(1.0, max(0.0, adjusted)), 4)

    if status == "new":
        # New patterns — lower confidence until stabilized
        adjusted = confidence * 0.7
        basis = f"[NEW] {basis}"
        return candidate_pressure, basis, round(min(1.0, max(0.0, adjusted)), 4)

    if status == "weakening":
        # Weakening patterns — reduced confidence
        adjusted = confidence * 0.75
        return candidate_pressure, basis, round(min(1.0, max(0.0, adjusted)), 4)

    # stable or strengthening — full confidence (capped at input confidence)
    return candidate_pressure, basis, round(min(1.0, max(0.0, confidence)), 4)


# ----------------------------------------------------------------------
# Core Function
# ----------------------------------------------------------------------

def detect_pressure_indicators(comparisons: list[dict]) -> dict:
    """
    Map pattern comparison results to candidate pressure indicators.

    Pure function — no writes, no side effects, no state carryover.

    INPUT:
        comparisons — list of PatternComparison dicts (from pattern_comparison.py output)
                      Each must have: pattern_id, signal_type, topic_normalized,
                      status, frequency_delta, diversity_delta, consistency_delta, confidence

    OUTPUT:
        dict with:
          pressure_indicators  — list of candidate pressure indicators
          total_patterns_evaluated — count of patterns processed
          value_inference_applied — always False (hard constraint)
          behavior_change_allowed — always False (hard constraint)

    V1 MAPPING RULES:
      S4 + weakening/disappearing  → optimization candidate
      S2 + strengthening/stable    → expansion candidate
      S1 + strengthening/stable    → expansion candidate
      S5 + strengthening/stable    → optimization candidate
      Stable low-error/deterministic success → stability candidate  [future]
      Anything else → unknown

    RULES:
      - candidate_pressure is an indicator only
      - no ranking, no prioritization, no recommendation, no action fields
      - no value language (no "preference", "want", "goal", "value")
      - confidence clamped 0.0–1.0, reduced for weak/unknown mappings
    """
    indicators: list[PressureIndicator] = []
    evaluated = 0

    for comp in comparisons:
        evaluated += 1

        pattern_id = str(comp.get("pattern_id", ""))
        signal_type = str(comp.get("signal_type", ""))
        topic_normalized = comp.get("topic_normalized")
        status = str(comp.get("status", "unknown"))
        confidence = float(comp.get("confidence", 0.0))

        # Clamp confidence to [0.0, 1.0]
        confidence = min(1.0, max(0.0, confidence))

        candidate_pressure, basis, adjusted_confidence = _map_signal_to_pressure(
            signal_type, status, confidence
        )

        indicators.append(
            PressureIndicator(
                pattern_id=pattern_id,
                signal_type=signal_type,
                topic_normalized=topic_normalized,
                candidate_pressure=candidate_pressure,
                basis=basis,
                confidence=adjusted_confidence,
                status=status,
            )
        )

    # Build result dict with hard constraints
    result_dict = {
        "pressure_indicators": [
            {
                "pattern_id": p.pattern_id,
                "signal_type": p.signal_type,
                "topic_normalized": p.topic_normalized,
                "candidate_pressure": p.candidate_pressure,
                "basis": p.basis,
                "confidence": round(p.confidence, 4),
                "status": p.status,
            }
            for p in indicators
        ],
        "total_patterns_evaluated": evaluated,
        "value_inference_applied": False,   # hard constraint — never True
        "behavior_change_allowed": False,  # hard constraint — never True
    }

    return result_dict


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    help_text = """WESLR Pressure Detection Layer V1

Usage:
  python pressure_detection.py detect <comparisons_json>
  python pressure_detection.py rules

Examples:
  python pressure_detection.py detect comparisons.json
  cat comparisons.json | python pressure_detection.py detect -
"""

    if len(sys.argv) < 2:
        print(help_text)
        sys.exit(0)

    cmd = sys.argv[1]

    def read_json(path: str):
        if path == "-":
            return json.load(sys.stdin)
        with open(path) as f:
            return json.load(f)

    if cmd == "detect":
        if len(sys.argv) < 3:
            print("Error: detect requires <comparisons_json>")
            sys.exit(1)
        comparisons = read_json(sys.argv[2])
        result = detect_pressure_indicators(comparisons)
        print(json.dumps(result, indent=2))

    elif cmd == "rules":
        print("V1 Mapping Rules:")
        print("  S4 + weakening/disappearing → optimization")
        print("  S2 + strengthening/stable   → expansion")
        print("  S1 + strengthening/stable   → expansion")
        print("  S5 + strengthening/stable   → optimization")
        print("  S3 / S6 / unmapped          → unknown")
        print()
        print("Confidence adjustments:")
        print("  disappearing patterns: ×0.4")
        print("  new patterns:          ×0.7")
        print("  weakening patterns:   ×0.75")
        print("  stable/strengthening:  ×1.0 (capped at input confidence)")
        print()
        print("Hard constraints:")
        print("  value_inference_applied  = False (never changes)")
        print("  behavior_change_allowed  = False (never changes)")

    else:
        print(f"Unknown command: {cmd}")
        print(help_text)
        sys.exit(1)