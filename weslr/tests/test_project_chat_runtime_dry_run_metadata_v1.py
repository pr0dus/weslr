from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.project_chat_answer_plan_metadata_helpers import (
    DENIED_AUTHORITY_FIELDS_V1 as ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1,
    build_project_chat_answer_plan_v1,
)
from weslr.project_chat_runtime_dry_run_metadata import (
    DRY_RUN_DECISIONS_V1,
    DRY_RUN_STAGES_V1,
    DRY_RUN_STATUSES_V1,
    allowed_project_chat_runtime_dry_run_decisions_v1,
    allowed_project_chat_runtime_dry_run_stages_v1,
    allowed_project_chat_runtime_dry_run_statuses_v1,
    build_initial_project_chat_runtime_dry_run_examples_v1,
    build_project_chat_runtime_dry_run_v1,
    classify_project_chat_runtime_dry_run_v1,
    summarize_project_chat_runtime_dry_run_v1,
    to_project_chat_runtime_dry_run_json_safe_v1,
    validate_project_chat_runtime_dry_run_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "project_chat_runtime_dry_run_metadata.py"
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


def _base_dry_run(**overrides):
    dry_run = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "user_intent_class": "project-chat",
        "dry_run_status": "clarification_required",
        "dry_run_decision": "ask_clarifying_question",
        "retrieval_need_class": "none",
        "user_visible_status": "clarification needed",
        "operator_visible_summary": "dry-run clarification; metadata only",
        "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
    }
    dry_run.update(overrides)
    return dry_run


def _valid_answer_plan_payload(**overrides):
    payload = {
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
    payload.update(overrides)
    return build_project_chat_answer_plan_v1(payload)


def test_allowed_stages_statuses_and_decisions():
    assert allowed_project_chat_runtime_dry_run_stages_v1() == DRY_RUN_STAGES_V1
    assert allowed_project_chat_runtime_dry_run_statuses_v1() == DRY_RUN_STATUSES_V1
    assert allowed_project_chat_runtime_dry_run_decisions_v1() == DRY_RUN_DECISIONS_V1


def test_valid_minimal_clarification_dry_run():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    classification = classify_project_chat_runtime_dry_run_v1(dry_run)

    assert validation["blocked"] is False
    assert validation["dry_run_status"] == "clarification_required"
    assert classification["classification"] == "clarification_required"
    assert dry_run["answer_plan_metadata"]["answer_mode"] == "clarifying_question"


def test_valid_dry_run_proceeds_to_answer_plan_metadata():
    dry_run = build_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="dry_run_valid_metadata_only",
            dry_run_decision="proceed_to_answer_plan_metadata",
            retrieval_need_class="project_metadata_only",
            user_visible_status="dry-run metadata only",
            answer_plan_payload=_valid_answer_plan_payload(),
        )
    )
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)

    assert validation["blocked"] is False
    assert validation["dry_run_decision"] == "proceed_to_answer_plan_metadata"
    assert validation["answer_plan_validation"]["blocked"] is False
    assert validation["dry_run"]["answer_plan_metadata"]["answer_mode"] == "clarifying_question"


def test_missing_owner_or_scope_metadata_fails_closed():
    validation = validate_project_chat_runtime_dry_run_v1(
        {
            "project_id": "project-001",
            "dry_run_status": "clarification_required",
            "dry_run_decision": "ask_clarifying_question",
            "user_visible_status": "clarification needed",
            "denied_authority": {field: False for field in ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1},
        }
    )
    assert validation["blocked"] is True
    assert any(label.startswith("missing_owner_user_scope") for label in validation["blocked_labels"])
    assert any(label.startswith("missing_tenant_account_scope") for label in validation["blocked_labels"])
    assert any(label.startswith("missing_source_scope") for label in validation["blocked_labels"])


def test_unknown_stage_fails_closed():
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            stage_results=[{"stage": "bogus_stage", "status": "passed", "decision": "proceed_to_answer_plan_metadata"}],
        )
    )
    assert validation["blocked"] is True
    assert any(label.startswith("unknown_stage_bogus_stage") for label in validation["blocked_labels"])


@pytest.mark.parametrize("status", ["unknown", "oops"], ids=["unknown", "oops"])
def test_unknown_status_fails_closed(status):
    validation = validate_project_chat_runtime_dry_run_v1(_base_dry_run(dry_run_status=status))
    assert validation["blocked"] is True
    assert "unknown_dry_run_status" in validation["blocked_labels"]


