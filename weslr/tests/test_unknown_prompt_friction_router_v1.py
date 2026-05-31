from __future__ import annotations

import ast
import importlib
import inspect
import types

import pytest

from weslr.unknown_prompt_friction_router import (
    ValidationError,
    build_unknown_prompt_friction_packet_v1,
    route_unknown_prompt_friction_v1,
    summarize_unknown_prompt_friction_packet_v1,
    to_unknown_prompt_friction_json_safe_v1,
    validate_unknown_prompt_friction_packet_v1,
)


def test_module_imports_safely() -> None:
    module = importlib.import_module("weslr.unknown_prompt_friction_router")
    assert hasattr(module, "route_unknown_prompt_friction_v1")
    assert hasattr(module, "build_unknown_prompt_friction_packet_v1")


def test_router_builds_deterministic_packet() -> None:
    packet_one = route_unknown_prompt_friction_v1(["ordinary task"], {})
    packet_two = route_unknown_prompt_friction_v1(["ordinary task"], {})
    assert packet_one == packet_two


def test_normal_no_friction_packet_validates() -> None:
    packet = route_unknown_prompt_friction_v1(["ordinary task"], {})
    assert validate_unknown_prompt_friction_packet_v1(packet) is True
    assert packet.blocked is False
    assert packet.friction_level in {"none", "low"}


def test_direct_clear_prompt_has_low_or_no_friction() -> None:
    packet = route_unknown_prompt_friction_v1(["ordinary task"], {})
    assert packet.friction_detected is False or packet.friction_level in {"none", "low"}
    assert packet.response_policy == "answer_directly_bounded"
    assert packet.recommended_route_id == "ordinary_task_route"


def test_json_safe_export_works() -> None:
    packet = route_unknown_prompt_friction_v1(["ordinary task"], {})
    exported = to_unknown_prompt_friction_json_safe_v1(packet)
    assert exported["packet_type"] == "unknown_prompt_friction_router_v1"
    assert isinstance(exported["selector_packet_summary"], dict)
    assert isinstance(exported["safe_metadata"], dict)
    assert isinstance(exported["detected_signals"], list)


def test_summary_includes_friction_level_and_response_policy() -> None:
    packet = route_unknown_prompt_friction_v1(["ordinary task"], {})
    summary = summarize_unknown_prompt_friction_packet_v1(packet)
    assert summary["friction_level"] in {"none", "low"}
    assert summary["response_policy"] == "answer_directly_bounded"
    assert summary["route_id"] == "ordinary_task_route"


@pytest.mark.parametrize(
    "labels, context_signals, expected_route, expected_policy",
    [
        (["unknown word"], {}, "unknown_word_phrase_route", "route_unknown_friction"),
        (["unknown phrase"], {}, "unknown_word_phrase_route", "route_unknown_friction"),
        (["unknown intent"], {}, "unknown_intent_route", "route_unknown_friction"),
        (["unknown capability"], {}, "unknown_capability_route", "route_unknown_friction"),
        (["ordinary task"], {"evidence_needed": True}, "evidence_needed_route", "request_evidence"),
        (["ordinary task"], {"memory_unclear": True}, "memory_honesty_route", "route_memory_honesty"),
        (["ordinary task"], {"continuity_needed": True}, "continuity_route", "route_continuity_recap"),
        (["ordinary task"], {"relationship_signal": True}, "relationship_feedback_route", "route_relationship_feedback"),
        (["ordinary task"], {"correction_signal": True}, "correction_repair_route", "route_correction_repair"),
        (["ordinary task"], {"contradiction_signal": True}, "conflict_contradiction_route", "route_conflict_contradiction"),
        (["ordinary task"], {"language_signal": True}, "language_discovery_route", "route_language_discovery_explanation"),
        (["ordinary task"], {"grammar_signal": True}, "language_discovery_route", "route_language_discovery_explanation"),
        (["ordinary task"], {"vocabulary_signal": True}, "language_discovery_route", "route_language_discovery_explanation"),
        (["ordinary task"], {"future_capability_signal": True}, "capability_orientation_route", "route_capability_orientation"),
        (["ordinary task"], {"repeated_failure_signal": True}, "friction_repeated_failure_route", "route_unknown_friction"),
        (["ordinary task"], {"unsafe_signal": True}, "refusal_boundary_route", "refuse_with_boundary"),
        (["ordinary task"], {"public_mode": True}, "governance_escalation_route", "escalate_to_owner_review"),
        (["ordinary task"], {"model_available": False}, "capability_orientation_route", "route_capability_orientation"),
        (["ordinary task"], {"needs_owner_approval": True}, "governance_escalation_route", "escalate_to_owner_review"),
    ],
)
def test_signal_family_routing(labels, context_signals, expected_route, expected_policy) -> None:
    packet = route_unknown_prompt_friction_v1(labels, context_signals)
    assert packet.recommended_route_id == expected_route
    assert packet.response_policy == expected_policy
    assert validate_unknown_prompt_friction_packet_v1(packet) is True


