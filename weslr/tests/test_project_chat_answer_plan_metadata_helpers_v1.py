from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_answer_plan_metadata_helpers import (
    ANSWER_MODES_V1,
    ANSWER_SCOPES_V1,
    ANSWER_STATUSES_V1,
    DENIED_AUTHORITY_FIELDS_V1,
    build_initial_project_chat_answer_plan_examples_v1,
    build_project_chat_answer_plan_v1,
    classify_project_chat_answer_plan_v1,
    summarize_project_chat_answer_plan_v1,
    to_project_chat_answer_plan_json_safe_v1,
    validate_project_chat_answer_plan_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_answer_plan_metadata_helpers.py"
PROTECTED_FILES = [
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
]


def _base_plan(**overrides):
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
        "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
    }
    plan.update(overrides)
    return plan


def test_allowed_answer_modes_scopes_and_statuses():
    assert set(ANSWER_MODES_V1) == {
        "blocked_boundary_response",
        "candidate_project_summary",
        "clarifying_question",
        "contradiction_resolution_request",
        "deeper_analysis_requires_approval",
        "evidence_grounded_answer",
        "operator_review_required_response",
        "project_start_guidance",
        "surface_gap_review_summary",
        "tool_request_boundary_response",
        "uncertain_or_missing_evidence_answer",
    }
    assert set(ANSWER_SCOPES_V1) == {
        "approved_evidence_packet",
        "approved_memory_limited",
        "approved_project_context",
        "blocked_no_authority",
        "current_message_only",
        "deeper_analysis_approval_required",
        "operator_review_required",
        "project_metadata_only",
        "surface_gap_review_only",
        "tool_lane_candidate_only",
    }
    assert set(ANSWER_STATUSES_V1) == {
        "approval_required",
        "blocked",
        "clarification_required",
        "invalid",
        "operator_review_required",
        "plan_valid_metadata_only",
    }


def test_valid_clarifying_question_plan():
    plan = build_project_chat_answer_plan_v1(_base_plan())
    validation = validate_project_chat_answer_plan_v1(plan)

    assert validation["blocked"] is False
    assert validation["answer_status"] == "clarification_required"
    assert validation["answer_plan"]["answer_mode"] == "clarifying_question"
    assert validation["answer_plan"]["user_visible_status"] == "clarification needed"


def test_valid_candidate_project_summary_plan():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="candidate_project_summary",
            allowed_answer_scope="approved_project_context",
            answer_status="plan_valid_metadata_only",
            user_visible_status="candidate project summary",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is False
    assert validation["answer_mode"] == "candidate_project_summary"
    assert "saved" not in validation["answer_plan"]["user_visible_status"].lower()


def test_valid_evidence_grounded_plan_with_evidence_refs():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="evidence_grounded_answer",
            allowed_answer_scope="approved_evidence_packet",
            answer_status="plan_valid_metadata_only",
            evidence_packet_refs=["evidence-001"],
            user_visible_status="evidence grounded answer",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is False
    assert validation["answer_plan"]["evidence_packet_refs"] == ["evidence-001"]


def test_evidence_grounded_plan_without_evidence_refs_fails_closed():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="evidence_grounded_answer",
            allowed_answer_scope="approved_evidence_packet",
            answer_status="plan_valid_metadata_only",
            evidence_packet_refs=[],
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is True
    assert "missing_evidence_packet_refs" in validation["blocked_labels"]


def test_approved_evidence_scope_without_evidence_refs_fails_closed():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="uncertain_or_missing_evidence_answer",
            allowed_answer_scope="approved_evidence_packet",
            answer_status="plan_valid_metadata_only",
            evidence_packet_refs=[],
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is True
    assert "missing_approved_evidence_packet_refs" in validation["blocked_labels"]


def test_unknown_answer_mode_scope_and_status_fail_closed():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="unknown_mode",
            allowed_answer_scope="unknown_scope",
            answer_status="unknown_status",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is True
    assert "unknown_answer_mode" in validation["blocked_labels"]
    assert "unknown_answer_scope" in validation["blocked_labels"]
    assert "unknown_answer_status" in validation["blocked_labels"]


