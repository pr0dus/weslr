"""ARC color-role abstraction capability V1.

Synthetic-only, deterministic color reasoning helpers for ARC-style tasks.
This module infers simple recoloring rules from train pairs and executes them
on the test input, using the shared hypothesis engine for exact train-fit
validation.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from weslr.arc_hypothesis_engine_v1 import HypothesisCandidate, rank_hypotheses, score_train_consistency
from weslr.arc_object_extraction_v1 import extract_objects_v1, infer_background_value_v1, validate_grid_v1

SCHEMA_VERSION_V1 = "ArcColorRoleAbstractionV1"

COLOR_ROLE_FAMILY_ORDER_V1 = {
    "background_recolor": 0,
    "object_source_color_recolor": 1,
    "foreground_recolor": 2,
    "color_swap": 3,
}


@dataclass(frozen=True)
class ColorRoleRuleV1:
    family: str
    mapping: dict[int, int]
    background_input: int
    background_output: int
    foreground_input_colors: tuple[int, ...]
    foreground_output_colors: tuple[int, ...]
    source_color: int | None = None
    target_color: int | None = None
    swapped_colors: tuple[int, int] | None = None
    role_summary: dict[str, Any] | None = None


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _grid_copy(grid: Any) -> list[list[int]]:
    normalized = validate_grid_v1(grid)
    return [list(row) for row in normalized]


def color_histogram_v1(grid: Any) -> dict[int, int]:
    normalized = validate_grid_v1(grid)
    return dict(Counter(cell for row in normalized for cell in row))


def infer_background_color_v1(grid: Any) -> int:
    normalized = validate_grid_v1(grid)
    return infer_background_value_v1(normalized)


def foreground_color_set_v1(grid: Any) -> set[int]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized)
    return {cell for row in normalized for cell in row if cell != background}


def color_positions_v1(grid: Any) -> dict[int, list[tuple[int, int]]]:
    normalized = validate_grid_v1(grid)
    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(normalized):
        for col_index, cell in enumerate(row):
            positions.setdefault(cell, []).append((row_index, col_index))
    return positions


def color_role_summary_v1(grid: Any) -> dict[str, Any]:
    normalized = validate_grid_v1(grid)
    background = infer_background_value_v1(normalized)
    histogram = color_histogram_v1(normalized)
    positions = color_positions_v1(normalized)
    objects = extract_objects_v1(normalized, background_value=background)["objects"]
    return {
        "background_color": background,
        "histogram": histogram,
        "foreground_colors": sorted(cell for cell in histogram if cell != background),
        "foreground_color_count": len([cell for cell in histogram if cell != background]),
        "color_positions_count": {color: len(coords) for color, coords in positions.items()},
        "object_colors": sorted({int(obj["color"]) for obj in objects}),
        "object_count": len(objects),
        "color_roles": {
            "background": background,
            "foreground": sorted(cell for cell in histogram if cell != background),
        },
    }


def _pair_input(pair: Mapping[str, Any]) -> Any:
    return pair.get("input", pair.get("input_grid"))


def _pair_output(pair: Mapping[str, Any]) -> Any:
    return pair.get("output", pair.get("output_grid"))


def _validate_pair_grids(train_pairs: Sequence[Mapping[str, Any]]) -> tuple[list[list[int]], list[list[int]], int, int]:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        raise ValueError("empty_train_pairs")
    first_input = validate_grid_v1(_pair_input(train_pairs[0]))
    first_output = validate_grid_v1(_pair_output(train_pairs[0]))
    if len(first_input) != len(first_output) or len(first_input[0]) != len(first_output[0]):
        raise ValueError("shape_mismatch")
    return first_input, first_output, len(first_input), len(first_input[0])


def _apply_mapping(grid: Any, mapping: Mapping[int, int]) -> list[list[int]]:
    normalized = validate_grid_v1(grid)
    return [[int(mapping.get(cell, cell)) for cell in row] for row in normalized]


def _infer_color_mapping(train_pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        return None
    mapping: dict[int, int] = {}
    input_histograms: list[dict[int, int]] = []
    output_histograms: list[dict[int, int]] = []
    background_inputs: list[int] = []
    background_outputs: list[int] = []
    dims: tuple[int, int] | None = None
    for pair in train_pairs:
        input_grid = validate_grid_v1(_pair_input(pair))
        output_grid = validate_grid_v1(_pair_output(pair))
        if len(input_grid) != len(output_grid) or len(input_grid[0]) != len(output_grid[0]):
            return None
        pair_dims = (len(input_grid), len(input_grid[0]))
        if dims is None:
            dims = pair_dims
        elif dims != pair_dims:
            return None
        bg_in = infer_background_value_v1(input_grid)
        bg_out = infer_background_value_v1(output_grid)
        background_inputs.append(bg_in)
        background_outputs.append(bg_out)
        input_histograms.append(dict(Counter(cell for row in input_grid for cell in row)))
        output_histograms.append(dict(Counter(cell for row in output_grid for cell in row)))
        for row_in, row_out in zip(input_grid, output_grid):
            for cell_in, cell_out in zip(row_in, row_out):
                current = mapping.get(cell_in)
                if current is None:
                    mapping[cell_in] = cell_out
                elif current != cell_out:
                    return None

    if not mapping:
        return None

    changed = [source for source, target in mapping.items() if source != target]
    if not changed:
        return None

    return {
        "mapping": mapping,
        "changed": changed,
        "background_inputs": background_inputs,
        "background_outputs": background_outputs,
        "input_histograms": input_histograms,
        "output_histograms": output_histograms,
        "dims": dims,
    }


def _infer_color_role_rule(train_pairs: Sequence[Mapping[str, Any]]) -> ColorRoleRuleV1 | None:
    info = _infer_color_mapping(train_pairs)
    if info is None:
        return None
    mapping = dict(info["mapping"])
    changed = list(info["changed"])
    background_inputs = list(info["background_inputs"])
    background_outputs = list(info["background_outputs"])
    dims = info["dims"]
    if dims is None:
        return None

    # Identity-only rules are explicitly rejected.
    if not changed:
        return None

    background_input = background_inputs[0]
    background_output = background_outputs[0]
    if any(bg != background_input for bg in background_inputs):
        return None
    if any(bg != background_output for bg in background_outputs):
        return None

    # Candidate families are intentionally simple and exact.
    foreground_input_colors = tuple(sorted(cell for cell in mapping if cell != background_input))
    foreground_output_colors = tuple(sorted(cell for cell in mapping.values() if cell != background_output))
    role_summary = {
        "background_color": background_input,
        "foreground_colors": list(foreground_input_colors),
        "color_mapping_size": len(mapping),
        "changed_colors": sorted(changed),
    }

    # Background recolor: only the background changes.
    if changed == [background_input] and mapping[background_input] != background_input:
        return ColorRoleRuleV1(
            family="background_recolor",
            mapping=mapping,
            background_input=background_input,
            background_output=background_output,
            foreground_input_colors=foreground_input_colors,
            foreground_output_colors=foreground_output_colors,
            source_color=background_input,
            target_color=mapping[background_input],
            role_summary=role_summary,
        )

    # Single source-color recolor.
    if len(changed) == 1:
        source = changed[0]
        target = mapping[source]
        object_colors = {int(obj["color"]) for obj in extract_objects_v1(validate_grid_v1(_pair_input(train_pairs[0])), background_value=background_input)["objects"]}
        if source != background_input and source in object_colors:
            return ColorRoleRuleV1(
                family="object_source_color_recolor",
                mapping=mapping,
                background_input=background_input,
                background_output=background_output,
                foreground_input_colors=foreground_input_colors,
                foreground_output_colors=foreground_output_colors,
                source_color=source,
                target_color=target,
                role_summary=role_summary,
            )

    # Foreground recolor: all non-background colors map to one target, background stays fixed.
    if mapping.get(background_input, background_input) == background_input:
        foreground_targets = {mapping.get(color, color) for color in mapping if color != background_input}
        if len(foreground_targets) == 1:
            target = next(iter(foreground_targets))
            if target != background_input and any(mapping.get(color, color) != color for color in mapping if color != background_input):
                return ColorRoleRuleV1(
                    family="foreground_recolor",
                    mapping=mapping,
                    background_input=background_input,
                    background_output=background_output,
                    foreground_input_colors=foreground_input_colors,
                    foreground_output_colors=foreground_output_colors,
                    target_color=target,
                    role_summary=role_summary,
                )

    # Two-color swap: exact swap, everything else unchanged.
    if len(changed) == 2:
        a, b = changed[0], changed[1]
        if mapping.get(a) == b and mapping.get(b) == a:
            if all(mapping.get(color, color) == color for color in mapping if color not in {a, b}):
                return ColorRoleRuleV1(
                    family="color_swap",
                    mapping=mapping,
                    background_input=background_input,
                    background_output=background_output,
                    foreground_input_colors=foreground_input_colors,
                    foreground_output_colors=foreground_output_colors,
                    swapped_colors=(a, b),
                    role_summary=role_summary,
                )

    return None


def _build_rule_executor(rule: ColorRoleRuleV1):
    def executor(pair: Mapping[str, Any]) -> Any:
        grid = _pair_input(pair)
        normalized = validate_grid_v1(grid)
        if rule.family == "background_recolor" and rule.source_color is not None and rule.target_color is not None:
            return [[int(rule.target_color) if cell == rule.source_color else cell for cell in row] for row in normalized]
        if rule.family == "object_source_color_recolor" and rule.source_color is not None and rule.target_color is not None:
            return [[int(rule.target_color) if cell == rule.source_color else cell for cell in row] for row in normalized]
        if rule.family == "foreground_recolor" and rule.target_color is not None:
            return [[int(rule.target_color) if cell != rule.background_input else cell for cell in row] for row in normalized]
        if rule.family == "color_swap" and rule.swapped_colors is not None:
            a, b = rule.swapped_colors
            return [[b if cell == a else a if cell == b else cell for cell in row] for row in normalized]
        return _apply_mapping(grid, rule.mapping)

    return executor


def infer_color_role_hypotheses_v1(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[HypothesisCandidate]:
    rule = _infer_color_role_rule(train_pairs)
    if rule is None:
        return []

    candidate_trace = {
        "schema_version": SCHEMA_VERSION_V1,
        "family": rule.family,
        "background_input": rule.background_input,
        "background_output": rule.background_output,
        "foreground_input_colors": list(rule.foreground_input_colors),
        "foreground_output_colors": list(rule.foreground_output_colors),
        "rule_family_aliases": ["global_color_replacement", rule.family],
        "role_summary": deepcopy(rule.role_summary or {}),
        "synthetic_only": True,
    }
    if rule.source_color is not None:
        candidate_trace["source_color"] = rule.source_color
    if rule.target_color is not None:
        candidate_trace["target_color"] = rule.target_color
    if rule.swapped_colors is not None:
        candidate_trace["swapped_colors"] = list(rule.swapped_colors)

    # Small family-specific confidence bias keeps ranking deterministic.
    family_confidence = {
        "background_recolor": 1.0,
        "object_source_color_recolor": 0.99,
        "foreground_recolor": 0.98,
        "color_swap": 0.97,
    }.get(rule.family, 0.95)

    scored = score_train_consistency(
        train_pairs,
        _build_rule_executor(rule),
        family=rule.family,
        confidence=family_confidence,
        candidate_id=f"color_role:{rule.family}",
        trace=candidate_trace,
    )
    if not scored.train_fit:
        return []

    predicted = _build_rule_executor(rule)({"input": test_input})
    candidates = [
        HypothesisCandidate(
            family=rule.family,
            confidence=family_confidence,
            output=predicted,
            trace=scored.trace,
            train_fit=True,
            rejection_reason=None,
            candidate_id=f"color_role:{rule.family}",
        )
    ]
    if rule.family == "object_source_color_recolor" and rule.source_color is not None and rule.target_color is not None:
        alias_trace = dict(scored.trace)
        alias_trace["rule_family_aliases"] = ["global_color_replacement", "object_source_color_recolor"]
        candidates.append(
            HypothesisCandidate(
                family="global_color_replacement",
                confidence=max(0.0, family_confidence - 0.01),
                output=predicted,
                trace=alias_trace,
                train_fit=True,
                rejection_reason=None,
                candidate_id=f"color_role:global_color_replacement:{rule.source_color}->{rule.target_color}",
            )
        )
    return rank_hypotheses(candidates)


def solve_color_role_task(train_pairs: Sequence[Mapping[str, Any]], test_input: Any) -> list[dict[str, Any]]:
    if not isinstance(train_pairs, Sequence) or not train_pairs:
        return []
    ranked = infer_color_role_hypotheses_v1(train_pairs, test_input)
    return [candidate.to_dict() for candidate in ranked]


__all__ = [
    "COLOR_ROLE_FAMILY_ORDER_V1",
    "ColorRoleRuleV1",
    "color_histogram_v1",
    "color_positions_v1",
    "color_role_summary_v1",
    "foreground_color_set_v1",
    "infer_background_color_v1",
    "infer_color_role_hypotheses_v1",
    "solve_color_role_task",
]
