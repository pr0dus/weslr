from __future__ import annotations

import copy
import importlib
import inspect

import pytest

from weslr.answer_method_catalog import build_answer_method_catalog_v1, select_methods_for_turn_v1
from weslr.answer_shape_catalog import build_answer_shape_catalog_v1, select_answer_shapes_v1
from weslr.cognition_case_registry import (
    CognitionCaseRegistryPacket,
    build_cognition_case_registry_v1,
    select_cognition_cases_v1,
    summarize_cognition_case_registry_v1,
    to_cognition_case_registry_json_safe_v1,
    validate_cognition_case_registry_v1,
)


def test_module_imports_safely() -> None:
    module = importlib.import_module("weslr.cognition_case_registry")
    assert module.__name__ == "weslr.cognition_case_registry"


def test_registry_builds_deterministically() -> None:
    registry_one = build_cognition_case_registry_v1()
    registry_two = build_cognition_case_registry_v1()
    assert registry_one == registry_two
    assert isinstance(registry_one, CognitionCaseRegistryPacket)
    assert validate_cognition_case_registry_v1(registry_one)["valid"] is True


def test_all_required_case_families_exist() -> None:
    registry = build_cognition_case_registry_v1()
    families = {case.case_family for case in registry.cases}
    assert families == {
        "identity_status",
        "boundary_uncertainty",
        "task_workflow",
        "teaching_explanation_discovery",
        "relationship_correction_continuity",
        "response_shape_quality",
        "unknown_friction",
        "evidence_provenance",
        "memory_continuity",
        "capability_governance",
    }


def test_all_required_case_ids_exist() -> None:
    registry = build_cognition_case_registry_v1()
    case_ids = {case.case_id for case in registry.cases}
    assert case_ids == {
        "identity_self_description_case",
        "status_current_capability_case",
        "memory_honesty_case",
        "continuity_thread_recap_case",
        "capability_orientation_case",
        "clarification_needed_case",
        "bounded_uncertainty_case",
        "refusal_boundary_case",
        "evidence_needed_case",
        "partial_supported_case",
        "ordinary_task_planning_case",
        "implementation_planning_case",
        "workflow_next_lane_case",
        "governance_escalation_case",
        "teaching_explanation_case",
        "language_discovery_explanation_case",
        "scientific_discovery_guidance_case",
        "benchmark_evaluation_summary_case",
        "unknown_word_or_phrase_case",
        "unknown_intent_case",
        "unknown_capability_request_case",
        "friction_repeated_failure_case",
        "relationship_feedback_case",
        "correction_repair_case",
        "conflict_contradiction_case",
        "non_canned_specificity_pressure_case",
        "directness_concern_integration_case",
    }


def test_no_duplicate_case_ids() -> None:
    registry = build_cognition_case_registry_v1()
    case_ids = [case.case_id for case in registry.cases]
    assert len(case_ids) == len(set(case_ids))


@pytest.mark.parametrize(
    "field_name",
    [
        "case_id",
        "case_family",
        "name",
        "purpose",
        "turn_signals",
        "required_context",
        "missing_context_signals",
        "evidence_requirements",
        "memory_requirements",
        "capability_requirements",
        "relationship_signals",
        "friction_signals",
        "unknown_signals",
        "allowed_method_ids",
        "allowed_shape_ids",
        "blocked_if",
        "selection_priority",
        "risk_notes",
        "source_refs",
        "runtime_authority",
        "model_required",
        "writes_state",
        "generates_final_text",
        "safe_for_case_selection",
    ],
)
def test_required_fields_are_populated(field_name: str) -> None:
    registry = build_cognition_case_registry_v1()
    for case in registry.cases:
        value = getattr(case, field_name)
        if field_name in {
            "turn_signals",
            "required_context",
            "missing_context_signals",
            "evidence_requirements",
            "memory_requirements",
            "capability_requirements",
            "relationship_signals",
            "friction_signals",
            "unknown_signals",
            "allowed_method_ids",
            "allowed_shape_ids",
            "blocked_if",
            "source_refs",
        }:
            assert value
        elif field_name in {"runtime_authority", "model_required", "writes_state", "generates_final_text", "safe_for_case_selection"}:
            assert isinstance(value, bool)
        else:
            assert value


def test_source_refs_are_present() -> None:
    registry = build_cognition_case_registry_v1()
    assert all(case.source_refs for case in registry.cases)


def test_allowed_method_ids_exist_in_method_catalog() -> None:
    method_catalog = build_answer_method_catalog_v1()
    method_ids = {method.method_id for method in method_catalog.methods}
    registry = build_cognition_case_registry_v1()
    assert all(all(method_id in method_ids for method_id in case.allowed_method_ids) for case in registry.cases)


def test_allowed_shape_ids_exist_in_shape_catalog() -> None:
    shape_catalog = build_answer_shape_catalog_v1()
    shape_ids = {shape.shape_id for shape in shape_catalog.shapes}
    registry = build_cognition_case_registry_v1()
    assert all(all(shape_id in shape_ids for shape_id in case.allowed_shape_ids) for case in registry.cases)


def test_no_case_has_runtime_authority() -> None:
    registry = build_cognition_case_registry_v1()
    assert all(case.runtime_authority is False for case in registry.cases)


def test_no_case_requires_model_provider() -> None:
    registry = build_cognition_case_registry_v1()
    assert all(case.model_required is False for case in registry.cases)


def test_no_case_writes_state() -> None:
    registry = build_cognition_case_registry_v1()
    assert all(case.writes_state is False for case in registry.cases)


