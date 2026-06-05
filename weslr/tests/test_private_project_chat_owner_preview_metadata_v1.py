from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import weslr.private_project_chat_owner_preview_metadata as owner_preview_meta
from weslr.private_project_chat_owner_preview_metadata import (
    OWNER_PREVIEW_PACKET_TYPES_V1,
    OWNER_PREVIEW_READINESS_LABELS_V1,
    OWNER_PREVIEW_STATUSES_V1,
    allowed_private_project_chat_owner_preview_packet_types_v1,
    allowed_private_project_chat_owner_preview_readiness_labels_v1,
    allowed_private_project_chat_owner_preview_statuses_v1,
    build_initial_private_project_chat_owner_preview_examples_v1,
    build_private_project_chat_owner_preview_packet_v1,
    classify_private_project_chat_owner_preview_packet_v1,
    summarize_private_project_chat_owner_preview_packet_v1,
    to_private_project_chat_owner_preview_json_safe_v1,
    validate_private_project_chat_owner_preview_packet_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "private_project_chat_owner_preview_metadata.py"
REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_NEW_FILES = {
    "weslr/private_project_chat_owner_preview_metadata.py",
    "weslr/tests/test_private_project_chat_owner_preview_metadata_v1.py",
    "docs/WESLR_PRIVATE_PROJECT_CHAT_OWNER_PREVIEW_METADATA_HELPERS_IMPLEMENTATION_REPORT_V1.md",
}
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}
EXPECTED_DENIED_FIELDS = (
    "runtime_wiring_authority",
    "chat" + "_" + "responder_authority",
    "final_answer_generation_authority",
    "retrieval_execution_authority",
    "searxng_execution_authority",
    "tool_execution_authority",
    "storage_database_authority",
    "weslr_io_authority",
    "project_state_mutation_authority",
    "memory_mutation_authority",
    "external_action_authority",
    "public_access_authority",
    "tester_access_authority",
    "ui_consumption_authority",
    "private_data_exposure_authority",
    "public_readiness_claim_authority",
)
SAFE_OWNER_VISIBLE_STATUS = "This is a private owner preview."
SAFE_OWNER_SUMMARY = "Owner preview metadata only."
SAFE_OPERATOR_SUMMARY = "Owner preview metadata only."

FORBIDDEN_USER_VISIBLE_PHRASES = [
    "Unknown Engine",
    "chat" + "_" + "responder",
    "I executed",
    "I searched",
    "I saved",
    "I remembered",
    "final answer",
    "runtime authority",
    "public ready",
    "certified",
    "conscious",
    "autonomous deployment",
]


def _base_packet(**overrides):
    packet = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
    }
    packet.update(overrides)
    return build_private_project_chat_owner_preview_packet_v1(packet)


@pytest.mark.parametrize("getter,expected", [
    (allowed_private_project_chat_owner_preview_statuses_v1, OWNER_PREVIEW_STATUSES_V1),
    (allowed_private_project_chat_owner_preview_packet_types_v1, OWNER_PREVIEW_PACKET_TYPES_V1),
    (allowed_private_project_chat_owner_preview_readiness_labels_v1, OWNER_PREVIEW_READINESS_LABELS_V1),
])
def test_allowed_enums_match_constants(getter, expected):
    assert getter() == expected


@pytest.mark.parametrize(
    "preview_packet_type,expected_status,expected_readiness,expected_classification",
    [
        ("preview_shell_decision_summary", "preview_metadata_only", "owner_preview_design_ready", "metadata_only"),
        ("preview_shell_blocked_summary", "preview_blocked", "owner_preview_blocked", "blocked"),
        ("preview_shell_clarification_summary", "preview_clarification_required", "owner_preview_requires_review", "clarification_required"),
        ("preview_shell_approval_summary", "preview_approval_required", "owner_preview_requires_review", "approval_required"),
        ("preview_shell_operator_review_summary", "preview_operator_review_required", "owner_preview_requires_review", "operator_review_required"),
        ("preview_answer_plan_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only"),
        ("preview_retrieval_request_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only"),
        ("preview_tool_lane_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only"),
        ("preview_persistence_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only"),
        ("preview_observability_summary", "preview_metadata_only", "future_ui_candidate", "observability"),
        ("preview_dry_run_summary", "preview_metadata_only", "metadata_preview_ready", "metadata_only"),
        ("preview_consumption_plan_summary", "preview_metadata_only", "metadata_preview_ready", "metadata_only"),
        ("preview_validation_summary", "preview_metadata_only", "metadata_preview_ready", "validation"),
    ],
)
def test_valid_preview_packets(preview_packet_type, expected_status, expected_readiness, expected_classification):
    packet = _base_packet(preview_packet_type=preview_packet_type)
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    classification = classify_private_project_chat_owner_preview_packet_v1(packet)
    summary = summarize_private_project_chat_owner_preview_packet_v1(packet)

    assert validation["blocked"] is False
    assert validation["preview_status"] == expected_status
    assert validation["readiness_label"] == expected_readiness
    assert validation["classification"] == expected_classification
    assert classification["classification"] == expected_classification
    assert summary["summary_text"].startswith("Private owner preview:")
    assert packet["preview_packet_id"].startswith("preview-")
    assert packet["owner_only_access"] is True
    assert packet["private_or_protected_staging_only"] is True


