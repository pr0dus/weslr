from __future__ import annotations

import copy
import importlib
import inspect

import pytest

from weslr.answer_method_catalog import build_answer_method_catalog_v1, select_methods_for_turn_v1
from weslr.answer_shape_catalog import (
    AnswerShapeCatalogPacket,
    build_answer_shape_catalog_v1,
    select_answer_shapes_v1,
    summarize_answer_shape_catalog_v1,
    to_answer_shape_catalog_json_safe_v1,
    validate_answer_shape_catalog_v1,
)


def test_module_imports_safely() -> None:
    module = importlib.import_module("weslr.answer_shape_catalog")
    assert module.__name__ == "weslr.answer_shape_catalog"


def test_catalog_builds_deterministically() -> None:
    catalog_one = build_answer_shape_catalog_v1()
    catalog_two = build_answer_shape_catalog_v1()
    assert catalog_one == catalog_two
    assert isinstance(catalog_one, AnswerShapeCatalogPacket)
    assert validate_answer_shape_catalog_v1(catalog_one)["valid"] is True


def test_all_required_shapes_exist() -> None:
    catalog = build_answer_shape_catalog_v1()
    shape_ids = {shape.shape_id for shape in catalog.shapes}
    assert shape_ids == {
        "direct_bounded_answer",
        "clarifying_question",
        "bounded_uncertainty_answer",
        "refusal_boundary_answer",
        "evidence_needed_answer",
        "partial_supported_answer",
        "stepwise_plan_answer",
        "implementation_plan_answer",
        "workflow_next_lane_answer",
        "governance_escalation_answer",
        "teaching_explanation_answer",
        "language_discovery_explanation_answer",
        "scientific_discovery_guidance_answer",
        "benchmark_evaluation_summary_answer",
        "unknown_friction_branch_answer",
        "memory_honesty_answer",
        "continuity_thread_recap_answer",
        "relationship_feedback_answer",
        "correction_repair_answer",
        "conflict_contradiction_answer",
        "non_canned_specific_answer",
        "directness_concern_integrated_answer",
    }


def test_no_duplicate_shape_ids() -> None:
    catalog = build_answer_shape_catalog_v1()
    shape_ids = [shape.shape_id for shape in catalog.shapes]
    assert len(shape_ids) == len(set(shape_ids))


@pytest.mark.parametrize(
    "field_name",
    [
        "shape_id",
        "name",
        "purpose",
        "use_when",
        "avoid_when",
        "required_inputs",
        "compatible_method_families",
        "compatible_method_ids",
        "blocked_if",
        "output_contract",
        "risk_notes",
        "source_refs",
        "runtime_authority",
        "model_required",
        "writes_state",
        "generates_final_text",
        "safe_for_shape_selection",
    ],
)
def test_required_fields_are_populated(field_name: str) -> None:
    catalog = build_answer_shape_catalog_v1()
    for shape in catalog.shapes:
        value = getattr(shape, field_name)
        if field_name in {"required_inputs", "compatible_method_families", "compatible_method_ids", "blocked_if", "source_refs"}:
            assert value
        elif field_name in {"runtime_authority", "model_required", "writes_state", "generates_final_text", "safe_for_shape_selection"}:
            assert isinstance(value, bool)
        else:
            assert value


def test_source_refs_are_present() -> None:
    catalog = build_answer_shape_catalog_v1()
    assert all(shape.source_refs for shape in catalog.shapes)


def test_no_shape_has_runtime_authority() -> None:
    catalog = build_answer_shape_catalog_v1()
    assert all(shape.runtime_authority is False for shape in catalog.shapes)


def test_no_shape_writes_state() -> None:
    catalog = build_answer_shape_catalog_v1()
    assert all(shape.writes_state is False for shape in catalog.shapes)


def test_no_v1_selectable_shape_requires_model_provider() -> None:
    catalog = build_answer_shape_catalog_v1()
    assert all(shape.model_required is False for shape in catalog.shapes if shape.safe_for_shape_selection)


def test_no_shape_generates_final_text() -> None:
    catalog = build_answer_shape_catalog_v1()
    assert all(shape.generates_final_text is False for shape in catalog.shapes)


def test_json_safe_export_works() -> None:
    catalog = build_answer_shape_catalog_v1()
    safe = to_answer_shape_catalog_json_safe_v1(catalog)
    assert isinstance(safe, dict)
    assert safe["catalog_type"] == "answer_shape_catalog_v1"
    assert isinstance(safe["shapes"], list)


