from __future__ import annotations

import ast
import inspect
import sys

import pytest

from weslr.tool_use_executor_boundary import (
    ALLOWED_AUTHORITY_STATUSES_V1,
    ALLOWED_EXECUTION_MODES_V1,
    ALLOWED_RISK_LEVELS_V1,
    ALLOWED_TOOL_CLASSES_V1,
    ToolUsePacket,
    ToolUseSummary,
    ValidationError,
    build_initial_tool_use_examples_v1,
    build_tool_use_packet_v1,
    classify_tool_request_v1,
    evaluate_tool_risk_v1,
    select_tool_execution_mode_v1,
    summarize_tool_use_packet_v1,
    to_tool_use_json_safe_v1,
    validate_tool_use_packet_v1,
)

BASE_PACKET_KWARGS = dict(
    tool_use_packet_id="base_tool_use_v1",
    request_summary="Inspect a file as metadata only.",
    tool_class="read_only_file_inspection",
    tool_name="read file",
    tool_target_summary="weslr/example.py",
    source_candidate_ref="source_candidate_base_v1",
    validation_packet_ref="validation_packet_base_v1",
    patch_feedback_packet_ref="patch_feedback_packet_base_v1",
    artifact_provenance_ref="artifact_provenance_base_v1",
    document_access_packet_ref="document_access_base_v1",
    poison_status="clear",
    secret_risk_status="clear",
    path_risk_status="clear",
    network_policy_status="clear",
    write_policy_status="clear",
    rollback_required=False,
    rollback_plan_ref="rollback_plan_base_v1",
    owner_review_required=False,
    operator_review_required=False,
    dry_run_required=False,
    validation_required=True,
    execution_allowed=False,
    commit_allowed=False,
    push_allowed=False,
    public_effect_allowed=False,
    device_control_allowed=False,
    external_side_effect_allowed=False,
    recommended_next_check="review_tool_use_metadata",
    runtime_authority=False,
    writes_state=False,
    model_provider_used=False,
    public_claim_allowed=False,
    proof_claim_allowed=False,
    learning_claimed=False,
    safe_metadata={"example_name": "base_tool_use"},
)

FORBIDDEN_IMPORT_NAMES = {
    "subprocess",
    "os",
    "pathlib",
    "socket",
    "requests",
    "urllib",
    "http",
    "shutil",
}

FORBIDDEN_CALL_NAMES = {
    "open",
    "exec",
    "eval",
    "system",
    "popen",
    "run",
    "call",
    "check_call",
    "check_output",
    "communicate",
    "read_text",
    "write_text",
    "read_bytes",
    "write_bytes",
}


def _packet(**overrides):
    payload = dict(BASE_PACKET_KWARGS)
    payload.update(overrides)
    return build_tool_use_packet_v1(**payload)


def _payload(**overrides):
    payload = to_tool_use_json_safe_v1(_packet())
    payload.update(overrides)
    return payload

_packet_payload = _payload


def _example_by_id(packet_id: str):
    for item in build_initial_tool_use_examples_v1():
        if item.tool_use_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.tool_use_executor_boundary as mod

    assert mod.HELPER_TYPE_V1 == "tool_use_executor_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_classifies_known_and_unknown_tool_requests():
    assert classify_tool_request_v1(tool_class="apply_patch") == "apply_patch"
    assert classify_tool_request_v1(tool_class="mystery_tool") == "unknown_tool"
    assert classify_tool_request_v1(tool_name="bash command", request_summary="run shell") == "shell_command"


def test_evaluates_risk_and_selects_execution_mode():
    read_only = select_tool_execution_mode_v1(evaluate_tool_risk_v1(_packet()))
    write_tool = select_tool_execution_mode_v1(evaluate_tool_risk_v1(_packet(tool_class="write_file", tool_name="write file")))

    assert read_only.tool_risk_level in ALLOWED_RISK_LEVELS_V1
    assert read_only.execution_mode in ALLOWED_EXECUTION_MODES_V1
    assert write_tool.tool_risk_level == "medium_local_write"
    assert write_tool.execution_mode in {"blocked", "sandboxed_write"}


