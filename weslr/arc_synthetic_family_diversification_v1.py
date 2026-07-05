"""ARC-AGI-2 synthetic family diversification V1.

New synthetic ARC-style family types for benchmark diversification.
No public ARC data, no scoring, no submission, no solver repair.
"""

from __future__ import annotations

from random import Random
from typing import Any, Mapping, Sequence

DIVERSIFIED_FAMILY_ORDER_V1: tuple[str, ...] = (
    "complete_horizontal_symmetry",
    "complete_vertical_symmetry",
    "fill_enclosed_hole",
    "remove_distractor_object",
    "copy_object_to_marker",
    "extend_line_to_boundary",
    "extract_row_or_column_by_marker",
    "recolor_by_object_size",
)

DIVERSIFIED_FAMILY_COUNT_V1 = len(DIVERSIFIED_FAMILY_ORDER_V1)


def _grid(rows: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(map(int, row)) for row in rows]


def _task(task_id: str, *, family_label: str, primitive_chain: Sequence[str],
          train_pairs: Sequence[Mapping[str, Any]],
          test_input: Sequence[Sequence[int]],
          expected_output: Sequence[Sequence[int]],
          difficulty: str, variant: str, seed: int,
          metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "family_label": family_label,
        "primitive_chain": list(primitive_chain),
        "train_pairs": [{"input": _grid(p["input"]), "output": _grid(p["output"])} for p in train_pairs],
        "test_input": _grid(test_input),
        "expected_output": _grid(expected_output),
        "difficulty": difficulty,
        "variant": variant,
        "seed": int(seed),
        "metadata": {str(k): v for k, v in metadata.items()},
    }


def _rng(seed: int, family_label: str, variant: str) -> Random:
    return Random(f"{seed}:diversified:{family_label}:{variant}")


