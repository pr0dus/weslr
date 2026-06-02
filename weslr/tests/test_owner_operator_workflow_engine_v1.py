from __future__ import annotations

import ast
import inspect

import pytest

from weslr.owner_operator_workflow_engine import (  # noqa: F401
    ALLOWED_OWNER_OPERATOR_DECISION_CLASSES_V1,
    ALLOWED_WORKFLOW_REQUEST_CLASSES_V1,
    ALLOWED_WORKFLOW_SCOPE_CLASSES_V1,
    ALLOWED_WORKFLOW_STATUSES_V1,
    OwnerOperatorWorkflowPacket,
    OwnerOperatorWorkflowSummary,
    ValidationError,
    build_initial_owner_operator_workflow_examples_v1,
    build_owner_operator_workflow_packet_v1,
    classify_owner_operator_decision_v1,
    classify_workflow_request_v1,
    evaluate_workflow_readiness_v1,
    select_workflow_next_step_v1,
    summarize_owner_operator_workflow_packet_v1,
    to_owner_operator_workflow_json_safe_v1,
    validate_owner_operator_workflow_packet_v1,
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
    payload = dict(
        workflow_packet_id="owner_operator_workflow_base_v1",
        workflow_request_class="metadata_review_request",
        request_summary="Metadata-only owner/operator workflow candidate.",
        requester_role="reviewer",
        source_request_ref="source_base_v1",
        document_action_packet_ref="",
        tool_use_packet_ref="",
        action_authority_packet_ref="",
        rollback_packet_ref="",
        validation_packet_ref="",
        patch_feedback_packet_ref="",
        artifact_provenance_ref="",
        workflow_status="candidate_created",
        decision_class="no_decision_metadata_only",
        approval_scope_class="metadata_only_scope",
        approval_scope_summary="Metadata-only scope; no execution.",
        scope_limit_summary="No tools, writes, sends, or state changes.",
        constraints={"note": "metadata only"},
        single_action_only=False,
        time_limited=False,
        expires_after_action=False,
        owner_review_required=False,
        operator_review_required=False,
        dual_review_required=False,
        explicit_confirmation_required=False,
        legal_review_required=False,
        security_review_required=False,
        payment_review_required=False,
        device_safety_review_required=False,
        public_claim_review_required=False,
        preflight_required=False,
        preflight_status="not_started",
        validation_required=False,
        rollback_required=False,
        rollback_plan_ref="",
        audit_log_required=True,
        approval_metadata_recorded=True,
        approval_grants_runtime_authority=False,
        approval_grants_execution_authority=False,
        approval_grants_broad_future_authority=False,
        external_side_effect_possible=False,
        public_effect_possible=False,
        financial_effect_possible=False,
        physical_effect_possible=False,
        irreversible_effect_possible=False,
        secret_risk_status="clear",
        path_risk_status="clear",
        privacy_status="clear",
        poison_status="clear",
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
        recommended_next_check="inspect_workflow_metadata_only",
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
        safe_metadata={"example_name": "base"},
    )
    payload.update(overrides)
    return build_owner_operator_workflow_packet_v1(**payload)


def _example_by_id(packet_id: str):
    for item in build_initial_owner_operator_workflow_examples_v1():
        if item.workflow_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.owner_operator_workflow_engine as mod

    assert mod.HELPER_TYPE_V1 == "owner_operator_workflow_engine_v1"
    assert "weslr.chat_responder" not in inspect.getmodule(mod).__dict__


def test_public_apis_are_available_and_deterministic():
    packet = _packet()
    assert isinstance(packet, OwnerOperatorWorkflowPacket)
    assert evaluate_workflow_readiness_v1(packet) == packet
    assert isinstance(summarize_owner_operator_workflow_packet_v1(packet), OwnerOperatorWorkflowSummary)
    assert select_workflow_next_step_v1(packet) == "metadata_only_no_execution"
    assert classify_workflow_request_v1(workflow_request_class="owner_approval_request") == "owner_approval_request"
    assert classify_owner_operator_decision_v1(decision_class="approve_dry_run") == "approve_dry_run"


def test_request_and_decision_classification_fails_closed():
    assert classify_workflow_request_v1(request_summary="please clarify") == "clarification_request"
    assert classify_workflow_request_v1(request_summary="unknown thing") == "unknown_workflow_request"
    assert classify_owner_operator_decision_v1(decision_summary="request changes") == "request_changes"
    assert classify_owner_operator_decision_v1(decision_summary="unknown") == "unknown_decision"


def test_json_safe_conversion_does_not_mutate_input():
    raw = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    snapshot = {"packet": {"name": "alpha", "nested": [1, {"two": 2}], "flags": {"a", "b"}}}
    converted = to_owner_operator_workflow_json_safe_v1(raw)
    assert raw == snapshot
    assert converted is not raw
    assert converted["packet"]["nested"][1]["two"] == 2


def test_summary_contains_no_raw_private_or_secret_fields():
    summary = summarize_owner_operator_workflow_packet_v1(_packet())
    text = str(summary).lower()
    assert "raw_private" not in text
    assert "secret_token" not in text
    assert "hidden_prompt" not in text


def test_initial_examples_count_and_example_shape():
    examples = build_initial_owner_operator_workflow_examples_v1()
    assert len(examples) == 15
    assert {item.workflow_request_class for item in examples}.issubset(ALLOWED_WORKFLOW_REQUEST_CLASSES_V1)
    assert {item.decision_class for item in examples}.issubset(ALLOWED_OWNER_OPERATOR_DECISION_CLASSES_V1)
    assert {item.approval_scope_class for item in examples}.issubset(ALLOWED_WORKFLOW_SCOPE_CLASSES_V1)
    assert {item.workflow_status for item in examples}.issubset(ALLOWED_WORKFLOW_STATUSES_V1)


@pytest.mark.parametrize(
    "packet_id",
    [
        "metadata_review_stays_metadata_only_v1",
        "owner_approval_awaits_owner_review_v1",
        "operator_review_awaits_operator_review_v1",
        "dual_owner_operator_review_requires_both_roles_v1",
        "clarification_request_blocks_progression_v1",
        "validation_review_requires_validation_packet_ref_v1",
        "patch_proposal_review_links_patch_feedback_no_apply_v1",
        "rollback_plan_review_requires_rollback_refs_v1",
        "artifact_export_review_requires_provenance_v1",
        "deployment_review_requires_validation_and_rollback_v1",
        "public_post_review_requires_public_claim_review_v1",
        "payment_review_remains_blocked_v1",
        "device_safety_review_remains_blocked_v1",
        "memory_write_review_remains_blocked_v1",
    ],
)
def test_initial_examples_validate(packet_id: str):
    assert validate_owner_operator_workflow_packet_v1(_example_by_id(packet_id)) is True


def test_broad_runtime_example_is_intentionally_blocked():
    with pytest.raises(ValidationError, match="broad_runtime_scope_blocked"):
        validate_owner_operator_workflow_packet_v1(_example_by_id("broad_runtime_approval_blocked_v1"))


def test_unknown_request_decision_scope_and_status_fail_closed():
    with pytest.raises(ValidationError, match="unknown_request_promoted_as_valid"):
        validate_owner_operator_workflow_packet_v1(_packet(workflow_request_class="mystery"))
    with pytest.raises(ValidationError, match="unknown_decision_promoted_as_valid"):
        validate_owner_operator_workflow_packet_v1(_packet(decision_class="mystery"))
    with pytest.raises(ValidationError, match="unknown_scope_promoted_as_valid"):
        validate_owner_operator_workflow_packet_v1(_packet(approval_scope_class="mystery"))
    with pytest.raises(ValidationError, match="unknown_status_promoted_as_valid"):
        validate_owner_operator_workflow_packet_v1(_packet(workflow_status="mystery"))


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
        "commit_allowed",
        "push_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
        "approval_grants_runtime_authority",
        "approval_grants_execution_authority",
        "approval_grants_broad_future_authority",
    ],
)
def test_forbidden_true_flags_fail_validation(field_name: str):
    with pytest.raises(ValidationError, match=f"{field_name}_must_be_false"):
        validate_owner_operator_workflow_packet_v1(_packet(**{field_name: True}))


