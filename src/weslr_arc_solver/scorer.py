"""WESLR ARC-AGI-2 scoring utilities.

Synthetic-only. No public ARC ingestion. No scoring claims. No Kaggle writes.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def score_submission_v1(
    submission: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    """Score a submission against expected outputs.

    Synthetic-only. No public scoring. No Kaggle submission.

    Args:
        submission: Submission packet dict.
        expected: Expected outputs dict mapping task_id -> [grid, ...].

    Returns:
        Score summary dict.
    """
    task_entries = submission.get("task_entries", submission.get("entries", []))
    total_tasks = len(task_entries)
    correct_tasks = 0
    task_results: list[dict[str, Any]] = []

    for entry in task_entries:
        task_id = entry.get("task_id", "unknown")
        expected_outputs = expected.get(task_id, [])
        test_packets = entry.get("test_input_packets", entry.get("packets", []))

        task_correct = 0
        task_total = min(len(test_packets), len(expected_outputs))
        for packet_index, tp in enumerate(test_packets):
            if packet_index >= len(expected_outputs):
                break
            attempts = tp.get("attempts", [])
            if attempts and attempts[0].get("grid") == expected_outputs[packet_index]:
                task_correct += 1

        if task_total > 0 and task_correct == task_total:
            correct_tasks += 1

        task_results.append({
            "task_id": task_id,
            "correct": task_correct,
            "total": task_total,
        })

    return {
        "total_tasks": total_tasks,
        "correct_tasks": correct_tasks,
        "accuracy": correct_tasks / total_tasks if total_tasks > 0 else 0.0,
        "task_results": task_results,
        "synthetic_only": True,
    }
