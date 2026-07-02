"""WESLR Native ARC Oracle — independent reference primitive semantics.

This module implements oracle reference behavior for promoted native primitives.
It must NOT import or call solver dispatch (arc_synthetic_3_step_real_dispatch).

Currently implements: color_invert, constr_draw_rect_around, mask_complement,
topo_fill_holes, sel_leftmost
"""

from __future__ import annotations

from typing import Any, List, Tuple

# ---------------------------------------------------------------------------
# Shared helpers (oracle's own — not imported from solver)
# ---------------------------------------------------------------------------

def _background_value(grid: List[List[int]]) -> int:
    """For native primitives, background is always 0 (the default ARC background)."""
    return 0


def _connected_components(grid: List[List[int]], bg: int) -> List[List[Tuple[int, int]]]:
    """Oracle's own connected components implementation (4-connectivity)."""
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    visited = [[False] * w for _ in range(h)]
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != bg and not visited[r][c]:
                stack = [(r, c)]
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= h or cc < 0 or cc >= w:
                        continue
                    if visited[cr][cc] or grid[cr][cc] == bg:
                        continue
                    visited[cr][cc] = True
                    comp.append((cr, cc))
                    stack.extend([(cr+1, cc), (cr-1, cc), (cr, cc+1), (cr, cc-1)])
                if comp:
                    components.append(comp)
    return components


def _bbox(cells: List[Tuple[int, int]]) -> Tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


# ---------------------------------------------------------------------------
# color_invert oracle reference
# ---------------------------------------------------------------------------

def oracle_color_invert(grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Oracle reference for color_invert.

    Replaces each non-background color c with (10 - c).
    Background remains unchanged.
    """
    if not grid:
        return True, [], {"primitive_id": "color_invert", "empty": True}
    bg = 0
    out = [[(10 - v) if v != 0 else 0 for v in row] for row in grid]
    return True, out, {"primitive_id": "color_invert", "background": bg}


# ---------------------------------------------------------------------------
# constr_draw_rect_around oracle reference
# ---------------------------------------------------------------------------

def oracle_constr_draw_rect_around(grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Oracle reference for constr_draw_rect_around.

    Draws a rectangle outline (color 2) around the bounding box of the
    largest connected component. Only background perimeter cells become 2.
    Existing non-background cells are preserved.
    """
    if not grid:
        return True, [], {"primitive_id": "constr_draw_rect_around", "empty": True}
    bg = 0
    components = _connected_components(grid, bg)
    if not components:
        return True, [row[:] for row in grid], {"primitive_id": "constr_draw_rect_around", "no_object": True}
    largest = max(components, key=len)
    min_r, min_c, max_r, max_c = _bbox(largest)
    out = [row[:] for row in grid]
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if r == min_r or r == max_r or c == min_c or c == max_c:
                if 0 <= r < len(out) and 0 <= c < len(out[0]):
                    if out[r][c] == bg:
                        out[r][c] = 2
    return True, out, {"primitive_id": "constr_draw_rect_around", "bbox": [min_r, min_c, max_r, max_c]}


# ---------------------------------------------------------------------------
# mask_complement oracle reference
# ---------------------------------------------------------------------------

def oracle_mask_complement(grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Oracle reference for mask_complement.

    Full-grid mask complement: background 0 becomes 1, non-background becomes 0.
    """
    if not grid:
        return True, [], {"primitive_id": "mask_complement", "empty": True}
    out = [[1 if v == 0 else 0 for v in row] for row in grid]
    return True, out, {"primitive_id": "mask_complement"}


# ---------------------------------------------------------------------------
# topo_fill_holes oracle reference
# ---------------------------------------------------------------------------

def oracle_topo_fill_holes(grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Oracle reference for topo_fill_holes.

    Fills background cells enclosed by objects (not reachable from grid border
    via 4-connected background path) with the surrounding object's color.
    """
    if not grid:
        return True, [], {"primitive_id": "topo_fill_holes", "empty": True}
    bg = 0
    h, w = len(grid), len(grid[0])
    if h == 0 or w == 0:
        return True, [row[:] for row in grid], {"primitive_id": "topo_fill_holes", "empty": True}
    # Flood fill from border background cells
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
    # Fill enclosed bg cells with surrounding color
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


# ---------------------------------------------------------------------------
# sel_leftmost oracle reference
# ---------------------------------------------------------------------------

def oracle_sel_leftmost(grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Oracle reference for sel_leftmost.

    Selects the leftmost connected component (minimum bbox min_col,
    tie-break by minimum bbox min_row) and returns a grid containing
    only that component.
    """
    if not grid:
        return True, [], {"primitive_id": "sel_leftmost", "empty": True}
    bg = 0
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
# Dispatch table for native oracle primitives
# ---------------------------------------------------------------------------

NATIVE_ORACLE_PRIMITIVES = {
    "color_invert": oracle_color_invert,
    "constr_draw_rect_around": oracle_constr_draw_rect_around,
    "mask_complement": oracle_mask_complement,
    "topo_fill_holes": oracle_topo_fill_holes,
    "sel_leftmost": oracle_sel_leftmost,
}


def run_native_oracle(primitive_id: str, grid: List[List[int]]) -> Tuple[bool, List[List[int]], dict]:
    """Run a native oracle primitive. Returns (supported, output_grid, trace)."""
    fn = NATIVE_ORACLE_PRIMITIVES.get(primitive_id)
    if fn is None:
        return False, grid, {"unsupported_reason": f"oracle: native primitive '{primitive_id}' not implemented"}
    return fn(grid)