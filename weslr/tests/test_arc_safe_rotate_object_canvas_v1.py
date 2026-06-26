from __future__ import annotations

import ast
import inspect
import json

from weslr.arc_style_depth2_compositional_program_search import run_arc_style_depth2_compositional_program_search_v1
from weslr.arc_style_grid_adapter_phase2 import _apply_primitive_step, _rotate_object_canvas_grid
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


def test_rotate_object_canvas_signature_is_present_and_safe() -> None:
    catalog = build_arc_style_typed_primitive_signature_catalog_v1()
    signature = catalog["rotate_object_canvas"]
    assert validate_arc_style_typed_primitive_signature_v1(signature)["valid"] is True
    assert signature["parameter_schema"]["properties"]["angle"]["enum"] == [90, 180, 270]
    assert "train_only_anchor" in signature["safe_parameter_proposal_families"]


def test_rotate_object_canvas_rotates_bbox_and_preserves_input_canvas_by_default() -> None:
    grid = [
        [0, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
    ]
    rotated, reason = _rotate_object_canvas_grid(
        grid,
        angle=90,
        background_value=0,
        object_value=1,
        canvas_policy="preserve_input_canvas",
        anchor_policy="same_anchor",
    )
    assert reason is None
    assert rotated == [
        [0, 1, 1, 1],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
    ]


def test_rotate_object_canvas_supports_bounded_rotated_canvas_anchor_policy() -> None:
    grid = [
        [0, 2, 2],
        [0, 2, 0],
    ]
    rotated, reason = _rotate_object_canvas_grid(
        grid,
        angle=90,
        background_value=0,
        object_value=2,
        canvas_policy="rotate_input_canvas",
        anchor_policy="rotate_with_input_canvas",
    )
    assert reason is None
    assert rotated == [
        [0, 0],
        [2, 2],
        [0, 2],
    ]


def test_rotate_object_canvas_rejects_invalid_grid_bool_cells_and_overflow() -> None:
    invalid_grid, invalid_reason = _rotate_object_canvas_grid([[True, 0], [0, 0]], angle=90, background_value=0, object_value=1)
    assert invalid_grid == [[True, 0], [0, 0]]
    assert invalid_reason == "invalid_grid"

    color_grid, color_reason = _rotate_object_canvas_grid([[0, 10], [0, 0]], angle=90, background_value=0, object_value=10)
    assert color_grid == [[0, 10], [0, 0]]
    assert color_reason == "invalid_grid"

    overflow_grid, overflow_reason = _rotate_object_canvas_grid(
        [[0, 3, 3], [0, 3, 0]],
        angle=90,
        background_value=0,
        object_value=3,
        canvas_policy="preserve_input_canvas",
        anchor_policy="explicit_anchor",
        anchor_row=1,
        anchor_column=2,
    )
    assert overflow_grid == [[0, 3, 3], [0, 3, 0]]
    assert overflow_reason == "placement_overflow"


def test_rotate_then_recolor_heldout_family_now_solves_with_rotate_object_canvas() -> None:
    result = run_arc_style_depth2_compositional_program_search_v1(seed=20260625)
    rotate_rows = [row for row in result["heldout_task_results"] if row["recipe_family_id"] == "rotate_then_recolor"]
    assert len(rotate_rows) == 2
    assert all(row["heldout_fit_status"] == "fit" for row in rotate_rows)
    assert all(
        "rotate_object_canvas" in row["selected_top2_program_packet"]["attempts"][0]["metadata"]["candidate_program_id"]
        for row in rotate_rows
    )


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.tests.test_arc_safe_rotate_object_canvas_v1", fromlist=["*"])
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
    assert json.dumps({"ok": True})
