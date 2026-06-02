"""Metadata-only action-authority boundary v1.

This module classifies action authority requests into bounded metadata packets.
It is deterministic, import-safe, pure in-memory, and fail-closed.
No subprocess. No shell execution. No file I/O. No model/provider/API calls.
No runtime wiring. No `.weslr` access. No action execution, tool execution,
patch application, commit/push authority, public claims, proof claims, or
learning claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Mapping

HELPER_TYPE_V1 = "action_authority_boundary_v1"
PACKET_TYPE_V1 = "action_authority_packet_v1"
SUMMARY_TYPE_V1 = "action_authority_summary_v1"

ALLOWED_ACTION_CLASSES_V1 = {
    "no_action_summary_only",
    "read_only_inspection",
    "file_write",
    "patch_apply",
    "test_run",
    "shell_command",
    "external_api_mutation",
    "email_or_message_send",
    "calendar_change",
    "device_control",
    "deployment",
    "public_post",
    "payment_or_billing",
    "database_mutation",
    "git_commit",
    "git_push",
    "artifact_export",
    "memory_write",
    "account_or_permission_change",
    "unknown_action",
}

ALLOWED_RISK_LEVELS_V1 = {
    "none_metadata_only",
    "low_reversible",
    "medium_local_state_change",
    "high_external_side_effect",
    "critical_public_financial_physical_or_irreversible",
    "blocked_unknown_risk",
}

ALLOWED_APPROVAL_AUTHORITY_CLASSES_V1 = {
    "no_approval_needed_metadata_only",
    "owner_approval_required",
    "operator_approval_required",
    "dual_owner_operator_approval_required",
    "explicit_user_confirmation_required",
    "legal_review_required",
    "security_review_required",
    "public_claim_review_required",
    "payment_review_required",
    "device_safety_review_required",
    "blocked_no_authority",
    "unknown_approval_authority",
}

ALLOWED_AUTHORITY_STATUSES_V1 = {
    "not_requested",
    "proposal_only",
    "clarification_required",
    "preflight_required",
    "approval_pending",
    "approved_for_dry_run_only",
    "approved_for_read_only",
    "approved_for_sandbox_only",
    "approved_for_single_action",
    "approved_with_constraints",
    "blocked_by_policy",
    "blocked_by_missing_approval",
    "blocked_by_missing_validation",
    "blocked_by_missing_rollback",
    "blocked_by_secret_or_path_risk",
    "blocked_by_public_effect",
    "blocked_by_unknown_risk",
    "unknown_status",
}

ALLOWED_CLEAR_BLOCKED_UNKNOWN_V1 = {"clear", "blocked", "poisoned", "unknown"}

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
    "model authority",
    "tool authority",
    "learning claim",
    "autonomous learning",
)

AUTHORITY_PHRASES_V1 = (
    "authorize",
    "permission to run",
    "self-authorize",
    "go ahead",
    "execute this",
    "run this",
    "do it now",
)

ACTION_HINTS_V1 = {
    "summary": "no_action_summary_only",
    "read": "read_only_inspection",
    "inspect": "read_only_inspection",
    "write file": "file_write",
    "file write": "file_write",
    "patch": "patch_apply",
    "test": "test_run",
    "shell": "shell_command",
    "api": "external_api_mutation",
    "email": "email_or_message_send",
    "message": "email_or_message_send",
    "calendar": "calendar_change",
    "device": "device_control",
    "deploy": "deployment",
    "post": "public_post",
    "public": "public_post",
    "payment": "payment_or_billing",
    "billing": "payment_or_billing",
    "database": "database_mutation",
    "commit": "git_commit",
    "push": "git_push",
    "export": "artifact_export",
    "memory": "memory_write",
    "permission": "account_or_permission_change",
    "account": "account_or_permission_change",
}

RISK_BY_ACTION_V1 = {
    "no_action_summary_only": "none_metadata_only",
    "read_only_inspection": "low_reversible",
    "file_write": "medium_local_state_change",
    "patch_apply": "medium_local_state_change",
    "test_run": "low_reversible",
    "shell_command": "high_external_side_effect",
    "external_api_mutation": "high_external_side_effect",
    "email_or_message_send": "high_external_side_effect",
    "calendar_change": "high_external_side_effect",
    "device_control": "critical_public_financial_physical_or_irreversible",
    "deployment": "critical_public_financial_physical_or_irreversible",
    "public_post": "critical_public_financial_physical_or_irreversible",
    "payment_or_billing": "critical_public_financial_physical_or_irreversible",
    "database_mutation": "high_external_side_effect",
    "git_commit": "medium_local_state_change",
    "git_push": "high_external_side_effect",
    "artifact_export": "low_reversible",
    "memory_write": "high_external_side_effect",
    "account_or_permission_change": "critical_public_financial_physical_or_irreversible",
    "unknown_action": "blocked_unknown_risk",
}

class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ActionAuthorityPacket:
    action_authority_packet_id: str
    action_request_ref: str
    source_proposal_ref: str
    document_action_packet_ref: str
    tool_use_packet_ref: str
    validation_packet_ref: str
    patch_feedback_packet_ref: str
    artifact_provenance_ref: str
    action_class: str
    action_summary: str
    action_risk_level: str
    approval_authority_class: str
    authority_status: str
    requested_scope: str
    approved_scope: str
    scope_limit_summary: str
    preflight_required: bool
    preflight_status: str
    owner_approval_required: bool
    operator_approval_required: bool
    explicit_confirmation_required: bool
    rollback_required: bool
    rollback_plan_ref: str
    audit_log_required: bool
    dry_run_required: bool
    validation_required: bool
    secret_risk_status: str
    path_risk_status: str
    network_policy_status: str
    privacy_status: str
    poison_status: str
    public_effect_possible: bool
    external_side_effect_possible: bool
    financial_effect_possible: bool
    physical_effect_possible: bool
    irreversible_effect_possible: bool
    execution_allowed: bool
    tool_execution_allowed: bool
    write_allowed: bool
    send_allowed: bool
    calendar_change_allowed: bool
    device_control_allowed: bool
    deployment_allowed: bool
    public_post_allowed: bool
    payment_allowed: bool
    memory_write_allowed: bool
    commit_allowed: bool
    push_allowed: bool
    recommended_next_check: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ActionAuthoritySummary:
    summary_type: str
    action_authority_packet_id: str
    action_class: str
    action_risk_level: str
    approval_authority_class: str
    authority_status: str
    requested_scope: str
    approved_scope: str
    scope_limit_summary: str
    execution_allowed: bool
    tool_execution_allowed: bool
    write_allowed: bool
    send_allowed: bool
    calendar_change_allowed: bool
    device_control_allowed: bool
    deployment_allowed: bool
    public_post_allowed: bool
    payment_allowed: bool
    memory_write_allowed: bool
    commit_allowed: bool
    push_allowed: bool
    recommended_next_check: str


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
    return " ".join(_safe_text(value).split()).lower()


def _safe_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return { _safe_text(k): to_action_authority_json_safe_v1(v) for k, v in value.items() }
    return {"value": to_action_authority_json_safe_v1(value)}


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _contains_forbidden_field(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(hint in key_text for hint in FORBIDDEN_FIELD_HINTS_V1):
                return key_text
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    return ""


def _contains_claim_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if key_text in {"safe_metadata", "action_summary", "scope_limit_summary", "requested_scope", "approved_scope"} or key_text.endswith("_metadata"):
                if _contains_claim_marker(item):
                    return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_claim_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _contains_authorize_phrase(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if key_text in {"action_request_text", "proposal_text", "document_text", "model_output", "source_text", "action_summary"}:
                if _contains_authorize_phrase(item):
                    return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_authorize_phrase(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in AUTHORITY_PHRASES_V1)


def to_action_authority_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return { _safe_text(key): to_action_authority_json_safe_v1(item) for key, item in sorted(value.items(), key=lambda item: _safe_text(item[0])) }
    if isinstance(value, tuple):
        return [to_action_authority_json_safe_v1(item) for item in value]
    if isinstance(value, list):
        return [to_action_authority_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        items = [to_action_authority_json_safe_v1(item) for item in value]
        return sorted(items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_action_authority_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_action_authority_json_safe_v1(vars(value))
    return _safe_text(value)


def _packet_like(value: Any) -> ActionAuthorityPacket:
    if isinstance(value, ActionAuthorityPacket):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    safe_metadata = value.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        safe_metadata = {"value": safe_metadata}
    return ActionAuthorityPacket(
        action_authority_packet_id=_safe_text(value.get("action_authority_packet_id")),
        action_request_ref=_safe_text(value.get("action_request_ref")),
        source_proposal_ref=_safe_text(value.get("source_proposal_ref")),
        document_action_packet_ref=_safe_text(value.get("document_action_packet_ref")),
        tool_use_packet_ref=_safe_text(value.get("tool_use_packet_ref")),
        validation_packet_ref=_safe_text(value.get("validation_packet_ref")),
        patch_feedback_packet_ref=_safe_text(value.get("patch_feedback_packet_ref")),
        artifact_provenance_ref=_safe_text(value.get("artifact_provenance_ref")),
        action_class=_safe_text(value.get("action_class")),
        action_summary=_safe_text(value.get("action_summary")),
        action_risk_level=_safe_text(value.get("action_risk_level")),
        approval_authority_class=_safe_text(value.get("approval_authority_class")),
        authority_status=_safe_text(value.get("authority_status")),
        requested_scope=_safe_text(value.get("requested_scope")),
        approved_scope=_safe_text(value.get("approved_scope")),
        scope_limit_summary=_safe_text(value.get("scope_limit_summary")),
        preflight_required=_safe_bool(value.get("preflight_required", False)),
        preflight_status=_safe_text(value.get("preflight_status", "unknown")),
        owner_approval_required=_safe_bool(value.get("owner_approval_required", False)),
        operator_approval_required=_safe_bool(value.get("operator_approval_required", False)),
        explicit_confirmation_required=_safe_bool(value.get("explicit_confirmation_required", False)),
        rollback_required=_safe_bool(value.get("rollback_required", False)),
        rollback_plan_ref=_safe_text(value.get("rollback_plan_ref")),
        audit_log_required=_safe_bool(value.get("audit_log_required", False)),
        dry_run_required=_safe_bool(value.get("dry_run_required", False)),
        validation_required=_safe_bool(value.get("validation_required", False)),
        secret_risk_status=_safe_text(value.get("secret_risk_status", "clear")),
        path_risk_status=_safe_text(value.get("path_risk_status", "clear")),
        network_policy_status=_safe_text(value.get("network_policy_status", "clear")),
        privacy_status=_safe_text(value.get("privacy_status", "clear")),
        poison_status=_safe_text(value.get("poison_status", "clear")),
        public_effect_possible=_safe_bool(value.get("public_effect_possible", False)),
        external_side_effect_possible=_safe_bool(value.get("external_side_effect_possible", False)),
        financial_effect_possible=_safe_bool(value.get("financial_effect_possible", False)),
        physical_effect_possible=_safe_bool(value.get("physical_effect_possible", False)),
        irreversible_effect_possible=_safe_bool(value.get("irreversible_effect_possible", False)),
        execution_allowed=_safe_bool(value.get("execution_allowed", False)),
        tool_execution_allowed=_safe_bool(value.get("tool_execution_allowed", False)),
        write_allowed=_safe_bool(value.get("write_allowed", False)),
        send_allowed=_safe_bool(value.get("send_allowed", False)),
        calendar_change_allowed=_safe_bool(value.get("calendar_change_allowed", False)),
        device_control_allowed=_safe_bool(value.get("device_control_allowed", False)),
        deployment_allowed=_safe_bool(value.get("deployment_allowed", False)),
        public_post_allowed=_safe_bool(value.get("public_post_allowed", False)),
        payment_allowed=_safe_bool(value.get("payment_allowed", False)),
        memory_write_allowed=_safe_bool(value.get("memory_write_allowed", False)),
        commit_allowed=_safe_bool(value.get("commit_allowed", False)),
        push_allowed=_safe_bool(value.get("push_allowed", False)),
        recommended_next_check=_safe_text(value.get("recommended_next_check", "inspect_authority_metadata_only")),
        runtime_authority=_safe_bool(value.get("runtime_authority", False)),
        writes_state=_safe_bool(value.get("writes_state", False)),
        model_provider_used=_safe_bool(value.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(value.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(value.get("learning_claimed", False)),
        safe_metadata=dict(safe_metadata or {}),
    )


def classify_action_authority_request_v1(
    *,
    action_class: str | None = None,
    action_summary: str | None = None,
    requested_scope: str | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> str:
    candidate = _safe_text(action_class).strip().lower()
    if candidate in ALLOWED_ACTION_CLASSES_V1:
        return candidate
    probe = " ".join([
        _safe_text(action_class),
        _safe_text(action_summary),
        _safe_text(requested_scope),
        " ".join(_safe_text(item) for item in (safe_metadata or {}).values()) if isinstance(safe_metadata, Mapping) else "",
    ]).lower()
    for hint, klass in ACTION_HINTS_V1.items():
        if hint in probe:
            return klass
    return "unknown_action"


def evaluate_action_risk_v1(packet: Any) -> ActionAuthorityPacket:
    current = _packet_like(packet)
    action_class = classify_action_authority_request_v1(
        action_class=current.action_class,
        action_summary=current.action_summary,
        requested_scope=current.requested_scope,
        safe_metadata=current.safe_metadata,
    )
    action_risk_level = RISK_BY_ACTION_V1.get(action_class, "blocked_unknown_risk")

    public_effect = action_class == "public_post"
    external_effect = action_class in {
        "file_write",
        "patch_apply",
        "test_run",
        "shell_command",
        "external_api_mutation",
        "email_or_message_send",
        "calendar_change",
        "device_control",
        "deployment",
        "public_post",
        "payment_or_billing",
        "database_mutation",
        "git_commit",
        "git_push",
        "artifact_export",
        "memory_write",
        "account_or_permission_change",
    }
    financial_effect = action_class in {"payment_or_billing"}
    physical_effect = action_class in {"device_control"}
    irreversible_effect = action_class in {"deployment", "public_post", "payment_or_billing", "account_or_permission_change", "git_push"}

    approval_authority_class = {
        "no_action_summary_only": "no_approval_needed_metadata_only",
        "read_only_inspection": "owner_approval_required",
        "file_write": "owner_approval_required",
        "patch_apply": "dual_owner_operator_approval_required",
        "test_run": "operator_approval_required",
        "shell_command": "operator_approval_required",
        "external_api_mutation": "operator_approval_required",
        "email_or_message_send": "explicit_user_confirmation_required",
        "calendar_change": "owner_approval_required",
        "device_control": "device_safety_review_required",
        "deployment": "dual_owner_operator_approval_required",
        "public_post": "public_claim_review_required",
        "payment_or_billing": "payment_review_required",
        "database_mutation": "operator_approval_required",
        "git_commit": "owner_approval_required",
        "git_push": "dual_owner_operator_approval_required",
        "artifact_export": "owner_approval_required",
        "memory_write": "owner_approval_required",
        "account_or_permission_change": "security_review_required",
    }.get(action_class, "unknown_approval_authority")

    authority_status = "proposal_only"
    if action_class == "no_action_summary_only":
        authority_status = "not_requested"
    elif action_class == "read_only_inspection":
        authority_status = "approved_for_read_only" if _safe_text(current.requested_scope) == "read_only" else "blocked_by_missing_approval"
    elif action_class == "file_write":
        authority_status = "approved_for_sandbox_only" if _safe_text(current.requested_scope) in {"sandbox", "write_boundary"} else "blocked_by_missing_approval"
    elif action_class == "patch_apply":
        authority_status = "approval_pending"
    elif action_class in {"test_run", "shell_command", "external_api_mutation", "database_mutation", "artifact_export"}:
        authority_status = "preflight_required"
    elif action_class in {"email_or_message_send", "calendar_change", "deployment", "public_post", "payment_or_billing", "memory_write", "account_or_permission_change", "git_commit", "git_push", "device_control"}:
        authority_status = "blocked_by_missing_approval"
    elif action_class == "unknown_action":
        authority_status = "blocked_by_unknown_risk"

    if public_effect:
        authority_status = "blocked_by_public_effect" if authority_status != "approved_for_single_action" else authority_status
    if financial_effect and authority_status not in {"approval_pending", "blocked_by_missing_approval"}:
        authority_status = "blocked_by_missing_approval"
    if physical_effect and authority_status not in {"approval_pending", "blocked_by_missing_approval"}:
        authority_status = "blocked_by_missing_approval"
    if irreversible_effect and authority_status not in {"blocked_by_missing_approval", "approval_pending", "preflight_required"}:
        authority_status = "blocked_by_missing_rollback"

    rollback_required = action_class in {"file_write", "patch_apply", "deployment", "database_mutation", "git_commit", "git_push", "account_or_permission_change", "public_post", "payment_or_billing"}
    validation_required = action_class in {"patch_apply", "test_run", "deployment", "database_mutation", "git_commit", "git_push"}
    preflight_required = action_class in {"read_only_inspection", "file_write", "patch_apply", "test_run", "shell_command", "external_api_mutation", "deployment", "public_post", "payment_or_billing", "memory_write", "account_or_permission_change", "git_commit", "git_push", "device_control"}

    if current.safe_metadata and _contains_authorize_phrase(current.safe_metadata):
        authority_status = "blocked_by_policy"

    action_summary = current.action_summary or {
        "no_action_summary_only": "Metadata-only summary; no execution authority.",
        "read_only_inspection": "Read-only inspection requires explicit read scope.",
        "file_write": "File write requires sandbox/write boundary and rollback.",
        "patch_apply": "Patch apply requires validation, patch feedback, rollback, and approval.",
        "test_run": "Test run requires preflight and does not itself authorize action.",
        "shell_command": "Shell command remains blocked without tool authority.",
        "external_api_mutation": "External API mutation requires approval.",
        "email_or_message_send": "Email send requires explicit confirmation and remains blocked.",
        "calendar_change": "Calendar change requires approval and remains blocked.",
        "device_control": "Device control requires device safety review and remains blocked.",
        "deployment": "Deployment requires validation, rollback, and owner/operator approval.",
        "public_post": "Public post requires public-effect/public-claim review.",
        "payment_or_billing": "Payment action requires payment review and remains blocked.",
        "database_mutation": "Database mutation requires approval and rollback coverage.",
        "git_commit": "Git commit requires explicit source-control authority.",
        "git_push": "Git push requires explicit source-control authority.",
        "artifact_export": "Artifact export is a bounded export request only.",
        "memory_write": "Memory write requires memory write boundary.",
        "account_or_permission_change": "Account or permission change requires security review.",
        "unknown_action": "Unknown action remains blocked by default.",
    }.get(action_class, "Action authority candidate only.")

    requested_scope = current.requested_scope or {
        "no_action_summary_only": "metadata_only",
        "read_only_inspection": "read_only",
        "file_write": "sandbox_write_boundary",
        "patch_apply": "validation_and_patch_feedback",
        "test_run": "validation_runner",
        "shell_command": "tool_use_executor_boundary",
        "external_api_mutation": "operator_review",
        "email_or_message_send": "single_confirmation",
        "calendar_change": "calendar_boundary",
        "device_control": "device_safety_boundary",
        "deployment": "deployment_boundary",
        "public_post": "public_review_boundary",
        "payment_or_billing": "payment_review_boundary",
        "database_mutation": "rollback_boundary",
        "git_commit": "source_control_authority",
        "git_push": "source_control_authority",
        "artifact_export": "export_boundary",
        "memory_write": "memory_boundary",
        "account_or_permission_change": "security_review_boundary",
        "unknown_action": "unknown",
    }.get(action_class, "proposal_only")

    approved_scope = current.approved_scope or {
        "no_action_summary_only": "none",
        "read_only_inspection": "read_only",
        "file_write": "sandbox_only",
        "patch_apply": "none",
        "test_run": "dry_run_only",
        "shell_command": "none",
        "external_api_mutation": "none",
        "email_or_message_send": "none",
        "calendar_change": "none",
        "device_control": "none",
        "deployment": "none",
        "public_post": "none",
        "payment_or_billing": "none",
        "database_mutation": "none",
        "git_commit": "none",
        "git_push": "none",
        "artifact_export": "export_only",
        "memory_write": "none",
        "account_or_permission_change": "none",
        "unknown_action": "none",
    }.get(action_class, "none")

    scope_limit_summary = current.scope_limit_summary or {
        "no_action_summary_only": "summary only; no execution",
        "read_only_inspection": "read-only scope only",
        "file_write": "sandbox write only with rollback",
        "patch_apply": "validation plus patch feedback with rollback",
        "test_run": "dry-run or validation only",
        "shell_command": "tool boundary required",
        "external_api_mutation": "operator approval required",
        "email_or_message_send": "explicit confirmation required",
        "calendar_change": "calendar approval required",
        "device_control": "device safety review required",
        "deployment": "deployment approval and rollback required",
        "public_post": "public review required",
        "payment_or_billing": "payment review required",
        "database_mutation": "rollback and operator review required",
        "git_commit": "source control authority required",
        "git_push": "source control authority required",
        "artifact_export": "export-only boundary",
        "memory_write": "memory boundary required",
        "account_or_permission_change": "security review required",
        "unknown_action": "blocked by default",
    }.get(action_class, "proposal-only")

    result = replace(
        current,
        action_class=action_class,
        action_risk_level=action_risk_level,
        approval_authority_class=approval_authority_class,
        authority_status=authority_status,
        requested_scope=requested_scope,
        approved_scope=approved_scope,
        scope_limit_summary=scope_limit_summary,
        preflight_required=preflight_required,
        preflight_status=current.preflight_status or ("required" if preflight_required else "clear"),
        owner_approval_required=action_class in {"read_only_inspection", "file_write", "calendar_change", "git_commit", "artifact_export", "memory_write"},
        operator_approval_required=action_class in {"patch_apply", "test_run", "shell_command", "external_api_mutation", "database_mutation", "deployment", "git_push", "account_or_permission_change"},
        explicit_confirmation_required=current.explicit_confirmation_required or action_class in {"email_or_message_send"},
        rollback_required=rollback_required,
        audit_log_required=True,
        dry_run_required=action_class in {"test_run", "shell_command", "external_api_mutation", "database_mutation", "deployment", "account_or_permission_change", "git_push"},
        validation_required=validation_required,
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
        public_effect_possible=public_effect,
        external_side_effect_possible=external_effect,
        financial_effect_possible=financial_effect,
        physical_effect_possible=physical_effect,
        irreversible_effect_possible=irreversible_effect,
        recommended_next_check={
            "no_action_summary_only": "inspect_metadata_only",
            "read_only_inspection": "request_read_scope",
            "file_write": "collect_rollback_plan",
            "patch_apply": "collect_validation_and_rollback",
            "test_run": "preflight_validation_only",
            "shell_command": "route_to_tool_use_executor_boundary",
            "external_api_mutation": "operator_review_required",
            "email_or_message_send": "request_explicit_confirmation",
            "calendar_change": "request_calendar_approval",
            "device_control": "request_device_safety_review",
            "deployment": "request_deployment_review",
            "public_post": "request_public_review",
            "payment_or_billing": "request_payment_review",
            "database_mutation": "collect_rollback_and_review",
            "git_commit": "request_source_control_authority",
            "git_push": "request_source_control_authority",
            "artifact_export": "export_only_boundary",
            "memory_write": "request_memory_boundary",
            "account_or_permission_change": "request_security_review",
            "unknown_action": "block_by_default",
        }.get(action_class, "inspect_metadata_only"),
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
    )
    return replace(result, authority_status=select_action_authority_status_v1(result))


def select_action_authority_status_v1(packet: Any) -> str:
    current = _packet_like(packet)
    if current.action_class == "unknown_action":
        return "blocked_by_unknown_risk"
    if current.poison_status == "poisoned":
        return "blocked_by_policy"
    if current.secret_risk_status == "blocked" or current.path_risk_status == "blocked" or current.network_policy_status == "blocked":
        return "blocked_by_secret_or_path_risk"
    if current.public_effect_possible and current.authority_status not in {"blocked_by_public_effect", "approved_for_single_action", "approved_with_constraints"}:
        return "blocked_by_public_effect"
    if current.validation_required and not current.validation_packet_ref:
        return "blocked_by_missing_validation"
    if current.rollback_required and not current.rollback_plan_ref:
        return "blocked_by_missing_rollback"
    if current.action_class in {"patch_apply", "deployment", "database_mutation", "git_commit", "git_push"} and not current.rollback_required:
        return "blocked_by_missing_rollback"
    if current.action_class in {"public_post", "payment_or_billing", "device_control", "deployment", "account_or_permission_change", "git_push"} and current.authority_status == "proposal_only":
        return "blocked_by_missing_approval"
    if current.external_side_effect_possible and current.authority_status in {"proposal_only", "not_requested"}:
        return "blocked_by_missing_approval"
    if current.action_class == "read_only_inspection":
        return current.authority_status if current.requested_scope == "read_only" else "blocked_by_missing_approval"
    return current.authority_status or "proposal_only"


def validate_action_authority_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")

    raw = _packet_like(packet)
    normalized = evaluate_action_risk_v1(raw)
    normalized = replace(normalized, authority_status=select_action_authority_status_v1(normalized))

    if raw.action_class not in ALLOWED_ACTION_CLASSES_V1:
        raise ValidationError("unknown_action_promoted_as_valid")
    if raw.action_risk_level not in ALLOWED_RISK_LEVELS_V1:
        raise ValidationError("unknown_risk_promoted_as_valid")
    if raw.approval_authority_class not in ALLOWED_APPROVAL_AUTHORITY_CLASSES_V1:
        raise ValidationError("unknown_approval_authority_promoted_as_valid")
    if raw.authority_status not in ALLOWED_AUTHORITY_STATUSES_V1:
        raise ValidationError("unknown_status_promoted_as_valid")
    for status_name in (raw.secret_risk_status, raw.path_risk_status, raw.network_policy_status, raw.privacy_status, raw.poison_status):
        if status_name not in ALLOWED_CLEAR_BLOCKED_UNKNOWN_V1:
            raise ValidationError("unknown_status_promoted_as_valid")

    if normalized.secret_risk_status == "blocked" or normalized.path_risk_status == "blocked" or normalized.network_policy_status == "blocked":
        if raw.execution_allowed:
            raise ValidationError("secret_or_path_risk_blocks_execution")

    if raw.execution_allowed:
        raise ValidationError("execution_allowed_must_be_false")
    if raw.tool_execution_allowed:
        raise ValidationError("tool_execution_allowed_must_be_false")
    if raw.write_allowed:
        raise ValidationError("write_allowed_must_be_false")
    if raw.send_allowed:
        raise ValidationError("send_allowed_must_be_false")
    if raw.calendar_change_allowed:
        raise ValidationError("calendar_change_allowed_must_be_false")
    if raw.device_control_allowed:
        raise ValidationError("device_control_allowed_must_be_false")
    if raw.deployment_allowed:
        raise ValidationError("deployment_allowed_must_be_false")
    if raw.public_post_allowed:
        raise ValidationError("public_post_allowed_must_be_false")
    if raw.payment_allowed:
        raise ValidationError("payment_allowed_must_be_false")
    if raw.memory_write_allowed:
        raise ValidationError("memory_write_allowed_must_be_false")
    if raw.commit_allowed:
        raise ValidationError("commit_allowed_must_be_false")
    if raw.push_allowed:
        raise ValidationError("push_allowed_must_be_false")
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

    if raw.action_summary and _contains_claim_marker(raw.action_summary):
        raise ValidationError("forbidden_claim_marker_detected")
    if raw.action_summary and _contains_authorize_phrase(raw.action_summary):
        raise ValidationError("document_text_authorizes_action")
    if raw.safe_metadata and _contains_claim_marker(raw.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")
    if raw.safe_metadata and _contains_authorize_phrase(raw.safe_metadata):
        raise ValidationError("document_text_authorizes_action")

    if normalized.action_class == "unknown_action":
        raise ValidationError("unknown_action_promoted_as_valid")
    if raw.action_class in {"patch_apply", "file_write"} and raw.authority_status == "proposal_only":
        raise ValidationError("patch_proposal_alone_does_not_authorize_action")
    if normalized.validation_required and not normalized.validation_packet_ref:
        raise ValidationError("validation_required_without_validation_packet")
    if normalized.irreversible_effect_possible and not normalized.explicit_confirmation_required:
        raise ValidationError("irreversible_action_requires_acknowledgment")
    if normalized.rollback_required and not normalized.rollback_plan_ref:
        raise ValidationError("rollback_required_without_rollback_plan")
    if normalized.secret_risk_status == "blocked" or normalized.path_risk_status == "blocked" or normalized.network_policy_status == "blocked":
        if raw.execution_allowed:
            raise ValidationError("secret_or_path_risk_blocks_execution")
    if raw.poison_status == "poisoned" and raw.authority_status not in {"blocked_by_policy", "blocked_by_missing_approval", "blocked_by_missing_validation", "blocked_by_missing_rollback", "blocked_by_secret_or_path_risk", "blocked_by_unknown_risk"}:
        raise ValidationError("poisoned_source_cannot_authorize_action")
    if normalized.public_effect_possible and normalized.authority_status not in {"blocked_by_public_effect", "approved_with_constraints", "approved_for_single_action"}:
        raise ValidationError("public_effect_requires_public_review")
    if normalized.financial_effect_possible and normalized.approval_authority_class != "payment_review_required":
        raise ValidationError("financial_effect_requires_payment_review")
    if normalized.physical_effect_possible and normalized.approval_authority_class != "device_safety_review_required":
        raise ValidationError("physical_effect_requires_device_safety_review")
    if normalized.external_side_effect_possible and normalized.authority_status == "proposal_only":
        raise ValidationError("external_side_effect_requires_approval")

    return True


def summarize_action_authority_packet_v1(packet: Any) -> ActionAuthoritySummary:
    normalized = _packet_like(packet)
    validate_action_authority_packet_v1(normalized)
    return ActionAuthoritySummary(
        summary_type=SUMMARY_TYPE_V1,
        action_authority_packet_id=normalized.action_authority_packet_id,
        action_class=normalized.action_class,
        action_risk_level=normalized.action_risk_level,
        approval_authority_class=normalized.approval_authority_class,
        authority_status=normalized.authority_status,
        requested_scope=normalized.requested_scope,
        approved_scope=normalized.approved_scope,
        scope_limit_summary=normalized.scope_limit_summary,
        execution_allowed=normalized.execution_allowed,
        tool_execution_allowed=normalized.tool_execution_allowed,
        write_allowed=normalized.write_allowed,
        send_allowed=normalized.send_allowed,
        calendar_change_allowed=normalized.calendar_change_allowed,
        device_control_allowed=normalized.device_control_allowed,
        deployment_allowed=normalized.deployment_allowed,
        public_post_allowed=normalized.public_post_allowed,
        payment_allowed=normalized.payment_allowed,
        memory_write_allowed=normalized.memory_write_allowed,
        commit_allowed=normalized.commit_allowed,
        push_allowed=normalized.push_allowed,
        recommended_next_check=normalized.recommended_next_check,
    )


def build_action_authority_packet_v1(**kwargs: Any) -> ActionAuthorityPacket:
    packet = ActionAuthorityPacket(
        action_authority_packet_id=_safe_text(kwargs.get("action_authority_packet_id")),
        action_request_ref=_safe_text(kwargs.get("action_request_ref")),
        source_proposal_ref=_safe_text(kwargs.get("source_proposal_ref")),
        document_action_packet_ref=_safe_text(kwargs.get("document_action_packet_ref")),
        tool_use_packet_ref=_safe_text(kwargs.get("tool_use_packet_ref")),
        validation_packet_ref=_safe_text(kwargs.get("validation_packet_ref")),
        patch_feedback_packet_ref=_safe_text(kwargs.get("patch_feedback_packet_ref")),
        artifact_provenance_ref=_safe_text(kwargs.get("artifact_provenance_ref")),
        action_class=classify_action_authority_request_v1(
            action_class=kwargs.get("action_class"),
            action_summary=kwargs.get("action_summary"),
            requested_scope=kwargs.get("requested_scope"),
            safe_metadata=kwargs.get("safe_metadata"),
        ),
        action_summary=_safe_text(kwargs.get("action_summary")),
        action_risk_level=_safe_text(kwargs.get("action_risk_level", "none_metadata_only")),
        approval_authority_class=_safe_text(kwargs.get("approval_authority_class", "unknown_approval_authority")),
        authority_status=_safe_text(kwargs.get("authority_status", "proposal_only")),
        requested_scope=_safe_text(kwargs.get("requested_scope", "proposal_only")),
        approved_scope=_safe_text(kwargs.get("approved_scope", "none")),
        scope_limit_summary=_safe_text(kwargs.get("scope_limit_summary", "proposal-only")),
        preflight_required=_safe_bool(kwargs.get("preflight_required", False)),
        preflight_status=_safe_text(kwargs.get("preflight_status", "unknown")),
        owner_approval_required=_safe_bool(kwargs.get("owner_approval_required", False)),
        operator_approval_required=_safe_bool(kwargs.get("operator_approval_required", False)),
        explicit_confirmation_required=_safe_bool(kwargs.get("explicit_confirmation_required", False)),
        rollback_required=_safe_bool(kwargs.get("rollback_required", False)),
        rollback_plan_ref=_safe_text(kwargs.get("rollback_plan_ref")),
        audit_log_required=_safe_bool(kwargs.get("audit_log_required", True)),
        dry_run_required=_safe_bool(kwargs.get("dry_run_required", False)),
        validation_required=_safe_bool(kwargs.get("validation_required", False)),
        secret_risk_status=_safe_text(kwargs.get("secret_risk_status", "clear")),
        path_risk_status=_safe_text(kwargs.get("path_risk_status", "clear")),
        network_policy_status=_safe_text(kwargs.get("network_policy_status", "clear")),
        privacy_status=_safe_text(kwargs.get("privacy_status", "clear")),
        poison_status=_safe_text(kwargs.get("poison_status", "clear")),
        public_effect_possible=_safe_bool(kwargs.get("public_effect_possible", False)),
        external_side_effect_possible=_safe_bool(kwargs.get("external_side_effect_possible", False)),
        financial_effect_possible=_safe_bool(kwargs.get("financial_effect_possible", False)),
        physical_effect_possible=_safe_bool(kwargs.get("physical_effect_possible", False)),
        irreversible_effect_possible=_safe_bool(kwargs.get("irreversible_effect_possible", False)),
        execution_allowed=_safe_bool(kwargs.get("execution_allowed", False)),
        tool_execution_allowed=_safe_bool(kwargs.get("tool_execution_allowed", False)),
        write_allowed=_safe_bool(kwargs.get("write_allowed", False)),
        send_allowed=_safe_bool(kwargs.get("send_allowed", False)),
        calendar_change_allowed=_safe_bool(kwargs.get("calendar_change_allowed", False)),
        device_control_allowed=_safe_bool(kwargs.get("device_control_allowed", False)),
        deployment_allowed=_safe_bool(kwargs.get("deployment_allowed", False)),
        public_post_allowed=_safe_bool(kwargs.get("public_post_allowed", False)),
        payment_allowed=_safe_bool(kwargs.get("payment_allowed", False)),
        memory_write_allowed=_safe_bool(kwargs.get("memory_write_allowed", False)),
        commit_allowed=_safe_bool(kwargs.get("commit_allowed", False)),
        push_allowed=_safe_bool(kwargs.get("push_allowed", False)),
        recommended_next_check=_safe_text(kwargs.get("recommended_next_check", "inspect_authority_metadata_only")),
        runtime_authority=_safe_bool(kwargs.get("runtime_authority", False)),
        writes_state=_safe_bool(kwargs.get("writes_state", False)),
        model_provider_used=_safe_bool(kwargs.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(kwargs.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(kwargs.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(kwargs.get("learning_claimed", False)),
        safe_metadata=_safe_mapping(kwargs.get("safe_metadata")),
    )
    packet = evaluate_action_risk_v1(packet)
    packet = replace(packet, authority_status=select_action_authority_status_v1(packet))
    return packet


def build_initial_action_authority_examples_v1() -> list[ActionAuthorityPacket]:
    examples: list[ActionAuthorityPacket] = []

    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="summary_only_metadata_v1",
        action_request_ref="request_summary_only_v1",
        source_proposal_ref="proposal_summary_only_v1",
        action_class="no_action_summary_only",
        action_summary="Summary-only action needs no approval but grants no execution.",
        approval_authority_class="no_approval_needed_metadata_only",
        authority_status="not_requested",
        requested_scope="metadata_only",
        approved_scope="metadata_only",
        scope_limit_summary="summary only; no execution",
        safe_metadata={"example_name": "summary_only_metadata"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="read_only_requires_scope_v1",
        action_request_ref="request_read_only_v1",
        source_proposal_ref="proposal_read_only_v1",
        action_class="read_only_inspection",
        action_summary="Read-only inspection requires explicit read scope.",
        approval_authority_class="owner_approval_required",
        authority_status="approved_for_read_only",
        requested_scope="read_only",
        approved_scope="read_only",
        scope_limit_summary="read-only scope only",
        owner_approval_required=True,
        safe_metadata={"example_name": "read_only_requires_scope"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="file_write_sandbox_rollback_v1",
        action_request_ref="request_file_write_v1",
        source_proposal_ref="proposal_file_write_v1",
        document_action_packet_ref="document_action_file_write_v1",
        validation_packet_ref="validation_file_write_v1",
        rollback_plan_ref="rollback_file_write_v1",
        action_class="file_write",
        action_summary="File write requires sandbox/write boundary and rollback.",
        approval_authority_class="owner_approval_required",
        authority_status="approved_for_sandbox_only",
        requested_scope="sandbox_write_boundary",
        approved_scope="sandbox_only",
        scope_limit_summary="sandbox write only with rollback",
        rollback_required=True,
        owner_approval_required=True,
        validation_required=False,
        safe_metadata={"example_name": "file_write_sandbox_rollback"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="patch_apply_validation_feedback_v1",
        action_request_ref="request_patch_apply_v1",
        source_proposal_ref="proposal_patch_apply_v1",
        document_action_packet_ref="document_action_patch_v1",
        tool_use_packet_ref="tool_use_patch_v1",
        validation_packet_ref="validation_patch_v1",
        patch_feedback_packet_ref="patch_feedback_patch_v1",
        rollback_plan_ref="rollback_patch_v1",
        action_class="patch_apply",
        action_summary="Patch apply requires validation, patch feedback, rollback, and approval.",
        approval_authority_class="dual_owner_operator_approval_required",
        authority_status="approval_pending",
        requested_scope="validation_and_patch_feedback",
        approved_scope="none",
        scope_limit_summary="validation plus patch feedback with rollback",
        preflight_required=True,
        rollback_required=True,
        validation_required=True,
        owner_approval_required=True,
        operator_approval_required=True,
        dry_run_required=True,
        safe_metadata={"example_name": "patch_apply_validation_feedback"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="email_send_confirmation_blocked_v1",
        action_request_ref="request_email_send_v1",
        source_proposal_ref="proposal_email_send_v1",
        action_class="email_or_message_send",
        action_summary="Email send requires explicit confirmation and remains blocked.",
        approval_authority_class="explicit_user_confirmation_required",
        authority_status="blocked_by_missing_approval",
        requested_scope="single_confirmation",
        approved_scope="none",
        scope_limit_summary="explicit confirmation required",
        explicit_confirmation_required=True,
        external_side_effect_possible=True,
        dry_run_required=True,
        safe_metadata={"example_name": "email_send_confirmation_blocked"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="calendar_change_approval_blocked_v1",
        action_request_ref="request_calendar_change_v1",
        source_proposal_ref="proposal_calendar_change_v1",
        action_class="calendar_change",
        action_summary="Calendar change requires approval and remains blocked.",
        approval_authority_class="owner_approval_required",
        authority_status="blocked_by_missing_approval",
        requested_scope="calendar_boundary",
        approved_scope="none",
        scope_limit_summary="calendar approval required",
        external_side_effect_possible=True,
        owner_approval_required=True,
        safe_metadata={"example_name": "calendar_change_approval_blocked"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="device_control_safety_review_blocked_v1",
        action_request_ref="request_device_control_v1",
        source_proposal_ref="proposal_device_control_v1",
        action_class="device_control",
        action_summary="Device control requires device safety review and remains blocked.",
        approval_authority_class="device_safety_review_required",
        authority_status="blocked_by_missing_approval",
        requested_scope="device_safety_boundary",
        approved_scope="none",
        scope_limit_summary="device safety review required",
        external_side_effect_possible=True,
        physical_effect_possible=True,
        safe_metadata={"example_name": "device_control_safety_review_blocked"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="deployment_validation_rollback_owner_operator_v1",
        action_request_ref="request_deployment_v1",
        source_proposal_ref="proposal_deployment_v1",
        document_action_packet_ref="document_action_deployment_v1",
        validation_packet_ref="validation_deployment_v1",
        rollback_plan_ref="rollback_deployment_v1",
        action_class="deployment",
        action_summary="Deployment requires validation, rollback, and owner/operator approval.",
        approval_authority_class="dual_owner_operator_approval_required",
        authority_status="approval_pending",
        requested_scope="deployment_boundary",
        approved_scope="none",
        scope_limit_summary="deployment approval and rollback required",
        rollback_required=True,
        validation_required=True,
        owner_approval_required=True,
        operator_approval_required=True,
        explicit_confirmation_required=True,
        external_side_effect_possible=True,
        irreversible_effect_possible=True,
        safe_metadata={"example_name": "deployment_validation_rollback_owner_operator"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="public_post_public_review_v1",
        action_request_ref="request_public_post_v1",
        source_proposal_ref="proposal_public_post_v1",
        action_class="public_post",
        action_summary="Public post requires public-effect review.",
        approval_authority_class="public_claim_review_required",
        authority_status="blocked_by_public_effect",
        requested_scope="public_review_boundary",
        approved_scope="none",
        scope_limit_summary="public review required",
        rollback_required=True,
        rollback_plan_ref="rollback_public_post_v1",
        explicit_confirmation_required=True,
        public_effect_possible=True,
        irreversible_effect_possible=False,
        safe_metadata={"example_name": "public_post_public_review"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="payment_review_blocked_v1",
        action_request_ref="request_payment_v1",
        source_proposal_ref="proposal_payment_v1",
        action_class="payment_or_billing",
        action_summary="Payment action requires payment review and remains blocked.",
        approval_authority_class="payment_review_required",
        authority_status="blocked_by_missing_approval",
        requested_scope="payment_review_boundary",
        approved_scope="none",
        scope_limit_summary="payment review required",
        rollback_required=True,
        rollback_plan_ref="rollback_payment_v1",
        explicit_confirmation_required=True,
        financial_effect_possible=True,
        external_side_effect_possible=True,
        irreversible_effect_possible=False,
        safe_metadata={"example_name": "payment_review_blocked"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="git_commit_push_explicit_authority_v1",
        action_request_ref="request_git_commit_push_v1",
        source_proposal_ref="proposal_git_commit_push_v1",
        action_class="git_commit",
        action_summary="Git commit and push require explicit source-control authority.",
        approval_authority_class="owner_approval_required",
        authority_status="blocked_by_missing_approval",
        requested_scope="source_control_authority",
        approved_scope="none",
        scope_limit_summary="source control authority required",
        rollback_required=True,
        rollback_plan_ref="rollback_git_commit_v1",
        validation_required=True,
        validation_packet_ref="validation_git_commit_v1",
        safe_metadata={"example_name": "git_commit_push_explicit_authority"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="memory_write_boundary_v1",
        action_request_ref="request_memory_write_v1",
        source_proposal_ref="proposal_memory_write_v1",
        action_class="memory_write",
        action_summary="Memory write requires memory write boundary.",
        approval_authority_class="owner_approval_required",
        authority_status="blocked_by_missing_approval",
        requested_scope="memory_boundary",
        approved_scope="none",
        scope_limit_summary="memory boundary required",
        external_side_effect_possible=True,
        safe_metadata={"example_name": "memory_write_boundary"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="poisoned_source_blocked_v1",
        action_request_ref="request_poisoned_source_v1",
        source_proposal_ref="proposal_poisoned_source_v1",
        action_class="external_api_mutation",
        action_summary="Poisoned source action remains blocked.",
        approval_authority_class="blocked_no_authority",
        authority_status="blocked_by_policy",
        requested_scope="operator_review",
        approved_scope="none",
        scope_limit_summary="poisoned source blocked",
        poison_status="poisoned",
        external_side_effect_possible=True,
        safe_metadata={"example_name": "poisoned_source_blocked"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="validation_pass_alone_no_authority_v1",
        action_request_ref="request_validation_pass_v1",
        source_proposal_ref="proposal_validation_pass_v1",
        validation_packet_ref="validation_pass_v1",
        action_class="patch_apply",
        action_summary="Validation pass alone does not grant action.",
        approval_authority_class="dual_owner_operator_approval_required",
        authority_status="approval_pending",
        requested_scope="validation_only",
        approved_scope="none",
        scope_limit_summary="validation alone is not authority",
        validation_required=True,
        rollback_required=True,
        rollback_plan_ref="rollback_validation_pass_v1",
        safe_metadata={"example_name": "validation_pass_alone_no_authority"},
    ))
    examples.append(build_action_authority_packet_v1(
        action_authority_packet_id="owner_approval_one_action_only_v1",
        action_request_ref="request_owner_approval_v1",
        source_proposal_ref="proposal_owner_approval_v1",
        action_class="file_write",
        action_summary="Owner approval stays scoped to one action only.",
        approval_authority_class="owner_approval_required",
        authority_status="approved_for_single_action",
        requested_scope="single_action_only",
        approved_scope="single_action_only",
        scope_limit_summary="approval scoped to one action only",
        rollback_required=True,
        rollback_plan_ref="rollback_owner_approval_v1",
        owner_approval_required=True,
        safe_metadata={"example_name": "owner_approval_one_action_only"},
    ))

    return examples
