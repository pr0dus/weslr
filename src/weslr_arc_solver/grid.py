"""WESLR ARC-AGI-2 grid utilities.

Synthetic-only. No public ARC ingestion. No scoring claims.
"""

from __future__ import annotations

from typing import Any, Sequence


def validate_grid_v1(grid: Any) -> list[list[int]]:
    """Validate and normalize a grid to list[list[int]].

    Raises ValueError if the grid is malformed.
    """
    if not isinstance(grid, list):
        raise ValueError(f"grid must be a list, got {type(grid).__name__}")
    if not grid:
        raise ValueError("grid must not be empty")
    height = len(grid)
    width = None
    result: list[list[int]] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, list):
            raise ValueError(f"row[{row_index}] must be a list, got {type(row).__name__}")
        if not row:
            raise ValueError(f"row[{row_index}] is empty")
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(f"row[{row_index}] has {len(row)} columns, expected {width}")
        int_row: list[int] = []
        for col_index, cell in enumerate(row):
            if not isinstance(cell, int) or isinstance(cell, bool):
                raise ValueError(f"grid[{row_index}][{col_index}] must be int, got {type(cell).__name__}")
            if cell < 0 or cell > 9:
                raise ValueError(f"grid[{row_index}][{col_index}] value {cell} out of range 0-9")
            int_row.append(cell)
        result.append(int_row)
    return result


def grid_shape(grid: Any) -> tuple[int, int]:
    """Return (height, width) of a grid."""
    validated = validate_grid_v1(grid)
    return (len(validated), len(validated[0]) if validated else 0)


def grids_equal(a: Any, b: Any) -> bool:
    """Check if two grids are structurally equal."""
    try:
        return validate_grid_v1(a) == validate_grid_v1(b)
    except (ValueError, TypeError):
        return False


def grid_copy(grid: Any) -> list[list[int]]:
    """Deep copy a validated grid."""
    return [list(row) for row in validate_grid_v1(grid)]