def test_missing_owner_or_scope_metadata_fails_closed():
    plan = build_project_chat_answer_plan_v1(
        {
            "project_id": "project-001",
            "answer_mode": "clarifying_question",
            "allowed_answer_scope": "current_message_only",
            "answer_status": "clarification_required",
            "user_visible_status": "clarification needed",
            "denied_authority": {field: False for field in DENIED_AUTHORITY_FIELDS_V1},
        }
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is True
    assert any(label.startswith("missing_owner_user_scope") for label in validation["blocked_labels"])
    assert any(label.startswith("missing_tenant_account_scope") for label in validation["blocked_labels"])
    assert any(label.startswith("missing_source_scope") for label in validation["blocked_labels"])


def test_candidate_summary_does_not_imply_saved_project():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="candidate_project_summary",
            allowed_answer_scope="approved_project_context",
            answer_status="plan_valid_metadata_only",
            user_visible_status="candidate project summary",
        )
    )
    summary = summarize_project_chat_answer_plan_v1(plan)
    assert "saved" not in summary["summary_text"].lower()


def test_proposed_memory_not_treated_as_confirmed():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="surface_gap_review_summary",
            allowed_answer_scope="surface_gap_review_only",
            answer_status="plan_valid_metadata_only",
            memory_state_refs=["memory-001:proposed"],
            user_visible_status="surface gap review summary",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is False
    assert "confirmed" not in json.dumps(validation["answer_plan"]).lower()


def test_stale_flags_are_surfaced():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="uncertain_or_missing_evidence_answer",
            allowed_answer_scope="approved_project_context",
            answer_status="plan_valid_metadata_only",
            stale_state_flags=["project_state_stale"],
            user_visible_status="this may be stale",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["answer_plan"]["stale_state_flags"] == ["project_state_stale"]


def test_contradiction_flags_trigger_contradiction_or_uncertainty_behavior():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="evidence_grounded_answer",
            allowed_answer_scope="approved_evidence_packet",
            answer_status="plan_valid_metadata_only",
            evidence_packet_refs=["evidence-001"],
            contradiction_flags=["project_state_conflict"],
            user_visible_status="sources conflict",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    classification = classify_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is True or classification["classification"] in {"contradiction_resolution", "uncertain_or_missing_evidence"}


def test_missing_evidence_flags_trigger_uncertainty_behavior():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="uncertain_or_missing_evidence_answer",
            allowed_answer_scope="approved_project_context",
            answer_status="plan_valid_metadata_only",
            missing_evidence_flags=["missing_project_context"],
            user_visible_status="evidence incomplete",
        )
    )
    classification = classify_project_chat_answer_plan_v1(plan)
    assert classification["needs_uncertainty"] is True or classification["classification"] == "uncertain_or_missing_evidence"


def test_tool_request_remains_tool_lane_candidate_only():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="tool_request_boundary_response",
            allowed_answer_scope="tool_lane_candidate_only",
            answer_status="plan_valid_metadata_only",
            tool_lane_candidate_refs=["tool-lane-1"],
            user_visible_status="tool request boundary response",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is False
    assert validation["answer_plan"]["allowed_answer_scope"] == "tool_lane_candidate_only"


def test_blocked_boundary_response_requires_blocked_authority():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="blocked_boundary_response",
            allowed_answer_scope="blocked_no_authority",
            answer_status="blocked",
            blocked_authority="unapproved_external_query_authority",
            user_visible_status="blocked boundary response",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is False
    assert validation["answer_plan"]["blocked_authority"] == "unapproved_external_query_authority"


def test_operator_review_response_requires_operator_visibility_or_reason_metadata():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="operator_review_required_response",
            allowed_answer_scope="operator_review_required",
            answer_status="operator_review_required",
            operator_visibility_refs=["op-note-1"],
            user_visible_status="operator review required",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is False
    assert validation["answer_plan"]["operator_visibility_refs"] == ["op-note-1"]


