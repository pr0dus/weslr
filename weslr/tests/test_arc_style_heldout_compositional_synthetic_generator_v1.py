from __future__ import annotations

import ast
import copy
import inspect
import json
from typing import Any

from weslr.arc_style_grid_schema_helpers import build_arc_style_grid_metadata_v1, validate_arc_style_grid_task_packet_v1
from weslr.arc_style_heldout_compositional_synthetic_generator import (
    HELDOUT_RECIPE_FAMILIES_V1,
    RECIPE_VARIANTS_PER_FAMILY_V1,
    TASK_SOURCE_INTERNAL_HELDOUT_COMPOSITIONAL_V1,
    build_arc_style_heldout_composition_recipe_v1,
    build_initial_arc_style_heldout_composition_recipes_v1,
    generate_arc_style_heldout_compositional_suite_v1,
    generate_arc_style_heldout_compositional_task_v1,
    summarize_arc_style_heldout_compositional_suite_v1,
    to_arc_style_heldout_compositional_suite_json_safe_v1,
    validate_arc_style_heldout_composition_recipe_v1,
    validate_arc_style_heldout_compositional_suite_v1,
    validate_arc_style_heldout_compositional_task_v1,
)
from weslr.arc_style_typed_primitive_signatures import (
    get_arc_style_typed_primitive_signature_v1,
    validate_arc_style_typed_primitive_signature_v1,
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
    "requests",
    "pathlib",
    "subprocess",
)


def _json_safe(value: Any) -> Any:
    safe = to_arc_style_heldout_compositional_suite_json_safe_v1(value)
    json.dumps(safe, ensure_ascii=False)
    return safe


