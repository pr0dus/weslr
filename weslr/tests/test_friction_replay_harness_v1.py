from __future__ import annotations

import ast
import inspect
import importlib

import pytest

from weslr.friction_case_capture import build_initial_renderer_friction_cases_v1
from weslr.friction_replay_harness import (
    FrictionReplayHarnessPacket,
    ValidationError,
    build_friction_replay_case_result_v1,
    build_initial_renderer_friction_replay_v1,
    run_friction_replay_v1,
    summarize_friction_replay_packet_v1,
    to_friction_replay_json_safe_v1,
    validate_friction_replay_packet_v1,
)


def test_module_imports_safely() -> None:
    module = importlib.import_module("weslr.friction_replay_harness")
    assert hasattr(module, "run_friction_replay_v1")
    assert hasattr(module, "build_initial_renderer_friction_replay_v1")


def test_replay_packet_builds_deterministically() -> None:
    packet_one = build_initial_renderer_friction_replay_v1()
    packet_two = build_initial_renderer_friction_replay_v1()
    assert packet_one == packet_two


def test_valid_replay_packet_validates() -> None:
    packet = build_initial_renderer_friction_replay_v1()
    assert validate_friction_replay_packet_v1(packet) is True


def test_json_safe_export_works() -> None:
    packet = build_initial_renderer_friction_replay_v1()
    safe = to_friction_replay_json_safe_v1(packet)
    assert safe["packet_type"] == "friction_replay_harness_v1"
    assert isinstance(safe["results"], list)


def test_summary_includes_pass_fail_partial_counts() -> None:
    packet = build_initial_renderer_friction_replay_v1()
    summary = summarize_friction_replay_packet_v1(packet)
    assert summary["passed_count"] >= 0
    assert summary["failed_count"] >= 0
    assert summary["partial_count"] >= 0


def test_initial_four_friction_cases_are_replayed() -> None:
    packet = build_initial_renderer_friction_replay_v1()
    assert packet.case_count == 4
    assert {result.case_id for result in packet.results} == {
        "what_is_weslr_identity_friction",
        "what_can_you_do_now_capability_friction",
        "unknown_word_blorvatek_friction",
        "upload_files_now_boundary_friction",
    }


@pytest.mark.parametrize(
    "case_id",
    [
        "what_is_weslr_identity_friction",
        "what_can_you_do_now_capability_friction",
        "unknown_word_blorvatek_friction",
        "upload_files_now_boundary_friction",
    ],
)
def test_initial_replay_result_exists(case_id: str) -> None:
    packet = build_initial_renderer_friction_replay_v1()
    assert any(result.case_id == case_id for result in packet.results)


def test_harness_can_report_expected_failure_without_failing_validation() -> None:
    case = build_initial_renderer_friction_cases_v1()[0]
    result = build_friction_replay_case_result_v1(
        case,
        observed_response={
            "render_mode": "clarifying_question",
            "selected_method_id": "clarifying_question_answer_v1",
            "selected_shape_id": "clarifying_question",
            "selected_case_id": "clarification_case",
            "selected_route_id": "clarification_route",
            "blocked": False,
            "needs_clarification": False,
            "needs_evidence": False,
            "needs_owner_approval": False,
            "model_provider_used": False,
            "runtime_authority": False,
            "writes_state": False,
        },
    )
    assert result.match_status == "fails_expected"
    assert validate_friction_replay_packet_v1({"packet_type": "friction_replay_harness_v1", "case_count": 1, "passed_count": 0, "failed_count": 1, "partial_count": 0, "blocked_count": 0, "invalid_count": 0, "results": [result], "learning_claimed": False, "runtime_authority": False, "writes_state": False, "model_provider_used": False, "proposal_created": False, "promotion_performed": False}) is True


def test_harness_can_report_partial_match() -> None:
    case = build_initial_renderer_friction_cases_v1()[0]
    result = build_friction_replay_case_result_v1(
        case,
        observed_response={
            "render_mode": "direct_bounded",
            "selected_method_id": "clarifying_question_answer_v1",
            "selected_shape_id": "direct_bounded_answer",
            "selected_case_id": "clarification_case",
            "selected_route_id": "identity_status_route",
            "blocked": False,
            "needs_clarification": False,
            "needs_evidence": False,
            "needs_owner_approval": False,
            "model_provider_used": False,
            "runtime_authority": False,
            "writes_state": False,
        },
    )
    assert result.match_status == "partially_matches_expected"


def test_harness_can_report_pass() -> None:
    case = build_initial_renderer_friction_cases_v1()[0]
    result = build_friction_replay_case_result_v1(
        case,
        observed_response={
            "render_mode": "direct_bounded",
            "selected_method_id": "verified_identity_status_answer_v1",
            "selected_shape_id": "direct_bounded_answer",
            "selected_case_id": "identity_self_description_case",
            "selected_route_id": "identity_status_route",
            "blocked": False,
            "needs_clarification": False,
            "needs_evidence": False,
            "needs_owner_approval": False,
            "model_provider_used": False,
            "runtime_authority": False,
            "writes_state": False,
        },
    )
    assert result.match_status == "passes_expected"


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("match_status", "unknown_status"),
    ],
)
def test_unknown_match_status_fails_validation(field_name, value) -> None:
    packet = to_friction_replay_json_safe_v1(build_initial_renderer_friction_replay_v1())
    packet["results"][0][field_name] = value
    with pytest.raises(ValidationError):
        validate_friction_replay_packet_v1(packet)


def test_count_mismatch_fails_validation() -> None:
    packet = to_friction_replay_json_safe_v1(build_initial_renderer_friction_replay_v1())
    packet["passed_count"] += 1
    with pytest.raises(ValidationError):
        validate_friction_replay_packet_v1(packet)


def test_duplicate_result_case_ids_fail_validation() -> None:
    packet = to_friction_replay_json_safe_v1(build_initial_renderer_friction_replay_v1())
    packet["results"][1]["case_id"] = packet["results"][0]["case_id"]
    with pytest.raises(ValidationError):
        validate_friction_replay_packet_v1(packet)


@pytest.mark.parametrize("field_name", ["learning_claimed", "proposal_created", "promotion_performed", "runtime_authority", "writes_state", "model_provider_used"])
def test_boolean_drift_fails_validation(field_name: str) -> None:
    packet = to_friction_replay_json_safe_v1(build_initial_renderer_friction_replay_v1())
    packet[field_name] = True
    with pytest.raises(ValidationError):
        validate_friction_replay_packet_v1(packet)


@pytest.mark.parametrize(
    "field_name",
    ["raw_prompt_stored", "raw_answer_stored", "transcript_text"],
)
def test_raw_fields_fail_validation(field_name: str) -> None:
    packet = to_friction_replay_json_safe_v1(build_initial_renderer_friction_replay_v1())
    packet[field_name] = "secret"
    with pytest.raises(ValidationError):
        validate_friction_replay_packet_v1(packet)


@pytest.mark.parametrize("module_name", ["chat_responder", "main", "dialogue", "chat_ui"])
def test_module_source_does_not_import_prohibited_modules(module_name: str) -> None:
    import weslr.friction_replay_harness as module

    tree = ast.parse(inspect.getsource(module))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    assert not any(module_name == imported or imported.endswith(f".{module_name}") for imported in imports)
