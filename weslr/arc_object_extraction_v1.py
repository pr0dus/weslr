"""ARC object extraction and simple bbox/translation helpers V1.

Pure Python, deterministic, and metadata-safe.
This module does not touch public ARC data, scoring, provider calls, or
runtime/chat/UI paths.
"""

from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ObjectCandidate:
    object_id: str
    color: int
    cells: tuple[tuple[int, int], ...]
    bbox: tuple[int, int, int, int]
    size: int
    width: int
    height: int
    touches_boundary: bool
    has_hole: bool
    canonical_shape: tuple[tuple[int, int], ...]


def _is_int_cell(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_grid_v1(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("invalid_grid")
    if any(not isinstance(row, list) or not row for row in grid):
        raise ValueError("invalid_grid")
    width = len(grid[0])
    out: list[list[int]] = []
    for row in grid:
        if len(row) != width:
            raise ValueError("ragged_grid")
        normalized_row: list[int] = []
        for cell in row:
            if not _is_int_cell(cell):
                raise ValueError("non_integer_cell")
            normalized_row.append(int(cell))
        out.append(normalized_row)
    return out


def infer_background_value_v1(grid: Sequence[Sequence[int]], explicit_background: int | None = None) -> int:
    if explicit_background is not None:
        if not _is_int_cell(explicit_background):
            raise ValueError("invalid_background_override")
        return int(explicit_background)
    values = [cell for row in grid for cell in row]
    if not values:
        raise ValueError("empty_grid")
    return Counter(values).most_common(1)[0][0]


def _neighbors(row: int, column: int) -> list[tuple[int, int]]:
    return [(row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)]


def _in_bounds(grid: Sequence[Sequence[int]], row: int, column: int) -> bool:
    return 0 <= row < len(grid) and 0 <= column < len(grid[0])


def _bounding_box(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _canonical_shape(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    row0, col0, _, _ = _bounding_box(cells)
    return tuple(sorted((r - row0, c - col0) for r, c in cells))


def _has_hole(grid: Sequence[Sequence[int]], cells: Sequence[tuple[int, int]], bbox: tuple[int, int, int, int]) -> bool:
    row0, col0, row1, col1 = bbox
    cell_set = set(cells)
    seen: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()
    # Seed with background cells on the bbox border.
    for r in range(row0, row1 + 1):
        for c in range(col0, col1 + 1):
            if r not in {row0, row1} and c not in {col0, col1}:
                continue
            if (r, c) not in cell_set:
                q.append((r, c))
                seen.add((r, c))
    while q:
        r, c = q.popleft()
        for nr, nc in _neighbors(r, c):
            if nr < row0 or nr > row1 or nc < col0 or nc > col1:
                continue
            if (nr, nc) in cell_set or (nr, nc) in seen:
                continue
            seen.add((nr, nc))
            q.append((nr, nc))
    for r in range(row0 + 1, row1):
        for c in range(col0 + 1, col1):
            if (r, c) not in cell_set and (r, c) not in seen:
                return True
    return False


def _connected_components_by_color(grid: Sequence[Sequence[int]], background_value: int) -> list[list[tuple[int, int]]]:
    visited: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if (row, col) in visited or grid[row][col] == background_value:
                continue
            color = grid[row][col]
            q = deque([(row, col)])
            visited.add((row, col))
            cells: list[tuple[int, int]] = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for nr, nc in _neighbors(r, c):
                    if not _in_bounds(grid, nr, nc) or (nr, nc) in visited:
                        continue
                    if grid[nr][nc] != color:
                        continue
                    visited.add((nr, nc))
                    q.append((nr, nc))
            components.append(sorted(cells))
    components.sort(key=lambda cells: (_bounding_box(cells)[0], _bounding_box(cells)[1], len(cells), grid[cells[0][0]][cells[0][1]]))
    return components


def extract_objects_v1(grid: Any, *, background_value: int | None = None) -> dict[str, Any]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    components = _connected_components_by_color(normalized, background)
    objects: list[dict[str, Any]] = []
    for index, cells in enumerate(components):
        bbox = _bounding_box(cells)
        row0, col0, row1, col1 = bbox
        objects.append(
            {
                "object_id": f"component:{index}",
                "color": normalized[cells[0][0]][cells[0][1]],
                "cells": [[r, c] for r, c in cells],
                "bbox": [row0, col0, row1, col1],
                "size": len(cells),
                "width": col1 - col0 + 1,
                "height": row1 - row0 + 1,
                "touches_boundary": any(r in {0, len(normalized) - 1} or c in {0, len(normalized[0]) - 1} for r, c in cells),
                "has_hole": _has_hole(normalized, cells, bbox),
                "canonical_shape": [[r, c] for r, c in _canonical_shape(cells)],
            }
        )
    return {
        "background_value": background,
        "objects": objects,
        "object_count": len(objects),
        "trace": {
            "background_inferred": background_value is None,
            "component_count": len(objects),
            "grid_height": len(normalized),
            "grid_width": len(normalized[0]),
        },
    }


def crop_grid_to_bbox_v1(grid: Any, bbox: Sequence[int]) -> list[list[int]]:
    normalized = validate_grid_v1(grid)
    if not isinstance(bbox, Sequence) or len(bbox) != 4:
        raise ValueError("invalid_bbox")
    r0, c0, r1, c1 = (int(v) for v in bbox)
    if r0 < 0 or c0 < 0 or r1 < r0 or c1 < c0:
        raise ValueError("invalid_bbox")
    if r1 >= len(normalized) or c1 >= len(normalized[0]):
        raise ValueError("bbox_out_of_bounds")
    return [row[c0 : c1 + 1] for row in normalized[r0 : r1 + 1]]


def crop_to_foreground_bbox_v1(grid: Any, *, background_value: int | None = None) -> list[list[int]]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    cells = [(r, c) for r, row in enumerate(normalized) for c, cell in enumerate(row) if cell != background]
    if not cells:
        raise ValueError("no_foreground")
    return crop_grid_to_bbox_v1(normalized, _bounding_box(cells))


def crop_to_largest_object_bbox_v1(grid: Any, *, background_value: int | None = None) -> list[list[int]]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    if not objects:
        raise ValueError("no_foreground")
    largest_size = max(obj["size"] for obj in objects)
    largest = [obj for obj in objects if obj["size"] == largest_size]
    if len(largest) != 1:
        raise ValueError("largest_object_ambiguous")
    return crop_grid_to_bbox_v1(normalized, largest[0]["bbox"])


def crop_selected_color_object_v1(grid: Any, *, color: int, background_value: int | None = None) -> list[list[int]]:
    normalized = validate_grid_v1(grid)
    if not _is_int_cell(color):
        raise ValueError("invalid_color")
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    objects = [obj for obj in extract_objects_v1(normalized, background_value=background)["objects"] if obj["color"] == int(color)]
    if not objects:
        raise ValueError("selected_color_not_found")
    if len(objects) != 1:
        raise ValueError("selected_color_ambiguous")
    return crop_grid_to_bbox_v1(normalized, objects[0]["bbox"])


def translate_object_v1(grid: Any, *, delta_row: int, delta_col: int, background_value: int | None = None) -> list[list[int]]:
    normalized = validate_grid_v1(grid)
    if not isinstance(delta_row, int) or isinstance(delta_row, bool) or not isinstance(delta_col, int) or isinstance(delta_col, bool):
        raise ValueError("invalid_translation_delta")
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    if len(objects) != 1:
        raise ValueError("translation_ambiguous")
    obj = objects[0]
    out = [[background for _ in row] for row in normalized]
    for r, c in ((cell[0], cell[1]) for cell in obj["cells"]):
        nr, nc = r + delta_row, c + delta_col
        if not _in_bounds(normalized, nr, nc):
            raise ValueError("translation_out_of_bounds")
        out[nr][nc] = normalized[r][c]
    return out


__all__ = [
    "ObjectCandidate",
    "crop_grid_to_bbox_v1",
    "crop_selected_color_object_v1",
    "crop_to_foreground_bbox_v1",
    "crop_to_largest_object_bbox_v1",
    "extract_objects_v1",
    "infer_background_value_v1",
    "translate_object_v1",
    "validate_grid_v1",
]
