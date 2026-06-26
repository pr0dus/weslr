"""WESLR ARC-style typed primitive signatures V1.

Design-only metadata helper for primitive signature catalogs, lookup, filtering,
summary, and JSON-safe export. This module does not implement solver runtime,
program search, held-out generators, public ARC/Kaggle ingestion, score claims,
provider/model/API calls, ChatResponder wiring, website/runtime wiring, or
`.weslr` writes.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "ArcStyleTypedPrimitiveSignaturesV1"
HELPER_TYPE_V1 = "arc_style_typed_primitive_signatures_v1"
METADATA_ONLY_IMPLEMENTATION_STATUS_V1 = "metadata_only"
ALLOWED_IMPLEMENTATION_STATUSES_V1 = (METADATA_ONLY_IMPLEMENTATION_STATUS_V1,)
EXPECTED_PRIMITIVE_NAMES_V1 = (
    "copy_grid",
    "recolor_symbol",
    "move_single_object",
    "fill_region",
    "complete_symmetry",
    "border_frame",
    "extract_largest_object",
    "remove_background_noise",
    "line_completion",
    "object_count_to_pattern",
    "construct_count_pattern",
    "crop_to_non_background_bbox",
    "place_object_on_new_canvas",
    "preserve_input_canvas",
    "rotate_object_canvas",
    "rotate_object_90",
    "reflect_object_horizontal_or_vertical",
)
REQUIRED_SIGNATURE_FIELDS_V1 = (
    "name",
    "primitive_id",
    "input_grid_constraints",
    "output_grid_constraints",
    "parameter_schema",
    "safe_parameter_proposal_families",
    "composability_tags",
    "shape_effects",
    "color_effects",
    "object_effects",
    "failure_behavior",
    "leakage_flags",
    "authority_flags",
    "scope_flags",
    "deterministic_identity",
    "implementation_status",
)
REQUIRED_LEAKAGE_FLAG_NAMES_V1 = (
    "uses_test_output_for_candidate_generation",
    "uses_solution_file",
    "uses_answer_key",
    "uses_task_id_for_candidate_selection",
    "uses_notes_for_candidate_selection",
    "uses_provider_model_api",
    "uses_public_arc_kaggle_data",
    "uses_runtime_website_chat_responder",
    "uses_benchmark_examples_or_solutions",
)
REQUIRED_AUTHORITY_FLAG_NAMES_V1 = (
    "execution_authority",
    "program_search_authority",
    "public_data_authority",
    "kaggle_ready_authority",
    "official_score_authority",
    "runtime_authority",
    "chat_responder_authority",
)
REQUIRED_SCOPE_FLAG_NAMES_V1 = ("metadata_only_helper",)


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
    return str(value)


def to_arc_style_typed_primitive_signatures_json_safe_v1(value: Any) -> Any:
    safe = _json_safe(value)
    json.dumps(safe, ensure_ascii=False, allow_nan=False)
    return safe


def _false_flag_mapping(names: tuple[str, ...]) -> dict[str, bool]:
    return {name: False for name in names}


def _signature_blueprints() -> dict[str, dict[str, Any]]:
    common_leakage_flags = _false_flag_mapping(REQUIRED_LEAKAGE_FLAG_NAMES_V1)
    common_authority_flags = _false_flag_mapping(REQUIRED_AUTHORITY_FLAG_NAMES_V1)
    common_scope_flags = {"metadata_only_helper": True}

    return {
        "copy_grid": {
            "name": "copy_grid",
            "primitive_id": "copy",
            "input_grid_constraints": ["rectangular", "stable_dimensions"],
            "output_grid_constraints": ["same_shape_as_input", "same_cell_values_as_input"],
            "parameter_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            "safe_parameter_proposal_families": ["identity"],
            "composability_tags": ["identity", "baseline", "copy"],
            "shape_effects": ["preserve_shape"],
            "color_effects": ["preserve_colors"],
            "object_effects": ["preserve_objects"],
            "failure_behavior": ["reject_if_grid_invalid"],
            "deterministic_identity": "copy_grid:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "recolor_symbol": {
            "name": "recolor_symbol",
            "primitive_id": "recolor",
            "input_grid_constraints": ["rectangular", "stable_palette", "train_delta_color_mapping_available"],
            "output_grid_constraints": ["same_shape_as_input", "preserve_object_layout"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "from_value": {"type": ["integer", "string"]},
                    "to_value": {"type": ["integer", "string"]},
                },
                "required": ["from_value", "to_value"],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["color_mapping"],
            "composability_tags": ["recolor", "color_transform", "symbol_transform"],
            "shape_effects": ["preserve_shape"],
            "color_effects": ["map_colors"],
            "object_effects": ["preserve_objects"],
            "failure_behavior": ["reject_if_train_delta_is_not_single_color_mapping"],
            "deterministic_identity": "recolor_symbol:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "move_single_object": {
            "name": "move_single_object",
            "primitive_id": "move",
            "input_grid_constraints": ["rectangular", "single_object_present", "background_known"],
            "output_grid_constraints": ["rectangular", "object_count_preserved", "background_preserved"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["up", "down", "left", "right", "up_left", "up_right", "down_left", "down_right"]},
                    "steps": {"type": "integer", "minimum": 1},
                    "object_value": {"type": ["integer", "string"]},
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": ["direction", "steps"],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["movement_vector"],
            "composability_tags": ["translate", "single_object", "position_effect"],
            "shape_effects": ["preserve_shape", "change_position"],
            "color_effects": ["preserve_colors"],
            "object_effects": ["move_object"],
            "failure_behavior": ["reject_if_multi_object_delta", "reject_if_non_translation_delta"],
            "deterministic_identity": "move_single_object:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "fill_region": {
            "name": "fill_region",
            "primitive_id": "fill_region",
            "input_grid_constraints": ["rectangular", "border_detectable", "interior_region_present"],
            "output_grid_constraints": ["rectangular", "interior_region_filled", "border_preserved"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "fill_value": {"type": ["integer", "string"]},
                    "border_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["region_fill"],
            "composability_tags": ["fill", "region", "completion"],
            "shape_effects": ["preserve_outer_shape", "fill_interior_region"],
            "color_effects": ["paint_region"],
            "object_effects": ["preserve_border", "change_interior"],
            "failure_behavior": ["reject_if_border_not_detected"],
            "deterministic_identity": "fill_region:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "complete_symmetry": {
            "name": "complete_symmetry",
            "primitive_id": "complete_symmetry",
            "input_grid_constraints": ["rectangular", "partial_symmetry_detectable"],
            "output_grid_constraints": ["rectangular", "symmetry_completed", "axis_consistent"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "axes": {"type": "array", "items": {"type": "string", "enum": ["horizontal", "vertical"]}, "minItems": 1},
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": ["axes"],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["symmetry_axis"],
            "composability_tags": ["symmetry", "mirror", "completion"],
            "shape_effects": ["preserve_extent", "mirror_completion"],
            "color_effects": ["copy_colors_to_mirrors"],
            "object_effects": ["complete_objects"],
            "failure_behavior": ["reject_if_axis_ambiguous"],
            "deterministic_identity": "complete_symmetry:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "border_frame": {
            "name": "border_frame",
            "primitive_id": "border_frame",
            "input_grid_constraints": ["rectangular", "frame_detectable"],
            "output_grid_constraints": ["rectangular", "border_emphasized", "interior_preserved_or_filled"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "frame_value": {"type": ["integer", "string"]},
                    "fill_entire_grid": {"type": "boolean"},
                    "thickness": {"type": "integer", "minimum": 1},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["border_frame"],
            "composability_tags": ["border", "frame", "region"],
            "shape_effects": ["preserve_outer_shape", "alter_border_cells"],
            "color_effects": ["paint_border"],
            "object_effects": ["frame_object"],
            "failure_behavior": ["reject_if_frame_not_detectable"],
            "deterministic_identity": "border_frame:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "extract_largest_object": {
            "name": "extract_largest_object",
            "primitive_id": "extract_largest_object",
            "input_grid_constraints": ["rectangular", "multiple_objects_detectable"],
            "output_grid_constraints": ["rectangular", "largest_object_preserved", "other_cells_backgrounded"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["object_selection"],
            "composability_tags": ["extract", "object_selection", "denoise"],
            "shape_effects": ["preserve_largest_object_shape", "remove_smaller_components"],
            "color_effects": ["preserve_object_color"],
            "object_effects": ["select_largest_object"],
            "failure_behavior": ["reject_if_largest_object_ambiguous"],
            "deterministic_identity": "extract_largest_object:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "remove_background_noise": {
            "name": "remove_background_noise",
            "primitive_id": "remove_background_noise",
            "input_grid_constraints": ["rectangular", "dominant_component_detectable"],
            "output_grid_constraints": ["rectangular", "dominant_component_preserved", "noise_removed"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["object_selection"],
            "composability_tags": ["denoise", "object_selection", "cleanup"],
            "shape_effects": ["preserve_dominant_shape"],
            "color_effects": ["preserve_dominant_color"],
            "object_effects": ["remove_noise_objects"],
            "failure_behavior": ["reject_if_dominant_component_ambiguous"],
            "deterministic_identity": "remove_background_noise:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "line_completion": {
            "name": "line_completion",
            "primitive_id": "line_completion",
            "input_grid_constraints": ["rectangular", "line_gap_detectable"],
            "output_grid_constraints": ["rectangular", "line_completed", "row_or_column_preserved"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "row_index": {"type": ["integer", "null"], "minimum": 0},
                    "line_value": {"type": ["integer", "string"]},
                    "background_value": {"type": ["integer", "string"]},
                    "span_start_column": {"type": ["integer", "null"], "minimum": 0},
                    "span_end_column": {"type": ["integer", "null"], "minimum": 0},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["line_completion"],
            "composability_tags": ["line", "completion", "span"],
            "shape_effects": ["preserve_grid_extent", "complete_line"],
            "color_effects": ["paint_line"],
            "object_effects": ["extend_line_object"],
            "failure_behavior": ["reject_if_line_gap_not_detectable"],
            "deterministic_identity": "line_completion:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "object_count_to_pattern": {
            "name": "object_count_to_pattern",
            "primitive_id": "object_count_to_pattern",
            "input_grid_constraints": ["rectangular", "count_signal_detectable"],
            "output_grid_constraints": ["rectangular", "pattern_length_matches_count"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "count": {"type": ["integer", "null"], "minimum": 0},
                    "pattern_value": {"type": ["integer", "string"]},
                    "row_index": {"type": ["integer", "null"], "minimum": 0},
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["count_encoding", "pattern_shape"],
            "composability_tags": ["count", "pattern", "encoding"],
            "shape_effects": ["emit_count_pattern"],
            "color_effects": ["paint_pattern"],
            "object_effects": ["encode_count_as_object_pattern"],
            "failure_behavior": ["reject_if_count_signal_ambiguous"],
            "deterministic_identity": "object_count_to_pattern:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "construct_count_pattern": {
            "name": "construct_count_pattern",
            "primitive_id": "construct_count_pattern",
            "input_grid_constraints": ["rectangular", "count_signal_detectable", "train_only_output_shape_proposal"],
            "output_grid_constraints": ["rectangular", "bounded_canvas", "pattern_length_matches_count", "background_explicit"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "count": {"type": ["integer", "null"], "minimum": 0},
                    "pattern_value": {"type": ["integer", "string"]},
                    "background_value": {"type": ["integer", "string"]},
                    "row_index": {"type": ["integer", "null"], "minimum": 0},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["count_encoding", "train_only_output_shape", "pattern_shape"],
            "composability_tags": ["count", "pattern", "canvas_construction", "train_only"],
            "shape_effects": ["construct_bounded_canvas", "emit_count_pattern"],
            "color_effects": ["paint_pattern", "preserve_background"],
            "object_effects": ["encode_count_as_pattern"],
            "failure_behavior": ["reject_if_count_ambiguous", "reject_if_output_shape_ambiguous"],
            "deterministic_identity": "construct_count_pattern:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "crop_to_non_background_bbox": {
            "name": "crop_to_non_background_bbox",
            "primitive_id": "crop_to_non_background_bbox",
            "input_grid_constraints": ["rectangular", "background_known_or_inferable", "tight_bbox_detectable"],
            "output_grid_constraints": ["rectangular", "tight_bbox_crop", "bounded_canvas"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["bbox_crop", "train_only_background"],
            "composability_tags": ["crop", "bbox", "shape_construction", "train_only"],
            "shape_effects": ["crop_to_tight_bbox"],
            "color_effects": ["preserve_non_background_colors"],
            "object_effects": ["preserve_object_extent"],
            "failure_behavior": ["reject_if_background_ambiguous", "reject_if_no_non_background_cells"],
            "deterministic_identity": "crop_to_non_background_bbox:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "place_object_on_new_canvas": {
            "name": "place_object_on_new_canvas",
            "primitive_id": "place_object_on_new_canvas",
            "input_grid_constraints": ["rectangular", "object_bbox_detectable", "train_only_canvas_shape_proposal", "train_only_background_proposal"],
            "output_grid_constraints": ["rectangular", "bounded_canvas", "object_placed", "background_explicit"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "canvas_height": {"type": ["integer", "null"], "minimum": 1},
                    "canvas_width": {"type": ["integer", "null"], "minimum": 1},
                    "background_value": {"type": ["integer", "string"]},
                    "anchor_row": {"type": ["integer", "null"], "minimum": 0},
                    "anchor_column": {"type": ["integer", "null"], "minimum": 0},
                    "object_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["canvas_placement", "train_only_canvas_shape", "train_only_background"],
            "composability_tags": ["place", "canvas", "shape_construction", "train_only"],
            "shape_effects": ["construct_bounded_canvas", "place_object"],
            "color_effects": ["preserve_object_colors", "preserve_background"],
            "object_effects": ["place_object_on_canvas"],
            "failure_behavior": ["reject_if_canvas_shape_ambiguous", "reject_if_placement_overflow", "reject_if_object_ambiguous"],
            "deterministic_identity": "place_object_on_new_canvas:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "preserve_input_canvas": {
            "name": "preserve_input_canvas",
            "primitive_id": "preserve_input_canvas",
            "input_grid_constraints": ["rectangular", "canvas_shape_detectable"],
            "output_grid_constraints": ["same_shape_as_input", "same_background_as_input"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["identity", "train_only_canvas_shape"],
            "composability_tags": ["canvas", "identity", "shape_preservation", "train_only"],
            "shape_effects": ["preserve_shape", "preserve_canvas"],
            "color_effects": ["preserve_colors"],
            "object_effects": ["preserve_objects"],
            "failure_behavior": ["reject_if_grid_invalid"],
            "deterministic_identity": "preserve_input_canvas:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "rotate_object_canvas": {
            "name": "rotate_object_canvas",
            "primitive_id": "rotate_object_canvas",
            "input_grid_constraints": ["rectangular", "bounded_palette_0_to_9", "no_bool_cells", "object_bbox_detectable", "train_only_parameter_proposal"],
            "output_grid_constraints": ["rectangular", "bounded_canvas", "background_preserved", "rotated_bbox_consistent", "deterministic_train_only_canvas_policy"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "angle": {"type": "integer", "enum": [90, 180, 270]},
                    "object_value": {"type": ["integer", "string"]},
                    "background_value": {"type": ["integer", "string"]},
                    "canvas_policy": {"type": "string", "enum": ["preserve_input_canvas", "rotate_input_canvas"]},
                    "anchor_policy": {"type": "string", "enum": ["same_anchor", "rotate_with_input_canvas", "explicit_anchor"]},
                    "canvas_height": {"type": ["integer", "null"], "minimum": 1},
                    "canvas_width": {"type": ["integer", "null"], "minimum": 1},
                    "anchor_row": {"type": ["integer", "null"], "minimum": 0},
                    "anchor_column": {"type": ["integer", "null"], "minimum": 0}
                },
                "required": ["angle"],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["rotation", "train_only_canvas_shape", "train_only_anchor"],
            "composability_tags": ["rotate", "canvas", "object_transform", "train_only"],
            "shape_effects": ["rotate_shape", "preserve_or_rotate_canvas"],
            "color_effects": ["preserve_colors", "preserve_background"],
            "object_effects": ["rotate_object", "place_object_on_canvas"],
            "failure_behavior": ["reject_if_grid_invalid", "reject_if_angle_unsupported", "reject_if_canvas_or_anchor_ambiguous", "reject_if_placement_overflow"],
            "deterministic_identity": "rotate_object_canvas:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "rotate_object_90": {
            "name": "rotate_object_90",
            "primitive_id": "rotate_object_90",
            "input_grid_constraints": ["rectangular", "object_bbox_detectable"],
            "output_grid_constraints": ["rectangular", "same_palette_or_subset", "rotated_bbox_consistent"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "object_value": {"type": ["integer", "string"]},
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": [],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["rotation"],
            "composability_tags": ["rotate", "object_transform", "orientation"],
            "shape_effects": ["rotate_shape_90"],
            "color_effects": ["preserve_colors"],
            "object_effects": ["rotate_object"],
            "failure_behavior": ["reject_if_bbox_not_detectable"],
            "deterministic_identity": "rotate_object_90:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
        "reflect_object_horizontal_or_vertical": {
            "name": "reflect_object_horizontal_or_vertical",
            "primitive_id": "reflect_object_horizontal_or_vertical",
            "input_grid_constraints": ["rectangular", "object_bbox_detectable", "axis_candidate_detectable"],
            "output_grid_constraints": ["rectangular", "same_palette_or_subset", "reflected_bbox_consistent"],
            "parameter_schema": {
                "type": "object",
                "properties": {
                    "axis": {"type": "string", "enum": ["horizontal", "vertical"]},
                    "object_value": {"type": ["integer", "string"]},
                    "background_value": {"type": ["integer", "string"]},
                },
                "required": ["axis"],
                "additionalProperties": False,
            },
            "safe_parameter_proposal_families": ["reflection"],
            "composability_tags": ["reflect", "object_transform", "orientation"],
            "shape_effects": ["reflect_shape"],
            "color_effects": ["preserve_colors"],
            "object_effects": ["reflect_object"],
            "failure_behavior": ["reject_if_axis_ambiguous"],
            "deterministic_identity": "reflect_object_horizontal_or_vertical:v1",
            "implementation_status": METADATA_ONLY_IMPLEMENTATION_STATUS_V1,
        },
    }


_DEF_SIGNATURE_BLUEPRINTS_V1 = _signature_blueprints()


def _build_signature(name: str, blueprint: Mapping[str, Any]) -> dict[str, Any]:
    signature = {
        **deepcopy(dict(blueprint)),
        "name": name,
        "leakage_flags": _false_flag_mapping(REQUIRED_LEAKAGE_FLAG_NAMES_V1),
        "authority_flags": _false_flag_mapping(REQUIRED_AUTHORITY_FLAG_NAMES_V1),
        "scope_flags": {"metadata_only_helper": True},
    }
    signature.setdefault("primitive_id", name)
    return signature


def build_arc_style_typed_primitive_signature_catalog_v1() -> dict[str, dict[str, Any]]:
    return {name: _build_signature(name, blueprint) for name, blueprint in sorted(_DEF_SIGNATURE_BLUEPRINTS_V1.items())}


def _contains_callable(value: Any) -> bool:
    if callable(value):
        return True
    if isinstance(value, Mapping):
        return any(_contains_callable(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_callable(item) for item in value)
    return False


def _missing_required_fields(signature: Mapping[str, Any]) -> list[str]:
    return [field for field in REQUIRED_SIGNATURE_FIELDS_V1 if field not in signature]


def validate_arc_style_typed_primitive_signature_v1(signature: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "name": None,
        "primitive_id": None,
        "blocked_reason_labels": [],
    }
    if not isinstance(signature, Mapping):
        result["blocked_reason_labels"].append("signature_not_mapping")
        return result

    result["name"] = signature.get("name")
    result["primitive_id"] = signature.get("primitive_id")
    missing = _missing_required_fields(signature)
    if missing:
        result["blocked_reason_labels"].append("missing_required_fields")
        result["blocked_reason_labels"].extend(f"missing:{field}" for field in missing)
        return result

    name = signature.get("name")
    if not isinstance(name, str) or not name:
        result["blocked_reason_labels"].append("missing_or_invalid_name")
        return result
    if name not in EXPECTED_PRIMITIVE_NAMES_V1:
        result["blocked_reason_labels"].append("unknown_primitive_name")
        return result

    if _contains_callable(signature):
        result["blocked_reason_labels"].append("callable_value_disallowed")
        return result

    parameter_schema = signature.get("parameter_schema")
    if not isinstance(parameter_schema, Mapping):
        result["blocked_reason_labels"].append("parameter_schema_not_mapping")
        return result

    for field_name in ("input_grid_constraints", "output_grid_constraints", "safe_parameter_proposal_families", "composability_tags", "shape_effects", "color_effects", "object_effects", "failure_behavior"):
        value = signature.get(field_name)
        if not isinstance(value, (list, tuple)) or len(value) == 0:
            result["blocked_reason_labels"].append(f"{field_name}_invalid")
            return result

    leakage_flags = signature.get("leakage_flags")
    if not isinstance(leakage_flags, Mapping):
        result["blocked_reason_labels"].append("leakage_flags_not_mapping")
        return result
    for flag_name in REQUIRED_LEAKAGE_FLAG_NAMES_V1:
        if flag_name not in leakage_flags:
            result["blocked_reason_labels"].append(f"missing_leakage_flag:{flag_name}")
            return result
        if bool(leakage_flags.get(flag_name)):
            result["blocked_reason_labels"].append(f"unsafe_leakage_flag:{flag_name}")
            return result

    authority_flags = signature.get("authority_flags")
    if not isinstance(authority_flags, Mapping):
        result["blocked_reason_labels"].append("authority_flags_not_mapping")
        return result
    for flag_name in REQUIRED_AUTHORITY_FLAG_NAMES_V1:
        if flag_name not in authority_flags:
            result["blocked_reason_labels"].append(f"missing_authority_flag:{flag_name}")
            return result
        if bool(authority_flags.get(flag_name)):
            result["blocked_reason_labels"].append(f"unsafe_authority_flag:{flag_name}")
            return result

    scope_flags = signature.get("scope_flags")
    if not isinstance(scope_flags, Mapping):
        result["blocked_reason_labels"].append("scope_flags_not_mapping")
        return result
    for flag_name in REQUIRED_SCOPE_FLAG_NAMES_V1:
        if flag_name not in scope_flags:
            result["blocked_reason_labels"].append(f"missing_scope_flag:{flag_name}")
            return result
    if not bool(scope_flags.get("metadata_only_helper")):
        result["blocked_reason_labels"].append("metadata_only_helper_must_be_true")
        return result

    deterministic_identity = signature.get("deterministic_identity")
    if not isinstance(deterministic_identity, str) or not deterministic_identity:
        result["blocked_reason_labels"].append("missing_deterministic_identity")
        return result

    implementation_status = signature.get("implementation_status")
    if implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES_V1:
        result["blocked_reason_labels"].append("invalid_implementation_status")
        return result

    result["valid"] = True
    return result


def validate_arc_style_typed_primitive_signature_catalog_v1(catalog: Any) -> dict[str, Any]:
    result = {
        "valid": False,
        "primitive_names": [],
        "blocked_reason_labels": [],
    }
    if not isinstance(catalog, Mapping):
        result["blocked_reason_labels"].append("catalog_not_mapping")
        return result
    catalog_names = sorted(str(name) for name in catalog.keys())
    result["primitive_names"] = catalog_names
    unknown_names = [name for name in catalog_names if name not in EXPECTED_PRIMITIVE_NAMES_V1]
    missing_names = [name for name in EXPECTED_PRIMITIVE_NAMES_V1 if name not in catalog]
    if unknown_names:
        result["blocked_reason_labels"].append("unknown_primitive_name")
        result["blocked_reason_labels"].extend(f"unknown:{name}" for name in unknown_names)
    if missing_names:
        result["blocked_reason_labels"].append("missing_expected_primitives")
        result["blocked_reason_labels"].extend(f"missing:{name}" for name in missing_names)
    for name in EXPECTED_PRIMITIVE_NAMES_V1:
        if name in catalog:
            validation = validate_arc_style_typed_primitive_signature_v1(catalog[name])
            if not validation["valid"]:
                result["blocked_reason_labels"].append(f"invalid_signature:{name}")
                result["blocked_reason_labels"].extend(validation["blocked_reason_labels"])
    if not result["blocked_reason_labels"]:
        result["valid"] = True
    return result


def get_arc_style_typed_primitive_signature_v1(primitive_name: str, catalog: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    active_catalog = catalog if catalog is not None else build_arc_style_typed_primitive_signature_catalog_v1()
    signature = active_catalog.get(primitive_name) if isinstance(active_catalog, Mapping) else None
    return deepcopy(signature) if isinstance(signature, Mapping) else None


def list_arc_style_typed_primitive_signatures_v1(catalog: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    active_catalog = catalog if catalog is not None else build_arc_style_typed_primitive_signature_catalog_v1()
    if not isinstance(active_catalog, Mapping):
        return []
    return [deepcopy(active_catalog[name]) for name in sorted(active_catalog) if isinstance(active_catalog.get(name), Mapping)]


def _filter_signatures_by_field_value(field_name: str, value: str, catalog: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    signatures = list_arc_style_typed_primitive_signatures_v1(catalog)
    filtered: list[dict[str, Any]] = []
    for signature in signatures:
        items = signature.get(field_name, [])
        if isinstance(items, (list, tuple)) and value in items:
            filtered.append(signature)
    return filtered


def filter_arc_style_typed_primitive_signatures_by_composability_tag_v1(tag: str, catalog: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    return _filter_signatures_by_field_value("composability_tags", tag, catalog)


def filter_arc_style_typed_primitive_signatures_by_shape_effect_v1(effect: str, catalog: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    return _filter_signatures_by_field_value("shape_effects", effect, catalog)


def filter_arc_style_typed_primitive_signatures_by_color_effect_v1(effect: str, catalog: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    return _filter_signatures_by_field_value("color_effects", effect, catalog)


def filter_arc_style_typed_primitive_signatures_by_object_effect_v1(effect: str, catalog: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    return _filter_signatures_by_field_value("object_effects", effect, catalog)


def summarize_arc_style_typed_primitive_signatures_v1(catalog: Mapping[str, Any] | None = None) -> dict[str, Any]:
    signatures = list_arc_style_typed_primitive_signatures_v1(catalog)
    tag_counts: dict[str, int] = {}
    shape_counts: dict[str, int] = {}
    color_counts: dict[str, int] = {}
    object_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for signature in signatures:
        status = str(signature.get("implementation_status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
        for field_name, counts in (
            ("composability_tags", tag_counts),
            ("shape_effects", shape_counts),
            ("color_effects", color_counts),
            ("object_effects", object_counts),
        ):
            for item in signature.get(field_name, []):
                text = str(item)
                counts[text] = counts.get(text, 0) + 1
    summary = {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "signature_count": len(signatures),
        "primitive_names": [signature["name"] for signature in signatures],
        "implementation_status_counts": {key: status_counts[key] for key in sorted(status_counts)},
        "composability_tag_counts": {key: tag_counts[key] for key in sorted(tag_counts)},
        "shape_effect_counts": {key: shape_counts[key] for key in sorted(shape_counts)},
        "color_effect_counts": {key: color_counts[key] for key in sorted(color_counts)},
        "object_effect_counts": {key: object_counts[key] for key in sorted(object_counts)},
        "metadata_only_helper": True,
        "design_guarded": True,
        "public_data_ready": False,
        "kaggle_ready": False,
        "execution_authority": False,
        "program_search_authority": False,
        "official_score_authority": False,
    }
    return summary


__all__ = [
    "ALLOWED_IMPLEMENTATION_STATUSES_V1",
    "EXPECTED_PRIMITIVE_NAMES_V1",
    "HELPER_TYPE_V1",
    "METADATA_ONLY_IMPLEMENTATION_STATUS_V1",
    "REQUIRED_AUTHORITY_FLAG_NAMES_V1",
    "REQUIRED_LEAKAGE_FLAG_NAMES_V1",
    "REQUIRED_SCOPE_FLAG_NAMES_V1",
    "REQUIRED_SIGNATURE_FIELDS_V1",
    "SCHEMA_VERSION_V1",
    "build_arc_style_typed_primitive_signature_catalog_v1",
    "filter_arc_style_typed_primitive_signatures_by_color_effect_v1",
    "filter_arc_style_typed_primitive_signatures_by_composability_tag_v1",
    "filter_arc_style_typed_primitive_signatures_by_object_effect_v1",
    "filter_arc_style_typed_primitive_signatures_by_shape_effect_v1",
    "get_arc_style_typed_primitive_signature_v1",
    "list_arc_style_typed_primitive_signatures_v1",
    "summarize_arc_style_typed_primitive_signatures_v1",
    "to_arc_style_typed_primitive_signatures_json_safe_v1",
    "validate_arc_style_typed_primitive_signature_catalog_v1",
    "validate_arc_style_typed_primitive_signature_v1",
]
