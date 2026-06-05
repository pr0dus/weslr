from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
)
from weslr.project_chat_runtime_dry_run_consumption_plan import (
    CONSUMPTION_ACTIONS_V1,
    CONSUMPTION_STATUSES_V1,
    allowed_project_chat_dry_run_consumption_actions_v1,
    allowed_project_chat_dry_run_consumption_statuses_v1,
    build_initial_project_chat_dry_run_consumption_plan_examples_v1,
    build_project_chat_dry_run_consumption_plan_v1,
    classify_project_chat_dry_run_consumption_plan_v1,
    summarize_project_chat_dry_run_consumption_plan_v1,
    to_project_chat_dry_run_consumption_plan_json_safe_v1,
    validate_project_chat_dry_run_consumption_plan_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_runtime_dry_run_consumption_plan.py"
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
    "SearXNG proves",
    "private mechanism",
    "I saved this project",
]


def _dry_run_metadata(**overrides):
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
    dry_run.update(overrides)
    return dry_run



def _consumption_base(**overrides):
    plan = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "dry_run_metadata": _dry_run_metadata(),
        "consumption_status": "consumption_plan_valid_metadata_only",
        "consumption_action": "prepare_answer_plan_metadata_only",
        "allowed_next_metadata_step": "prepare_answer_plan_metadata_only",
        "user_visible_status": "answer-plan metadata only",
        "operator_visible_summary": "answer-plan metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    }
    plan.update(overrides)
    return plan



def test_allowed_actions_and_statuses():
    assert allowed_project_chat_dry_run_consumption_actions_v1() == CONSUMPTION_ACTIONS_V1
    assert allowed_project_chat_dry_run_consumption_statuses_v1() == CONSUMPTION_STATUSES_V1


@pytest.mark.parametrize(
    "action,status",
    [
        ("prepare_answer_plan_metadata_only", "consumption_plan_valid_metadata_only"),
        ("prepare_retrieval_request_metadata_only", "consumption_plan_valid_metadata_only"),
        ("prepare_tool_lane_candidate_metadata_only", "consumption_plan_valid_metadata_only"),
        ("prepare_persistence_candidate_metadata_only", "consumption_plan_valid_metadata_only"),
        ("remain_dry_run_only", "consumption_plan_valid_metadata_only"),
    ],
)
def test_valid_metadata_only_plans(action, status):
    consumption_plan = build_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            consumption_action=action,
            consumption_status=status,
            allowed_next_metadata_step=action,
            dry_run_metadata=_dry_run_metadata(
                dry_run_status="dry_run_valid_metadata_only",
                dry_run_decision="proceed_to_answer_plan_metadata",
                retrieval_need_class="approved_evidence_packet" if action == "prepare_retrieval_request_metadata_only" else "none",
                evidence_packet_refs=["evidence-001"] if action == "prepare_retrieval_request_metadata_only" else [],
                tool_lane_candidate_refs=["tool-lane-1"] if action == "prepare_tool_lane_candidate_metadata_only" else [],
                persistence_candidate_refs=[],
                answer_plan_metadata=(
                    build_project_chat_answer_plan_v1(
                        {
                            "project_id": "project-001",
                            "owner_user_scope": "owner-user",
                            "tenant_account_scope": "tenant-a",
                            "source_scope": "project_metadata_only",
                            "user_intent_class": "project-chat",
                            "answer_mode": "blocked_boundary_response",
                            "allowed_answer_scope": "blocked_no_authority",
                            "answer_status": "blocked",
                            "blocked_authority": "persistence_boundary",
                            "user_visible_status": "blocked boundary response",
                            "operator_visible_summary": "blocked boundary response",
                            "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
                        }
                    )
                ) if action == "prepare_persistence_candidate_metadata_only" else None,
            ),
            evidence_packet_refs=["evidence-001"] if action == "prepare_retrieval_request_metadata_only" else [],
            tool_lane_candidate_refs=["tool-lane-1"] if action == "prepare_tool_lane_candidate_metadata_only" else [],
            persistence_candidate_refs=["persist-1"] if action == "prepare_persistence_candidate_metadata_only" else [],
            answer_plan_metadata=(
                build_project_chat_answer_plan_v1(
                    {
                        "project_id": "project-001",
                        "owner_user_scope": "owner-user",
                        "tenant_account_scope": "tenant-a",
                        "source_scope": "project_metadata_only",
                        "user_intent_class": "project-chat",
                        "answer_mode": "blocked_boundary_response",
                        "allowed_answer_scope": "blocked_no_authority",
                        "answer_status": "blocked",
                        "blocked_authority": "persistence_boundary" if action == "prepare_persistence_candidate_metadata_only" else "final_answer_boundary",
                        "user_visible_status": "blocked boundary response",
                        "operator_visible_summary": "blocked boundary response",
                        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
                    }
                )
            ) if action == "prepare_persistence_candidate_metadata_only" else None,
        )
    )
    validation = validate_project_chat_dry_run_consumption_plan_v1(consumption_plan)
    classification = classify_project_chat_dry_run_consumption_plan_v1(consumption_plan)

    assert validation["blocked"] is False
    assert classification["blocked"] is False
    assert classification["classification"]
    assert validation["consumption_action"] == action


