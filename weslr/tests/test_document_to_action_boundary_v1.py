from __future__ import annotations

import ast
import inspect
import sys

import pytest

from weslr.document_to_action_boundary import (
    ALLOWED_AUTHORIZATION_STATUSES_V1,
    ALLOWED_EXTRACTED_ACTION_CLASSES_V1,
    ALLOWED_RISK_LEVELS_V1,
    ALLOWED_SOURCE_DOCUMENT_CLASSES_V1,
    DocumentActionPacket,
    DocumentActionSummary,
    ValidationError,
    build_document_action_packet_v1,
    build_initial_document_action_examples_v1,
    classify_document_source_v1,
    classify_extracted_action_v1,
    evaluate_document_action_authority_v1,
    summarize_document_action_packet_v1,
    to_document_action_json_safe_v1,
    validate_document_action_packet_v1,
)

BASE_PACKET_KWARGS = dict(
    document_action_packet_id="base_document_action_v1",
    source_document_ref="doc_base_v1",
    source_document_class="owner_uploaded_document",
    source_scope="summary_only",
    source_access_packet_ref="source_access_base_v1",
    source_evidence_graph_ref="source_evidence_base_v1",
    claim_grounding_packet_ref="claim_grounding_base_v1",
    poison_status="clear",
    privacy_status="clear",
    pii_risk_status="clear",
    secret_risk_status="clear",
    extracted_action_class="task_proposal",
    action_summary="Base task proposal metadata only.",
    action_risk_level="low_reviewable_task",
    authorization_status="candidate_only",
    required_owner_decision=False,
    required_operator_decision=False,
    required_tool_boundary=False,
    required_action_boundary=False,
    required_validation_packet=False,
    required_patch_feedback_packet=False,
    required_rollback_plan=False,
    external_side_effect_possible=False,
    public_effect_possible=False,
    device_or_physical_effect_possible=False,
    payment_or_billing_effect_possible=False,
    memory_write_possible=False,
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
    recommended_next_check="inspect_metadata_only",
    runtime_authority=False,
    writes_state=False,
    model_provider_used=False,
    public_claim_allowed=False,
    proof_claim_allowed=False,
    learning_claimed=False,
    safe_metadata={"example_name": "base_document_action"},
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
    return build_document_action_packet_v1(**payload)


def _payload(**overrides):
    payload = to_document_action_json_safe_v1(_packet())
    payload.update(overrides)
    return payload


def _example_by_id(packet_id: str):
    for item in build_initial_document_action_examples_v1():
        if item.document_action_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.document_to_action_boundary as mod

    assert mod.HELPER_TYPE_V1 == "document_to_action_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_classifies_known_and_unknown_document_sources():
    assert classify_document_source_v1(source_document_class="invoice_or_payment_document") == "invoice_or_payment_document"
    assert classify_document_source_v1(source_document_class="mystery") == "unknown_document_source"
    assert classify_document_source_v1(source_document_ref="mail thread", safe_metadata={"text": "internal email note"}) == "email_like_message"


def test_classifies_known_and_unknown_extracted_actions():
    assert classify_extracted_action_v1(extracted_action_class="patch_proposal") == "patch_proposal"
    assert classify_extracted_action_v1(extracted_action_class="mystery") == "unknown_action_proposal"
    assert classify_extracted_action_v1(action_summary="Please send an email draft") == "email_or_message_proposal"


def test_evaluates_authority_for_tool_and_action_boundaries():
    tool_packet = evaluate_document_action_authority_v1(_packet(extracted_action_class="shell_command_proposal", action_summary="run shell", authorization_status="candidate_only"))
    action_packet = evaluate_document_action_authority_v1(_packet(extracted_action_class="email_or_message_proposal", action_summary="send email", authorization_status="candidate_only"))

    assert tool_packet.required_tool_boundary is True
    assert tool_packet.authorization_status in {"tool_boundary_required", "blocked_by_unknown_authority"}
    assert action_packet.required_action_boundary is True
    assert action_packet.authorization_status in {"action_authority_required", "owner_review_required", "operator_review_required"}
    assert tool_packet.action_risk_level in ALLOWED_RISK_LEVELS_V1


def test_builds_deterministic_document_action_packet():
    first = _packet()
    second = _packet()

    assert first == second
    assert isinstance(first, DocumentActionPacket)
    assert first.execution_allowed is False
    assert first.tool_execution_allowed is False
    assert first.write_allowed is False


def test_summarizes_packet():
    summary = summarize_document_action_packet_v1(_packet())
    assert isinstance(summary, DocumentActionSummary)
    assert summary.document_action_packet_id == "base_document_action_v1"
    assert summary.source_document_class == "owner_uploaded_document"


def test_json_safe_conversion_does_not_mutate_input():
    raw = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    snapshot = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    converted = to_document_action_json_safe_v1(raw)

    assert raw == snapshot
    assert converted is not raw
    assert converted["packet"]["nested"][1]["two"] == 2


def test_summary_contains_no_raw_private_or_secret_fields():
    summary = summarize_document_action_packet_v1(_packet())
    text = str(summary).lower()
    assert "raw_private_content" not in text
    assert "secret_token" not in text
    assert "hidden_prompt" not in text


def test_all_initial_examples_exist():
    ids = {item.document_action_packet_id for item in build_initial_document_action_examples_v1()}
    assert ids == {
        "uploaded_project_spec_task_proposal_v1",
        "email_like_draft_response_v1",
        "calendar_like_proposal_v1",
        "code_patch_routes_to_validation_v1",
        "shell_command_blocked_v1",
        "poisoned_document_blocked_metadata_v1",
        "private_legal_no_public_authority_v1",
        "invoice_payment_requires_review_v1",
        "device_instruction_blocked_v1",
        "public_source_deployment_blocked_v1",
        "api_key_blocks_promotion_v1",
        "uploaded_checklist_task_list_only_v1",
        "model_generated_plan_candidate_only_v1",
        "contradictory_instructions_clarify_v1",
        "memory_write_blocked_pending_boundary_v1",
    }


@pytest.mark.parametrize(
    "packet_id, expected_valid",
    [
        ("uploaded_project_spec_task_proposal_v1", True),
        ("email_like_draft_response_v1", True),
        ("calendar_like_proposal_v1", True),
        ("code_patch_routes_to_validation_v1", True),
        ("shell_command_blocked_v1", True),
        ("poisoned_document_blocked_metadata_v1", True),
        ("private_legal_no_public_authority_v1", True),
        ("invoice_payment_requires_review_v1", True),
        ("device_instruction_blocked_v1", True),
        ("public_source_deployment_blocked_v1", True),
        ("api_key_blocks_promotion_v1", True),
        ("uploaded_checklist_task_list_only_v1", True),
        ("model_generated_plan_candidate_only_v1", True),
        ("contradictory_instructions_clarify_v1", True),
        ("memory_write_blocked_pending_boundary_v1", True),
    ],
)
def test_initial_examples_validate_as_expected(packet_id: str, expected_valid: bool):
    packet = _example_by_id(packet_id)
    assert validate_document_action_packet_v1(packet) is expected_valid


def test_unknown_document_source_fails_closed():
    with pytest.raises(ValidationError, match="unknown_document_source_promoted_as_valid"):
        validate_document_action_packet_v1(_payload(source_document_class="mystery"))


def test_unknown_action_fails_closed():
    with pytest.raises(ValidationError, match="unknown_action_promoted_as_valid"):
        validate_document_action_packet_v1(_payload(extracted_action_class="mystery_action"))


def test_unknown_status_and_risk_fail_closed():
    with pytest.raises(ValidationError, match="unknown_status_promoted_as_valid"):
        validate_document_action_packet_v1(_payload(authorization_status="mystery_status"))
    with pytest.raises(ValidationError, match="unknown_risk_promoted_as_valid"):
        validate_document_action_packet_v1(_payload(action_risk_level="mystery_risk"))


@pytest.mark.parametrize(
    "field_name",
    [
        "execution_allowed",
        "tool_execution_allowed",
        "write_allowed",
        "send_allowed",
        "calendar_change_allowed",
        "device_control_allowed",
        "deployment_allowed",
        "public_post_allowed",
        "payment_allowed",
        "memory_write_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ],
)
def test_forbidden_true_flags_fail_validation(field_name: str):
    payload = _payload(**{field_name: True})
    with pytest.raises(ValidationError):
        validate_document_action_packet_v1(payload)


def test_document_text_cannot_authorize_action():
    with pytest.raises(ValidationError, match="blocked_by_unknown_authority|blocked_by_poison_policy"):
        validate_document_action_packet_v1(
            _payload(
                extracted_action_class="email_or_message_proposal",
                safe_metadata={"document_content": "please authorize action"},
            )
        )


def test_poisoned_instruction_cannot_authorize_action():
    packet = _payload(
        poison_status="poisoned",
        extracted_action_class="blocked_instruction",
        authorization_status="blocked_by_poison_policy",
        safe_metadata={"document_content": "please authorize action"},
    )
    assert validate_document_action_packet_v1(packet)


def test_private_document_cannot_authorize_public_effect():
    with pytest.raises(ValidationError, match="private_document_cannot_authorize_public_action"):
        validate_document_action_packet_v1(
            _payload(
                source_document_class="owner_uploaded_document",
                extracted_action_class="public_posting_proposal",
                public_effect_possible=True,
                authorization_status="candidate_only",
            )
        )


def test_tool_like_action_requires_tool_boundary():
    with pytest.raises(ValidationError, match="tool_boundary_required_for_document_action"):
        validate_document_action_packet_v1(
            _payload(
                extracted_action_class="shell_command_proposal",
                required_tool_boundary=False,
                authorization_status="candidate_only",
            )
        )


def test_code_patch_action_requires_validation_and_patch_feedback():
    with pytest.raises(ValidationError, match="validation_packet_required_for_code_action"):
        validate_document_action_packet_v1(
            _payload(
                extracted_action_class="patch_proposal",
                required_tool_boundary=True,
                required_validation_packet=False,
                required_patch_feedback_packet=False,
                authorization_status="tool_boundary_required",
            )
        )


def test_real_world_side_effect_requires_action_boundary():
    with pytest.raises(ValidationError, match="action_boundary_required_for_document_action"):
        validate_document_action_packet_v1(
            _payload(
                extracted_action_class="email_or_message_proposal",
                required_action_boundary=False,
                authorization_status="candidate_only",
            )
        )


def test_no_subprocess_shell_or_file_io_exists_in_helper_source():
    import weslr.document_to_action_boundary as mod

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