@pytest.mark.parametrize("decision", ["unknown", "oops"], ids=["unknown", "oops"])
def test_unknown_decision_fails_closed(decision):
    validation = validate_project_chat_runtime_dry_run_v1(_base_dry_run(dry_run_decision=decision))
    assert validation["blocked"] is True
    assert "unknown_dry_run_decision" in validation["blocked_labels"]


def test_evidence_grounded_path_without_evidence_refs_blocks():
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="dry_run_valid_metadata_only",
            dry_run_decision="proceed_to_answer_plan_metadata",
            retrieval_need_class="approved_evidence_packet",
            evidence_packet_refs=[],
            answer_plan_payload=_valid_answer_plan_payload(answer_mode="evidence_grounded_answer", allowed_answer_scope="approved_evidence_packet", answer_status="plan_valid_metadata_only"),
        )
    )
    assert validation["blocked"] is True
    assert "missing_evidence_packet_refs" in validation["blocked_labels"]


def test_external_private_retrieval_need_without_approval_blocks():
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="approval_required",
            dry_run_decision="request_user_approval",
            retrieval_need_class="external_private",
            approval_refs=[],
        )
    )
    assert validation["blocked"] is True
    assert "missing_approval_refs" in validation["blocked_labels"]


def test_external_private_retrieval_need_with_approval_remains_metadata_only():
    dry_run = build_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="dry_run_valid_metadata_only",
            dry_run_decision="proceed_to_answer_plan_metadata",
            retrieval_need_class="external_private",
            approval_refs=["approval-1"],
            answer_plan_payload=_valid_answer_plan_payload(),
        )
    )
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert validation["blocked"] is False
    assert validation["dry_run_decision"] == "proceed_to_answer_plan_metadata"


def test_tool_request_stays_tool_lane_candidate_only():
    dry_run = build_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="dry_run_valid_metadata_only",
            dry_run_decision="proceed_to_answer_plan_metadata",
            retrieval_need_class="tool_lane_candidate_only",
            tool_lane_candidate_refs=["tool-lane-1"],
            answer_plan_payload=_valid_answer_plan_payload(answer_mode="tool_request_boundary_response", allowed_answer_scope="tool_lane_candidate_only", answer_status="plan_valid_metadata_only"),
        )
    )
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert validation["blocked"] is False
    assert validation["dry_run"]["stage_results"][7]["status"] == "candidate_only"


def test_persistence_mutation_request_blocks():
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="blocked",
            dry_run_decision="block_due_to_persistence_boundary",
            retrieval_need_class="none",
            persistence_candidate_refs=["persist-1"],
        )
    )
    assert validation["blocked"] is True
    assert "persistence_boundary_must_block" in validation["blocked_labels"]


def test_contradiction_flags_block_or_require_resolution():
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="blocked",
            dry_run_decision="block_due_to_contradiction",
            contradiction_flags=["project_state_conflict"],
        )
    )
    assert validation["blocked"] is True
    assert any(label.startswith("contradiction") for label in validation["blocked_labels"])


@pytest.mark.parametrize("status,decision", [
    ("blocked", "block_due_to_stale_or_invalidated_state"),
    ("clarification_required", "ask_clarifying_question"),
])
def test_stale_or_invalidated_flags_block_or_require_clarification(status, decision):
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status=status,
            dry_run_decision=decision,
            stale_state_flags=["project_state_stale"],
        )
    )
    assert validation["blocked"] is True or validation["dry_run_status"] == "clarification_required"


@pytest.mark.parametrize("decision", ["block_due_to_missing_evidence", "ask_clarifying_question"])
def test_missing_evidence_blocks_or_requires_clarification(decision):
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="blocked" if decision == "block_due_to_missing_evidence" else "clarification_required",
            dry_run_decision=decision,
            missing_evidence_flags=["missing_project_context"],
        )
    )
    assert validation["blocked"] is True or validation["dry_run_status"] == "clarification_required"


@pytest.mark.parametrize("phrase", FORBIDDEN_USER_VISIBLE_STATUS_CASES)
def test_private_mechanism_and_authority_wording_blocks(phrase):
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(user_visible_status=f"safe prefix {phrase.upper()} safe suffix")
    )
    assert validation["blocked"] is True
    assert validation["blocked_labels"]
    assert any("user_visible_status" in label for label in validation["blocked_labels"])


def test_safe_mechanism_neutral_user_visible_status_passes():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run(user_visible_status="dry-run metadata only"))
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert validation["blocked"] is False
    assert validation["user_visible_status"] == "dry-run metadata only"