def _contains_callable(value: Any) -> bool:
    if callable(value):
        return True
    if isinstance(value, dict):
        return any(_contains_callable(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_callable(item) for item in value)
    return False


def test_initial_recipe_set_covers_all_required_families_and_two_variants_each() -> None:
    recipes = build_initial_arc_style_heldout_composition_recipes_v1()
    assert len(recipes) == len(HELDOUT_RECIPE_FAMILIES_V1) * RECIPE_VARIANTS_PER_FAMILY_V1
    family_counts = {family_id: 0 for family_id in HELDOUT_RECIPE_FAMILIES_V1}
    for recipe in recipes:
        validation = validate_arc_style_heldout_composition_recipe_v1(recipe)
        assert validation["valid"] is True
        assert recipe["recipe_family_id"] in HELDOUT_RECIPE_FAMILIES_V1
        family_counts[recipe["recipe_family_id"]] += 1
        assert recipe["boundary_flags"]["metadata_only"] is True
        assert recipe["boundary_flags"]["heldout_compositional"] is True
        assert recipe["leakage_flags"]["synthetic_only"] is True
        for primitive_name in recipe["primitive_sequence"]:
            primitive_validation = validate_arc_style_typed_primitive_signature_v1(
                get_arc_style_typed_primitive_signature_v1(primitive_name)
            )
            assert primitive_validation["valid"] is True
    assert family_counts == {family_id: RECIPE_VARIANTS_PER_FAMILY_V1 for family_id in HELDOUT_RECIPE_FAMILIES_V1}


def test_generated_suite_is_deterministic_by_seed_and_validates() -> None:
    first = generate_arc_style_heldout_compositional_suite_v1(seed=1234)
    second = generate_arc_style_heldout_compositional_suite_v1(seed=1234)
    assert _json_safe(first) == _json_safe(second)
    validation = validate_arc_style_heldout_compositional_suite_v1(first)
    summary = summarize_arc_style_heldout_compositional_suite_v1(first)
    assert validation["valid"] is True
    assert summary["valid"] is True
    assert summary["recipe_count"] == 14
    assert summary["task_count"] == 14
    assert summary["recipe_family_count"] == len(HELDOUT_RECIPE_FAMILIES_V1)
    assert summary["variant_count_per_family"] == RECIPE_VARIANTS_PER_FAMILY_V1
    assert set(summary["recipe_families"]) == set(HELDOUT_RECIPE_FAMILIES_V1)
    assert summary["solver_visible_expected_outputs_absent"] is True
    assert summary["evaluation_outputs_separated"] is True
    assert summary["typed_primitive_signatures_referenced"] is True
    assert set(summary["depth_values"]).issubset({2, 3})
    assert 3 in summary["depth_values"]


def test_each_generated_task_validates_and_keeps_evaluation_outputs_separate() -> None:
    suite = generate_arc_style_heldout_compositional_suite_v1(seed=4321)
    for task in suite["tasks"]:
        task_validation = validate_arc_style_heldout_compositional_task_v1(task)
        assert task_validation["valid"] is True
        assert task["task_packet"]["task_source"] == TASK_SOURCE_INTERNAL_HELDOUT_COMPOSITIONAL_V1
        assert task["task_packet"]["trace"]["heldout_compositional"] is True
        assert task["task_packet"]["trace"]["internal_synthetic_only"] is True
        assert task["task_packet"]["trace"]["solver_visible_expected_outputs_absent"] is True
        assert "expected_outputs" not in task["task_packet"]
        assert "answer_key" not in task["task_packet"]
        assert "solution" not in task["task_packet"]
        assert "test_output" not in task["task_packet"]
        assert task["evaluation_metadata"]["heldout_compositional"] is True
        assert task["evaluation_metadata"]["synthetic_only"] is True
        assert len(task["evaluation_metadata"]["expected_outputs"]) == 1
        expected_output = task["evaluation_metadata"]["expected_outputs"][0]["output_grid"]
        assert build_arc_style_grid_metadata_v1(expected_output)["invalid_cells"] == []
        assert validate_arc_style_grid_task_packet_v1(task["task_packet"])["valid"] is True
        assert task["provenance_metadata"]["typed_primitive_signatures_referenced"] is True
        assert task["boundary_flags"]["metadata_only"] is True
        assert task["boundary_flags"]["no_public_arc_data"] is True
        assert task["boundary_flags"]["no_kaggle_data"] is True


def test_generated_grids_validate_under_existing_schema_rules() -> None:
    suite = generate_arc_style_heldout_compositional_suite_v1(seed=777)
    for task in suite["tasks"]:
        packet = task["task_packet"]
        assert validate_arc_style_grid_task_packet_v1(packet)["valid"] is True
        for train_pair in packet["train_pairs"]:
            assert build_arc_style_grid_metadata_v1(train_pair["input_grid"])["invalid_cells"] == []
            assert build_arc_style_grid_metadata_v1(train_pair["output_grid"])["invalid_cells"] == []
        test_input = packet["test_input"]
        assert build_arc_style_grid_metadata_v1(test_input["cell_values"])["invalid_cells"] == []
        expected_output = task["evaluation_metadata"]["expected_outputs"][0]["output_grid"]
        assert build_arc_style_grid_metadata_v1(expected_output)["invalid_cells"] == []


def test_invalid_recipe_and_duplicate_ids_fail_closed() -> None:
    missing_recipe = {
        "recipe_id": "bad_recipe",
        "recipe_family_id": "extract_object_then_recolor",
    }
    missing_validation = validate_arc_style_heldout_composition_recipe_v1(missing_recipe)
    assert missing_validation["valid"] is False
    assert "missing_required_fields" in missing_validation["blocked_reason_labels"]

    invalid_sequence_recipe = build_arc_style_heldout_composition_recipe_v1(
        recipe_family_id="extract_object_then_recolor",
        variant_index=0,
        task_id="invalid_sequence_task",
        seed=1,
        depth=2,
        primitive_sequence=["copy_grid", "not_a_primitive"],
        train_pair_count=2,
        test_input_count=1,
        generation_parameters={"rows": 5, "cols": 5, "background_color": 0},
    )
    invalid_sequence_validation = validate_arc_style_heldout_composition_recipe_v1(invalid_sequence_recipe)
    assert invalid_sequence_validation["valid"] is False
    assert "primitive_sequence_unsupported" in invalid_sequence_validation["blocked_reason_labels"]

    suite = generate_arc_style_heldout_compositional_suite_v1(seed=99)
    duplicated = copy.deepcopy(suite)
    duplicated["recipe_specs"].append(copy.deepcopy(duplicated["recipe_specs"][0]))
    duplicated["tasks"].append(copy.deepcopy(duplicated["tasks"][0]))
    validation = validate_arc_style_heldout_compositional_suite_v1(duplicated)
    assert validation["valid"] is False
    assert "duplicate_recipe_ids" in validation["blocked_reason_labels"]


def test_invalid_grids_fail_closed() -> None:
    task = generate_arc_style_heldout_compositional_task_v1(build_initial_arc_style_heldout_composition_recipes_v1()[0])
    bad_task = copy.deepcopy(task)
    bad_task["task_packet"]["test_input"]["cell_values"][0][0] = 10
    validation = validate_arc_style_heldout_compositional_task_v1(bad_task)
    assert validation["valid"] is False
    assert any(label.startswith("task_packet_invalid") or label == "task_packet_invalid" for label in validation["blocked_reason_labels"])


def test_json_safe_export_contains_no_callable_objects() -> None:
    suite = generate_arc_style_heldout_compositional_suite_v1(seed=2026)
    safe = _json_safe(suite)
    assert _contains_callable(safe) is False
    assert safe["suite_id"] == "arc_style_heldout_compositional_synthetic_suite_v1"
    assert safe["generator_metadata"]["heldout_compositional"] is True


def test_module_source_has_no_forbidden_provider_or_chat_calls() -> None:
    module = __import__("weslr.arc_style_heldout_compositional_synthetic_generator", fromlist=["*"])
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
    assert "respond_chat(" not in source
    assert "chat_responder." not in source
    assert "openai" not in source.lower()
    assert "anthropic" not in source.lower()
    assert "requests." not in source
    assert "open(" not in source.lower()