def _embed(center: Sequence[Sequence[int]], *, background: int = 0,
           top: int = 1, left: int = 1, height: int = 5, width: int = 5) -> list[list[int]]:
    grid = [[background for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(center):
        for c, cell in enumerate(row):
            grid[top + r][left + c] = int(cell)
    return grid


def _recolor(grid: Sequence[Sequence[int]], mapping: Mapping[int, int]) -> list[list[int]]:
    return [[int(mapping.get(int(cell), int(cell))) for cell in row] for row in grid]


def _hflip(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _vflip(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return list(reversed(grid))


def _bbox(grid: Sequence[Sequence[int]]) -> tuple[int, int, int, int]:
    """Return (min_r, min_c, max_r, max_c) of non-zero cells."""
    rows, cols = len(grid), len(grid[0])
    min_r, min_c, max_r, max_c = rows, cols, -1, -1
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0:
                min_r = min(min_r, r)
                min_c = min(min_c, c)
                max_r = max(max_r, r)
                max_c = max(max_c, c)
    return (min_r, min_c, max_r, max_c)


def _connected_components(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    """Find connected components (4-directional) of non-zero cells."""
    rows, cols = len(grid), len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    components: list[list[tuple[int, int]]] = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 0 and not visited[r][c]:
                color = grid[r][c]
                stack = [(r, c)]
                comp: list[tuple[int, int]] = []
                while stack:
                    cr, cc = stack.pop()
                    if cr < 0 or cr >= rows or cc < 0 or cc >= cols:
                        continue
                    if visited[cr][cc] or grid[cr][cc] != color:
                        continue
                    visited[cr][cc] = True
                    comp.append((cr, cc))
                    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        stack.append((cr + dr, cc + dc))
                components.append(comp)
    return components


def _object_sizes(grid: Sequence[Sequence[int]]) -> dict[int, int]:
    """Return {color: pixel_count} for each non-zero color."""
    sizes: dict[int, int] = {}
    for row in grid:
        for cell in row:
            if cell != 0:
                sizes[cell] = sizes.get(cell, 0) + 1
    return sizes


# --- Family generators ---

def _gen_complete_horizontal_symmetry(seed: int, variant: str) -> dict[str, Any]:
    """Input: left half of a symmetric shape. Output: full symmetric shape."""
    rng = _rng(seed, "complete_horizontal_symmetry", variant)
    color = 1 + rng.randint(0, 5)
    # Create a left-half shape (3x3 left half)
    left_half = _grid([[color, 0], [color, color], [color, 0]])
    # Full shape: left half + horizontal mirror
    full = [row + list(reversed(row)) for row in left_half]
    # Train: embed both
    train_in = _embed(left_half, height=5, width=6)
    train_out = _embed(full, height=5, width=6)
    # Test: different color, same shape
    test_color = 1 + ((color + 1) % 6)
    test_left = _grid([[test_color, 0], [test_color, test_color], [test_color, 0]])
    test_full = [row + list(reversed(row)) for row in test_left]
    test_in = _embed(test_left, height=5, width=6)
    test_exp = _embed(test_full, height=5, width=6)
    return _task(
        f"{seed}:complete_horizontal_symmetry:{variant}",
        family_label="complete_horizontal_symmetry",
        primitive_chain=("complete_horizontal_symmetry",),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=test_exp,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "complete_horizontal_symmetry"},
    )


def _gen_complete_vertical_symmetry(seed: int, variant: str) -> dict[str, Any]:
    """Input: top half of a symmetric shape. Output: full symmetric shape."""
    rng = _rng(seed, "complete_vertical_symmetry", variant)
    color = 1 + rng.randint(0, 5)
    # Top half shape (2x3)
    top_half = _grid([[color, color, color], [color, 0, color]])
    # Full shape: top half + vertical mirror
    full = top_half + list(reversed(top_half))
    train_in = _embed(top_half, height=6, width=5)
    train_out = _embed(full, height=6, width=5)
    test_color = 1 + ((color + 1) % 6)
    test_top = _grid([[test_color, test_color, test_color], [test_color, 0, test_color]])
    test_full = test_top + list(reversed(test_top))
    test_in = _embed(test_top, height=6, width=5)
    test_exp = _embed(test_full, height=6, width=5)
    return _task(
        f"{seed}:complete_vertical_symmetry:{variant}",
        family_label="complete_vertical_symmetry",
        primitive_chain=("complete_vertical_symmetry",),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=test_exp,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "complete_vertical_symmetry"},
    )


def _gen_fill_enclosed_hole(seed: int, variant: str) -> dict[str, Any]:
    """Input: object with interior hole. Output: hole filled with object color."""
    rng = _rng(seed, "fill_enclosed_hole", variant)
    color = 1 + rng.randint(0, 5)
    # A 5x5 ring with a hole
    ring = [
        [color, color, color, color, color],
        [color, 0, 0, 0, color],
        [color, 0, 0, 0, color],
        [color, 0, 0, 0, color],
        [color, color, color, color, color],
    ]
    filled = [
        [color, color, color, color, color],
        [color, color, color, color, color],
        [color, color, color, color, color],
        [color, color, color, color, color],
        [color, color, color, color, color],
    ]
    test_color = 1 + ((color + 1) % 6)
    test_ring = [[test_color if cell == color else 0 for cell in row] for row in ring]
    test_filled = [[test_color if cell == color else test_color for cell in row] for row in filled]
    return _task(
        f"{seed}:fill_enclosed_hole:{variant}",
        family_label="fill_enclosed_hole",
        primitive_chain=("fill_enclosed_hole",),
        train_pairs=(({"input": ring, "output": filled}),),
        test_input=test_ring,
        expected_output=test_filled,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "fill_enclosed_hole"},
    )


def _gen_remove_distractor_object(seed: int, variant: str) -> dict[str, Any]:
    """Input: target + distractor objects. Output: only target object."""
    rng = _rng(seed, "remove_distractor_object", variant)
    target_color = 1 + rng.randint(0, 5)
    dist_color = 1 + ((target_color + 2) % 6)
    # Train: 5x5 with target (2x2 block) and distractor (single cell)
    train_in = _grid([
        [0, 0, 0, 0, 0],
        [0, target_color, target_color, 0, 0],
        [0, target_color, target_color, 0, 0],
        [0, 0, 0, 0, dist_color],
        [0, 0, 0, 0, 0],
    ])
    train_out = _grid([
        [0, 0, 0, 0, 0],
        [0, target_color, target_color, 0, 0],
        [0, target_color, target_color, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    # Test: different positions
    test_in = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, target_color, target_color, 0],
        [0, 0, target_color, target_color, 0],
        [dist_color, 0, 0, 0, 0],
    ])
    test_out = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, target_color, target_color, 0],
        [0, 0, target_color, target_color, 0],
        [0, 0, 0, 0, 0],
    ])
    return _task(
        f"{seed}:remove_distractor_object:{variant}",
        family_label="remove_distractor_object",
        primitive_chain=("remove_distractor_object",),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=test_out,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "remove_distractor_object"},
    )


def _gen_copy_object_to_marker(seed: int, variant: str) -> dict[str, Any]:
    """Input: object + marker cell. Output: object copied near marker."""
    rng = _rng(seed, "copy_object_to_marker", variant)
    color = 1 + rng.randint(0, 5)
    marker = 1 + ((color + 3) % 6)
    # Train: 5x5, object at top-left, marker at bottom-right
    train_in = _grid([
        [color, color, 0, 0, 0],
        [color, color, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, marker],
        [0, 0, 0, 0, 0],
    ])
    train_out = _grid([
        [color, color, 0, 0, 0],
        [color, color, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, color, color],
        [0, 0, 0, color, color],
    ])
    # Test: different positions
    test_in = _grid([
        [0, 0, 0, 0, 0],
        [0, color, color, 0, 0],
        [0, color, color, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, marker],
    ])
    test_out = _grid([
        [0, 0, 0, 0, 0],
        [0, color, color, 0, 0],
        [0, color, color, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, color, color],
    ])
    return _task(
        f"{seed}:copy_object_to_marker:{variant}",
        family_label="copy_object_to_marker",
        primitive_chain=("copy_object_to_marker",),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=test_out,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "copy_object_to_marker"},
    )


