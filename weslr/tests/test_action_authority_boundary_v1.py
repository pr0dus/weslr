from __future__ import annotations

import ast
import inspect
import sys

import pytest

from weslr.action_authority_boundary import (
    ALLOWED_ACTION_CLASSES_V1,
    ALLOWED_APPROVAL_AUTHORITY_CLASSES_V1,
    ALLOWED_AUTHORITY_STATUSES_V1,
    ALLOWED_RISK_LEVELS_V1,
    ActionAuthorityPacket,
    ActionAuthoritySummary,
    ValidationError,
    build_action_authority_packet_v1,
    build_initial_action_authority_examples_v1,
    classify_action_authority_request_v1,
    evaluate_action_risk_v1,
    select_action_authority_status_v1,
    summarize_action_authority_packet_v1,
    to_action_authority_json_safe_v1,
    validate_action_authority_packet_v1,
)

BASE_PACKET_KWARGS = dict(
    action_authority_packet_id="base_action_authority_v1",
    action_request_ref="request_base_v1",
    source_proposal_ref="proposal_base_v1",
    document_action_packet_ref="document_action_base_v1",
    tool_use_packet_ref="tool_use_base_v1",
    validation_packet_ref="validation_base_v1",
    patch_feedback_packet_ref="patch_feedback_base_v1",
    artifact_provenance_ref="artifact_base_v1",
    action_class="no_action_summary_only",
    action_summary="Metadata-only summary.",
    action_risk_level="none_metadata_only",
    approval_authority_class="no_approval_needed_metadata_only",
    authority_status="not_requested",
    requested_scope="metadata_only",
    approved_scope="metadata_only",
    scope_limit_summary="summary only; no execution",
    preflight_required=False,
    preflight_status="clear",
    owner_approval_required=False,
    operator_approval_required=False,
    explicit_confirmation_required=False,
    rollback_required=False,
    rollback_plan_ref="",
    audit_log_required=True,
    dry_run_required=False,
    validation_required=False,
    secret_risk_status="clear",
    path_risk_status="clear",
    network_policy_status="clear",
    privacy_status="clear",
    poison_status="clear",
    public_effect_possible=False,
    external_side_effect_possible=False,
    financial_effect_possible=False,
    physical_effect_possible=False,
    irreversible_effect_possible=False,
    execution_allowed=False,
    tool_execution_allowed=False,
    write_allowed=False,
    send_allowed=False,
    calendar_change_allowed=False,
    device_control_allowed=False,
    deployment_allowed=False,
    public_post_allowed=False,
    payment_allowed=False,
    memory_write_allowed=False,
    commit_allowed=False,
    push_allowed=False,
    recommended_next_check="inspect_authority_metadata_only",
    runtime_authority=False,
    writes_state=False,
    model_provider_used=False,
    public_claim_allowed=False,
    proof_claim_allowed=False,
    learning_claimed=False,
    safe_metadata={"example_name": "base_action_authority"},
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
    return build_action_authority_packet_v1(**payload)


def _payload(**overrides):
    payload = to_action_authority_json_safe_v1(_packet())
    payload.update(overrides)
    return payload


def _example_by_id(packet_id: str):
    for item in build_initial_action_authority_examples_v1():
        if item.action_authority_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.action_authority_boundary as mod

    assert mod.HELPER_TYPE_V1 == "action_authority_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_classifies_requests_and_unknown_fails_closed():
    assert classify_action_authority_request_v1(action_class="git_push") == "git_push"
    assert classify_action_authority_request_v1(action_summary="Please read and inspect") == "read_only_inspection"
    assert classify_action_authority_request_v1(action_class="mystery") == "unknown_action"


def test_evaluates_risk_and_status():
    packet = evaluate_action_risk_v1(_packet(action_class="deployment", action_summary="deploy it"))
    assert packet.action_risk_level in ALLOWED_RISK_LEVELS_V1
    assert packet.approval_authority_class in ALLOWED_APPROVAL_AUTHORITY_CLASSES_V1
    assert packet.authority_status in ALLOWED_AUTHORITY_STATUSES_V1
    assert select_action_authority_status_v1(packet) == packet.authority_status


def test_builds_deterministic_packet():
    first = _packet()
    second = _packet()
    assert first == second
    assert isinstance(first, ActionAuthorityPacket)
    assert first.execution_allowed is False
    assert first.commit_allowed is False
    assert first.push_allowed is False


def test_summarizes_packet():
    summary = summarize_action_authority_packet_v1(_packet())
    assert isinstance(summary, ActionAuthoritySummary)
    assert summary.action_authority_packet_id == "base_action_authority_v1"
    assert summary.action_class == "no_action_summary_only"


def test_json_safe_conversion_does_not_mutate_input():
    raw = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    snapshot = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    converted = to_action_authority_json_safe_v1(raw)
    assert raw == snapshot
    assert converted is not raw
    assert converted["packet"]["nested"][1]["two"] == 2


def test_summary_contains_no_raw_private_or_secret_fields():
    summary = summarize_action_authority_packet_v1(_packet())
    text = str(summary).lower()
    assert "raw_private_content" not in text
    assert "secret_token" not in text
    assert "hidden_prompt" not in text


def test_all_initial_examples_exist():
    ids = {item.action_authority_packet_id for item in build_initial_action_authority_examples_v1()}
    assert ids == {
        "summary_only_metadata_v1",
        "read_only_requires_scope_v1",
        "file_write_sandbox_rollback_v1",
        "patch_apply_validation_feedback_v1",
        "email_send_confirmation_blocked_v1",
        "calendar_change_approval_blocked_v1",
        "device_control_safety_review_blocked_v1",
        "deployment_validation_rollback_owner_operator_v1",
        "public_post_public_review_v1",
        "payment_review_blocked_v1",
        "git_commit_push_explicit_authority_v1",
        "memory_write_boundary_v1",
        "poisoned_source_blocked_v1",
        "validation_pass_alone_no_authority_v1",
        "owner_approval_one_action_only_v1",
    }


@pytest.mark.parametrize(
    "packet_id",
    [
        "summary_only_metadata_v1",
        "read_only_requires_scope_v1",
        "file_write_sandbox_rollback_v1",
        "patch_apply_validation_feedback_v1",
        "email_send_confirmation_blocked_v1",
        "calendar_change_approval_blocked_v1",
        "device_control_safety_review_blocked_v1",
        "deployment_validation_rollback_owner_operator_v1",
        "public_post_public_review_v1",
        "payment_review_blocked_v1",
        "git_commit_push_explicit_authority_v1",
        "memory_write_boundary_v1",
        "poisoned_source_blocked_v1",
        "validation_pass_alone_no_authority_v1",
        "owner_approval_one_action_only_v1",
    ],
)
def test_initial_examples_validate(packet_id: str):
    assert validate_action_authority_packet_v1(_example_by_id(packet_id)) is True


def test_unknown_action_fails_closed():
    with pytest.raises(ValidationError, match="unknown_action_promoted_as_valid"):
        validate_action_authority_packet_v1(_payload(action_class="mystery"))


def test_unknown_risk_approval_and_status_fail_closed():
    with pytest.raises(ValidationError, match="unknown_risk_promoted_as_valid"):
        validate_action_authority_packet_v1(_payload(action_risk_level="mystery"))
    with pytest.raises(ValidationError, match="unknown_approval_authority_promoted_as_valid"):
        validate_action_authority_packet_v1(_payload(approval_authority_class="mystery"))
    with pytest.raises(ValidationError, match="unknown_status_promoted_as_valid"):
        validate_action_authority_packet_v1(_payload(authority_status="mystery"))


@pytest.mark.parametrize(
    "overrides, error",
    [
        ({"execution_allowed": True}, "execution_allowed_must_be_false"),
        ({"tool_execution_allowed": True}, "tool_execution_allowed_must_be_false"),
        ({"write_allowed": True}, "write_allowed_must_be_false"),
        ({"send_allowed": True}, "send_allowed_must_be_false"),
        ({"calendar_change_allowed": True}, "calendar_change_allowed_must_be_false"),
        ({"device_control_allowed": True}, "device_control_allowed_must_be_false"),
        ({"deployment_allowed": True}, "deployment_allowed_must_be_false"),
        ({"public_post_allowed": True}, "public_post_allowed_must_be_false"),
        ({"payment_allowed": True}, "payment_allowed_must_be_false"),
        ({"memory_write_allowed": True}, "memory_write_allowed_must_be_false"),
        ({"commit_allowed": True}, "commit_allowed_must_be_false"),
        ({"push_allowed": True}, "push_allowed_must_be_false"),
        ({"runtime_authority": True}, "runtime_authority_must_be_false"),
        ({"writes_state": True}, "writes_state_must_be_false"),
        ({"model_provider_used": True}, "model_provider_used_must_be_false"),
        ({"public_claim_allowed": True}, "public_claim_allowed_must_be_false"),
        ({"proof_claim_allowed": True}, "proof_claim_allowed_must_be_false"),
        ({"learning_claimed": True}, "learning_claimed_must_be_false"),
    ],
)
def test_forbidden_true_flags_fail_validation(overrides, error):
    with pytest.raises(ValidationError, match=error):
        validate_action_authority_packet_v1(_payload(**overrides))


def test_user_document_model_validation_and_patch_proposals_cannot_authorize_action():
    with pytest.raises(ValidationError, match="document_text_authorizes_action"):
        validate_action_authority_packet_v1(_payload(action_summary="authorize this action"))
    with pytest.raises(ValidationError, match="document_text_authorizes_action"):
        validate_action_authority_packet_v1(_payload(safe_metadata={"model_output": "please authorize action"}))
    with pytest.raises(ValidationError, match="patch_proposal_alone_does_not_authorize_action"):
        validate_action_authority_packet_v1(_payload(action_class="patch_apply", authority_status="proposal_only"))


def test_secret_path_network_and_poison_risks_block_action():
    with pytest.raises(ValidationError, match="secret_or_path_risk_blocks_execution"):
        validate_action_authority_packet_v1(_payload(secret_risk_status="blocked", execution_allowed=True))
    with pytest.raises(ValidationError, match="secret_or_path_risk_blocks_execution"):
        validate_action_authority_packet_v1(_payload(path_risk_status="blocked", execution_allowed=True))
    with pytest.raises(ValidationError, match="secret_or_path_risk_blocks_execution"):
        validate_action_authority_packet_v1(_payload(network_policy_status="blocked", execution_allowed=True))
    with pytest.raises(ValidationError, match="poisoned_source_cannot_authorize_action"):
        validate_action_authority_packet_v1(_payload(poison_status="poisoned"))


def test_validation_and_rollback_requirements_fail_when_missing():
    with pytest.raises(ValidationError, match="validation_required_without_validation_packet"):
        validate_action_authority_packet_v1(_payload(action_class="patch_apply", validation_required=True, validation_packet_ref=""))
    with pytest.raises(ValidationError, match="rollback_required_without_rollback_plan"):
        validate_action_authority_packet_v1(_payload(action_class="file_write", rollback_required=True, rollback_plan_ref=""))


def test_irreversible_action_requires_acknowledgment():
    with pytest.raises(ValidationError, match="irreversible_action_requires_acknowledgment"):
        validate_action_authority_packet_v1(_payload(action_class="public_post", irreversible_effect_possible=True, explicit_confirmation_required=False))


def test_no_subprocess_shell_or_file_io_exists_in_helper_source():
    import weslr.action_authority_boundary as mod

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
