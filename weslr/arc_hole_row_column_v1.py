"""ARC-AGI-2 hole filling and row/column extraction capability V1.

Synthetic-only solver capability for:
- fill_enclosed_hole
- extract_row_or_column_by_marker

No public ARC data, no scoring, no submission.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


ADAPTER_NAME_V1 = "arc_hole_row_column_v1"
SCHEMA_VERSION_V1 = "ArcHoleRowColumnV1"


def _grid(rows: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(map(int, row)) for row in rows]


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _grids_equal(a: Any, b: Any) -> bool:
    if not isinstance(a, list) or not isinstance(b, list):
        return False
    if len(a) != len(b):
        return False
    for ra, rb in zip(a, b):
        if not isinstance(ra, list) or not isinstance(rb, list):
            return False
        if len(ra) != len(rb):
            return False
        for ca, cb in zip(ra, rb):
            if int(ca) != int(cb):
                return False
    return True


def _pair_input(pair: Mapping[str, Any]) -> list[list[int]]:
    raw = pair.get("input", pair.get("input_grid", []))
    return _grid(raw)


def _pair_output(pair: Mapping[str, Any]) -> list[list[int]]:
    raw = pair.get("output", pair.get("output_grid", []))
    return _grid(raw)


def _non_background_cells(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    """Return (r, c, color) for all non-zero cells."""
    cells: list[tuple[int, int, int]] = []
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell != 0:
                cells.append((r, c, int(cell)))
    return cells


# --- Hole filling ---

def _is_enclosed_hole(grid: Sequence[Sequence[int]], r: int, c: int) -> bool:
    """Check if cell (r,c) is a background cell enclosed by non-background cells.
    Uses flood-fill from the cell; if the flood reaches the grid boundary, it's not enclosed.
    """
    h = len(grid)
    w = len(grid[0])
    visited = set()
    stack = [(r, c)]
    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in visited:
            continue
        visited.add((cr, cc))
        # If we reach the boundary, the hole is not enclosed
        if cr == 0 or cr == h - 1 or cc == 0 or cc == w - 1:
            return False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                if grid[nr][nc] == 0:
                    stack.append((nr, nc))
    return True


def _infer_fill_color(train_pairs: Sequence[Mapping[str, Any]], test_input: Sequence[Sequence[int]]) -> int | None:
    """Infer the fill color from train pairs and test input.
    The fill color is the non-zero border color that surrounds the hole.
    First try to find a non-zero cell adjacent to a hole in the test input.
    Fall back to the train pair's fill color.
    """
    # Try test input first: find a non-zero cell adjacent to a background cell
    h = len(test_input)
    w = len(test_input[0])
    for r in range(h):
        for c in range(w):
            if test_input[r][c] == 0:
                # Check neighbors for non-zero color
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and test_input[nr][nc] != 0:
                        return int(test_input[nr][nc])
    # Fall back to train pair
    for pair in train_pairs:
        train_in = _pair_input(pair)
        train_out = _pair_output(pair)
        if not isinstance(train_in, list) or not isinstance(train_out, list):
            continue
        if not train_in or not train_out:
            continue
        for r in range(len(train_in)):
            if r >= len(train_out):
                continue
            for c in range(len(train_in[0])):
                if c >= len(train_out[0]):
                    continue
                if train_in[r][c] == 0 and train_out[r][c] != 0:
                    return int(train_out[r][c])
    return None


def _fill_enclosed_holes(
    test_input: Sequence[Sequence[int]],
    fill_color: int,
) -> list[list[int]] | None:
    """Fill all enclosed background holes with the given color."""
    h = len(test_input)
    w = len(test_input[0])
    output = [list(row) for row in test_input]
    filled = False
    for r in range(h):
        for c in range(w):
            if output[r][c] == 0 and _is_enclosed_hole(output, r, c):
                output[r][c] = fill_color
                filled = True
    return output if filled else None


# --- Row/column extraction by marker ---

def _find_marker_cells(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    """Find non-zero cells that could be markers.
    Markers are non-zero cells that appear in a grid where most cells are background.
    """
    cells = _non_background_cells(grid)
    # In a marker task, non-zero cells are the markers
    return cells


def _infer_marker_pattern(train_pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Infer the marker pattern from train pairs.
    Returns a dict with:
    - 'mode': 'row' or 'column'
    - 'left_marker_color': color of the left/top marker
    - 'right_marker_color': color of the right/bottom marker
    - 'output_row' or 'output_col': the extracted row/column index
    """
    for pair in train_pairs:
        train_in = _pair_input(pair)
        train_out = _pair_output(pair)
        markers = _find_marker_cells(train_in)
        if len(markers) != 2:
            continue
        
        m1, m2 = markers
        r1, c1, color1 = m1
        r2, c2, color2 = m2
        
        # Check if markers are in the same row (row extraction)
        if r1 == r2:
            left = min(c1, c2)
            right = max(c1, c2)
            left_color = color1 if c1 < c2 else color2
            right_color = color2 if c1 < c2 else color1
            # Output should be a single row
            if len(train_out) == 1:
                return {
                    "mode": "row",
                    "row_index": r1,
                    "left_marker_color": left_color,
                    "right_marker_color": right_color,
                }
        
        # Check if markers are in the same column (column extraction)
        if c1 == c2:
            top = min(r1, r2)
            bottom = max(r1, r2)
            top_color = color1 if r1 < r2 else color2
            bottom_color = color2 if r1 < r2 else color1
            if len(train_out[0]) == 1:
                return {
                    "mode": "column",
                    "col_index": c1,
                    "top_marker_color": top_color,
                    "bottom_marker_color": bottom_color,
                }
    
    return None


