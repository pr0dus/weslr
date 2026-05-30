from __future__ import annotations

import copy
import inspect
import importlib

import pytest

from weslr.answer_method_catalog import (
    AnswerMethodCatalogPacket,
    build_answer_method_catalog_v1,
    select_methods_for_turn_v1,
    summarize_answer_method_catalog_v1,
    to_answer_method_catalog_json_safe_v1,
    validate_answer_method_catalog_v1,
)


def test_module_imports_safely() -> None:
    module = importlib.import_module("weslr.answer_method_catalog")
    assert module.__name__ == "weslr.answer_method_catalog"


def test_catalog_builds_deterministically() -> None:
    catalog_one = build_answer_method_catalog_v1()
    catalog_two = build_answer_method_catalog_v1()
    assert catalog_one == catalog_two
    assert isinstance(catalog_one, AnswerMethodCatalogPacket)
    assert validate_answer_method_catalog_v1(catalog_one)["valid"] is True


def test_all_required_families_exist() -> None:
    catalog = build_answer_method_catalog_v1()
    family_ids = {family.family_id for family in catalog.families}
    assert family_ids == {
        "identity_status",
        "boundary_uncertainty",
        "task_workflow",
        "teaching_explanation_discovery",
        "relationship_correction_continuity",
        "response_shape_quality",
    }


def test_all_27_methods_exist() -> None:
    catalog = build_answer_method_catalog_v1()
    assert len(catalog.methods) == 27


def test_no_duplicate_method_ids() -> None:
    catalog = build_answer_method_catalog_v1()
    method_ids = [method.method_id for method in catalog.methods]
    assert len(method_ids) == len(set(method_ids))


def test_no_duplicate_family_ids() -> None:
    catalog = build_answer_method_catalog_v1()
    family_ids = [family.family_id for family in catalog.families]
    assert len(family_ids) == len(set(family_ids))


def test_all_methods_reference_valid_families() -> None:
    catalog = build_answer_method_catalog_v1()
    family_ids = {family.family_id for family in catalog.families}
    assert all(method.family_id in family_ids for method in catalog.methods)


@pytest.mark.parametrize(
    "field_name",
    [
        "method_id",
        "family_id",
        "name",
        "purpose",
        "triggers",
        "required_inputs",
        "output_shape",
        "method_type",
        "implementation_status",
        "source_refs",
        "target_files",
        "diff_vs_generic_llm",
        "runtime_authority",
        "model_required",
        "writes_state",
        "safe_for_catalog_selection",
    ],
)
def test_required_fields_are_populated(field_name: str) -> None:
    catalog = build_answer_method_catalog_v1()
    for method in catalog.methods:
        value = getattr(method, field_name)
        if field_name in {"triggers", "required_inputs", "source_refs", "target_files"}:
            assert value
        elif field_name in {"runtime_authority", "model_required", "writes_state", "safe_for_catalog_selection"}:
            assert isinstance(value, bool)
        else:
            assert value


def test_source_refs_are_present() -> None:
    catalog = build_answer_method_catalog_v1()
    assert all(method.source_refs for method in catalog.methods)
    assert all(family.source_refs for family in catalog.families)


def test_no_method_has_runtime_authority() -> None:
    catalog = build_answer_method_catalog_v1()
    assert all(method.runtime_authority is False for method in catalog.methods)


def test_no_method_writes_state() -> None:
    catalog = build_answer_method_catalog_v1()
    assert all(method.writes_state is False for method in catalog.methods)


def test_no_v1_selectable_method_requires_model_provider() -> None:
    catalog = build_answer_method_catalog_v1()
    assert all(method.model_required is False for method in catalog.methods if method.safe_for_catalog_selection)


def test_json_safe_export_works() -> None:
    catalog = build_answer_method_catalog_v1()
    safe = to_answer_method_catalog_json_safe_v1(catalog)
    assert isinstance(safe, dict)
    assert safe["catalog_type"] == "answer_method_catalog_v1"
    assert isinstance(safe["families"], list)
    assert isinstance(safe["methods"], list)


def test_summary_includes_family_and_method_counts() -> None:
    catalog = build_answer_method_catalog_v1()
    summary = summarize_answer_method_catalog_v1(catalog)
    assert summary["family_count"] == 6
    assert summary["method_count"] == 27
    assert summary["selectable_method_count"] == 27


@pytest.mark.parametrize(
    "labels, expected_family",
    [
        (["identity", "status"], "identity_status"),
        (["memory", "continuity"], "identity_status"),
        (["boundary", "uncertainty"], "boundary_uncertainty"),
        (["task", "workflow"], "task_workflow"),
        (["teaching", "explanation"], "teaching_explanation_discovery"),
        (["correction", "continuity"], "relationship_correction_continuity"),
        (["response-shape", "quality"], "response_shape_quality"),
    ],
)
def test_selection_works_for_family_labels(labels: list[str], expected_family: str) -> None:
    catalog = build_answer_method_catalog_v1()
    selection = select_methods_for_turn_v1(labels, catalog)
    assert selection["selected_methods"]
    assert expected_family in selection["selected_family_ids"]


def test_unknown_labels_fail_closed_or_return_safe_fallback_metadata() -> None:
    catalog = build_answer_method_catalog_v1()
    selection = select_methods_for_turn_v1(["qzxy", "orphaned-token", "labels"], catalog)
    assert selection["fallback_used"] is True
    assert selection["selected_method_ids"] == ["clarifying_question_answer_v1"]
    assert selection["selected_family_ids"] == ["boundary_uncertainty"]


def test_mutated_invalid_catalog_fails_validation() -> None:
    catalog = to_answer_method_catalog_json_safe_v1(build_answer_method_catalog_v1())
    mutated = copy.deepcopy(catalog)
    mutated["methods"][0]["runtime_authority"] = True
    result = validate_answer_method_catalog_v1(mutated)
    assert result["valid"] is False
    assert "runtime_authority_must_be_false" in result["blocked_labels"]


def test_catalog_does_not_generate_final_answer_prose() -> None:
    catalog = build_answer_method_catalog_v1()
    selection = select_methods_for_turn_v1(["identity", "status"], catalog)
    forbidden_keys = {"answer_text", "response_text", "final_answer", "generated_text", "prose"}
    assert forbidden_keys.isdisjoint(selection.keys())
    assert all(forbidden_keys.isdisjoint(method.keys()) for method in selection["selected_methods"])


def test_catalog_does_not_import_or_call_runtime_chat_files() -> None:
    import weslr.answer_method_catalog as module

    source = inspect.getsource(module)
    forbidden_fragments = ["chat_responder.py", "main.py", "dialogue.py", "chat_ui.py"]
    assert all(fragment not in source for fragment in forbidden_fragments)
    assert not any(name in module.__dict__ for name in {"chat_responder", "dialogue", "chat_ui"})
