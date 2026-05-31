from __future__ import annotations

import ast
import importlib
import inspect
import json
import sys
import types
from dataclasses import replace

import pytest

from weslr.response_method_selector import (
    ValidationError,
    build_response_selection_packet_v1,
    select_response_route_v1,
    summarize_response_selection_packet_v1,
    to_response_selection_json_safe_v1,
    validate_response_selection_packet_v1,
)


def _base_packet():
    return select_response_route_v1(["ordinary task"], {"memory_available": True, "evidence_available": True})


def _fake_candidate(kind: str, route_id: str, item_id: str, compatible_item_id: str):
    if kind == "method":
        return {
            "method_id": item_id,
            "method_family": "custom_family",
            "route_id": route_id,
            "label": item_id,
            "confidence": 0.99,
            "compatible_shape_ids": [compatible_item_id],
            "compatible_case_ids": ["custom_case"],
            "notes": ["fake"],
        }
    if kind == "shape":
        return {
            "shape_id": item_id,
            "shape_family": "custom_family",
            "route_id": route_id,
            "label": item_id,
            "confidence": 0.99,
            "compatible_method_ids": [compatible_item_id],
            "compatible_case_ids": ["custom_case"],
            "notes": ["fake"],
        }
    return {
        "case_id": item_id,
        "case_family": "custom_family",
        "route_id": route_id,
        "label": item_id,
        "confidence": 0.99,
        "compatible_method_ids": [compatible_item_id],
        "compatible_shape_ids": ["custom_shape"],
        "notes": ["fake"],
    }


@pytest.fixture

def fake_catalog_modules(monkeypatch):
    method_mod = types.ModuleType("weslr.answer_method_catalog")
    shape_mod = types.ModuleType("weslr.answer_shape_catalog")
    case_mod = types.ModuleType("weslr.cognition_case_registry")

    def select_methods_for_turn_v1(turn_labels=None, context_signals=None):
        return [
            _fake_candidate("method", "ordinary_task_route", "custom_method", "custom_shape"),
        ]

    def select_answer_shapes_v1(turn_labels=None, context_signals=None):
        return [
            _fake_candidate("shape", "ordinary_task_route", "custom_shape", "custom_method"),
        ]

    def select_cognition_cases_v1(turn_labels=None, context_signals=None):
        return [
            _fake_candidate("case", "ordinary_task_route", "custom_case", "custom_method"),
        ]

    method_mod.select_methods_for_turn_v1 = select_methods_for_turn_v1
    shape_mod.select_answer_shapes_v1 = select_answer_shapes_v1
    case_mod.select_cognition_cases_v1 = select_cognition_cases_v1

    monkeypatch.setitem(sys.modules, "weslr.answer_method_catalog", method_mod)
    monkeypatch.setitem(sys.modules, "weslr.answer_shape_catalog", shape_mod)
    monkeypatch.setitem(sys.modules, "weslr.cognition_case_registry", case_mod)
    return method_mod, shape_mod, case_mod


def test_module_imports_safely():
    mod = importlib.import_module("weslr.response_method_selector")
    assert hasattr(mod, "select_response_route_v1")
    assert hasattr(mod, "build_response_selection_packet_v1")


def test_selector_builds_deterministic_packets():
    p1 = select_response_route_v1(["ordinary task"], {"memory_available": True})
    p2 = select_response_route_v1(["ordinary task"], {"memory_available": True})
    assert p1 == p2


def test_validates_normal_selection_packet():
    packet = _base_packet()
    assert validate_response_selection_packet_v1(packet) is True


def test_json_safe_export_works():
    packet = _base_packet()
    exported = to_response_selection_json_safe_v1(packet)
    json.dumps(exported)
    assert exported["selected_route_id"] == "ordinary_task_route"


def test_summary_includes_route_method_shape_case():
    packet = _base_packet()
    summary = summarize_response_selection_packet_v1(packet)
    assert summary["route_id"]
    assert summary["method_id"]
    assert summary["shape_id"]
    assert summary["case_id"]


