"""WESLR Native ARC Solver — solver dispatch targets for native primitives.

This module implements solver execution targets for promoted native primitives.
It must NOT import or call the oracle (native_arc_oracle).

Currently implements: color_invert
"""

from __future__ import annotations

from typing import Any, List, Tuple, Dict

# Reuse background detection from existing dispatch (shared utility, not oracle)
from weslr.arc_synthetic_3_step_real_dispatch import _background_value_from_grid


def solver_color_invert(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for color_invert.

    Replaces each non-background color c with (10 - c).
    Background remains unchanged.

    Returns (supported, output_grid, trace).
    """
    if not grid:
        return True, [], {"primitive_id": "color_invert", "empty": True}
    out = [[(10 - v) if v != 0 else 0 for v in row] for row in grid]
    return True, out, {"primitive_id": "color_invert", "background": 0}


# ---------------------------------------------------------------------------
# Dispatch table for native solver primitives
# ---------------------------------------------------------------------------

NATIVE_SOLVER_PRIMITIVES = {
    "color_invert": solver_color_invert,
}


def run_native_solver(primitive_id: str, grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Run a native solver primitive. Returns (supported, output_grid, trace)."""
    fn = NATIVE_SOLVER_PRIMITIVES.get(primitive_id)
    if fn is None:
        return False, grid, {"unsupported_reason": f"solver: native primitive '{primitive_id}' not implemented"}
    return fn(grid, params)