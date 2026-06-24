from __future__ import annotations

import ast
import inspect
import json
from typing import Any

from weslr.arc_style_grid_adapter_phase2 import (
    ADAPTER_TYPE_V1,
    DEFERRED_PRIMITIVE_IDS_V1,
    PRIMITIVE_CATEGORIES_V1,
    SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1,
    build_arc_style_phase2_adapter_packet_v1,
    build_arc_style_primitive_registry_v1,
    extract_arc_style_object_candidates_v1,
    summarize_arc_style_phase2_adapter_packet_v1,
    to_arc_style_phase2_adapter_json_safe_v1,
    validate_arc_style_phase2_adapter_packet_v1,
    validate_arc_style_train_pair_with_candidate_v1,
)
from weslr.arc_style_grid_schema_helpers import (
    TASK_SOURCE_INTERNAL_SYNTHETIC_V1,
    TOY_TASK_TYPES_V1,
    build_arc_style_grid_task_packet_v1,
    build_arc_style_grid_train_pair_v1,
    build_internal_arc_style_grid_toy_tasks_v1,
    to_arc_style_grid_task_json_safe_v1,
    validate_arc_style_grid_task_packet_v1,
)

FORBIDDEN_IMPORT_FRAGMENTS = (
    "provider",
    "payment",
    "chat_responder",
    "respond_chat",
    "openai",
    "anthropic",
    "google",
    "ollama",
)


def _json_safe(value: Any) -> dict[str, Any]:
    safe = to_arc_style_phase2_adapter_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def test_primitive_registry_includes_all_required_categories() -> None:
    registry = build_arc_style_primitive_registry_v1()
    categories = {entry["category"] for entry in registry}
    assert categories == set(PRIMITIVE_CATEGORIES_V1)
    assert len(registry) == len(PRIMITIVE_CATEGORIES_V1)


def test_primitive_entries_are_json_safe_and_shape_complete() -> None:
    registry = build_arc_style_primitive_registry_v1()
    for entry in registry:
        assert set(entry.keys()) >= {
            "primitive_id",
            "category",
            "description",
            "required_inputs",
            "allowed_assumptions",
            "failure_mode_labels",
            "bounded_depth_allowed",
            "is_executable_now",
        }
        assert json.dumps(_json_safe(entry), ensure_ascii=False)


def test_executable_and_deferred_primitive_flags_are_clear() -> None:
    registry = build_arc_style_primitive_registry_v1()
    executable = {entry["primitive_id"] for entry in registry if entry["is_executable_now"] is True}
    deferred = {entry["primitive_id"] for entry in registry if entry["is_executable_now"] is False}
    assert executable == set(SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1)
    assert deferred == set(DEFERRED_PRIMITIVE_IDS_V1)


def test_connected_components_color_groups_and_bounding_boxes_are_extracted() -> None:
    packet = extract_arc_style_object_candidates_v1([[0, 1, 1], [0, 1, 0], [2, 2, 0]], task_id="object-test")
    object_candidates = packet["object_candidates"]
    assert any(candidate["object_type"] == "connected_component" for candidate in object_candidates)
    assert any(candidate["object_type"] == "background_candidate" for candidate in object_candidates)
    assert packet["trace"]["connected_component_count"] >= 2
    comp = next(candidate for candidate in object_candidates if candidate["object_type"] == "connected_component" and candidate["value"] == 1)
    assert comp["bounding_box"] == [0, 1, 1, 2]
    assert comp["size"] == 3
    assert packet["color_group_candidates"]
    assert {candidate["value"] for candidate in packet["color_group_candidates"]} == {0, 1, 2}


def test_background_candidate_and_border_hint_are_traced() -> None:
    toy_task = next(task for task in build_internal_arc_style_grid_toy_tasks_v1() if task["trace"]["toy_task_type"] == "border_frame_fill")
    extraction = extract_arc_style_object_candidates_v1(toy_task["test_input"], task_id=toy_task["task_id"])
    assert any(candidate["object_type"] == "background_candidate" for candidate in extraction["object_candidates"])
    assert extraction["trace"]["background_value"] is not None
    assert extraction["border_frame_hints"]
    assert all(candidate["object_type"] == "border_frame_hint" for candidate in extraction["border_frame_hints"])


def test_symmetry_hints_are_candidate_based_and_not_overclaimed() -> None:
    extraction = extract_arc_style_object_candidates_v1([[0, 1, 0], [2, 0, 3], [0, 1, 0]], task_id="symmetry-check")
    for hint in extraction["symmetry_hints"]:
        assert hint["object_type"] == "symmetry_hint"
        assert hint["confidence_metadata"]["confidence"] in {"low", "medium", "high"}
    if extraction["symmetry_hints"]:
        assert all(hint["confidence_metadata"]["reason"] for hint in extraction["symmetry_hints"])


