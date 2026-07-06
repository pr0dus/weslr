"""WESLR ARC-AGI-2 portable solver package.

This package wraps the WESLR solver stack for Kaggle-style offline dry runs.
It does not contain the real solver modules — it imports them from the WESLR
repo via sys.path injection in portable_solver.py.

Synthetic-only. No public ARC ingestion. No scoring claims. No Kaggle writes.
"""

from __future__ import annotations

from .portable_solver import (
    solve_task,
    solve_challenges,
    validate_submission_packet,
)
from .solver import run_solver_on_challenges_file

__all__ = [
    "solve_task",
    "solve_challenges",
    "validate_submission_packet",
    "run_solver_on_challenges_file",
]
