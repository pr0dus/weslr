"""BH80 Scene Materializer — converts scene_spec into a concrete integer grid.

Independent from solver dispatch and oracle. Reads scene_spec only.
"""

from __future__ import annotations

import hashlib
from typing import Any


def _background_value(spec: dict) -> int:
    return spec.get("background", 0)


def _seed_from_task_id(task_id: str) -> int:
    h = hashlib.sha256(task_id.encode()).digest()
    return int.from_bytes(h[:4], "big")


def _draw_rectangle(grid: list[list[int]], row: int, col: int, h: int, w: int, color: int, grid_h: int, grid_w: int) -> None:
    for r in range(row, min(row + h, grid_h)):
        for c in range(col, min(col + w, grid_w)):
            if 0 <= r < grid_h and 0 <= c < grid_w:
                grid[r][c] = color


def _draw_l_shape(grid: list[list[int]], row: int, col: int, color: int, grid_h: int, grid_w: int) -> None:
    # L-shape: 3x3 minus top-right corner
    shape = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
    for dr, dc in shape:
        r, c = row + dr, col + dc
        if 0 <= r < grid_h and 0 <= c < grid_w:
            grid[r][c] = color


def _draw_cross(grid: list[list[int]], row: int, col: int, color: int, grid_h: int, grid_w: int) -> None:
    # Plus sign: center + 4 neighbors
    shape = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    for dr, dc in shape:
        r, c = row + dr, col + dc
        if 0 <= r < grid_h and 0 <= c < grid_w:
            grid[r][c] = color


def _draw_donut(grid: list[list[int]], row: int, col: int, h: int, w: int, color: int, bg: int, grid_h: int, grid_w: int) -> None:
    # Fill rectangle, then hollow out interior
    _draw_rectangle(grid, row, col, h, w, color, grid_h, grid_w)
    inner_r, inner_c = row + 1, col + 1
    inner_h, inner_w = max(h - 2, 0), max(w - 2, 0)
    for r in range(inner_r, min(inner_r + inner_h, grid_h)):
        for c in range(inner_c, min(inner_c + inner_w, grid_w)):
            if 0 <= r < grid_h and 0 <= c < grid_w:
                grid[r][c] = bg


def _draw_disconnected(grid: list[list[int]], row: int, col: int, h: int, w: int, color: int, grid_h: int, grid_w: int) -> None:
    # Two rectangles with a 2-cell gap
    half_w = max(w // 2, 1)
    _draw_rectangle(grid, row, col, h, half_w, color, grid_h, grid_w)
    _draw_rectangle(grid, row, col + half_w + 2, h, half_w, color, grid_h, grid_w)


def _draw_object(grid: list[list[int]], obj: dict, bg: int, grid_h: int, grid_w: int) -> None:
    obj_type = obj.get("type", "rectangle")
    attrs = obj.get("attributes", obj)  # support both nested and flat
    color = attrs.get("color", 1)
    if isinstance(color, str):
        color_map = {"red": 1, "green": 2, "blue": 3, "yellow": 4, "purple": 5, "orange": 6, "pink": 7, "gray": 8, "cyan": 9}
        color = color_map.get(color, 1)
    row, col = attrs.get("position", [0, 0])
    size = attrs.get("size", [2, 2])
    h, w = size[0], size[1]

    if obj_type == "rectangle":
        _draw_rectangle(grid, row, col, h, w, color, grid_h, grid_w)
    elif obj_type == "l_shape":
        _draw_l_shape(grid, row, col, color, grid_h, grid_w)
    elif obj_type == "cross":
        _draw_cross(grid, row, col, color, grid_h, grid_w)
    elif obj_type == "donut":
        _draw_donut(grid, row, col, h, w, color, bg, grid_h, grid_w)
    elif obj_type == "disconnected":
        _draw_disconnected(grid, row, col, h, w, color, grid_h, grid_w)
    else:
        _draw_rectangle(grid, row, col, h, w, color, grid_h, grid_w)


def materialize_scene(scene_spec: dict, task_id: str | None = None) -> list[list[int]]:
    """Convert a scene_spec dict into a concrete integer grid.

    Supports: grid_size, background, initial_objects, distractors,
    rectangle/l_shape/cross/donut/disconnected shapes, noise_pixels,
    edge clipping, overlapping objects by draw order, colors 1-9.
    """
    grid_h, grid_w = scene_spec.get("grid_size", [10, 10])
    grid_h, grid_w = int(grid_h), int(grid_w)
    bg = _background_value(scene_spec)
    grid = [[bg for _ in range(grid_w)] for _ in range(grid_h)]

    # Draw initial objects in order
    for obj in scene_spec.get("initial_objects", []):
        _draw_object(grid, obj, bg, grid_h, grid_w)

    # Draw distractors
    for obj in scene_spec.get("distractors", []):
        _draw_object(grid, obj, bg, grid_h, grid_w)

    # Deterministic noise
    noise_count = scene_spec.get("noise_pixels", 0)
    if noise_count > 0 and task_id:
        rng = _seed_from_task_id(task_id)
        for _ in range(noise_count):
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            r = rng % grid_h
            rng = (rng * 1103515245 + 12345) & 0x7FFFFFFF
            c = rng % grid_w
            grid[r][c] = (rng % 9) + 1

    return grid