def test_summary_includes_shape_count_and_compatibility_summary() -> None:
    catalog = build_answer_shape_catalog_v1()
    summary = summarize_answer_shape_catalog_v1(catalog)
    assert summary["shape_count"] == 22
    assert "compatibility_summary" in summary
    assert summary["selectable_shape_count"] == 22


@pytest.mark.parametrize(
    "labels, expected_shape",
    [
        (["direct", "answer"], "direct_bounded_answer"),
        (["clarify", "missing"], "clarifying_question"),
        (["uncertain", "not sure"], "bounded_uncertainty_answer"),
        (["refuse", "privacy"], "refusal_boundary_answer"),
        (["evidence", "source"], "evidence_needed_answer"),
        (["partial", "supported"], "partial_supported_answer"),
        (["plan", "steps"], "stepwise_plan_answer"),
        (["teaching", "explain"], "teaching_explanation_answer"),
        (["language", "grammar"], "language_discovery_explanation_answer"),
        (["unknown", "friction"], "unknown_friction_branch_answer"),
        (["memory", "continuity"], "memory_honesty_answer"),
        (["correction", "relationship"], "correction_repair_answer"),
        (["contradiction", "conflict"], "conflict_contradiction_answer"),
    ],
)
def test_selection_works_for_labels(labels: list[str], expected_shape: str) -> None:
    catalog = build_answer_shape_catalog_v1()
    selection = select_answer_shapes_v1(labels, catalog=catalog)
    assert selection["selected_shapes"]
    assert expected_shape in selection["selected_shape_ids"]


def test_unknown_labels_fail_closed_or_return_safe_bounded_fallback_metadata() -> None:
    catalog = build_answer_shape_catalog_v1()
    selection = select_answer_shapes_v1(["qzxy", "orphaned-token"], catalog=catalog)
    assert selection["fallback_used"] is True
    assert selection["selected_shape_ids"] == ["clarifying_question"]


def test_incompatible_method_family_shape_pair_is_rejected() -> None:
    shape_catalog = build_answer_shape_catalog_v1()
    method_catalog = build_answer_method_catalog_v1()
    method_candidates = select_methods_for_turn_v1(["teaching", "explanation"], method_catalog)
    selection = select_answer_shapes_v1(["teaching", "explanation"], method_candidates=method_candidates, catalog=shape_catalog)
    assert selection["selected_shape_ids"] == ["teaching_explanation_answer"]
    assert "direct_bounded_answer" in selection["rejected_shape_ids"]


def test_compatible_method_family_shape_pair_is_accepted() -> None:
    shape_catalog = build_answer_shape_catalog_v1()
    method_catalog = build_answer_method_catalog_v1()
    method_candidates = select_methods_for_turn_v1(["identity", "status"], method_catalog)
    selection = select_answer_shapes_v1(["identity", "status"], method_candidates=method_candidates, catalog=shape_catalog)
    assert "direct_bounded_answer" in selection["selected_shape_ids"]


def test_mutated_invalid_catalog_fails_validation() -> None:
    catalog = to_answer_shape_catalog_json_safe_v1(build_answer_shape_catalog_v1())
    mutated = copy.deepcopy(catalog)
    mutated["shapes"][0]["generates_final_text"] = True
    result = validate_answer_shape_catalog_v1(mutated)
    assert result["valid"] is False
    assert "generates_final_text_must_be_false" in result["blocked_labels"]


def test_catalog_does_not_generate_final_answer_prose() -> None:
    catalog = build_answer_shape_catalog_v1()
    selection = select_answer_shapes_v1(["identity", "status"], catalog=catalog)
    forbidden_keys = {"answer_text", "response_text", "final_answer", "generated_text", "prose"}
    assert forbidden_keys.isdisjoint(selection.keys())
    assert all(forbidden_keys.isdisjoint(shape.keys()) for shape in selection["selected_shapes"])


def test_catalog_does_not_import_or_call_runtime_chat_files() -> None:
    import weslr.answer_shape_catalog as module

    source = inspect.getsource(module)
    forbidden_fragments = ["chat_responder.py", "main.py", "dialogue.py", "chat_ui.py"]
    assert all(fragment not in source for fragment in forbidden_fragments)
    assert not any(name in module.__dict__ for name in {"chat_responder", "dialogue", "chat_ui"})


def test_shape_catalog_can_consume_method_candidates_from_method_catalog() -> None:
    method_selection = select_methods_for_turn_v1(["identity", "status"], build_answer_method_catalog_v1())
    shape_selection = select_answer_shapes_v1(["identity", "status"], method_candidates=method_selection)
    assert shape_selection["method_candidate_summary"]["candidate_count"] > 0
    assert shape_selection["selected_shape_ids"]
