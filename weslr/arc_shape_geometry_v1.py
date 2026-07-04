"""ARC shape geometry capability V1.

Single-object shape transforms with canonical signatures and exact train
consistency checks. This module stays synthetic-only and metadata-safe.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from weslr.arc_hypothesis_engine_v1 import HypothesisCandidate, rank_hypotheses, score_train_consistency
from weslr.arc_object_extraction_v1 import (
    extract_objects_v1,
    infer_background_value_v1,
    validate_grid_v1,
)

SHAPE_GEOMETRY_FAMILY_ORDER_V1 = {
    "rotate_90_single_object": 0,
    "rotate_180_single_object": 1,
    "rotate_270_single_object": 2,
    "reflect_horizontal_single_object": 3,
    "reflect_vertical_single_object": 4,
    "translate_single_object": 5,
}


def _pair_input(pair: Mapping[str, Any]) -> Any:
    return pair.get("input_grid", pair.get("input"))


def _pair_output(pair: Mapping[str, Any]) -> Any:
    return pair.get("output_grid", pair.get("output"))


def _pair_background(pair: Mapping[str, Any]) -> int | None:
    background = pair.get("background_value", pair.get("background"))
    return int(background) if isinstance(background, int) and not isinstance(background, bool) else None


def _as_cells(cells: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    return [(int(r), int(c)) for r, c in cells]


def normalize_object_mask_v1(cells: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    normalized = _as_cells(cells)
    if not normalized:
        return []
    min_row = min(r for r, _ in normalized)
    min_col = min(c for _, c in normalized)
    return sorted((r - min_row, c - min_col) for r, c in normalized)


def canonical_shape_signature_v1(cells: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(normalize_object_mask_v1(cells))


def rotate_object_mask_v1(cells: Sequence[Sequence[int]], turns: int) -> list[tuple[int, int]]:
    normalized = normalize_object_mask_v1(cells)
    turns = int(turns) % 4
    if turns == 0 or not normalized:
        return normalized
    coords = normalized
    for _ in range(turns):
        height = max(r for r, _ in coords) + 1
        width = max(c for _, c in coords) + 1
        coords = [(c, height - 1 - r) for r, c in coords]
        coords = normalize_object_mask_v1(coords)
    return coords


def reflect_object_mask_v1(cells: Sequence[Sequence[int]], axis: str) -> list[tuple[int, int]]:
    normalized = normalize_object_mask_v1(cells)
    if not normalized:
        return []
    height = max(r for r, _ in normalized) + 1
    width = max(c for _, c in normalized) + 1
    if axis == "horizontal":
        reflected = [(height - 1 - r, c) for r, c in normalized]
    elif axis == "vertical":
        reflected = [(r, width - 1 - c) for r, c in normalized]
    else:
        raise ValueError("invalid_reflection_axis")
    return normalize_object_mask_v1(reflected)


def compare_shape_signatures_independent_of_position_v1(
    first: Sequence[Sequence[int]],
    second: Sequence[Sequence[int]],
) -> bool:
    return canonical_shape_signature_v1(first) == canonical_shape_signature_v1(second)


def rebuild_object_into_background_grid_v1(
    cells: Sequence[Sequence[int]],
    *,
    color: int,
    background_value: int,
    height: int | None = None,
    width: int | None = None,
    anchor_row: int = 0,
    anchor_col: int = 0,
) -> list[list[int]]:
    normalized = normalize_object_mask_v1(cells)
    if not normalized:
        return [[background_value]] if height is None or width is None else [[background_value for _ in range(width)] for _ in range(height)]
    object_height = max(r for r, _ in normalized) + 1
    object_width = max(c for _, c in normalized) + 1
    out_height = int(height) if height is not None else object_height
    out_width = int(width) if width is not None else object_width
    if out_height <= 0 or out_width <= 0:
        raise ValueError("invalid_grid_dimensions")
    out = [[background_value for _ in range(out_width)] for _ in range(out_height)]
    for r, c in normalized:
        rr = anchor_row + r
        cc = anchor_col + c
        if rr < 0 or cc < 0 or rr >= out_height or cc >= out_width:
            raise ValueError("rebuild_out_of_bounds")
        out[rr][cc] = color
    return out


def _extract_single_object_or_none(grid: Any, *, background_value: int | None = None) -> dict[str, Any] | None:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized, explicit_background=background_value)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    if len(objects) != 1:
        return None
    return {"grid": normalized, "background": background, "object": objects[0]}


def _family_prediction_from_input(
    grid: Any,
    *,
    family: str,
    background_value: int | None = None,
    delta_row: int = 0,
    delta_col: int = 0,
    output_mode: str = "canvas",
) -> list[list[int]]:
    extracted = _extract_single_object_or_none(grid, background_value=background_value)
    if extracted is None:
        raise ValueError("single_object_required")
    normalized = extracted["grid"]
    background = extracted["background"]
    obj = extracted["object"]
    color = int(obj["color"])
    cells = _as_cells(obj["cells"])
    bbox = obj["bbox"]
    anchor_row, anchor_col = int(bbox[0]), int(bbox[1])

    if family == "translate_single_object":
        return rebuild_object_into_background_grid_v1(
            cells,
            color=color,
            background_value=background,
            height=len(normalized),
            width=len(normalized[0]),
            anchor_row=anchor_row + delta_row,
            anchor_col=anchor_col + delta_col,
        )

    if family.startswith("rotate_") or family.startswith("reflect_"):
        if family == "rotate_90_single_object":
            transformed = rotate_object_mask_v1(cells, 1)
        elif family == "rotate_180_single_object":
            transformed = rotate_object_mask_v1(cells, 2)
        elif family == "rotate_270_single_object":
            transformed = rotate_object_mask_v1(cells, 3)
        elif family == "reflect_horizontal_single_object":
            transformed = reflect_object_mask_v1(cells, "horizontal")
        elif family == "reflect_vertical_single_object":
            transformed = reflect_object_mask_v1(cells, "vertical")
        else:
            raise ValueError("unsupported_family")
        if output_mode == "crop":
            return rebuild_object_into_background_grid_v1(
                transformed,
                color=color,
                background_value=background,
            )
        return rebuild_object_into_background_grid_v1(
            transformed,
            color=color,
            background_value=background,
            height=len(normalized),
            width=len(normalized[0]),
            anchor_row=anchor_row,
            anchor_col=anchor_col,
        )

    raise ValueError("unsupported_family")


def _infer_family_parameters(train_pairs: Sequence[Mapping[str, Any]], family: str) -> dict[str, Any] | None:
    params: dict[str, Any] = {}
    inferred_output_mode: str | None = None
    inferred_color: int | None = None
    inferred_delta: tuple[int, int] | None = None
    for pair in train_pairs:
        input_info = _extract_single_object_or_none(_pair_input(pair), background_value=_pair_background(pair))
        output_info = _extract_single_object_or_none(_pair_output(pair), background_value=_pair_background(pair))
        if input_info is None or output_info is None:
            return None
        input_object = input_info["object"]
        output_object = output_info["object"]
        if int(input_object["color"]) != int(output_object["color"]):
            return None
        if inferred_color is None:
            inferred_color = int(input_object["color"])
        elif inferred_color != int(input_object["color"]):
            return None

        input_cells = _as_cells(input_object["cells"])
        output_cells = _as_cells(output_object["cells"])
        if family == "translate_single_object":
            if canonical_shape_signature_v1(input_cells) != canonical_shape_signature_v1(output_cells):
                return None
            input_bbox = input_object["bbox"]
            output_bbox = output_object["bbox"]
            pair_delta = (int(output_bbox[0]) - int(input_bbox[0]), int(output_bbox[1]) - int(input_bbox[1]))
            if inferred_delta is None:
                inferred_delta = pair_delta
            elif inferred_delta != pair_delta:
                return None
            if len(input_info["grid"]) != len(output_info["grid"]) or len(input_info["grid"][0]) != len(output_info["grid"][0]):
                return None
            continue

        if family == "rotate_90_single_object":
            if rotate_object_mask_v1(input_cells, 1) != normalize_object_mask_v1(output_cells):
                return None
        elif family == "rotate_180_single_object":
            if rotate_object_mask_v1(input_cells, 2) != normalize_object_mask_v1(output_cells):
                return None
        elif family == "rotate_270_single_object":
            if rotate_object_mask_v1(input_cells, 3) != normalize_object_mask_v1(output_cells):
                return None
        elif family == "reflect_horizontal_single_object":
            if reflect_object_mask_v1(input_cells, "horizontal") != normalize_object_mask_v1(output_cells):
                return None
        elif family == "reflect_vertical_single_object":
            if reflect_object_mask_v1(input_cells, "vertical") != normalize_object_mask_v1(output_cells):
                return None
        else:
            return None

        input_mode = (len(input_info["grid"]), len(input_info["grid"][0]))
        output_mode = (len(output_info["grid"]), len(output_info["grid"][0]))
        if inferred_output_mode is None:
            inferred_output_mode = "canvas" if input_mode == output_mode else "crop"
        elif inferred_output_mode == "canvas" and input_mode != output_mode:
            return None
        elif inferred_output_mode == "crop" and input_mode == output_mode:
            # Allow crop only when the output is the tight object grid.
            pass

    if family == "translate_single_object":
        if inferred_delta is None:
            return None
        params["delta_row"] = inferred_delta[0]
        params["delta_col"] = inferred_delta[1]
        params["output_mode"] = "canvas"
    else:
        params["output_mode"] = inferred_output_mode or "canvas"
    params["background_value"] = _pair_background(train_pairs[0]) if train_pairs else None
    params["color"] = inferred_color
    return params


def infer_shape_geometry_hypotheses_v1(
    train_pairs: Sequence[Mapping[str, Any]],
    test_input: Any,
) -> list[HypothesisCandidate]:
    families = [
        "rotate_90_single_object",
        "rotate_180_single_object",
        "rotate_270_single_object",
        "reflect_horizontal_single_object",
        "reflect_vertical_single_object",
        "translate_single_object",
    ]
    candidates: list[HypothesisCandidate] = []
    for family in families:
        params = _infer_family_parameters(train_pairs, family)
        if params is None:
            continue

        def executor(pair: Mapping[str, Any], *, _family: str = family, _params: Mapping[str, Any] = params) -> Any:
            return _family_prediction_from_input(
                _pair_input(pair),
                family=_family,
                background_value=_params.get("background_value"),
                delta_row=int(_params.get("delta_row", 0) or 0),
                delta_col=int(_params.get("delta_col", 0) or 0),
                output_mode=_params.get("output_mode", "canvas"),
            )

        score = score_train_consistency(
            train_pairs,
            executor,
            family=family,
            confidence=1.0,
            candidate_id=family,
            trace={
                "rule_family": family,
                "shape_signature_count": len({canonical_shape_signature_v1(_as_cells(_extract_single_object_or_none(_pair_input(pair), background_value=_pair_background(pair))["object"]["cells"])) for pair in train_pairs}),
                "output_mode": params.get("output_mode"),
            },
        )
        if not score.train_fit:
            continue
        predicted = _family_prediction_from_input(
            test_input,
            family=family,
            background_value=params.get("background_value"),
            delta_row=int(params.get("delta_row", 0) or 0),
            delta_col=int(params.get("delta_col", 0) or 0),
            output_mode=params.get("output_mode", "canvas"),
        )
        candidate_trace = dict(score.trace)
        candidate_trace.update(
            {
                "family": family,
                "transform_parameters": {k: v for k, v in params.items() if k in {"delta_row", "delta_col", "output_mode"}},
                "synthetic_only": True,
            }
        )
        candidates.append(
            HypothesisCandidate(
                family=family,
                confidence=1.0,
                output=predicted,
                trace=candidate_trace,
                train_fit=True,
                rejection_reason=None,
                candidate_id=family,
            )
        )
    return rank_hypotheses(candidates)


def solve_shape_geometry_task(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[dict[str, Any]]:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        return []
    ranked = infer_shape_geometry_hypotheses_v1(train_pairs, test_input)
    return [candidate.to_dict() for candidate in ranked]


__all__ = [
    "canonical_shape_signature_v1",
    "compare_shape_signatures_independent_of_position_v1",
    "infer_shape_geometry_hypotheses_v1",
    "rebuild_object_into_background_grid_v1",
    "reflect_object_mask_v1",
    "rotate_object_mask_v1",
    "solve_shape_geometry_task",
]
