"""Tests for ARC primitive sequence to grid reconstruction V1.

Tests that the reconstruction helper correctly materializes predicted grids
from primitive sequences for the 5 dry-run toy tasks.
"""

from __future__ import annotations

import pytest

from weslr.arc_style_grid_solver_dry_run import run_arc_style_bounded_solver_dry_run_v1
from weslr.arc_primitive_sequence_grid_reconstruction import (
    apply_primitive_sequence_to_grid_v1,
    validate_reconstructed_grid_v1,
    SUPPORTED_PRIMITIVE_IDS_V1,
    SCHEMA_VERSION_V1,
)


def test_reconstruction_schema_version():
    """Helper has correct schema version."""
    assert SCHEMA_VERSION_V1 == "ArcPrimitiveSequenceGridReconstructionV1"


def test_supported_primitive_ids_includes_dry_run_primitives():
    """Supported primitives include all dry-run selected primitives."""
    dry_run_primitives = {"copy", "recolor", "move", "complete_symmetry", "fill"}
    for primitive_id in dry_run_primitives:
        assert primitive_id in SUPPORTED_PRIMITIVE_IDS_V1


def _get_input_grid_from_task(task_result):
    """Extract input grid from task result's trace or reconstruct from task packet."""
    # Try trace first
    trace = task_result.get("trace", {})
    if "input_grid" in trace:
        return trace["input_grid"]
    # Fall back to extracting from train_pairs in task packet
    task_id = task_result.get("task_id")
    from weslr.arc_style_grid_schema_helpers import build_internal_arc_style_grid_toy_tasks_v1
    tasks = build_internal_arc_style_grid_toy_tasks_v1()
    for t in tasks:
        if t.get("task_id") == task_id:
            pairs = t.get("train_pairs", [])
            if pairs:
                return pairs[0].get("input_grid", [])
    return None


def test_reconstruct_toy_copy_grid():
    """Reconstruct toy_copy_grid_v1 task."""
    result = run_arc_style_bounded_solver_dry_run_v1()
    toy_task = next(tr for tr in result.get("task_results", []) if tr.get("task_id") == "toy_copy_grid_v1")
    input_grid = _get_input_grid_from_task(toy_task)
    primitive_sequence = toy_task["selected_primitive_sequence"]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["reconstruction_success"] is True
    assert rec["reconstructed_grid"] is not None


def test_reconstruct_toy_recolor_symbol():
    """Reconstruct toy_recolor_symbol_v1 task."""
    result = run_arc_style_bounded_solver_dry_run_v1()
    toy_task = next(tr for tr in result.get("task_results", []) if tr.get("task_id") == "toy_recolor_symbol_v1")
    input_grid = _get_input_grid_from_task(toy_task)
    primitive_sequence = toy_task["selected_primitive_sequence"]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["reconstruction_success"] is True
    assert rec["reconstructed_grid"] is not None


def test_reconstruct_toy_move_single_object():
    """Reconstruct toy_move_single_object_v1 task."""
    result = run_arc_style_bounded_solver_dry_run_v1()
    toy_task = next(tr for tr in result.get("task_results", []) if tr.get("task_id") == "toy_move_single_object_v1")
    input_grid = _get_input_grid_from_task(toy_task)
    primitive_sequence = toy_task["selected_primitive_sequence"]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["reconstruction_success"] is True
    assert rec["reconstructed_grid"] is not None


def test_reconstruct_toy_complete_symmetry():
    """Reconstruct toy_complete_symmetry_v1 task."""
    result = run_arc_style_bounded_solver_dry_run_v1()
    toy_task = next(tr for tr in result.get("task_results", []) if tr.get("task_id") == "toy_complete_symmetry_v1")
    input_grid = _get_input_grid_from_task(toy_task)
    primitive_sequence = toy_task["selected_primitive_sequence"]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["reconstruction_success"] is True
    assert rec["reconstructed_grid"] is not None


