"""
WESLR Pattern Comparison Layer V1

Read-only comparison of observed signal patterns across observation runs.
WITHOUT interpreting patterns as values or pressure categories.

Architecture: raw signals → pattern observer → pattern comparison → later pressure detection

This layer answers:
  "Is this pattern stable, strengthening, weakening, new, or disappearing?"

This layer does NOT answer:
  "What does this pattern mean?"
  "Is this a value?"
  "What should WESLR do?"

No writes, no side effects, pure function only.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ----------------------------------------------------------------------
# Data Structures
# ----------------------------------------------------------------------

@dataclass
class PatternComparison:
    """Result of comparing a single pattern across two observation runs."""

    pattern_id: str
    signal_type: str
    topic_normalized: str | None
    status: str  # new | stable | strengthening | weakening | disappearing
    frequency_delta: int  # current - previous
    diversity_delta: int  # current - previous
    consistency_delta: float  # current - previous
    confidence: float  # 0.0–1.0 — comparison reliability only


@dataclass
class ComparisonResult:
    """Full output of the pattern comparison layer."""

    comparisons: list[PatternComparison]
    total_previous: int  # total patterns in previous run
    total_current: int   # total patterns in current run
    previous_run_id: str
    current_run_id: str

    def to_dict(self) -> dict:
        return {
            "comparisons": [
                {
                    "pattern_id": c.pattern_id,
                    "signal_type": c.signal_type,
                    "topic_normalized": c.topic_normalized,
                    "status": c.status,
                    "frequency_delta": c.frequency_delta,
                    "diversity_delta": c.diversity_delta,
                    "consistency_delta": round(c.consistency_delta, 4),
                    "confidence": round(c.confidence, 4),
                }
                for c in self.comparisons
            ],
            "total_previous": self.total_previous,
            "total_current": self.total_current,
            "previous_run_id": self.previous_run_id,
            "current_run_id": self.current_run_id,
        }


# ----------------------------------------------------------------------
# Pure Functions
# ----------------------------------------------------------------------

def _compute_confidence(
    session_diversity: int,
    consistency: float,
    has_previous: bool,
) -> float:
    """
    Compute deterministic comparison confidence.
    Confidence is about comparison reliability — NOT about pattern meaning.

    Higher session diversity + consistent consistency → higher confidence.
    Comparing a single-observation pattern → lower confidence.
    """
    if not has_previous:
        # For new patterns, confidence based on current diversity and consistency
        # More distinct sessions + consistent observations = more reliable new-pattern detection
        base = min(1.0, (session_diversity / 5.0) * 0.6 + consistency * 0.4)
        return round(base, 4)

    # For existing patterns, session diversity stabilizes the comparison
    diversity_factor = min(1.0, session_diversity / 4.0)
    consistency_factor = 0.5 + consistency * 0.5
    base = diversity_factor * consistency_factor
    return round(min(1.0, max(0.0, base)), 4)


def _classify_status(
    in_previous: bool,
    in_current: bool,
    frequency_delta: int,
    consistency_delta: float,
    current_diversity: int,
) -> str:
    """
    Classify pattern status across two runs.
    No pressure categories, no rankings, no recommendations.
    """
    if not in_previous and in_current:
        return "new"
    if in_previous and not in_current:
        return "disappearing"
    if in_previous and in_current:
        # Both present — classify based on deltas
        freq_up = frequency_delta > 0
        cons_up = consistency_delta >= 0
        cons_down = consistency_delta < -0.15

        if freq_up and cons_up:
            return "strengthening"
        if frequency_delta < 0 or cons_down:
            return "weakening"
        # Small deltas in either direction → stable
        return "stable"

    # Edge case: neither present (shouldn't happen in normal flow)
    return "unknown"


def compare_pattern_runs(
    previous_patterns: list[dict],
    current_patterns: list[dict],
    previous_run_id: str = "previous",
    current_run_id: str = "current",
) -> ComparisonResult:
    """
    Compare pattern observations across two runs.

    Pure function — no writes, no side effects, no state carryover.

    Returns ComparisonResult with per-pattern comparisons and aggregate counts.

    Comparison status rules:
      new        — pattern only in current run
      disappearing — pattern only in previous run
      strengthening — frequency increased AND consistency not down
      weakening  — frequency dropped OR consistency dropped >0.15
      stable     — small deltas, no strong direction
    """
    # Build lookup for previous patterns
    prev_by_id: dict[str, dict] = {
        p["pattern_id"]: p for p in previous_patterns
    }
    curr_by_id: dict[str, dict] = {
        p["pattern_id"]: p for p in current_patterns
    }

    all_ids: set[str] = set(prev_by_id.keys()) | set(curr_by_id.keys())
    comparisons: list[PatternComparison] = []

    for pid in sorted(all_ids):  # sorted for determinism
        prev = prev_by_id.get(pid)
        curr = curr_by_id.get(pid)

        in_prev = prev is not None
        in_curr = curr is not None

        if in_prev and in_curr:
            frequency_delta = curr["frequency"] - prev["frequency"]
            diversity_delta = curr["session_diversity"] - prev["session_diversity"]
            consistency_delta = curr["consistency"] - prev["consistency"]

            status = _classify_status(
                in_previous=True,
                in_current=True,
                frequency_delta=frequency_delta,
                consistency_delta=consistency_delta,
                current_diversity=curr["session_diversity"],
            )
            confidence = _compute_confidence(
                session_diversity=curr["session_diversity"],
                consistency=curr["consistency"],
                has_previous=True,
            )
        elif in_curr and not in_prev:
            frequency_delta = curr["frequency"]
            diversity_delta = curr["session_diversity"] - 0
            consistency_delta = curr["consistency"]  # no previous to compare

            status = _classify_status(
                in_previous=False,
                in_current=True,
                frequency_delta=frequency_delta,
                consistency_delta=consistency_delta,
                current_diversity=curr["session_diversity"],
            )
            confidence = _compute_confidence(
                session_diversity=curr["session_diversity"],
                consistency=curr["consistency"],
                has_previous=False,
            )
        elif in_prev and not in_curr:
            frequency_delta = -prev["frequency"]
            diversity_delta = -prev["session_diversity"]
            consistency_delta = -prev["consistency"]

            status = _classify_status(
                in_previous=True,
                in_current=False,
                frequency_delta=frequency_delta,
                consistency_delta=consistency_delta,
                current_diversity=0,
            )
            # Lower confidence for disappearing patterns — no current data
            confidence = _compute_confidence(
                session_diversity=prev["session_diversity"],
                consistency=prev["consistency"],
                has_previous=False,  # no current run for this pattern
            )
        else:
            # Neither — shouldn't happen
            continue

        comparisons.append(
            PatternComparison(
                pattern_id=pid,
                signal_type=curr["signal_type"] if in_curr else prev["signal_type"],
                topic_normalized=curr.get("topic_normalized") if in_curr else prev.get("topic_normalized"),
                status=status,
                frequency_delta=frequency_delta,
                diversity_delta=diversity_delta,
                consistency_delta=round(consistency_delta, 4),
                confidence=confidence,
            )
        )

    return ComparisonResult(
        comparisons=comparisons,
        total_previous=len(previous_patterns),
        total_current=len(current_patterns),
        previous_run_id=previous_run_id,
        current_run_id=current_run_id,
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    help_text = """WESLR Pattern Comparison Layer V1

