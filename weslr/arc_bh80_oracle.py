"""BH80 Independent Oracle — reference primitive semantics.

This module implements its own primitive semantics independently from
the solver dispatch path. It must NOT import or call run_primitive(),
_process_task(), or any solver/dispatch function.

The oracle produces reference output grids for semantic comparison.
"""

from __future__ import annotations

from typing import Any, List, Tuple

# ---------------------------------------------------------------------------
# Connected components (oracle's own implementation)
# ---------------------------------------------------------------------------

def _background_value(grid: List[List[int]]) -> int:
    if not grid or not grid[0]:
        return 0
    from collections import Counter
    flat = [v for row in grid for v in row]
    return Counter(flat).most_common(1)[0][0]


def _connected_components(grid: List[List[int]], bg: int) -> List[List[Tuple[int, int]]]:
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


def _largest_component(grid: List[List[int]], bg: int) -> List[Tuple[int, int]]:
    comps = _connected_components(grid, bg)
    if not comps:
        return []
    return max(comps, key=len)


# ---------------------------------------------------------------------------
# Oracle reference primitives
# ---------------------------------------------------------------------------

def reference_primitive(name: str, grid: List[List[int]], params: dict | None = None) -> Tuple[bool, List[List[int]], dict]:
    """Execute a reference primitive. Returns (supported, output_grid, trace).

    This is the oracle's own implementation — completely independent from
    the solver's run_primitive().
    """
    params = params or {}
    if not grid:
        grid = [[0]]
    bg = _background_value(grid)

    # --- extract / extract_largest_object / extract_object ---
    if name in ("extract", "extract_largest_object", "extract_object"):
        largest = _largest_component(grid, bg)
        if not largest:
            return True, [[bg]], {"primitive_id": name, "empty": True}
        min_r, min_c, max_r, max_c = _bbox(largest)
        out = [[bg for _ in range(min_c, max_c + 1)] for _ in range(min_r, max_r + 1)]
        for r, c in largest:
            out[r - min_r][c - min_c] = grid[r][c]
        return True, out, {"primitive_id": name, "bbox": [min_r, min_c, max_r, max_c]}

    # --- isolate_largest ---
    if name == "isolate_largest":
        largest = _largest_component(grid, bg)
        if not largest:
            return True, [row[:] for row in grid], {"primitive_id": "isolate_largest", "empty": True}
        out = [[bg for _ in row] for row in grid]
        for r, c in largest:
            out[r][c] = grid[r][c]
        return True, out, {"primitive_id": "isolate_largest"}

    # --- extract_boundary ---
    if name == "extract_boundary":
        largest = _largest_component(grid, bg)
        if not largest:
            return True, [row[:] for row in grid], {"primitive_id": "extract_boundary", "bbox": []}
        min_r, min_c, max_r, max_c = _bbox(largest)
        out = [row[:] for row in grid]
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                if r == min_r or r == max_r or c == min_c or c == max_c:
                    if out[r][c] == bg:
                        out[r][c] = 1
        return True, out, {"primitive_id": "extract_boundary", "bbox": [min_r, min_c, max_r, max_c]}

    # --- crop / crop_object ---
    if name in ("crop", "crop_object"):
        largest = _largest_component(grid, bg)
        if not largest:
            return True, [row[:] for row in grid], {"primitive_id": name, "cropped": False}
        min_r, min_c, max_r, max_c = _bbox(largest)
        out = [row[min_c:max_c + 1] for row in grid[min_r:max_r + 1]]
        return True, out, {"primitive_id": name, "bbox": [min_r, min_c, max_r, max_c]}

    # --- mirror_object ---
    if name == "mirror_object":
        out = [list(reversed(row)) for row in grid]
        return True, out, {"primitive_id": "mirror_object"}

    # --- rotate ---
    if name == "rotate":
        h, w = len(grid), len(grid[0]) if grid else 0
        out = [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
        return True, out, {"primitive_id": "rotate"}

    # --- recolor ---
    if name == "recolor":
        out = [[2 if v != bg else bg for v in row] for row in grid]
        return True, out, {"primitive_id": "recolor"}

    # --- normalize_position ---
    if name == "normalize_position":
        largest = _largest_component(grid, bg)
        if not largest:
            return True, [row[:] for row in grid], {"primitive_id": "normalize_position", "empty": True}
        rows = [r for r, _ in largest]
        cols = [c for _, c in largest]
        centroid_r = sum(rows) / len(rows)
        centroid_c = sum(cols) / len(cols)
        h, w = len(grid), len(grid[0]) if grid else 1
        target_r = h / 2
        target_c = w / 2
        dr = int(round(target_r - centroid_r))
        dc = int(round(target_c - centroid_c))
        out = [[bg for _ in range(w)] for _ in range(h)]
        for r, c in largest:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = grid[r][c]
        return True, out, {"primitive_id": "normalize_position", "shift": [dr, dc]}

    # --- place_back ---
    if name == "place_back":
        # Place current grid centered on a canvas matching the original grid size.
        # The oracle receives the original canvas size via params ("original_h", "original_w").
        # If not provided, use current grid size (identity for single-step pipelines).
        orig_h = params.get("original_h", len(grid))
        orig_w = params.get("original_w", len(grid[0]) if grid else 0)
        cur_h, cur_w = len(grid), len(grid[0]) if grid else 0
        out = [[bg for _ in range(orig_w)] for _ in range(orig_h)]
        offset_r = max(0, (orig_h - cur_h) // 2)
        offset_c = max(0, (orig_w - cur_w) // 2)
        for r in range(cur_h):
            for c in range(cur_w):
                nr, nc = r + offset_r, c + offset_c
                if 0 <= nr < orig_h and 0 <= nc < orig_w:
                    out[nr][nc] = grid[r][c]
        return True, out, {"primitive_id": "place_back", "canvas": [orig_h, orig_w], "offset": [offset_r, offset_c]}

    # --- count_objects / count / count_or_pattern ---
    if name in ("count_objects", "count"):
        comps = _connected_components(grid, bg)
        return True, [row[:] for row in grid], {"primitive_id": name, "count": len(comps)}

    if name == "count_or_pattern":
        comps = _connected_components(grid, bg)
        if len(comps) == 1:
            return True, [row[:] for row in grid], {"primitive_id": "count_or_pattern", "mode": "count", "count": 1}
        # pattern_output mode
        out = [row[:] for row in grid]
        for r in range(len(out)):
            for c in range(len(out[0]) if out else 0):
                if out[r][c] != bg:
                    out[r][c] = 1 if r % 2 == 0 else 2
        return True, out, {"primitive_id": "count_or_pattern", "mode": "pattern", "count": len(comps)}

    # --- pattern_output ---
    if name == "pattern_output":
        out = [row[:] for row in grid]
        for r in range(len(out)):
            for c in range(len(out[0]) if out else 0):
                if out[r][c] != bg:
                    out[r][c] = 1 if r % 2 == 0 else 2
        return True, out, {"primitive_id": "pattern_output"}

    # --- transform ---
    if name == "transform":
        # Flip vertically
        out = list(reversed([row[:] for row in grid]))
        return True, out, {"primitive_id": "transform"}

    # --- remove_noise ---
    if name == "remove_noise":
        out = [row[:] for row in grid]
        h, w = len(out), len(out[0]) if out else 0
        for r in range(h):
            for c in range(w):
                if out[r][c] != bg:
                    has_neighbor = False
                    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == out[r][c]:
                            has_neighbor = True
                            break
                    if not has_neighbor:
                        out[r][c] = bg
        return True, out, {"primitive_id": "remove_noise"}

    # --- recolor_boundary ---
    if name == "recolor_boundary":
        largest = _largest_component(grid, bg)
        if not largest:
            return True, [row[:] for row in grid], {"primitive_id": "recolor_boundary", "empty": True}
        min_r, min_c, max_r, max_c = _bbox(largest)
        out = [row[:] for row in grid]
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                if r == min_r or r == max_r or c == min_c or c == max_c:
                    if out[r][c] != bg:
                        out[r][c] = 2
        return True, out, {"primitive_id": "recolor_boundary", "bbox": [min_r, min_c, max_r, max_c]}

    # --- extract_changed_region ---
    if name == "extract_changed_region":
        largest = _largest_component(grid, bg)
        if not largest:
            return True, [row[:] for row in grid], {"primitive_id": "extract_changed_region", "bbox": []}
        min_r, min_c, max_r, max_c = _bbox(largest)
        out = [row[min_c:max_c + 1] for row in grid[min_r:max_r + 1]]
        return True, out, {"primitive_id": "extract_changed_region", "bbox": [min_r, min_c, max_r, max_c]}

    # --- fill_region ---
    if name == "fill_region":
        h, w = len(grid), len(grid[0]) if grid else 0
        return True, [[1 for _ in range(w)] for _ in range(h)], {"primitive_id": "fill_region"}

    # Unknown primitive
    return False, grid, {"unsupported_reason": f"oracle: primitive '{name}' not implemented"}


def run_oracle_pipeline(primitive_sequence: List[str], input_grid: List[List[int]]) -> Tuple[bool, List[List[int]], List[dict]]:
    """Run the full 3-step oracle pipeline. Returns (all_supported, final_grid, traces).

    Passes original canvas size through params for place_back context.
    """
    grid = [row[:] for row in input_grid]
    orig_h = len(input_grid)
    orig_w = len(input_grid[0]) if input_grid else 0
    traces = []
    for name in primitive_sequence:
        params = {"original_h": orig_h, "original_w": orig_w}
        supported, grid, trace = reference_primitive(name, grid, params)
        traces.append(trace)
        if not supported:
            return False, grid, traces
    return True, grid, traces