"""Metadata-only document-to-action boundary v1.

This module extracts action candidates from documents as bounded metadata.
It is deterministic, import-safe, pure in-memory, and fail-closed.
No subprocess. No shell execution. No file I/O. No model/provider/API calls.
No runtime wiring. No `.weslr` access. No action execution, tool execution,
patch application, commit/push authority, or public/proof/learning claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Mapping

HELPER_TYPE_V1 = "document_to_action_boundary_v1"
PACKET_TYPE_V1 = "document_action_packet_v1"
SUMMARY_TYPE_V1 = "document_action_summary_v1"

ALLOWED_SOURCE_DOCUMENT_CLASSES_V1 = {
    "owner_uploaded_document",
    "operator_internal_document",
    "project_internal_document",
    "workspace_shared_document",
    "public_source_document",
    "third_party_document",
    "retrieved_web_document",
    "email_like_message",
    "legal_or_policy_document",
    "technical_specification",
    "code_or_patch_document",
    "calendar_or_schedule_document",
    "invoice_or_payment_document",
    "device_instruction_document",
    "unknown_document_source",
}

ALLOWED_EXTRACTED_ACTION_CLASSES_V1 = {
    "clarification_request",
    "information_summary",
    "task_proposal",
    "file_write_proposal",
    "patch_proposal",
    "test_run_proposal",
    "shell_command_proposal",
    "api_call_proposal",
    "email_or_message_proposal",
    "calendar_event_proposal",
    "device_control_proposal",
    "deployment_proposal",
    "payment_or_billing_proposal",
    "public_posting_proposal",
    "memory_write_proposal",
    "blocked_instruction",
    "unknown_action_proposal",
}

ALLOWED_RISK_LEVELS_V1 = {
    "no_action_summary_only",
    "low_reviewable_task",
    "medium_local_state_change",
    "high_external_side_effect",
    "critical_public_or_irreversible",
    "blocked_unknown_risk",
}

ALLOWED_AUTHORIZATION_STATUSES_V1 = {
    "not_actionable",
    "candidate_only",
    "clarification_required",
    "owner_review_required",
    "operator_review_required",
    "tool_boundary_required",
    "action_authority_required",
    "blocked_by_access_policy",
    "blocked_by_pii_policy",
    "blocked_by_poison_policy",
    "blocked_by_secret_risk",
    "blocked_by_public_effect",
    "blocked_by_unknown_authority",
    "unknown_status",
}

ALLOWED_STATUS_VALUES_V1 = {"clear", "blocked", "poisoned", "unknown"}

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

AUTHORIZATION_PHRASES_V1 = (
    "authorize",
    "self-authorize",
    "execute",
    "run this",
    "do it now",
    "go ahead",
    "permission to run",
)

SOURCE_HINTS_V1 = {
    "owner": "owner_uploaded_document",
    "operator": "operator_internal_document",
    "project": "project_internal_document",
    "workspace": "workspace_shared_document",
    "public source": "public_source_document",
    "third party": "third_party_document",
    "web": "retrieved_web_document",
    "email": "email_like_message",
    "policy": "legal_or_policy_document",
    "legal": "legal_or_policy_document",
    "spec": "technical_specification",
    "code": "code_or_patch_document",
    "patch": "code_or_patch_document",
    "calendar": "calendar_or_schedule_document",
    "schedule": "calendar_or_schedule_document",
    "invoice": "invoice_or_payment_document",
    "payment": "invoice_or_payment_document",
    "device": "device_instruction_document",
}

ACTION_HINTS_V1 = {
    "clarification": "clarification_request",
    "question": "clarification_request",
    "summary": "information_summary",
    "summarize": "information_summary",
    "task": "task_proposal",
    "checklist": "task_proposal",
    "plan": "task_proposal",
    "todo": "task_proposal",
    "file write": "file_write_proposal",
    "write file": "file_write_proposal",
    "patch": "patch_proposal",
    "diff": "patch_proposal",
    "test": "test_run_proposal",
    "pytest": "test_run_proposal",
    "shell": "shell_command_proposal",
    "command": "shell_command_proposal",
    "api": "api_call_proposal",
    "http": "api_call_proposal",
    "email": "email_or_message_proposal",
    "message": "email_or_message_proposal",
    "calendar": "calendar_event_proposal",
    "schedule": "calendar_event_proposal",
    "device": "device_control_proposal",
    "deploy": "deployment_proposal",
    "release": "deployment_proposal",
    "invoice": "payment_or_billing_proposal",
    "payment": "payment_or_billing_proposal",
    "bill": "payment_or_billing_proposal",
    "public": "public_posting_proposal",
    "post": "public_posting_proposal",
    "tweet": "public_posting_proposal",
    "memory": "memory_write_proposal",
    "remember": "memory_write_proposal",
    "blocked": "blocked_instruction",
    "poison": "blocked_instruction",
    "secret": "blocked_instruction",
}

class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DocumentActionPacket:
    document_action_packet_id: str
    source_document_ref: str
    source_document_class: str
    source_scope: str
    source_access_packet_ref: str
    source_evidence_graph_ref: str
    claim_grounding_packet_ref: str
    poison_status: str
    privacy_status: str
    pii_risk_status: str
    secret_risk_status: str
    extracted_action_class: str
    action_summary: str
    action_risk_level: str
    authorization_status: str
    required_owner_decision: bool
    required_operator_decision: bool
    required_tool_boundary: bool
    required_action_boundary: bool
    required_validation_packet: bool
    required_patch_feedback_packet: bool
    required_rollback_plan: bool
    external_side_effect_possible: bool
    public_effect_possible: bool
    device_or_physical_effect_possible: bool
    payment_or_billing_effect_possible: bool
    memory_write_possible: bool
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
    recommended_next_check: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class DocumentActionSummary:
    summary_type: str
    document_action_packet_id: str
    source_document_class: str
    extracted_action_class: str
    action_risk_level: str
    authorization_status: str
    recommended_next_check: str
    required_owner_decision: bool
    required_operator_decision: bool
    required_tool_boundary: bool
    required_action_boundary: bool


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
        return { _safe_text(key): to_document_action_json_safe_v1(item) for key, item in value.items() }
    return {"value": to_document_action_json_safe_v1(value)}


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
            if key_text in {"safe_metadata", "action_summary", "source_scope", "recommended_next_check"} or key_text.endswith("_metadata"):
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
            if key_text in {"document_content", "document_text", "source_text", "body_text", "message_text", "extracted_text"}:
                if _contains_authorize_phrase(item):
                    return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_authorize_phrase(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in AUTHORIZATION_PHRASES_V1)


def _contains_secret_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(hint in key_text for hint in ("secret", "token", "api key", "credential", "password")):
                return True
            if _contains_secret_marker(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_secret_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(hint in blob for hint in ("secret", "token", "api key", "credential", "password"))


def _contains_poison_signal(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        if _normalize_text(value.get("poison_status")) == "poisoned":
            return True
        for item in value.values():
            if _contains_poison_signal(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_poison_signal(item) for item in value)
    return False


def to_document_action_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return { _safe_text(key): to_document_action_json_safe_v1(item) for key, item in sorted(value.items(), key=lambda item: _safe_text(item[0])) }
    if isinstance(value, tuple):
        return [to_document_action_json_safe_v1(item) for item in value]
    if isinstance(value, list):
        return [to_document_action_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        items = [to_document_action_json_safe_v1(item) for item in value]
        return sorted(items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_document_action_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_document_action_json_safe_v1(vars(value))
    return _safe_text(value)


def _packet_like(value: Any) -> DocumentActionPacket:
    if isinstance(value, DocumentActionPacket):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    safe_metadata = value.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        safe_metadata = {"value": safe_metadata}
    return DocumentActionPacket(
        document_action_packet_id=_safe_text(value.get("document_action_packet_id")),
        source_document_ref=_safe_text(value.get("source_document_ref")),
        source_document_class=_safe_text(value.get("source_document_class")),
        source_scope=_safe_text(value.get("source_scope")),
        source_access_packet_ref=_safe_text(value.get("source_access_packet_ref")),
        source_evidence_graph_ref=_safe_text(value.get("source_evidence_graph_ref")),
        claim_grounding_packet_ref=_safe_text(value.get("claim_grounding_packet_ref")),
        poison_status=_safe_text(value.get("poison_status", "unknown")),
        privacy_status=_safe_text(value.get("privacy_status", "unknown")),
        pii_risk_status=_safe_text(value.get("pii_risk_status", "unknown")),
        secret_risk_status=_safe_text(value.get("secret_risk_status", "unknown")),
        extracted_action_class=_safe_text(value.get("extracted_action_class")),
        action_summary=_safe_text(value.get("action_summary")),
        action_risk_level=_safe_text(value.get("action_risk_level")),
        authorization_status=_safe_text(value.get("authorization_status")),
        required_owner_decision=_safe_bool(value.get("required_owner_decision", False)),
        required_operator_decision=_safe_bool(value.get("required_operator_decision", False)),
        required_tool_boundary=_safe_bool(value.get("required_tool_boundary", False)),
        required_action_boundary=_safe_bool(value.get("required_action_boundary", False)),
        required_validation_packet=_safe_bool(value.get("required_validation_packet", False)),
        required_patch_feedback_packet=_safe_bool(value.get("required_patch_feedback_packet", False)),
        required_rollback_plan=_safe_bool(value.get("required_rollback_plan", False)),
        external_side_effect_possible=_safe_bool(value.get("external_side_effect_possible", False)),
        public_effect_possible=_safe_bool(value.get("public_effect_possible", False)),
        device_or_physical_effect_possible=_safe_bool(value.get("device_or_physical_effect_possible", False)),
        payment_or_billing_effect_possible=_safe_bool(value.get("payment_or_billing_effect_possible", False)),
        memory_write_possible=_safe_bool(value.get("memory_write_possible", False)),
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
        recommended_next_check=_safe_text(value.get("recommended_next_check")),
        runtime_authority=_safe_bool(value.get("runtime_authority", False)),
        writes_state=_safe_bool(value.get("writes_state", False)),
        model_provider_used=_safe_bool(value.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(value.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(value.get("learning_claimed", False)),
        safe_metadata=dict(safe_metadata or {}),
    )


def classify_document_source_v1(
    *,
    source_document_class: str | None = None,
    source_document_ref: str | None = None,
    source_scope: str | None = None,
    source_access_packet_ref: str | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> str:
    candidate = _safe_text(source_document_class).strip().lower()
    if candidate in ALLOWED_SOURCE_DOCUMENT_CLASSES_V1:
        return candidate

    probe = " ".join([
        _safe_text(source_document_class),
        _safe_text(source_document_ref),
        _safe_text(source_scope),
        _safe_text(source_access_packet_ref),
        " ".join(_safe_text(item) for item in (safe_metadata or {}).values()) if isinstance(safe_metadata, Mapping) else "",
    ]).lower()

    for hint, klass in SOURCE_HINTS_V1.items():
        if hint in probe:
            return klass
    return "unknown_document_source"


def classify_extracted_action_v1(
    *,
    extracted_action_class: str | None = None,
    action_summary: str | None = None,
    source_document_class: str | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> str:
    candidate = _safe_text(extracted_action_class).strip().lower()
    if candidate in ALLOWED_EXTRACTED_ACTION_CLASSES_V1:
        return candidate

    probe = " ".join([
        _safe_text(extracted_action_class),
        _safe_text(action_summary),
        _safe_text(source_document_class),
        " ".join(_safe_text(item) for item in (safe_metadata or {}).values()) if isinstance(safe_metadata, Mapping) else "",
    ]).lower()

    for hint, klass in ACTION_HINTS_V1.items():
        if hint in probe:
            return klass
    return "unknown_action_proposal"


def evaluate_document_action_authority_v1(packet: Any) -> DocumentActionPacket:
    current = _packet_like(packet)
    source_document_class = classify_document_source_v1(
        source_document_class=current.source_document_class,
        source_document_ref=current.source_document_ref,
        source_scope=current.source_scope,
        source_access_packet_ref=current.source_access_packet_ref,
        safe_metadata=current.safe_metadata,
    )
    extracted_action_class = classify_extracted_action_v1(
        extracted_action_class=current.extracted_action_class,
        action_summary=current.action_summary,
        source_document_class=source_document_class,
        safe_metadata=current.safe_metadata,
    )
    source_private = source_document_class in {
        "owner_uploaded_document",
        "operator_internal_document",
        "project_internal_document",
        "workspace_shared_document",
        "email_like_message",
        "legal_or_policy_document",
        "invoice_or_payment_document",
    }
    tool_like = extracted_action_class in {
        "file_write_proposal",
        "patch_proposal",
        "test_run_proposal",
        "shell_command_proposal",
        "api_call_proposal",
    }
    action_side_effect = extracted_action_class in {
        "email_or_message_proposal",
        "calendar_event_proposal",
        "device_control_proposal",
        "deployment_proposal",
        "payment_or_billing_proposal",
        "public_posting_proposal",
        "memory_write_proposal",
    }
    public_effect = extracted_action_class == "public_posting_proposal"
    device_effect = extracted_action_class == "device_control_proposal"
    payment_effect = extracted_action_class == "payment_or_billing_proposal"
    memory_effect = extracted_action_class == "memory_write_proposal"
    external_effect = action_side_effect or tool_like

    risk = "low_reviewable_task"
    authorization_status = "candidate_only"
    required_owner_decision = False
    required_operator_decision = False
    required_tool_boundary = False
    required_action_boundary = False
    required_validation_packet = False
    required_patch_feedback_packet = False
    required_rollback_plan = False
    execution_allowed = False
    tool_execution_allowed = False
    write_allowed = False
    send_allowed = False
    calendar_change_allowed = False
    device_control_allowed = False
    deployment_allowed = False
    public_post_allowed = False
    payment_allowed = False
    memory_write_allowed = False

    if current.poison_status == "poisoned":
        risk = "blocked_unknown_risk"
        authorization_status = "blocked_by_poison_policy"
    elif current.secret_risk_status == "blocked":
        risk = "blocked_unknown_risk"
        authorization_status = "blocked_by_secret_risk"
    elif current.pii_risk_status == "blocked":
        risk = "blocked_unknown_risk"
        authorization_status = "blocked_by_pii_policy"
    elif current.privacy_status == "blocked" and public_effect:
        risk = "blocked_unknown_risk"
        authorization_status = "blocked_by_public_effect"
    elif source_document_class == "unknown_document_source":
        risk = "blocked_unknown_risk"
        authorization_status = "blocked_by_unknown_authority"
    elif extracted_action_class == "blocked_instruction":
        risk = "no_action_summary_only"
        authorization_status = "blocked_by_poison_policy" if current.poison_status == "poisoned" else "blocked_by_access_policy"
    elif extracted_action_class == "clarification_request":
        risk = "no_action_summary_only"
        authorization_status = "clarification_required"
    elif extracted_action_class in {"information_summary", "task_proposal"}:
        risk = "low_reviewable_task"
        authorization_status = "candidate_only"
    elif extracted_action_class in {"file_write_proposal", "patch_proposal", "test_run_proposal", "shell_command_proposal", "api_call_proposal"}:
        risk = "medium_local_state_change" if extracted_action_class in {"file_write_proposal", "patch_proposal"} else "high_external_side_effect"
        authorization_status = "tool_boundary_required"
        required_tool_boundary = True
        if extracted_action_class in {"file_write_proposal", "patch_proposal", "test_run_proposal"}:
            required_validation_packet = True
            if extracted_action_class == "patch_proposal":
                required_patch_feedback_packet = True
        if extracted_action_class in {"shell_command_proposal", "api_call_proposal"}:
            required_tool_boundary = True
    elif extracted_action_class in {"email_or_message_proposal", "calendar_event_proposal", "device_control_proposal", "deployment_proposal", "payment_or_billing_proposal", "public_posting_proposal", "memory_write_proposal"}:
        risk = "critical_public_or_irreversible" if extracted_action_class in {"deployment_proposal", "payment_or_billing_proposal", "public_posting_proposal"} else "high_external_side_effect"
        authorization_status = "action_authority_required"
        required_action_boundary = True
        if extracted_action_class in {"email_or_message_proposal", "calendar_event_proposal", "device_control_proposal"}:
            required_owner_decision = True
        if extracted_action_class in {"payment_or_billing_proposal", "device_control_proposal", "deployment_proposal", "public_posting_proposal", "memory_write_proposal"}:
            required_operator_decision = True
    else:
        risk = "blocked_unknown_risk"
        authorization_status = "blocked_by_unknown_authority"

    if source_document_class in {"legal_or_policy_document", "invoice_or_payment_document", "device_instruction_document"}:
        required_owner_decision = True
        required_operator_decision = True
        if authorization_status in {"candidate_only", "clarification_required"}:
            authorization_status = "owner_review_required"
    if source_document_class == "public_source_document" and public_effect:
        required_owner_decision = True
        required_operator_decision = True
        authorization_status = "blocked_by_public_effect"
    if source_document_class in {"legal_or_policy_document", "invoice_or_payment_document", "device_instruction_document"} and action_side_effect:
        required_action_boundary = True
    if source_document_class == "code_or_patch_document" and extracted_action_class in {"patch_proposal", "file_write_proposal", "test_run_proposal"}:
        required_validation_packet = True
        required_patch_feedback_packet = extracted_action_class == "patch_proposal"
        required_tool_boundary = True
    if tool_like:
        required_tool_boundary = True
    if action_side_effect:
        required_action_boundary = True
    if public_effect:
        required_operator_decision = True
    if device_effect or payment_effect or memory_effect:
        required_operator_decision = True
    if extracted_action_class == "blocked_instruction":
        required_tool_boundary = False
        required_action_boundary = False

    if extracted_action_class == "patch_proposal":
        required_validation_packet = True
        required_patch_feedback_packet = True
    if extracted_action_class == "file_write_proposal":
        required_validation_packet = True
        required_tool_boundary = True
    if extracted_action_class == "test_run_proposal":
        required_validation_packet = True
        required_tool_boundary = True
    if extracted_action_class == "memory_write_proposal":
        required_action_boundary = True

    if source_private and public_effect:
        authorization_status = "blocked_by_public_effect"
    if current.poison_status == "poisoned":
        authorization_status = "blocked_by_poison_policy"
    if current.secret_risk_status == "blocked":
        authorization_status = "blocked_by_secret_risk"
    if current.pii_risk_status == "blocked":
        authorization_status = "blocked_by_pii_policy"

    if required_tool_boundary and authorization_status in {"candidate_only", "clarification_required", "owner_review_required", "operator_review_required"}:
        authorization_status = "tool_boundary_required"
    if required_action_boundary and authorization_status in {"candidate_only", "clarification_required", "owner_review_required", "operator_review_required", "tool_boundary_required"}:
        authorization_status = "action_authority_required"

    if current.safe_metadata and _contains_secret_marker(current.safe_metadata):
        if authorization_status not in {"blocked_by_secret_risk", "blocked_by_access_policy"}:
            authorization_status = "blocked_by_secret_risk"
            risk = "blocked_unknown_risk"
    if current.safe_metadata and _contains_authorize_phrase(current.safe_metadata):
        if authorization_status not in {"blocked_by_poison_policy", "blocked_by_secret_risk", "blocked_by_pii_policy", "blocked_by_public_effect", "blocked_by_access_policy", "blocked_by_unknown_authority"}:
            authorization_status = "blocked_by_unknown_authority"
            risk = "blocked_unknown_risk"

    action_summary = current.action_summary or {
        "clarification_request": "Clarification needed before any action proposal.",
        "information_summary": "Source can be summarized as metadata only.",
        "task_proposal": "Reviewable task proposal only.",
        "file_write_proposal": "File write proposal; requires validation boundary.",
        "patch_proposal": "Patch proposal; requires validation and patch feedback boundaries.",
        "test_run_proposal": "Test run proposal; requires validation runner boundary.",
        "shell_command_proposal": "Shell command proposal; requires tool boundary.",
        "api_call_proposal": "API call proposal; requires tool boundary.",
        "email_or_message_proposal": "Draft message proposal; requires action authority.",
        "calendar_event_proposal": "Calendar event proposal; requires action authority.",
        "device_control_proposal": "Device control proposal; requires action authority.",
        "deployment_proposal": "Deployment proposal; requires action authority.",
        "payment_or_billing_proposal": "Payment or billing proposal; requires action authority.",
        "public_posting_proposal": "Public posting proposal; requires later public boundary.",
        "memory_write_proposal": "Memory write proposal; requires later memory boundary.",
        "blocked_instruction": "Blocked instruction preserved as metadata only.",
        "unknown_action_proposal": "Unknown action stays candidate only.",
    }.get(extracted_action_class, "Document action candidate only.")

    recommended_next_check = current.recommended_next_check or {
        "clarification_request": "request_clarification",
        "information_summary": "inspect_metadata_only",
        "task_proposal": "review_task_proposal",
        "file_write_proposal": "route_to_validation_runner",
        "patch_proposal": "route_to_validation_and_patch_feedback",
        "test_run_proposal": "route_to_validation_runner",
        "shell_command_proposal": "route_to_tool_use_executor_boundary",
        "api_call_proposal": "route_to_tool_use_executor_boundary",
        "email_or_message_proposal": "route_to_action_authority_boundary",
        "calendar_event_proposal": "route_to_action_authority_boundary",
        "device_control_proposal": "route_to_action_authority_boundary",
        "deployment_proposal": "route_to_action_authority_boundary",
        "payment_or_billing_proposal": "route_to_action_authority_boundary",
        "public_posting_proposal": "route_to_public_boundary_later",
        "memory_write_proposal": "route_to_memory_boundary_later",
        "blocked_instruction": "preserve_blocked_metadata_only",
        "unknown_action_proposal": "request_clarification",
    }.get(extracted_action_class, "inspect_metadata_only")

    return replace(
        current,
        source_document_class=source_document_class,
        extracted_action_class=extracted_action_class,
        action_summary=action_summary,
        action_risk_level=risk,
        authorization_status=authorization_status,
        required_owner_decision=required_owner_decision,
        required_operator_decision=required_operator_decision,
        required_tool_boundary=required_tool_boundary,
        required_action_boundary=required_action_boundary,
        required_validation_packet=required_validation_packet,
        required_patch_feedback_packet=required_patch_feedback_packet,
        required_rollback_plan=required_rollback_plan,
        external_side_effect_possible=external_effect,
        public_effect_possible=public_effect,
        device_or_physical_effect_possible=device_effect,
        payment_or_billing_effect_possible=payment_effect,
        memory_write_possible=memory_effect,
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
        recommended_next_check=recommended_next_check,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        learning_claimed=False,
    )


def build_document_action_packet_v1(**kwargs: Any) -> DocumentActionPacket:
    packet = DocumentActionPacket(
        document_action_packet_id=_safe_text(kwargs.get("document_action_packet_id")),
        source_document_ref=_safe_text(kwargs.get("source_document_ref")),
        source_document_class=classify_document_source_v1(
            source_document_class=kwargs.get("source_document_class"),
            source_document_ref=kwargs.get("source_document_ref"),
            source_scope=kwargs.get("source_scope"),
            source_access_packet_ref=kwargs.get("source_access_packet_ref"),
            safe_metadata=kwargs.get("safe_metadata"),
        ),
        source_scope=_safe_text(kwargs.get("source_scope", "metadata_only")),
        source_access_packet_ref=_safe_text(kwargs.get("source_access_packet_ref")),
        source_evidence_graph_ref=_safe_text(kwargs.get("source_evidence_graph_ref")),
        claim_grounding_packet_ref=_safe_text(kwargs.get("claim_grounding_packet_ref")),
        poison_status=_safe_text(kwargs.get("poison_status", "clear")),
        privacy_status=_safe_text(kwargs.get("privacy_status", "clear")),
        pii_risk_status=_safe_text(kwargs.get("pii_risk_status", "clear")),
        secret_risk_status=_safe_text(kwargs.get("secret_risk_status", "clear")),
        extracted_action_class=classify_extracted_action_v1(
            extracted_action_class=kwargs.get("extracted_action_class"),
            action_summary=kwargs.get("action_summary"),
            source_document_class=kwargs.get("source_document_class"),
            safe_metadata=kwargs.get("safe_metadata"),
        ),
        action_summary=_safe_text(kwargs.get("action_summary")),
        action_risk_level=_safe_text(kwargs.get("action_risk_level", "low_reviewable_task")),
        authorization_status=_safe_text(kwargs.get("authorization_status", "candidate_only")),
        required_owner_decision=_safe_bool(kwargs.get("required_owner_decision", False)),
        required_operator_decision=_safe_bool(kwargs.get("required_operator_decision", False)),
        required_tool_boundary=_safe_bool(kwargs.get("required_tool_boundary", False)),
        required_action_boundary=_safe_bool(kwargs.get("required_action_boundary", False)),
        required_validation_packet=_safe_bool(kwargs.get("required_validation_packet", False)),
        required_patch_feedback_packet=_safe_bool(kwargs.get("required_patch_feedback_packet", False)),
        required_rollback_plan=_safe_bool(kwargs.get("required_rollback_plan", False)),
        external_side_effect_possible=_safe_bool(kwargs.get("external_side_effect_possible", False)),
        public_effect_possible=_safe_bool(kwargs.get("public_effect_possible", False)),
        device_or_physical_effect_possible=_safe_bool(kwargs.get("device_or_physical_effect_possible", False)),
        payment_or_billing_effect_possible=_safe_bool(kwargs.get("payment_or_billing_effect_possible", False)),
        memory_write_possible=_safe_bool(kwargs.get("memory_write_possible", False)),
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
        recommended_next_check=_safe_text(kwargs.get("recommended_next_check", "inspect_metadata_only")),
        runtime_authority=_safe_bool(kwargs.get("runtime_authority", False)),
        writes_state=_safe_bool(kwargs.get("writes_state", False)),
        model_provider_used=_safe_bool(kwargs.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(kwargs.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(kwargs.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(kwargs.get("learning_claimed", False)),
        safe_metadata=_safe_mapping(kwargs.get("safe_metadata")),
    )
    packet = evaluate_document_action_authority_v1(packet)
    return packet


def validate_document_action_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _packet_like(packet)

    if normalized.source_document_class not in ALLOWED_SOURCE_DOCUMENT_CLASSES_V1:
        raise ValidationError("unknown_document_source_promoted_as_valid")
    if normalized.extracted_action_class not in ALLOWED_EXTRACTED_ACTION_CLASSES_V1:
        raise ValidationError("unknown_action_promoted_as_valid")
    if normalized.action_risk_level not in ALLOWED_RISK_LEVELS_V1:
        raise ValidationError("unknown_risk_promoted_as_valid")
    if normalized.authorization_status not in ALLOWED_AUTHORIZATION_STATUSES_V1:
        raise ValidationError("unknown_status_promoted_as_valid")
    for status_name in (normalized.poison_status, normalized.privacy_status, normalized.pii_risk_status, normalized.secret_risk_status):
        if status_name not in ALLOWED_STATUS_VALUES_V1:
            raise ValidationError("unknown_status_promoted_as_valid")

    if normalized.execution_allowed:
        raise ValidationError("execution_allowed_must_be_false")
    if normalized.tool_execution_allowed:
        raise ValidationError("tool_execution_allowed_must_be_false")
    if normalized.write_allowed:
        raise ValidationError("write_allowed_must_be_false")
    if normalized.send_allowed:
        raise ValidationError("send_allowed_must_be_false")
    if normalized.calendar_change_allowed:
        raise ValidationError("calendar_change_allowed_must_be_false")
    if normalized.device_control_allowed:
        raise ValidationError("device_control_allowed_must_be_false")
    if normalized.deployment_allowed:
        raise ValidationError("deployment_allowed_must_be_false")
    if normalized.public_post_allowed:
        raise ValidationError("public_post_allowed_must_be_false")
    if normalized.payment_allowed:
        raise ValidationError("payment_allowed_must_be_false")
    if normalized.memory_write_allowed:
        raise ValidationError("memory_write_allowed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.proof_claim_allowed:
        raise ValidationError("proof_claim_allowed_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")

    if normalized.action_summary and _contains_claim_marker(normalized.action_summary):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.safe_metadata and _contains_claim_marker(normalized.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.safe_metadata and _contains_authorize_phrase(normalized.safe_metadata) and normalized.authorization_status not in {"blocked_by_poison_policy", "blocked_by_secret_risk", "blocked_by_pii_policy", "blocked_by_public_effect", "blocked_by_access_policy", "blocked_by_unknown_authority"}:
        raise ValidationError("blocked_by_unknown_authority")

    if normalized.poison_status == "poisoned" and normalized.authorization_status not in {"blocked_by_poison_policy", "blocked_by_access_policy"}:
        raise ValidationError("poisoned_document_cannot_authorize_action")
    if normalized.secret_risk_status == "blocked" and normalized.authorization_status not in {"blocked_by_secret_risk", "blocked_by_access_policy", "blocked_by_pii_policy", "blocked_by_unknown_authority"}:
        raise ValidationError("secret_risk_blocks_action_promotion")
    if normalized.privacy_status == "blocked" and normalized.public_effect_possible and normalized.authorization_status not in {"blocked_by_public_effect", "blocked_by_access_policy", "blocked_by_pii_policy"}:
        raise ValidationError("private_document_cannot_authorize_public_action")
    if normalized.pii_risk_status == "blocked" and normalized.public_effect_possible and normalized.authorization_status not in {"blocked_by_public_effect", "blocked_by_access_policy", "blocked_by_pii_policy"}:
        raise ValidationError("private_document_cannot_authorize_public_action")

    if normalized.public_effect_possible and normalized.source_document_class not in {"public_source_document", "retrieved_web_document"}:
        if normalized.authorization_status not in {"blocked_by_public_effect", "blocked_by_access_policy", "blocked_by_pii_policy"}:
            raise ValidationError("private_document_cannot_authorize_public_action")

    if normalized.required_owner_decision is False and normalized.source_document_class in {"legal_or_policy_document", "invoice_or_payment_document", "device_instruction_document"}:
        raise ValidationError("owner_review_required_for_document_action")
    if normalized.required_operator_decision is False and normalized.source_document_class in {"legal_or_policy_document", "invoice_or_payment_document", "device_instruction_document"}:
        raise ValidationError("operator_review_required_for_document_action")
    if normalized.required_tool_boundary is False and normalized.extracted_action_class in {"file_write_proposal", "patch_proposal", "test_run_proposal", "shell_command_proposal", "api_call_proposal"}:
        raise ValidationError("tool_boundary_required_for_document_action")
    if normalized.required_action_boundary is False and normalized.extracted_action_class in {"email_or_message_proposal", "calendar_event_proposal", "device_control_proposal", "deployment_proposal", "payment_or_billing_proposal", "public_posting_proposal", "memory_write_proposal"}:
        raise ValidationError("action_boundary_required_for_document_action")
    if normalized.required_validation_packet is False and normalized.extracted_action_class in {"patch_proposal", "file_write_proposal", "test_run_proposal"}:
        raise ValidationError("validation_packet_required_for_code_action")
    if normalized.required_patch_feedback_packet is False and normalized.extracted_action_class == "patch_proposal":
        raise ValidationError("patch_feedback_required_for_patch_action")

    if normalized.required_tool_boundary and normalized.extracted_action_class in {"file_write_proposal", "patch_proposal", "test_run_proposal", "shell_command_proposal", "api_call_proposal"} and normalized.authorization_status not in {"tool_boundary_required", "blocked_by_access_policy", "blocked_by_unknown_authority", "blocked_by_secret_risk", "blocked_by_pii_policy", "candidate_only"}:
        raise ValidationError("tool_boundary_must_be_visible")
    if normalized.required_action_boundary and normalized.extracted_action_class in {"email_or_message_proposal", "calendar_event_proposal", "device_control_proposal", "deployment_proposal", "payment_or_billing_proposal", "public_posting_proposal", "memory_write_proposal"} and normalized.authorization_status not in {"action_authority_required", "owner_review_required", "operator_review_required", "blocked_by_access_policy", "blocked_by_public_effect", "blocked_by_unknown_authority", "blocked_by_secret_risk", "blocked_by_pii_policy"}:
        raise ValidationError("action_boundary_must_be_visible")

    if normalized.required_tool_boundary is False and normalized.tool_execution_allowed:
        raise ValidationError("tool_boundary_must_block_execution")
    if normalized.required_action_boundary is False and (normalized.send_allowed or normalized.calendar_change_allowed or normalized.device_control_allowed or normalized.deployment_allowed or normalized.public_post_allowed or normalized.payment_allowed or normalized.memory_write_allowed):
        raise ValidationError("action_boundary_must_block_execution")

    return True


def summarize_document_action_packet_v1(packet: Any) -> DocumentActionSummary:
    normalized = _packet_like(packet)
    validate_document_action_packet_v1(normalized)
    return DocumentActionSummary(
        summary_type=SUMMARY_TYPE_V1,
        document_action_packet_id=normalized.document_action_packet_id,
        source_document_class=normalized.source_document_class,
        extracted_action_class=normalized.extracted_action_class,
        action_risk_level=normalized.action_risk_level,
        authorization_status=normalized.authorization_status,
        recommended_next_check=normalized.recommended_next_check,
        required_owner_decision=normalized.required_owner_decision,
        required_operator_decision=normalized.required_operator_decision,
        required_tool_boundary=normalized.required_tool_boundary,
        required_action_boundary=normalized.required_action_boundary,
    )


def build_initial_document_action_examples_v1() -> list[DocumentActionPacket]:
    examples: list[DocumentActionPacket] = []

    examples.append(build_document_action_packet_v1(
        document_action_packet_id="uploaded_project_spec_task_proposal_v1",
        source_document_ref="doc_uploaded_spec_v1",
        source_document_class="owner_uploaded_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_uploaded_spec_v1",
        source_evidence_graph_ref="source_evidence_uploaded_spec_v1",
        claim_grounding_packet_ref="claim_grounding_uploaded_spec_v1",
        extracted_action_class="task_proposal",
        action_summary="Uploaded project spec becomes a reviewable task proposal only.",
        authorization_status="candidate_only",
        safe_metadata={"example_name": "uploaded_project_spec_task_proposal"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="email_like_draft_response_v1",
        source_document_ref="doc_email_like_v1",
        source_document_class="email_like_message",
        source_scope="summary_only",
        source_access_packet_ref="source_access_email_v1",
        source_evidence_graph_ref="source_evidence_email_v1",
        claim_grounding_packet_ref="claim_grounding_email_v1",
        extracted_action_class="email_or_message_proposal",
        action_summary="Email-like message becomes a draft-response proposal, not send authority.",
        required_owner_decision=True,
        required_operator_decision=True,
        required_action_boundary=True,
        authorization_status="action_authority_required",
        safe_metadata={"example_name": "email_like_draft_response"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="calendar_like_proposal_v1",
        source_document_ref="doc_calendar_like_v1",
        source_document_class="calendar_or_schedule_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_calendar_v1",
        source_evidence_graph_ref="source_evidence_calendar_v1",
        claim_grounding_packet_ref="claim_grounding_calendar_v1",
        extracted_action_class="calendar_event_proposal",
        action_summary="Calendar-like document becomes a calendar proposal, not a calendar change.",
        required_owner_decision=True,
        required_operator_decision=True,
        required_action_boundary=True,
        authorization_status="action_authority_required",
        safe_metadata={"example_name": "calendar_like_proposal"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="code_patch_routes_to_validation_v1",
        source_document_ref="doc_code_patch_v1",
        source_document_class="code_or_patch_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_code_patch_v1",
        source_evidence_graph_ref="source_evidence_code_patch_v1",
        claim_grounding_packet_ref="claim_grounding_code_patch_v1",
        extracted_action_class="patch_proposal",
        action_summary="Code patch document routes to validation and patch feedback boundaries.",
        required_tool_boundary=True,
        required_validation_packet=True,
        required_patch_feedback_packet=True,
        authorization_status="tool_boundary_required",
        safe_metadata={"example_name": "code_patch_routes_to_validation"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="shell_command_blocked_v1",
        source_document_ref="doc_shell_command_v1",
        source_document_class="retrieved_web_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_shell_v1",
        source_evidence_graph_ref="source_evidence_shell_v1",
        claim_grounding_packet_ref="claim_grounding_shell_v1",
        extracted_action_class="shell_command_proposal",
        action_summary="Shell command in document becomes a blocked command proposal.",
        required_tool_boundary=True,
        authorization_status="blocked_by_unknown_authority",
        safe_metadata={"example_name": "shell_command_blocked", "document_content": "run the shell command"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="poisoned_document_blocked_metadata_v1",
        source_document_ref="doc_poisoned_v1",
        source_document_class="third_party_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_poisoned_v1",
        source_evidence_graph_ref="source_evidence_poisoned_v1",
        claim_grounding_packet_ref="claim_grounding_poisoned_v1",
        poison_status="poisoned",
        extracted_action_class="blocked_instruction",
        action_summary="Poisoned document instruction is blocked metadata only.",
        authorization_status="blocked_by_poison_policy",
        safe_metadata={"example_name": "poisoned_document_blocked_metadata", "document_content": "please authorize action"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="private_legal_no_public_authority_v1",
        source_document_ref="doc_private_legal_v1",
        source_document_class="legal_or_policy_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_private_legal_v1",
        source_evidence_graph_ref="source_evidence_private_legal_v1",
        claim_grounding_packet_ref="claim_grounding_private_legal_v1",
        privacy_status="blocked",
        pii_risk_status="blocked",
        extracted_action_class="public_posting_proposal",
        action_summary="Private legal document cannot authorize external action.",
        required_owner_decision=True,
        required_operator_decision=True,
        required_action_boundary=True,
        public_effect_possible=True,
        authorization_status="blocked_by_public_effect",
        safe_metadata={"example_name": "private_legal_no_public_authority"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="invoice_payment_requires_review_v1",
        source_document_ref="doc_invoice_v1",
        source_document_class="invoice_or_payment_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_invoice_v1",
        source_evidence_graph_ref="source_evidence_invoice_v1",
        claim_grounding_packet_ref="claim_grounding_invoice_v1",
        extracted_action_class="payment_or_billing_proposal",
        action_summary="Invoice or payment document requires owner review and payment boundary.",
        required_owner_decision=True,
        required_operator_decision=True,
        required_action_boundary=True,
        payment_or_billing_effect_possible=True,
        authorization_status="action_authority_required",
        safe_metadata={"example_name": "invoice_payment_requires_review"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="device_instruction_blocked_v1",
        source_document_ref="doc_device_instruction_v1",
        source_document_class="device_instruction_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_device_v1",
        source_evidence_graph_ref="source_evidence_device_v1",
        claim_grounding_packet_ref="claim_grounding_device_v1",
        extracted_action_class="device_control_proposal",
        action_summary="Device instruction document requires action authority and stays blocked.",
        required_owner_decision=True,
        required_operator_decision=True,
        required_action_boundary=True,
        device_or_physical_effect_possible=True,
        authorization_status="action_authority_required",
        safe_metadata={"example_name": "device_instruction_blocked"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="public_source_deployment_blocked_v1",
        source_document_ref="doc_public_source_v1",
        source_document_class="public_source_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_public_v1",
        source_evidence_graph_ref="source_evidence_public_v1",
        claim_grounding_packet_ref="claim_grounding_public_v1",
        extracted_action_class="deployment_proposal",
        action_summary="Public source suggests a deployment step, but it stays blocked.",
        required_owner_decision=True,
        required_operator_decision=True,
        required_action_boundary=True,
        authorization_status="blocked_by_public_effect",
        safe_metadata={"example_name": "public_source_deployment_blocked"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="api_key_blocks_promotion_v1",
        source_document_ref="doc_api_key_v1",
        source_document_class="technical_specification",
        source_scope="summary_only",
        source_access_packet_ref="source_access_api_key_v1",
        source_evidence_graph_ref="source_evidence_api_key_v1",
        claim_grounding_packet_ref="claim_grounding_api_key_v1",
        secret_risk_status="blocked",
        extracted_action_class="api_call_proposal",
        action_summary="API key in the document blocks promotion.",
        required_tool_boundary=True,
        authorization_status="blocked_by_secret_risk",
        safe_metadata={"example_name": "api_key_blocks_promotion", "document_content": "contains API key for access"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="uploaded_checklist_task_list_only_v1",
        source_document_ref="doc_checklist_v1",
        source_document_class="owner_uploaded_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_checklist_v1",
        source_evidence_graph_ref="source_evidence_checklist_v1",
        claim_grounding_packet_ref="claim_grounding_checklist_v1",
        extracted_action_class="task_proposal",
        action_summary="User-uploaded checklist becomes a reviewable task list only.",
        authorization_status="candidate_only",
        safe_metadata={"example_name": "uploaded_checklist_task_list_only"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="model_generated_plan_candidate_only_v1",
        source_document_ref="doc_model_plan_v1",
        source_document_class="project_internal_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_model_plan_v1",
        source_evidence_graph_ref="source_evidence_model_plan_v1",
        claim_grounding_packet_ref="claim_grounding_model_plan_v1",
        extracted_action_class="task_proposal",
        action_summary="Model-generated plan from a document stays candidate-only.",
        authorization_status="candidate_only",
        safe_metadata={"example_name": "model_generated_plan_candidate_only"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="contradictory_instructions_clarify_v1",
        source_document_ref="doc_contradictory_v1",
        source_document_class="third_party_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_contradictory_v1",
        source_evidence_graph_ref="source_evidence_contradictory_v1",
        claim_grounding_packet_ref="claim_grounding_contradictory_v1",
        extracted_action_class="clarification_request",
        action_summary="Contradictory document instructions require clarification.",
        authorization_status="clarification_required",
        safe_metadata={"example_name": "contradictory_instructions_clarify"},
    ))
    examples.append(build_document_action_packet_v1(
        document_action_packet_id="memory_write_blocked_pending_boundary_v1",
        source_document_ref="doc_memory_write_v1",
        source_document_class="operator_internal_document",
        source_scope="summary_only",
        source_access_packet_ref="source_access_memory_v1",
        source_evidence_graph_ref="source_evidence_memory_v1",
        claim_grounding_packet_ref="claim_grounding_memory_v1",
        extracted_action_class="memory_write_proposal",
        action_summary="Memory write suggested by document is blocked pending memory boundary.",
        required_action_boundary=True,
        memory_write_possible=True,
        authorization_status="action_authority_required",
        safe_metadata={"example_name": "memory_write_blocked_pending_boundary"},
    ))

    return examples
