"""Solver adapter for BH80 semantic scoring — accepts materialized input grids.

This wraps the existing run_primitive dispatch so the solver can receive
a real input grid instead of defaulting to [[1]].
"""

from __future__ import annotations

from typing import List, Tuple, Any
from weslr.arc_synthetic_3_step_real_dispatch import run_primitive


def solver_run_with_input(input_grid: List[List[int]], primitive_sequence: List[str]) -> Tuple[bool, List[List[int]] | None]:
    """Run the solver dispatch on a materialized input grid.

    Returns (supported, output_grid).
    """
    grid = [row[:] for row in input_grid]
    params = {}

    for prim_name in primitive_sequence:
        supported, grid, _ = run_primitive(prim_name, grid, params)
        if not supported:
            return False, grid
    return True, grid