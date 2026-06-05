from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import weslr.owner_preview_rendering_metadata as render_meta
from weslr.owner_preview_rendering_metadata import (
    OWNER_PREVIEW_RENDER_PACKET_TYPES_V1,
    OWNER_PREVIEW_RENDER_STATES_V1,
    allowed_owner_preview_render_packet_types_v1,
    allowed_owner_preview_render_states_v1,
    build_initial_owner_preview_render_examples_v1,
    build_owner_preview_render_packet_v1,
    classify_owner_preview_render_packet_v1,
    summarize_owner_preview_render_packet_v1,
    to_owner_preview_render_json_safe_v1,
    validate_owner_preview_render_packet_v1,
)
from weslr.private_project_chat_owner_preview_metadata import (
    OWNER_PREVIEW_PACKET_TYPES_V1,
    OWNER_PREVIEW_STATUSES_V1,
    build_initial_private_project_chat_owner_preview_examples_v1,
    build_private_project_chat_owner_preview_packet_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "owner_preview_rendering_metadata.py"
REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_NEW_FILES = {
    "weslr/owner_preview_rendering_metadata.py",
    "weslr/tests/test_owner_preview_rendering_metadata_v1.py",
    "docs/WESLR_OWNER_PREVIEW_RENDERING_METADATA_HELPERS_IMPLEMENTATION_REPORT_V1.md",
}
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

FORBIDDEN_WORDING = [
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


def _source_packet(**overrides):
    packet = {
        "project_id": "project-001",
        "owner_user_scope": "owner-user",
        "tenant_account_scope": "tenant-a",
        "source_scope": "project_metadata_only",
        "preview_packet_type": "preview_shell_decision_summary",
    }
    packet.update(overrides)
    return build_private_project_chat_owner_preview_packet_v1(packet)


@pytest.mark.parametrize("getter,expected", [
    (allowed_owner_preview_render_states_v1, OWNER_PREVIEW_RENDER_STATES_V1),
    (allowed_owner_preview_render_packet_types_v1, OWNER_PREVIEW_RENDER_PACKET_TYPES_V1),
])
def test_allowed_render_enums_match_constants(getter, expected):
    assert getter() == expected


@pytest.mark.parametrize(
    "source_packet_type,expected_render_packet_type,expected_render_state,expected_classification",
    [
        ("preview_shell_decision_summary", "render_shell_decision_summary", "render_metadata_only", "metadata_only"),
        ("preview_shell_blocked_summary", "render_blocked_summary", "render_blocked", "blocked"),
        ("preview_shell_clarification_summary", "render_clarification_summary", "render_clarification_required", "clarification"),
        ("preview_shell_approval_summary", "render_approval_summary", "render_approval_required", "approval"),
        ("preview_shell_operator_review_summary", "render_operator_review_summary", "render_operator_review_required", "operator_review"),
        ("preview_answer_plan_candidate_summary", "render_answer_plan_candidate_summary", "render_candidate_only", "candidate_only"),
        ("preview_retrieval_request_candidate_summary", "render_retrieval_request_candidate_summary", "render_candidate_only", "candidate_only"),
        ("preview_tool_lane_candidate_summary", "render_tool_lane_candidate_summary", "render_candidate_only", "candidate_only"),
        ("preview_persistence_candidate_summary", "render_persistence_candidate_summary", "render_candidate_only", "candidate_only"),
        ("preview_observability_summary", "render_observability_summary", "render_metadata_only", "observability"),
        ("preview_dry_run_summary", "render_dry_run_summary", "render_metadata_only", "dry_run"),
        ("preview_consumption_plan_summary", "render_consumption_plan_summary", "render_metadata_only", "consumption_plan"),
        ("preview_validation_summary", "render_validation_summary", "render_metadata_only", "validation"),
    ],
)
def test_render_packet_families(source_packet_type, expected_render_packet_type, expected_render_state, expected_classification):
    source_packet = _source_packet(preview_packet_type=source_packet_type)
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": source_packet})
    validation = validate_owner_preview_render_packet_v1(packet)
    classification = classify_owner_preview_render_packet_v1(packet)
    summary = summarize_owner_preview_render_packet_v1(packet)

    assert packet["render_packet_type"] == expected_render_packet_type
    assert packet["render_state"] == expected_render_state
    assert validation["blocked"] is False
    assert validation["classification"] == expected_classification
    assert classification["classification"] == expected_classification
    assert summary["summary_text"].startswith("Private owner preview render:")
    assert packet["display_title"] == "Private owner preview"
    assert packet["display_label"]
    assert packet["display_status"]
    assert packet["display_summary"]
    assert packet["display_details"]
    assert packet["render_packet_id"].startswith("render-")


def test_render_not_public_ready_state_is_supported():
    source_packet = _source_packet(
        preview_packet_type="preview_validation_summary",
    )
    source_packet["readiness_label"] = "not_public_ready"
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": source_packet})
    validation = validate_owner_preview_render_packet_v1(packet)
    assert packet["render_state"] == "render_not_public_ready"
    assert validation["blocked"] is False
    assert validation["classification"] == "not_public_ready"
    assert packet["display_label"] == "Not public ready"


@pytest.mark.parametrize("field", ["project_id", "owner_user_scope", "tenant_account_scope", "source_scope"])
def test_missing_owner_scope_blocks_rendering(field):
    source_packet = _source_packet()
    source_packet.pop(field)
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": source_packet})
    validation = validate_owner_preview_render_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("missing_") for label in validation["blocked_labels"])


@pytest.mark.parametrize("field", ["render_state", "render_packet_type"])
def test_unknown_render_state_or_type_fails_closed(field):
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": _source_packet()})
    packet[field] = "unknown-value"
    validation = validate_owner_preview_render_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("unknown_") for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("display_summary", "I executed the final answer."),
        ("display_details", "Unknown Engine and chat_responder"),
        ("redaction_summary", "I searched and I saved it."),
        ("display_status", "public ready certified conscious autonomous deployment"),
        ("display_label", "final answer"),
    ],
)
def test_unsafe_wording_blocks_rendering(field, value):
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": _source_packet()})
    packet[field] = value
    validation = validate_owner_preview_render_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label.startswith("forbidden_") for label in validation["blocked_labels"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("display_summary", "raw private project data"),
        ("display_details", "raw traces and raw memory/project payloads"),
        ("display_summary", "raw `.weslr` state"),
        ("display_details", "retrieval/tool/persistence executed"),
    ],
)
def test_raw_private_or_execution_claims_block_rendering(field, value):
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": _source_packet()})
    packet[field] = value
    validation = validate_owner_preview_render_packet_v1(packet)
    assert validation["blocked"] is True