def _extract_row_by_marker(
    test_input: Sequence[Sequence[int]],
    pattern: dict[str, Any],
) -> list[list[int]] | None:
    """Extract a row from test input based on marker pattern."""
    markers = _find_marker_cells(test_input)
    if len(markers) != 2:
        return None
    
    m1, m2 = markers
    r1, c1, color1 = m1
    r2, c2, color2 = m2
    
    # Find the row that has both markers
    if r1 != r2:
        return None
    
    row_idx = r1
    left_color = pattern.get("left_marker_color")
    right_color = pattern.get("right_marker_color")
    
    # Verify marker colors match
    left_marker = color1 if c1 < c2 else color2
    right_marker = color2 if c1 < c2 else color1
    if left_marker != left_color or right_marker != right_color:
        return None
    
    # Extract the row, replacing the right marker with 0
    w = len(test_input[0])
    output = [list(test_input[row_idx])]
    # Find the rightmost marker and replace it with 0
    rightmost_c = max(c1, c2)
    output[0][rightmost_c] = 0
    return output


def _extract_column_by_marker(
    test_input: Sequence[Sequence[int]],
    pattern: dict[str, Any],
) -> list[list[int]] | None:
    """Extract a column from test input based on marker pattern."""
    markers = _find_marker_cells(test_input)
    if len(markers) != 2:
        return None
    
    m1, m2 = markers
    r1, c1, color1 = m1
    r2, c2, color2 = m2
    
    # Find the column that has both markers
    if c1 != c2:
        return None
    
    col_idx = c1
    top_color = pattern.get("top_marker_color")
    bottom_color = pattern.get("bottom_marker_color")
    
    # Verify marker colors match
    top_marker = color1 if r1 < r2 else color2
    bottom_marker = color2 if r1 < r2 else color1
    if top_marker != top_color or bottom_marker != bottom_color:
        return None
    
    # Extract the column, replacing the bottom marker with 0
    h = len(test_input)
    output = [[test_input[r][col_idx]] for r in range(h)]
    # Find the bottommost marker and replace it with 0
    bottommost_r = max(r1, r2)
    output[bottommost_r][0] = 0
    return output


# --- Main solver ---

def solve_hole_row_column_task(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
) -> list[dict[str, Any]]:
    """Solve a hole filling or row/column extraction task. Returns candidates."""
    test_grid = _grid(test_input)
    candidates: list[dict[str, Any]] = []

    # Try hole filling
    fill_color = _infer_fill_color(train_pairs, test_grid)
    if fill_color is not None:
        result = _fill_enclosed_holes(test_grid, fill_color)
        if result is not None:
            candidates.append({
                "grid": result,
                "family": "fill_enclosed_hole",
                "confidence": 0.9,
                "metadata": {"fill_color": fill_color, "source": ADAPTER_NAME_V1},
            })

    # Try row/column extraction by marker
    pattern = _infer_marker_pattern(train_pairs)
    if pattern is not None:
        if pattern["mode"] == "row":
            result = _extract_row_by_marker(test_grid, pattern)
            if result is not None:
                candidates.append({
                    "grid": result,
                    "family": "extract_row_or_column_by_marker",
                    "confidence": 0.9,
                    "metadata": {"mode": "row", "source": ADAPTER_NAME_V1},
                })
        elif pattern["mode"] == "column":
            result = _extract_column_by_marker(test_grid, pattern)
            if result is not None:
                candidates.append({
                    "grid": result,
                    "family": "extract_row_or_column_by_marker",
                    "confidence": 0.9,
                    "metadata": {"mode": "column", "source": ADAPTER_NAME_V1},
                })

    return candidates


