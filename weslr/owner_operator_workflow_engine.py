"""Metadata-only owner/operator workflow engine v1.

This module classifies owner/operator workflow review metadata into bounded
in-memory packets. It is deterministic, import-safe, pure in-memory, and
fail-closed.

No subprocess. No shell execution. No file I/O. No model/provider/API calls.
No runtime wiring. No `.weslr` access. No action execution, tool execution,
patch application, commit/push authority, public claims, proof claims, or
learning claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Mapping

HELPER_TYPE_V1 = "owner_operator_workflow_engine_v1"
PACKET_TYPE_V1 = "owner_operator_workflow_packet_v1"
SUMMARY_TYPE_V1 = "owner_operator_workflow_summary_v1"

ALLOWED_WORKFLOW_REQUEST_CLASSES_V1 = {
    "metadata_review_request",
    "owner_approval_request",
    "operator_review_request",
    "dual_owner_operator_review_request",
    "clarification_request",
    "preflight_review_request",
    "validation_review_request",
    "patch_proposal_review_request",
    "rollback_plan_review_request",
    "artifact_export_review_request",
    "deployment_review_request",
    "public_post_review_request",
    "payment_review_request",
    "device_safety_review_request",
    "memory_write_review_request",
    "access_permission_review_request",
    "unknown_workflow_request",
}

ALLOWED_OWNER_OPERATOR_DECISION_CLASSES_V1 = {
    "no_decision_metadata_only",
    "approve_metadata_only",
    "approve_read_only",
    "approve_dry_run",
    "approve_sandbox_write",
    "approve_single_action",
    "approve_with_constraints",
    "request_changes",
    "request_clarification",
    "reject",
    "defer_to_owner",
    "defer_to_operator",
    "defer_to_legal_review",
    "defer_to_security_review",
    "defer_to_payment_review",
    "defer_to_device_safety_review",
    "blocked_no_authority",
    "unknown_decision",
}

ALLOWED_WORKFLOW_SCOPE_CLASSES_V1 = {
    "metadata_only_scope",
    "read_only_scope",
    "dry_run_scope",
    "sandbox_write_scope",
    "single_action_scope",
    "time_limited_scope",
    "bounded_batch_scope",
    "public_effect_scope_requires_review",
    "financial_effect_scope_requires_review",
    "physical_effect_scope_requires_review",
    "broad_runtime_scope_blocked",
    "unknown_scope",
}

ALLOWED_WORKFLOW_STATUSES_V1 = {
    "not_started",
    "candidate_created",
    "awaiting_owner_review",
    "awaiting_operator_review",
    "awaiting_dual_review",
    "clarification_required",
    "preflight_required",
    "validation_required",
    "rollback_required",
    "approved_for_metadata_only",
    "approved_for_read_only",
    "approved_for_dry_run",
    "approved_for_sandbox_only",
    "approved_for_single_action_metadata_only",
    "rejected",
    "blocked_by_policy",
    "blocked_by_missing_authority",
    "blocked_by_missing_scope",
    "blocked_by_missing_rollback",
    "blocked_by_secret_or_path_risk",
    "blocked_by_unknown_risk",
    "unknown_status",
}

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
    "legal compliance",
    "security certification",
    "certification",
    "production ready",
    "public-ready",
    "public ready",
)

SELF_AUTHORIZE_PHRASES_V1 = (
    "self-authorize",
    "self authorize",
    "authorize this action",
    "grant approval",
    "grant yourself",
    "approve this action",
)

RISK_BLOCK_VALUES_V1 = {"blocked", "poisoned", "unknown", "mismatch", "risky"}
CLEAR_VALUES_V1 = {"clear", "none", "false", "safe", "metadata_only"}

class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OwnerOperatorWorkflowPacket:
    workflow_packet_id: str
    workflow_request_class: str
    request_summary: str
    requester_role: str
    source_request_ref: str
    document_action_packet_ref: str
    tool_use_packet_ref: str
    action_authority_packet_ref: str
    rollback_packet_ref: str
    validation_packet_ref: str
    patch_feedback_packet_ref: str
    artifact_provenance_ref: str
    workflow_status: str
    decision_class: str
    approval_scope_class: str
    approval_scope_summary: str
    scope_limit_summary: str
    constraints: dict[str, Any]
    single_action_only: bool
    time_limited: bool
    expires_after_action: bool
    owner_review_required: bool
    operator_review_required: bool
    dual_review_required: bool
    explicit_confirmation_required: bool
    legal_review_required: bool
    security_review_required: bool
    payment_review_required: bool
    device_safety_review_required: bool
    public_claim_review_required: bool
    preflight_required: bool
    preflight_status: str
    validation_required: bool
    rollback_required: bool
    rollback_plan_ref: str
    audit_log_required: bool
    approval_metadata_recorded: bool
    approval_grants_runtime_authority: bool
    approval_grants_execution_authority: bool
    approval_grants_broad_future_authority: bool
    external_side_effect_possible: bool
    public_effect_possible: bool
    financial_effect_possible: bool
    physical_effect_possible: bool
    irreversible_effect_possible: bool
    secret_risk_status: str
    path_risk_status: str
    privacy_status: str
    poison_status: str
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
class OwnerOperatorWorkflowSummary:
    summary_type: str
    workflow_packet_id: str
    workflow_request_class: str
    workflow_status: str
    decision_class: str
    approval_scope_class: str
    approval_scope_summary: str
    scope_limit_summary: str
    owner_review_required: bool
    operator_review_required: bool
    dual_review_required: bool
    validation_required: bool
    rollback_required: bool
    public_claim_review_required: bool
    payment_review_required: bool
    device_safety_review_required: bool
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
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    learning_claimed: bool
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


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _safe_metadata_dict(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return { _safe_text(key): to_owner_operator_workflow_json_safe_v1(item) for key, item in value.items() }
    return {"value": to_owner_operator_workflow_json_safe_v1(value)}


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
        return any(_contains_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_claim_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _contains_self_authorize_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_self_authorize_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_self_authorize_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in SELF_AUTHORIZE_PHRASES_V1)


def _contains_risk_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for item in value.values():
            if _contains_risk_marker(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_risk_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(marker in blob for marker in ("secret", "private", "raw", "poison", "toxic", "hidden prompt"))


def _packet_like(value: Any) -> OwnerOperatorWorkflowPacket:
    if isinstance(value, OwnerOperatorWorkflowPacket):
        return value
    if is_dataclass(value):
        value = asdict(value)
    if not isinstance(value, Mapping):
        raise TypeError("workflow packet must be mapping-like")
    safe_metadata = value.get("safe_metadata")
    return OwnerOperatorWorkflowPacket(
        workflow_packet_id=_safe_text(value.get("workflow_packet_id")),
        workflow_request_class=_safe_text(value.get("workflow_request_class")),
        request_summary=_safe_text(value.get("request_summary")),
        requester_role=_safe_text(value.get("requester_role")),
        source_request_ref=_safe_text(value.get("source_request_ref")),
        document_action_packet_ref=_safe_text(value.get("document_action_packet_ref")),
        tool_use_packet_ref=_safe_text(value.get("tool_use_packet_ref")),
        action_authority_packet_ref=_safe_text(value.get("action_authority_packet_ref")),
        rollback_packet_ref=_safe_text(value.get("rollback_packet_ref")),
        validation_packet_ref=_safe_text(value.get("validation_packet_ref")),
        patch_feedback_packet_ref=_safe_text(value.get("patch_feedback_packet_ref")),
        artifact_provenance_ref=_safe_text(value.get("artifact_provenance_ref")),
        workflow_status=_safe_text(value.get("workflow_status", "candidate_created")),
        decision_class=_safe_text(value.get("decision_class", "no_decision_metadata_only")),
        approval_scope_class=_safe_text(value.get("approval_scope_class", "metadata_only_scope")),
        approval_scope_summary=_safe_text(value.get("approval_scope_summary", "metadata-only scope; no execution")),
        scope_limit_summary=_safe_text(value.get("scope_limit_summary", "bounded metadata-only review")),
        constraints=to_owner_operator_workflow_json_safe_v1(value.get("constraints") or {}),
        single_action_only=_safe_bool(value.get("single_action_only", False)),
        time_limited=_safe_bool(value.get("time_limited", False)),
        expires_after_action=_safe_bool(value.get("expires_after_action", False)),
        owner_review_required=_safe_bool(value.get("owner_review_required", False)),
        operator_review_required=_safe_bool(value.get("operator_review_required", False)),
        dual_review_required=_safe_bool(value.get("dual_review_required", False)),
        explicit_confirmation_required=_safe_bool(value.get("explicit_confirmation_required", False)),
        legal_review_required=_safe_bool(value.get("legal_review_required", False)),
        security_review_required=_safe_bool(value.get("security_review_required", False)),
        payment_review_required=_safe_bool(value.get("payment_review_required", False)),
        device_safety_review_required=_safe_bool(value.get("device_safety_review_required", False)),
        public_claim_review_required=_safe_bool(value.get("public_claim_review_required", False)),
        preflight_required=_safe_bool(value.get("preflight_required", False)),
        preflight_status=_safe_text(value.get("preflight_status", "not_started")),
        validation_required=_safe_bool(value.get("validation_required", False)),
        rollback_required=_safe_bool(value.get("rollback_required", False)),
        rollback_plan_ref=_safe_text(value.get("rollback_plan_ref", "")),
        audit_log_required=_safe_bool(value.get("audit_log_required", True)),
        approval_metadata_recorded=_safe_bool(value.get("approval_metadata_recorded", True)),
        approval_grants_runtime_authority=_safe_bool(value.get("approval_grants_runtime_authority", False)),
        approval_grants_execution_authority=_safe_bool(value.get("approval_grants_execution_authority", False)),
        approval_grants_broad_future_authority=_safe_bool(value.get("approval_grants_broad_future_authority", False)),
        external_side_effect_possible=_safe_bool(value.get("external_side_effect_possible", False)),
        public_effect_possible=_safe_bool(value.get("public_effect_possible", False)),
        financial_effect_possible=_safe_bool(value.get("financial_effect_possible", False)),
        physical_effect_possible=_safe_bool(value.get("physical_effect_possible", False)),
        irreversible_effect_possible=_safe_bool(value.get("irreversible_effect_possible", False)),
        secret_risk_status=_safe_text(value.get("secret_risk_status", "clear")),
        path_risk_status=_safe_text(value.get("path_risk_status", "clear")),
        privacy_status=_safe_text(value.get("privacy_status", "clear")),
        poison_status=_safe_text(value.get("poison_status", "clear")),
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
        recommended_next_check=_safe_text(value.get("recommended_next_check", "inspect_workflow_metadata_only")),
        runtime_authority=_safe_bool(value.get("runtime_authority", False)),
        writes_state=_safe_bool(value.get("writes_state", False)),
        model_provider_used=_safe_bool(value.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(value.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(value.get("learning_claimed", False)),
        safe_metadata=_safe_metadata_dict(safe_metadata),
    )


def to_owner_operator_workflow_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return { _safe_text(key): to_owner_operator_workflow_json_safe_v1(item) for key, item in sorted(value.items(), key=lambda item: _safe_text(item[0])) }
    if isinstance(value, tuple):
        return [to_owner_operator_workflow_json_safe_v1(item) for item in value]
    if isinstance(value, list):
        return [to_owner_operator_workflow_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        items = [to_owner_operator_workflow_json_safe_v1(item) for item in value]
        return sorted(items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_owner_operator_workflow_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_owner_operator_workflow_json_safe_v1(vars(value))
    return _safe_text(value)


def classify_workflow_request_v1(**kwargs: Any) -> str:
    explicit = _safe_text(kwargs.get("workflow_request_class") or kwargs.get("request_class"))
    if explicit:
        if explicit in ALLOWED_WORKFLOW_REQUEST_CLASSES_V1:
            return explicit
        return "unknown_workflow_request"

    text = " ".join(
        _safe_text(kwargs.get(name))
        for name in (
            "request_summary",
            "requester_role",
            "source_request_ref",
            "document_action_packet_ref",
            "tool_use_packet_ref",
            "action_authority_packet_ref",
            "rollback_packet_ref",
            "validation_packet_ref",
            "patch_feedback_packet_ref",
            "artifact_provenance_ref",
        )
    ).lower()

    if any(hint in text for hint in ("clarification", "clarify", "needs clarification", "need clarification")):
        return "clarification_request"
    if any(hint in text for hint in ("dual", "owner/operator", "owner operator", "both roles")):
        return "dual_owner_operator_review_request"
    if any(hint in text for hint in ("owner approval", "owner review")):
        return "owner_approval_request"
    if any(hint in text for hint in ("operator review", "operator approval")):
        return "operator_review_request"
    if any(hint in text for hint in ("validation", "validate")):
        return "validation_review_request"
    if any(hint in text for hint in ("preflight", "pre-flight")):
        return "preflight_review_request"
    if any(hint in text for hint in ("patch proposal", "patch feedback", "patch")):
        return "patch_proposal_review_request"
    if any(hint in text for hint in ("rollback", "reversal")):
        return "rollback_plan_review_request"
    if any(hint in text for hint in ("artifact export", "export artifact", "export")):
        return "artifact_export_review_request"
    if any(hint in text for hint in ("deployment", "deploy")):
        return "deployment_review_request"
    if any(hint in text for hint in ("public post", "public claim", "publish", "post")):
        return "public_post_review_request"
    if any(hint in text for hint in ("payment", "billing")):
        return "payment_review_request"
    if any(hint in text for hint in ("device safety", "device control", "device")):
        return "device_safety_review_request"
    if any(hint in text for hint in ("memory write", "memory boundary", "memory")):
        return "memory_write_review_request"
    if any(hint in text for hint in ("permission", "access", "account")):
        return "access_permission_review_request"
    if any(hint in text for hint in ("summary only", "metadata only", "metadata_review")):
        return "metadata_review_request"
    return "unknown_workflow_request"


def classify_owner_operator_decision_v1(**kwargs: Any) -> str:
    explicit = _safe_text(kwargs.get("decision_class") or kwargs.get("decision"))
    if explicit in ALLOWED_OWNER_OPERATOR_DECISION_CLASSES_V1:
        return explicit

    text = " ".join(
        _safe_text(kwargs.get(name))
        for name in (
            "decision_summary",
            "request_summary",
            "approval_scope_summary",
            "scope_limit_summary",
            "constraints",
        )
    ).lower()

    if any(hint in text for hint in ("request changes", "needs changes")):
        return "request_changes"
    if any(hint in text for hint in ("clarification", "need more context", "needs clarification")):
        return "request_clarification"
    if any(hint in text for hint in ("defer to owner", "owner decides")):
        return "defer_to_owner"
    if any(hint in text for hint in ("defer to operator", "operator decides")):
        return "defer_to_operator"
    if any(hint in text for hint in ("legal", "lawyer", "compliance")):
        return "defer_to_legal_review"
    if any(hint in text for hint in ("security", "risk review")):
        return "defer_to_security_review"
    if any(hint in text for hint in ("payment", "billing")):
        return "defer_to_payment_review"
    if any(hint in text for hint in ("device safety", "device")):
        return "defer_to_device_safety_review"
    if any(hint in text for hint in ("approve metadata only", "metadata only")):
        return "approve_metadata_only"
    if any(hint in text for hint in ("approve read only", "read only")):
        return "approve_read_only"
    if any(hint in text for hint in ("dry run", "dry-run")):
        return "approve_dry_run"
    if any(hint in text for hint in ("sandbox" ,)):
        return "approve_sandbox_write"
    if any(hint in text for hint in ("single action",)):
        return "approve_single_action"
    if any(hint in text for hint in ("constraints", "bounded")):
        return "approve_with_constraints"
    if any(hint in text for hint in ("reject", "blocked")):
        return "reject"
    return "unknown_decision"


def _approval_statuses() -> set[str]:
    return {
        "approved_for_metadata_only",
        "approved_for_read_only",
        "approved_for_dry_run",
        "approved_for_sandbox_only",
        "approved_for_single_action_metadata_only",
    }


def _active_review_statuses() -> set[str]:
    return {
        "candidate_created",
        "awaiting_owner_review",
        "awaiting_operator_review",
        "awaiting_dual_review",
        "clarification_required",
        "preflight_required",
        "validation_required",
        "rollback_required",
    }


def _blocked_statuses() -> set[str]:
    return {
        "rejected",
        "blocked_by_policy",
        "blocked_by_missing_authority",
        "blocked_by_missing_scope",
        "blocked_by_missing_rollback",
        "blocked_by_secret_or_path_risk",
        "blocked_by_unknown_risk",
    }


def _is_clear(value: str) -> bool:
    return _normalize_text(value) in CLEAR_VALUES_V1


def _is_risk(value: str) -> bool:
    normalized = _normalize_text(value)
    return bool(normalized) and normalized not in CLEAR_VALUES_V1


def _risk_present(packet: OwnerOperatorWorkflowPacket) -> bool:
    return any(
        _is_risk(value)
        for value in (
            packet.secret_risk_status,
            packet.path_risk_status,
            packet.privacy_status,
            packet.poison_status,
        )
    )


def _approval_progression_requested(packet: OwnerOperatorWorkflowPacket) -> bool:
    return (
        packet.decision_class in {
            "approve_metadata_only",
            "approve_read_only",
            "approve_dry_run",
            "approve_sandbox_write",
            "approve_single_action",
            "approve_with_constraints",
        }
        or packet.workflow_status in _approval_statuses()
        or packet.owner_review_required
        or packet.operator_review_required
        or packet.dual_review_required
        or packet.preflight_required
        or packet.validation_required
        or packet.rollback_required
    )


def validate_owner_operator_workflow_packet_v1(packet: Any) -> bool:
    pkt = _packet_like(packet)

    hidden = _contains_forbidden_field(pkt)
    if hidden:
        raise ValidationError(f"hidden_private_or_secret_like_fields_not_allowed:{hidden}")

    if pkt.workflow_request_class not in ALLOWED_WORKFLOW_REQUEST_CLASSES_V1:
        raise ValidationError("unknown_request_promoted_as_valid")
    if pkt.decision_class not in ALLOWED_OWNER_OPERATOR_DECISION_CLASSES_V1:
        raise ValidationError("unknown_decision_promoted_as_valid")
    if pkt.approval_scope_class not in ALLOWED_WORKFLOW_SCOPE_CLASSES_V1:
        raise ValidationError("unknown_scope_promoted_as_valid")
    if pkt.workflow_status not in ALLOWED_WORKFLOW_STATUSES_V1:
        raise ValidationError("unknown_status_promoted_as_valid")

    for field_name in (
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
    ):
        if getattr(pkt, field_name):
            raise ValidationError(f"{field_name}_must_be_false")

    if pkt.approval_scope_class == "broad_runtime_scope_blocked":
        raise ValidationError("broad_runtime_scope_blocked")

    if not pkt.approval_scope_summary.strip():
        raise ValidationError("approval_without_scope_summary")

    if pkt.decision_class == "approve_single_action" and not pkt.single_action_only:
        raise ValidationError("single_action_approval_requires_single_action_only")

    if pkt.rollback_required and (not pkt.rollback_packet_ref.strip() or not pkt.rollback_plan_ref.strip()):
        raise ValidationError("rollback_required_without_rollback_refs")

    if pkt.validation_required and not pkt.validation_packet_ref.strip():
        raise ValidationError("validation_required_without_validation_packet")

    if pkt.public_effect_possible and not pkt.public_claim_review_required:
        raise ValidationError("public_effect_without_public_review_requirement")

    if pkt.financial_effect_possible and not pkt.payment_review_required:
        raise ValidationError("financial_effect_without_payment_review_requirement")

    if (pkt.physical_effect_possible or pkt.device_control_allowed) and not pkt.device_safety_review_required:
        raise ValidationError("physical_or_device_effect_without_device_safety_review_requirement")

    if pkt.public_claim_allowed or pkt.proof_claim_allowed or pkt.learning_claimed:
        raise ValidationError("authority_or_claim_flags_must_be_false")

    if _contains_claim_marker(pkt.request_summary) or _contains_claim_marker(pkt.approval_scope_summary) or _contains_claim_marker(pkt.scope_limit_summary) or _contains_claim_marker(pkt.constraints) or _contains_claim_marker(pkt.safe_metadata):
        raise ValidationError("correctness_or_public_readiness_claims_not_allowed")

    if _contains_self_authorize_marker(pkt.request_summary) or _contains_self_authorize_marker(pkt.constraints) or _contains_self_authorize_marker(pkt.safe_metadata):
        raise ValidationError("document_or_model_output_self_authorizes_approval")

    if pkt.poison_status and not _is_clear(pkt.poison_status) and _approval_progression_requested(pkt):
        raise ValidationError("poisoned_source_blocks_approval_progression")

    if _risk_present(pkt) and _approval_progression_requested(pkt) and pkt.workflow_status not in _blocked_statuses():
        raise ValidationError("secret_or_path_risk_blocks_approval_progression")

    if any(
        _contains_risk_marker(getattr(pkt, field_name))
        for field_name in ("request_summary", "approval_scope_summary", "scope_limit_summary", "constraints")
    ) and pkt.workflow_status not in _blocked_statuses():
        raise ValidationError("secret_path_privacy_or_poison_risk_must_remain_visible")

    return True


def _next_status_for_request(packet: OwnerOperatorWorkflowPacket) -> str:
    if packet.workflow_request_class == "metadata_review_request":
        return "approved_for_metadata_only" if not _risk_present(packet) else "blocked_by_secret_or_path_risk"
    if packet.workflow_request_class == "owner_approval_request":
        return "awaiting_owner_review"
    if packet.workflow_request_class == "operator_review_request":
        return "awaiting_operator_review"
    if packet.workflow_request_class == "dual_owner_operator_review_request":
        return "awaiting_dual_review"
    if packet.workflow_request_class == "clarification_request":
        return "clarification_required"
    if packet.workflow_request_class == "preflight_review_request":
        return "preflight_required"
    if packet.workflow_request_class == "validation_review_request":
        return "validation_required"
    if packet.workflow_request_class == "patch_proposal_review_request":
        return "awaiting_operator_review"
    if packet.workflow_request_class == "rollback_plan_review_request":
        return "rollback_required"
    if packet.workflow_request_class == "artifact_export_review_request":
        return "awaiting_operator_review"
    if packet.workflow_request_class == "deployment_review_request":
        if not packet.validation_packet_ref.strip():
            return "validation_required"
        if not packet.rollback_packet_ref.strip() or not packet.rollback_plan_ref.strip():
            return "rollback_required"
        return "awaiting_dual_review"
    if packet.workflow_request_class == "public_post_review_request":
        return "awaiting_dual_review"
    if packet.workflow_request_class == "payment_review_request":
        return "blocked_by_missing_authority"
    if packet.workflow_request_class == "device_safety_review_request":
        return "blocked_by_missing_authority"
    if packet.workflow_request_class == "memory_write_review_request":
        return "blocked_by_missing_scope"
    if packet.workflow_request_class == "access_permission_review_request":
        return "awaiting_dual_review"
    return "blocked_by_unknown_risk"


def _next_check_for_status(status: str) -> str:
    mapping = {
        "not_started": "create_candidate_metadata",
        "candidate_created": "route_to_review_queue",
        "awaiting_owner_review": "route_to_owner_review",
        "awaiting_operator_review": "route_to_operator_review",
        "awaiting_dual_review": "route_to_dual_review",
        "clarification_required": "request_clarification",
        "preflight_required": "attach_preflight_metadata",
        "validation_required": "attach_validation_packet",
        "rollback_required": "attach_rollback_plan",
        "approved_for_metadata_only": "metadata_only_no_execution",
        "approved_for_read_only": "read_only_no_execution",
        "approved_for_dry_run": "dry_run_only_no_execution",
        "approved_for_sandbox_only": "sandbox_only_no_execution",
        "approved_for_single_action_metadata_only": "single_action_metadata_only",
        "rejected": "stop_and_report_rejection",
        "blocked_by_policy": "block_and_report_policy",
        "blocked_by_missing_authority": "block_and_request_authority",
        "blocked_by_missing_scope": "block_and_request_scope",
        "blocked_by_missing_rollback": "block_and_request_rollback",
        "blocked_by_secret_or_path_risk": "block_and_redact_risk",
        "blocked_by_unknown_risk": "block_and_report_unknown_risk",
        "unknown_status": "manual_review_required",
    }
    return mapping.get(status, "manual_review_required")


def evaluate_workflow_readiness_v1(packet: Any) -> OwnerOperatorWorkflowPacket:
    pkt = _packet_like(packet)

    request_class = classify_workflow_request_v1(workflow_request_class=pkt.workflow_request_class, request_summary=pkt.request_summary, requester_role=pkt.requester_role, source_request_ref=pkt.source_request_ref, document_action_packet_ref=pkt.document_action_packet_ref, tool_use_packet_ref=pkt.tool_use_packet_ref, action_authority_packet_ref=pkt.action_authority_packet_ref, rollback_packet_ref=pkt.rollback_packet_ref, validation_packet_ref=pkt.validation_packet_ref, patch_feedback_packet_ref=pkt.patch_feedback_packet_ref, artifact_provenance_ref=pkt.artifact_provenance_ref)
    decision_class = classify_owner_operator_decision_v1(decision_class=pkt.decision_class, decision_summary=pkt.approval_scope_summary, request_summary=pkt.request_summary, approval_scope_summary=pkt.approval_scope_summary, scope_limit_summary=pkt.scope_limit_summary, constraints=pkt.constraints)

    status = pkt.workflow_status
    if status in {"candidate_created", "not_started"}:
        status = _next_status_for_request(replace(pkt, workflow_request_class=request_class, decision_class=decision_class))

    scope_class = pkt.approval_scope_class if pkt.approval_scope_class in ALLOWED_WORKFLOW_SCOPE_CLASSES_V1 else "unknown_scope"
    if scope_class == "unknown_scope" and status not in _blocked_statuses():
        status = "blocked_by_unknown_risk"

    owner_review_required = pkt.owner_review_required or request_class in {"owner_approval_request", "dual_owner_operator_review_request", "deployment_review_request", "access_permission_review_request"}
    operator_review_required = pkt.operator_review_required or request_class in {"operator_review_request", "dual_owner_operator_review_request", "patch_proposal_review_request", "artifact_export_review_request", "public_post_review_request"}
    dual_review_required = pkt.dual_review_required or request_class in {"dual_owner_operator_review_request", "deployment_review_request", "public_post_review_request", "access_permission_review_request"}
    preflight_required = pkt.preflight_required or request_class in {"preflight_review_request", "deployment_review_request"}
    validation_required = pkt.validation_required or request_class in {"validation_review_request", "deployment_review_request"}
    rollback_required = pkt.rollback_required or request_class in {"rollback_plan_review_request", "deployment_review_request"}

    public_claim_review_required = pkt.public_claim_review_required or request_class == "public_post_review_request"
    payment_review_required = pkt.payment_review_required or request_class == "payment_review_request"
    device_safety_review_required = pkt.device_safety_review_required or request_class == "device_safety_review_request"
    legal_review_required = pkt.legal_review_required or request_class in {"deployment_review_request", "access_permission_review_request"}
    security_review_required = pkt.security_review_required or request_class in {"deployment_review_request", "access_permission_review_request"}

    approval_scope_summary = pkt.approval_scope_summary

    scope_limit_summary = pkt.scope_limit_summary

    recommended_next_check = _next_check_for_status(status)
    if request_class == "clarification_request":
        recommended_next_check = "request_clarification"
    if request_class == "payment_review_request":
        recommended_next_check = "defer_to_payment_review"
    if request_class == "device_safety_review_request":
        recommended_next_check = "defer_to_device_safety_review"
    if request_class == "deployment_review_request" and rollback_required and validation_required and dual_review_required:
        recommended_next_check = "route_to_dual_review_with_validation_and_rollback"

    approved_flag = status.startswith("approved_for_")
    if decision_class in {"reject", "request_changes", "request_clarification", "blocked_no_authority"}:
        approved_flag = False

    if _risk_present(pkt) and approved_flag:
        status = "blocked_by_secret_or_path_risk"
        recommended_next_check = "block_and_redact_risk"

    if pkt.poison_status and not _is_clear(pkt.poison_status) and approved_flag:
        status = "blocked_by_unknown_risk"
        recommended_next_check = "block_and_report_poisoned_source"

    if request_class == "unknown_workflow_request":
        status = "blocked_by_unknown_risk"
        recommended_next_check = "manual_review_required"

    if decision_class == "reject":
        status = "rejected"
        recommended_next_check = "stop_and_report_rejection"
    elif decision_class == "request_changes":
        status = "clarification_required"
        recommended_next_check = "request_changes_and_pause"
    elif decision_class == "request_clarification":
        status = "clarification_required"
        recommended_next_check = "request_clarification"
    elif decision_class == "defer_to_owner":
        status = "awaiting_owner_review"
    elif decision_class == "defer_to_operator":
        status = "awaiting_operator_review"
    elif decision_class in {"defer_to_legal_review", "defer_to_security_review", "defer_to_payment_review", "defer_to_device_safety_review"}:
        status = "awaiting_dual_review" if dual_review_required else "blocked_by_missing_authority"
    elif decision_class == "blocked_no_authority":
        status = "blocked_by_missing_authority"
    elif decision_class in {"approve_metadata_only", "approve_read_only", "approve_dry_run", "approve_sandbox_write", "approve_single_action", "approve_with_constraints"}:
        if pkt.approval_scope_class == "broad_runtime_scope_blocked":
            status = "blocked_by_missing_scope"
        elif request_class == "metadata_review_request":
            if decision_class == "approve_read_only":
                status = "approved_for_read_only"
            elif decision_class == "approve_dry_run":
                status = "approved_for_dry_run"
            elif decision_class == "approve_sandbox_write":
                status = "approved_for_sandbox_only"
            elif decision_class == "approve_single_action":
                status = "approved_for_single_action_metadata_only"
            else:
                status = "approved_for_metadata_only"

    if request_class == "payment_review_request":
        status = "blocked_by_missing_authority" if status not in _blocked_statuses() else status
    if request_class == "device_safety_review_request":
        status = "blocked_by_missing_authority" if status not in _blocked_statuses() else status
    if request_class == "memory_write_review_request":
        status = "blocked_by_missing_scope" if status not in _blocked_statuses() else status
    if request_class == "clarification_request":
        status = "clarification_required"
    if request_class == "validation_review_request" and validation_required and status in {"approved_for_metadata_only", "candidate_created"}:
        status = "validation_required"
    if request_class == "rollback_plan_review_request" and rollback_required and status in {"approved_for_metadata_only", "candidate_created"}:
        status = "rollback_required"

    approval_metadata_recorded = True

    pkt = replace(
        pkt,
        approval_scope_summary=approval_scope_summary,
        scope_limit_summary=scope_limit_summary,
        workflow_status=status,
        owner_review_required=owner_review_required,
        operator_review_required=operator_review_required,
        dual_review_required=dual_review_required,
        preflight_required=preflight_required,
        validation_required=validation_required,
        rollback_required=rollback_required,
        public_claim_review_required=public_claim_review_required,
        payment_review_required=payment_review_required,
        device_safety_review_required=device_safety_review_required,
        legal_review_required=legal_review_required,
        security_review_required=security_review_required,
        audit_log_required=True,
        approval_metadata_recorded=approval_metadata_recorded,
        recommended_next_check=recommended_next_check,
    )

    return pkt


def select_workflow_next_step_v1(packet: Any) -> str:
    pkt = _packet_like(packet)
    if pkt.decision_class == "request_changes":
        return "request_changes_and_pause"
    if pkt.decision_class == "request_clarification":
        return "request_clarification"
    return _next_check_for_status(pkt.workflow_status)


def summarize_owner_operator_workflow_packet_v1(packet: Any) -> OwnerOperatorWorkflowSummary:
    pkt = _packet_like(packet)
    return OwnerOperatorWorkflowSummary(
        summary_type=SUMMARY_TYPE_V1,
        workflow_packet_id=pkt.workflow_packet_id,
        workflow_request_class=pkt.workflow_request_class,
        workflow_status=pkt.workflow_status,
        decision_class=pkt.decision_class,
        approval_scope_class=pkt.approval_scope_class,
        approval_scope_summary=pkt.approval_scope_summary,
        scope_limit_summary=pkt.scope_limit_summary,
        owner_review_required=pkt.owner_review_required,
        operator_review_required=pkt.operator_review_required,
        dual_review_required=pkt.dual_review_required,
        validation_required=pkt.validation_required,
        rollback_required=pkt.rollback_required,
        public_claim_review_required=pkt.public_claim_review_required,
        payment_review_required=pkt.payment_review_required,
        device_safety_review_required=pkt.device_safety_review_required,
        execution_allowed=pkt.execution_allowed,
        tool_execution_allowed=pkt.tool_execution_allowed,
        write_allowed=pkt.write_allowed,
        send_allowed=pkt.send_allowed,
        calendar_change_allowed=pkt.calendar_change_allowed,
        device_control_allowed=pkt.device_control_allowed,
        deployment_allowed=pkt.deployment_allowed,
        public_post_allowed=pkt.public_post_allowed,
        payment_allowed=pkt.payment_allowed,
        memory_write_allowed=pkt.memory_write_allowed,
        commit_allowed=pkt.commit_allowed,
        push_allowed=pkt.push_allowed,
        runtime_authority=pkt.runtime_authority,
        writes_state=pkt.writes_state,
        model_provider_used=pkt.model_provider_used,
        public_claim_allowed=pkt.public_claim_allowed,
        proof_claim_allowed=pkt.proof_claim_allowed,
        learning_claimed=pkt.learning_claimed,
        recommended_next_check=pkt.recommended_next_check,
    )


def build_owner_operator_workflow_packet_v1(**kwargs: Any) -> OwnerOperatorWorkflowPacket:
    request_class = _safe_text(kwargs.get("workflow_request_class") or kwargs.get("request_class")) or classify_workflow_request_v1(**kwargs)
    decision_class = _safe_text(kwargs.get("decision_class") or kwargs.get("decision")) or classify_owner_operator_decision_v1(**kwargs)
    base = {
        "workflow_packet_id": kwargs.get("workflow_packet_id", "owner_operator_workflow_packet_v1"),
        "workflow_request_class": request_class,
        "request_summary": kwargs.get("request_summary", "Metadata-only owner/operator workflow candidate."),
        "requester_role": kwargs.get("requester_role", "unknown_role"),
        "source_request_ref": kwargs.get("source_request_ref", "source_request_v1"),
        "document_action_packet_ref": kwargs.get("document_action_packet_ref", ""),
        "tool_use_packet_ref": kwargs.get("tool_use_packet_ref", ""),
        "action_authority_packet_ref": kwargs.get("action_authority_packet_ref", ""),
        "rollback_packet_ref": kwargs.get("rollback_packet_ref", ""),
        "validation_packet_ref": kwargs.get("validation_packet_ref", ""),
        "patch_feedback_packet_ref": kwargs.get("patch_feedback_packet_ref", ""),
        "artifact_provenance_ref": kwargs.get("artifact_provenance_ref", ""),
        "workflow_status": kwargs.get("workflow_status", "candidate_created"),
        "decision_class": decision_class,
        "approval_scope_class": kwargs.get("approval_scope_class", "metadata_only_scope"),
        "approval_scope_summary": kwargs.get("approval_scope_summary", "metadata-only scope; no execution"),
        "scope_limit_summary": kwargs.get("scope_limit_summary", "bounded metadata-only review"),
        "constraints": to_owner_operator_workflow_json_safe_v1(kwargs.get("constraints") or {}),
        "single_action_only": kwargs.get("single_action_only", False),
        "time_limited": kwargs.get("time_limited", False),
        "expires_after_action": kwargs.get("expires_after_action", False),
        "owner_review_required": kwargs.get("owner_review_required", False),
        "operator_review_required": kwargs.get("operator_review_required", False),
        "dual_review_required": kwargs.get("dual_review_required", False),
        "explicit_confirmation_required": kwargs.get("explicit_confirmation_required", False),
        "legal_review_required": kwargs.get("legal_review_required", False),
        "security_review_required": kwargs.get("security_review_required", False),
        "payment_review_required": kwargs.get("payment_review_required", False),
        "device_safety_review_required": kwargs.get("device_safety_review_required", False),
        "public_claim_review_required": kwargs.get("public_claim_review_required", False),
        "preflight_required": kwargs.get("preflight_required", False),
        "preflight_status": kwargs.get("preflight_status", "not_started"),
        "validation_required": kwargs.get("validation_required", False),
        "rollback_required": kwargs.get("rollback_required", False),
        "rollback_plan_ref": kwargs.get("rollback_plan_ref", ""),
        "audit_log_required": kwargs.get("audit_log_required", True),
        "approval_metadata_recorded": kwargs.get("approval_metadata_recorded", True),
        "approval_grants_runtime_authority": kwargs.get("approval_grants_runtime_authority", False),
        "approval_grants_execution_authority": kwargs.get("approval_grants_execution_authority", False),
        "approval_grants_broad_future_authority": kwargs.get("approval_grants_broad_future_authority", False),
        "external_side_effect_possible": kwargs.get("external_side_effect_possible", False),
        "public_effect_possible": kwargs.get("public_effect_possible", False),
        "financial_effect_possible": kwargs.get("financial_effect_possible", False),
        "physical_effect_possible": kwargs.get("physical_effect_possible", False),
        "irreversible_effect_possible": kwargs.get("irreversible_effect_possible", False),
        "secret_risk_status": kwargs.get("secret_risk_status", "clear"),
        "path_risk_status": kwargs.get("path_risk_status", "clear"),
        "privacy_status": kwargs.get("privacy_status", "clear"),
        "poison_status": kwargs.get("poison_status", "clear"),
        "execution_allowed": kwargs.get("execution_allowed", False),
        "tool_execution_allowed": kwargs.get("tool_execution_allowed", False),
        "write_allowed": kwargs.get("write_allowed", False),
        "send_allowed": kwargs.get("send_allowed", False),
        "calendar_change_allowed": kwargs.get("calendar_change_allowed", False),
        "device_control_allowed": kwargs.get("device_control_allowed", False),
        "deployment_allowed": kwargs.get("deployment_allowed", False),
        "public_post_allowed": kwargs.get("public_post_allowed", False),
        "payment_allowed": kwargs.get("payment_allowed", False),
        "memory_write_allowed": kwargs.get("memory_write_allowed", False),
        "commit_allowed": kwargs.get("commit_allowed", False),
        "push_allowed": kwargs.get("push_allowed", False),
        "recommended_next_check": kwargs.get("recommended_next_check", "inspect_workflow_metadata_only"),
        "runtime_authority": kwargs.get("runtime_authority", False),
        "writes_state": kwargs.get("writes_state", False),
        "model_provider_used": kwargs.get("model_provider_used", False),
        "public_claim_allowed": kwargs.get("public_claim_allowed", False),
        "proof_claim_allowed": kwargs.get("proof_claim_allowed", False),
        "learning_claimed": kwargs.get("learning_claimed", False),
        "safe_metadata": kwargs.get("safe_metadata"),
    }
    return evaluate_workflow_readiness_v1(OwnerOperatorWorkflowPacket(**base))


def build_initial_owner_operator_workflow_examples_v1() -> list[OwnerOperatorWorkflowPacket]:
    examples: list[OwnerOperatorWorkflowPacket] = [
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="metadata_review_stays_metadata_only_v1",
            workflow_request_class="metadata_review_request",
            request_summary="Metadata review stays metadata-only.",
            requester_role="reviewer",
            source_request_ref="source_metadata_review_v1",
            decision_class="approve_metadata_only",
            approval_scope_class="metadata_only_scope",
            approval_scope_summary="Metadata-only scope; no execution.",
            scope_limit_summary="No tools, writes, sends, or state changes.",
            recommended_next_check="metadata_only_no_execution",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="owner_approval_awaits_owner_review_v1",
            workflow_request_class="owner_approval_request",
            request_summary="Owner approval request.",
            requester_role="reviewer",
            source_request_ref="source_owner_review_v1",
            decision_class="defer_to_owner",
            owner_review_required=True,
            approval_scope_class="read_only_scope",
            approval_scope_summary="Owner review required before any action.",
            scope_limit_summary="Owner review only; no execution.",
            recommended_next_check="route_to_owner_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="operator_review_awaits_operator_review_v1",
            workflow_request_class="operator_review_request",
            request_summary="Operator review request.",
            requester_role="reviewer",
            source_request_ref="source_operator_review_v1",
            decision_class="defer_to_operator",
            operator_review_required=True,
            approval_scope_class="read_only_scope",
            approval_scope_summary="Operator review required before any action.",
            scope_limit_summary="Operator review only; no execution.",
            recommended_next_check="route_to_operator_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="dual_owner_operator_review_requires_both_roles_v1",
            workflow_request_class="dual_owner_operator_review_request",
            request_summary="Dual owner/operator review request.",
            requester_role="reviewer",
            source_request_ref="source_dual_review_v1",
            decision_class="approve_with_constraints",
            owner_review_required=True,
            operator_review_required=True,
            dual_review_required=True,
            approval_scope_class="bounded_batch_scope",
            approval_scope_summary="Both roles must review before proceeding.",
            scope_limit_summary="Bounded batch only; no broad authority.",
            recommended_next_check="route_to_dual_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="clarification_request_blocks_progression_v1",
            workflow_request_class="clarification_request",
            request_summary="Clarification is needed before review can continue.",
            requester_role="reviewer",
            source_request_ref="source_clarification_v1",
            decision_class="request_clarification",
            workflow_status="clarification_required",
            approval_scope_class="metadata_only_scope",
            approval_scope_summary="Clarification required; no approval.",
            scope_limit_summary="Pause until clarification arrives.",
            recommended_next_check="request_clarification",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="validation_review_requires_validation_packet_ref_v1",
            workflow_request_class="validation_review_request",
            request_summary="Validation review request.",
            requester_role="reviewer",
            source_request_ref="source_validation_v1",
            decision_class="defer_to_operator",
            validation_required=True,
            validation_packet_ref="validation_packet_v1",
            approval_scope_class="dry_run_scope",
            approval_scope_summary="Validation packet required; no execution.",
            scope_limit_summary="Validation only; no tools or writes.",
            recommended_next_check="attach_validation_packet",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="patch_proposal_review_links_patch_feedback_no_apply_v1",
            workflow_request_class="patch_proposal_review_request",
            request_summary="Patch proposal review.",
            requester_role="reviewer",
            source_request_ref="source_patch_proposal_v1",
            decision_class="defer_to_operator",
            patch_feedback_packet_ref="patch_feedback_packet_v1",
            tool_use_packet_ref="tool_use_packet_v1",
            approval_scope_class="sandbox_write_scope",
            approval_scope_summary="Patch feedback linked; patch not applied.",
            scope_limit_summary="No patch application; review metadata only.",
            recommended_next_check="route_to_operator_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="rollback_plan_review_requires_rollback_refs_v1",
            workflow_request_class="rollback_plan_review_request",
            request_summary="Rollback plan review.",
            requester_role="reviewer",
            source_request_ref="source_rollback_review_v1",
            decision_class="approve_with_constraints",
            rollback_required=True,
            rollback_packet_ref="rollback_packet_v1",
            rollback_plan_ref="rollback_plan_v1",
            approval_scope_class="metadata_only_scope",
            approval_scope_summary="Rollback packet and plan required; no rollback execution.",
            scope_limit_summary="Rollback metadata only.",
            recommended_next_check="attach_rollback_plan",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="artifact_export_review_requires_provenance_v1",
            workflow_request_class="artifact_export_review_request",
            request_summary="Artifact export review.",
            requester_role="reviewer",
            source_request_ref="source_artifact_export_v1",
            decision_class="defer_to_operator",
            artifact_provenance_ref="artifact_provenance_v1",
            approval_scope_class="metadata_only_scope",
            approval_scope_summary="Artifact provenance required; export not performed.",
            scope_limit_summary="Artifact provenance metadata only; no export.",
            recommended_next_check="route_to_operator_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="deployment_review_requires_validation_and_rollback_v1",
            workflow_request_class="deployment_review_request",
            request_summary="Deployment review requires validation, rollback, and owner/operator review.",
            requester_role="reviewer",
            source_request_ref="source_deployment_v1",
            decision_class="approve_with_constraints",
            owner_review_required=True,
            operator_review_required=True,
            dual_review_required=True,
            validation_required=True,
            validation_packet_ref="validation_packet_v1",
            rollback_required=True,
            rollback_packet_ref="rollback_packet_v1",
            rollback_plan_ref="rollback_plan_v1",
            legal_review_required=True,
            security_review_required=True,
            preflight_required=True,
            preflight_status="required",
            approval_scope_class="bounded_batch_scope",
            approval_scope_summary="Deployment review with validation and rollback; no deployment.",
            scope_limit_summary="Bounded deployment review only; no runtime authority.",
            recommended_next_check="route_to_dual_review_with_validation_and_rollback",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="public_post_review_requires_public_claim_review_v1",
            workflow_request_class="public_post_review_request",
            request_summary="Public post review requires public-effect/public-claim review.",
            requester_role="reviewer",
            source_request_ref="source_public_post_v1",
            decision_class="defer_to_legal_review",
            owner_review_required=True,
            operator_review_required=True,
            dual_review_required=True,
            public_effect_possible=True,
            public_claim_review_required=True,
            public_post_allowed=False,
            approval_scope_class="public_effect_scope_requires_review",
            approval_scope_summary="Public effect review required; no public posting.",
            scope_limit_summary="Public-claim review only; no public effect or post.",
            recommended_next_check="route_to_dual_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="payment_review_remains_blocked_v1",
            workflow_request_class="payment_review_request",
            request_summary="Payment review remains blocked.",
            requester_role="reviewer",
            source_request_ref="source_payment_v1",
            decision_class="defer_to_payment_review",
            financial_effect_possible=True,
            payment_review_required=True,
            payment_allowed=False,
            workflow_status="blocked_by_missing_authority",
            approval_scope_class="financial_effect_scope_requires_review",
            approval_scope_summary="Payment review required; no charge or billing action.",
            scope_limit_summary="Payment boundary only; remain blocked.",
            recommended_next_check="defer_to_payment_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="device_safety_review_remains_blocked_v1",
            workflow_request_class="device_safety_review_request",
            request_summary="Device safety review remains blocked.",
            requester_role="reviewer",
            source_request_ref="source_device_safety_v1",
            decision_class="defer_to_device_safety_review",
            physical_effect_possible=True,
            device_safety_review_required=True,
            device_control_allowed=False,
            workflow_status="blocked_by_missing_authority",
            approval_scope_class="physical_effect_scope_requires_review",
            approval_scope_summary="Device safety review required; no device control.",
            scope_limit_summary="Device safety boundary only; remain blocked.",
            recommended_next_check="defer_to_device_safety_review",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="memory_write_review_remains_blocked_v1",
            workflow_request_class="memory_write_review_request",
            request_summary="Memory write review remains blocked.",
            requester_role="reviewer",
            source_request_ref="source_memory_write_v1",
            decision_class="blocked_no_authority",
            memory_write_allowed=False,
            workflow_status="blocked_by_missing_scope",
            approval_scope_class="metadata_only_scope",
            approval_scope_summary="Memory boundary review required; no memory write.",
            scope_limit_summary="Memory boundary only; remain blocked.",
            recommended_next_check="block_and_request_scope",
        ),
        build_owner_operator_workflow_packet_v1(
            workflow_packet_id="broad_runtime_approval_blocked_v1",
            workflow_request_class="owner_approval_request",
            request_summary="Broad runtime approval should be blocked.",
            requester_role="reviewer",
            source_request_ref="source_broad_runtime_v1",
            decision_class="approve_single_action",
            approval_scope_class="broad_runtime_scope_blocked",
            approval_scope_summary="Broad runtime approval is blocked.",
            scope_limit_summary="No broad runtime authority; this should fail validation.",
            single_action_only=False,
            workflow_status="blocked_by_missing_scope",
            recommended_next_check="block_and_request_scope",
        ),
    ]
    return examples