@pytest.mark.parametrize(
    "denied_field",
    [
        "runtime_wiring_authority",
        "chat_responder_authority",
        "final_answer_generation_authority",
        "retrieval_execution_authority",
        "searxng_execution_authority",
        "tool_execution_authority",
        "storage_database_authority",
        "weslr_io_authority",
        "project_state_mutation_authority",
        "memory_mutation_authority",
        "ui_consumption_implementation_authority",
        "public_access_authority",
        "tester_access_authority",
        "private_data_exposure_authority",
        "public_readiness_claim_authority",
    ],
)
def test_denied_authority_is_complete_and_defaults_false(denied_field):
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": _source_packet()})
    assert denied_field in packet["denied_authority"]
    assert packet["denied_authority"][denied_field] is False


@pytest.mark.parametrize("field", ["source_preview_packet_ref", "display_summary", "display_details", "display_flags", "limitations"])
def test_missing_source_or_display_data_blocks_rendering(field):
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": _source_packet()})
    if field in {"display_flags", "limitations"}:
        packet[field] = []
    else:
        packet[field] = ""
    validation = validate_owner_preview_render_packet_v1(packet)
    assert validation["blocked"] is True


@pytest.mark.parametrize("phrase", FORBIDDEN_WORDING)
def test_forbidden_wording_blocks_rendering(phrase):
    packet = build_owner_preview_render_packet_v1({"source_preview_packet": _source_packet()})
    packet["display_details"] = phrase
    validation = validate_owner_preview_render_packet_v1(packet)
    assert validation["blocked"] is True


def test_json_safe_conversion_works():
    value = to_owner_preview_render_json_safe_v1({"items": {1, 2}, "tuple": ("a", "b")})
    assert value["items"] in ([1, 2], [2, 1])
    json.dumps(value, sort_keys=True)


def test_examples_are_synthetic_only():
    examples = build_initial_owner_preview_render_examples_v1()
    assert examples
    assert all(example["display_title"] == "Private owner preview" for example in examples)
    assert all(example["source_preview_packet_ref"].startswith("preview-") for example in examples)
    assert all("final answer" not in example["display_summary"].lower() for example in examples)
    assert all("final answer" not in example["display_details"].lower() for example in examples)
    assert all(example["redaction_summary"] for example in examples)


def test_validation_returns_metadata_not_uncaught_exceptions():
    validation = validate_owner_preview_render_packet_v1(build_owner_preview_render_packet_v1({"source_preview_packet": _source_packet()}))
    assert isinstance(validation, dict)
    assert "blocked_labels" in validation
    assert "render_packet" in validation
    assert "display_summary" in validation


def test_static_source_scan_confirms_no_filesystem_network_subprocess_runtime_or_protected_imports():
    text = HELPER_PATH.read_text()
    forbidden_patterns = [
        "open(",
        "subprocess",
        "requests",
        "socket",
        ".weslr",
        "from weslr.chat_responder",
        "import weslr.chat_responder",
        "from weslr.main",
        "import weslr.main",
        "from dialogue",
        "import dialogue",
        "from chat_ui",
        "import chat_ui",
    ]
    for forbidden in forbidden_patterns:
        assert forbidden not in text


def test_protected_file_drift_remains_absent():
    status_output = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=no"], check=True, capture_output=True, text=True).stdout
    status_paths = {line[3:].strip() for line in status_output.splitlines() if line.strip()}
    diff_output = subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--name-only"], check=True, capture_output=True, text=True).stdout
    diff_paths = {line.strip() for line in diff_output.splitlines() if line.strip()}
    assert not (status_paths & PROTECTED_FILES)
    assert not (diff_paths & PROTECTED_FILES)
    if status_paths:
        assert status_paths <= ALLOWED_NEW_FILES
    if diff_paths:
        assert diff_paths <= ALLOWED_NEW_FILES


@pytest.mark.parametrize(
    "command",
    [
        ["python3", "-m", "pytest", "weslr/tests/test_private_project_chat_owner_preview_metadata_v1.py", "-q"],
        ["python3", "-m", "pytest", "weslr/tests/test_controlled_project_chat_runtime_shell_metadata_v1.py", "-q"],
        ["python3", "-m", "pytest", "weslr/tests/test_project_chat_runtime_dry_run_consumption_plan_v1.py", "-q"],
        ["python3", "-m", "pytest", "weslr/tests/test_project_chat_runtime_dry_run_metadata_v1.py", "-q"],
        ["python3", "-m", "pytest", "weslr/tests/test_project_chat_answer_plan_metadata_helpers_v1.py", "-q"],
    ],
)
def test_existing_dependency_suites_still_pass(command):
    completed = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
