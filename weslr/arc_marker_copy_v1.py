"""ARC-AGI-2 marker-copy capability V1.

Synthetic-only solver capability for:
- copy_object_to_marker

No public ARC data, no scoring, no submission.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


ADAPTER_NAME_V1 = "arc_marker_copy_v1"
SCHEMA_VERSION_V1 = "ArcMarkerCopyV1"


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


def _find_connected_objects(
    grid: Sequence[Sequence[int]],
) -> list[dict[str, Any]]:
    """Find connected components (4-directional) of non-background cells.
    Returns list of {color, cells, min_r, max_r, min_c, max_c, height, width}.
    """
    h = len(grid)
    w = len(grid[0])
    visited = set()
    objects: list[dict[str, Any]] = []

    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in visited:
                color = int(grid[r][c])
                stack = [(r, c)]
                cells: list[tuple[int, int]] = []
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    if grid[cr][cc] == color:
                        cells.append((cr, cc))
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited:
                                if grid[nr][nc] == color:
                                    stack.append((nr, nc))
                if cells:
                    min_r = min(c[0] for c in cells)
                    max_r = max(c[0] for c in cells)
                    min_c = min(c[1] for c in cells)
                    max_c = max(c[1] for c in cells)
                    objects.append({
                        "color": color,
                        "cells": cells,
                        "min_r": min_r,
                        "max_r": max_r,
                        "min_c": min_c,
                        "max_c": max_c,
                        "height": max_r - min_r + 1,
                        "width": max_c - min_c + 1,
                    })
    return objects


def _infer_marker_copy_pattern(
    train_pairs: Sequence[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Infer the marker-copy pattern from train pairs.
    Returns a dict with:
    - 'source_color': color of the source object
    - 'marker_color': color of the marker
    - 'source_height': height of source object
    - 'source_width': width of source object
    - 'placement': 'top_right' (marker is at top-right of copy)
    """
    for pair in train_pairs:
        train_in = _pair_input(pair)
        train_out = _pair_output(pair)

        objects_in = _find_connected_objects(train_in)

        # Find single-cell objects (markers)
        markers = [o for o in objects_in if len(o["cells"]) == 1]
        if len(markers) != 1:
            continue

        marker = markers[0]
        marker_color = marker["color"]
        marker_pos = marker["cells"][0]

        # Find source objects (multi-cell objects that are not the marker)
        sources = [o for o in objects_in if len(o["cells"]) > 1 and o["color"] != marker_color]
        if len(sources) != 1:
            continue

        source = sources[0]
        source_color = source["color"]

        # Verify: output has a copy of the source placed so its top-right
        # corner aligns with the marker position
        # Copy extends downward and leftward from marker
        copy_top_left_r = marker_pos[0]
        copy_top_left_c = marker_pos[1] - source["width"] + 1

        # Check that the copy exists in output
        copy_found = True
        for dr in range(source["height"]):
            for dc in range(source["width"]):
                r = copy_top_left_r + dr
                c = copy_top_left_c + dc
                if not (0 <= r < len(train_out) and 0 <= c < len(train_out[0])):
                    copy_found = False
                    break
                if train_out[r][c] != source_color:
                    copy_found = False
                    break
            if not copy_found:
                break

        if not copy_found:
            continue

        return {
            "source_color": source_color,
            "marker_color": marker_color,
            "source_height": source["height"],
            "source_width": source["width"],
            "placement": "top_right",
        }

    return None


def _find_source_object(
    grid: Sequence[Sequence[int]],
    source_color: int,
) -> dict[str, Any] | None:
    """Find the source object of the given color in the grid."""
    objects = _find_connected_objects(grid)
    for obj in objects:
        if obj["color"] == source_color and len(obj["cells"]) > 1:
            return obj
    return None


