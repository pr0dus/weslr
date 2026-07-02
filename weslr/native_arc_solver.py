"""WESLR Native ARC Solver — solver dispatch targets for native primitives.

This module implements solver execution targets for promoted native primitives.
It must NOT import or call the oracle (native_arc_oracle).

Currently implements: color_invert, constr_draw_rect_around, mask_complement,
topo_fill_holes, sel_leftmost
"""

from __future__ import annotations

from typing import Any, List, Tuple, Dict

# Reuse background detection and CC utilities from existing dispatch (shared utility, not oracle)
from weslr.arc_synthetic_3_step_real_dispatch import _background_value_from_grid, _connected_components, _bounding_box_for_cells


def solver_color_invert(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for color_invert."""
    if not grid:
        return True, [], {"primitive_id": "color_invert", "empty": True}
    out = [[(10 - v) if v != 0 else 0 for v in row] for row in grid]
    return True, out, {"primitive_id": "color_invert", "background": 0}


def solver_constr_draw_rect_around(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for constr_draw_rect_around.

    Draws rectangle outline (color 2) around largest component bbox.
    Only background perimeter cells become 2.
    """
    if not grid:
        return True, [], {"primitive_id": "constr_draw_rect_around", "empty": True}
    bg = _background_value_from_grid(grid)
    components = _connected_components(grid, bg)
    if not components:
        return True, [row[:] for row in grid], {"primitive_id": "constr_draw_rect_around", "no_object": True}
    largest = max(components, key=len)
    min_r, min_c, max_r, max_c = _bounding_box_for_cells(largest)
    out = [row[:] for row in grid]
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if r == min_r or r == max_r or c == min_c or c == max_c:
                if 0 <= r < len(out) and 0 <= c < len(out[0]):
                    if out[r][c] == bg:
                        out[r][c] = 2
    return True, out, {"primitive_id": "constr_draw_rect_around", "bbox": [min_r, min_c, max_r, max_c]}


def solver_mask_complement(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for mask_complement.

    Full-grid mask complement: bg 0 → 1, non-bg → 0.
    """
    if not grid:
        return True, [], {"primitive_id": "mask_complement", "empty": True}
    out = [[1 if v == 0 else 0 for v in row] for row in grid]
    return True, out, {"primitive_id": "mask_complement"}


def solver_topo_fill_holes(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for topo_fill_holes.

    Fills enclosed background cells with surrounding object color.
    Uses 4-connectivity flood fill from borders.
    """
    if not grid:
        return True, [], {"primitive_id": "topo_fill_holes", "empty": True}
    bg = _background_value_from_grid(grid)
    h, w = len(grid), len(grid[0]) if grid else 0
    if h == 0 or w == 0:
        return True, [row[:] for row in grid], {"primitive_id": "topo_fill_holes", "empty": True}
    visited = [[False] * w for _ in range(h)]
    queue = []
    for r in range(h):
        for c in range(w):
            if (r == 0 or r == h - 1 or c == 0 or c == w - 1) and grid[r][c] == bg:
                queue.append((r, c))
                visited[r][c] = True
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == bg:
                visited[nr][nc] = True
                queue.append((nr, nc))
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] == bg and not visited[r][c]:
                for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != bg:
                        out[r][c] = grid[nr][nc]
                        break
    return True, out, {"primitive_id": "topo_fill_holes", "filled": sum(1 for r in range(h) for c in range(w) if grid[r][c] == bg and not visited[r][c])}


def solver_sel_leftmost(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for sel_leftmost.

    Selects leftmost connected component (min bbox min_col, tie-break min_r).
    """
    if not grid:
        return True, [], {"primitive_id": "sel_leftmost", "empty": True}
    bg = _background_value_from_grid(grid)
    components = _connected_components(grid, bg)
    if not components:
        return True, [row[:] for row in grid], {"primitive_id": "sel_leftmost", "no_object": True}
    def leftmost_key(comp):
        min_r = min(r for r, _ in comp)
        min_c = min(c for _, c in comp)
        return (min_c, min_r)
    selected = min(components, key=leftmost_key)
    out = [[bg for _ in row] for row in grid]
    for r, c in selected:
        out[r][c] = grid[r][c]
    return True, out, {"primitive_id": "sel_leftmost", "selected_cells": len(selected)}


# ---------------------------------------------------------------------------
# cond_if_holes_fill solver reference
# ---------------------------------------------------------------------------

def solver_cond_if_holes_fill(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for cond_if_holes_fill.

    Fill holes in the largest connected component only.
    """
    if not grid:
        return True, [], {"primitive_id": "cond_if_holes_fill", "empty": True}
    bg = _background_value_from_grid(grid)
    components = _connected_components(grid, bg)
    if not components:
        return True, [row[:] for row in grid], {"primitive_id": "cond_if_holes_fill", "no_object": True}
    largest = max(components, key=len)
    largest_set = set(largest)
    min_r, min_c, max_r, max_c = _bounding_box_for_cells(largest)
    h, w = len(grid), len(grid[0])
    visited = [[False] * w for _ in range(h)]
    queue = []
    for r in range(h):
        for c in range(w):
            if (r == 0 or r == h - 1 or c == 0 or c == w - 1) and grid[r][c] == bg:
                queue.append((r, c))
                visited[r][c] = True
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == bg:
                visited[nr][nc] = True
                queue.append((nr, nc))
    out = [row[:] for row in grid]
    filled = 0
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if grid[r][c] == bg and not visited[r][c]:
                for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) in largest_set:
                        out[r][c] = grid[nr][nc]
                        filled += 1
                        break
    return True, out, {"primitive_id": "cond_if_holes_fill", "filled": filled}


# ---------------------------------------------------------------------------
# rel_swap_positions solver reference
# ---------------------------------------------------------------------------

def solver_rel_swap_positions(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for rel_swap_positions.

    Swap positions of two largest connected components by bbox centroid.
    """
    if not grid:
        return True, [], {"primitive_id": "rel_swap_positions", "empty": True}
    bg = _background_value_from_grid(grid)
    components = _connected_components(grid, bg)
    if len(components) < 2:
        return True, [row[:] for row in grid], {"primitive_id": "rel_swap_positions", "few_objects": True}
    comps = sorted(components, key=len, reverse=True)
    obj_a, obj_b = comps[0], comps[1]
    a_min_r, a_min_c, a_max_r, a_max_c = _bounding_box_for_cells(obj_a)
    b_min_r, b_min_c, b_max_r, b_max_c = _bounding_box_for_cells(obj_b)
    a_cr = (a_min_r + a_max_r) // 2
    a_cc = (a_min_c + a_max_c) // 2
    b_cr = (b_min_r + b_max_r) // 2
    b_cc = (b_min_c + b_max_c) // 2
    dr_a = b_cr - a_cr
    dc_a = b_cc - a_cc
    dr_b = a_cr - b_cr
    dc_b = a_cc - b_cc
    out = [[bg for _ in row] for row in grid]
    obj_cells = set(obj_a) | set(obj_b)
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if (r, c) not in obj_cells:
                out[r][c] = grid[r][c]
    for r, c in obj_a:
        nr, nc = r + dr_a, c + dc_a
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = grid[r][c]
    for r, c in obj_b:
        nr, nc = r + dr_b, c + dc_b
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = grid[r][c]
    return True, out, {"primitive_id": "rel_swap_positions", "swapped": True}


# ---------------------------------------------------------------------------
# color_swap_1_2 solver reference
# ---------------------------------------------------------------------------

def solver_color_swap_1_2(grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Solver target for color_swap_1_2.

    Swap colors 1 and 2. All other colors unchanged.
    """
    if not grid:
        return True, [], {"primitive_id": "color_swap_1_2", "empty": True}
    swap_map = {1: 2, 2: 1}
    out = [[swap_map.get(v, v) for v in row] for row in grid]
    return True, out, {"primitive_id": "color_swap_1_2"}


# ---------------------------------------------------------------------------
# Dispatch table for native solver primitives
# ---------------------------------------------------------------------------

NATIVE_SOLVER_PRIMITIVES = {
    "color_invert": solver_color_invert,
    "constr_draw_rect_around": solver_constr_draw_rect_around,
    "mask_complement": solver_mask_complement,
    "topo_fill_holes": solver_topo_fill_holes,
    "sel_leftmost": solver_sel_leftmost,
    "cond_if_holes_fill": solver_cond_if_holes_fill,
    "rel_swap_positions": solver_rel_swap_positions,
    "color_swap_1_2": solver_color_swap_1_2,
}


def run_native_solver(primitive_id: str, grid: List[List[int]], params: Dict[str, Any]) -> Tuple[bool, List[List[int]], dict]:
    """Run a native solver primitive. Returns (supported, output_grid, trace)."""
    fn = NATIVE_SOLVER_PRIMITIVES.get(primitive_id)
    if fn is None:
        return False, grid, {"unsupported_reason": f"solver: native primitive '{primitive_id}' not implemented"}
    return fn(grid, params)