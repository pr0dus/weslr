"""WESLR Native ARC Oracle — independent reference primitive semantics.

This module implements oracle reference behavior for promoted native primitives.
It must NOT import or call solver dispatch (arc_synthetic_3_step_real_dispatch).

Currently implements: color_invert
"""

from __future__ import annotations

from typing import Any, List, Tuple

# ---------------------------------------------------------------------------
# Shared helpers (oracle's own — not imported from solver)
# ---------------------------------------------------------------------------

def _background_value(grid: List[List[int]]) -> int:
    """For color_invert, background is always 0 (the default ARC background)."""
    return 0


# ---------------------------------------------------------------------------
# color_invert oracle reference
# ---------------------------------------------------------------------------

def oracle_color_invert(grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Oracle reference for color_invert.

    Replaces each non-background color c with (10 - c).
    Background remains unchanged.

    Returns (supported, output_grid, trace).
    """
    if not grid:
        return True, [], {"primitive_id": "color_invert", "empty": True}
    bg = 0  # background is always 0 for color_invert
    out = [[(10 - v) if v != 0 else 0 for v in row] for row in grid]
    return True, out, {"primitive_id": "color_invert", "background": bg}


# ---------------------------------------------------------------------------
# Dispatch table for native oracle primitives
# ---------------------------------------------------------------------------

NATIVE_ORACLE_PRIMITIVES = {
    "color_invert": oracle_color_invert,
}


def run_native_oracle(primitive_id: str, grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Run a native oracle primitive. Returns (supported, output_grid, trace)."""
    fn = NATIVE_ORACLE_PRIMITIVES.get(primitive_id)
    if fn is None:
        return False, grid, {"unsupported_reason": f"oracle: native primitive '{primitive_id}' not implemented"}
    return fn(grid)