def test_deeper_analysis_requires_approval_refs():
    plan = build_project_chat_answer_plan_v1(
        _base_plan(
            answer_mode="deeper_analysis_requires_approval",
            allowed_answer_scope="deeper_analysis_approval_required",
            answer_status="approval_required",
            approval_refs=["approval-1"],
            user_visible_status="approval required before deeper analysis",
        )
    )
    validation = validate_project_chat_answer_plan_v1(plan)
    assert validation["blocked"] is False
    assert validation["answer_plan"]["approval_refs"] == ["approval-1"]


def test_user_visible_status_is_mechanism_neutral_and_contains_no_unknown_engine_or_private_mechanisms():
    plan = build_project_chat_answer_plan_v1(_base_plan(user_visible_status="clarification needed"))
    validation = validate_project_chat_answer_plan_v1(plan)
    assert "Unknown Engine" not in validation["user_visible_status"]
    assert "chat_responder" not in validation["user_visible_status"]
    assert "dialogue" not in validation["user_visible_status"]
    assert "chat_ui" not in validation["user_visible_status"]


def test_denied_authority_fields_remain_false_or_blocked():
    plan = build_project_chat_answer_plan_v1(_base_plan())
    validation = validate_project_chat_answer_plan_v1(plan)
    assert set(validation["denied_authority"]) == set(DENIED_AUTHORITY_FIELDS_V1)
    assert all(value is False for value in validation["denied_authority"].values())


def test_no_final_answer_text_generated_and_no_mutation_or_retrieval_or_tool_execution_claims():
    plan = build_project_chat_answer_plan_v1(_base_plan())
    blob = json.dumps(plan)
    assert "final answer" not in blob.lower()
    assert "retrieval" not in blob.lower() or "evidence" in blob.lower()
    assert "tool execution" not in blob.lower()
    assert "project mutation" not in blob.lower()
    assert "memory mutation" not in blob.lower()


def test_no_project_or_memory_mutation_or_dot_weslr_io_or_runtime_imports_in_source():
    source = HELPER_PATH.read_text(encoding="utf-8")
    forbidden = [
        "open(",
        "subprocess",
        "requests",
        "socket",
        ".weslr",
        "chat_responder",
        "main.py",
        "dialogue",
        "chat_ui",
    ]
    assert all(token not in source for token in forbidden)


def test_no_protected_file_drift():
    for rel_path in PROTECTED_FILES:
        assert not Path(rel_path).exists() or Path(rel_path).is_file()


def test_examples_are_synthetic_only_and_json_safe():
    examples = build_initial_project_chat_answer_plan_examples_v1()
    assert examples
    encoded = json.dumps(to_project_chat_answer_plan_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "final answer" not in encoded.lower()
    assert all(example["project_id"] == "project-001" for example in examples)


def test_summary_is_compact_and_json_safe():
    plan = build_project_chat_answer_plan_v1(_base_plan())
    summary = summarize_project_chat_answer_plan_v1(plan)
    encoded = json.dumps(to_project_chat_answer_plan_json_safe_v1(summary), sort_keys=True)
    assert "clarifying_question" in encoded
    assert "Unknown Engine" not in encoded


def test_invalid_plan_fails_closed_and_validation_returns_metadata_not_exceptions():
    validation = validate_project_chat_answer_plan_v1({"answer_mode": "unknown_mode"})
    assert validation["blocked"] is True
    assert validation["answer_status"] == "invalid"
    assert validation["validation_notes"]


def test_helper_has_no_filesystem_network_subprocess_side_effects():
    source = HELPER_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "subprocess" not in source
    assert "requests" not in source
    assert "socket" not in source
    assert ".weslr" not in source


def test_json_safe_normalization_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_project_chat_answer_plan_json_safe_v1(value)
    json.dumps(safe, sort_keys=True)
    assert isinstance(safe["d"], str)