def _candidate_packets_for_top2(
    *,
    task_id: str,
    test_input_index: int,
    test_input: Any,
    candidates: list[dict[str, Any]],
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Build top-2 candidate packets from hole/row-column candidates."""
    candidate_packets: list[dict[str, Any]] = []
    used_fallback = False

    for candidate in candidates[:2]:
        family = _safe_text(candidate.get("family", "hole_row_column"))
        output = deepcopy(candidate["grid"])
        metadata = {
            "adapter_name": ADAPTER_NAME_V1,
            "schema_version": SCHEMA_VERSION_V1,
            "task_id": task_id,
            "test_input_index": test_input_index,
            "source_family": family,
            "synthetic_only": True,
            "source_kind": "hole_row_column_solver",
            "trace_labels": ["hole_row_column", family, "synthetic_only"],
        }
        candidate_packets.append({
            "candidate_id": f"{task_id}:{test_input_index}:{family}",
            "source_candidate_id": f"{task_id}:{test_input_index}:{family}",
            "source_kind": "hole_row_column_solver",
            "synthetic_only": True,
            "grid": output,
            "confidence_label": "high",
            "evidence_labels": ["hole_row_column", family, "synthetic_only"],
            "leakage_flags": {
                "uses_test_output": False,
                "uses_solution_file": False,
                "uses_answer_key": False,
                "uses_hidden_private_data": False,
                "uses_task_id_shortcut": False,
                "uses_notes_shortcut": False,
                "lookup_table_detected": False,
            },
            "metadata": metadata,
        })

    # Ensure at least 2 candidate packets for top2 contract
    if len(candidate_packets) == 1 and fallback_candidate_packets:
        for fb in fallback_candidate_packets:
            candidate_packets.append(dict(fb))
            break
        used_fallback = True
    elif len(candidate_packets) == 1:
        dup = dict(candidate_packets[0])
        dup["metadata"] = dict(dup.get("metadata", {}))
        dup["metadata"]["source_family"] = "fallback"
        candidate_packets.append(dup)
        used_fallback = True

    if not candidate_packets and fallback_candidate_packets:
        for fb in fallback_candidate_packets:
            candidate_packets.append(dict(fb))
        used_fallback = True

    return candidate_packets, used_fallback


def build_arc_agi2_hole_row_column_top2_attempt_packet_v1(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    *,
    task_id: Any = "arc_agi2_hole_row_column_task",
    test_input_index: Any = 0,
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a top-2 attempt packet for hole/row-column completion."""
    task_id_text = str(task_id)
    test_input_index_int = int(test_input_index)
    test_grid = _grid(test_input)

    solver_candidates = solve_hole_row_column_task(train_pairs, test_grid)
    candidate_packets, used_fallback = _candidate_packets_for_top2(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        test_input=test_grid,
        candidates=solver_candidates,
        fallback_candidate_packets=fallback_candidate_packets,
    )

    packet_metadata = {
        "adapter_name": ADAPTER_NAME_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "task_id": task_id_text,
        "test_input_index": test_input_index_int,
        "candidate_count": len(solver_candidates),
        "used_fallback": used_fallback,
        "synthetic_only": True,
        "trace_labels": ["hole_row_column", "top2_attempts", "synthetic_only"],
    }
    if isinstance(metadata, Mapping):
        packet_metadata.update(dict(metadata))

    from weslr.arc_agi2_submission_contract import build_arc_agi2_top2_attempt_packet_v1
    return build_arc_agi2_top2_attempt_packet_v1(
        task_id=task_id_text,
        test_input_index=test_input_index_int,
        candidate_packets=candidate_packets,
        metadata=packet_metadata,
    )