def test_approval_cannot_grant_scope_or_authority():
    with pytest.raises(ValidationError, match="approval_without_scope_summary"):
        validate_owner_operator_workflow_packet_v1(_packet(approval_scope_summary=""))
    with pytest.raises(ValidationError, match="single_action_approval_requires_single_action_only"):
        validate_owner_operator_workflow_packet_v1(_packet(decision_class="approve_single_action", single_action_only=False))


def test_rollback_and_validation_requirements_fail_when_missing():
    with pytest.raises(ValidationError, match="rollback_required_without_rollback_refs"):
        validate_owner_operator_workflow_packet_v1(_packet(rollback_required=True, rollback_packet_ref="", rollback_plan_ref=""))
    with pytest.raises(ValidationError, match="validation_required_without_validation_packet"):
        validate_owner_operator_workflow_packet_v1(_packet(validation_required=True, validation_packet_ref=""))


def test_public_financial_and_physical_effects_require_proper_review_flags():
    with pytest.raises(ValidationError, match="public_effect_without_public_review_requirement"):
        validate_owner_operator_workflow_packet_v1(_packet(public_effect_possible=True, public_claim_review_required=False))
    with pytest.raises(ValidationError, match="financial_effect_without_payment_review_requirement"):
        validate_owner_operator_workflow_packet_v1(_packet(financial_effect_possible=True, payment_review_required=False))
    with pytest.raises(ValidationError, match="physical_or_device_effect_without_device_safety_review_requirement"):
        validate_owner_operator_workflow_packet_v1(_packet(physical_effect_possible=True, device_safety_review_required=False))