def _find_marker(
    grid: Sequence[Sequence[int]],
    marker_color: int,
) -> tuple[int, int] | None:
    """Find the marker cell of the given color."""
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if int(cell) == marker_color:
                return (r, c)
    return None


def _copy_object_to_marker(
    test_input: Sequence[Sequence[int]],
    pattern: dict[str, Any],
) -> list[list[int]] | None:
    """Copy the source object so its top-right corner aligns with the marker.
    The copy extends downward and leftward from the marker position.
    """
    source_color = pattern["source_color"]
    marker_color = pattern["marker_color"]
    source_h = pattern["source_height"]
    source_w = pattern["source_width"]

    source = _find_source_object(test_input, source_color)
    if source is None:
        return None

    marker = _find_marker(test_input, marker_color)
    if marker is None:
        return None

    marker_r, marker_c = marker

    # Place copy so top-right corner is at marker position
    # Copy extends downward and leftward from marker
    copy_top_left_r = marker_r
    copy_top_left_c = marker_c - source_w + 1

    h = len(test_input)
    w = len(test_input[0])

    output = [list(row) for row in test_input]

    # Copy the source object shape
    for dr in range(source_h):
        for dc in range(source_w):
            r = copy_top_left_r + dr
            c = copy_top_left_c + dc
            if 0 <= r < h and 0 <= c < w:
                # Only copy cells that were part of the source object
                src_r = source["min_r"] + dr
                src_c = source["min_c"] + dc
                if test_input[src_r][src_c] == source_color:
                    output[r][c] = source_color

    return output


# --- Main solver ---

def solve_marker_copy_task(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
) -> list[dict[str, Any]]:
    """Solve a marker-copy task. Returns candidates."""
    test_grid = _grid(test_input)
    candidates: list[dict[str, Any]] = []

    pattern = _infer_marker_copy_pattern(train_pairs)
    if pattern is not None:
        result = _copy_object_to_marker(test_grid, pattern)
        if result is not None:
            candidates.append({
                "grid": result,
                "family": "copy_object_to_marker",
                "confidence": 0.9,
                "metadata": {
                    "source_color": pattern["source_color"],
                    "marker_color": pattern["marker_color"],
                    "source_height": pattern["source_height"],
                    "source_width": pattern["source_width"],
                    "source": ADAPTER_NAME_V1,
                },
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
    """Build top-2 candidate packets from marker-copy candidates."""
    candidate_packets: list[dict[str, Any]] = []
    used_fallback = False

    for candidate in candidates[:2]:
        family = _safe_text(candidate.get("family", "marker_copy"))
        output = deepcopy(candidate["grid"])
        metadata = {
            "adapter_name": ADAPTER_NAME_V1,
            "schema_version": SCHEMA_VERSION_V1,
            "task_id": task_id,
            "test_input_index": test_input_index,
            "source_family": family,
            "synthetic_only": True,
            "source_kind": "marker_copy_solver",
            "trace_labels": ["marker_copy", family, "synthetic_only"],
        }
        candidate_packets.append({
            "candidate_id": f"{task_id}:{test_input_index}:{family}",
            "source_candidate_id": f"{task_id}:{test_input_index}:{family}",
            "source_kind": "marker_copy_solver",
            "synthetic_only": True,
            "grid": output,
            "confidence_label": "high",
            "evidence_labels": ["marker_copy", family, "synthetic_only"],
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


def build_arc_agi2_marker_copy_top2_attempt_packet_v1(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
    *,
    task_id: Any = "arc_agi2_marker_copy_task",
    test_input_index: Any = 0,
    fallback_candidate_packets: Sequence[Mapping[str, Any]] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a top-2 attempt packet for marker-copy completion."""
    task_id_text = str(task_id)
    test_input_index_int = int(test_input_index)
    test_grid = _grid(test_input)

    solver_candidates = solve_marker_copy_task(train_pairs, test_grid)
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
        "trace_labels": ["marker_copy", "top2_attempts", "synthetic_only"],
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