@pytest.mark.parametrize(
    "label, expected_route",
    [
        ("identity status", "identity_status_route"),
        ("memory honesty", "memory_honesty_route"),
        ("continuity", "continuity_route"),
        ("capability orientation", "capability_orientation_route"),
        ("clarification", "clarification_route"),
        ("uncertainty", "uncertainty_route"),
        ("refusal boundary", "refusal_boundary_route"),
        ("evidence needed", "evidence_needed_route"),
        ("partial supported", "partial_supported_route"),
        ("ordinary task", "ordinary_task_route"),
        ("implementation planning", "implementation_planning_route"),
        ("workflow next lane", "workflow_next_lane_route"),
        ("governance escalation", "governance_escalation_route"),
        ("teaching explanation", "teaching_explanation_route"),
        ("language discovery", "language_discovery_route"),
        ("scientific discovery", "scientific_discovery_route"),
        ("benchmark evaluation", "benchmark_evaluation_route"),
        ("unknown word phrase", "unknown_word_phrase_route"),
        ("unknown intent", "unknown_intent_route"),
        ("unknown capability", "unknown_capability_route"),
        ("friction repeated failure", "friction_repeated_failure_route"),
        ("relationship feedback", "relationship_feedback_route"),
        ("correction repair", "correction_repair_route"),
        ("conflict contradiction", "conflict_contradiction_route"),
        ("non canned specificity", "non_canned_specificity_route"),
        ("directness concern", "directness_concern_route"),
    ],
)
def test_route_family_selection(label, expected_route):
    packet = select_response_route_v1([label])
    assert packet.selected_route_id == expected_route
    assert validate_response_selection_packet_v1(packet) is True


def test_unknown_labels_fail_closed_into_clarification_or_unknown_friction_metadata():
    packet = select_response_route_v1(["gibberish lotus"], {})
    assert packet.selected_route_id in {
        "clarification_route",
        "uncertainty_route",
        "unknown_word_phrase_route",
        "unknown_intent_route",
        "unknown_capability_route",
        "friction_repeated_failure_route",
    }
    assert packet.blocked is True


def test_selector_consumes_method_catalog_output(fake_catalog_modules):
    packet = select_response_route_v1(["ordinary task"], {})
    assert packet.selected_method_id == "custom_method"


def test_selector_consumes_shape_catalog_output(monkeypatch):
    shape_mod = types.ModuleType("weslr.answer_shape_catalog")

    def select_answer_shapes_v1(turn_labels=None, context_signals=None):
        return [_fake_candidate("shape", "ordinary_task_route", "custom_shape", "method_ordinary_task")]

    shape_mod.select_answer_shapes_v1 = select_answer_shapes_v1
    monkeypatch.setitem(sys.modules, "weslr.answer_shape_catalog", shape_mod)

    packet = select_response_route_v1(["ordinary task"], {})
    assert packet.selected_shape_id == "custom_shape"


def test_selector_consumes_cognition_case_registry_output(monkeypatch):
    case_mod = types.ModuleType("weslr.cognition_case_registry")

    def select_cognition_cases_v1(turn_labels=None, context_signals=None):
        return [_fake_candidate("case", "ordinary_task_route", "custom_case", "method_ordinary_task")]

    case_mod.select_cognition_cases_v1 = select_cognition_cases_v1
    monkeypatch.setitem(sys.modules, "weslr.cognition_case_registry", case_mod)

    packet = select_response_route_v1(["ordinary task"], {})
    assert packet.selected_case_id == "custom_case"


def test_incompatible_method_shape_case_combination_is_rejected():
    packet = to_response_selection_json_safe_v1(_base_packet())
    method = next(candidate for candidate in packet["method_selection"]["candidates"] if candidate["method_id"] == packet["selected_method_id"])
    shape = next(candidate for candidate in packet["shape_selection"]["candidates"] if candidate["shape_id"] == packet["selected_shape_id"])
    case = next(candidate for candidate in packet["case_selection"]["candidates"] if candidate["case_id"] == packet["selected_case_id"])
    method["compatible_shape_ids"] = ["other_shape"]
    shape["compatible_method_ids"] = ["other_method"]
    case["compatible_method_ids"] = ["other_method"]
    with pytest.raises(ValidationError):
        validate_response_selection_packet_v1(packet)


def test_authority_drift_fails_validation():
    packet = to_response_selection_json_safe_v1(_base_packet())
    packet["runtime_authority"] = True
    with pytest.raises(ValidationError):
        validate_response_selection_packet_v1(packet)


def test_model_provider_usage_fails_validation():
    packet = to_response_selection_json_safe_v1(_base_packet())
    packet["model_provider_used"] = True
    with pytest.raises(ValidationError):
        validate_response_selection_packet_v1(packet)


def test_writes_state_true_fails_validation():
    packet = to_response_selection_json_safe_v1(_base_packet())
    packet["writes_state"] = True
    with pytest.raises(ValidationError):
        validate_response_selection_packet_v1(packet)


def test_generates_final_text_true_fails_validation():
    packet = to_response_selection_json_safe_v1(_base_packet())
    packet["generates_final_text"] = True
    with pytest.raises(ValidationError):
        validate_response_selection_packet_v1(packet)


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_selector_source_does_not_import_prohibited_modules(module_name):
    import weslr.response_method_selector as module

    tree = ast.parse(inspect.getsource(module))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    assert module_name not in imports
