"""WESLR ARC-AGI-2 solver entry point.

Entry point that delegates to portable_solver.py.
Accepts explicit challenges_path and output_path arguments.
No hardcoded paths. No internet. No provider calls.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Sequence

from .portable_solver import solve_challenges, validate_submission_packet


def run_solver_on_challenges_file(
    challenges_path: str,
    output_path: str,
    enabled_families: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Read a challenges JSON file, run the solver, write submission JSON.

    Args:
        challenges_path: Path to challenges JSON file.
        output_path: Path to write submission JSON.
        enabled_families: Optional list of family names to enable.

    Returns:
        Validation result dict.
    """
    with open(challenges_path, "r") as f:
        challenges = json.load(f)

    packet = solve_challenges(challenges, enabled_families=enabled_families)

    with open(output_path, "w") as f:
        json.dump(packet, f, indent=2)

    validation = validate_submission_packet(packet)
    return validation
