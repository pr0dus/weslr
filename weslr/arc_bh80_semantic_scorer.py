"""BH80 Semantic Scorer — compares solver output to oracle output.

The scorer is independent from both solver and oracle execution paths.
It only performs grid equality comparison and classification.
"""

from __future__ import annotations

from typing import Any, List, Tuple

from weslr.arc_bh80_oracle import run_oracle_pipeline
from weslr.arc_bh80_materializer import materialize_scene


def grids_equal(a: List[List[int]], b: List[List[int]]) -> bool:
    """True if two grids are dimension-wise and cell-wise equal."""
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb):
            return False
        for va, vb in zip(ra, rb):
            if va != vb:
                return False
    return True


def score_task(
    task: dict,
    solver_run_fn,
) -> dict:
    """Score a single BH80 task semantically.

    Args:
        task: BH80 task dict with scene_spec and primitive_sequence
        solver_run_fn: callable(input_grid, primitive_sequence) -> (supported, output_grid)

    Returns:
        dict with: task_id, result (semantic_exact/unsupported/failed/structural_pass),
                   solver_supported, oracle_supported, grids_equal,
                   solver_grid_summary, oracle_grid_summary
    """
    task_id = task["task_id"]
    scene_spec = task["scene_spec"]
    prims = task["primitive_sequence"]

    # Materialize input grid
    input_grid = materialize_scene(scene_spec, task_id)

    # Run oracle
    oracle_supported, oracle_grid, oracle_traces = run_oracle_pipeline(prims, input_grid)

    # Run solver
    solver_supported, solver_grid = solver_run_fn(input_grid, prims)

    # Classify
    if not solver_supported:
        result = "unsupported"
    elif solver_grid is None:
        result = "failed"
    elif oracle_supported and grids_equal(solver_grid, oracle_grid):
        result = "semantic_exact"
    else:
        result = "failed"

    # Structural pass (separate metric)
    structural_pass = solver_supported

    return {
        "task_id": task_id,
        "result": result,
        "structural_pass": structural_pass,
        "solver_supported": solver_supported,
        "oracle_supported": oracle_supported,
        "grids_equal": grids_equal(solver_grid, oracle_grid) if (solver_supported and oracle_supported) else False,
        "solver_grid_dims": (len(solver_grid), len(solver_grid[0]) if solver_grid else 0) if solver_grid else (0, 0),
        "oracle_grid_dims": (len(oracle_grid), len(oracle_grid[0]) if oracle_grid else 0) if oracle_grid else (0, 0),
    }


def score_tasks(tasks: list[dict], solver_run_fn) -> dict:
    """Score a list of BH80 tasks. Returns aggregate metrics and per-task reports."""
    reports = []
    counts = {"semantic_exact": 0, "unsupported": 0, "failed": 0, "structural_pass": 0}

    for task in tasks:
        report = score_task(task, solver_run_fn)
        reports.append(report)
        counts[report["result"]] = counts.get(report["result"], 0) + 1
        if report["structural_pass"]:
            counts["structural_pass"] += 1

    total = len(tasks)
    return {
        "aggregate": {
            "total": total,
            "semantic_exact": counts["semantic_exact"],
            "unsupported": counts["unsupported"],
            "failed": counts["failed"],
            "structural_pass": counts["structural_pass"],
            "semantic_exact_rate": (counts["semantic_exact"] / total * 100) if total else 0,
        },
        "task_reports": reports,
    }