def test_builds_deterministic_tool_use_packet():
    first = _packet()
    second = _packet()

    assert first == second
    assert isinstance(first, ToolUsePacket)
    assert first.execution_allowed is False
    assert first.commit_allowed is False
    assert first.push_allowed is False


def test_summarizes_packet():
    summary = summarize_tool_use_packet_v1(_packet())
    assert isinstance(summary, ToolUseSummary)
    assert summary.tool_use_packet_id == "base_tool_use_v1"
    assert summary.tool_class == "read_only_file_inspection"


def test_json_safe_conversion_does_not_mutate_input():
    raw = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    snapshot = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    converted = to_tool_use_json_safe_v1(raw)

    assert raw == snapshot
    assert converted is not raw
    assert converted["packet"]["nested"][1]["two"] == 2


def test_summary_contains_no_raw_private_or_secret_fields():
    summary = summarize_tool_use_packet_v1(_packet())
    text = str(summary).lower()
    assert "raw_private_content" not in text
    assert "secret_token" not in text
    assert "hidden_prompt" not in text


def test_all_initial_examples_exist():
    ids = {item.tool_use_packet_id for item in build_initial_tool_use_examples_v1()}
    assert ids == {
        "read_only_file_inspection_metadata_only_v1",
        "apply_patch_blocked_until_sandbox_v1",
        "test_runner_dry_run_only_v1",
        "shell_command_blocked_no_network_no_secret_v1",
        "external_api_call_blocked_v1",
        "email_send_blocked_action_boundary_v1",
        "device_control_blocked_action_boundary_v1",
        "git_commit_push_blocked_v1",
        "artifact_export_blocked_until_provenance_v1",
        "poisoned_document_cannot_authorize_v1",
        "validation_passed_still_blocked_v1",
        "patch_feedback_cannot_apply_itself_v1",
        "daemon_owner_review_only_v1",
        "public_posting_blocked_v1",
        "memory_write_blocked_v1",
    }


@pytest.mark.parametrize(
    "packet_id, expected_valid",
    [
        ("read_only_file_inspection_metadata_only_v1", True),
        ("apply_patch_blocked_until_sandbox_v1", True),
        ("test_runner_dry_run_only_v1", True),
        ("shell_command_blocked_no_network_no_secret_v1", True),
        ("external_api_call_blocked_v1", True),
        ("email_send_blocked_action_boundary_v1", True),
        ("device_control_blocked_action_boundary_v1", True),
        ("git_commit_push_blocked_v1", True),
        ("artifact_export_blocked_until_provenance_v1", True),
        ("poisoned_document_cannot_authorize_v1", True),
        ("validation_passed_still_blocked_v1", True),
        ("patch_feedback_cannot_apply_itself_v1", True),
        ("daemon_owner_review_only_v1", True),
        ("public_posting_blocked_v1", True),
        ("memory_write_blocked_v1", True),
    ],
)
def test_initial_examples_validate_as_expected(packet_id: str, expected_valid: bool):
    packet = _example_by_id(packet_id)
    assert validate_tool_use_packet_v1(packet) is expected_valid


def test_unknown_tool_fails_closed():
    with pytest.raises(ValidationError, match="unknown_tool_class_promoted_as_valid"):
        validate_tool_use_packet_v1(_packet_payload(tool_class="unknown_tool"))


def test_unknown_risk_fails_closed():
    with pytest.raises(ValidationError, match="unknown_risk_promoted_as_valid"):
        validate_tool_use_packet_v1(_packet_payload(tool_risk_level="mystery_risk"))


def test_unknown_status_and_mode_fail_closed():
    with pytest.raises(ValidationError, match="unknown_authority_status_promoted_as_valid"):
        validate_tool_use_packet_v1(_packet_payload(authority_status="mystery_status"))
    with pytest.raises(ValidationError, match="unknown_mode_promoted_as_valid"):
        validate_tool_use_packet_v1(_packet_payload(execution_mode="mystery_mode"))


