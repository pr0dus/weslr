"""ARC-AGI-2 synthetic discovery task generator V1.

Synthetic-only task corpus generation for WESLR discovery evaluation.
No public ARC data, no scoring, no submission, no open-ended planning.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any, Iterable, Mapping, Sequence

SINGLE_STEP_FAMILY_ORDER_V1 = (
    "crop_foreground_bbox",
    "crop_largest_object",
    "translate_single_object",
    "rotate_object_90",
    "rotate_object_180",
    "reflect_object_horizontal",
    "reflect_object_vertical",
    "recolor_foreground",
    "swap_two_colors",
    "tile_grid",
    "scale_cells_integer",
    "add_uniform_border",
    "count_objects_to_line",
    "object_count_to_square",
    "select_largest_object",
)

COMPOSITION_FAMILY_ORDER_V1 = (
    "crop_then_recolor",
    "crop_then_rotate_or_reflect",
    "crop_then_tile",
    "recolor_then_border",
    "select_then_recolor",
)

ADVERSARIAL_FAMILY_ORDER_V1 = (
    "inconsistent_train_examples",
    "ambiguous_multiple_rules",
    "unsupported_primitive_chain",
    "near_match_one_cell",
    "same_palette_wrong_geometry",
    "same_geometry_wrong_recolor",
    "count_tie_ambiguity",
)

SUPPORTED_FAMILY_ORDER_V1 = SINGLE_STEP_FAMILY_ORDER_V1 + COMPOSITION_FAMILY_ORDER_V1 + ADVERSARIAL_FAMILY_ORDER_V1


@dataclass(frozen=True)
class SyntheticDiscoveryTaskV1:
    task_id: str
    family_label: str
    primitive_chain: tuple[str, ...]
    train_pairs: tuple[dict[str, Any], ...]
    test_input: list[list[int]]
    expected_output: list[list[int]]
    difficulty: str
    variant: str
    seed: int
    metadata: dict[str, Any]

    def to_json_safe_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "family_label": self.family_label,
            "primitive_chain": list(self.primitive_chain),
            "train_pairs": [dict(pair) for pair in self.train_pairs],
            "test_input": [list(row) for row in self.test_input],
            "expected_output": [list(row) for row in self.expected_output],
            "difficulty": self.difficulty,
            "variant": self.variant,
            "seed": int(self.seed),
            "metadata": dict(self.metadata),
        }


def _grid(rows: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(map(int, row)) for row in rows]


def _shape_valid(grid: Sequence[Sequence[int]]) -> bool:
    if not isinstance(grid, list) or not grid:
        return False
    width = len(grid[0])
    if width <= 0:
        return False
    for row in grid:
        if not isinstance(row, list) or len(row) != width:
            return False
        for cell in row:
            if not isinstance(cell, int) or isinstance(cell, bool):
                return False
    return True


def _task(task_id: str, *, family_label: str, primitive_chain: Sequence[str], train_pairs: Sequence[Mapping[str, Any]], test_input: Sequence[Sequence[int]], expected_output: Sequence[Sequence[int]], difficulty: str, variant: str, seed: int, metadata: Mapping[str, Any]) -> dict[str, Any]:
    task = SyntheticDiscoveryTaskV1(
        task_id=task_id,
        family_label=family_label,
        primitive_chain=tuple(primitive_chain),
        train_pairs=tuple({"input": _grid(pair["input"]), "output": _grid(pair["output"])} for pair in train_pairs),
        test_input=_grid(test_input),
        expected_output=_grid(expected_output),
        difficulty=difficulty,
        variant=variant,
        seed=int(seed),
        metadata={str(key): value for key, value in metadata.items()},
    )
    return task.to_json_safe_dict()


def _rng(seed: int, family_label: str, variant: str) -> Random:
    return Random(f"{seed}:{family_label}:{variant}")


def _embed(center: Sequence[Sequence[int]], *, background: int = 0, top: int = 1, left: int = 1, height: int = 4, width: int = 4) -> list[list[int]]:
    grid = [[background for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(center):
        for c, cell in enumerate(row):
            grid[top + r][left + c] = int(cell)
    return grid


def _tile(grid: Sequence[Sequence[int]], repeat_rows: int, repeat_cols: int) -> list[list[int]]:
    base = [list(map(int, row)) for row in grid]
    out: list[list[int]] = []
    for _ in range(repeat_rows):
        for row in base:
            new_row: list[int] = []
            for _ in range(repeat_cols):
                new_row.extend(row)
            out.append(new_row)
    return out


def _scale_cells(grid: Sequence[Sequence[int]], scale: int) -> list[list[int]]:
    base = [list(map(int, row)) for row in grid]
    out: list[list[int]] = []
    for row in base:
        expanded_row: list[int] = []
        for cell in row:
            expanded_row.extend([int(cell)] * scale)
        for _ in range(scale):
            out.append(list(expanded_row))
    return out


def _border(grid: Sequence[Sequence[int]], color: int, padding: int = 1) -> list[list[int]]:
    base = [list(map(int, row)) for row in grid]
    height = len(base) + padding * 2
    width = len(base[0]) + padding * 2
    out = [[color for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(base):
        for c, cell in enumerate(row):
            out[padding + r][padding + c] = int(cell)
    return out


def _recolor(grid: Sequence[Sequence[int]], mapping: Mapping[int, int]) -> list[list[int]]:
    return [[int(mapping.get(int(cell), int(cell))) for cell in row] for row in grid]


def _count_objects(grid: Sequence[Sequence[int]]) -> int:
    return sum(1 for row in grid for cell in row if int(cell) != 0)


def _single_step_crop_foreground(seed: int, variant: str) -> dict[str, Any]:
    train_input = _grid([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]])
    train_output = _grid([[1, 1], [1, 1]])
    test_input = _grid([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]])
    expected = _grid([[1, 1], [1, 1]])
    return _task(
        f"{seed}:crop_foreground_bbox:{variant}",
        family_label="crop_foreground_bbox",
        primitive_chain=("crop_foreground_bbox",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "crop_foreground_bbox"},
    )


def _single_step_crop_largest(seed: int, variant: str) -> dict[str, Any]:
    train_input = _grid([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 2, 0, 0]])
    train_output = _grid([[1, 1], [1, 1]])
    test_input = _grid([[0, 0, 0, 0], [0, 3, 3, 0], [0, 3, 3, 0], [0, 4, 0, 0]])
    expected = _grid([[3, 3], [3, 3]])
    return _task(
        f"{seed}:crop_largest_object:{variant}",
        family_label="crop_largest_object",
        primitive_chain=("crop_largest_object",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "crop_largest_object"},
    )


def _single_step_translate(seed: int, variant: str) -> dict[str, Any]:
    rng = _rng(seed, "translate_single_object", variant)
    value = 1 + rng.randint(0, 5)
    train_input = _grid([[value, 0, 0], [value, value, 0], [value, 0, 0]])
    train_output = _grid([[0, 0, value], [0, value, value], [0, 0, value]])
    test_input = _grid([[value + 1, 0, 0], [value + 1, value + 1, 0], [value + 1, 0, 0]])
    expected = _grid([[0, 0, value + 1], [0, value + 1, value + 1], [0, 0, value + 1]])
    return _task(
        f"{seed}:translate_single_object:{variant}",
        family_label="translate_single_object",
        primitive_chain=("translate_single_object",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "translate_single_object"},
    )


def _single_step_rotate(seed: int, variant: str, turns: int) -> dict[str, Any]:
    pattern = _grid([[1, 0, 0], [1, 1, 0], [1, 0, 0]])
    if turns == 2:
        output = _grid([[0, 0, 1], [0, 1, 1], [0, 0, 1]])
    elif turns == 1:
        output = _grid([[1, 1, 1], [0, 1, 0], [0, 0, 0]])
    else:
        output = _grid([[0, 1, 0], [1, 1, 1], [0, 0, 0]])
    train_input = pattern
    test_input = pattern
    return _task(
        f"{seed}:rotate_object_{turns * 90}:{variant}",
        family_label=f"rotate_object_{turns * 90}",
        primitive_chain=(f"rotate_object_{turns * 90}",),
        train_pairs=(({"input": train_input, "output": output}),),
        test_input=test_input,
        expected_output=output,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": f"rotate_object_{turns * 90}"},
    )


def _single_step_reflect(seed: int, variant: str, axis: str) -> dict[str, Any]:
    pattern = _grid([[1, 0, 0], [1, 1, 0], [1, 0, 0]])
    if axis == "horizontal":
        output = _grid([[1, 0, 0], [1, 1, 0], [1, 0, 0]])
        family = "reflect_object_horizontal"
    else:
        output = _grid([[0, 1, 0], [1, 1, 0], [0, 1, 0]])
        family = "reflect_object_vertical"
    train_input = _embed(pattern, background=0, top=1, left=1, height=5, width=5)
    test_input = _embed(pattern, background=0, top=1, left=1, height=5, width=5)
    return _task(
        f"{seed}:{family}:{variant}",
        family_label=family,
        primitive_chain=(family,),
        train_pairs=(({"input": train_input, "output": output}),),
        test_input=test_input,
        expected_output=output,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": family},
    )


def _single_step_recolor_foreground(seed: int, variant: str) -> dict[str, Any]:
    train_input = _grid([[0, 0], [1, 1]])
    train_output = _grid([[0, 0], [2, 2]])
    test_input = _grid([[0, 0], [1, 1]])
    expected = _grid([[0, 0], [2, 2]])
    return _task(
        f"{seed}:recolor_foreground:{variant}",
        family_label="recolor_foreground",
        primitive_chain=("recolor_foreground",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "recolor_foreground"},
    )


def _single_step_swap_two_colors(seed: int, variant: str) -> dict[str, Any]:
    train_input = _grid([[1, 2], [2, 1]])
    train_output = _grid([[2, 1], [1, 2]])
    test_input = _grid([[1, 2], [2, 1]])
    return _task(
        f"{seed}:swap_two_colors:{variant}",
        family_label="swap_two_colors",
        primitive_chain=("swap_two_colors",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=train_output,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "swap_two_colors"},
    )


def _single_step_tile_grid(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[1, 2], [3, 4]])
    train_input = base
    train_output = _tile(base, 2, 2)
    test_input = _grid([[5, 6], [7, 8]])
    expected = _tile(test_input, 2, 2)
    return _task(
        f"{seed}:tile_grid:{variant}",
        family_label="tile_grid",
        primitive_chain=("tile_grid",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "tile_grid"},
    )


def _single_step_scale_cells(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[1, 2], [3, 4]])
    train_output = _scale_cells(base, 2)
    test_input = _grid([[5, 6], [7, 8]])
    expected = _scale_cells(test_input, 2)
    return _task(
        f"{seed}:scale_cells_integer:{variant}",
        family_label="scale_cells_integer",
        primitive_chain=("scale_cells_integer",),
        train_pairs=(({"input": base, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "scale_cells_integer"},
    )


def _single_step_border(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[1, 2], [3, 4]])
    train_output = _border(base, color=9, padding=1)
    test_input = _grid([[5, 6], [7, 8]])
    expected = _border(test_input, color=9, padding=1)
    return _task(
        f"{seed}:add_uniform_border:{variant}",
        family_label="add_uniform_border",
        primitive_chain=("add_uniform_border",),
        train_pairs=(({"input": base, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "add_uniform_border"},
    )


def _single_step_count_objects(seed: int, variant: str) -> dict[str, Any]:
    train_input = _grid([[0, 1, 0], [0, 0, 2], [0, 0, 0]])
    train_output = _grid([[7, 7]])
    test_input = _grid([[0, 5, 0], [0, 0, 6], [0, 0, 0]])
    expected = _grid([[7, 7]])
    return _task(
        f"{seed}:count_objects_to_line:{variant}",
        family_label="count_objects_to_line",
        primitive_chain=("count_objects_to_line",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "count_objects_to_line"},
    )


def _single_step_object_count_square(seed: int, variant: str) -> dict[str, Any]:
    train_input = _grid([[0, 1], [2, 0]])
    train_output = _grid([[3, 3], [3, 3]])
    test_input = _grid([[0, 4], [5, 0]])
    expected = _grid([[3, 3], [3, 3]])
    return _task(
        f"{seed}:object_count_to_square:{variant}",
        family_label="object_count_to_square",
        primitive_chain=("object_count_to_square",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "object_count_to_square"},
    )


def _single_step_select_largest(seed: int, variant: str) -> dict[str, Any]:
    train_input = _grid([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 2, 0, 0]])
    train_output = _grid([[1, 1], [1, 1]])
    test_input = _grid([[0, 0, 0, 0], [0, 3, 3, 0], [0, 3, 3, 0], [0, 4, 0, 0]])
    expected = _grid([[3, 3], [3, 3]])
    return _task(
        f"{seed}:select_largest_object:{variant}",
        family_label="select_largest_object",
        primitive_chain=("select_largest_object",),
        train_pairs=(({"input": train_input, "output": train_output}),),
        test_input=test_input,
        expected_output=expected,
        difficulty="easy",
        variant=variant,
        seed=seed,
        metadata={"kind": "single_step", "expected_behavior": "solve", "generator": "select_largest_object"},
    )


def _composition_crop_recolor(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]])
    recolored = _grid([[2, 2], [2, 2]])
    return _task(
        f"{seed}:crop_then_recolor:{variant}",
        family_label="crop_then_recolor",
        primitive_chain=("crop_foreground_bbox", "recolor_global"),
        train_pairs=(({"input": base, "output": recolored}),),
        test_input=base,
        expected_output=recolored,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "composition", "expected_behavior": "solve", "generator": "crop_then_recolor"},
    )


def _composition_crop_rotate(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[0, 0, 0, 0, 0], [0, 1, 0, 0, 0], [0, 1, 1, 0, 0], [0, 1, 0, 0, 0], [0, 0, 0, 0, 0]])
    rotated = _grid([[1, 1, 1], [0, 1, 0], [0, 0, 0]])
    transform = "rotate_object_90"
    if variant.endswith("180"):
        rotated = _grid([[0, 1, 0], [1, 1, 0], [0, 1, 0]])
        transform = "rotate_object_180"
    elif variant.endswith("horizontal"):
        rotated = _grid([[1, 0, 0], [1, 1, 0], [1, 0, 0]])
        transform = "reflect_object_horizontal"
    elif variant.endswith("vertical"):
        rotated = _grid([[0, 1, 0], [1, 1, 0], [0, 1, 0]])
        transform = "reflect_object_vertical"
    return _task(
        f"{seed}:crop_then_rotate_or_reflect:{variant}",
        family_label="crop_then_rotate_or_reflect",
        primitive_chain=("crop_foreground_bbox", transform),
        train_pairs=(({"input": base, "output": rotated}),),
        test_input=base,
        expected_output=rotated,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "composition", "expected_behavior": "solve", "generator": "crop_then_rotate_or_reflect"},
    )


def _composition_crop_tile(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[0, 0, 0, 0], [0, 1, 2, 0], [0, 3, 4, 0], [0, 0, 0, 0]])
    output = _tile([[1, 2], [3, 4]], 2, 2)
    return _task(
        f"{seed}:crop_then_tile:{variant}",
        family_label="crop_then_tile",
        primitive_chain=("crop_foreground_bbox", "tile_grid"),
        train_pairs=(({"input": base, "output": output}),),
        test_input=base,
        expected_output=output,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "composition", "expected_behavior": "solve", "generator": "crop_then_tile"},
    )


def _composition_recolor_border(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[1, 2], [3, 4]])
    output = _border(_recolor(base, {1: 5, 2: 6, 3: 7, 4: 8}), color=9, padding=1)
    return _task(
        f"{seed}:recolor_then_border:{variant}",
        family_label="recolor_then_border",
        primitive_chain=("recolor_global", "add_uniform_border"),
        train_pairs=(({"input": base, "output": output}),),
        test_input=base,
        expected_output=output,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "composition", "expected_behavior": "solve", "generator": "recolor_then_border"},
    )


def _composition_select_recolor(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 2, 0, 0]])
    output = _grid([[3, 3], [3, 3]])
    return _task(
        f"{seed}:select_then_recolor:{variant}",
        family_label="select_then_recolor",
        primitive_chain=("select_largest_object", "recolor_global"),
        train_pairs=(({"input": base, "output": output}),),
        test_input=base,
        expected_output=output,
        difficulty="medium",
        variant=variant,
        seed=seed,
        metadata={"kind": "composition", "expected_behavior": "solve", "generator": "select_then_recolor"},
    )


def _adversarial_inconsistent(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[0, 1, 0], [0, 1, 0], [0, 0, 0]])
    return _task(
        f"{seed}:inconsistent_train_examples:{variant}",
        family_label="inconsistent_train_examples",
        primitive_chain=("crop_foreground_bbox", "recolor_global"),
        train_pairs=(({"input": base, "output": [[1], [1]]}), ({"input": base, "output": [[2], [2]]})),
        test_input=base,
        expected_output=[[1], [1]],
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "adversarial", "expected_behavior": "reject", "adversarial_kind": "inconsistent_train_examples"},
    )


def _adversarial_ambiguous(seed: int, variant: str) -> dict[str, Any]:
    # Non-identity expected output: train maps cross to corners-only (ambiguous:
    # could be "invert cross", "fill corners", or "remove non-corner foreground").
    # Test uses a different color so color_role cannot trivially match.
    # Variant determines the test color (2..6), ensuring train (color 1) != test color.
    variant_idx = int(variant[1:]) if variant.startswith("v") and variant[1:].isdigit() else 0
    test_color = 2 + (variant_idx % 5)  # 2..6
    train_in = _grid([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    train_out = _grid([[1, 0, 1], [0, 0, 0], [1, 0, 1]])  # corners only
    test_in = _grid([[0, test_color, 0], [test_color, test_color, test_color], [0, test_color, 0]])
    expected = _grid([[test_color, 0, test_color], [0, 0, 0], [test_color, 0, test_color]])
    return _task(
        f"{seed}:ambiguous_multiple_rules:{variant}",
        family_label="ambiguous_multiple_rules",
        primitive_chain=("rotate_object_90", "reflect_object_horizontal"),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=expected,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "adversarial", "expected_behavior": "reject", "adversarial_kind": "ambiguous_multiple_rules"},
    )


def _adversarial_unsupported(seed: int, variant: str) -> dict[str, Any]:
    # Non-identity expected output: train maps 2x2 to 3x3 expansion (unsupported:
    # no existing solver primitive does arbitrary size expansion).
    # Test uses a different color so color_role cannot trivially match.
    variant_idx = int(variant[1:]) if variant.startswith("v") and variant[1:].isdigit() else 0
    test_color = 2 + (variant_idx % 5)  # 2..6
    train_in = _grid([[0, 1], [1, 0]])
    train_out = _grid([[0, 1, 1], [1, 1, 0], [1, 0, 0]])  # 3x3 from 2x2
    test_in = _grid([[0, test_color], [test_color, 0]])
    expected = _grid([[0, test_color, test_color], [test_color, test_color, 0], [test_color, 0, 0]])
    return _task(
        f"{seed}:unsupported_primitive_chain:{variant}",
        family_label="unsupported_primitive_chain",
        primitive_chain=("ghost_a", "ghost_b"),
        train_pairs=(({"input": train_in, "output": train_out}),),
        test_input=test_in,
        expected_output=expected,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "adversarial", "expected_behavior": "reject", "adversarial_kind": "unsupported_primitive_chain"},
    )


def _adversarial_near_match(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[1, 1], [1, 1]])
    wrong = _grid([[1, 1], [1, 0]])
    return _task(
        f"{seed}:near_match_one_cell:{variant}",
        family_label="near_match_one_cell",
        primitive_chain=("crop_foreground_bbox", "recolor_global"),
        train_pairs=(({"input": base, "output": wrong}),),
        test_input=base,
        expected_output=wrong,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "adversarial", "expected_behavior": "reject", "adversarial_kind": "near_match_one_cell"},
    )


def _adversarial_wrong_geometry(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    wrong = _grid([[1, 0, 0], [1, 1, 0], [1, 0, 0]])
    return _task(
        f"{seed}:same_palette_wrong_geometry:{variant}",
        family_label="same_palette_wrong_geometry",
        primitive_chain=("rotate_object_180",),
        train_pairs=(({"input": base, "output": wrong}),),
        test_input=base,
        expected_output=wrong,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "adversarial", "expected_behavior": "reject", "adversarial_kind": "same_palette_wrong_geometry"},
    )


def _adversarial_wrong_recolor(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[1, 1], [1, 1]])
    wrong = _grid([[2, 2], [2, 1]])
    return _task(
        f"{seed}:same_geometry_wrong_recolor:{variant}",
        family_label="same_geometry_wrong_recolor",
        primitive_chain=("recolor_global",),
        train_pairs=(({"input": base, "output": wrong}),),
        test_input=base,
        expected_output=wrong,
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "adversarial", "expected_behavior": "reject", "adversarial_kind": "same_geometry_wrong_recolor"},
    )


def _adversarial_count_tie(seed: int, variant: str) -> dict[str, Any]:
    base = _grid([[1, 2], [2, 1]])
    return _task(
        f"{seed}:count_tie_ambiguity:{variant}",
        family_label="count_tie_ambiguity",
        primitive_chain=("count_objects_to_line",),
        train_pairs=(({"input": base, "output": [[2, 2]]}),),
        test_input=base,
        expected_output=[[2, 2]],
        difficulty="hard",
        variant=variant,
        seed=seed,
        metadata={"kind": "adversarial", "expected_behavior": "reject", "adversarial_kind": "count_tie_ambiguity"},
    )


SINGLE_STEP_BUILDERS_V1 = {
    "crop_foreground_bbox": _single_step_crop_foreground,
    "crop_largest_object": _single_step_crop_largest,
    "translate_single_object": _single_step_translate,
    "rotate_object_90": lambda seed, variant: _single_step_rotate(seed, variant, 1),
    "rotate_object_180": lambda seed, variant: _single_step_rotate(seed, variant, 2),
    "reflect_object_horizontal": lambda seed, variant: _single_step_reflect(seed, variant, "horizontal"),
    "reflect_object_vertical": lambda seed, variant: _single_step_reflect(seed, variant, "vertical"),
    "recolor_foreground": _single_step_recolor_foreground,
    "swap_two_colors": _single_step_swap_two_colors,
    "tile_grid": _single_step_tile_grid,
    "scale_cells_integer": _single_step_scale_cells,
    "add_uniform_border": _single_step_border,
    "count_objects_to_line": _single_step_count_objects,
    "object_count_to_square": _single_step_object_count_square,
    "select_largest_object": _single_step_select_largest,
}

COMPOSITION_BUILDERS_V1 = {
    "crop_then_recolor": _composition_crop_recolor,
    "crop_then_rotate_or_reflect": _composition_crop_rotate,
    "crop_then_tile": _composition_crop_tile,
    "recolor_then_border": _composition_recolor_border,
    "select_then_recolor": _composition_select_recolor,
}

ADVERSARIAL_BUILDERS_V1 = {
    "inconsistent_train_examples": _adversarial_inconsistent,
    "ambiguous_multiple_rules": _adversarial_ambiguous,
    "unsupported_primitive_chain": _adversarial_unsupported,
    "near_match_one_cell": _adversarial_near_match,
    "same_palette_wrong_geometry": _adversarial_wrong_geometry,
    "same_geometry_wrong_recolor": _adversarial_wrong_recolor,
    "count_tie_ambiguity": _adversarial_count_tie,
}


def build_arc_synthetic_discovery_task_v1(
    family_label: str,
    *,
    seed: int,
    variant: str = "base",
    include_compositions: bool = True,
    include_adversarial: bool = True,
) -> dict[str, Any]:
    if family_label in SINGLE_STEP_BUILDERS_V1:
        return SINGLE_STEP_BUILDERS_V1[family_label](seed, variant)
    if include_compositions and family_label in COMPOSITION_BUILDERS_V1:
        return COMPOSITION_BUILDERS_V1[family_label](seed, variant)
    if include_adversarial and family_label in ADVERSARIAL_BUILDERS_V1:
        return ADVERSARIAL_BUILDERS_V1[family_label](seed, variant)
    raise ValueError(f"unsupported_family_label:{family_label}")


def build_arc_synthetic_discovery_task_corpus_v1(
    *,
    seed: int,
    tasks_per_family: int = 1,
    include_adversarial: bool = True,
    include_compositions: bool = True,
    max_grid_size: int = 6,
    min_train_pairs: int = 1,
    max_train_pairs: int = 2,
) -> list[dict[str, Any]]:
    if tasks_per_family <= 0:
        raise ValueError("tasks_per_family_must_be_positive")
    if max_grid_size < 2:
        raise ValueError("max_grid_size_too_small")
    if min_train_pairs <= 0 or max_train_pairs < min_train_pairs:
        raise ValueError("invalid_train_pair_bounds")
    corpus: list[dict[str, Any]] = []
    families: list[str] = list(SINGLE_STEP_FAMILY_ORDER_V1)
    if include_compositions:
        families.extend(COMPOSITION_FAMILY_ORDER_V1)
    if include_adversarial:
        families.extend(ADVERSARIAL_FAMILY_ORDER_V1)
    for family_index, family_label in enumerate(families):
        if family_label in COMPOSITION_BUILDERS_V1 and not include_compositions:
            continue
        if family_label in ADVERSARIAL_BUILDERS_V1 and not include_adversarial:
            continue
        for variant_index in range(tasks_per_family):
            variant = f"v{variant_index}"
            task_seed = seed + family_index * 101 + variant_index
            task = build_arc_synthetic_discovery_task_v1(
                family_label,
                seed=task_seed,
                variant=variant,
                include_compositions=include_compositions,
                include_adversarial=include_adversarial,
            )
            if max(len(task["test_input"]), len(task["test_input"][0])) > max_grid_size:
                raise ValueError("generated_grid_exceeds_max_grid_size")
            corpus.append(task)
    return corpus


def build_arc_synthetic_solver_packet_v1(task: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "train_pairs": [
            {"input": [list(row) for row in pair["input"]], "output": [list(row) for row in pair["output"]]}
            for pair in task.get("train_pairs", [])
        ],
        "test_input": [list(row) for row in task.get("test_input", [])],
    }


def summarize_synthetic_task_corpus_v1(tasks: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    family_counts: dict[str, int] = {}
    adversarial_counts: dict[str, int] = {}
    for task in tasks:
        family = str(task.get("family_label", ""))
        family_counts[family] = family_counts.get(family, 0) + 1
        metadata = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
        if str(metadata.get("kind", "")) == "adversarial":
            adversarial_counts[family] = adversarial_counts.get(family, 0) + 1
    return {
        "task_count": len(tasks),
        "family_counts": dict(sorted(family_counts.items())),
        "adversarial_counts": dict(sorted(adversarial_counts.items())),
    }


__all__ = [
    "ADVERSARIAL_FAMILY_ORDER_V1",
    "COMPOSITION_FAMILY_ORDER_V1",
    "SINGLE_STEP_FAMILY_ORDER_V1",
    "SUPPORTED_FAMILY_ORDER_V1",
    "SyntheticDiscoveryTaskV1",
    "build_arc_synthetic_discovery_task_corpus_v1",
    "build_arc_synthetic_discovery_task_v1",
    "build_arc_synthetic_solver_packet_v1",
    "summarize_synthetic_task_corpus_v1",
]