def test_missing_context_routes_to_clarifying_question() -> None:
    packet = route_unknown_prompt_friction_v1(["clarify this"], {"ambiguous_terms": True})
    assert packet.response_policy == "ask_clarifying_question"
    assert packet.recommended_route_id == "clarification_route"
    assert packet.blocked is True


def test_unknown_labels_fail_closed() -> None:
    packet = route_unknown_prompt_friction_v1(["gibberish lotus"], {})
    assert packet.blocked is True
    assert packet.response_policy in {"ask_clarifying_question", "route_unknown_friction"}


def test_router_consumes_response_selector_output(monkeypatch) -> None:
    import weslr.unknown_prompt_friction_router as module

    fake_selector_packet = types.SimpleNamespace(selected_route_id="ordinary_task_route")

    def fake_select_response_route_v1(turn_labels, context_signals=None):
        return fake_selector_packet

    def fake_summarize_response_selection_packet_v1(packet):
        return {
            "selection_type": "response_selection_v1",
            "route_id": "ordinary_task_route",
            "method_id": "method_ordinary_task",
            "shape_id": "shape_ordinary_task",
            "case_id": "case_ordinary_task",
            "blocked": False,
            "blocked_labels": [],
            "route_confidence": 0.99,
            "family": "ordinary_task",
            "turn_labels": ["ordinary task"],
        }

    monkeypatch.setattr(module, "select_response_route_v1", fake_select_response_route_v1)
    monkeypatch.setattr(module, "summarize_response_selection_packet_v1", fake_summarize_response_selection_packet_v1)

    packet = module.build_unknown_prompt_friction_packet_v1(["ordinary task"], {})
    assert packet.selector_packet_summary["route_id"] == "ordinary_task_route"
    assert packet.safe_metadata["selector_packet_summary"]["route_id"] == "ordinary_task_route"


def test_selected_route_method_shape_case_are_compatible() -> None:
    packet = route_unknown_prompt_friction_v1(["unknown capability"], {})
    assert packet.recommended_method_id == "method_unknown_capability"
    assert packet.recommended_shape_id == "shape_unknown_capability"
    assert packet.recommended_case_id == "case_unknown_capability"
    assert validate_unknown_prompt_friction_packet_v1(packet) is True


def test_no_raw_prompt_text_is_returned() -> None:
    raw_prompt = "Please explain this strange thing"
    packet = route_unknown_prompt_friction_v1(raw_prompt, {})
    safe = to_unknown_prompt_friction_json_safe_v1(packet)
    assert "prompt" not in safe
    assert "raw_prompt" not in safe
    assert "prompt_text" not in safe
    assert all("prompt" not in key for key in safe.keys())


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("runtime_authority", True),
        ("model_provider_used", True),
        ("generates_final_text", True),
        ("writes_state", True),
    ],
)
def test_authority_drift_and_forbidden_flags_fail_validation(field_name, value) -> None:
    packet = to_unknown_prompt_friction_json_safe_v1(route_unknown_prompt_friction_v1(["ordinary task"], {}))
    packet[field_name] = value
    with pytest.raises(ValidationError):
        validate_unknown_prompt_friction_packet_v1(packet)


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_router_source_does_not_import_prohibited_modules(module_name) -> None:
    import weslr.unknown_prompt_friction_router as module

    tree = ast.parse(inspect.getsource(module))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