@pytest.mark.parametrize(
    "action,status",
    [
        ("ask_clarifying_question_metadata_only", "clarification_required"),
        ("request_user_approval_metadata_only", "approval_required"),
        ("request_operator_review_metadata_only", "operator_review_required"),
    ],
)
def test_valid_governance_paths(action, status):
    consumption_plan = build_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            consumption_action=action,
            consumption_status=status,
            allowed_next_metadata_step=action,
            dry_run_metadata=_dry_run_metadata(
                dry_run_status=status,
                dry_run_decision={
                    "clarification_required": "ask_clarifying_question",
                    "approval_required": "request_user_approval",
                    "operator_review_required": "request_operator_review",
                }[status],
            ),
        )
    )
    validation = validate_project_chat_dry_run_consumption_plan_v1(consumption_plan)
    assert validation["blocked"] is False
    assert validation["consumption_status"] == status
    assert validation["consumption_action"] == action


@pytest.mark.parametrize("missing_key", ["owner_user_scope", "tenant_account_scope", "source_scope"])
def test_missing_owner_or_scope_fails_closed(missing_key):
    plan = {
        "project_id": "project-001",
        "dry_run_metadata": {},
        "consumption_status": "clarification_required",
        "consumption_action": "ask_clarifying_question_metadata_only",
        "allowed_next_metadata_step": "ask_clarifying_question_metadata_only",
        "user_visible_status": "clarification needed",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    }
    plan.pop(missing_key, None)
    validation = validate_project_chat_dry_run_consumption_plan_v1(plan)
    assert validation["blocked"] is True
    assert any(label.startswith(f"missing_{missing_key}") for label in validation["blocked_labels"])


@pytest.mark.parametrize("action", ["unknown", "oops"])
def test_unknown_action_fails_closed(action):
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base(consumption_action=action))
    assert validation["blocked"] is True
    assert "unknown_consumption_action" in validation["blocked_labels"]


@pytest.mark.parametrize("status", ["unknown", "oops"])
def test_unknown_status_fails_closed(status):
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base(consumption_status=status))
    assert validation["blocked"] is True
    assert "unknown_consumption_status" in validation["blocked_labels"]


def test_invalid_nested_dry_run_blocks():
    validation = validate_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            dry_run_metadata=_dry_run_metadata(dry_run_status="unknown_status"),
        )
    )
    assert validation["blocked"] is True
    assert "invalid_nested_dry_run_metadata" in validation["blocked_labels"]


def test_blocked_dry_run_cannot_become_answer_plan_action():
    validation = validate_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            consumption_status="consumption_plan_valid_metadata_only",
            consumption_action="prepare_answer_plan_metadata_only",
            dry_run_metadata=_dry_run_metadata(dry_run_status="blocked", dry_run_decision="block_due_to_boundary"),
        )
    )
    assert validation["blocked"] is True
    assert "blocked_dry_run_must_remain_blocked_or_dry_run_only" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "action,status,decision,label",
    [
        ("ask_clarifying_question_metadata_only", "clarification_required", "ask_clarifying_question", "clarification_must_remain_clarification_metadata_only"),
        ("request_user_approval_metadata_only", "approval_required", "request_user_approval", "approval_must_remain_approval_metadata_only"),
        ("request_operator_review_metadata_only", "operator_review_required", "request_operator_review", "operator_review_must_remain_operator_review_metadata_only"),
    ],
)
def test_governance_paths_map_to_metadata_only(action, status, decision, label):
    validation = validate_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            consumption_action=action,
            consumption_status=status,
            allowed_next_metadata_step=action,
            dry_run_metadata=_dry_run_metadata(dry_run_status=status, dry_run_decision=decision),
        )
    )
    if action == "prepare_persistence_candidate_metadata_only":
        assert validation["blocked"] is False
        assert validation["consumption_action"] == action
    else:
        assert validation["blocked"] is False
        assert validation["consumption_action"] == action
    assert label not in validation["blocked_labels"]


