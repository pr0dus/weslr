from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.controlled_project_chat_runtime_shell_metadata import (
    SHELL_DECISIONS_V1,
    SHELL_PACKET_TYPES_V1,
    SHELL_STATES_V1,
    SHELL_DENIED_AUTHORITY_FIELDS_V1,
    allowed_controlled_project_chat_shell_decisions_v1,
    allowed_controlled_project_chat_shell_packet_types_v1,
    allowed_controlled_project_chat_shell_states_v1,
    build_controlled_project_chat_shell_packet_v1,
    build_initial_controlled_project_chat_shell_examples_v1,
    classify_controlled_project_chat_shell_packet_v1,
    summarize_controlled_project_chat_shell_packet_v1,
    to_controlled_project_chat_shell_json_safe_v1,
    validate_controlled_project_chat_shell_packet_v1,
)
from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
    validate_project_chat_answer_plan_v1,
)
from weslr.project_chat_runtime_dry_run_consumption_plan import (
    build_project_chat_dry_run_consumption_plan_v1,
    validate_project_chat_dry_run_consumption_plan_v1,
)
from weslr.project_chat_runtime_dry_run_metadata import (
    build_project_chat_runtime_dry_run_v1,
    validate_project_chat_runtime_dry_run_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "controlled_project_chat_runtime_shell_metadata.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]

FORBIDDEN_USER_VISIBLE_STATUS_CASES = [
    "Unknown Engine",
    "chat_responder",
    "respond_chat",
    "generate_chat",
    "chat_ui",
    "dialogue",
    "main.py",
    ".weslr",
    "hidden prompt",
    "system prompt",
    "private mechanism",
    "internal mechanism",
    "internal scoring",
    "tool executed",
    "I executed",
    "I searched your private data",
    "I saved this project",
    "I remember this",
    "SearXNG proves",
    "the web confirms",
    "truth authority",
    "final answer authority",
    "runtime authority",
    "mutation authority",
    "memory authority",
    "tool execution authority",
    "storage authority",
    "public readiness",
    "certified intelligence",
    "autonomous self-improvement",
]


def _base_answer_plan(**overrides):
    plan = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "answer_mode": "clarifying_question",
        "allowed_answer_scope": "current_message_only",
        "answer_status": "clarification_required",
        "user_visible_status": "clarification needed",
        "operator_visible_summary": "clarification required; metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    }
    plan.update(overrides)
    return build_project_chat_answer_plan_v1(plan)



def _base_dry_run(answer_plan_payload=None, **overrides):
    dry_run = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "dry_run_status": "dry_run_valid_metadata_only",
        "dry_run_decision": "proceed_to_answer_plan_metadata",
        "retrieval_need_class": "none",
        "user_visible_status": "metadata only",
        "operator_visible_summary": "metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    }
    if answer_plan_payload is not None:
        dry_run["answer_plan_payload"] = answer_plan_payload
    dry_run.update(overrides)
    return build_project_chat_runtime_dry_run_v1(dry_run)



def _base_consumption_plan(dry_run_metadata=None, answer_plan_metadata=None, **overrides):
    plan = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "dry_run_metadata": dry_run_metadata if dry_run_metadata is not None else _base_dry_run(),
        "consumption_status": "consumption_plan_valid_metadata_only",
        "consumption_action": "prepare_answer_plan_metadata_only",
        "allowed_next_metadata_step": "prepare_answer_plan_metadata_only",
        "user_visible_status": "answer-plan metadata only",
        "operator_visible_summary": "answer-plan metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    }
    if answer_plan_metadata is not None:
        plan["answer_plan_metadata"] = answer_plan_metadata
    plan.update(overrides)
    return build_project_chat_dry_run_consumption_plan_v1(plan)



def _base_shell_packet(**overrides):
    answer_plan = _base_answer_plan()
    dry_run = _base_dry_run(answer_plan)
    consumption_plan = _base_consumption_plan(dry_run, answer_plan)
    packet = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "shell_state": "shell_design_only",
        "shell_decision": "build_dry_run_metadata",
        "shell_packet_type": "shell_decision_packet",
        "message_metadata": {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "message_intent_class": "project-chat",
            "message_status": "metadata only",
            "operator_visible_summary": "message intake metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
        "project_state_metadata": {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "project_state_status": "metadata only",
            "operator_visible_summary": "project context metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
        "memory_state_metadata": {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "memory_state_status": "metadata only",
            "operator_visible_summary": "memory metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
        "continuity_metadata": {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "continuity_status": "metadata only",
            "operator_visible_summary": "continuity metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
        "evidence_retrieval_metadata": {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "retrieval_need_class": "none",
            "retrieval_status": "metadata only",
            "operator_visible_summary": "retrieval decision metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
        "answer_plan_metadata": answer_plan,
        "dry_run_metadata": dry_run,
        "consumption_plan_metadata": consumption_plan,
        "operator_review_metadata": {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "operator_review_status": "metadata only",
            "operator_visible_summary": "operator review metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
        "approval_metadata": {
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "approval_status": "metadata only",
            "operator_visible_summary": "approval metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
        "selected_next_metadata_step": "build_dry_run_metadata",
        "blocked_authority": "metadata_orchestration_boundary",
        "approval_refs": [],
        "operator_visibility_refs": [],
        "uncertainty_flags": [],
        "stale_state_flags": [],
        "contradiction_flags": [],
        "missing_evidence_flags": [],
        "privacy_flags": [],
        "limitations": [],
        "user_visible_status": "Metadata only.",
        "operator_visible_summary": "decision packet; metadata only",
        "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
    }
    packet.update(overrides)
    return build_controlled_project_chat_shell_packet_v1(packet)



def test_allowed_states_decisions_and_packet_types():
    assert allowed_controlled_project_chat_shell_states_v1() == SHELL_STATES_V1
    assert allowed_controlled_project_chat_shell_decisions_v1() == SHELL_DECISIONS_V1
    assert allowed_controlled_project_chat_shell_packet_types_v1() == SHELL_PACKET_TYPES_V1


@pytest.mark.parametrize(
    "shell_state,shell_decision,shell_packet_type,classification,user_visible_status,blocked_authority",
    [
        ("shell_blocked", "block_before_runtime", "shell_blocked_packet", "blocked", "This is blocked until a future approved boundary exists.", "runtime_wiring_boundary"),
        ("shell_metadata_dry_run_only", "request_clarification_metadata", "shell_clarification_packet", "clarification_required", "I need one clarification before continuing.", "clarification_boundary"),
        ("shell_approval_required", "request_user_approval_metadata", "shell_approval_request_packet", "approval_required", "This needs approval before deeper review.", "approval_boundary"),
        ("shell_operator_review_required", "request_operator_review_metadata", "shell_operator_review_packet", "operator_review_required", "This needs operator review before continuing.", "operator_review_boundary"),
        ("shell_metadata_dry_run_only", "prepare_answer_plan_metadata_candidate", "shell_answer_plan_candidate_packet", "answer_plan_candidate", "This can only be prepared as a candidate.", "answer_plan_candidate_boundary"),
        ("shell_metadata_dry_run_only", "prepare_retrieval_request_metadata_candidate", "shell_retrieval_request_candidate_packet", "retrieval_request_candidate", "This can only be prepared as a candidate.", "retrieval_candidate_boundary"),
        ("shell_metadata_dry_run_only", "prepare_tool_lane_candidate_metadata", "shell_tool_lane_candidate_packet", "tool_lane_candidate", "This can only be prepared as a candidate.", "tool_lane_candidate_boundary"),
        ("shell_metadata_dry_run_only", "prepare_persistence_candidate_metadata", "shell_persistence_candidate_packet", "persistence_candidate", "This can only be prepared as a candidate.", "persistence_candidate_boundary"),
        ("shell_design_only", "build_dry_run_metadata", "shell_decision_packet", "decision", "Metadata only.", "metadata_orchestration_boundary"),
        ("shell_metadata_dry_run_only", "build_consumption_plan_metadata", "shell_observability_packet", "observability", "Metadata only.", "metadata_orchestration_boundary"),
    ],
)
def test_valid_packet_types(shell_state, shell_decision, shell_packet_type, classification, user_visible_status, blocked_authority):
    packet = _base_shell_packet(
        shell_state=shell_state,
        shell_decision=shell_decision,
        shell_packet_type=shell_packet_type,
        user_visible_status=user_visible_status,
        operator_visible_summary=f"{shell_packet_type}; metadata only",
        blocked_authority=blocked_authority,
        selected_next_metadata_step=shell_decision,
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    classified = classify_controlled_project_chat_shell_packet_v1(packet)

    assert validation["blocked"] is False
    assert validation["shell_state"] == shell_state
    assert validation["shell_decision"] == shell_decision
    assert validation["shell_packet_type"] == shell_packet_type
    assert classified["classification"] == classification


@pytest.mark.parametrize("missing_key", ["owner_user_scope", "tenant_account_scope", "source_scope"])
def test_missing_owner_or_scope_fails_closed(missing_key):
    packet = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "shell_state": "shell_blocked",
        "shell_decision": "block_before_runtime",
        "shell_packet_type": "shell_blocked_packet",
        "selected_next_metadata_step": "block_before_runtime",
        "user_visible_status": "This is blocked until a future approved boundary exists.",
        "operator_visible_summary": "blocked packet; metadata only",
        "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
    }
    packet.pop(missing_key)
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith(f"missing_{missing_key}") for label in validation["blocked_labels"])


@pytest.mark.parametrize("field,value", [("shell_state", "unknown"), ("shell_decision", "unknown"), ("shell_packet_type", "unknown")])
def test_unknown_shell_value_fails_closed(field, value):
    packet = _base_shell_packet(**{field: value})
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label == f"unknown_{field}" for label in validation["blocked_labels"])


def test_invalid_nested_dry_run_metadata_blocks():
    packet = _base_shell_packet(
        dry_run_metadata={
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "dry_run_status": "unknown_status",
            "dry_run_decision": "proceed_to_answer_plan_metadata",
            "retrieval_need_class": "none",
            "user_visible_status": "metadata only",
            "operator_visible_summary": "metadata only",
            "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        }
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_nested_dry_run_metadata" in validation["blocked_labels"]


def test_invalid_nested_consumption_plan_metadata_blocks():
    packet = _base_shell_packet(
        consumption_plan_metadata={
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "consumption_status": "unknown_status",
            "consumption_action": "prepare_answer_plan_metadata_only",
            "allowed_next_metadata_step": "prepare_answer_plan_metadata_only",
            "user_visible_status": "answer-plan metadata only",
            "operator_visible_summary": "answer-plan metadata only",
            "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        }
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_nested_consumption_plan_metadata" in validation["blocked_labels"]


def test_invalid_nested_answer_plan_metadata_blocks():
    packet = _base_shell_packet(
        answer_plan_metadata={
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "answer_mode": "unknown_mode",
            "allowed_answer_scope": "current_message_only",
            "answer_status": "clarification_required",
            "user_visible_status": "clarification needed",
            "operator_visible_summary": "clarification required; metadata only",
            "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        }
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_nested_answer_plan_metadata" in validation["blocked_labels"]


def test_runtime_wiring_remains_blocked():
    packet = _base_shell_packet(
        shell_state="shell_blocked",
        shell_decision="refuse_runtime_wiring",
        shell_packet_type="shell_blocked_packet",
        blocked_authority="runtime_wiring_boundary",
        user_visible_status="This is blocked until a future approved boundary exists.",
        operator_visible_summary="runtime wiring boundary; blocked metadata only",
        selected_next_metadata_step="refuse_runtime_wiring",
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["shell_decision"] == "refuse_runtime_wiring"


def test_final_answer_execution_remains_blocked():
    packet = _base_shell_packet(
        shell_state="shell_blocked",
        shell_decision="block_before_runtime",
        shell_packet_type="shell_blocked_packet",
        blocked_authority="final_answer_boundary",
        user_visible_status="This is blocked until a future approved boundary exists.",
        operator_visible_summary="final answer boundary; blocked metadata only",
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["shell_packet"]["blocked_authority"] == "final_answer_boundary"



def test_retrieval_searxng_execution_remains_candidate_only():
    packet = _base_shell_packet(
        shell_state="shell_metadata_dry_run_only",
        shell_decision="prepare_retrieval_request_metadata_candidate",
        shell_packet_type="shell_retrieval_request_candidate_packet",
        blocked_authority="retrieval_candidate_boundary",
        evidence_retrieval_metadata={
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "retrieval_need_class": "approved_evidence_packet",
            "retrieval_status": "metadata only",
            "operator_visible_summary": "retrieval decision metadata only",
            "denied_authority": {field: False for field in SHELL_DENIED_AUTHORITY_FIELDS_V1},
        },
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["classification"] == "retrieval_request_candidate"



def test_tool_execution_remains_candidate_only():
    packet = _base_shell_packet(
        shell_state="shell_metadata_dry_run_only",
        shell_decision="prepare_tool_lane_candidate_metadata",
        shell_packet_type="shell_tool_lane_candidate_packet",
        blocked_authority="tool_lane_candidate_boundary",
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["classification"] == "tool_lane_candidate"



def test_persistence_mutation_remains_candidate_only():
    packet = _base_shell_packet(
        shell_state="shell_metadata_dry_run_only",
        shell_decision="prepare_persistence_candidate_metadata",
        shell_packet_type="shell_persistence_candidate_packet",
        blocked_authority="persistence_candidate_boundary",
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["classification"] == "persistence_candidate"



def test_weslr_io_remains_blocked():
    packet = _base_shell_packet(
        shell_state="shell_blocked",
        shell_decision="block_before_runtime",
        shell_packet_type="shell_blocked_packet",
        blocked_authority="weslr_io_boundary",
        user_visible_status="This is blocked until a future approved boundary exists.",
        operator_visible_summary="weslr io boundary; blocked metadata only",
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["shell_packet"]["blocked_authority"] == "weslr_io_boundary"



def test_ui_consumption_remains_blocked():
    packet = _base_shell_packet(
        shell_state="shell_metadata_dry_run_only",
        shell_decision="build_consumption_plan_metadata",
        shell_packet_type="shell_observability_packet",
        blocked_authority="ui_consumption_boundary",
    )
    validation = validate_controlled_project_chat_shell_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["classification"] == "observability"


@pytest.mark.parametrize("phrase", FORBIDDEN_USER_VISIBLE_STATUS_CASES)
def test_forbidden_user_visible_status_cases_block(phrase):
    validation = validate_controlled_project_chat_shell_packet_v1(
        _base_shell_packet(user_visible_status=phrase, operator_visible_summary=phrase)
    )
    assert validation["blocked"] is True
    assert "user_visible_status_forbidden_phrase" in validation["blocked_labels"]


def test_safe_user_visible_status_passes():
    validation = validate_controlled_project_chat_shell_packet_v1(_base_shell_packet(user_visible_status="metadata only", operator_visible_summary="metadata only"))
    assert validation["blocked"] is False


def test_denied_authority_fields_remain_false():
    validation = validate_controlled_project_chat_shell_packet_v1(_base_shell_packet())
    denied = validation["shell_packet"]["denied_authority"]
    assert set(denied) == set(SHELL_DENIED_AUTHORITY_FIELDS_V1)
    assert all(not value for value in denied.values())


def test_json_safe_conversion_works():
    safe_value = to_controlled_project_chat_shell_json_safe_v1({"packet": {"items": {1, 2}}, "tuple": ("a", "b")})
    assert safe_value["packet"]["items"] == [1, 2] or safe_value["packet"]["items"] == [2, 1]
    json.dumps(safe_value, sort_keys=True)


def test_summary_is_compact_and_safe():
    summary = summarize_controlled_project_chat_shell_packet_v1(_base_shell_packet())
    assert "Unknown Engine" not in summary["summary_text"]
    assert "final answer" not in summary["summary_text"].lower()
    json.dumps(summary, sort_keys=True)


def test_examples_are_synthetic_only():
    examples = build_initial_controlled_project_chat_shell_examples_v1()
    assert examples
    assert all(example["project_id"] == "project-001" for example in examples)
    assert all("final answer text" not in json.dumps(example).lower() for example in examples)


def test_validation_returns_metadata_not_exceptions():
    validation = validate_controlled_project_chat_shell_packet_v1(_base_shell_packet())
    assert isinstance(validation, dict)
    assert "blocked_labels" in validation
    assert "shell_packet" in validation


def test_static_source_scan_confirms_no_filesystem_network_subprocess_runtime_or_protected_imports():
    helper_text = HELPER_PATH.read_text()
    for forbidden in ["open(", "subprocess", "requests", "socket", ".weslr", "chat_responder", "main.py", "dialogue", "chat_ui"]:
        assert forbidden not in helper_text


def test_protected_file_drift_remains_absent():
    helper_text = HELPER_PATH.read_text()
    for protected in PROTECTED_FILES:
        assert protected not in helper_text


@pytest.mark.parametrize(
    "builder,packet",
    [
        (
            "consumption",
            _base_consumption_plan(),
        ),
        (
            "dry_run",
            _base_dry_run(_base_answer_plan()),
        ),
        (
            "answer_plan",
            _base_answer_plan(),
        ),
    ],
)
def test_existing_dependency_helpers_still_pass(builder, packet):
    if builder == "consumption":
        validation = validate_project_chat_dry_run_consumption_plan_v1(packet)
        assert validation["blocked"] is False
    elif builder == "dry_run":
        validation = validate_project_chat_runtime_dry_run_v1(packet)
        assert validation["blocked"] is False
    else:
        validation = validate_project_chat_answer_plan_v1(packet)
        assert validation["blocked"] is False
