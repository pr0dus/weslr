"""WESLR ARC UNKNOWN ENGINE level-ladder generator V1.

Bounded, deterministic, synthetic-only ARC-style level generation for internal
transfer testing. This module implements generator-only scaffolding: level
metadata, family/tier definitions, solver-visible vs evaluator-only packet
separation, anti-cheat validation, curriculum recommendation scaffolds, and
JSON-safe summaries.

It does not modify solver behavior, add solver primitives, retry fill repair,
implement depth-3 search, ingest public ARC/Kaggle data, call providers,
perform payments, wire ChatResponder/runtime/website paths, or write `.weslr`.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Callable, Mapping, Sequence

from weslr.arc_style_grid_schema_helpers import build_arc_style_grid_metadata_v1

SCHEMA_VERSION_V1 = "ArcUnknownEngineLevelLadderGeneratorV1"
SUITE_ID_V1 = "arc_unknown_engine_level_ladder_v1"
DEFAULT_LEVEL_LADDER_SEED_V1 = 20260626
VARIANTS_PER_FAMILY_V1 = 2
MAX_GRID_SIZE_V1 = 30

PREVIOUS_HELDOUT_FAMILIES_V1 = (
    "extract_object_then_recolor",
    "move_then_border",
    "rotate_then_recolor",
    "remove_noise_then_complete_line",
    "count_object_then_emit_pattern",
    "reflect_then_recolor",
    "fill_region_then_extract_object",
)

LEVEL_TIERS_V1 = (
    {
        "tier": 0,
        "tier_id": "tier_0_calibration",
        "name": "calibration / sanity levels",
        "description": "bounded sanity levels that verify packet safety and basic relation capture",
        "concrete_in_v1": True,
    },
    {
        "tier": 1,
        "tier_id": "tier_1_transfer",
        "name": "transfer levels",
        "description": "bounded transfer levels with slightly wider relation and distractor pressure",
        "concrete_in_v1": True,
    },
    {
        "tier": 2,
        "tier_id": "tier_2_abstraction_pressure",
        "name": "abstraction-pressure levels",
        "description": "metadata only in V1",
        "concrete_in_v1": False,
    },
    {
        "tier": 3,
        "tier_id": "tier_3_strange_but_inferable",
        "name": "strange-but-train-inferable levels",
        "description": "metadata only in V1",
        "concrete_in_v1": False,
    },
    {
        "tier": 4,
        "tier_id": "tier_4_adversarial_curriculum",
        "name": "adversarial curriculum levels",
        "description": "metadata only in V1",
        "concrete_in_v1": False,
    },
    {
        "tier": 5,
        "tier_id": "tier_5_frontier_probe",
        "name": "frontier-probe levels",
        "description": "metadata only in V1",
        "concrete_in_v1": False,
    },
)

PRESSURE_AXES_V1 = {
    "hardness_axes": (
        "composition_depth",
        "abstraction_distance",
        "distractor_density",
        "ambiguity_level",
        "relation_dependency",
        "negative_evidence_dependency",
        "output_shape_uncertainty",
        "object_identity_drift",
        "rule_switching_pressure",
        "train_variation_distance",
        "misleading_local_regularity",
        "exception_handling",
        "sparse_evidence_pressure",
        "cross_example_consistency_pressure",
    ),
    "strangeness_axes": (
        "unfamiliar_object_role_remapping",
        "decoy_regularity",
        "partial_occlusion",
        "local_symmetry_conflict",
        "causal_feature_inversion",
        "absence_driven_rule_selection",
        "role_semantic_output_trigger",
        "cross_example_ambiguity_resolution",
    ),
}

LEVEL_FAMILY_CATALOG_V1 = (
    {
        "family_id": "relation_select_then_transform",
        "tier": 0,
        "variant_count": 2,
        "summary": "use a relation marker to choose one object and recolor only that object",
    },
    {
        "family_id": "distractor_suppression_by_consistency",
        "tier": 0,
        "variant_count": 2,
        "summary": "remove distractors and extend the only train-consistent line pattern",
    },
    {
        "family_id": "negative_evidence_object_choice",
        "tier": 0,
        "variant_count": 2,
        "summary": "select the object defined by a negative condition and suppress the rest",
    },
    {
        "family_id": "role_color_binding",
        "tier": 1,
        "variant_count": 2,
        "summary": "bind a role color from context and apply it to the active object",
    },
    {
        "family_id": "rule_switch_by_context",
        "tier": 1,
        "variant_count": 2,
        "summary": "switch between two bounded transformation rules using context",
    },
    {
        "family_id": "exception_based_symmetry_repair",
        "tier": 1,
        "variant_count": 2,
        "summary": "repair a near-symmetry while honoring an exception marker",
    },
)

FORBIDDEN_SOLVER_VISIBLE_KEYS_V1 = {
    "expected_output",
    "family_id",
    "generator_metadata",
    "mismatch_diagnosis_labels",
    "answer_key",
    "solution",
    "evaluator_packet",
}

PUBLIC_BOUNDARY_FLAGS_V1 = {
    "synthetic_only": True,
    "non_claim_safe": True,
    "uses_public_arc_data": False,
    "uses_kaggle_data": False,
    "uses_public_samples": False,
    "uses_benchmark_solution_copy": False,
    "solver_visible_answer_key": False,
    "provider_model_api_called": False,
    "chat_responder_called": False,
    "runtime_wiring_touched": False,
    "weslr_state_written": False,
}


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int)):
        return str(value)
    return default if value == "" else str(value)


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    return _safe_text(value)


def to_arc_unknown_engine_level_ladder_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _grid(rows: int, cols: int, fill: int = 0) -> list[list[int]]:
    return [[fill for _ in range(cols)] for _ in range(rows)]


def _clone(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _place_cells(grid: list[list[int]], cells: Sequence[tuple[int, int]], value: int) -> None:
    for row, col in cells:
        grid[row][col] = value


def _recolor_nonzero(grid: Sequence[Sequence[int]], color: int) -> list[list[int]]:
    out = _clone(grid)
    for row, row_values in enumerate(out):
        for col, value in enumerate(row_values):
            if value != 0:
                out[row][col] = color
    return out


def _valid_grid(grid: Any) -> bool:
    meta = build_arc_style_grid_metadata_v1(grid)
    return (
        isinstance(grid, list)
        and len(grid) >= 1
        and meta["width"] >= 1
        and meta["height"] >= 1
        and meta["width"] <= MAX_GRID_SIZE_V1
        and meta["height"] <= MAX_GRID_SIZE_V1
        and meta["trace"]["rectangular"] is True
        and not meta["invalid_cells"]
    )


def _validate_train(train_pairs: Sequence[Mapping[str, Any]]) -> bool:
    return all(
        isinstance(pair, Mapping)
        and _valid_grid(pair.get("input"))
        and _valid_grid(pair.get("output"))
        for pair in train_pairs
    )


def _make_train_pair(pair_id: str, input_grid: Sequence[Sequence[int]], output_grid: Sequence[Sequence[int]]) -> dict[str, Any]:
    return {
        "pair_id": pair_id,
        "input": _clone(input_grid),
        "output": _clone(output_grid),
    }


def _level_id(seed: int, tier: int, family_index: int, variant_index: int) -> str:
    return f"ue_v1_s{seed}_t{tier}_f{family_index:02d}_v{variant_index:02d}"


def _generic_solver_task_id(seed: int, tier: int, family_index: int, variant_index: int) -> str:
    return f"ue_task_{seed}_{tier}_{family_index}_{variant_index}"


def _base_packet_flags() -> dict[str, bool]:
    return dict(PUBLIC_BOUNDARY_FLAGS_V1)


def _base_forecast_seed_metadata(seed: int, family_index: int, variant_index: int) -> dict[str, Any]:
    return {
        "generator_seed": seed,
        "family_index": family_index,
        "variant_index": variant_index,
        "deterministic": True,
        "public_data_used": False,
    }


def _build_solver_visible_packet(
    *,
    task_id: str,
    tier: int,
    train: Sequence[Mapping[str, Any]],
    test_input: Sequence[Sequence[int]],
    hardness_axes: Sequence[str],
    strangeness_axes: Sequence[str],
    variant_id: str,
) -> dict[str, Any]:
    packet = {
        "task_id": task_id,
        "tier_hint": tier,
        "variant_id": variant_id,
        "train": [{"input": _clone(pair["input"]), "output": _clone(pair["output"])} for pair in train],
        "test_input": _clone(test_input),
        "pressure_metadata": {
            "hardness_axes": list(hardness_axes),
            "strangeness_axes": list(strangeness_axes),
            "axis_count": len(hardness_axes) + len(strangeness_axes),
        },
        "synthetic_only": True,
        "non_claim_safe": True,
        "public_boundary_flags": _base_packet_flags(),
    }
    return packet


def _build_evaluator_packet(
    *,
    level_id: str,
    family_id: str,
    tier: int,
    train: Sequence[Mapping[str, Any]],
    test_input: Sequence[Sequence[int]],
    expected_output: Sequence[Sequence[int]],
    hardness_axes: Sequence[str],
    strangeness_axes: Sequence[str],
    forecast_seed_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "level_id": level_id,
        "family_id": family_id,
        "tier": tier,
        "train": [{"input": _clone(pair["input"]), "output": _clone(pair["output"])} for pair in train],
        "test_input": _clone(test_input),
        "expected_output": _clone(expected_output),
        "hardness_axes": list(hardness_axes),
        "strangeness_axes": list(strangeness_axes),
        "mismatch_diagnosis_labels": [
            "synthetic_unknown_engine",
            "bounded_internal_transfer_testing",
        ],
        "generator_metadata": {
            "schema_version": SCHEMA_VERSION_V1,
            "forecast_seed_metadata": _json_safe(forecast_seed_metadata),
        },
        "synthetic_only": True,
        "non_claim_safe": True,
        "public_boundary_flags": _base_packet_flags(),
    }


def validate_solver_visible_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        return {"valid": False, "violations": ["packet_not_mapping"]}

    def _walk(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                key_text = _safe_text(key)
                if key_text in FORBIDDEN_SOLVER_VISIBLE_KEYS_V1:
                    violations.append(f"forbidden_key:{path}{key_text}")
                _walk(item, f"{path}{key_text}.")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                _walk(item, f"{path}{index}.")

    _walk(packet, "")
    if "test_input" not in packet:
        violations.append("missing_test_input")
    if "train" not in packet:
        violations.append("missing_train")
    if packet.get("synthetic_only") is not True:
        violations.append("synthetic_only_flag_missing")
    if packet.get("non_claim_safe") is not True:
        violations.append("non_claim_safe_flag_missing")
    if packet.get("public_boundary_flags", {}).get("solver_visible_answer_key") is not False:
        violations.append("boundary_flag_solver_answer_key_not_false")
    return {"valid": not violations, "violations": violations}


def validate_evaluator_packet_v1(packet: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(packet, Mapping):
        return {"valid": False, "violations": ["packet_not_mapping"]}
    if not _valid_grid(packet.get("expected_output")):
        violations.append("expected_output_invalid_or_missing")
    if not packet.get("family_id"):
        violations.append("family_id_missing")
    if packet.get("synthetic_only") is not True:
        violations.append("synthetic_only_flag_missing")
    if packet.get("non_claim_safe") is not True:
        violations.append("non_claim_safe_flag_missing")
    return {"valid": not violations, "violations": violations}


def validate_level_v1(level: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(level, Mapping):
        return {"valid": False, "violations": ["level_not_mapping"]}
    required = (
        "level_id",
        "tier",
        "family_id",
        "variant_id",
        "hardness_axes",
        "strangeness_axes",
        "train",
        "test_input",
        "solver_visible_packet",
        "evaluator_packet",
        "forecast_seed_metadata",
        "synthetic_only",
        "non_claim_safe",
    )
    for field in required:
        if field not in level:
            violations.append(f"missing_{field}")
    if not _validate_train(level.get("train", [])):
        violations.append("invalid_train_pairs")
    if not _valid_grid(level.get("test_input")):
        violations.append("invalid_test_input")
    expected_output = level.get("evaluator_packet", {}).get("expected_output") if isinstance(level.get("evaluator_packet"), Mapping) else None
    if not _valid_grid(expected_output):
        violations.append("invalid_expected_output")
    solver_validation = validate_solver_visible_packet_v1(level.get("solver_visible_packet"))
    if solver_validation["valid"] is False:
        violations.extend([f"solver_packet:{item}" for item in solver_validation["violations"]])
    evaluator_validation = validate_evaluator_packet_v1(level.get("evaluator_packet"))
    if evaluator_validation["valid"] is False:
        violations.extend([f"evaluator_packet:{item}" for item in evaluator_validation["violations"]])
    if level.get("synthetic_only") is not True:
        violations.append("synthetic_only_flag_missing")
    if level.get("non_claim_safe") is not True:
        violations.append("non_claim_safe_flag_missing")
    return {"valid": not violations, "violations": violations}


def _family_axes(*, tier: int, family_index: int) -> tuple[list[str], list[str]]:
    hardness_all = list(PRESSURE_AXES_V1["hardness_axes"])
    strange_all = list(PRESSURE_AXES_V1["strangeness_axes"])
    hardness = [hardness_all[(tier + family_index + offset) % len(hardness_all)] for offset in range(3)]
    strangeness = [strange_all[(family_index + offset) % len(strange_all)] for offset in range(2)]
    return hardness, strangeness


def _relation_select_then_transform(seed: int, variant_index: int) -> tuple[list[dict[str, Any]], list[list[int]], list[list[int]]]:
    object_a = 2 + variant_index
    object_b = 4 + variant_index
    target_color = 7 + variant_index
    marker = 9
    train_1 = _grid(5, 5, 0)
    _place_cells(train_1, [(1, 1), (1, 2)], object_a)
    _place_cells(train_1, [(3, 2), (3, 3)], object_b)
    _place_cells(train_1, [(2, 2)], marker)
    out_1 = _grid(5, 5, 0)
    _place_cells(out_1, [(3, 2), (3, 3)], target_color)

    train_2 = _grid(5, 5, 0)
    _place_cells(train_2, [(1, 3), (2, 3)], object_b)
    _place_cells(train_2, [(3, 1), (3, 2)], object_a)
    _place_cells(train_2, [(2, 2)], marker)
    out_2 = _grid(5, 5, 0)
    _place_cells(out_2, [(3, 1), (3, 2)], target_color)

    test_input = _grid(5, 5, 0)
    _place_cells(test_input, [(1, 1), (2, 1)], object_a)
    _place_cells(test_input, [(2, 3), (3, 3)], object_b)
    _place_cells(test_input, [(2, 2)], marker)
    expected = _grid(5, 5, 0)
    _place_cells(expected, [(1, 1), (2, 1)], target_color)
    return [_make_train_pair("p0", train_1, out_1), _make_train_pair("p1", train_2, out_2)], test_input, expected


def _distractor_suppression_by_consistency(seed: int, variant_index: int) -> tuple[list[dict[str, Any]], list[list[int]], list[list[int]]]:
    color = 2 + variant_index
    noise = 6 + variant_index
    train_1 = _grid(5, 5, 0)
    _place_cells(train_1, [(2, 0), (2, 2)], color)
    _place_cells(train_1, [(0, 4), (4, 0)], noise)
    out_1 = _grid(5, 5, 0)
    _place_cells(out_1, [(2, 0), (2, 1), (2, 2)], color)

    train_2 = _grid(5, 5, 0)
    _place_cells(train_2, [(0, 1), (2, 1)], color)
    _place_cells(train_2, [(4, 4)], noise)
    out_2 = _grid(5, 5, 0)
    _place_cells(out_2, [(0, 1), (1, 1), (2, 1)], color)

    test_input = _grid(5, 5, 0)
    _place_cells(test_input, [(1, 1), (1, 3)], color)
    _place_cells(test_input, [(4, 2), (0, 0)], noise)
    expected = _grid(5, 5, 0)
    _place_cells(expected, [(1, 1), (1, 2), (1, 3)], color)
    return [_make_train_pair("p0", train_1, out_1), _make_train_pair("p1", train_2, out_2)], test_input, expected


def _negative_evidence_object_choice(seed: int, variant_index: int) -> tuple[list[dict[str, Any]], list[list[int]], list[list[int]]]:
    inner = 3 + variant_index
    border = 5 + variant_index
    target = 8 - variant_index
    train_1 = _grid(5, 5, 0)
    _place_cells(train_1, [(0, 1), (0, 2)], border)
    _place_cells(train_1, [(2, 2), (3, 2)], inner)
    out_1 = _grid(5, 5, 0)
    _place_cells(out_1, [(2, 2), (3, 2)], target)

    train_2 = _grid(5, 5, 0)
    _place_cells(train_2, [(1, 0), (2, 0)], border)
    _place_cells(train_2, [(2, 3), (2, 4)], border)
    _place_cells(train_2, [(2, 2), (3, 2)], inner)
    out_2 = _grid(5, 5, 0)
    _place_cells(out_2, [(2, 2), (3, 2)], target)

    test_input = _grid(5, 5, 0)
    _place_cells(test_input, [(4, 2), (4, 3)], border)
    _place_cells(test_input, [(2, 1), (2, 2)], inner)
    expected = _grid(5, 5, 0)
    _place_cells(expected, [(2, 1), (2, 2)], target)
    return [_make_train_pair("p0", train_1, out_1), _make_train_pair("p1", train_2, out_2)], test_input, expected


def _role_color_binding(seed: int, variant_index: int) -> tuple[list[dict[str, Any]], list[list[int]], list[list[int]]]:
    binder_a = 2 + variant_index
    binder_b = 6 + variant_index
    object_color = 4
    train_1 = _grid(5, 5, 0)
    _place_cells(train_1, [(0, 0)], binder_a)
    _place_cells(train_1, [(0, 4)], binder_b)
    _place_cells(train_1, [(2, 2), (2, 3), (3, 2)], object_color)
    out_1 = _grid(5, 5, 0)
    _place_cells(out_1, [(2, 2), (2, 3), (3, 2)], binder_a)

    train_2 = _grid(5, 5, 0)
    _place_cells(train_2, [(0, 0)], binder_b)
    _place_cells(train_2, [(0, 4)], binder_a)
    _place_cells(train_2, [(1, 2), (2, 2), (2, 3)], object_color)
    out_2 = _grid(5, 5, 0)
    _place_cells(out_2, [(1, 2), (2, 2), (2, 3)], binder_b)

    test_input = _grid(5, 5, 0)
    _place_cells(test_input, [(0, 0)], binder_a)
    _place_cells(test_input, [(0, 4)], binder_b)
    _place_cells(test_input, [(2, 1), (2, 2), (3, 2)], object_color)
    expected = _grid(5, 5, 0)
    _place_cells(expected, [(2, 1), (2, 2), (3, 2)], binder_a)
    return [_make_train_pair("p0", train_1, out_1), _make_train_pair("p1", train_2, out_2)], test_input, expected


def _rule_switch_by_context(seed: int, variant_index: int) -> tuple[list[dict[str, Any]], list[list[int]], list[list[int]]]:
    object_color = 3 + variant_index
    horizontal_context = 1
    vertical_context = 2
    train_1 = _grid(5, 5, 0)
    train_1[0][0] = horizontal_context
    _place_cells(train_1, [(2, 1), (2, 2)], object_color)
    out_1 = _clone(train_1)
    _place_cells(out_1, [(2, 2), (2, 3)], object_color)
    out_1[0][0] = 0

    train_2 = _grid(5, 5, 0)
    train_2[0][0] = vertical_context
    _place_cells(train_2, [(1, 3), (2, 3)], object_color)
    out_2 = _clone(train_2)
    _place_cells(out_2, [(2, 3), (3, 3)], object_color)
    out_2[0][0] = 0

    test_input = _grid(5, 5, 0)
    test_input[0][0] = horizontal_context if variant_index == 0 else vertical_context
    if variant_index == 0:
        _place_cells(test_input, [(3, 1), (3, 2)], object_color)
        expected = _grid(5, 5, 0)
        _place_cells(expected, [(3, 1), (3, 2), (3, 3)], object_color)
    else:
        _place_cells(test_input, [(1, 1), (2, 1)], object_color)
        expected = _grid(5, 5, 0)
        _place_cells(expected, [(1, 1), (2, 1), (3, 1)], object_color)
    return [_make_train_pair("p0", train_1, out_1), _make_train_pair("p1", train_2, out_2)], test_input, expected


def _exception_based_symmetry_repair(seed: int, variant_index: int) -> tuple[list[dict[str, Any]], list[list[int]], list[list[int]]]:
    body = 2 + variant_index
    marker = 8
    repair = 5 + variant_index
    train_1 = _grid(5, 5, 0)
    _place_cells(train_1, [(1, 1), (1, 3), (2, 1)], body)
    _place_cells(train_1, [(4, 4)], marker)
    out_1 = _grid(5, 5, 0)
    _place_cells(out_1, [(1, 1), (1, 3), (2, 1), (2, 3)], repair)

    train_2 = _grid(5, 5, 0)
    _place_cells(train_2, [(2, 1), (2, 3), (3, 3)], body)
    _place_cells(train_2, [(4, 4)], marker)
    out_2 = _grid(5, 5, 0)
    _place_cells(out_2, [(2, 1), (2, 3), (3, 1), (3, 3)], repair)

    test_input = _grid(5, 5, 0)
    _place_cells(test_input, [(1, 1), (1, 3), (2, 3)], body)
    _place_cells(test_input, [(4, 4)], marker)
    expected = _grid(5, 5, 0)
    _place_cells(expected, [(1, 1), (1, 3), (2, 1), (2, 3)], repair)
    return [_make_train_pair("p0", train_1, out_1), _make_train_pair("p1", train_2, out_2)], test_input, expected


FAMILY_GENERATORS_V1: dict[str, Callable[[int, int], tuple[list[dict[str, Any]], list[list[int]], list[list[int]]]]] = {
    "relation_select_then_transform": _relation_select_then_transform,
    "distractor_suppression_by_consistency": _distractor_suppression_by_consistency,
    "negative_evidence_object_choice": _negative_evidence_object_choice,
    "role_color_binding": _role_color_binding,
    "rule_switch_by_context": _rule_switch_by_context,
    "exception_based_symmetry_repair": _exception_based_symmetry_repair,
}


def _build_level(seed: int, family_entry: Mapping[str, Any], family_index: int, variant_index: int) -> dict[str, Any]:
    family_id = _safe_text(family_entry["family_id"])
    tier = int(family_entry["tier"])
    hardness_axes, strangeness_axes = _family_axes(tier=tier, family_index=family_index)
    train, test_input, expected_output = FAMILY_GENERATORS_V1[family_id](seed, variant_index)
    level_id = _level_id(seed, tier, family_index, variant_index)
    variant_id = f"variant_{variant_index}"
    forecast_seed_metadata = _base_forecast_seed_metadata(seed, family_index, variant_index)
    solver_packet = _build_solver_visible_packet(
        task_id=_generic_solver_task_id(seed, tier, family_index, variant_index),
        tier=tier,
        train=train,
        test_input=test_input,
        hardness_axes=hardness_axes,
        strangeness_axes=strangeness_axes,
        variant_id=variant_id,
    )
    evaluator_packet = _build_evaluator_packet(
        level_id=level_id,
        family_id=family_id,
        tier=tier,
        train=train,
        test_input=test_input,
        expected_output=expected_output,
        hardness_axes=hardness_axes,
        strangeness_axes=strangeness_axes,
        forecast_seed_metadata=forecast_seed_metadata,
    )
    return {
        "level_id": level_id,
        "tier": tier,
        "family_id": family_id,
        "variant_id": variant_id,
        "hardness_axes": hardness_axes,
        "strangeness_axes": strangeness_axes,
        "train": train,
        "test_input": test_input,
        "solver_visible_packet": solver_packet,
        "evaluator_packet": evaluator_packet,
        "forecast_seed_metadata": forecast_seed_metadata,
        "synthetic_only": True,
        "non_claim_safe": True,
        "public_boundary_flags": _base_packet_flags(),
    }


def generate_arc_unknown_engine_level_ladder_v1(seed: int = DEFAULT_LEVEL_LADDER_SEED_V1) -> dict[str, Any]:
    levels: list[dict[str, Any]] = []
    for family_index, family_entry in enumerate(LEVEL_FAMILY_CATALOG_V1):
        for variant_index in range(int(family_entry["variant_count"])):
            levels.append(_build_level(seed, family_entry, family_index, variant_index))
    return {
        "suite_id": SUITE_ID_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "seed": int(seed),
        "level_tiers": _json_safe(LEVEL_TIERS_V1),
        "pressure_axes": _json_safe(PRESSURE_AXES_V1),
        "family_catalog": _json_safe(LEVEL_FAMILY_CATALOG_V1),
        "levels": levels,
        "generator_metadata": {
            "deterministic": True,
            "synthetic_only": True,
            "public_boundary_statement": "internal synthetic pressure testing only; not public ARC performance, not official scoring, not Kaggle readiness, not a benchmark result",
            "recommended_next_lane": "RUN_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_FROZEN_SOLVER_BASELINE_V1",
            "fallback_lane": "NARROW_ARC_UNKNOWN_ENGINE_LEVEL_LADDER_GENERATOR_TO_TIER_0_1_V1",
        },
        "boundary_flags": _base_packet_flags(),
    }


def summarize_arc_unknown_engine_level_ladder_v1(suite: Mapping[str, Any]) -> dict[str, Any]:
    levels = list(suite.get("levels", [])) if isinstance(suite, Mapping) else []
    family_ids = sorted({_safe_text(level.get("family_id")) for level in levels if isinstance(level, Mapping)})
    tier_ids = sorted({int(level.get("tier", -1)) for level in levels if isinstance(level, Mapping) and isinstance(level.get("tier"), int)})
    variants_by_family: dict[str, int] = {}
    for family in family_ids:
        variants_by_family[family] = len({
            _safe_text(level.get("variant_id"))
            for level in levels
            if isinstance(level, Mapping) and _safe_text(level.get("family_id")) == family
        })
    summary = {
        "suite_id": _safe_text(suite.get("suite_id")) if isinstance(suite, Mapping) else "",
        "level_count": len(levels),
        "family_count": len(family_ids),
        "families": family_ids,
        "represented_tier_count": len(LEVEL_TIERS_V1),
        "concrete_tier_count": len(tier_ids),
        "concrete_tiers": tier_ids,
        "variants_by_family": variants_by_family,
        "synthetic_only": bool(isinstance(suite, Mapping) and suite.get("boundary_flags", {}).get("synthetic_only") is True),
        "non_claim_safe": bool(isinstance(suite, Mapping) and suite.get("boundary_flags", {}).get("non_claim_safe") is True),
    }
    return to_arc_unknown_engine_level_ladder_json_safe_v1(summary)


def recommend_arc_unknown_engine_next_step_v1(prior_results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = [dict(item) for item in prior_results if isinstance(item, Mapping)]
    statuses = [_safe_text(item.get("solver_result")) for item in normalized]
    exact_count = statuses.count("exact")
    partial_count = statuses.count("partial")
    unsupported_count = statuses.count("unsupported")
    invalid_count = statuses.count("invalid")
    stable_success = bool(normalized) and all(status == "exact" for status in statuses)
    collapse = any(bool(item.get("small_variation_collapse")) for item in normalized)
    recent_tier = max([int(item.get("tier", 0)) for item in normalized if isinstance(item.get("tier"), int)] or [0])

    if invalid_count:
        mode = "boundary_diagnostics"
        action = "generate_boundary_diagnostics"
        next_tier = recent_tier
    elif unsupported_count:
        mode = "minimal_repro"
        action = "generate_minimal_repro_levels"
        next_tier = recent_tier
    elif partial_count >= 2:
        mode = "neighbor_levels"
        action = "classify_mismatch_and_generate_neighbors"
        next_tier = recent_tier
    elif collapse:
        mode = "overfit_frontier"
        action = "mark_overfit_frontier"
        next_tier = recent_tier
    elif stable_success and len(normalized) >= 2:
        mode = "unlock_next_tier"
        action = "increase_tier_after_stable_variations"
        next_tier = min(5, recent_tier + 1)
    else:
        mode = "increase_strangeness"
        action = "increase_strangeness_within_tier"
        next_tier = recent_tier

    return to_arc_unknown_engine_level_ladder_json_safe_v1(
        {
            "recommendation_mode": mode,
            "recommended_action": action,
            "next_tier": next_tier,
            "synthetic_only": True,
            "non_claim_safe": True,
        }
    )


def build_arc_unknown_engine_failure_forecast_v1(
    *,
    forecast_run_id: str,
    tier: int,
    level_family_id: str,
    pressure_axes: Sequence[str],
    prior_results: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    results = [dict(item) for item in (prior_results or []) if isinstance(item, Mapping)]
    statuses = [_safe_text(item.get("solver_result")) for item in results]
    last_status = statuses[-1] if statuses else "unknown"
    if "invalid" in statuses:
        failure_cause = "boundary_invalid_input_or_packet"
        recommendation = "review_grid_and_packet_boundaries"
        mode = "boundary_diagnostics"
    elif "unsupported" in statuses:
        failure_cause = "unsupported_reasoning_pattern"
        recommendation = "generate_minimal_repro_levels"
        mode = "minimal_repro"
    elif statuses.count("partial") >= 1:
        failure_cause = "mismatch_frontier_detected"
        recommendation = "classify_partial_mismatch_and_generate_neighbors"
        mode = "neighbor_levels"
    else:
        failure_cause = "forecast_only_no_failure_observed"
        recommendation = "increase_strangeness_within_safe_bounds"
        mode = "increase_strangeness"
    packet = {
        "forecast_run_id": _safe_text(forecast_run_id),
        "tier": int(tier),
        "level_family_id": _safe_text(level_family_id),
        "pressure_axes": list(pressure_axes),
        "frozen_solver_result": last_status,
        "likely_next_failure_family": _safe_text(level_family_id),
        "failure_cause": failure_cause,
        "evidence_from_played_levels": [
            {
                "level_id": _safe_text(item.get("level_id")),
                "solver_result": _safe_text(item.get("solver_result")),
                "tier": item.get("tier"),
            }
            for item in results
        ],
        "confidence_level": "bounded_medium" if results else "bounded_low",
        "recommended_bounded_intervention": recommendation,
        "recommendation_mode": mode,
        "non_claim_safe": True,
        "synthetic_only": True,
    }
    return to_arc_unknown_engine_level_ladder_json_safe_v1(packet)


def validate_arc_unknown_engine_level_ladder_v1(suite: Any) -> dict[str, Any]:
    violations: list[str] = []
    if not isinstance(suite, Mapping):
        return {"valid": False, "violations": ["suite_not_mapping"]}
    levels = suite.get("levels")
    if not isinstance(levels, list) or len(levels) < 12:
        violations.append("level_count_below_minimum")
    if len(LEVEL_FAMILY_CATALOG_V1) < 6:
        violations.append("family_count_below_minimum")
    reused = sorted(set(PREVIOUS_HELDOUT_FAMILIES_V1).intersection({entry["family_id"] for entry in LEVEL_FAMILY_CATALOG_V1}))
    if reused:
        violations.append("reused_previous_family_names")
    for level in levels or []:
        level_validation = validate_level_v1(level)
        if level_validation["valid"] is False:
            violations.extend(level_validation["violations"])
    return {"valid": not violations, "violations": sorted(set(violations))}