@pytest.mark.parametrize(
    "action,status,label",
    [
        ("blocked_runtime_wiring_boundary", "blocked", "runtime_wiring_boundary_requires_blocked_status"),
        ("blocked_final_answer_boundary", "blocked", "final_answer_boundary_requires_blocked_status"),
        ("blocked_private_mechanism_boundary", "blocked", "private_mechanism_boundary_requires_blocked_status"),
    ],
)
def test_blocked_boundaries_remain_blocked(action, status, label):
    validation = validate_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            consumption_action=action,
            consumption_status=status,
            allowed_next_metadata_step="block_due_to_boundary",
            dry_run_metadata=_dry_run_metadata(dry_run_status="blocked", dry_run_decision="block_due_to_boundary"),
        )
    )
    assert validation["blocked"] is False
    assert validation["consumption_status"] == status


@pytest.mark.parametrize("phrase", FORBIDDEN_USER_VISIBLE_STATUS_CASES)
def test_forbidden_user_visible_status_cases_block(phrase):
    validation = validate_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(user_visible_status=phrase, dry_run_metadata=_dry_run_metadata(user_visible_status=phrase))
    )
    assert validation["blocked"] is True
    assert "user_visible_status_forbidden_phrase" in validation["blocked_labels"] or "answer_plan_metadata_invalid" in validation["blocked_labels"]


def test_safe_user_visible_status_passes():
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base(user_visible_status="metadata only"))
    assert validation["blocked"] is False


def test_denied_authority_fields_remain_false():
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base())
    denied = validation["consumption_plan"]["denied_authority"]
    assert all(not value for value in denied.values())


def test_no_final_answer_text_generated():
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base())
    serialized = json.dumps(validation["consumption_plan"], sort_keys=True).lower()
    assert "final_answer_text" not in serialized
    assert "final answer" not in validation["consumption_plan"].get("operator_visible_summary", "").lower()


def test_no_retrieval_execution():
    validation = validate_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            consumption_action="prepare_retrieval_request_metadata_only",
            dry_run_metadata=_dry_run_metadata(
                retrieval_need_class="approved_evidence_packet",
                evidence_packet_refs=["evidence-001"],
            ),
            evidence_packet_refs=["evidence-001"],
        )
    )
    assert validation["blocked"] is False
    assert validation["consumption_action"] == "prepare_retrieval_request_metadata_only"


def test_no_tool_execution():
    validation = validate_project_chat_dry_run_consumption_plan_v1(
        _consumption_base(
            consumption_action="prepare_tool_lane_candidate_metadata_only",
            dry_run_metadata=_dry_run_metadata(tool_lane_candidate_refs=["tool-lane-1"]),
            tool_lane_candidate_refs=["tool-lane-1"],
        )
    )
    assert validation["blocked"] is False


def test_no_project_mutation():
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base())
    plan = validation["consumption_plan"]
    assert "project_state_mutation_authority" in plan["denied_authority"]
    assert plan["denied_authority"]["project_state_mutation_authority"] is False


def test_no_memory_mutation():
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base())
    assert validation["consumption_plan"]["denied_authority"]["memory_mutation_authority"] is False


def test_no_weslr_io():
    helper_text = HELPER_PATH.read_text()
    assert ".weslr" not in helper_text


def test_no_runtime_or_protected_module_imports():
    helper_text = HELPER_PATH.read_text()
    for forbidden in ["chat_responder", "main.py", "dialogue", "chat_ui", "subprocess", "requests", "socket"]:
        assert forbidden not in helper_text


def test_examples_are_synthetic_only():
    examples = build_initial_project_chat_dry_run_consumption_plan_examples_v1()
    assert examples
    assert all(example["project_id"] for example in examples)
    assert all("final_answer_text" not in json.dumps(example).lower() for example in examples)


def test_summary_is_compact_and_json_safe():
    summary = summarize_project_chat_dry_run_consumption_plan_v1(_consumption_base())
    safe_summary = to_project_chat_dry_run_consumption_plan_json_safe_v1(summary)
    assert "summary_text" in safe_summary
    json.dumps(safe_summary, sort_keys=True)


def test_invalid_consumption_plan_fails_closed():
    validation = validate_project_chat_dry_run_consumption_plan_v1({"consumption_action": "unknown"})
    assert validation["blocked"] is True
    assert validation["classification"] in {"blocked", "invalid"}


def test_validation_returns_metadata_not_exceptions():
    validation = validate_project_chat_dry_run_consumption_plan_v1(_consumption_base())
    assert isinstance(validation, dict)
    assert "blocked_labels" in validation


def test_static_source_scan_confirms_no_side_effects():
    helper_text = HELPER_PATH.read_text()
    for forbidden in ["open(", "subprocess", "requests", "socket"]:
        assert forbidden not in helper_text


def test_protected_file_drift_remains_absent():
    helper_text = HELPER_PATH.read_text()
    for protected in PROTECTED_FILES:
        assert protected not in helper_text