@pytest.mark.parametrize(
    "preview_packet_type,expected_status,expected_readiness,expected_classification,expected_user_status",
    [
        ("preview_shell_blocked_summary", "preview_blocked", "owner_preview_blocked", "blocked", "This path is blocked until a future approved boundary exists."),
        ("preview_shell_clarification_summary", "preview_clarification_required", "owner_preview_requires_review", "clarification_required", "This needs clarification."),
        ("preview_shell_approval_summary", "preview_approval_required", "owner_preview_requires_review", "approval_required", "This needs approval."),
        ("preview_shell_operator_review_summary", "preview_operator_review_required", "owner_preview_requires_review", "operator_review_required", "This needs operator review."),
        ("preview_answer_plan_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only", "This is only a candidate."),
        ("preview_retrieval_request_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only", "This is only a candidate."),
        ("preview_tool_lane_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only", "This is only a candidate."),
        ("preview_persistence_candidate_summary", "preview_candidate_only", "future_runtime_candidate", "candidate_only", "This is only a candidate."),
        ("preview_observability_summary", "preview_metadata_only", "future_ui_candidate", "observability", SAFE_OWNER_VISIBLE_STATUS),
    ],
)
def test_special_preview_packets(preview_packet_type, expected_status, expected_readiness, expected_classification, expected_user_status):
    packet = _base_packet(preview_packet_type=preview_packet_type)
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)

    assert validation["blocked"] is False
    assert validation["preview_status"] == expected_status
    assert validation["readiness_label"] == expected_readiness
    assert validation["classification"] == expected_classification
    assert validation["user_visible_status"] == expected_user_status


def test_missing_owner_or_scope_fails_closed():
    for field in ["project_id", "owner_user_scope", "tenant_account_scope", "source_scope"]:
        packet = _base_packet()
        packet.pop(field)
        validation = validate_private_project_chat_owner_preview_packet_v1(packet)
        assert validation["blocked"] is True
        assert any(label == f"missing_{field}" for label in validation["blocked_labels"])


@pytest.mark.parametrize("field", ["preview_status", "preview_packet_type", "readiness_label"])
def test_unknown_preview_enums_fail_closed(field):
    packet = _base_packet()
    packet[field] = "unknown-value"
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("unknown_") for label in validation["blocked_labels"])


def test_invalid_nested_shell_metadata_blocks():
    packet = _base_packet(
        shell_packet_metadata={
            "project_id": "project-001",
            "owner_user_scope": "",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "shell_state": "shell_metadata_dry_run_only",
            "shell_decision": "build_dry_run_metadata",
            "shell_packet_type": "shell_decision_packet",
            "user_visible_status": SAFE_OWNER_VISIBLE_STATUS,
            "operator_visible_summary": SAFE_OPERATOR_SUMMARY,
            "denied_authority": {field: False for field in EXPECTED_DENIED_FIELDS},
        }
    )
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_nested_shell_metadata" in validation["blocked_labels"]


def test_invalid_nested_dry_run_metadata_blocks():
    packet = _base_packet(
        dry_run_metadata={
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "dry_run_status": "bad",
            "dry_run_decision": "proceed_to_answer_plan_metadata",
            "retrieval_need_class": "none",
            "user_visible_status": SAFE_OWNER_VISIBLE_STATUS,
            "operator_visible_summary": SAFE_OPERATOR_SUMMARY,
            "denied_authority": {field: False for field in EXPECTED_DENIED_FIELDS},
            "answer_plan_payload": _base_packet()["answer_plan_metadata"],
        }
    )
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_nested_dry_run_metadata" in validation["blocked_labels"]


def test_invalid_nested_consumption_plan_metadata_blocks():
    packet = _base_packet(
        consumption_plan_metadata={
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "dry_run_metadata": _base_packet()["dry_run_metadata"],
            "answer_plan_metadata": _base_packet()["answer_plan_metadata"],
            "consumption_status": "bad",
            "consumption_action": "prepare_answer_plan_metadata_only",
            "allowed_next_metadata_step": "prepare_answer_plan_metadata_only",
            "user_visible_status": SAFE_OWNER_VISIBLE_STATUS,
            "operator_visible_summary": SAFE_OPERATOR_SUMMARY,
            "denied_authority": {field: False for field in EXPECTED_DENIED_FIELDS},
        }
    )
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_nested_consumption_plan_metadata" in validation["blocked_labels"]


def test_invalid_nested_answer_plan_metadata_blocks():
    packet = _base_packet(
        answer_plan_metadata={
            "project_id": "project-001",
            "owner_user_scope": "owner-user",
            "tenant_account_scope": "tenant-a",
            "source_scope": "project_metadata_only",
            "user_intent_class": "project-chat",
            "answer_mode": "bad",
            "allowed_answer_scope": "current_message_only",
            "answer_status": "clarification_required",
            "user_visible_status": SAFE_OWNER_VISIBLE_STATUS,
            "operator_visible_summary": SAFE_OPERATOR_SUMMARY,
            "denied_authority": {field: False for field in EXPECTED_DENIED_FIELDS},
        }
    )
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert "invalid_nested_answer_plan_metadata" in validation["blocked_labels"]


