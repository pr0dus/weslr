"""WESLR ARC-AGI-2 Kaggle dummy dry run.

Synthetic-only. No public ARC ingestion. No scoring claims. No Kaggle writes.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence


def run_kaggle_dummy_dry_run_v1(
    challenges: Mapping[str, Any],
    output_path: str,
) -> dict[str, Any]:
    """Run a Kaggle-style dummy dry run.

    This is a placeholder that validates the pipeline structure.
    The real solver is invoked via portable_solver.py.

    Args:
        challenges: Dict mapping task_id -> {"train": [...], "test": [...]}.
        output_path: Path to write dummy submission JSON.

    Returns:
        Summary dict.
    """
    task_ids = list(challenges.keys())
    submission = {
        "format": "arc_agi2_submission_v1",
        "synthetic_only": True,
        "kaggle_ready": False,
        "task_count": len(task_ids),
        "task_ids": task_ids,
    }
    with open(output_path, "w") as f:
        json.dump(submission, f, indent=2)
    return submission