def test_secret_path_privacy_and_poison_risks_block_approval_progression():
    with pytest.raises(ValidationError, match="secret_or_path_risk_blocks_approval_progression"):
        validate_owner_operator_workflow_packet_v1(_packet(secret_risk_status="blocked", decision_class="approve_metadata_only"))
    with pytest.raises(ValidationError, match="secret_or_path_risk_blocks_approval_progression"):
        validate_owner_operator_workflow_packet_v1(_packet(path_risk_status="blocked", decision_class="approve_metadata_only"))
    with pytest.raises(ValidationError, match="secret_or_path_risk_blocks_approval_progression"):
        validate_owner_operator_workflow_packet_v1(_packet(privacy_status="blocked", decision_class="approve_metadata_only"))
    with pytest.raises(ValidationError, match="poisoned_source_blocks_approval_progression"):
        validate_owner_operator_workflow_packet_v1(_packet(poison_status="poisoned", decision_class="approve_metadata_only"))


def test_document_or_model_output_cannot_self_authorize_approval():
    with pytest.raises(ValidationError, match="document_or_model_output_self_authorizes_approval"):
        validate_owner_operator_workflow_packet_v1(_packet(request_summary="please authorize this action"))
    with pytest.raises(ValidationError, match="document_or_model_output_self_authorizes_approval"):
        validate_owner_operator_workflow_packet_v1(_packet(safe_metadata={"model_output": "self-authorize this action"}))


def test_rejected_request_changes_and_clarification_block_progression():
    rejected = evaluate_workflow_readiness_v1(_packet(decision_class="reject"))
    changed = evaluate_workflow_readiness_v1(_packet(decision_class="request_changes"))
    clarified = evaluate_workflow_readiness_v1(_packet(decision_class="request_clarification"))
    assert rejected.workflow_status == "rejected"
    assert changed.workflow_status == "clarification_required"
    assert clarified.workflow_status == "clarification_required"
    assert select_workflow_next_step_v1(rejected) == "stop_and_report_rejection"
    assert select_workflow_next_step_v1(changed) == "request_changes_and_pause"
    assert select_workflow_next_step_v1(clarified) == "request_clarification"


def test_owner_and_operator_review_statuses_are_routed():
    owner = evaluate_workflow_readiness_v1(_packet(workflow_request_class="owner_approval_request", decision_class="defer_to_owner"))
    operator = evaluate_workflow_readiness_v1(_packet(workflow_request_class="operator_review_request", decision_class="defer_to_operator"))
    dual = evaluate_workflow_readiness_v1(_packet(workflow_request_class="dual_owner_operator_review_request", decision_class="approve_with_constraints"))
    assert owner.workflow_status == "awaiting_owner_review"
    assert operator.workflow_status == "awaiting_operator_review"
    assert dual.workflow_status == "awaiting_dual_review"


def test_no_subprocess_shell_or_file_io_exists_in_helper_source():
    import weslr.owner_operator_workflow_engine as mod

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
