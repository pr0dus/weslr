"""ARC object extraction + bbox crop/translate capability solver V1.

This is a small exact-match capability module for synthetic ARC-style tasks.
It only reasons about object extraction, bbox cropping, and single-object
translations. It is deterministic, pure Python, and metadata-safe.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping, Sequence

from weslr.arc_object_extraction_v1 import (
    crop_selected_color_object_v1,
    crop_to_foreground_bbox_v1,
    crop_to_largest_object_bbox_v1,
    extract_objects_v1,
    infer_background_value_v1,
    translate_object_v1,
    validate_grid_v1,
)


def _pair_input(pair: Mapping[str, Any]) -> Any:
    return pair.get("input_grid", pair.get("input"))


def _pair_output(pair: Mapping[str, Any]) -> Any:
    return pair.get("output_grid", pair.get("output"))


def _pair_background(pair: Mapping[str, Any]) -> int | None:
    background = pair.get("background_value", pair.get("background"))
    return int(background) if isinstance(background, int) and not isinstance(background, bool) else None


def _grids_equal(a: Any, b: Any) -> bool:
    return validate_grid_v1(a) == validate_grid_v1(b)


def _non_background_cells(grid: Sequence[Sequence[int]], background: int) -> list[tuple[int, int]]:
    return [(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell != background]


def _shape_signature(cells: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    if not cells:
        return tuple()
    rows = [cell[0] for cell in cells]
    cols = [cell[1] for cell in cells]
    r0, c0 = min(rows), min(cols)
    return tuple(sorted((cell[0] - r0, cell[1] - c0) for cell in cells))


def _bbox(cells: Sequence[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop_all_foreground_candidate(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> dict[str, Any] | None:
    for pair in train_pairs:
        inp = _pair_input(pair)
        out = _pair_output(pair)
        background = _pair_background(pair)
        try:
            predicted = crop_to_foreground_bbox_v1(inp, background_value=background)
        except Exception:
            return None
        if not _grids_equal(predicted, out):
            return None
    background = _pair_background(train_pairs[0]) if train_pairs else None
    try:
        output = crop_to_foreground_bbox_v1(test_input, background_value=background)
    except Exception:
        return None
    return {
        "family": "bbox_crop_all_foreground",
        "confidence": 1.0,
        "output": output,
        "trace": {"rule": "crop_to_non_background_bbox", "train_fit": True},
    }


def _crop_largest_object_candidate(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> dict[str, Any] | None:
    for pair in train_pairs:
        inp = _pair_input(pair)
        out = _pair_output(pair)
        background = _pair_background(pair)
        try:
            predicted = crop_to_largest_object_bbox_v1(inp, background_value=background)
        except Exception:
            return None
        if not _grids_equal(predicted, out):
            return None
    background = _pair_background(train_pairs[0]) if train_pairs else None
    try:
        output = crop_to_largest_object_bbox_v1(test_input, background_value=background)
    except Exception:
        return None
    return {
        "family": "bbox_crop_largest_object",
        "confidence": 1.0,
        "output": output,
        "trace": {"rule": "crop_to_largest_object_bbox", "train_fit": True},
    }


def _crop_selected_color_candidate(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> dict[str, Any] | None:
    selected_color: int | None = None
    background = _pair_background(train_pairs[0]) if train_pairs else None
    for pair in train_pairs:
        inp = validate_grid_v1(_pair_input(pair))
        out = validate_grid_v1(_pair_output(pair))
        bg = _pair_background(pair)
        objects = extract_objects_v1(inp, background_value=bg)["objects"]
        matching_colors: set[int] = set()
        for obj in objects:
            color = int(obj["color"])
            try:
                predicted = crop_selected_color_object_v1(inp, color=color, background_value=bg)
            except Exception:
                continue
            if predicted == out:
                matching_colors.add(color)
        if len(matching_colors) != 1:
            return None
        color = next(iter(matching_colors))
        if selected_color is None:
            selected_color = color
        elif selected_color != color:
            return None
    if selected_color is None:
        return None
    try:
        output = crop_selected_color_object_v1(test_input, color=selected_color, background_value=background)
    except Exception:
        return None
    return {
        "family": "bbox_crop_selected_color_object",
        "confidence": 1.0,
        "output": output,
        "trace": {"rule": "crop_selected_color_object", "selected_color": selected_color, "train_fit": True},
    }


def _translation_candidate(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> dict[str, Any] | None:
    delta: tuple[int, int] | None = None
    for pair in train_pairs:
        inp = validate_grid_v1(_pair_input(pair))
        out = validate_grid_v1(_pair_output(pair))
        bg = _pair_background(pair)
        if len(inp) != len(out) or len(inp[0]) != len(out[0]):
            return None
        in_objects = extract_objects_v1(inp, background_value=bg)["objects"]
        out_objects = extract_objects_v1(out, background_value=bg)["objects"]
        if len(in_objects) != 1 or len(out_objects) != 1:
            return None
        in_obj = in_objects[0]
        out_obj = out_objects[0]
        if in_obj["color"] != out_obj["color"]:
            return None
        if tuple(in_obj["canonical_shape"]) != tuple(out_obj["canonical_shape"]):
            return None
        in_bbox = in_obj["bbox"]
        out_bbox = out_obj["bbox"]
        pair_delta = (out_bbox[0] - in_bbox[0], out_bbox[1] - in_bbox[1])
        if delta is None:
            delta = pair_delta
        elif delta != pair_delta:
            return None
    if delta is None:
        return None
    try:
        output = translate_object_v1(test_input, delta_row=delta[0], delta_col=delta[1], background_value=_pair_background(train_pairs[0]) if train_pairs else None)
    except Exception:
        return None
    return {
        "family": "translation_single_object",
        "confidence": 1.0,
        "output": output,
        "trace": {"rule": "translate_single_object", "delta_row": delta[0], "delta_col": delta[1], "train_fit": True},
    }


def solve_object_bbox_task(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[dict[str, Any]]:
    """Return at most one exact-fit candidate for the task.

    The solver tries small exact families in priority order:
    crop all foreground, crop largest object, crop selected color object,
    and single-object translation.
    """
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        return []
    for builder in (
        _crop_all_foreground_candidate,
        _crop_largest_object_candidate,
        _crop_selected_color_candidate,
        _translation_candidate,
    ):
        try:
            candidate = builder(train_pairs, test_input)
        except Exception:
            candidate = None
        if candidate is not None:
            return [candidate]
    return []


__all__ = ["solve_object_bbox_task"]
