"""
WESLR Pressure Aggregation Layer V1

Aggregate pressure indicators across multiple observation runs to detect
persistence and recurrence over time — WITHOUT ranking, prioritization, or behavior change.

Architecture: raw signals → pattern observer → pattern comparison
                         → pressure detection → pressure aggregation
                         → (future operator review)

This layer answers:
  "How consistently has each pressure type been observed across runs?"

This layer does NOT answer:
  "Which pressure is most important?"
  "What should WESLR do?"
  "Should behavior change?"

NO writes, NO side effects, pure function only.
"""

from __future__ import annotations

from collections import defaultdict


# ----------------------------------------------------------------------
# Core Function
# ----------------------------------------------------------------------

def aggregate_pressure_indicators(runs: list[list[dict]]) -> dict:
    """
    Aggregate pressure indicators across multiple observation runs.

    Pure function — no writes, no side effects, no state carryover.

    INPUT:
        runs — list of pressure_indicator lists (each is output from detect_pressure_indicators()).
               Each run is a list of pressure indicator dicts, each with:
                 pattern_id, signal_type, topic_normalized, candidate_pressure,
                 basis, confidence, status

    OUTPUT:
        dict with:
          pressure_summary — aggregated stats per candidate_pressure
          total_runs       — count of runs processed
          value_inference_applied  — always False (hard constraint)
          behavior_change_allowed  — always False (hard constraint)

    RULES:
      - Group by candidate_pressure only
      - Calculate: occurrences, run_diversity, temporal_span, persistence_score
      - No ordering, no ranking, no "dominant" field, no recommendation
      - persistence_score is deterministic function, clamped [0.0, 1.0]
      - score indicates persistence only, not importance

    PERSISTENCE SCORE FORMULA:
      score = (0.4 * norm_occurrences) + (0.4 * norm_run_diversity) + (0.2 * norm_temporal_span)

      where:
        norm_occurrences  = min(1.0, total_occurrences / max_occurrences)
        norm_run_diversity = min(1.0, run_diversity / total_runs)
        norm_temporal_span = min(1.0, (last_run_index - first_run_index) / max(1, total_runs - 1))

      If only 1 run: norm_temporal_span = 0 (no temporal spread observable)
    """
    if not runs:
        return {
            "pressure_summary": [],
            "total_runs": 0,
            "value_inference_applied": False,
            "behavior_change_allowed": False,
        }

    total_runs = len(runs)

    # Accumulate stats per candidate_pressure
    # pressure -> {occurrences: int, run_indices: set[int], pattern_ids: set[str]}
    stats: dict[str, dict] = defaultdict(lambda: {
        "occurrences": 0,
        "run_indices": set(),
        "pattern_ids": set(),
    })

    for run_idx, run in enumerate(runs):
        for indicator in run:
            cp = str(indicator.get("candidate_pressure", "unknown"))
            stats[cp]["occurrences"] += 1
            stats[cp]["run_indices"].add(run_idx)
            stats[cp]["pattern_ids"].add(str(indicator.get("pattern_id", "")))

    # Compute per-pressure summary
    pressure_summary: list[dict] = []

    for cp, data in stats.items():
        occurrences = data["occurrences"]
        run_indices = sorted(data["run_indices"])
        run_diversity = len(run_indices)

        # temporal_span: difference between last and first run index
        if len(run_indices) > 1:
            temporal_span = float(run_indices[-1] - run_indices[0])
        else:
            temporal_span = 0.0

        # Persistence score
        max_occurrences = max(s["occurrences"] for s in stats.values()) if stats else 1
        norm_occurrences = min(1.0, occurrences / max(max_occurrences, 1))
        norm_run_diversity = min(1.0, run_diversity / total_runs)

        if total_runs > 1 and len(run_indices) > 1:
            max_span = total_runs - 1
            norm_temporal_span = min(1.0, (run_indices[-1] - run_indices[0]) / max_span)
        else:
            norm_temporal_span = 0.0

        persistence_score = round(
            0.4 * norm_occurrences + 0.4 * norm_run_diversity + 0.2 * norm_temporal_span,
            4,
        )

        pressure_summary.append({
            "candidate_pressure": cp,
            "occurrences": occurrences,
            "run_diversity": run_diversity,
            "temporal_span": round(temporal_span, 3),
            "persistence_score": persistence_score,
        })

    # No ranking — return in stable order (alphabetical by candidate_pressure for determinism)
    pressure_summary.sort(key=lambda x: x["candidate_pressure"])

    return {
        "pressure_summary": pressure_summary,
        "total_runs": total_runs,
        "value_inference_applied": False,   # hard constraint
        "behavior_change_allowed": False,  # hard constraint
    }


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    help_text = """WESLR Pressure Aggregation Layer V1

Usage:
  python pressure_aggregation.py aggregate <runs_json>
  python pressure_aggregation.py formula

Examples:
  python pressure_aggregation.py aggregate runs.json
  cat runs.json | python pressure_aggregation.py aggregate -
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

    if cmd == "aggregate":
        if len(sys.argv) < 3:
            print("Error: aggregate requires <runs_json>")
            sys.exit(1)
        runs = read_json(sys.argv[2])
        result = aggregate_pressure_indicators(runs)
        print(json.dumps(result, indent=2))

    elif cmd == "formula":
        print("Persistence Score Formula:")
        print("  score = 0.4*norm_occ + 0.4*norm_div + 0.2*norm_span")
        print()
        print("  norm_occ  = min(1.0, occurrences / max_occurrences)")
        print("  norm_div  = min(1.0, run_diversity / total_runs)")
        print("  norm_span = min(1.0, temporal_span / max_temporal_span)")
        print()
        print("  temporal_span = last_run_index - first_run_index")
        print("  max_temporal_span = total_runs - 1")
        print()
        print("Hard constraints:")
        print("  value_inference_applied  = False (never changes)")
        print("  behavior_change_allowed  = False (never changes)")

    else:
        print(f"Unknown command: {cmd}")
        print(help_text)
        sys.exit(1)