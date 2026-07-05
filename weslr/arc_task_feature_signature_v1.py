"""ARC task feature signature extractor V1.

Synthetic-only, metadata-safe task summarization for ARC-style train pairs and
test inputs. This module produces compact signatures for grid, object, color,
shape, and relation structure without emitting raw grids or solution labels.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha1
from typing import Any, Iterable, Mapping, Sequence

from weslr.arc_object_extraction_v1 import extract_objects_v1, infer_background_value_v1, validate_grid_v1
from weslr.arc_shape_geometry_v1 import canonical_shape_signature_v1, reflect_object_mask_v1, rotate_object_mask_v1

SCHEMA_VERSION_V1 = "ArcTaskFeatureSignatureV1"

CANDIDATE_HINT_LABELS_V1 = (
    "possible_crop",
    "possible_translate",
    "possible_recolor",
    "possible_rotate_or_reflect",
    "possible_tile",
    "possible_scale",
    "possible_count_output",
    "possible_border",
)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _pair_input(pair: Mapping[str, Any]) -> Any:
    return pair.get("input", pair.get("input_grid"))


def _pair_output(pair: Mapping[str, Any]) -> Any:
    return pair.get("output", pair.get("output_grid"))


def _grid_dimensions(grid: Sequence[Sequence[int]]) -> tuple[int, int]:
    return len(grid), len(grid[0])


def _repeat_grid(grid: list[list[int]], repeat_rows: int, repeat_cols: int) -> list[list[int]]:
    return [
        [cell for cell in row for _ in range(repeat_cols)]
        for row in grid
        for _ in range(repeat_rows)
    ]


def _tile_grid(grid: list[list[int]], repeat_rows: int, repeat_cols: int) -> list[list[int]]:
    return [
        [grid[row % len(grid)][column % len(grid[0])] for column in range(len(grid[0]) * repeat_cols)]
        for row in range(len(grid) * repeat_rows)
    ]


def _hash_token(value: Any) -> str:
    return sha1(repr(value).encode("utf-8")).hexdigest()[:12]


def _listify_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def summarize_arc_grid_v1(grid: Any) -> dict[str, Any]:
    normalized = validate_grid_v1(grid)
    height, width = _grid_dimensions(normalized)
    histogram = Counter(cell for row in normalized for cell in row)
    background = infer_background_value_v1(normalized)
    palette = sorted(histogram)
    foreground_colors = sorted(color for color in histogram if color != background)
    foreground_cell_count = sum(count for color, count in histogram.items() if color != background)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "height": height,
        "width": width,
        "cell_count": height * width,
        "palette": palette,
        "color_histogram": {int(color): int(count) for color, count in sorted(histogram.items(), key=lambda item: item[0])},
        "inferred_background_color": background,
        "foreground_color_set": foreground_colors,
        "foreground_cell_count": foreground_cell_count,
        "empty_status": "non_empty",
        "is_empty": False,
        "is_non_empty": True,
    }


def _foreground_cells(normalized: Sequence[Sequence[int]], background: int) -> list[tuple[int, int]]:
    return [(row_index, column_index) for row_index, row in enumerate(normalized) for column_index, cell in enumerate(row) if cell != background]


def _foreground_bbox(cells: Sequence[tuple[int, int]]) -> list[int] | None:
    if not cells:
        return None
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    return [min(rows), min(columns), max(rows), max(columns)]


def summarize_arc_object_v1(grid: Any, *, background_value: int | None = None) -> dict[str, Any]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    extracted = extract_objects_v1(normalized, background_value=background)
    objects = extracted["objects"]
    object_count_by_color: dict[int, int] = {}
    bounding_boxes: list[list[int]] = []
    object_color_sets: list[list[int]] = []
    touch_flags: list[bool] = []
    object_sizes: list[int] = []
    foreground_cells: list[tuple[int, int]] = []
    for obj in objects:
        color = int(obj["color"])
        object_count_by_color[color] = object_count_by_color.get(color, 0) + 1
        bounding_boxes.append([int(value) for value in obj["bbox"]])
        object_color_sets.append([color])
        touch_flags.append(bool(obj["touches_boundary"]))
        object_sizes.append(int(obj["size"]))
        foreground_cells.extend((int(row), int(column)) for row, column in obj["cells"])
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "object_count": len(objects),
        "object_count_by_color": object_count_by_color,
        "largest_object_size": max(object_sizes) if object_sizes else None,
        "smallest_object_size": min(object_sizes) if object_sizes else None,
        "bounding_boxes": bounding_boxes,
        "object_color_sets": object_color_sets,
        "foreground_bbox": _foreground_bbox(foreground_cells),
        "objects_touch_border": any(touch_flags),
        "object_touch_border_flags": touch_flags,
        "single_object": len(objects) == 1,
        "multi_object": len(objects) > 1,
        "background_color": background,
    }


def _shape_symmetry_hints(canonical_shape: Sequence[Sequence[int]]) -> list[str]:
    cells = [tuple(int(value) for value in cell) for cell in canonical_shape]
    if not cells:
        return []
    hints: list[str] = []
    if canonical_shape_signature_v1(cells) == canonical_shape_signature_v1(reflect_object_mask_v1(cells, "horizontal")):
        hints.append("horizontal_reflect")
    if canonical_shape_signature_v1(cells) == canonical_shape_signature_v1(reflect_object_mask_v1(cells, "vertical")):
        hints.append("vertical_reflect")
    if canonical_shape_signature_v1(cells) == canonical_shape_signature_v1(rotate_object_mask_v1(cells, 2)):
        hints.append("rotational_180")
    if canonical_shape_signature_v1(cells) == canonical_shape_signature_v1(rotate_object_mask_v1(cells, 1)):
        hints.append("rotational_90")
    return hints


def _canonical_shape_to_token(canonical_shape: Sequence[Sequence[int]]) -> str:
    cells = [[int(row), int(column)] for row, column in canonical_shape]
    return f"shape:{len(cells)}:{_hash_token(cells)}"


def summarize_arc_shape_v1(grid: Any, *, background_value: int | None = None) -> dict[str, Any]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    shape_summaries: list[dict[str, Any]] = []
    for obj in objects:
        canonical_shape = canonical_shape_signature_v1(obj["cells"])
        shape_height = max((int(row) for row, _ in canonical_shape), default=-1) + 1
        shape_width = max((int(column) for _, column in canonical_shape), default=-1) + 1
        shape_summaries.append(
            {
                "object_id": obj["object_id"],
                "color": int(obj["color"]),
                "bbox": [int(value) for value in obj["bbox"]],
                "normalized_shape_height": shape_height,
                "normalized_shape_width": shape_width,
                "area": int(obj["size"]),
                "shape_token": _canonical_shape_to_token(canonical_shape),
                "symmetry_hints": _shape_symmetry_hints(canonical_shape),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "shape_count": len(shape_summaries),
        "object_shapes": shape_summaries,
        "shape_tokens": [shape_summary["shape_token"] for shape_summary in shape_summaries],
        "shape_token_set": sorted({shape_summary["shape_token"] for shape_summary in shape_summaries}),
    }


def _same_size_relation_labels(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> list[str]:
    input_height, input_width = _grid_dimensions(input_grid)
    output_height, output_width = _grid_dimensions(output_grid)
    labels = ["same_size"] if (input_height, input_width) == (output_height, output_width) else []
    if output_height > input_height or output_width > input_width:
        labels.append("output_larger")
    if output_height < input_height or output_width < input_width:
        labels.append("output_smaller")
    if (output_height != input_height) ^ (output_width != input_width):
        labels.append("mixed_size_change")
    return labels


def _palette_relation_labels(input_summary: Mapping[str, Any], output_summary: Mapping[str, Any]) -> list[str]:
    labels = ["palette_changed" if input_summary["palette"] != output_summary["palette"] else "palette_unchanged"]
    if input_summary["inferred_background_color"] != output_summary["inferred_background_color"]:
        labels.append("background_changed")
    return labels


def _count_relation_labels(name: str, input_value: int, output_value: int) -> list[str]:
    labels = [f"{name}_same" if input_value == output_value else f"{name}_changed"]
    if output_value > input_value:
        labels.append(f"{name}_increased")
    if output_value < input_value:
        labels.append(f"{name}_decreased")
    return labels


def _exact_scale_relation(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, int] | None:
    input_height, input_width = _grid_dimensions(input_grid)
    output_height, output_width = _grid_dimensions(output_grid)
    if input_height <= 0 or input_width <= 0:
        return None
    if output_height % input_height != 0 or output_width % input_width != 0:
        return None
    scale_rows = output_height // input_height
    scale_cols = output_width // input_width
    if scale_rows <= 1 and scale_cols <= 1:
        return None
    if _repeat_grid(_listify_grid(input_grid), scale_rows, scale_cols) == _listify_grid(output_grid):
        return {"scale_rows": scale_rows, "scale_cols": scale_cols}
    return None


def _exact_tile_relation(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, int] | None:
    input_height, input_width = _grid_dimensions(input_grid)
    output_height, output_width = _grid_dimensions(output_grid)
    if input_height <= 0 or input_width <= 0:
        return None
    if output_height % input_height != 0 or output_width % input_width != 0:
        return None
    repeat_rows = output_height // input_height
    repeat_cols = output_width // input_width
    if repeat_rows <= 1 and repeat_cols <= 1:
        return None
    if _tile_grid(_listify_grid(input_grid), repeat_rows, repeat_cols) == _listify_grid(output_grid):
        return {"repeat_rows": repeat_rows, "repeat_cols": repeat_cols}
    return None


def _exact_border_relation(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, int] | None:
    input_height, input_width = _grid_dimensions(input_grid)
    output_height, output_width = _grid_dimensions(output_grid)
    if output_height < input_height or output_width < input_width:
        return None
    pad_height = output_height - input_height
    pad_width = output_width - input_width
    if pad_height % 2 != 0 or pad_width % 2 != 0:
        return None
    top = bottom = pad_height // 2
    left = right = pad_width // 2
    if top == 0 and left == 0:
        return None
    background = output_grid[0][0]
    for row_index, row in enumerate(output_grid):
        for column_index, cell in enumerate(row):
            inside_row = top <= row_index < top + input_height
            inside_column = left <= column_index < left + input_width
            if inside_row and inside_column:
                if cell != input_grid[row_index - top][column_index - left]:
                    return None
            elif cell != background:
                return None
    return {"top": top, "bottom": bottom, "left": left, "right": right, "border_color": int(background)}


def _exact_recolor_relation(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> bool:
    input_height, input_width = _grid_dimensions(input_grid)
    output_height, output_width = _grid_dimensions(output_grid)
    if (input_height, input_width) != (output_height, output_width):
        return False
    input_summary = summarize_arc_object_v1(input_grid)
    output_summary = summarize_arc_object_v1(output_grid)
    if input_summary["object_count"] != output_summary["object_count"]:
        return False
    if input_summary["bounding_boxes"] != output_summary["bounding_boxes"]:
        return False
    input_shapes = summarize_arc_shape_v1(input_grid)["shape_tokens"]
    output_shapes = summarize_arc_shape_v1(output_grid)["shape_tokens"]
    return input_shapes == output_shapes and summarize_arc_grid_v1(input_grid)["foreground_color_set"] != summarize_arc_grid_v1(output_grid)["foreground_color_set"]


def _possible_rotate_or_reflect_relation(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> bool:
    input_summary = summarize_arc_object_v1(input_grid)
    output_summary = summarize_arc_object_v1(output_grid)
    if input_summary["object_count"] != 1 or output_summary["object_count"] != 1:
        return False
    input_objects = extract_objects_v1(validate_grid_v1(input_grid), background_value=input_summary["background_color"])["objects"]
    output_objects = extract_objects_v1(validate_grid_v1(output_grid), background_value=output_summary["background_color"])["objects"]
    input_cells = input_objects[0]["cells"]
    output_cells = output_objects[0]["cells"]
    input_canonical = canonical_shape_signature_v1(input_cells)
    output_canonical = canonical_shape_signature_v1(output_cells)
    if input_canonical == output_canonical:
        return False
    candidates = [
        rotate_object_mask_v1(input_cells, 1),
        rotate_object_mask_v1(input_cells, 2),
        rotate_object_mask_v1(input_cells, 3),
        reflect_object_mask_v1(input_cells, "horizontal"),
        reflect_object_mask_v1(input_cells, "vertical"),
    ]
    return any(canonical_shape_signature_v1(candidate) == output_canonical for candidate in candidates)


def _possible_translate_relation(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> bool:
    input_summary = summarize_arc_object_v1(input_grid)
    output_summary = summarize_arc_object_v1(output_grid)
    if input_summary["object_count"] != output_summary["object_count"]:
        return False
    if input_summary["object_count"] != 1:
        return False
    input_objects = extract_objects_v1(validate_grid_v1(input_grid), background_value=input_summary["background_color"])["objects"]
    output_objects = extract_objects_v1(validate_grid_v1(output_grid), background_value=output_summary["background_color"])["objects"]
    input_object = input_objects[0]
    output_object = output_objects[0]
    if canonical_shape_signature_v1(input_object["cells"]) != canonical_shape_signature_v1(output_object["cells"]):
        return False
    input_bbox = [int(value) for value in input_object["bbox"]]
    output_bbox = [int(value) for value in output_object["bbox"]]
    return (output_bbox[0] - input_bbox[0], output_bbox[1] - input_bbox[1]) != (0, 0)


def _possible_count_output_relation(input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]], input_object_summary: Mapping[str, Any], input_grid_summary: Mapping[str, Any]) -> bool:
    output_height, output_width = _grid_dimensions(output_grid)
    if not ((output_height == 1 or output_width == 1) and len({cell for row in output_grid for cell in row}) == 1):
        if not (output_height == output_width and len({cell for row in output_grid for cell in row}) == 1):
            return False
    count_targets = {
        int(input_object_summary["object_count"]),
        int(input_grid_summary["foreground_cell_count"]),
        int(input_grid_summary["cell_count"]),
    }
    if output_height == 1 or output_width == 1:
        return output_height * output_width in count_targets
    if output_height == output_width:
        return output_height * output_width in count_targets
    return False


def _pair_relation_signature_v1(pair: Mapping[str, Any]) -> dict[str, Any]:
    input_grid = validate_grid_v1(_pair_input(pair))
    output_grid = validate_grid_v1(_pair_output(pair))
    input_grid_summary = summarize_arc_grid_v1(input_grid)
    output_grid_summary = summarize_arc_grid_v1(output_grid)
    input_object_summary = summarize_arc_object_v1(input_grid)
    output_object_summary = summarize_arc_object_v1(output_grid)
    input_shape_summary = summarize_arc_shape_v1(input_grid)
    output_shape_summary = summarize_arc_shape_v1(output_grid)

    size_labels = _same_size_relation_labels(input_grid, output_grid)
    palette_labels = _palette_relation_labels(input_grid_summary, output_grid_summary)
    object_count_labels = _count_relation_labels("object_count", int(input_object_summary["object_count"]), int(output_object_summary["object_count"]))
    foreground_count_labels = _count_relation_labels("foreground_count", int(input_grid_summary["foreground_cell_count"]), int(output_grid_summary["foreground_cell_count"]))

    hint_labels: set[str] = set()
    if int(output_grid_summary["cell_count"]) < int(input_grid_summary["cell_count"]):
        hint_labels.add("possible_crop")
    if _possible_translate_relation(input_grid, output_grid):
        hint_labels.add("possible_translate")
    if _exact_recolor_relation(input_grid, output_grid):
        hint_labels.add("possible_recolor")
    if _possible_rotate_or_reflect_relation(input_grid, output_grid):
        hint_labels.add("possible_rotate_or_reflect")
    if _exact_tile_relation(input_grid, output_grid):
        hint_labels.add("possible_tile")
    scale_relation = _exact_scale_relation(input_grid, output_grid)
    if scale_relation is not None:
        hint_labels.add("possible_scale")
    if _possible_count_output_relation(input_grid, output_grid, input_object_summary, input_grid_summary):
        hint_labels.add("possible_count_output")
    if _exact_border_relation(input_grid, output_grid) is not None:
        hint_labels.add("possible_border")

    size_relation: dict[str, Any] = {
        "input_size": [int(input_grid_summary["height"]), int(input_grid_summary["width"])],
        "output_size": [int(output_grid_summary["height"]), int(output_grid_summary["width"])],
        "same_size": (input_grid_summary["height"], input_grid_summary["width"]) == (output_grid_summary["height"], output_grid_summary["width"]),
        "output_size_relation": (
            "same"
            if (input_grid_summary["height"], input_grid_summary["width"]) == (output_grid_summary["height"], output_grid_summary["width"])
            else "larger"
            if output_grid_summary["height"] >= input_grid_summary["height"] and output_grid_summary["width"] >= input_grid_summary["width"]
            else "smaller"
        ),
        "integer_scale_relation": scale_relation,
        "crop_like_relation_hint": "possible_crop" in hint_labels,
        "tile_like_relation_hint": "possible_tile" in hint_labels,
        "palette_changed": input_grid_summary["palette"] != output_grid_summary["palette"],
        "foreground_count_changed": input_grid_summary["foreground_cell_count"] != output_grid_summary["foreground_cell_count"],
        "object_count_changed": input_object_summary["object_count"] != output_object_summary["object_count"],
        "candidate_primitive_hint_labels": sorted(hint_labels),
    }
    size_relation["relation_labels"] = sorted(set(size_labels + palette_labels + object_count_labels + foreground_count_labels + size_relation["candidate_primitive_hint_labels"]))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "input_grid_summary": input_grid_summary,
        "output_grid_summary": output_grid_summary,
        "input_object_summary": input_object_summary,
        "output_object_summary": output_object_summary,
        "input_shape_summary": input_shape_summary,
        "output_shape_summary": output_shape_summary,
        "size_relation": size_relation,
        "size_relation_labels": size_labels,
        "palette_relation_labels": palette_labels,
        "object_count_relation_labels": object_count_labels,
        "foreground_count_relation_labels": foreground_count_labels,
    }


def _common_labels(label_lists: Sequence[Sequence[str]]) -> list[str]:
    if not label_lists:
        return []
    common = set(label_lists[0])
    for labels in label_lists[1:]:
        common &= set(labels)
    return sorted(common)


def _contradiction_labels(pair_signatures: Sequence[Mapping[str, Any]]) -> list[str]:
    contradictions: list[str] = []
    if len({signature["size_relation"]["output_size_relation"] for signature in pair_signatures}) > 1:
        contradictions.append("size_relation_disagreement")
    if len({signature["size_relation"]["palette_changed"] for signature in pair_signatures}) > 1:
        contradictions.append("palette_relation_disagreement")
    if len({signature["size_relation"]["object_count_changed"] for signature in pair_signatures}) > 1:
        contradictions.append("object_count_relation_disagreement")
    if len({signature["size_relation"]["foreground_count_changed"] for signature in pair_signatures}) > 1:
        contradictions.append("foreground_count_relation_disagreement")
    if len({tuple(signature["size_relation"]["candidate_primitive_hint_labels"]) for signature in pair_signatures}) > 1:
        contradictions.append("primitive_hint_disagreement")
    return contradictions


def build_arc_task_feature_signature_v1(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> dict[str, Any]:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        raise ValueError("empty_train_pairs")
    train_pair_signatures = []
    for index, pair in enumerate(train_pairs):
        pair_signature = _pair_relation_signature_v1(pair)
        pair_signature["pair_index"] = index
        train_pair_signatures.append(pair_signature)

    task_level_signature = {
        "schema_version": SCHEMA_VERSION_V1,
        "train_pair_count": len(train_pair_signatures),
        "consistent_size_relation_labels": _common_labels([signature["size_relation_labels"] for signature in train_pair_signatures]),
        "consistent_palette_relation_labels": _common_labels([signature["palette_relation_labels"] for signature in train_pair_signatures]),
        "consistent_object_count_relation_labels": _common_labels([signature["object_count_relation_labels"] for signature in train_pair_signatures]),
        "consistent_foreground_count_relation_labels": _common_labels([signature["foreground_count_relation_labels"] for signature in train_pair_signatures]),
        "possible_primitive_hint_intersection": sorted(set.intersection(*(set(signature["size_relation"]["candidate_primitive_hint_labels"]) for signature in train_pair_signatures))) if train_pair_signatures else [],
        "contradiction_labels": _contradiction_labels(train_pair_signatures),
    }

    test_grid_summary = summarize_arc_grid_v1(test_input)
    test_object_summary = summarize_arc_object_v1(test_input)
    test_shape_summary = summarize_arc_shape_v1(test_input)
    test_input_signature = {
        "schema_version": SCHEMA_VERSION_V1,
        "grid_summary": test_grid_summary,
        "object_summary": test_object_summary,
        "shape_summary": test_shape_summary,
    }

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "train_pair_count": len(train_pair_signatures),
        "train_pair_signatures": train_pair_signatures,
        "task_level_signature": task_level_signature,
        "test_input_signature": test_input_signature,
        "trace": {
            "synthetic_only": True,
            "metadata_safe": True,
            "no_public_arc_data_used": True,
        },
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "build_arc_task_feature_signature_v1",
    "summarize_arc_grid_v1",
    "summarize_arc_object_v1",
    "summarize_arc_shape_v1",
]