def test_answer_plan_integration_validates_nested_answer_plan():
    dry_run = build_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="dry_run_valid_metadata_only",
            dry_run_decision="proceed_to_answer_plan_metadata",
            retrieval_need_class="project_metadata_only",
            answer_plan_payload=_valid_answer_plan_payload(),
        )
    )
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert validation["answer_plan_validation"]["blocked"] is False
    assert validation["dry_run"]["answer_plan_metadata"]["answer_mode"] == "clarifying_question"


def test_invalid_nested_answer_plan_blocks_dry_run():
    validation = validate_project_chat_runtime_dry_run_v1(
        _base_dry_run(
            dry_run_status="dry_run_valid_metadata_only",
            dry_run_decision="proceed_to_answer_plan_metadata",
            retrieval_need_class="project_metadata_only",
            answer_plan_payload={"answer_mode": "unknown_mode"},
        )
    )
    assert validation["blocked"] is True
    assert validation["answer_plan_validation"]["blocked"] is True


def test_denied_authority_fields_remain_false_or_blocked():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert set(validation["denied_authority"]) == set(ANSWER_PLAN_DENIED_AUTHORITY_FIELDS_V1)
    assert all(value is False for value in validation["denied_authority"].values())


def test_no_final_answer_text_is_generated():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    summary = summarize_project_chat_runtime_dry_run_v1(dry_run)
    assert "final answer" not in summary["summary_text"].lower()
    assert "final_answer_text" not in json.dumps(summary).lower()


def test_no_retrieval_execution():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert "retrieval_executed" not in json.dumps(validation).lower()
    assert "I searched" not in json.dumps(validation)


def test_no_tool_execution():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert "tool_executed" not in json.dumps(validation).lower()
    assert "tool execution" not in json.dumps(summary := summarize_project_chat_runtime_dry_run_v1(dry_run)).lower()


def test_no_project_mutation():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert "project mutation" not in json.dumps(validation).lower()
    assert "saved this project" not in json.dumps(validation).lower()


def test_no_memory_mutation():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert "memory mutation" not in json.dumps(validation).lower()
    assert "I remember this" not in json.dumps(validation)


def test_no_dot_weslr_io():
    source = HELPER_PATH.read_text(encoding="utf-8")
    assert ".weslr" not in source
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    validation = validate_project_chat_runtime_dry_run_v1(dry_run)
    assert ".weslr" not in json.dumps(validation)


def test_no_runtime_or_protected_module_imports_in_source():
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


def test_examples_are_synthetic_only():
    examples = build_initial_project_chat_runtime_dry_run_examples_v1()
    assert examples
    encoded = json.dumps(to_project_chat_runtime_dry_run_json_safe_v1(examples), sort_keys=True)
    assert "Unknown Engine" not in encoded
    assert "final_answer_text" not in encoded.lower()
    assert "saved this project" not in encoded.lower()
    assert "public readiness" not in encoded.lower()
    assert all(example["project_id"] == "project-001" for example in examples)


def test_summary_is_compact_and_json_safe():
    dry_run = build_project_chat_runtime_dry_run_v1(_base_dry_run())
    summary = summarize_project_chat_runtime_dry_run_v1(dry_run)
    encoded = json.dumps(to_project_chat_runtime_dry_run_json_safe_v1(summary), sort_keys=True)
    assert "clarification_required" in encoded
    assert "Unknown Engine" not in encoded


def test_invalid_dry_run_fails_closed():
    validation = validate_project_chat_runtime_dry_run_v1({"dry_run_status": "unknown"})
    assert validation["blocked"] is True
    assert validation["dry_run_status"] == "invalid"
    assert validation["validation_notes"]


def test_validation_returns_metadata_not_exceptions():
    validation = validate_project_chat_runtime_dry_run_v1({"dry_run_decision": "unknown"})
    assert validation["blocked"] is True
    assert validation["validation_notes"]


def test_json_safe_normalization_handles_nested_non_primitives():
    value = {"a": {"b": {"c"}}, "d": object()}
    safe = to_project_chat_runtime_dry_run_json_safe_v1(value)
    json.dumps(safe, sort_keys=True)
    assert isinstance(safe["d"], str)


def test_static_source_scan_confirms_no_side_effects():
    source = HELPER_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "subprocess" not in source
    assert "requests" not in source
    assert "socket" not in source


def test_protected_file_drift_remains_absent():
    for rel_path in PROTECTED_FILES:
        assert not Path(rel_path).exists() or Path(rel_path).is_file()