def test_reconstruct_toy_border_frame_fill():
    """Reconstruct toy_border_frame_fill_v1 task."""
    result = run_arc_style_bounded_solver_dry_run_v1()
    toy_task = next(tr for tr in result.get("task_results", []) if tr.get("task_id") == "toy_border_frame_fill_v1")
    input_grid = _get_input_grid_from_task(toy_task)
    primitive_sequence = toy_task["selected_primitive_sequence"]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["reconstruction_success"] is True
    assert rec["reconstructed_grid"] is not None


def test_all_5_dry_run_tasks_reconstruct():
    """All 5 dry-run toy tasks reconstruct successfully."""
    result = run_arc_style_bounded_solver_dry_run_v1()
    for toy_task in result.get("task_results", [])[:5]:
        input_grid = _get_input_grid_from_task(toy_task)
        primitive_sequence = toy_task["selected_primitive_sequence"]
        rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
        assert rec["reconstruction_success"] is True, f"Failed on {toy_task.get('task_id')}: {rec.get('failure_reason')}"
        assert rec["reconstructed_grid"] is not None


def test_unsupported_primitive_fails_closed():
    """Unsupported primitive fails closed."""
    input_grid = [[0, 1], [1, 0]]
    primitive_sequence = [{"primitive_id": "unsupported_primitive", "parameters": {}}]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["reconstruction_success"] is False
    assert "unsupported_primitive" in rec["failure_reason"]


def test_empty_primitive_sequence_fails_closed():
    """Empty primitive sequence fails closed."""
    input_grid = [[0, 1], [1, 0]]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, [])
    assert rec["reconstruction_success"] is False
    assert rec["failure_reason"] == "empty_primitive_sequence"


def test_invalid_input_grid_fails_closed():
    """Invalid input grid fails closed."""
    rec = apply_primitive_sequence_to_grid_v1("not_a_grid", [{"primitive_id": "copy", "parameters": {}}])
    assert rec["reconstruction_success"] is False
    assert rec["failure_reason"] == "invalid_input_grid"


def test_input_grid_not_mutated():
    """Input grid is not mutated by reconstruction."""
    input_grid = [[0, 1], [1, 0]]
    original = [row[:] for row in input_grid]
    primitive_sequence = [{"primitive_id": "recolor", "parameters": {"from_value": 1, "to_value": 2}}]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert input_grid == original


def test_validation_valid_result():
    """Validation passes for valid reconstruction result."""
    rec = {
        "reconstructed_grid": [[1, 2], [3, 4]],
        "reconstruction_success": True,
        "failure_reason": None,
        "provenance": "primitive_sequence_reconstruction",
        "schema_version": SCHEMA_VERSION_V1,
    }
    validation = validate_reconstructed_grid_v1(rec)
    assert validation["valid"] is True


def test_validation_missing_fields():
    """Validation fails for missing fields."""
    rec = {"reconstructed_grid": [[1, 2]]}
    validation = validate_reconstructed_grid_v1(rec)
    assert validation["valid"] is False
    assert len(validation["blocked_reason_labels"]) > 0


def test_validation_invalid_grid():
    """Validation fails when reconstruction success but grid invalid."""
    rec = {
        "reconstructed_grid": "not_a_grid",
        "reconstruction_success": True,
        "failure_reason": None,
        "provenance": "primitive_sequence_reconstruction",
        "schema_version": SCHEMA_VERSION_V1,
    }
    validation = validate_reconstructed_grid_v1(rec)
    assert validation["valid"] is False


def test_provenance_is_primitive_sequence_reconstruction():
    """Provenance field correctly set."""
    result = run_arc_style_bounded_solver_dry_run_v1()
    toy_task = result["task_results"][0]
    input_grid = _get_input_grid_from_task(toy_task)
    primitive_sequence = toy_task["selected_primitive_sequence"]
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["provenance"] == "primitive_sequence_reconstruction"


def test_no_expected_output_passed():
    """Reconstruction does not require or use expected outputs."""
    input_grid = [[0, 1], [1, 0]]
    primitive_sequence = [{"primitive_id": "copy", "parameters": {}}]
    # No expected_grid passed - reconstruction only needs input + sequence
    rec = apply_primitive_sequence_to_grid_v1(input_grid, primitive_sequence)
    assert rec["reconstruction_success"] is True