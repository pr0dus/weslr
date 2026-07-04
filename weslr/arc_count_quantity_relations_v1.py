"""ARC count / quantity relations capability V1.

Synthetic-only counting and quantity reasoning for ARC-style tasks.
This module infers small exact train-consistent families that map counts to
line length, square size, selected color masks, or largest-object crops.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from weslr.arc_hypothesis_engine_v1 import HypothesisCandidate, rank_hypotheses, score_train_consistency
from weslr.arc_object_extraction_v1 import (
    crop_selected_color_object_v1,
    crop_to_largest_object_bbox_v1,
    extract_objects_v1,
    infer_background_value_v1,
    validate_grid_v1,
)

SCHEMA_VERSION_V1 = "ArcCountQuantityRelationsV1"

COUNT_QUANTITY_FAMILY_ORDER_V1 = {
    "object_count_to_line": 0,
    "foreground_cell_count_to_line": 1,
    "unique_color_count_to_line": 2,
    "object_count_to_square": 3,
    "select_most_frequent_foreground_color": 4,
    "select_largest_object": 5,
}


@dataclass(frozen=True)
class CountQuantityRuleV1:
    family: str
    params: dict[str, Any]
    role_summary: dict[str, Any]


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


def infer_background_value_strict_v1(grid: Any) -> int:
    normalized = validate_grid_v1(grid)
    counts = Counter(cell for row in normalized for cell in row)
    if not counts:
        raise ValueError("empty_grid")
    most_common = counts.most_common()
    if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
        raise ValueError("ambiguous_background")
    return int(most_common[0][0])


def grid_height_v1(grid: Any) -> int:
    return len(validate_grid_v1(grid))


def grid_width_v1(grid: Any) -> int:
    return len(validate_grid_v1(grid)[0])


def count_color_histogram_v1(grid: Any) -> dict[int, int]:
    normalized = validate_grid_v1(grid)
    return dict(Counter(cell for row in normalized for cell in row))


def count_foreground_cells_v1(grid: Any, *, background_value: int | None = None) -> int:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    return sum(1 for row in normalized for cell in row if cell != background)


def count_connected_components_v1(grid: Any, *, background_value: int | None = None) -> int:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    return len(extract_objects_v1(normalized, background_value=background)["objects"])


def count_foreground_objects_v1(grid: Any, *, background_value: int | None = None) -> int:
    return count_connected_components_v1(grid, background_value=background_value)


def count_objects_by_color_v1(grid: Any, *, background_value: int | None = None) -> dict[int, int]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    counts: dict[int, int] = {}
    for obj in objects:
        color = int(obj["color"])
        counts[color] = counts.get(color, 0) + 1
    return counts


def count_unique_foreground_colors_v1(grid: Any, *, background_value: int | None = None) -> int:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    return len({cell for row in normalized for cell in row if cell != background})


def count_row_foreground_counts_v1(grid: Any, *, background_value: int | None = None) -> list[int]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    return [sum(1 for cell in row if cell != background) for row in normalized]


def count_column_foreground_counts_v1(grid: Any, *, background_value: int | None = None) -> list[int]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    return [sum(1 for row in normalized if row[column] != background) for column in range(len(normalized[0]))]


def largest_object_size_v1(grid: Any, *, background_value: int | None = None) -> int | None:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    if not objects:
        return None
    return max(int(obj["size"]) for obj in objects)


def smallest_object_size_v1(grid: Any, *, background_value: int | None = None) -> int | None:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized) if background_value is None else int(background_value)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    if not objects:
        return None
    return min(int(obj["size"]) for obj in objects)


def count_quantity_summary_v1(grid: Any) -> dict[str, Any]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_strict_v1(normalized)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    foreground_cells = count_foreground_cells_v1(normalized, background_value=background)
    object_sizes = [int(obj["size"]) for obj in objects]
    foreground_colors = sorted({int(cell) for row in normalized for cell in row if cell != background})
    return {
        "background_color": background,
        "histogram": count_color_histogram_v1(normalized),
        "foreground_cell_count": foreground_cells,
        "foreground_object_count": len(objects),
        "connected_component_count": len(objects),
        "unique_foreground_color_count": len(foreground_colors),
        "foreground_colors": foreground_colors,
        "object_count_by_color": count_objects_by_color_v1(normalized, background_value=background),
        "row_foreground_counts": count_row_foreground_counts_v1(normalized, background_value=background),
        "column_foreground_counts": count_column_foreground_counts_v1(normalized, background_value=background),
        "largest_object_size": max(object_sizes) if object_sizes else None,
        "smallest_object_size": min(object_sizes) if object_sizes else None,
        "object_sizes": object_sizes,
    }


def _line_grid(length: int, color: int, *, horizontal: bool) -> list[list[int]]:
    if length <= 0:
        raise ValueError("invalid_line_length")
    if horizontal:
        return [[color for _ in range(length)]]
    return [[color] for _ in range(length)]


def _filled_square(size: int, color: int) -> list[list[int]]:
    if size <= 0:
        raise ValueError("invalid_square_size")
    return [[color for _ in range(size)] for _ in range(size)]


def _mask_color(grid: list[list[int]], color: int, background: int) -> list[list[int]]:
    return [[color if cell == color else background for cell in row] for row in grid]


def _pair_orientation(output_grid: list[list[int]]) -> str:
    if len(output_grid) == 1:
        return "horizontal"
    if len(output_grid[0]) == 1:
        return "vertical"
    raise ValueError("output_not_line")


def _pair_single_color(output_grid: list[list[int]]) -> int:
    colors = {cell for row in output_grid for cell in row}
    if len(colors) != 1:
        raise ValueError("output_not_single_color")
    return next(iter(colors))


def _infer_object_count_to_line_rule(train_pairs: Sequence[Mapping[str, Any]]) -> CountQuantityRuleV1 | None:
    orientation: str | None = None
    line_color: int | None = None
    count_summary: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            background = infer_background_value_strict_v1(input_grid)
        except Exception:
            return None
        objects = extract_objects_v1(input_grid, background_value=background)["objects"]
        if not objects:
            return None
        try:
            output_orientation = _pair_orientation(output_grid)
            output_color = _pair_single_color(output_grid)
        except Exception:
            return None
        if orientation is None:
            orientation = output_orientation
        elif orientation != output_orientation:
            return None
        if line_color is None:
            line_color = output_color
        elif line_color != output_color:
            return None
        count = len(objects)
        expected = _line_grid(count, output_color, horizontal=orientation == "horizontal")
        if expected != output_grid:
            return None
        count_summary.append({"object_count": count, "orientation": output_orientation, "line_color": output_color})
    if orientation is None or line_color is None:
        return None
    return CountQuantityRuleV1(
        family="object_count_to_line",
        params={"orientation": orientation, "line_color": line_color},
        role_summary={"rule": "object_count_to_line", "pair_count": len(train_pairs), "orientation": orientation, "line_color": line_color, "pair_summaries": count_summary},
    )


def _infer_foreground_cell_count_to_line_rule(train_pairs: Sequence[Mapping[str, Any]]) -> CountQuantityRuleV1 | None:
    orientation: str | None = None
    line_color: int | None = None
    count_summary: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            background = infer_background_value_strict_v1(input_grid)
        except Exception:
            return None
        try:
            output_orientation = _pair_orientation(output_grid)
            output_color = _pair_single_color(output_grid)
        except Exception:
            return None
        if orientation is None:
            orientation = output_orientation
        elif orientation != output_orientation:
            return None
        if line_color is None:
            line_color = output_color
        elif line_color != output_color:
            return None
        count = count_foreground_cells_v1(input_grid, background_value=background)
        expected = _line_grid(count, output_color, horizontal=orientation == "horizontal")
        if expected != output_grid:
            return None
        count_summary.append({"foreground_cell_count": count, "orientation": output_orientation, "line_color": output_color})
    if orientation is None or line_color is None:
        return None
    return CountQuantityRuleV1(
        family="foreground_cell_count_to_line",
        params={"orientation": orientation, "line_color": line_color},
        role_summary={"rule": "foreground_cell_count_to_line", "pair_count": len(train_pairs), "orientation": orientation, "line_color": line_color, "pair_summaries": count_summary},
    )


def _infer_unique_color_count_to_line_rule(train_pairs: Sequence[Mapping[str, Any]]) -> CountQuantityRuleV1 | None:
    orientation: str | None = None
    line_color: int | None = None
    count_summary: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            background = infer_background_value_strict_v1(input_grid)
        except Exception:
            return None
        try:
            output_orientation = _pair_orientation(output_grid)
            output_color = _pair_single_color(output_grid)
        except Exception:
            return None
        if orientation is None:
            orientation = output_orientation
        elif orientation != output_orientation:
            return None
        if line_color is None:
            line_color = output_color
        elif line_color != output_color:
            return None
        count = count_unique_foreground_colors_v1(input_grid, background_value=background)
        expected = _line_grid(count, output_color, horizontal=orientation == "horizontal")
        if expected != output_grid:
            return None
        count_summary.append({"unique_foreground_color_count": count, "orientation": output_orientation, "line_color": output_color})
    if orientation is None or line_color is None:
        return None
    return CountQuantityRuleV1(
        family="unique_color_count_to_line",
        params={"orientation": orientation, "line_color": line_color},
        role_summary={"rule": "unique_color_count_to_line", "pair_count": len(train_pairs), "orientation": orientation, "line_color": line_color, "pair_summaries": count_summary},
    )


def _infer_object_count_to_square_rule(train_pairs: Sequence[Mapping[str, Any]]) -> CountQuantityRuleV1 | None:
    fill_color: int | None = None
    count_summary: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            background = infer_background_value_strict_v1(input_grid)
        except Exception:
            return None
        objects = extract_objects_v1(input_grid, background_value=background)["objects"]
        count = len(objects)
        if count <= 0 or len(output_grid) != count or len(output_grid[0]) != count:
            return None
        output_colors = {cell for row in output_grid for cell in row}
        if len(output_colors) != 1:
            return None
        output_color = next(iter(output_colors))
        if fill_color is None:
            fill_color = output_color
        elif fill_color != output_color:
            return None
        expected = _filled_square(count, output_color)
        if expected != output_grid:
            return None
        count_summary.append({"object_count": count, "square_size": count, "fill_color": output_color})
    if fill_color is None:
        return None
    return CountQuantityRuleV1(
        family="object_count_to_square",
        params={"fill_color": fill_color},
        role_summary={"rule": "object_count_to_square", "pair_count": len(train_pairs), "fill_color": fill_color, "pair_summaries": count_summary},
    )


def _infer_select_most_frequent_foreground_color_rule(train_pairs: Sequence[Mapping[str, Any]]) -> CountQuantityRuleV1 | None:
    selected_color: int | None = None
    output_mode: str | None = None
    count_summary: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            background = infer_background_value_strict_v1(input_grid)
        except Exception:
            return None
        histogram = Counter(cell for row in input_grid for cell in row if cell != background)
        if not histogram:
            return None
        counts = histogram.most_common()
        if len(counts) > 1 and counts[0][1] == counts[1][1]:
            return None
        pair_color = int(counts[0][0])
        if selected_color is None:
            selected_color = pair_color
        elif selected_color != pair_color:
            return None
        mask = _mask_color(input_grid, pair_color, background)
        if mask == output_grid:
            pair_mode = "mask"
        else:
            try:
                selected_objects = [obj for obj in extract_objects_v1(input_grid, background_value=background)["objects"] if int(obj["color"]) == pair_color]
                if len(selected_objects) != 1:
                    return None
                pair_mode = "crop"
                mask = crop_selected_color_object_v1(input_grid, color=pair_color, background_value=background)
            except Exception:
                return None
            if mask != output_grid:
                return None
        if output_mode is None:
            output_mode = pair_mode
        elif output_mode != pair_mode:
            return None
        count_summary.append({"selected_color": pair_color, "output_mode": pair_mode})
    if selected_color is None or output_mode is None:
        return None
    return CountQuantityRuleV1(
        family="select_most_frequent_foreground_color",
        params={"selected_color": selected_color, "output_mode": output_mode},
        role_summary={"rule": "select_most_frequent_foreground_color", "pair_count": len(train_pairs), "selected_color": selected_color, "output_mode": output_mode, "pair_summaries": count_summary},
    )


def _infer_select_largest_object_rule(train_pairs: Sequence[Mapping[str, Any]]) -> CountQuantityRuleV1 | None:
    selected_size: int | None = None
    count_summary: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            background = infer_background_value_strict_v1(input_grid)
        except Exception:
            return None
        objects = extract_objects_v1(input_grid, background_value=background)["objects"]
        if not objects:
            return None
        largest_size = max(int(obj["size"]) for obj in objects)
        largest = [obj for obj in objects if int(obj["size"]) == largest_size]
        if len(largest) != 1:
            return None
        if selected_size is None:
            selected_size = largest_size
        elif selected_size != largest_size:
            return None
        try:
            predicted = crop_to_largest_object_bbox_v1(input_grid, background_value=background)
        except Exception:
            return None
        if predicted != output_grid:
            return None
        count_summary.append({"largest_object_size": largest_size, "crop_size": [len(output_grid), len(output_grid[0])]})
    if selected_size is None:
        return None
    return CountQuantityRuleV1(
        family="select_largest_object",
        params={"largest_object_size": selected_size},
        role_summary={"rule": "select_largest_object", "pair_count": len(train_pairs), "largest_object_size": selected_size, "pair_summaries": count_summary},
    )


def _build_executor(rule: CountQuantityRuleV1):
    def executor(pair: Mapping[str, Any]) -> Any:
        input_grid = validate_grid_v1(_pair_input(pair))
        background = infer_background_value_strict_v1(input_grid)
        if rule.family == "object_count_to_line":
            objects = extract_objects_v1(input_grid, background_value=background)["objects"]
            return _line_grid(len(objects), int(rule.params["line_color"]), horizontal=rule.params["orientation"] == "horizontal")
        if rule.family == "foreground_cell_count_to_line":
            count = count_foreground_cells_v1(input_grid, background_value=background)
            return _line_grid(count, int(rule.params["line_color"]), horizontal=rule.params["orientation"] == "horizontal")
        if rule.family == "unique_color_count_to_line":
            count = count_unique_foreground_colors_v1(input_grid, background_value=background)
            return _line_grid(count, int(rule.params["line_color"]), horizontal=rule.params["orientation"] == "horizontal")
        if rule.family == "object_count_to_square":
            objects = extract_objects_v1(input_grid, background_value=background)["objects"]
            return _filled_square(len(objects), int(rule.params["fill_color"]))
        if rule.family == "select_most_frequent_foreground_color":
            color = int(rule.params["selected_color"])
            mode = _safe_text(rule.params.get("output_mode"), "mask")
            if mode == "crop":
                return crop_selected_color_object_v1(input_grid, color=color, background_value=background)
            return _mask_color(input_grid, color, background)
        if rule.family == "select_largest_object":
            return crop_to_largest_object_bbox_v1(input_grid, background_value=background)
        raise ValueError("unsupported_family")

    return executor


def infer_count_quantity_hypotheses_v1(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[HypothesisCandidate]:
    rule_builders = [
        _infer_object_count_to_line_rule,
        _infer_foreground_cell_count_to_line_rule,
        _infer_unique_color_count_to_line_rule,
        _infer_object_count_to_square_rule,
        _infer_select_most_frequent_foreground_color_rule,
        _infer_select_largest_object_rule,
    ]
    candidates: list[HypothesisCandidate] = []
    for builder in rule_builders:
        rule = builder(train_pairs)
        if rule is None:
            continue
        confidence = 1.0 - (COUNT_QUANTITY_FAMILY_ORDER_V1.get(rule.family, 99) * 0.01)
        scored = score_train_consistency(
            train_pairs,
            _build_executor(rule),
            family=rule.family,
            confidence=confidence,
            candidate_id=f"count_quantity:{rule.family}",
            trace={"schema_version": SCHEMA_VERSION_V1, "family": rule.family, "role_summary": deepcopy(rule.role_summary), "synthetic_only": True},
        )
        if not scored.train_fit:
            continue
        predicted = _build_executor(rule)({"input": test_input})
        candidates.append(
            HypothesisCandidate(
                family=rule.family,
                confidence=confidence,
                output=predicted,
                trace=scored.trace,
                train_fit=True,
                rejection_reason=None,
                candidate_id=f"count_quantity:{rule.family}",
            )
        )
    return rank_hypotheses(candidates)


def solve_count_quantity_task(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[dict[str, Any]]:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        return []
    ranked = infer_count_quantity_hypotheses_v1(train_pairs, test_input)
    return [candidate.to_dict() for candidate in ranked]


__all__ = [
    "COUNT_QUANTITY_FAMILY_ORDER_V1",
    "CountQuantityRuleV1",
    "count_color_histogram_v1",
    "count_column_foreground_counts_v1",
    "count_connected_components_v1",
    "count_foreground_cells_v1",
    "count_foreground_objects_v1",
    "count_objects_by_color_v1",
    "count_quantity_summary_v1",
    "count_row_foreground_counts_v1",
    "count_unique_foreground_colors_v1",
    "grid_height_v1",
    "grid_width_v1",
    "infer_background_value_strict_v1",
    "infer_count_quantity_hypotheses_v1",
    "largest_object_size_v1",
    "smallest_object_size_v1",
    "solve_count_quantity_task",
]