Usage:
  python pattern_comparison.py compare <previous_json> <current_json>
  python pattern_comparison.py status <comparison_json> <stable|strengthening|weakening|new|disappearing>

Examples:
  python pattern_comparison.py compare prev.json curr.json
  cat comparison_result.json | python pattern_comparison.py status - stable
"""

    if len(sys.argv) < 2:
        print(help_text)
        sys.exit(0)

    cmd = sys.argv[1]

    def read_json(path: str) -> list[dict]:
        if path == "-":
            return json.load(sys.stdin)
        with open(path) as f:
            return json.load(f)

    if cmd == "compare":
        if len(sys.argv) < 4:
            print("Error: compare requires <previous_json> <current_json>")
            sys.exit(1)
        prev = read_json(sys.argv[2])
        curr = read_json(sys.argv[3])
        result = compare_pattern_runs(prev, curr)
        print(json.dumps(result.to_dict(), indent=2))

    elif cmd == "status":
        if len(sys.argv) < 3:
            print("Error: status requires <comparison_json>")
            sys.exit(1)
        data = read_json(sys.argv[2])
        # Filter by status if third arg given
        target = sys.argv[4] if len(sys.argv) > 4 else None
        if target:
            filtered = [c for c in data["comparisons"] if c["status"] == target]
            print(f"Patterns with status '{target}': {len(filtered)}")
            for c in filtered:
                print(f"  {c['pattern_id']} ({c['signal_type']}): freq={c['frequency_delta']:+d}, cons={c['consistency_delta']:+.4f}")
        else:
            counts = {}
            for c in data["comparisons"]:
                counts[c["status"]] = counts.get(c["status"], 0) + 1
            print(f"Status distribution: {counts}")
    else:
        print(f"Unknown command: {cmd}")
        print(help_text)
        sys.exit(1)