"""WESLR ARC-AGI-2 emitter — two-output emission helpers.

Synthetic-only. No public ARC ingestion. No scoring claims.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


def emit_top2_attempts_v1(
    task_id: str,
    test_input_index: int,
    candidates: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Emit a top-2 attempt packet for a single test input.

    Args:
        task_id: Task identifier.
        test_input_index: Index of the test input.
        candidates: List of candidate attempt dicts, each with at least
            "grid", "source_candidate_id", "rank", "confidence_label",
            "evidence_labels", "leakage_flags", "metadata".

    Returns:
        A top-2 attempt packet dict.
    """
    attempts = []
    for rank, candidate in enumerate(candidates[:2], 1):
        attempt = {
            "attempt_id": f"{task_id}_test{test_input_index}_rank{rank}",
            "grid": deepcopy(candidate.get("grid", [])),
            "source_candidate_id": candidate.get("source_candidate_id", f"candidate_{rank}"),
            "rank": rank,
            "confidence_label": candidate.get("confidence_label", "unknown"),
            "evidence_labels": list(candidate.get("evidence_labels", [])),
            "leakage_flags": dict(candidate.get("leakage_flags", {})),
            "metadata": dict(candidate.get("metadata", {})),
        }
        attempts.append(attempt)

    return {
        "task_id": task_id,
        "test_input_index": test_input_index,
        "attempts": attempts,
        "metadata": {
            "synthetic_only": True,
            "emitter_version": "emitter_v1",
        },
    }
