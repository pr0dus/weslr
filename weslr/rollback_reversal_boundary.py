"""Metadata-only rollback and reversal boundary v1.

This module classifies rollback/reversal metadata into bounded packets.
It is deterministic, import-safe, pure in-memory, and fail-closed.
No subprocess. No shell execution. No file I/O. No model/provider/API calls.
No runtime wiring. No `.weslr` access. No rollback execution, action execution,
tool execution, patch application, commit/push authority, public claims,
proof claims, or learning claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Mapping

HELPER_TYPE_V1 = "rollback_reversal_boundary_v1"
PACKET_TYPE_V1 = "rollback_packet_v1"
SUMMARY_TYPE_V1 = "rollback_summary_v1"

ALLOWED_TARGET_CLASSES_V1 = {
    "file_change",
    "patch_application",
    "generated_artifact",
    "artifact_export",
    "database_mutation",
    "configuration_change",
    "deployment_change",
    "git_commit",
    "git_push",
    "memory_write",
    "email_or_message_send",
    "calendar_change",
    "device_control",
    "public_post",
    "payment_or_billing",
    "account_or_permission_change",
    "external_api_mutation",
    "unknown_reversal_target",
}

ALLOWED_REVERSIBILITY_LEVELS_V1 = {
    "fully_reversible",
    "partially_reversible",
    "compensating_action_only",
    "irreversible",
    "reversibility_unknown",
    "blocked_until_classified",
}

ALLOWED_ROLLBACK_PLAN_STATUSES_V1 = {
    "not_required_metadata_only",
    "required_missing",
    "draft_plan_present",
    "validated_plan_present",
    "owner_review_required",
    "operator_review_required",
    "blocked_missing_plan",
    "blocked_irreversible_without_acknowledgment",
    "blocked_unknown_reversibility",
    "unknown_status",
}

ALLOWED_ROLLBACK_ACTION_CLASSES_V1 = {
    "restore_previous_file",
    "reverse_patch",
    "restore_manifest",
    "restore_artifact_version",
    "database_restore",
    "configuration_restore",
    "deployment_rollback",
    "git_revert_proposal",
    "memory_delete_or_revert",
    "calendar_event_revert",
    "device_state_restore",
    "public_post_retract_or_correction",
    "payment_refund_or_manual_review",
    "account_permission_restore",
    "external_api_compensating_action",
    "no_safe_rollback_available",
    "unknown_rollback_action",
}

ALLOWED_CLEAR_BLOCKED_UNKNOWN_V1 = {"clear", "blocked", "unknown", "poisoned"}

FORBIDDEN_FIELD_HINTS_V1 = (
    "hidden_prompt",
    "raw_private",
    "private_data",
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "secret_token",
    "secret_key",
    "api_key",
    "credential",
    "password",
)

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "proof",
    "correctness",
    "public readiness",
    "public_readiness",
    "security certification",
    "certification",
    "legal compliance",
    "public claim",
    "runtime authority",
    "model authority",
    "tool authority",
    "learning claim",
    "autonomous learning",
)

POISON_HINTS_V1 = (
    "poison",
    "poisoned",
    "toxic",
)

TARGET_HINTS_V1 = {
    "file": "file_change",
    "write": "file_change",
    "edit": "file_change",
    "patch": "patch_application",
    "artifact export": "artifact_export",
    "export": "artifact_export",
    "artifact": "generated_artifact",
    "generated artifact": "generated_artifact",
    "build output": "generated_artifact",
    "database": "database_mutation",
    "db": "database_mutation",
    "config": "configuration_change",
    "configuration": "configuration_change",
    "deploy": "deployment_change",
    "release": "deployment_change",
    "commit": "git_commit",
    "push": "git_push",
    "memory": "memory_write",
    "email": "email_or_message_send",
    "message": "email_or_message_send",
    "calendar": "calendar_change",
    "event": "calendar_change",
    "device": "device_control",
    "public post": "public_post",
    "post": "public_post",
    "payment": "payment_or_billing",
    "billing": "payment_or_billing",
    "account": "account_or_permission_change",
    "permission": "account_or_permission_change",
    "api": "external_api_mutation",
    "external api": "external_api_mutation",
}

ROLLBACK_ACTION_BY_TARGET_V1 = {
    "file_change": "restore_previous_file",
    "patch_application": "reverse_patch",
    "generated_artifact": "restore_artifact_version",
    "artifact_export": "restore_manifest",
    "database_mutation": "database_restore",
    "configuration_change": "configuration_restore",
    "deployment_change": "deployment_rollback",
    "git_commit": "git_revert_proposal",
    "git_push": "git_revert_proposal",
    "memory_write": "memory_delete_or_revert",
    "email_or_message_send": "external_api_compensating_action",
    "calendar_change": "calendar_event_revert",
    "device_control": "device_state_restore",
    "public_post": "public_post_retract_or_correction",
    "payment_or_billing": "payment_refund_or_manual_review",
    "account_or_permission_change": "account_permission_restore",
    "external_api_mutation": "external_api_compensating_action",
    "unknown_reversal_target": "unknown_rollback_action",
}

REVERSIBILITY_BY_TARGET_V1 = {
    "file_change": "fully_reversible",
    "patch_application": "partially_reversible",
    "generated_artifact": "partially_reversible",
    "artifact_export": "compensating_action_only",
    "database_mutation": "compensating_action_only",
    "configuration_change": "fully_reversible",
    "deployment_change": "partially_reversible",
    "git_commit": "partially_reversible",
    "git_push": "partially_reversible",
    "memory_write": "compensating_action_only",
    "email_or_message_send": "compensating_action_only",
    "calendar_change": "compensating_action_only",
    "device_control": "partially_reversible",
    "public_post": "compensating_action_only",
    "payment_or_billing": "compensating_action_only",
    "account_or_permission_change": "partially_reversible",
    "external_api_mutation": "compensating_action_only",
    "unknown_reversal_target": "blocked_until_classified",
}

class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class RollbackPacket:
    rollback_packet_id: str
    action_authority_packet_ref: str
    tool_use_packet_ref: str
    document_action_packet_ref: str
    patch_feedback_packet_ref: str
    validation_packet_ref: str
    artifact_provenance_ref: str
    target_class: str
    target_summary: str
    reversibility_level: str
    rollback_plan_status: str
    rollback_action_class: str
    rollback_summary: str
    before_state_ref: str
    after_state_ref: str
    diff_summary_ref: str
    manifest_ref: str
    backup_ref: str
    audit_log_required: bool
    owner_review_required: bool
    operator_review_required: bool
    explicit_irreversible_ack_required: bool
    reversal_test_required: bool
    validation_rerun_required: bool
    rollback_execution_allowed: bool
    original_action_allowed: bool
    compensating_action_required: bool
    public_correction_required: bool
    external_notification_required: bool
    retention_or_deletion_implication: bool
    privacy_or_pii_implication: bool
    secret_risk_status: str
    path_risk_status: str
    network_policy_status: str
    financial_effect_possible: bool
    physical_effect_possible: bool
    public_effect_possible: bool
    irreversible_effect_possible: bool
    recommended_next_check: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class RollbackSummary:
    summary_type: str
    rollback_packet_id: str
    target_class: str
    reversibility_level: str
    rollback_plan_status: str
    rollback_action_class: str
    rollback_execution_allowed: bool
    original_action_allowed: bool
    owner_review_required: bool
    operator_review_required: bool
    recommended_next_check: str
    target_summary: str


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _normalize_text(value: Any) -> str:
    return _safe_text(value).lower()


def _safe_metadata_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return dict(asdict(value).get("safe_metadata") or {})
    return {}


def _contains_forbidden_field(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _normalize_text(key) in FORBIDDEN_FIELD_HINTS_V1:
                return True
            if _contains_forbidden_field(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_field(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(hint in blob for hint in FORBIDDEN_FIELD_HINTS_V1)


def _contains_claim_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_claim_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _contains_poison_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_poison_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_poison_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(hint in blob for hint in POISON_HINTS_V1)


def _packet_like(value: Any) -> RollbackPacket:
    if isinstance(value, RollbackPacket):
        return value
    if is_dataclass(value):
        value = asdict(value)
    if not isinstance(value, Mapping):
        raise TypeError("rollback packet must be mapping-like")
    safe_metadata = value.get("safe_metadata")
    return RollbackPacket(
        rollback_packet_id=_safe_text(value.get("rollback_packet_id")),
        action_authority_packet_ref=_safe_text(value.get("action_authority_packet_ref")),
        tool_use_packet_ref=_safe_text(value.get("tool_use_packet_ref")),
        document_action_packet_ref=_safe_text(value.get("document_action_packet_ref")),
        patch_feedback_packet_ref=_safe_text(value.get("patch_feedback_packet_ref")),
        validation_packet_ref=_safe_text(value.get("validation_packet_ref")),
        artifact_provenance_ref=_safe_text(value.get("artifact_provenance_ref")),
        target_class=_safe_text(value.get("target_class")),
        target_summary=_safe_text(value.get("target_summary")),
        reversibility_level=_safe_text(value.get("reversibility_level")),
        rollback_plan_status=_safe_text(value.get("rollback_plan_status")),
        rollback_action_class=_safe_text(value.get("rollback_action_class")),
        rollback_summary=_safe_text(value.get("rollback_summary")),
        before_state_ref=_safe_text(value.get("before_state_ref")),
        after_state_ref=_safe_text(value.get("after_state_ref")),
        diff_summary_ref=_safe_text(value.get("diff_summary_ref")),
        manifest_ref=_safe_text(value.get("manifest_ref")),
        backup_ref=_safe_text(value.get("backup_ref")),
        audit_log_required=_safe_bool(value.get("audit_log_required", False)),
        owner_review_required=_safe_bool(value.get("owner_review_required", False)),
        operator_review_required=_safe_bool(value.get("operator_review_required", False)),
        explicit_irreversible_ack_required=_safe_bool(value.get("explicit_irreversible_ack_required", False)),
        reversal_test_required=_safe_bool(value.get("reversal_test_required", False)),
        validation_rerun_required=_safe_bool(value.get("validation_rerun_required", False)),
        rollback_execution_allowed=_safe_bool(value.get("rollback_execution_allowed", False)),
        original_action_allowed=_safe_bool(value.get("original_action_allowed", False)),
        compensating_action_required=_safe_bool(value.get("compensating_action_required", False)),
        public_correction_required=_safe_bool(value.get("public_correction_required", False)),
        external_notification_required=_safe_bool(value.get("external_notification_required", False)),
        retention_or_deletion_implication=_safe_bool(value.get("retention_or_deletion_implication", False)),
        privacy_or_pii_implication=_safe_bool(value.get("privacy_or_pii_implication", False)),
        secret_risk_status=_safe_text(value.get("secret_risk_status", "clear")),
        path_risk_status=_safe_text(value.get("path_risk_status", "clear")),
        network_policy_status=_safe_text(value.get("network_policy_status", "clear")),
        financial_effect_possible=_safe_bool(value.get("financial_effect_possible", False)),
        physical_effect_possible=_safe_bool(value.get("physical_effect_possible", False)),
        public_effect_possible=_safe_bool(value.get("public_effect_possible", False)),
        irreversible_effect_possible=_safe_bool(value.get("irreversible_effect_possible", False)),
        recommended_next_check=_safe_text(value.get("recommended_next_check", "inspect_rollback_metadata_only")),
        runtime_authority=_safe_bool(value.get("runtime_authority", False)),
        writes_state=_safe_bool(value.get("writes_state", False)),
        model_provider_used=_safe_bool(value.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(value.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(value.get("learning_claimed", False)),
        safe_metadata=_safe_metadata_dict(safe_metadata),
    )


def build_rollback_packet_v1(**kwargs: Any) -> RollbackPacket:
    payload = {
        "rollback_packet_id": kwargs.get("rollback_packet_id", "rollback_packet_v1"),
        "action_authority_packet_ref": kwargs.get("action_authority_packet_ref", "action_authority_packet_v1"),
        "tool_use_packet_ref": kwargs.get("tool_use_packet_ref", "tool_use_packet_v1"),
        "document_action_packet_ref": kwargs.get("document_action_packet_ref", "document_action_packet_v1"),
        "patch_feedback_packet_ref": kwargs.get("patch_feedback_packet_ref", "patch_feedback_packet_v1"),
        "validation_packet_ref": kwargs.get("validation_packet_ref", "validation_packet_v1"),
        "artifact_provenance_ref": kwargs.get("artifact_provenance_ref", "artifact_provenance_v1"),
        "target_class": kwargs.get("target_class", "unknown_reversal_target"),
        "target_summary": kwargs.get("target_summary", "Metadata-only rollback candidate."),
        "reversibility_level": kwargs.get("reversibility_level", "blocked_until_classified"),
        "rollback_plan_status": kwargs.get("rollback_plan_status", "not_required_metadata_only"),
        "rollback_action_class": kwargs.get("rollback_action_class", "unknown_rollback_action"),
        "rollback_summary": kwargs.get("rollback_summary", "Metadata-only rollback summary."),
        "before_state_ref": kwargs.get("before_state_ref", ""),
        "after_state_ref": kwargs.get("after_state_ref", ""),
        "diff_summary_ref": kwargs.get("diff_summary_ref", ""),
        "manifest_ref": kwargs.get("manifest_ref", ""),
        "backup_ref": kwargs.get("backup_ref", ""),
        "audit_log_required": kwargs.get("audit_log_required", True),
        "owner_review_required": kwargs.get("owner_review_required", False),
        "operator_review_required": kwargs.get("operator_review_required", False),
        "explicit_irreversible_ack_required": kwargs.get("explicit_irreversible_ack_required", False),
        "reversal_test_required": kwargs.get("reversal_test_required", False),
        "validation_rerun_required": kwargs.get("validation_rerun_required", False),
        "rollback_execution_allowed": kwargs.get("rollback_execution_allowed", False),
        "original_action_allowed": kwargs.get("original_action_allowed", False),
        "compensating_action_required": kwargs.get("compensating_action_required", False),
        "public_correction_required": kwargs.get("public_correction_required", False),
        "external_notification_required": kwargs.get("external_notification_required", False),
        "retention_or_deletion_implication": kwargs.get("retention_or_deletion_implication", False),
        "privacy_or_pii_implication": kwargs.get("privacy_or_pii_implication", False),
        "secret_risk_status": kwargs.get("secret_risk_status", "clear"),
        "path_risk_status": kwargs.get("path_risk_status", "clear"),
        "network_policy_status": kwargs.get("network_policy_status", "clear"),
        "financial_effect_possible": kwargs.get("financial_effect_possible", False),
        "physical_effect_possible": kwargs.get("physical_effect_possible", False),
        "public_effect_possible": kwargs.get("public_effect_possible", False),
        "irreversible_effect_possible": kwargs.get("irreversible_effect_possible", False),
        "recommended_next_check": kwargs.get("recommended_next_check", "inspect_rollback_metadata_only"),
        "runtime_authority": kwargs.get("runtime_authority", False),
        "writes_state": kwargs.get("writes_state", False),
        "model_provider_used": kwargs.get("model_provider_used", False),
        "public_claim_allowed": kwargs.get("public_claim_allowed", False),
        "proof_claim_allowed": kwargs.get("proof_claim_allowed", False),
        "learning_claimed": kwargs.get("learning_claimed", False),
        "safe_metadata": kwargs.get("safe_metadata", {}),
    }
    payload.update({k: v for k, v in kwargs.items() if k in payload})
    return _packet_like(payload)


def classify_reversal_target_v1(
    *,
    target_class: str | None = None,
    target_summary: str | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> str:
    candidate = _safe_text(target_class).strip().lower()
    if candidate in ALLOWED_TARGET_CLASSES_V1:
        return candidate
    probe = " ".join([
        _safe_text(target_class),
        _safe_text(target_summary),
        " ".join(_safe_text(item) for item in (safe_metadata or {}).values()) if isinstance(safe_metadata, Mapping) else "",
    ]).lower()
    for hint, klass in TARGET_HINTS_V1.items():
        if hint in probe:
            return klass
    return "unknown_reversal_target"


def evaluate_reversibility_v1(packet: Any) -> RollbackPacket:
    current = _packet_like(packet)
    target_class = classify_reversal_target_v1(
        target_class=current.target_class,
        target_summary=current.target_summary,
        safe_metadata=current.safe_metadata,
    )

    target_summary = current.target_summary or {
        "file_change": "File change rollback requires previous-state metadata.",
        "patch_application": "Patch application rollback requires reverse-patch metadata.",
        "generated_artifact": "Generated artifact rollback requires version/provenance metadata.",
        "artifact_export": "Artifact export rollback requires manifest and retraction policy.",
        "database_mutation": "Database mutation rollback requires backup or compensating action metadata.",
        "configuration_change": "Configuration change rollback requires previous config metadata.",
        "deployment_change": "Deployment rollback requires rollback strategy and review metadata.",
        "git_commit": "Git commit rollback requires source-control revert metadata.",
        "git_push": "Git push rollback requires source-control rollback policy.",
        "memory_write": "Memory write rollback requires deletion or reversal boundary metadata.",
        "email_or_message_send": "Message rollback requires compensating notification metadata.",
        "calendar_change": "Calendar rollback requires safe-state event reversal metadata.",
        "device_control": "Device rollback requires safe-state recovery metadata.",
        "public_post": "Public post rollback requires correction or retraction metadata.",
        "payment_or_billing": "Payment rollback requires refund or manual review metadata.",
        "account_or_permission_change": "Account rollback requires permission restore metadata.",
        "external_api_mutation": "External API rollback requires compensating action metadata.",
        "unknown_reversal_target": "Unknown reversal target remains blocked until classified.",
    }.get(target_class, "Metadata-only rollback candidate.")

    reversibility_level = current.reversibility_level or REVERSIBILITY_BY_TARGET_V1.get(target_class, "reversibility_unknown")
    rollback_action_class = current.rollback_action_class or ROLLBACK_ACTION_BY_TARGET_V1.get(target_class, "unknown_rollback_action")

    has_before = bool(current.before_state_ref)
    has_after = bool(current.after_state_ref)
    has_diff = bool(current.diff_summary_ref)
    has_manifest = bool(current.manifest_ref)
    has_backup = bool(current.backup_ref)
    has_plan_refs = any([current.before_state_ref, current.after_state_ref, current.diff_summary_ref, current.manifest_ref, current.backup_ref])

    secret_risk_status = current.secret_risk_status if current.secret_risk_status in ALLOWED_CLEAR_BLOCKED_UNKNOWN_V1 else "unknown"
    path_risk_status = current.path_risk_status if current.path_risk_status in ALLOWED_CLEAR_BLOCKED_UNKNOWN_V1 else "unknown"
    network_policy_status = current.network_policy_status if current.network_policy_status in ALLOWED_CLEAR_BLOCKED_UNKNOWN_V1 else "unknown"

    owner_review_required = current.owner_review_required or target_class in {
        "file_change",
        "configuration_change",
        "generated_artifact",
        "artifact_export",
        "git_commit",
        "memory_write",
        "account_or_permission_change",
    }
    operator_review_required = current.operator_review_required or target_class in {
        "patch_application",
        "database_mutation",
        "deployment_change",
        "git_push",
        "external_api_mutation",
    }
    explicit_irreversible_ack_required = current.explicit_irreversible_ack_required or target_class in {
        "deployment_change",
        "public_post",
        "payment_or_billing",
        "account_or_permission_change",
        "device_control",
    }
    reversal_test_required = current.reversal_test_required or target_class in {
        "patch_application",
        "deployment_change",
        "database_mutation",
        "configuration_change",
        "git_push",
    }
    validation_rerun_required = current.validation_rerun_required or target_class in {
        "patch_application",
        "deployment_change",
        "configuration_change",
        "database_mutation",
        "file_change",
    }

    rollback_plan_status = current.rollback_plan_status or "unknown_status"
    if target_class == "unknown_reversal_target":
        if "metadata-only" in _normalize_text(target_summary) or current.rollback_plan_status == "not_required_metadata_only":
            rollback_plan_status = "not_required_metadata_only"
        else:
            rollback_plan_status = "blocked_unknown_reversibility"
    elif reversibility_level == "irreversible" and not explicit_irreversible_ack_required:
        rollback_plan_status = "blocked_irreversible_without_acknowledgment"
    elif reversibility_level == "reversibility_unknown":
        rollback_plan_status = "blocked_unknown_reversibility"
    elif not has_plan_refs and target_class != "unknown_reversal_target":
        rollback_plan_status = "required_missing"
    elif has_plan_refs and any([has_before, has_diff, has_manifest, has_backup]):
        rollback_plan_status = "validated_plan_present"
    elif has_plan_refs:
        rollback_plan_status = "draft_plan_present"
    elif current.rollback_plan_status in {"owner_review_required", "operator_review_required"}:
        rollback_plan_status = current.rollback_plan_status
    elif target_class == "unknown_reversal_target":
        rollback_plan_status = "not_required_metadata_only"

    rollback_summary = current.rollback_summary or {
        "file_change": "Restore previous file state metadata only.",
        "patch_application": "Reverse patch metadata only.",
        "generated_artifact": "Restore artifact version metadata only.",
        "artifact_export": "Restore manifest and retraction metadata only.",
        "database_mutation": "Database restore or compensating action metadata only.",
        "configuration_change": "Restore previous configuration metadata only.",
        "deployment_change": "Deployment rollback metadata only.",
        "git_commit": "Git revert proposal metadata only.",
        "git_push": "Git revert proposal metadata only.",
        "memory_write": "Memory delete or revert metadata only.",
        "email_or_message_send": "Compensating notification metadata only.",
        "calendar_change": "Calendar event revert metadata only.",
        "device_control": "Device state restore metadata only.",
        "public_post": "Retraction or correction metadata only.",
        "payment_or_billing": "Refund or manual review metadata only.",
        "account_or_permission_change": "Account permission restore metadata only.",
        "external_api_mutation": "External API compensating action metadata only.",
        "unknown_reversal_target": "Blocked until classified metadata only.",
    }.get(target_class, "Metadata-only rollback summary.")

    if target_class == "unknown_reversal_target":
        reversibility_level = "blocked_until_classified"
        rollback_action_class = "unknown_rollback_action"
    elif reversibility_level not in ALLOWED_REVERSIBILITY_LEVELS_V1:
        reversibility_level = "reversibility_unknown"
        rollback_action_class = "unknown_rollback_action"
    elif current.irreversible_effect_possible:
        reversibility_level = "irreversible"
    elif target_class in {"database_mutation", "public_post", "payment_or_billing", "email_or_message_send", "calendar_change", "external_api_mutation"}:
        reversibility_level = REVERSIBILITY_BY_TARGET_V1.get(target_class, "compensating_action_only")
    elif target_class in {"deployment_change", "git_commit", "git_push", "device_control", "account_or_permission_change", "patch_application"}:
        reversibility_level = REVERSIBILITY_BY_TARGET_V1.get(target_class, "partially_reversible")
    else:
        reversibility_level = REVERSIBILITY_BY_TARGET_V1.get(target_class, reversibility_level)

    if current.safe_metadata and _contains_poison_marker(current.safe_metadata):
        rollback_plan_status = "blocked_unknown_reversibility"
        rollback_action_class = "unknown_rollback_action"

    if target_class in {"database_mutation", "payment_or_billing"} and not has_backup and not has_plan_refs:
        rollback_plan_status = "blocked_missing_plan"
    if target_class in {"patch_application", "file_change", "configuration_change", "deployment_change", "git_commit", "git_push"} and not (has_before or has_diff or has_manifest or has_plan_refs):
        rollback_plan_status = "blocked_missing_plan"
    if target_class in {"public_post", "email_or_message_send", "calendar_change", "device_control", "memory_write", "account_or_permission_change", "external_api_mutation"} and not has_plan_refs:
        rollback_plan_status = "blocked_missing_plan"

    original_action_allowed = False
    if current.original_action_allowed and rollback_plan_status in {"required_missing", "blocked_missing_plan", "blocked_irreversible_without_acknowledgment", "blocked_unknown_reversibility"}:
        original_action_allowed = True

    return replace(
        current,
        target_class=target_class,
        target_summary=target_summary,
        reversibility_level=reversibility_level,
        rollback_plan_status=rollback_plan_status,
        rollback_action_class=rollback_action_class,
        rollback_summary=rollback_summary,
        audit_log_required=True,
        owner_review_required=owner_review_required,
        operator_review_required=operator_review_required,
        explicit_irreversible_ack_required=explicit_irreversible_ack_required,
        reversal_test_required=reversal_test_required,
        validation_rerun_required=validation_rerun_required,
        rollback_execution_allowed=False,
        original_action_allowed=original_action_allowed,
        compensating_action_required=current.compensating_action_required or target_class in {
            "database_mutation",
            "public_post",
            "payment_or_billing",
            "email_or_message_send",
            "calendar_change",
            "device_control",
            "external_api_mutation",
            "memory_write",
        },
        public_correction_required=current.public_correction_required or target_class == "public_post",
        external_notification_required=current.external_notification_required or target_class in {"email_or_message_send", "payment_or_billing"},
        retention_or_deletion_implication=current.retention_or_deletion_implication or target_class in {"memory_write", "artifact_export"},
        privacy_or_pii_implication=current.privacy_or_pii_implication or target_class in {"memory_write", "account_or_permission_change", "email_or_message_send", "payment_or_billing"},
        secret_risk_status=secret_risk_status,
        path_risk_status=path_risk_status,
        network_policy_status=network_policy_status,
        financial_effect_possible=current.financial_effect_possible or target_class == "payment_or_billing",
        physical_effect_possible=current.physical_effect_possible or target_class == "device_control",
        public_effect_possible=current.public_effect_possible or target_class == "public_post",
        irreversible_effect_possible=current.irreversible_effect_possible or target_class in {"deployment_change", "public_post", "payment_or_billing", "account_or_permission_change", "device_control"},
        recommended_next_check=current.recommended_next_check or {
            "file_change": "collect_before_state_and_diff_metadata",
            "patch_application": "collect_reverse_patch_and_validation_rerun",
            "generated_artifact": "collect_version_and_manifest_metadata",
            "artifact_export": "collect_manifest_provenance_and_retraction_policy",
            "database_mutation": "collect_backup_or_compensating_policy",
            "configuration_change": "collect_previous_config_reference",
            "deployment_change": "collect_rollback_strategy_and_review",
            "git_commit": "collect_source_control_revert_policy",
            "git_push": "collect_source_control_revert_policy",
            "memory_write": "collect_memory_deletion_or_reversal_boundary",
            "email_or_message_send": "collect_notification_compensation_policy",
            "calendar_change": "collect_event_reversal_plan",
            "device_control": "collect_safe_state_recovery_plan",
            "public_post": "collect_correction_or_retraction_policy",
            "payment_or_billing": "collect_refund_or_manual_review_policy",
            "account_or_permission_change": "collect_permission_restore_policy",
            "external_api_mutation": "collect_compensating_action_policy",
            "unknown_reversal_target": "classify_target_before_planning",
        }.get(target_class, "inspect_rollback_metadata_only"),
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
    )


def select_rollback_action_v1(packet: Any) -> str:
    current = _packet_like(packet)
    normalized = evaluate_reversibility_v1(current)
    return normalized.rollback_action_class


def validate_rollback_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")

    raw = _packet_like(packet)
    normalized = evaluate_reversibility_v1(raw)
    normalized = replace(normalized, rollback_action_class=select_rollback_action_v1(normalized))

    if raw.target_class not in ALLOWED_TARGET_CLASSES_V1:
        raise ValidationError("unknown_reversal_target")
    if raw.reversibility_level not in ALLOWED_REVERSIBILITY_LEVELS_V1:
        raise ValidationError("unknown_reversibility_blocks_action")
    if raw.rollback_plan_status not in ALLOWED_ROLLBACK_PLAN_STATUSES_V1:
        raise ValidationError("unknown_status_promoted_as_valid")
    if raw.rollback_action_class not in ALLOWED_ROLLBACK_ACTION_CLASSES_V1:
        raise ValidationError("unknown_rollback_action")
    for status_name in (raw.secret_risk_status, raw.path_risk_status, raw.network_policy_status):
        if status_name not in ALLOWED_CLEAR_BLOCKED_UNKNOWN_V1:
            raise ValidationError("unknown_status_promoted_as_valid")

    if raw.rollback_execution_allowed:
        raise ValidationError("rollback_execution_not_allowed")
    if raw.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if raw.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if raw.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if raw.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if raw.proof_claim_allowed:
        raise ValidationError("proof_claim_allowed_must_be_false")
    if raw.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")

    if raw.safe_metadata and _contains_claim_marker(raw.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")
    if raw.target_summary and _contains_claim_marker(raw.target_summary):
        raise ValidationError("forbidden_claim_marker_detected")
    if raw.rollback_summary and _contains_claim_marker(raw.rollback_summary):
        raise ValidationError("forbidden_claim_marker_detected")

    if raw.safe_metadata and _contains_poison_marker(raw.safe_metadata):
        raise ValidationError("poisoned_source_cannot_authorize_action")

    if normalized.target_class == "unknown_reversal_target":
        if normalized.rollback_plan_status != "not_required_metadata_only":
            raise ValidationError("unknown_target_promoted_as_safe")
    elif normalized.reversibility_level == "blocked_until_classified":
        raise ValidationError("unknown_reversibility_blocks_action")

    if normalized.reversibility_level == "reversibility_unknown":
        raise ValidationError("unknown_reversibility_blocks_action")

    if normalized.rollback_plan_status in {"required_missing", "blocked_missing_plan"} and raw.original_action_allowed:
        raise ValidationError("original_action_not_authorized")

    if raw.original_action_allowed:
        raise ValidationError("original_action_not_authorized")

    if normalized.rollback_plan_status == "blocked_irreversible_without_acknowledgment" and not raw.explicit_irreversible_ack_required:
        raise ValidationError("irreversible_action_requires_explicit_acknowledgment")

    if normalized.reversibility_level == "irreversible" and not raw.explicit_irreversible_ack_required:
        raise ValidationError("irreversible_action_requires_explicit_acknowledgment")

    if raw.target_class == "file_change" and not (raw.before_state_ref or raw.diff_summary_ref):
        raise ValidationError("file_write_requires_before_or_diff_reference")
    if raw.target_class == "patch_application" and not (raw.diff_summary_ref or raw.patch_feedback_packet_ref):
        raise ValidationError("patch_application_requires_reverse_or_restore_plan")
    if raw.target_class == "deployment_change" and not raw.validation_packet_ref:
        raise ValidationError("deployment_requires_rollback_plan")
    if raw.target_class == "database_mutation" and not (raw.backup_ref or raw.compensating_action_required):
        raise ValidationError("database_mutation_requires_backup_or_compensating_action")
    if raw.target_class == "configuration_change" and not raw.before_state_ref:
        raise ValidationError("configuration_change_requires_previous_config_reference")
    if raw.target_class == "device_control" and not (raw.before_state_ref or raw.backup_ref or raw.compensating_action_required):
        raise ValidationError("device_action_requires_safe_state_plan")
    if raw.target_class == "public_post" and not raw.public_correction_required:
        raise ValidationError("public_post_requires_correction_or_retraction_path")
    if raw.target_class == "payment_or_billing" and not (raw.compensating_action_required or raw.external_notification_required):
        raise ValidationError("payment_requires_manual_review_or_refund_path")
    if raw.target_class == "git_push" and not (raw.before_state_ref or raw.diff_summary_ref or raw.rollback_summary):
        raise ValidationError("git_push_requires_source_control_rollback_policy")
    if raw.target_class == "memory_write" and not raw.retention_or_deletion_implication:
        raise ValidationError("memory_write_requires_deletion_or_reversal_boundary")
    if raw.target_class == "artifact_export" and not (raw.manifest_ref and raw.artifact_provenance_ref and raw.public_correction_required is not None):
        raise ValidationError("artifact_export_requires_manifest_provenance_and_retraction_policy")

    return True


def summarize_rollback_packet_v1(packet: Any) -> RollbackSummary:
    normalized = _packet_like(packet)
    validate_rollback_packet_v1(normalized)
    return RollbackSummary(
        summary_type=SUMMARY_TYPE_V1,
        rollback_packet_id=normalized.rollback_packet_id,
        target_class=normalized.target_class,
        reversibility_level=normalized.reversibility_level,
        rollback_plan_status=normalized.rollback_plan_status,
        rollback_action_class=normalized.rollback_action_class,
        rollback_execution_allowed=normalized.rollback_execution_allowed,
        original_action_allowed=normalized.original_action_allowed,
        owner_review_required=normalized.owner_review_required,
        operator_review_required=normalized.operator_review_required,
        recommended_next_check=normalized.recommended_next_check,
        target_summary=normalized.target_summary,
    )


def to_rollback_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(key): to_rollback_json_safe_v1(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_rollback_json_safe_v1(item) for item in value]
    if isinstance(value, tuple):
        return [to_rollback_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_rollback_json_safe_v1(item) for item in sorted(value, key=_safe_text)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_text(value)


def build_initial_rollback_examples_v1() -> list[RollbackPacket]:
    examples: list[RollbackPacket] = []

    examples.append(build_rollback_packet_v1(
        rollback_packet_id="metadata_only_summary_v1",
        action_authority_packet_ref="action_authority_metadata_only_v1",
        tool_use_packet_ref="tool_use_metadata_only_v1",
        document_action_packet_ref="document_action_metadata_only_v1",
        patch_feedback_packet_ref="patch_feedback_metadata_only_v1",
        validation_packet_ref="validation_metadata_only_v1",
        artifact_provenance_ref="artifact_metadata_only_v1",
        target_class="unknown_reversal_target",
        target_summary="Metadata-only summary requires no rollback.",
        reversibility_level="blocked_until_classified",
        rollback_plan_status="not_required_metadata_only",
        rollback_action_class="unknown_rollback_action",
        rollback_summary="Summary-only metadata packet.",
        recommended_next_check="inspect_rollback_metadata_only",
        safe_metadata={"example_name": "metadata_only_summary"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="file_write_previous_state_required_v1",
        action_authority_packet_ref="action_authority_file_write_v1",
        tool_use_packet_ref="tool_use_file_write_v1",
        document_action_packet_ref="document_action_file_write_v1",
        patch_feedback_packet_ref="patch_feedback_file_write_v1",
        validation_packet_ref="validation_file_write_v1",
        artifact_provenance_ref="artifact_file_write_v1",
        target_class="file_change",
        target_summary="File write requires previous-state reference.",
        reversibility_level="fully_reversible",
        rollback_plan_status="validated_plan_present",
        rollback_action_class="restore_previous_file",
        rollback_summary="Restore previous file state.",
        before_state_ref="before_file_v1",
        diff_summary_ref="diff_file_v1",
        owner_review_required=True,
        validation_rerun_required=True,
        safe_metadata={"example_name": "file_write_previous_state_required"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="patch_application_reverse_patch_validation_rerun_v1",
        action_authority_packet_ref="action_authority_patch_v1",
        tool_use_packet_ref="tool_use_patch_v1",
        document_action_packet_ref="document_action_patch_v1",
        patch_feedback_packet_ref="patch_feedback_patch_v1",
        validation_packet_ref="validation_patch_v1",
        artifact_provenance_ref="artifact_patch_v1",
        target_class="patch_application",
        target_summary="Patch application requires reverse-patch plan and validation rerun.",
        reversibility_level="partially_reversible",
        rollback_plan_status="validated_plan_present",
        rollback_action_class="reverse_patch",
        rollback_summary="Reverse patch plan with validation rerun.",
        diff_summary_ref="diff_patch_v1",
        validation_rerun_required=True,
        reversal_test_required=True,
        operator_review_required=True,
        safe_metadata={"example_name": "patch_application_reverse_patch_validation_rerun"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="deployment_rollback_owner_operator_v1",
        action_authority_packet_ref="action_authority_deployment_v1",
        tool_use_packet_ref="tool_use_deployment_v1",
        document_action_packet_ref="document_action_deployment_v1",
        patch_feedback_packet_ref="patch_feedback_deployment_v1",
        validation_packet_ref="validation_deployment_v1",
        artifact_provenance_ref="artifact_deployment_v1",
        target_class="deployment_change",
        target_summary="Deployment requires rollback plan and owner/operator review.",
        reversibility_level="partially_reversible",
        rollback_plan_status="operator_review_required",
        rollback_action_class="deployment_rollback",
        rollback_summary="Deployment rollback strategy ready for review.",
        before_state_ref="before_deployment_v1",
        validation_rerun_required=True,
        owner_review_required=True,
        operator_review_required=True,
        explicit_irreversible_ack_required=True,
        safe_metadata={"example_name": "deployment_rollback_owner_operator"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="database_mutation_backup_restore_blocked_v1",
        action_authority_packet_ref="action_authority_database_v1",
        tool_use_packet_ref="tool_use_database_v1",
        document_action_packet_ref="document_action_database_v1",
        patch_feedback_packet_ref="patch_feedback_database_v1",
        validation_packet_ref="validation_database_v1",
        artifact_provenance_ref="artifact_database_v1",
        target_class="database_mutation",
        target_summary="Database mutation blocks without backup/restore policy.",
        reversibility_level="compensating_action_only",
        rollback_plan_status="blocked_missing_plan",
        rollback_action_class="database_restore",
        rollback_summary="Database restore blocked until backup policy exists.",
        operator_review_required=True,
        compensating_action_required=True,
        safe_metadata={"example_name": "database_mutation_backup_restore_blocked"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="configuration_change_previous_config_reference_v1",
        action_authority_packet_ref="action_authority_configuration_v1",
        tool_use_packet_ref="tool_use_configuration_v1",
        document_action_packet_ref="document_action_configuration_v1",
        patch_feedback_packet_ref="patch_feedback_configuration_v1",
        validation_packet_ref="validation_configuration_v1",
        artifact_provenance_ref="artifact_configuration_v1",
        target_class="configuration_change",
        target_summary="Config change requires previous config reference.",
        reversibility_level="fully_reversible",
        rollback_plan_status="validated_plan_present",
        rollback_action_class="configuration_restore",
        rollback_summary="Restore previous configuration.",
        before_state_ref="before_config_v1",
        validation_rerun_required=True,
        safe_metadata={"example_name": "configuration_change_previous_config_reference"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="device_action_safe_state_recovery_v1",
        action_authority_packet_ref="action_authority_device_v1",
        tool_use_packet_ref="tool_use_device_v1",
        document_action_packet_ref="document_action_device_v1",
        patch_feedback_packet_ref="patch_feedback_device_v1",
        validation_packet_ref="validation_device_v1",
        artifact_provenance_ref="artifact_device_v1",
        target_class="device_control",
        target_summary="Device action requires safe-state recovery plan.",
        reversibility_level="partially_reversible",
        rollback_plan_status="owner_review_required",
        rollback_action_class="device_state_restore",
        rollback_summary="Safe-state recovery plan for device control.",
        before_state_ref="safe_state_device_v1",
        owner_review_required=True,
        explicit_irreversible_ack_required=True,
        safe_metadata={"example_name": "device_action_safe_state_recovery"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="public_post_correction_retraction_v1",
        action_authority_packet_ref="action_authority_public_post_v1",
        tool_use_packet_ref="tool_use_public_post_v1",
        document_action_packet_ref="document_action_public_post_v1",
        patch_feedback_packet_ref="patch_feedback_public_post_v1",
        validation_packet_ref="validation_public_post_v1",
        artifact_provenance_ref="artifact_public_post_v1",
        target_class="public_post",
        target_summary="Public post requires correction/retraction path.",
        reversibility_level="compensating_action_only",
        rollback_plan_status="validated_plan_present",
        rollback_action_class="public_post_retract_or_correction",
        rollback_summary="Public correction or retraction path ready.",
        public_correction_required=True,
        external_notification_required=True,
        explicit_irreversible_ack_required=True,
        safe_metadata={"example_name": "public_post_correction_retraction"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="payment_action_manual_review_refund_blocked_v1",
        action_authority_packet_ref="action_authority_payment_v1",
        tool_use_packet_ref="tool_use_payment_v1",
        document_action_packet_ref="document_action_payment_v1",
        patch_feedback_packet_ref="patch_feedback_payment_v1",
        validation_packet_ref="validation_payment_v1",
        artifact_provenance_ref="artifact_payment_v1",
        target_class="payment_or_billing",
        target_summary="Payment action requires manual review/refund path and stays blocked.",
        reversibility_level="compensating_action_only",
        rollback_plan_status="blocked_missing_plan",
        rollback_action_class="payment_refund_or_manual_review",
        rollback_summary="Payment refund or manual review policy required.",
        compensating_action_required=True,
        external_notification_required=True,
        financial_effect_possible=True,
        explicit_irreversible_ack_required=True,
        safe_metadata={"example_name": "payment_action_manual_review_refund_blocked"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="git_push_source_control_rollback_policy_blocked_v1",
        action_authority_packet_ref="action_authority_git_push_v1",
        tool_use_packet_ref="tool_use_git_push_v1",
        document_action_packet_ref="document_action_git_push_v1",
        patch_feedback_packet_ref="patch_feedback_git_push_v1",
        validation_packet_ref="validation_git_push_v1",
        artifact_provenance_ref="artifact_git_push_v1",
        target_class="git_push",
        target_summary="Git push is blocked without source-control rollback policy.",
        reversibility_level="partially_reversible",
        rollback_plan_status="blocked_missing_plan",
        rollback_action_class="git_revert_proposal",
        rollback_summary="Git revert policy missing.",
        before_state_ref="git_before_push_v1",
        operator_review_required=True,
        safe_metadata={"example_name": "git_push_source_control_rollback_policy_blocked"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="memory_write_deletion_reversal_boundary_v1",
        action_authority_packet_ref="action_authority_memory_v1",
        tool_use_packet_ref="tool_use_memory_v1",
        document_action_packet_ref="document_action_memory_v1",
        patch_feedback_packet_ref="patch_feedback_memory_v1",
        validation_packet_ref="validation_memory_v1",
        artifact_provenance_ref="artifact_memory_v1",
        target_class="memory_write",
        target_summary="Memory write requires memory deletion/reversal boundary.",
        reversibility_level="compensating_action_only",
        rollback_plan_status="validated_plan_present",
        rollback_action_class="memory_delete_or_revert",
        rollback_summary="Memory delete or revert boundary noted.",
        retention_or_deletion_implication=True,
        privacy_or_pii_implication=True,
        owner_review_required=True,
        safe_metadata={"example_name": "memory_write_deletion_reversal_boundary"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="artifact_export_manifest_provenance_retraction_v1",
        action_authority_packet_ref="action_authority_artifact_export_v1",
        tool_use_packet_ref="tool_use_artifact_export_v1",
        document_action_packet_ref="document_action_artifact_export_v1",
        patch_feedback_packet_ref="patch_feedback_artifact_export_v1",
        validation_packet_ref="validation_artifact_export_v1",
        artifact_provenance_ref="artifact_export_provenance_v1",
        target_class="artifact_export",
        target_summary="Artifact export requires manifest/provenance and retraction policy.",
        reversibility_level="compensating_action_only",
        rollback_plan_status="validated_plan_present",
        rollback_action_class="restore_manifest",
        rollback_summary="Manifest, provenance, and retraction policy recorded.",
        manifest_ref="manifest_artifact_export_v1",
        backup_ref="artifact_backup_v1",
        public_correction_required=True,
        retention_or_deletion_implication=True,
        safe_metadata={"example_name": "artifact_export_manifest_provenance_retraction"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="irreversible_action_requires_acknowledgment_blocked_v1",
        action_authority_packet_ref="action_authority_irreversible_v1",
        tool_use_packet_ref="tool_use_irreversible_v1",
        document_action_packet_ref="document_action_irreversible_v1",
        patch_feedback_packet_ref="patch_feedback_irreversible_v1",
        validation_packet_ref="validation_irreversible_v1",
        artifact_provenance_ref="artifact_irreversible_v1",
        target_class="deployment_change",
        target_summary="Irreversible action is blocked without explicit acknowledgment.",
        reversibility_level="irreversible",
        rollback_plan_status="blocked_irreversible_without_acknowledgment",
        rollback_action_class="no_safe_rollback_available",
        rollback_summary="Irreversible action blocked until acknowledgment.",
        explicit_irreversible_ack_required=True,
        irreversible_effect_possible=True,
        owner_review_required=True,
        operator_review_required=True,
        safe_metadata={"example_name": "irreversible_action_requires_acknowledgment_blocked"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="unknown_reversibility_blocks_action_v1",
        action_authority_packet_ref="action_authority_unknown_reversibility_v1",
        tool_use_packet_ref="tool_use_unknown_reversibility_v1",
        document_action_packet_ref="document_action_unknown_reversibility_v1",
        patch_feedback_packet_ref="patch_feedback_unknown_reversibility_v1",
        validation_packet_ref="validation_unknown_reversibility_v1",
        artifact_provenance_ref="artifact_unknown_reversibility_v1",
        target_class="unknown_reversal_target",
        target_summary="Metadata-only unknown reversibility blocks action.",
        reversibility_level="blocked_until_classified",
        rollback_plan_status="blocked_unknown_reversibility",
        rollback_action_class="unknown_rollback_action",
        rollback_summary="Unknown reversibility remains blocked.",
        safe_metadata={"example_name": "unknown_reversibility_blocks_action"},
    ))
    examples.append(build_rollback_packet_v1(
        rollback_packet_id="rollback_plan_exists_does_not_authorize_original_action_v1",
        action_authority_packet_ref="action_authority_rollback_plan_v1",
        tool_use_packet_ref="tool_use_rollback_plan_v1",
        document_action_packet_ref="document_action_rollback_plan_v1",
        patch_feedback_packet_ref="patch_feedback_rollback_plan_v1",
        validation_packet_ref="validation_rollback_plan_v1",
        artifact_provenance_ref="artifact_rollback_plan_v1",
        target_class="file_change",
        target_summary="Rollback plan exists but does not authorize original action.",
        reversibility_level="fully_reversible",
        rollback_plan_status="validated_plan_present",
        rollback_action_class="restore_previous_file",
        rollback_summary="Rollback plan documented; original action still blocked.",
        before_state_ref="before_rollback_plan_v1",
        diff_summary_ref="diff_rollback_plan_v1",
        safe_metadata={"example_name": "rollback_plan_exists_does_not_authorize_original_action"},
    ))

    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "PACKET_TYPE_V1",
    "SUMMARY_TYPE_V1",
    "ALLOWED_TARGET_CLASSES_V1",
    "ALLOWED_REVERSIBILITY_LEVELS_V1",
    "ALLOWED_ROLLBACK_PLAN_STATUSES_V1",
    "ALLOWED_ROLLBACK_ACTION_CLASSES_V1",
    "RollbackPacket",
    "RollbackSummary",
    "ValidationError",
    "build_rollback_packet_v1",
    "classify_reversal_target_v1",
    "evaluate_reversibility_v1",
    "select_rollback_action_v1",
    "validate_rollback_packet_v1",
    "summarize_rollback_packet_v1",
    "to_rollback_json_safe_v1",
    "build_initial_rollback_examples_v1",
]