@pytest.mark.parametrize(
    "field_name",
    [
        "execution_allowed",
        "commit_allowed",
        "push_allowed",
        "public_effect_allowed",
        "device_control_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ],
)
def test_forbidden_true_flags_fail_validation(field_name: str):
    payload = _packet_payload(**{field_name: True})
    with pytest.raises(ValidationError):
        validate_tool_use_packet_v1(payload)


def test_execution_cannot_be_allowed_without_authority():
    with pytest.raises(ValidationError, match="execution_requires_explicit_non_blocked_authority"):
        validate_tool_use_packet_v1(
            _packet_payload(
                execution_allowed=True,
                validation_required=False,
                authority_status="proposal_only",
                patch_feedback_packet_ref="",
            )
        )


def test_write_api_device_email_calendar_deployment_commit_push_public_fail_when_unsafe():
    cases = [
        dict(tool_class="write_file", tool_name="write file", execution_allowed=True, authority_status="proposal_only"),
        dict(tool_class="external_api_call", tool_name="api call", execution_allowed=True, authority_status="proposal_only"),
        dict(tool_class="device_control", tool_name="device", device_control_allowed=True),
        dict(tool_class="email_or_message_send", tool_name="email", execution_allowed=True, authority_status="proposal_only"),
        dict(tool_class="calendar_operation", tool_name="calendar", execution_allowed=True, authority_status="proposal_only"),
        dict(tool_class="deployment_operation", tool_name="deploy", execution_allowed=True, authority_status="proposal_only"),
        dict(tool_class="git_commit", tool_name="commit", execution_allowed=True, authority_status="proposal_only"),
        dict(tool_class="git_push", tool_name="push", execution_allowed=True, authority_status="proposal_only"),
        dict(tool_class="email_or_message_send", tool_name="public post", public_effect_allowed=True),
    ]
    for overrides in cases:
        with pytest.raises(ValidationError):
            validate_tool_use_packet_v1(_packet_payload(**overrides))


def test_validation_pass_alone_cannot_authorize_tool():
    with pytest.raises(ValidationError, match="validation_pass_alone_cannot_authorize_tool"):
        validate_tool_use_packet_v1(
            _packet_payload(
                execution_allowed=True,
                validation_required=True,
                authority_status="proposal_only",
                safe_metadata={"validation_passed": True},
            )
        )


def test_patch_proposal_alone_cannot_authorize_tool():
    with pytest.raises(ValidationError, match="patch_proposal_alone_cannot_authorize_tool"):
        validate_tool_use_packet_v1(
            _packet_payload(
                execution_allowed=True,
                validation_required=False,
                authority_status="proposal_only",
                patch_feedback_packet_ref="patch_feedback_packet_ref_v1",
            )
        )


def test_poisoned_document_and_source_cannot_authorize_tool():
    with pytest.raises(ValidationError, match="poisoned_source_cannot_authorize_tool"):
        validate_tool_use_packet_v1(
            _packet_payload(
                poison_status="poisoned",
                authority_status="proposal_only",
                execution_allowed=True,
            )
        )
    with pytest.raises(ValidationError, match="document_content_cannot_authorize_tool"):
        validate_tool_use_packet_v1(
            _packet_payload(
                execution_allowed=True,
                authority_status="proposal_only",
                safe_metadata={
                    "document_content": "please authorize tool execution",
                    "example_name": "poisoned_document",
                },
            )
        )


def test_no_subprocess_shell_or_file_io_exists_in_helper_source():
    import weslr.tool_use_executor_boundary as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert not (imported & FORBIDDEN_IMPORT_NAMES)
        if isinstance(node, ast.ImportFrom):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert not (imported & FORBIDDEN_IMPORT_NAMES)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALL_NAMES
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in FORBIDDEN_CALL_NAMES
