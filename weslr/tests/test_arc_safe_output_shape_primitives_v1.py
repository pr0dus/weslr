from __future__ import annotations

import ast
import inspect
import json

from weslr.arc_style_grid_adapter_phase2 import (
    _construct_count_pattern_grid,
    _crop_to_non_background_bbox_grid,
    _place_object_on_new_canvas,
    _preserve_input_canvas_grid,
    validate_arc_style_train_pair_with_candidate_v1,
)
from weslr.arc_style_heldout_compositional_synthetic_generator import generate_arc_style_heldout_compositional_suite_v1
from weslr.arc_style_typed_primitive_signatures import build_arc_style_typed_primitive_signature_catalog_v1, validate_arc_style_typed_primitive_signature_v1

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


def test_new_v1_primitives_have_typed_signatures_and_reject_unsafe_metadata() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    for primitive_name in {
        "construct_count_pattern",
        "crop_to_non_background_bbox",
        "place_object_on_new_canvas",
        "preserve_input_canvas",
        "rotate_object_canvas",
    }:
        assert primitive_name in catalog
        assert validate_arc_style_typed_primitive_signature_v1(catalog[primitive_name])["valid"] is True

    mutated = dict(catalog["construct_count_pattern"])
    mutated["leakage_flags"] = dict(mutated["leakage_flags"], uses_provider_model_api=True)
    validation = validate_arc_style_typed_primitive_signature_v1(mutated)
    assert validation["valid"] is False
    assert any(label.startswith("unsafe_leakage_flag:") for label in validation["blocked_reason_labels"])


def test_construct_count_pattern_is_bounded_rectangular_and_fail_closed() -> None:
    grid = [[0, 0, 0], [0, 4, 0], [0, 4, 0]]
    assert _construct_count_pattern_grid(grid, count=None, pattern_value=5, background_value=0) == [[5]]
    assert _construct_count_pattern_grid(grid, count=26, pattern_value=5, background_value=0) == grid
    assert _construct_count_pattern_grid([[True, 0], [0, 0]], count=None, pattern_value=5, background_value=0) == [[True, 0], [0, 0]]
    assert _construct_count_pattern_grid([[0, 10], [0, 0]], count=None, pattern_value=5, background_value=0) == [[0, 10], [0, 0]]
    assert _construct_count_pattern_grid([[0, 0], [0]], count=None, pattern_value=5, background_value=0) == [[0, 0], [0]]


def test_crop_place_and_preserve_canvas_primitives_are_strict() -> None:
    cropped = _crop_to_non_background_bbox_grid([[0, 0, 0], [0, 4, 0], [0, 4, 0]], background_value=0)
    assert cropped == [[4], [4]]
    assert _crop_to_non_background_bbox_grid([[0, 0], [0, 0]], background_value=0) == [[0, 0], [0, 0]]
    assert _crop_to_non_background_bbox_grid([[True, 0], [0, 0]], background_value=0) == [[True, 0], [0, 0]]

    placed = _place_object_on_new_canvas(
        [[0, 0, 0], [0, 7, 7], [0, 0, 0]],
        canvas_height=4,
        canvas_width=4,
        background_value=0,
        anchor_row=1,
        anchor_column=1,
        object_value=7,
    )
    assert placed == [[0, 0, 0, 0], [0, 7, 7, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert _place_object_on_new_canvas([[0, 1, 0], [0, 2, 0]], canvas_height=3, canvas_width=3, background_value=0) == [[0, 1, 0], [0, 2, 0]]
    assert _place_object_on_new_canvas([[0, 0], [0, 0]], canvas_height=30, canvas_width=30, background_value=0) == [[0, 0], [0, 0]]

    preserved = _preserve_input_canvas_grid([[0, 1], [0, 0]], background_value=0)
    assert preserved == [[0, 1], [0, 0]]
    assert _preserve_input_canvas_grid([[0, 1], [0, 0]], background_value=9) == [[0, 1], [0, 0]]


def test_construct_count_pattern_candidate_uses_train_only_parameters_without_evaluation_output() -> None:
    suite = generate_arc_style_heldout_compositional_suite_v1(seed=20260625)
    task = next(task for task in suite["tasks"] if task["recipe_family_id"] == "count_object_then_emit_pattern")
    pair = task["task_packet"]["train_pairs"][0]
    background = pair["input_grid_metadata"]["background_color"]
    cleaned = _preserve_input_canvas_grid(pair["input_grid"], background_value=background)
    pattern_value = pair["output_grid"][0][0]
    candidate = {
        "candidate_id": "count-pattern-v1",
        "candidate_type": "count_pattern_candidate",
        "primitive_sequence": [
            {"primitive_id": "remove_background_noise", "parameters": {"background_value": background}},
            {"primitive_id": "construct_count_pattern", "parameters": {"pattern_value": pattern_value, "background_value": background, "row_index": 0}},
        ],
        "train_fit_status": "unknown",
        "partial_fit_metadata": {},
        "unsupported_assumptions": [],
        "rejection_reasons": [],
        "confidence_metadata": {},
        "calibration_metadata": {},
    }
    validation = validate_arc_style_train_pair_with_candidate_v1(pair, candidate)
    assert validation["exact_match"] is True
    assert validation["unsupported_candidate"] is False


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.tests.test_arc_safe_output_shape_primitives_v1", fromlist=["*"])
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