@pytest.mark.parametrize("field", ["public_access_authority", "tester_access_authority", "ui_consumption_authority"])
def test_public_or_tester_or_ui_access_remains_denied(field):
    denied = {name: False for name in EXPECTED_DENIED_FIELDS}
    denied[field] = True
    packet = _base_packet(denied_authority=denied)
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label == f"denied_authority_enabled_{field}" for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field",
    [
        "runtime_wiring_authority",
        "chat" + "_" + "responder_authority",
        "final_answer_generation_authority",
        "retrieval_execution_authority",
        "searxng_execution_authority",
        "tool_execution_authority",
        "storage_database_authority",
        "weslr_io_authority",
        "project_state_mutation_authority",
        "memory_mutation_authority",
        "external_action_authority",
        "private_data_exposure_authority",
        "public_readiness_claim_authority",
    ],
)
def test_execution_and_exposure_authorities_remain_blocked_when_enabled(field):
    denied = {name: False for name in EXPECTED_DENIED_FIELDS}
    denied[field] = True
    packet = _base_packet(denied_authority=denied)
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label == f"denied_authority_enabled_{field}" for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "phrase",
    FORBIDDEN_USER_VISIBLE_PHRASES,
)
def test_forbidden_user_visible_phrases_block(phrase):
    packet = _base_packet(user_visible_status=phrase, owner_visible_summary=SAFE_OWNER_SUMMARY, operator_visible_summary=SAFE_OPERATOR_SUMMARY)
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label == "forbidden_user_visible_status" for label in validation["blocked_labels"])


def test_safe_owner_preview_wording_passes():
    packet = _base_packet(user_visible_status=SAFE_OWNER_VISIBLE_STATUS)
    validation = validate_private_project_chat_owner_preview_packet_v1(packet)
    assert validation["blocked"] is False
    assert validation["user_visible_status"] == SAFE_OWNER_VISIBLE_STATUS


def test_denied_authority_fields_remain_false_by_default():
    packet = _base_packet()
    denied = packet["denied_authority"]
    assert set(denied) == set(EXPECTED_DENIED_FIELDS)
    assert all(not value for value in denied.values())


def test_json_safe_conversion_works():
    value = to_private_project_chat_owner_preview_json_safe_v1({"packet": {"items": {1, 2}}, "tuple": ("a", "b")})
    assert value["packet"]["items"] in ([1, 2], [2, 1])
    json.dumps(value, sort_keys=True)


def test_summary_is_compact_and_safe():
    summary = summarize_private_project_chat_owner_preview_packet_v1(_base_packet())
    assert "private owner preview" in summary["summary_text"].lower()
    assert "Unknown Engine" not in summary["summary_text"]
    assert "final answer" not in summary["summary_text"].lower()
    assert len(summary["summary_text"]) < 220
    json.dumps(summary, sort_keys=True)


def test_examples_are_synthetic_only():
    examples = build_initial_private_project_chat_owner_preview_examples_v1()
    assert examples
    assert all(example["owner_only_access"] is True for example in examples)
    assert all(example["private_or_protected_staging_only"] is True for example in examples)
    assert all(example["project_id"] == "project-001" for example in examples)
    assert all(example["preview_packet_id"].startswith("preview-") for example in examples)
    assert all(example["redaction_summary"] for example in examples)


def test_validation_returns_metadata_not_uncaught_exceptions():
    validation = validate_private_project_chat_owner_preview_packet_v1(_base_packet())
    assert isinstance(validation, dict)
    assert "blocked_labels" in validation
    assert "preview_packet" in validation
    assert "shell_validation" in validation


def test_static_source_scan_confirms_no_filesystem_network_subprocess_runtime_or_protected_imports():
    text = HELPER_PATH.read_text()
    for forbidden in ["open(", "subprocess", "requests", "socket", ".weslr", "chat_responder", "main.py", "dialogue", "chat_ui"]:
        assert forbidden not in text


def test_protected_file_drift_remains_absent():
    status_output = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--short"], check=True, capture_output=True, text=True).stdout
    status_paths = {line[3:].strip() for line in status_output.splitlines() if line.strip()}
    assert not (status_paths & PROTECTED_FILES)
    assert ALLOWED_NEW_FILES <= status_paths


@pytest.mark.parametrize(
    "command",
    [
        ["python3", "-m", "pytest", "weslr/tests/test_controlled_project_chat_runtime_shell_metadata_v1.py", "-q"],
        ["python3", "-m", "pytest", "weslr/tests/test_project_chat_runtime_dry_run_consumption_plan_v1.py", "-q"],
        ["python3", "-m", "pytest", "weslr/tests/test_project_chat_runtime_dry_run_metadata_v1.py", "-q"],
        ["python3", "-m", "pytest", "weslr/tests/test_project_chat_answer_plan_metadata_helpers_v1.py", "-q"],
    ],
)
def test_existing_dependency_suites_still_pass(command):
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