def _gen_extend_line_to_boundary(seed: int, variant: str) -> dict[str, Any]:
    """Input: partial line. Output: line extended to grid boundary."""
    rng = _rng(seed, "extend_line_to_boundary", variant)
    color = 1 + rng.randint(0, 5)
    # Train: 5x5, partial horizontal line at row 2, columns 1-3
    train_in = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, color, color, color, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    train_out = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [color, color, color, color, color],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    # Test: partial vertical line at column 2, rows 1-3
    test_in = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, color, 0, 0],
        [0, 0, color, 0, 0],
        [0, 0, color, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    test_out = _grid([
        [0, 0, color, 0, 0],
        [0, 0, color, 0, 0],
        [0, 0, color, 0, 0],
        [0, 0, color, 0, 0],
        [0, 0, color, 0, 0],
    ])
    return _task(
        f"{seed}:extend_line_to_boundary:{variant}",
        family_label="extend_line_to_boundary",
        primitive_chain=("extend_line_to_boundary",),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=test_out,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "extend_line_to_boundary"},
    )


def _gen_extract_row_or_column_by_marker(seed: int, variant: str) -> dict[str, Any]:
    """Input: grid with marker pointing to a row. Output: extracted row."""
    rng = _rng(seed, "extract_row_or_column_by_marker", variant)
    color = 1 + rng.randint(0, 5)
    marker = 1 + ((color + 3) % 6)
    # Train: 5x5, marker in last column of row 2, extract that row
    train_in = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [color, 0, 0, 0, marker],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    train_out = _grid([[color, 0, 0, 0, 0]])
    # Test: different row
    test_in = _grid([
        [0, 0, 0, 0, 0],
        [0, color, 0, 0, marker],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ])
    test_out = _grid([[0, color, 0, 0, 0]])
    return _task(
        f"{seed}:extract_row_or_column_by_marker:{variant}",
        family_label="extract_row_or_column_by_marker",
        primitive_chain=("extract_row_or_column_by_marker",),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=test_out,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "extract_row_or_column_by_marker"},
    )


def _gen_recolor_by_object_size(seed: int, variant: str) -> dict[str, Any]:
    """Input: multiple objects. Output: smallest object recolored."""
    rng = _rng(seed, "recolor_by_object_size", variant)
    color_a = 1 + rng.randint(0, 5)
    color_b = 1 + ((color_a + 2) % 6)
    new_color = 1 + ((color_a + 4) % 6)
    # Train: 5x5, two objects: 2x2 block (4 cells) and 1x1 dot (1 cell)
    train_in = _grid([
        [color_a, color_a, 0, 0, 0],
        [color_a, color_a, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, color_b],
        [0, 0, 0, 0, 0],
    ])
    train_out = _grid([
        [color_a, color_a, 0, 0, 0],
        [color_a, color_a, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, new_color],
        [0, 0, 0, 0, 0],
    ])
    # Test: different positions, same size relationship
    test_in = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, color_b, 0, 0],
        [0, color_a, color_a, 0, 0],
        [0, color_a, color_a, 0, 0],
    ])
    test_out = _grid([
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, new_color, 0, 0],
        [0, color_a, color_a, 0, 0],
        [0, color_a, color_a, 0, 0],
    ])
    return _task(
        f"{seed}:recolor_by_object_size:{variant}",
        family_label="recolor_by_object_size",
        primitive_chain=("recolor_by_object_size",),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=test_out,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "recolor_by_object_size"},
    )


DIVERSIFIED_BUILDERS_V1: dict[str, callable] = {
    "complete_horizontal_symmetry": _gen_complete_horizontal_symmetry,
    "complete_vertical_symmetry": _gen_complete_vertical_symmetry,
    "fill_enclosed_hole": _gen_fill_enclosed_hole,
    "remove_distractor_object": _gen_remove_distractor_object,
    "copy_object_to_marker": _gen_copy_object_to_marker,
    "extend_line_to_boundary": _gen_extend_line_to_boundary,
    "extract_row_or_column_by_marker": _gen_extract_row_or_column_by_marker,
    "recolor_by_object_size": _gen_recolor_by_object_size,
}


def build_diversified_family_task_v1(family: str, *, seed: int, variant: str) -> dict[str, Any]:
    """Build a single diversified family task."""
    builder = DIVERSIFIED_BUILDERS_V1.get(family)
    if builder is None:
        raise ValueError(f"Unknown diversified family: {family}")
    return builder(seed, variant)


def build_diversified_family_corpus_v1(
    seed: int,
    tasks_per_family: int = 3,
) -> list[dict[str, Any]]:
    """Build a corpus of diversified family tasks."""
    tasks: list[dict[str, Any]] = []
    for family in DIVERSIFIED_FAMILY_ORDER_V1:
        for vi in range(tasks_per_family):
            variant = f"v{vi}"
            task = build_diversified_family_task_v1(family, seed=seed, variant=variant)
            tasks.append(task)
    return tasks


__all__ = [
    "DIVERSIFIED_FAMILY_ORDER_V1",
    "DIVERSIFIED_FAMILY_COUNT_V1",
    "DIVERSIFIED_BUILDERS_V1",
    "build_diversified_family_task_v1",
    "build_diversified_family_corpus_v1",
]