def test_train_pair_exact_match_works_for_copy_toy_task() -> None:
    pair = build_arc_style_grid_train_pair_v1("copy-pair", [[1, 2], [3, 4]], [[1, 2], [3, 4]], "copy")
    candidate = {
        "candidate_id": "copy-candidate",
        "candidate_type": "copy_candidate",
        "primitive_sequence": [{"primitive_id": "copy", "parameters": {}}],
        "train_fit_status": "unknown",
        "partial_fit_metadata": {},
        "unsupported_assumptions": [],
        "rejection_reasons": [],
        "confidence_metadata": {},
        "calibration_metadata": {},
    }
    validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
    assert validation["exact_match"] is True
    assert validation["mismatch_category"] == "exact_match"
    assert validation["unsupported_candidate"] is False


def test_recolor_move_symmetry_and_border_toy_tasks_validate_or_mark_unsupported() -> None:
    tasks = build_internal_arc_style_grid_toy_tasks_v1()
    by_type = {task["trace"]["toy_task_type"]: task for task in tasks}
    for task_type in TOY_TASK_TYPES_V1:
        task = by_type[task_type]
        pair = task["train_pairs"][0]
        candidate = build_arc_style_phase2_adapter_packet_v1([task])["task_packets"][0]["train_pair_validations"][0]
        assert candidate["pair_id"] == pair["pair_id"]
        assert candidate["candidate_id"]
        assert candidate["exact_match"] is True or candidate["unsupported_candidate"] is True
        if candidate["unsupported_candidate"]:
            assert candidate["mismatch_category"] == "unsupported_candidate"
        else:
            assert candidate["mismatch_category"] == "exact_match"


def test_unsupported_primitive_is_not_falsely_marked_solved() -> None:
    pair = build_arc_style_grid_train_pair_v1("rotate-pair", [[1, 0], [0, 1]], [[0, 1], [1, 0]], "rotate")
    candidate = {
        "candidate_id": "rotate-candidate",
        "candidate_type": "rotate_candidate",
        "primitive_sequence": [{"primitive_id": "rotate", "parameters": {"angle": 90}}],
        "train_fit_status": "unknown",
        "partial_fit_metadata": {},
        "unsupported_assumptions": [],
        "rejection_reasons": [],
        "confidence_metadata": {},
        "calibration_metadata": {},
    }
    validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
    assert validation["unsupported_candidate"] is True
    assert validation["exact_match"] is False
    assert validation["mismatch_category"] == "unsupported_candidate"


def test_validator_mismatch_categories_are_stable() -> None:
    pair = build_arc_style_grid_train_pair_v1("mismatch-pair", [[1, 1], [1, 1]], [[1, 1], [1, 0]], "copy")
    candidate = {
        "candidate_id": "copy-candidate",
        "candidate_type": "copy_candidate",
        "primitive_sequence": [{"primitive_id": "copy", "parameters": {}}],
        "train_fit_status": "unknown",
        "partial_fit_metadata": {},
        "unsupported_assumptions": [],
        "rejection_reasons": [],
        "confidence_metadata": {},
        "calibration_metadata": {},
    }
    validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
    assert validation["mismatch_category"] in {"cell_values_mismatch", "exact_match"}
    assert validation["failure_localization"]["mismatch_cells"]


def test_full_phase2_packet_is_json_safe_and_internal_only() -> None:
    packet = build_arc_style_phase2_adapter_packet_v1()
    safe = _json_safe(packet)
    assert packet["adapter_type"] == ADAPTER_TYPE_V1
    assert packet["phase_number"] == 2
    assert packet["toy_task_count"] == 5
    assert len(packet["task_packets"]) == 5
    assert all(task["task_source"] == TASK_SOURCE_INTERNAL_SYNTHETIC_V1 for task in packet["task_packets"])
    assert all(task["task_trace"]["internal_synthetic_only"] is True for task in packet["task_packets"])
    assert all(task["toy_task_type"] in TOY_TASK_TYPES_V1 for task in packet["task_packets"])
    assert json.dumps(safe, ensure_ascii=False)


def test_phase2_adapter_validation_and_summary_work() -> None:
    packet = build_arc_style_phase2_adapter_packet_v1()
    validation = validate_arc_style_phase2_adapter_packet_v1(packet)
    summary = summarize_arc_style_phase2_adapter_packet_v1(packet)
    assert validation["valid"] is True
    assert summary["toy_task_count"] == 5
    assert summary["executable_primitive_count"] == len(SUPPORTED_EXECUTABLE_PRIMITIVE_IDS_V1)
    assert summary["deferred_primitive_count"] == len(DEFERRED_PRIMITIVE_IDS_V1)
    assert summary["valid"] is True


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_grid_adapter_phase2", fromlist=["*"])
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    forbidden = {
        fragment
        for fragment in FORBIDDEN_IMPORT_FRAGMENTS
        if fragment in imported_modules or any(fragment in mod for mod in imported_modules)
    }
    assert forbidden == set()
    assert "respond_chat" not in source
    assert "chat_responder" not in source
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