def test_no_case_generates_final_text() -> None:
    registry = build_cognition_case_registry_v1()
    assert all(case.generates_final_text is False for case in registry.cases)


def test_json_safe_export_works() -> None:
    registry = build_cognition_case_registry_v1()
    safe = to_cognition_case_registry_json_safe_v1(registry)
    assert isinstance(safe, dict)
    assert safe["registry_type"] == "cognition_case_registry_v1"
    assert isinstance(safe["cases"], list)


def test_summary_includes_case_counts_and_family_counts() -> None:
    summary = summarize_cognition_case_registry_v1(build_cognition_case_registry_v1())
    assert summary["case_count"] == 27
    assert summary["case_family_count"] == 10
    assert summary["selectable_case_count"] == 27


def _method_selection(labels: list[str]):
    return select_methods_for_turn_v1(labels, build_answer_method_catalog_v1())


def _shape_selection(labels: list[str], method_candidates=None):
    return select_answer_shapes_v1(labels, method_candidates=method_candidates, catalog=build_answer_shape_catalog_v1())


@pytest.mark.parametrize(
    "labels, expected_case",
    [
        (["identity", "status"], "identity_self_description_case"),
        (["memory", "honesty"], "memory_honesty_case"),
        (["continuity", "recap"], "continuity_thread_recap_case"),
        (["capability", "orientation"], "capability_orientation_case"),
        (["clarify", "missing"], "clarification_needed_case"),
        (["uncertain", "not sure"], "bounded_uncertainty_case"),
        (["refuse", "privacy"], "refusal_boundary_case"),
        (["evidence", "needed"], "evidence_needed_case"),
        (["task", "planning"], "ordinary_task_planning_case"),
        (["implementation", "plan"], "implementation_planning_case"),
        (["next lane", "workflow"], "workflow_next_lane_case"),
        (["teaching", "explanation"], "teaching_explanation_case"),
        (["language", "discovery"], "language_discovery_explanation_case"),
        (["unknown word", "phrase"], "unknown_word_or_phrase_case"),
        (["unknown intent"], "unknown_intent_case"),
        (["unknown capability request"], "unknown_capability_request_case"),
        (["repeated failure", "friction"], "friction_repeated_failure_case"),
        (["correction", "feedback"], "correction_repair_case"),
        (["relationship", "feedback"], "relationship_feedback_case"),
        (["conflict", "contradiction"], "conflict_contradiction_case"),
        (["template", "generic"], "non_canned_specificity_pressure_case"),
        (["directness", "concern"], "directness_concern_integration_case"),
    ],
)
def test_selection_works_for_cases(labels: list[str], expected_case: str) -> None:
    method_selection = _method_selection(labels)
    shape_selection = _shape_selection(labels, method_candidates=method_selection)
    selection = select_cognition_cases_v1(labels, method_candidates=method_selection, shape_candidates=shape_selection)
    assert selection["selected_cases"]
    assert expected_case in selection["selected_case_ids"]


def test_selection_consumes_method_candidates_from_answer_method_catalog() -> None:
    method_selection = _method_selection(["identity", "status"])
    selection = select_cognition_cases_v1(["identity", "status"], method_candidates=method_selection)
    assert selection["method_candidate_summary"]["candidate_count"] > 0
    assert "identity_self_description_case" in selection["selected_case_ids"]


def test_selection_consumes_shape_candidates_from_answer_shape_catalog() -> None:
    method_selection = _method_selection(["identity", "status"])
    shape_selection = _shape_selection(["identity", "status"], method_candidates=method_selection)
    selection = select_cognition_cases_v1(["identity", "status"], shape_candidates=shape_selection)
    assert selection["shape_candidate_summary"]["candidate_count"] > 0
    assert "identity_self_description_case" in selection["selected_case_ids"]


def test_incompatible_method_shape_case_combination_is_rejected() -> None:
    method_selection = _method_selection(["teaching", "explanation"])
    shape_selection = _shape_selection(["identity", "status"])
    selection = select_cognition_cases_v1(["teaching", "explanation"], method_candidates=method_selection, shape_candidates=shape_selection)
    assert "teaching_explanation_case" not in selection["selected_case_ids"]
    assert selection["fallback_used"] is True or selection["selected_case_ids"]


def test_unknown_labels_fail_closed_into_unknown_or_clarification_or_friction_metadata() -> None:
    selection = select_cognition_cases_v1(["qzxy", "orphaned-token"])
    assert selection["selected_case_ids"]
    assert any(case_id in selection["selected_case_ids"] for case_id in ["unknown_intent_case", "clarification_needed_case", "friction_repeated_failure_case"])


def test_mutated_invalid_registry_fails_validation() -> None:
    registry = to_cognition_case_registry_json_safe_v1(build_cognition_case_registry_v1())
    mutated = copy.deepcopy(registry)
    mutated["cases"][0]["runtime_authority"] = True
    result = validate_cognition_case_registry_v1(mutated)
    assert result["valid"] is False
    assert "runtime_authority_must_be_false" in result["blocked_labels"]


def test_registry_does_not_import_or_call_runtime_chat_files() -> None:
    import weslr.cognition_case_registry as module

    source = inspect.getsource(module)
    forbidden_fragments = ["chat_responder.py", "main.py", "dialogue.py", "chat_ui.py"]
    assert all(fragment not in source for fragment in forbidden_fragments)
    assert not any(name in module.__dict__ for name in {"chat_responder", "dialogue", "chat_ui"})
