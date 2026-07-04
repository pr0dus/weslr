"""ARC resize / tile / canvas-pattern capability V1.

Synthetic-only size/repetition/canvas reasoning for ARC-style tasks.
The module infers small exact train-consistent transformation families and
executes them on the test input.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from weslr.arc_hypothesis_engine_v1 import HypothesisCandidate, rank_hypotheses, score_train_consistency
from weslr.arc_object_extraction_v1 import crop_to_foreground_bbox_v1, extract_objects_v1, infer_background_value_v1, validate_grid_v1

SCHEMA_VERSION_V1 = "ArcResizeTileCanvasV1"

RESIZE_TILE_FAMILY_ORDER_V1 = {
    "crop_foreground_bbox": 0,
    "tile_repeat": 1,
    "integer_scale": 2,
    "border_padding": 3,
    "crop_then_tile": 4,
}


@dataclass(frozen=True)
class ResizeTileRuleV1:
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


def grid_dimensions_v1(grid: Any) -> tuple[int, int]:
    normalized = validate_grid_v1(grid)
    return len(normalized), len(normalized[0])


def output_size_relation_v1(input_grid: Any, output_grid: Any) -> dict[str, Any]:
    in_h, in_w = grid_dimensions_v1(input_grid)
    out_h, out_w = grid_dimensions_v1(output_grid)
    return {
        "input_height": in_h,
        "input_width": in_w,
        "output_height": out_h,
        "output_width": out_w,
        "height_ratio": out_h / in_h,
        "width_ratio": out_w / in_w,
    }


def _repeat_grid(grid: list[list[int]], repeat_rows: int, repeat_cols: int) -> list[list[int]]:
    out: list[list[int]] = []
    for row in grid:
        expanded_row: list[int] = []
        for cell in row:
            expanded_row.extend([cell] * repeat_cols)
        for _ in range(repeat_rows):
            out.append(list(expanded_row))
    return out


def _tile_grid(grid: list[list[int]], repeat_rows: int, repeat_cols: int) -> list[list[int]]:
    if repeat_rows <= 0 or repeat_cols <= 0:
        raise ValueError("invalid_repeat_factor")
    return [
        [grid[r % len(grid)][c % len(grid[0])] for c in range(len(grid[0]) * repeat_cols)]
        for r in range(len(grid) * repeat_rows)
    ]


def _scale_grid(grid: list[list[int]], scale_rows: int, scale_cols: int) -> list[list[int]]:
    if scale_rows <= 0 or scale_cols <= 0:
        raise ValueError("invalid_scale_factor")
    return _repeat_grid(grid, scale_rows, scale_cols)


def _pad_grid(grid: list[list[int]], top: int, bottom: int, left: int, right: int, border_color: int) -> list[list[int]]:
    inner_w = len(grid[0]) if grid else 0
    padded_width = inner_w + left + right
    out: list[list[int]] = []
    for _ in range(top):
        out.append([border_color] * padded_width)
    for row in grid:
        out.append([border_color] * left + list(row) + [border_color] * right)
    for _ in range(bottom):
        out.append([border_color] * padded_width)
    return out


def _pair_input(pair: Mapping[str, Any]) -> Any:
    return pair.get("input", pair.get("input_grid"))


def _pair_output(pair: Mapping[str, Any]) -> Any:
    return pair.get("output", pair.get("output_grid"))


def _all_cells_same(grid: list[list[int]], value: int) -> bool:
    return all(cell == value for row in grid for cell in row)


def _is_integer_ratio(numerator: int, denominator: int) -> bool:
    return denominator > 0 and numerator > 0 and numerator % denominator == 0


def _infer_crop_foreground_rule(train_pairs: Sequence[Mapping[str, Any]]) -> ResizeTileRuleV1 | None:
    summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            cropped = crop_to_foreground_bbox_v1(input_grid)
        except Exception:
            return None
        if cropped != output_grid:
            return None
        summaries.append({"input_size": [len(input_grid), len(input_grid[0])], "output_size": [len(output_grid), len(output_grid[0])]})
    return ResizeTileRuleV1(
        family="crop_foreground_bbox",
        params={},
        role_summary={"rule": "crop_foreground_bbox", "pair_count": len(train_pairs), "sizes": summaries},
    )


def _infer_tile_repeat_rule(train_pairs: Sequence[Mapping[str, Any]]) -> ResizeTileRuleV1 | None:
    repeat_rows: int | None = None
    repeat_cols: int | None = None
    summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        in_h, in_w = len(input_grid), len(input_grid[0])
        out_h, out_w = len(output_grid), len(output_grid[0])
        if not _is_integer_ratio(out_h, in_h) or not _is_integer_ratio(out_w, in_w):
            return None
        pair_repeat_rows = out_h // in_h
        pair_repeat_cols = out_w // in_w
        if repeat_rows is None:
            repeat_rows = pair_repeat_rows
        elif repeat_rows != pair_repeat_rows:
            return None
        if repeat_cols is None:
            repeat_cols = pair_repeat_cols
        elif repeat_cols != pair_repeat_cols:
            return None
        if _tile_grid(input_grid, pair_repeat_rows, pair_repeat_cols) != output_grid:
            return None
        summaries.append({"repeat_rows": pair_repeat_rows, "repeat_cols": pair_repeat_cols})
    if repeat_rows is None or repeat_cols is None:
        return None
    return ResizeTileRuleV1(
        family="tile_repeat",
        params={"repeat_rows": repeat_rows, "repeat_cols": repeat_cols},
        role_summary={"rule": "tile_repeat", "pair_count": len(train_pairs), "repeat_rows": repeat_rows, "repeat_cols": repeat_cols, "pair_summaries": summaries},
    )


def _infer_integer_scale_rule(train_pairs: Sequence[Mapping[str, Any]]) -> ResizeTileRuleV1 | None:
    scale_rows: int | None = None
    scale_cols: int | None = None
    summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        in_h, in_w = len(input_grid), len(input_grid[0])
        out_h, out_w = len(output_grid), len(output_grid[0])
        if not _is_integer_ratio(out_h, in_h) or not _is_integer_ratio(out_w, in_w):
            return None
        pair_scale_rows = out_h // in_h
        pair_scale_cols = out_w // in_w
        if scale_rows is None:
            scale_rows = pair_scale_rows
        elif scale_rows != pair_scale_rows:
            return None
        if scale_cols is None:
            scale_cols = pair_scale_cols
        elif scale_cols != pair_scale_cols:
            return None
        if _repeat_grid(input_grid, pair_scale_rows, pair_scale_cols) != output_grid:
            return None
        summaries.append({"scale_rows": pair_scale_rows, "scale_cols": pair_scale_cols})
    if scale_rows is None or scale_cols is None:
        return None
    return ResizeTileRuleV1(
        family="integer_scale",
        params={"scale_rows": scale_rows, "scale_cols": scale_cols},
        role_summary={"rule": "integer_scale", "pair_count": len(train_pairs), "scale_rows": scale_rows, "scale_cols": scale_cols, "pair_summaries": summaries},
    )


def _infer_border_padding_rule(train_pairs: Sequence[Mapping[str, Any]]) -> ResizeTileRuleV1 | None:
    top: int | None = None
    bottom: int | None = None
    left: int | None = None
    right: int | None = None
    border_color: int | None = None
    summaries: list[dict[str, Any]] = []
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        in_h, in_w = len(input_grid), len(input_grid[0])
        out_h, out_w = len(output_grid), len(output_grid[0])
        if out_h < in_h or out_w < in_w:
            return None
        pad_h = out_h - in_h
        pad_w = out_w - in_w
        if pad_h % 2 != 0 or pad_w % 2 != 0:
            return None
        pair_top = pair_bottom = pad_h // 2
        pair_left = pair_right = pad_w // 2
        if top is None:
            top = pair_top
            bottom = pair_bottom
            left = pair_left
            right = pair_right
        elif (top, bottom, left, right) != (pair_top, pair_bottom, pair_left, pair_right):
            return None
        if out_h == in_h or out_w == in_w:
            return None
        candidate_border = output_grid[0][0]
        if border_color is None:
            border_color = candidate_border
        elif border_color != candidate_border:
            return None
        expected = _pad_grid(input_grid, pair_top, pair_bottom, pair_left, pair_right, candidate_border)
        if expected != output_grid:
            return None
        summaries.append({"padding": [pair_top, pair_bottom, pair_left, pair_right], "border_color": candidate_border})
    if top is None or border_color is None:
        return None
    return ResizeTileRuleV1(
        family="border_padding",
        params={"top": top, "bottom": bottom or 0, "left": left or 0, "right": right or 0, "border_color": border_color},
        role_summary={"rule": "border_padding", "pair_count": len(train_pairs), "padding": [top, bottom or 0, left or 0, right or 0], "border_color": border_color, "pair_summaries": summaries},
    )


def _infer_crop_then_tile_rule(train_pairs: Sequence[Mapping[str, Any]]) -> ResizeTileRuleV1 | None:
    crop_summaries: list[dict[str, Any]] = []
    repeat_rows: int | None = None
    repeat_cols: int | None = None
    for pair in train_pairs:
        output_grid = validate_grid_v1(_pair_output(pair))
        try:
            cropped = crop_to_foreground_bbox_v1(_pair_input(pair))
        except Exception:
            return None
        out_h, out_w = len(output_grid), len(output_grid[0])
        crop_h, crop_w = len(cropped), len(cropped[0])
        if not _is_integer_ratio(out_h, crop_h) or not _is_integer_ratio(out_w, crop_w):
            return None
        pair_repeat_rows = out_h // crop_h
        pair_repeat_cols = out_w // crop_w
        if repeat_rows is None:
            repeat_rows = pair_repeat_rows
        elif repeat_rows != pair_repeat_rows:
            return None
        if repeat_cols is None:
            repeat_cols = pair_repeat_cols
        elif repeat_cols != pair_repeat_cols:
            return None
        if _tile_grid(cropped, pair_repeat_rows, pair_repeat_cols) != output_grid:
            return None
        crop_summaries.append({"repeat_rows": pair_repeat_rows, "repeat_cols": pair_repeat_cols, "crop_size": [crop_h, crop_w]})
    if repeat_rows is None or repeat_cols is None:
        return None
    return ResizeTileRuleV1(
        family="crop_then_tile",
        params={"repeat_rows": repeat_rows, "repeat_cols": repeat_cols},
        role_summary={"rule": "crop_then_tile", "pair_count": len(train_pairs), "repeat_rows": repeat_rows, "repeat_cols": repeat_cols, "pair_summaries": crop_summaries},
    )


def _build_executor(rule: ResizeTileRuleV1):
    def executor(pair: Mapping[str, Any]) -> Any:
        input_grid = validate_grid_v1(_pair_input(pair))
        if rule.family == "crop_foreground_bbox":
            return crop_to_foreground_bbox_v1(input_grid)
        if rule.family == "tile_repeat":
            return _tile_grid(input_grid, int(rule.params["repeat_rows"]), int(rule.params["repeat_cols"]))
        if rule.family == "integer_scale":
            return _repeat_grid(input_grid, int(rule.params["scale_rows"]), int(rule.params["scale_cols"]))
        if rule.family == "border_padding":
            return _pad_grid(
                input_grid,
                int(rule.params["top"]),
                int(rule.params["bottom"]),
                int(rule.params["left"]),
                int(rule.params["right"]),
                int(rule.params["border_color"]),
            )
        if rule.family == "crop_then_tile":
            cropped = crop_to_foreground_bbox_v1(input_grid)
            return _tile_grid(cropped, int(rule.params["repeat_rows"]), int(rule.params["repeat_cols"]))
        raise ValueError("unsupported_family")

    return executor


def infer_resize_tile_hypotheses_v1(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[HypothesisCandidate]:
    rule_builders = [
        _infer_crop_foreground_rule,
        _infer_tile_repeat_rule,
        _infer_integer_scale_rule,
        _infer_border_padding_rule,
        _infer_crop_then_tile_rule,
    ]
    candidates: list[HypothesisCandidate] = []
    for builder in rule_builders:
        rule = builder(train_pairs)
        if rule is None:
            continue
        confidence = 1.0 - (RESIZE_TILE_FAMILY_ORDER_V1.get(rule.family, 99) * 0.01)
        scored = score_train_consistency(
            train_pairs,
            _build_executor(rule),
            family=rule.family,
            confidence=confidence,
            candidate_id=f"resize_tile:{rule.family}",
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
                candidate_id=f"resize_tile:{rule.family}",
            )
        )
    return rank_hypotheses(candidates)


def solve_resize_tile_task(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[dict[str, Any]]:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        return []
    ranked = infer_resize_tile_hypotheses_v1(train_pairs, test_input)
    return [candidate.to_dict() for candidate in ranked]


__all__ = [
    "RESIZE_TILE_FAMILY_ORDER_V1",
    "ResizeTileRuleV1",
    "grid_dimensions_v1",
    "output_size_relation_v1",
    "infer_resize_tile_hypotheses_v1",
    "solve_resize_tile_task",
]
