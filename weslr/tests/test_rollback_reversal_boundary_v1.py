from __future__ import annotations

import ast
import inspect
import sys

import pytest

from weslr.rollback_reversal_boundary import (
    ALLOWED_REVERSIBILITY_LEVELS_V1,
    ALLOWED_ROLLBACK_ACTION_CLASSES_V1,
    ALLOWED_ROLLBACK_PLAN_STATUSES_V1,
    ALLOWED_TARGET_CLASSES_V1,
    RollbackPacket,
    RollbackSummary,
    ValidationError,
    build_initial_rollback_examples_v1,
    build_rollback_packet_v1,
    classify_reversal_target_v1,
    evaluate_reversibility_v1,
    select_rollback_action_v1,
    summarize_rollback_packet_v1,
    to_rollback_json_safe_v1,
    validate_rollback_packet_v1,
)

BASE_PACKET_KWARGS = dict(
    rollback_packet_id="base_rollback_v1",
    action_authority_packet_ref="action_authority_base_v1",
    tool_use_packet_ref="tool_use_base_v1",
    document_action_packet_ref="document_action_base_v1",
    patch_feedback_packet_ref="patch_feedback_base_v1",
    validation_packet_ref="validation_base_v1",
    artifact_provenance_ref="artifact_base_v1",
    target_class="unknown_reversal_target",
    target_summary="Metadata-only rollback summary.",
    reversibility_level="blocked_until_classified",
    rollback_plan_status="not_required_metadata_only",
    rollback_action_class="unknown_rollback_action",
    rollback_summary="Metadata-only rollback summary.",
    before_state_ref="",
    after_state_ref="",
    diff_summary_ref="",
    manifest_ref="",
    backup_ref="",
    audit_log_required=True,
    owner_review_required=False,
    operator_review_required=False,
    explicit_irreversible_ack_required=False,
    reversal_test_required=False,
    validation_rerun_required=False,
    rollback_execution_allowed=False,
    original_action_allowed=False,
    compensating_action_required=False,
    public_correction_required=False,
    external_notification_required=False,
    retention_or_deletion_implication=False,
    privacy_or_pii_implication=False,
    secret_risk_status="clear",
    path_risk_status="clear",
    network_policy_status="clear",
    financial_effect_possible=False,
    physical_effect_possible=False,
    public_effect_possible=False,
    irreversible_effect_possible=False,
    recommended_next_check="inspect_rollback_metadata_only",
    runtime_authority=False,
    writes_state=False,
    model_provider_used=False,
    public_claim_allowed=False,
    proof_claim_allowed=False,
    learning_claimed=False,
    safe_metadata={"example_name": "base_rollback"},
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
    return build_rollback_packet_v1(**payload)


def _payload(**overrides):
    payload = to_rollback_json_safe_v1(_packet())
    payload.update(overrides)
    return payload


def _example_by_id(packet_id: str):
    for item in build_initial_rollback_examples_v1():
        if item.rollback_packet_id == packet_id:
            return item
    raise AssertionError(f"missing example: {packet_id}")


def test_module_imports_safely():
    import weslr.rollback_reversal_boundary as mod

    assert mod.HELPER_TYPE_V1 == "rollback_reversal_boundary_v1"
    assert "weslr.chat_responder" not in sys.modules
    assert "weslr.main" not in sys.modules
    assert "dialogue" not in sys.modules
    assert "chat_ui" not in sys.modules


def test_public_apis_and_classification():
    assert classify_reversal_target_v1(target_class="git_push") == "git_push"
    assert classify_reversal_target_v1(target_summary="restore this file") == "file_change"
    assert classify_reversal_target_v1(target_class="mystery") == "unknown_reversal_target"
    assert ALLOWED_TARGET_CLASSES_V1
    assert ALLOWED_REVERSIBILITY_LEVELS_V1
    assert ALLOWED_ROLLBACK_PLAN_STATUSES_V1
    assert ALLOWED_ROLLBACK_ACTION_CLASSES_V1


def test_evaluates_reversibility_and_selects_action():
    packet = evaluate_reversibility_v1(_packet(target_class="deployment_change", validation_packet_ref="validation_deployment_v1", before_state_ref="before_deployment_v1"))
    assert packet.reversibility_level in ALLOWED_REVERSIBILITY_LEVELS_V1
    assert packet.rollback_plan_status in ALLOWED_ROLLBACK_PLAN_STATUSES_V1
    assert packet.rollback_action_class in ALLOWED_ROLLBACK_ACTION_CLASSES_V1
    assert select_rollback_action_v1(packet) == packet.rollback_action_class


def test_builds_deterministic_packet():
    first = _packet()
    second = _packet()
    assert first == second
    assert isinstance(first, RollbackPacket)


def test_json_safe_conversion_does_not_mutate_input():
    packet = _packet(safe_metadata={"nested": ["x", {"y": "z"}]})
    original = packet.safe_metadata.copy()
    payload = to_rollback_json_safe_v1(packet)
    assert packet.safe_metadata == original
    assert payload["safe_metadata"]["nested"][1]["y"] == "z"
    assert isinstance(payload, dict)


def test_summary_is_metadata_only():
    summary = summarize_rollback_packet_v1(_packet(target_class="file_change", before_state_ref="before_v1", diff_summary_ref="diff_v1"))
    assert isinstance(summary, RollbackSummary)
    safe = to_rollback_json_safe_v1(summary)
    assert "secret" not in str(safe).lower()
    assert "password" not in str(safe).lower()
    assert "raw_private" not in str(safe).lower()


def test_initial_examples_validate():
    for example in build_initial_rollback_examples_v1():
        assert validate_rollback_packet_v1(example) is True


def test_unknown_target_fails_closed():
    with pytest.raises(ValidationError, match="unknown_reversal_target"):
        validate_rollback_packet_v1(_payload(target_class="mystery_target", target_summary="real action"))


def test_unknown_reversibility_fails_closed():
    with pytest.raises(ValidationError, match="unknown_reversibility_blocks_action"):
        validate_rollback_packet_v1(_payload(target_class="file_change", reversibility_level="mystery_reversibility"))


def test_unknown_rollback_status_fails_closed():
    with pytest.raises(ValidationError, match="unknown_status_promoted_as_valid"):
        validate_rollback_packet_v1(_payload(rollback_plan_status="mystery_status"))


def test_unknown_rollback_action_fails_closed():
    with pytest.raises(ValidationError, match="unknown_rollback_action"):
        validate_rollback_packet_v1(_payload(rollback_action_class="mystery_action"))


def test_rollback_execution_cannot_be_allowed():
    with pytest.raises(ValidationError, match="rollback_execution_not_allowed"):
        validate_rollback_packet_v1(_payload(**{"rollback_execution_allowed": True}))


def test_original_action_cannot_be_allowed_when_plan_missing():
    with pytest.raises(ValidationError, match="original_action_not_authorized"):
        validate_rollback_packet_v1(_payload(target_class="file_change", original_action_allowed=True, rollback_plan_status="blocked_missing_plan"))


def test_irreversible_action_requires_explicit_acknowledgment():
    with pytest.raises(ValidationError, match="irreversible_action_requires_explicit_acknowledgment"):
        validate_rollback_packet_v1(_payload(target_class="deployment_change", irreversible_effect_possible=True, explicit_irreversible_ack_required=False))


def test_file_write_requires_before_or_diff_reference():
    with pytest.raises(ValidationError, match="file_write_requires_before_or_diff_reference"):
        validate_rollback_packet_v1(_payload(target_class="file_change", rollback_plan_status="blocked_missing_plan"))


def test_patch_application_requires_reverse_or_restore_plan():
    with pytest.raises(ValidationError, match="patch_application_requires_reverse_or_restore_plan"):
        validate_rollback_packet_v1(_payload(target_class="patch_application", diff_summary_ref="", patch_feedback_packet_ref=""))


def test_deployment_requires_rollback_plan():
    with pytest.raises(ValidationError, match="deployment_requires_rollback_plan"):
        validate_rollback_packet_v1(_payload(target_class="deployment_change", validation_packet_ref=""))


def test_database_mutation_requires_backup_or_compensating_action():
    with pytest.raises(ValidationError, match="database_mutation_requires_backup_or_compensating_action"):
        validate_rollback_packet_v1(_payload(target_class="database_mutation", backup_ref="", compensating_action_required=False, rollback_plan_status="blocked_missing_plan"))


def test_public_post_requires_correction_or_retraction_path():
    with pytest.raises(ValidationError, match="public_post_requires_correction_or_retraction_path"):
        validate_rollback_packet_v1(_payload(target_class="public_post", public_correction_required=False, rollback_plan_status="blocked_missing_plan"))


def test_payment_requires_manual_review_or_refund_path():
    with pytest.raises(ValidationError, match="payment_requires_manual_review_or_refund_path"):
        validate_rollback_packet_v1(_payload(target_class="payment_or_billing", compensating_action_required=False, external_notification_required=False, rollback_plan_status="blocked_missing_plan"))


def test_device_action_requires_safe_state_plan():
    with pytest.raises(ValidationError, match="device_action_requires_safe_state_plan"):
        validate_rollback_packet_v1(_payload(target_class="device_control", before_state_ref="", backup_ref="", compensating_action_required=False, rollback_plan_status="blocked_missing_plan"))


def test_git_push_requires_source_control_rollback_policy():
    with pytest.raises(ValidationError, match="git_push_requires_source_control_rollback_policy"):
        validate_rollback_packet_v1(_payload(target_class="git_push", before_state_ref="", diff_summary_ref="", rollback_summary="", rollback_plan_status="blocked_missing_plan"))


def test_memory_write_requires_deletion_or_reversal_boundary():
    with pytest.raises(ValidationError, match="memory_write_requires_deletion_or_reversal_boundary"):
        validate_rollback_packet_v1(_payload(target_class="memory_write", retention_or_deletion_implication=False, rollback_plan_status="blocked_missing_plan"))


def test_artifact_export_requires_manifest_provenance_and_retraction_policy():
    with pytest.raises(ValidationError, match="artifact_export_requires_manifest_provenance_and_retraction_policy"):
        validate_rollback_packet_v1(_payload(target_class="artifact_export", manifest_ref="", artifact_provenance_ref="", public_correction_required=False))


def test_runtime_write_model_public_proof_learning_flags_cannot_be_true():
    for key in [
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ]:
        with pytest.raises(ValidationError):
            validate_rollback_packet_v1(_payload(**{key: True}))


def test_poisoned_source_cannot_authorize_rollback_or_action():
    with pytest.raises(ValidationError, match="poisoned_source_cannot_authorize_action"):
        validate_rollback_packet_v1(_payload(safe_metadata={"source_poison_status": "poisoned"}))


def test_summary_contains_no_raw_private_secret_fields():
    summary = summarize_rollback_packet_v1(_packet(target_class="configuration_change", before_state_ref="before_cfg_v1"))
    text = str(to_rollback_json_safe_v1(summary)).lower()
    for token in ["raw_private", "raw_answer", "raw_response", "secret_token", "password"]:
        assert token not in text


def test_source_inspection_finds_no_forbidden_io_or_process_calls():
    import weslr.rollback_reversal_boundary as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)

    imports = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            fn = node.func
            name = None
            if isinstance(fn, ast.Name):
                name = fn.id
            elif isinstance(fn, ast.Attribute):
                name = fn.attr
            if name:
                calls.add(name)

    assert not (imports & FORBIDDEN_IMPORT_NAMES)
    assert not (calls & FORBIDDEN_CALL_NAMES)


def test_initial_examples_have_expected_count():
    assert len(build_initial_rollback_examples_v1()) == 15
