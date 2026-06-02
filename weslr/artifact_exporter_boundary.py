"""Metadata-only artifact exporter boundary v1.

This module classifies artifact export readiness into bounded in-memory packets.
It is deterministic, import-safe, pure in-memory, and fail-closed.
No subprocess. No shell execution. No file I/O. No model/provider/API calls.
No runtime wiring. No `.weslr` access. No artifact export, file generation,
upload, download, share, publication, deployment, tool execution, or action
execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Mapping

HELPER_TYPE_V1 = "artifact_exporter_boundary_v1"
PACKET_TYPE_V1 = "artifact_export_packet_v1"
SUMMARY_TYPE_V1 = "artifact_export_summary_v1"

ALLOWED_EXPORT_REQUEST_CLASSES_V1 = {
    "download_request",
    "local_save_request",
    "owner_handoff_request",
    "operator_handoff_request",
    "workspace_share_request",
    "email_attachment_request",
    "public_publish_request",
    "deployment_artifact_request",
    "legal_document_export_request",
    "code_patch_export_request",
    "report_export_request",
    "dataset_export_request",
    "memory_export_request",
    "artifact_marketplace_request",
    "unknown_export_request",
}

ALLOWED_ARTIFACT_TARGET_CLASSES_V1 = {
    "markdown_document",
    "pdf_document",
    "docx_document",
    "spreadsheet",
    "slide_deck",
    "image_asset",
    "code_file",
    "patch_file",
    "configuration_file",
    "json_metadata",
    "report_artifact",
    "dataset_artifact",
    "legal_or_policy_artifact",
    "public_website_asset",
    "unknown_artifact_target",
}

ALLOWED_EXPORT_READINESS_STATUSES_V1 = {
    "not_requested",
    "metadata_only_ready",
    "candidate_ready_for_owner_review",
    "candidate_ready_for_operator_review",
    "blocked_missing_provenance",
    "blocked_missing_validation",
    "blocked_missing_access_packet",
    "blocked_pii_or_privacy_risk",
    "blocked_secret_risk",
    "blocked_poison_risk",
    "blocked_public_claim_risk",
    "blocked_missing_rollback_or_retraction",
    "blocked_unknown_target",
    "blocked_unknown_request",
    "unknown_status",
}

ALLOWED_ARTIFACT_EXPORT_NEXT_STEP_CLASSES_V1 = {
    "no_export_metadata_only",
    "request_owner_review",
    "request_operator_review",
    "request_dual_review",
    "request_validation_packet",
    "request_provenance_packet",
    "request_document_access_packet",
    "request_pii_scrub",
    "request_secret_review",
    "request_public_claim_review",
    "request_rollback_or_retraction_plan",
    "defer_to_action_authority",
    "defer_to_owner_operator_workflow",
    "blocked_no_safe_export",
    "unknown_next_step",
}

CLEAR_VALUES_V1 = {"clear", "none", "false", "safe", "metadata_only"}
RISK_BLOCK_VALUES_V1 = {"blocked", "poisoned", "unknown", "mismatch", "risky"}

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
    "production-ready",
)

class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ArtifactExportPacket:
    artifact_export_packet_id: str
    export_request_class: str
    artifact_target_class: str
    artifact_ref: str
    artifact_summary: str
    artifact_provenance_ref: str
    document_access_packet_ref: str
    claim_grounding_packet_ref: str
    source_evidence_graph_ref: str
    validation_packet_ref: str
    owner_operator_workflow_packet_ref: str
    action_authority_packet_ref: str
    rollback_packet_ref: str
    export_readiness_status: str
    export_next_step: str
    export_scope_summary: str
    destination_summary: str
    owner_review_required: bool
    operator_review_required: bool
    dual_review_required: bool
    validation_required: bool
    provenance_required: bool
    document_access_required: bool
    pii_scrub_required: bool
    secret_review_required: bool
    public_claim_review_required: bool
    rollback_or_retraction_required: bool
    privacy_status: str
    pii_risk_status: str
    secret_risk_status: str
    poison_status: str
    public_effect_possible: bool
    external_side_effect_possible: bool
    marketplace_effect_possible: bool
    download_allowed: bool
    local_save_allowed: bool
    share_allowed: bool
    email_attachment_allowed: bool
    public_publish_allowed: bool
    deployment_artifact_allowed: bool
    marketplace_publish_allowed: bool
    export_execution_allowed: bool
    recommended_next_check: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ArtifactExportSummary:
    summary_type: str
    artifact_export_packet_id: str
    export_request_class: str
    artifact_target_class: str
    export_readiness_status: str
    export_next_step: str
    export_scope_summary: str
    destination_summary: str
    owner_review_required: bool
    operator_review_required: bool
    dual_review_required: bool
    validation_required: bool
    provenance_required: bool
    document_access_required: bool
    pii_scrub_required: bool
    secret_review_required: bool
    public_claim_review_required: bool
    rollback_or_retraction_required: bool
    public_effect_possible: bool
    external_side_effect_possible: bool
    marketplace_effect_possible: bool
    export_execution_allowed: bool
    recommended_next_check: str


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_bool(value: Any) -> bool:
    return bool(value)


def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).lower().split())


def _json_sort_key(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return repr(value)
    return repr(value)


def _safe_metadata_dict(value: Any) -> dict[str, Any]:
    safe = to_artifact_export_json_safe_v1(value) if value is not None else {}
    if safe is None:
        return {}
    if not isinstance(safe, Mapping):
        return {"value": safe}
    return dict(safe)


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
    text = _normalize_text(value)
    return any(phrase in text for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _contains_risk_marker(value: Any) -> bool:
    text = _normalize_text(value)
    return any(marker in text for marker in ("secret", "private", "pii", "poison", "raw"))


def _is_clear(value: str) -> bool:
    return _normalize_text(value) in CLEAR_VALUES_V1


def _is_risk(value: str) -> bool:
    normalized = _normalize_text(value)
    return bool(normalized) and normalized not in CLEAR_VALUES_V1


def _request_text(kwargs: Mapping[str, Any]) -> str:
    return " ".join(
        _safe_text(kwargs.get(name))
        for name in (
            "export_request_class",
            "request_class",
            "request_summary",
            "artifact_summary",
            "export_scope_summary",
            "destination_summary",
            "artifact_ref",
            "claim_grounding_packet_ref",
            "source_evidence_graph_ref",
        )
    ).lower()


def classify_artifact_export_request_v1(**kwargs: Any) -> str:
    explicit = _safe_text(kwargs.get("export_request_class") or kwargs.get("request_class"))
    if explicit:
        if explicit in ALLOWED_EXPORT_REQUEST_CLASSES_V1:
            return explicit
        return "unknown_export_request"

    text = _request_text(kwargs)
    if any(hint in text for hint in ("local save", "save locally", "save to disk")):
        return "local_save_request"
    if any(hint in text for hint in ("download", "downloadable", "export download")):
        return "download_request"
    if any(hint in text for hint in ("owner handoff", "owner hand-off", "owner review")):
        return "owner_handoff_request"
    if any(hint in text for hint in ("operator handoff", "operator hand-off", "operator review")):
        return "operator_handoff_request"
    if any(hint in text for hint in ("workspace share", "workspace", "share")):
        return "workspace_share_request"
    if any(hint in text for hint in ("email attachment", "message attachment", "attachment", "email")):
        return "email_attachment_request"
    if any(hint in text for hint in ("public publish", "public website", "public post", "publish", "website")):
        return "public_publish_request"
    if any(hint in text for hint in ("deployment", "deploy", "staging")):
        return "deployment_artifact_request"
    if any(hint in text for hint in ("legal document", "legal policy", "policy draft", "legal")):
        return "legal_document_export_request"
    if any(hint in text for hint in ("patch", "diff", "code patch", "patch bundle")):
        return "code_patch_export_request"
    if any(hint in text for hint in ("report", "evidence report", "markdown report")):
        return "report_export_request"
    if any(hint in text for hint in ("dataset", "csv", "spreadsheet", "table", "data export")):
        return "dataset_export_request"
    if any(hint in text for hint in ("memory", "memory export")):
        return "memory_export_request"
    if any(hint in text for hint in ("marketplace", "listing", "market place")):
        return "artifact_marketplace_request"
    return "unknown_export_request"


def classify_artifact_export_target_v1(**kwargs: Any) -> str:
    explicit = _safe_text(kwargs.get("artifact_target_class") or kwargs.get("target_class"))
    if explicit:
        if explicit in ALLOWED_ARTIFACT_TARGET_CLASSES_V1:
            return explicit
        return "unknown_artifact_target"

    text = " ".join(
        _safe_text(kwargs.get(name))
        for name in (
            "artifact_target_class",
            "target_class",
            "artifact_summary",
            "export_scope_summary",
            "destination_summary",
            "artifact_ref",
            "claim_grounding_packet_ref",
            "source_evidence_graph_ref",
        )
    ).lower()

    if any(hint in text for hint in ("markdown", ".md", "md document")):
        return "markdown_document"
    if any(hint in text for hint in ("pdf", "portable document")):
        return "pdf_document"
    if any(hint in text for hint in ("docx", "word document", "word")):
        return "docx_document"
    if any(hint in text for hint in ("spreadsheet", "xlsx", "csv", "sheet")):
        return "spreadsheet"
    if any(hint in text for hint in ("slide", "deck", "ppt", "presentation")):
        return "slide_deck"
    if any(hint in text for hint in ("image", "png", "jpg", "jpeg", "svg", "visual", "figure")):
        return "image_asset"
    if any(hint in text for hint in ("patch", "diff")):
        return "patch_file"
    if any(hint in text for hint in ("config", "yaml", "yml", "toml", "ini")):
        return "configuration_file"
    if any(hint in text for hint in ("json", "metadata")):
        return "json_metadata"
    if any(hint in text for hint in ("code", "python", "module", ".py", "source")):
        return "code_file"
    if any(hint in text for hint in ("dataset", "data", "corpus")):
        return "dataset_artifact"
    if any(hint in text for hint in ("legal", "policy", "compliance")):
        return "legal_or_policy_artifact"
    if any(hint in text for hint in ("public website", "website", "web page", "html", "static site")):
        return "public_website_asset"
    if any(hint in text for hint in ("report", "evidence")):
        return "report_artifact"
    return "unknown_artifact_target"


def _is_publicish_request(request_class: str, target_class: str) -> bool:
    return request_class in {"public_publish_request", "artifact_marketplace_request"} or target_class == "public_website_asset"


def _is_external_request(request_class: str) -> bool:
    return request_class in {
        "workspace_share_request",
        "email_attachment_request",
        "public_publish_request",
        "deployment_artifact_request",
        "artifact_marketplace_request",
    }


def _is_validation_request(request_class: str, target_class: str) -> bool:
    return request_class in {"code_patch_export_request", "deployment_artifact_request"} or target_class in {
        "code_file",
        "patch_file",
        "configuration_file",
    }


def _is_document_access_request(request_class: str, target_class: str) -> bool:
    return request_class in {"legal_document_export_request", "dataset_export_request", "memory_export_request"} or target_class in {
        "legal_or_policy_artifact",
        "dataset_artifact",
    }


def _is_privacy_review_request(request_class: str, target_class: str) -> bool:
    return request_class in {"dataset_export_request", "memory_export_request", "legal_document_export_request"} or target_class in {
        "dataset_artifact",
        "legal_or_policy_artifact",
    }


def _is_rollback_request(request_class: str, target_class: str) -> bool:
    return request_class in {
        "public_publish_request",
        "deployment_artifact_request",
        "artifact_marketplace_request",
        "workspace_share_request",
        "email_attachment_request",
    } or target_class in {"public_website_asset"}


def _base_packet_kwargs() -> dict[str, Any]:
    return {
        "artifact_export_packet_id": "artifact_export_packet_v1",
        "export_request_class": "report_export_request",
        "artifact_target_class": "report_artifact",
        "artifact_ref": "artifact_ref_v1",
        "artifact_summary": "Metadata-only artifact export candidate.",
        "artifact_provenance_ref": "artifact_provenance_v1",
        "document_access_packet_ref": "",
        "claim_grounding_packet_ref": "",
        "source_evidence_graph_ref": "",
        "validation_packet_ref": "",
        "owner_operator_workflow_packet_ref": "",
        "action_authority_packet_ref": "",
        "rollback_packet_ref": "",
        "export_readiness_status": "not_requested",
        "export_next_step": "no_export_metadata_only",
        "export_scope_summary": "metadata-only export boundary; no export execution",
        "destination_summary": "internal review only",
        "owner_review_required": False,
        "operator_review_required": False,
        "dual_review_required": False,
        "validation_required": False,
        "provenance_required": True,
        "document_access_required": False,
        "pii_scrub_required": False,
        "secret_review_required": False,
        "public_claim_review_required": False,
        "rollback_or_retraction_required": False,
        "privacy_status": "clear",
        "pii_risk_status": "clear",
        "secret_risk_status": "clear",
        "poison_status": "clear",
        "public_effect_possible": False,
        "external_side_effect_possible": False,
        "marketplace_effect_possible": False,
        "download_allowed": False,
        "local_save_allowed": False,
        "share_allowed": False,
        "email_attachment_allowed": False,
        "public_publish_allowed": False,
        "deployment_artifact_allowed": False,
        "marketplace_publish_allowed": False,
        "export_execution_allowed": False,
        "recommended_next_check": "inspect_export_metadata_only",
        "runtime_authority": False,
        "writes_state": False,
        "model_provider_used": False,
        "public_claim_allowed": False,
        "proof_claim_allowed": False,
        "learning_claimed": False,
        "safe_metadata": {},
    }


def _packet_like(value: Any) -> ArtifactExportPacket:
    if isinstance(value, ArtifactExportPacket):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("artifact export packet must be mapping-like")
    data = _base_packet_kwargs()
    data.update(value)
    data["safe_metadata"] = _safe_metadata_dict(data.get("safe_metadata"))
    return ArtifactExportPacket(**data)


def to_artifact_export_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            _safe_text(key): to_artifact_export_json_safe_v1(item)
            for key, item in sorted(value.items(), key=lambda item: _safe_text(item[0]))
        }
    if isinstance(value, tuple):
        return [to_artifact_export_json_safe_v1(item) for item in value]
    if isinstance(value, list):
        return [to_artifact_export_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        items = [to_artifact_export_json_safe_v1(item) for item in value]
        return sorted(items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_artifact_export_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_artifact_export_json_safe_v1(vars(value))
    return _safe_text(value)


def _derive_requirements(request_class: str, target_class: str) -> dict[str, Any]:
    owner_review_required = request_class in {"owner_handoff_request", "legal_document_export_request", "report_export_request"} or target_class in {"legal_or_policy_artifact", "report_artifact"}
    operator_review_required = request_class in {"operator_handoff_request", "code_patch_export_request"} or target_class in {"code_file", "patch_file", "configuration_file"}
    dual_review_required = request_class in {"workspace_share_request", "public_publish_request", "deployment_artifact_request", "artifact_marketplace_request"}
    validation_required = _is_validation_request(request_class, target_class)
    provenance_required = request_class != "unknown_export_request" and target_class != "unknown_artifact_target"
    document_access_required = _is_document_access_request(request_class, target_class)
    pii_scrub_required = _is_privacy_review_request(request_class, target_class)
    secret_review_required = target_class in {"configuration_file", "code_file", "patch_file"} or request_class in {"code_patch_export_request", "deployment_artifact_request"}
    public_claim_review_required = _is_publicish_request(request_class, target_class)
    rollback_or_retraction_required = _is_rollback_request(request_class, target_class)
    public_effect_possible = _is_publicish_request(request_class, target_class)
    external_side_effect_possible = _is_external_request(request_class)
    marketplace_effect_possible = request_class == "artifact_marketplace_request"
    download_allowed = False
    local_save_allowed = False
    share_allowed = False
    email_attachment_allowed = False
    public_publish_allowed = False
    deployment_artifact_allowed = False
    marketplace_publish_allowed = False
    export_execution_allowed = False

    if request_class == "metadata_review_request":
        scope_summary = "metadata-only review; no export execution"
        destination_summary = "internal review only"
        status = "candidate_ready_for_owner_review"
        next_step = "request_owner_review"
    elif request_class == "download_request":
        scope_summary = "download export review; metadata only"
        destination_summary = "internal review or owner download"
        status = "candidate_ready_for_owner_review"
        next_step = "request_owner_review"
    elif request_class == "local_save_request":
        scope_summary = "local save request blocked; helper cannot write files"
        destination_summary = "local save blocked"
        status = "blocked_missing_access_packet"
        next_step = "blocked_no_safe_export"
    elif request_class == "owner_handoff_request":
        scope_summary = "owner handoff review; no export execution"
        destination_summary = "owner handoff"
        status = "candidate_ready_for_owner_review"
        next_step = "request_owner_review"
    elif request_class == "operator_handoff_request":
        scope_summary = "operator handoff review; no export execution"
        destination_summary = "operator handoff"
        status = "candidate_ready_for_operator_review"
        next_step = "request_operator_review"
    elif request_class == "workspace_share_request":
        scope_summary = "workspace share review; external handoff gated"
        destination_summary = "workspace share blocked until review"
        status = "candidate_ready_for_owner_review"
        next_step = "defer_to_owner_operator_workflow"
    elif request_class == "email_attachment_request":
        scope_summary = "email attachment request; action authority required"
        destination_summary = "email attachment blocked"
        status = "blocked_missing_access_packet"
        next_step = "defer_to_action_authority"
    elif request_class == "public_publish_request":
        scope_summary = "public publish requires public claim and retraction review"
        destination_summary = "public publish blocked until review"
        status = "blocked_missing_rollback_or_retraction"
        next_step = "request_rollback_or_retraction_plan"
    elif request_class == "deployment_artifact_request":
        scope_summary = "deployment artifact review; validation and rollback required"
        destination_summary = "deployment artifact blocked until review"
        status = "blocked_missing_validation"
        next_step = "request_validation_packet"
    elif request_class == "legal_document_export_request":
        scope_summary = "legal document export; owner and privacy review required"
        destination_summary = "legal document handoff blocked until review"
        status = "blocked_missing_access_packet"
        next_step = "request_document_access_packet"
    elif request_class == "code_patch_export_request":
        scope_summary = "code patch export; validation and provenance required"
        destination_summary = "patch export blocked until review"
        status = "blocked_missing_validation"
        next_step = "request_validation_packet"
    elif request_class == "report_export_request":
        scope_summary = "report export; provenance required before review"
        destination_summary = "report export candidate"
        status = "candidate_ready_for_owner_review"
        next_step = "request_owner_review"
    elif request_class == "dataset_export_request":
        scope_summary = "dataset export; privacy and PII review required"
        destination_summary = "dataset export blocked until review"
        status = "blocked_missing_access_packet"
        next_step = "request_document_access_packet"
    elif request_class == "memory_export_request":
        scope_summary = "memory export; privacy boundary remains blocked"
        destination_summary = "memory export blocked"
        status = "blocked_missing_access_packet"
        next_step = "request_document_access_packet"
    elif request_class == "artifact_marketplace_request":
        scope_summary = "marketplace export; public, legal, and retraction review required"
        destination_summary = "marketplace listing blocked"
        status = "blocked_public_claim_risk"
        next_step = "request_public_claim_review"
    elif request_class == "unknown_export_request":
        scope_summary = "unknown export request; block and review"
        destination_summary = "unknown export blocked"
        status = "blocked_unknown_request"
        next_step = "blocked_no_safe_export"
    else:
        scope_summary = "metadata-only export boundary; no export execution"
        destination_summary = "internal review only"
        status = "not_requested"
        next_step = "no_export_metadata_only"

    if target_class == "unknown_artifact_target" and request_class != "unknown_export_request":
        status = "blocked_unknown_target"
        next_step = "blocked_no_safe_export"

    return {
        "owner_review_required": owner_review_required,
        "operator_review_required": operator_review_required,
        "dual_review_required": dual_review_required,
        "validation_required": validation_required,
        "provenance_required": provenance_required,
        "document_access_required": document_access_required,
        "pii_scrub_required": pii_scrub_required,
        "secret_review_required": secret_review_required,
        "public_claim_review_required": public_claim_review_required,
        "rollback_or_retraction_required": rollback_or_retraction_required,
        "public_effect_possible": public_effect_possible,
        "external_side_effect_possible": external_side_effect_possible,
        "marketplace_effect_possible": marketplace_effect_possible,
        "download_allowed": download_allowed,
        "local_save_allowed": local_save_allowed,
        "share_allowed": share_allowed,
        "email_attachment_allowed": email_attachment_allowed,
        "public_publish_allowed": public_publish_allowed,
        "deployment_artifact_allowed": deployment_artifact_allowed,
        "marketplace_publish_allowed": marketplace_publish_allowed,
        "export_execution_allowed": export_execution_allowed,
        "export_scope_summary": scope_summary,
        "destination_summary": destination_summary,
        "export_readiness_status": status,
        "export_next_step": next_step,
        "recommended_next_check": {
            "candidate_ready_for_owner_review": "request_owner_review",
            "candidate_ready_for_operator_review": "request_operator_review",
            "blocked_missing_provenance": "request_provenance_packet",
            "blocked_missing_validation": "request_validation_packet",
            "blocked_missing_access_packet": "request_document_access_packet",
            "blocked_pii_or_privacy_risk": "request_pii_scrub",
            "blocked_secret_risk": "request_secret_review",
            "blocked_poison_risk": "blocked_no_safe_export",
            "blocked_public_claim_risk": "request_public_claim_review",
            "blocked_missing_rollback_or_retraction": "request_rollback_or_retraction_plan",
            "blocked_unknown_target": "blocked_no_safe_export",
            "blocked_unknown_request": "blocked_no_safe_export",
            "metadata_only_ready": "no_export_metadata_only",
            "not_requested": "no_export_metadata_only",
        }.get(status, "blocked_no_safe_export"),
    }


def build_artifact_export_packet_v1(**kwargs: Any) -> ArtifactExportPacket:
    default_base = _base_packet_kwargs()
    explicit_request = _safe_text(kwargs.get("export_request_class") or kwargs.get("request_class"))
    if explicit_request:
        request_class = explicit_request
    else:
        request_class = classify_artifact_export_request_v1(**kwargs)
        if request_class == "unknown_export_request":
            request_class = default_base["export_request_class"]
    explicit_target = _safe_text(kwargs.get("artifact_target_class") or kwargs.get("target_class"))
    if explicit_target:
        target_class = explicit_target
    else:
        target_class = classify_artifact_export_target_v1(**kwargs)
        if target_class == "unknown_artifact_target":
            target_class = default_base["artifact_target_class"]
    base = _base_packet_kwargs()
    base.update(
        {
            "artifact_export_packet_id": kwargs.get("artifact_export_packet_id", "artifact_export_packet_v1"),
            "export_request_class": request_class,
            "artifact_target_class": target_class,
            "artifact_ref": kwargs.get("artifact_ref", "artifact_ref_v1"),
            "artifact_summary": kwargs.get("artifact_summary", "Metadata-only artifact export candidate."),
            "artifact_provenance_ref": kwargs.get("artifact_provenance_ref", "artifact_provenance_v1"),
            "document_access_packet_ref": kwargs.get("document_access_packet_ref", ""),
            "claim_grounding_packet_ref": kwargs.get("claim_grounding_packet_ref", ""),
            "source_evidence_graph_ref": kwargs.get("source_evidence_graph_ref", ""),
            "validation_packet_ref": kwargs.get("validation_packet_ref", ""),
            "owner_operator_workflow_packet_ref": kwargs.get("owner_operator_workflow_packet_ref", ""),
            "action_authority_packet_ref": kwargs.get("action_authority_packet_ref", ""),
            "rollback_packet_ref": kwargs.get("rollback_packet_ref", ""),
            "privacy_status": kwargs.get("privacy_status", "clear"),
            "pii_risk_status": kwargs.get("pii_risk_status", "clear"),
            "secret_risk_status": kwargs.get("secret_risk_status", "clear"),
            "poison_status": kwargs.get("poison_status", "clear"),
            "runtime_authority": kwargs.get("runtime_authority", False),
            "writes_state": kwargs.get("writes_state", False),
            "model_provider_used": kwargs.get("model_provider_used", False),
            "public_claim_allowed": kwargs.get("public_claim_allowed", False),
            "proof_claim_allowed": kwargs.get("proof_claim_allowed", False),
            "learning_claimed": kwargs.get("learning_claimed", False),
            "safe_metadata": kwargs.get("safe_metadata"),
        }
    )
    base["safe_metadata"] = _safe_metadata_dict(base.get("safe_metadata"))
    base.update(_derive_requirements(request_class, target_class))
    return evaluate_artifact_export_readiness_v1(ArtifactExportPacket(**base))


def _derive_status_from_risk(packet: ArtifactExportPacket, request_class: str, target_class: str) -> tuple[str, str]:
    if request_class == "unknown_export_request":
        return "blocked_unknown_request", "blocked_no_safe_export"
    if target_class == "unknown_artifact_target":
        return "blocked_unknown_target", "blocked_no_safe_export"

    if _is_risk(packet.secret_risk_status) and not _is_clear(packet.secret_risk_status):
        return "blocked_secret_risk", "request_secret_review"
    if _is_risk(packet.poison_status) and not _is_clear(packet.poison_status):
        return "blocked_poison_risk", "blocked_no_safe_export"
    if (packet.privacy_status and not _is_clear(packet.privacy_status)) or (packet.pii_risk_status and not _is_clear(packet.pii_risk_status)):
        return "blocked_pii_or_privacy_risk", "request_pii_scrub"
    return "", ""


def _missing_requirement_status(packet: ArtifactExportPacket, request_class: str, target_class: str) -> tuple[str, str]:
    if packet.provenance_required and not packet.artifact_provenance_ref.strip():
        return "blocked_missing_provenance", "request_provenance_packet"
    if packet.document_access_required and not packet.document_access_packet_ref.strip():
        return "blocked_missing_access_packet", "request_document_access_packet"
    if packet.validation_required and not packet.validation_packet_ref.strip():
        return "blocked_missing_validation", "request_validation_packet"
    if packet.public_claim_review_required and not packet.claim_grounding_packet_ref.strip() and _is_publicish_request(request_class, target_class):
        return "blocked_public_claim_risk", "request_public_claim_review"
    if packet.rollback_or_retraction_required and not packet.rollback_packet_ref.strip():
        return "blocked_missing_rollback_or_retraction", "request_rollback_or_retraction_plan"
    return "", ""


def evaluate_artifact_export_readiness_v1(packet: Any) -> ArtifactExportPacket:
    pkt = _packet_like(packet)
    request_class = pkt.export_request_class if pkt.export_request_class in ALLOWED_EXPORT_REQUEST_CLASSES_V1 else classify_artifact_export_request_v1(**asdict(pkt))
    target_class = pkt.artifact_target_class if pkt.artifact_target_class in ALLOWED_ARTIFACT_TARGET_CLASSES_V1 else classify_artifact_export_target_v1(**asdict(pkt))

    derived = _derive_requirements(request_class, target_class)
    status, next_step = derived["export_readiness_status"], derived["export_next_step"]

    risk_status, risk_next = _derive_status_from_risk(pkt, request_class, target_class)
    if risk_status:
        status, next_step = risk_status, risk_next
    else:
        missing_status, missing_next = _missing_requirement_status(pkt, request_class, target_class)
        if missing_status:
            status, next_step = missing_status, missing_next

    if request_class == "public_publish_request" and not pkt.public_claim_review_required:
        status, next_step = "blocked_public_claim_risk", "request_public_claim_review"
    if request_class == "artifact_marketplace_request" and status not in {"blocked_secret_risk", "blocked_poison_risk", "blocked_pii_or_privacy_risk"}:
        if not pkt.public_claim_review_required:
            status, next_step = "blocked_public_claim_risk", "request_public_claim_review"
        elif status.startswith("candidate"):
            status, next_step = "candidate_ready_for_owner_review", "request_dual_review"
    if request_class == "deployment_artifact_request" and status.startswith("candidate"):
        status, next_step = "candidate_ready_for_operator_review", "request_validation_packet"
    if request_class == "code_patch_export_request" and status.startswith("candidate"):
        status, next_step = "candidate_ready_for_operator_review", "request_validation_packet"
    if request_class == "email_attachment_request":
        status, next_step = "blocked_missing_access_packet", "defer_to_action_authority"
    if request_class == "workspace_share_request" and status.startswith("candidate"):
        status, next_step = "candidate_ready_for_owner_review", "defer_to_owner_operator_workflow"
    if request_class == "owner_handoff_request" and status.startswith("candidate"):
        status, next_step = "candidate_ready_for_owner_review", "request_owner_review"
    if request_class == "operator_handoff_request" and status.startswith("candidate"):
        status, next_step = "candidate_ready_for_operator_review", "request_operator_review"

    if request_class == "local_save_request":
        status, next_step = "blocked_missing_access_packet", "blocked_no_safe_export"
    if request_class == "memory_export_request" and status.startswith("candidate"):
        status, next_step = "blocked_missing_access_packet", "request_document_access_packet"

    pkt = replace(
        pkt,
        export_request_class=request_class,
        artifact_target_class=target_class,
        export_readiness_status=status,
        export_next_step=next_step,
        owner_review_required=derived["owner_review_required"],
        operator_review_required=derived["operator_review_required"],
        dual_review_required=derived["dual_review_required"],
        validation_required=derived["validation_required"],
        provenance_required=derived["provenance_required"],
        document_access_required=derived["document_access_required"],
        pii_scrub_required=derived["pii_scrub_required"],
        secret_review_required=derived["secret_review_required"],
        public_claim_review_required=derived["public_claim_review_required"],
        rollback_or_retraction_required=derived["rollback_or_retraction_required"],
        public_effect_possible=derived["public_effect_possible"],
        external_side_effect_possible=derived["external_side_effect_possible"],
        marketplace_effect_possible=derived["marketplace_effect_possible"],
        download_allowed=derived["download_allowed"],
        local_save_allowed=derived["local_save_allowed"],
        share_allowed=derived["share_allowed"],
        email_attachment_allowed=derived["email_attachment_allowed"],
        public_publish_allowed=derived["public_publish_allowed"],
        deployment_artifact_allowed=derived["deployment_artifact_allowed"],
        marketplace_publish_allowed=derived["marketplace_publish_allowed"],
        export_execution_allowed=derived["export_execution_allowed"],
        export_scope_summary=derived["export_scope_summary"],
        destination_summary=derived["destination_summary"],
        recommended_next_check={
            "metadata_only_ready": "no_export_metadata_only",
            "candidate_ready_for_owner_review": "request_owner_review",
            "candidate_ready_for_operator_review": "request_operator_review",
            "blocked_missing_provenance": "request_provenance_packet",
            "blocked_missing_validation": "request_validation_packet",
            "blocked_missing_access_packet": "request_document_access_packet",
            "blocked_pii_or_privacy_risk": "request_pii_scrub",
            "blocked_secret_risk": "request_secret_review",
            "blocked_poison_risk": "blocked_no_safe_export",
            "blocked_public_claim_risk": "request_public_claim_review",
            "blocked_missing_rollback_or_retraction": "request_rollback_or_retraction_plan",
            "blocked_unknown_target": "blocked_no_safe_export",
            "blocked_unknown_request": "blocked_no_safe_export",
            "not_requested": "no_export_metadata_only",
        }.get(status, "blocked_no_safe_export"),
    )
    return pkt


def select_artifact_export_next_step_v1(packet: Any) -> str:
    pkt = _packet_like(packet)
    if pkt.export_next_step in ALLOWED_ARTIFACT_EXPORT_NEXT_STEP_CLASSES_V1:
        return pkt.export_next_step
    mapping = {
        "metadata_only_ready": "no_export_metadata_only",
        "candidate_ready_for_owner_review": "request_owner_review",
        "candidate_ready_for_operator_review": "request_operator_review",
        "blocked_missing_provenance": "request_provenance_packet",
        "blocked_missing_validation": "request_validation_packet",
        "blocked_missing_access_packet": "request_document_access_packet",
        "blocked_pii_or_privacy_risk": "request_pii_scrub",
        "blocked_secret_risk": "request_secret_review",
        "blocked_poison_risk": "blocked_no_safe_export",
        "blocked_public_claim_risk": "request_public_claim_review",
        "blocked_missing_rollback_or_retraction": "request_rollback_or_retraction_plan",
        "blocked_unknown_target": "blocked_no_safe_export",
        "blocked_unknown_request": "blocked_no_safe_export",
        "not_requested": "no_export_metadata_only",
        "unknown_status": "unknown_next_step",
    }
    return mapping.get(pkt.export_readiness_status, "unknown_next_step")


def summarize_artifact_export_packet_v1(packet: Any) -> ArtifactExportSummary:
    pkt = _packet_like(packet)
    return ArtifactExportSummary(
        summary_type=SUMMARY_TYPE_V1,
        artifact_export_packet_id=pkt.artifact_export_packet_id,
        export_request_class=pkt.export_request_class,
        artifact_target_class=pkt.artifact_target_class,
        export_readiness_status=pkt.export_readiness_status,
        export_next_step=pkt.export_next_step,
        export_scope_summary=pkt.export_scope_summary,
        destination_summary=pkt.destination_summary,
        owner_review_required=pkt.owner_review_required,
        operator_review_required=pkt.operator_review_required,
        dual_review_required=pkt.dual_review_required,
        validation_required=pkt.validation_required,
        provenance_required=pkt.provenance_required,
        document_access_required=pkt.document_access_required,
        pii_scrub_required=pkt.pii_scrub_required,
        secret_review_required=pkt.secret_review_required,
        public_claim_review_required=pkt.public_claim_review_required,
        rollback_or_retraction_required=pkt.rollback_or_retraction_required,
        public_effect_possible=pkt.public_effect_possible,
        external_side_effect_possible=pkt.external_side_effect_possible,
        marketplace_effect_possible=pkt.marketplace_effect_possible,
        export_execution_allowed=pkt.export_execution_allowed,
        recommended_next_check=pkt.recommended_next_check,
    )


def validate_artifact_export_packet_v1(packet: Any) -> bool:
    pkt = _packet_like(packet)

    hidden = _contains_forbidden_field(pkt)
    if hidden:
        raise ValidationError(f"hidden_private_or_secret_like_fields_not_allowed:{hidden}")

    if pkt.artifact_export_packet_id.strip() == "" or pkt.artifact_ref.strip() == "":
        raise ValidationError("missing_required_export_identity")

    if pkt.export_request_class not in ALLOWED_EXPORT_REQUEST_CLASSES_V1:
        raise ValidationError("unknown_request_promoted_as_valid")
    if pkt.export_request_class == "unknown_export_request":
        raise ValidationError("unknown_request_promoted_as_valid")
    if pkt.artifact_target_class not in ALLOWED_ARTIFACT_TARGET_CLASSES_V1:
        raise ValidationError("unknown_target_promoted_as_valid")
    if pkt.artifact_target_class == "unknown_artifact_target":
        raise ValidationError("unknown_target_promoted_as_valid")
    if pkt.export_readiness_status not in ALLOWED_EXPORT_READINESS_STATUSES_V1:
        raise ValidationError("unknown_status_promoted_as_valid")
    if pkt.export_next_step not in ALLOWED_ARTIFACT_EXPORT_NEXT_STEP_CLASSES_V1:
        raise ValidationError("unknown_next_step_promoted_as_valid")

    for field_name in (
        "download_allowed",
        "local_save_allowed",
        "share_allowed",
        "email_attachment_allowed",
        "public_publish_allowed",
        "deployment_artifact_allowed",
        "marketplace_publish_allowed",
        "export_execution_allowed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "proof_claim_allowed",
        "learning_claimed",
    ):
        if getattr(pkt, field_name):
            raise ValidationError(f"{field_name}_must_be_false")

    if not pkt.export_scope_summary.strip():
        raise ValidationError("export_without_scope_summary")
    if not pkt.destination_summary.strip():
        raise ValidationError("export_without_destination_summary")

    if pkt.export_readiness_status == "unknown_status":
        raise ValidationError("unknown_status_promoted_as_valid")
    if pkt.export_next_step == "unknown_next_step":
        raise ValidationError("unknown_next_step_promoted_as_valid")

    if pkt.provenance_required and not pkt.artifact_provenance_ref.strip():
        raise ValidationError("missing_provenance_when_required")
    if pkt.document_access_required and not pkt.document_access_packet_ref.strip():
        raise ValidationError("missing_document_access_when_required")
    if pkt.validation_required and not pkt.validation_packet_ref.strip():
        raise ValidationError("missing_validation_when_required")
    if pkt.public_effect_possible and not pkt.public_claim_review_required:
        raise ValidationError("public_export_without_public_claim_review")
    if pkt.rollback_or_retraction_required and not pkt.rollback_packet_ref.strip():
        raise ValidationError("missing_rollback_or_retraction_when_required")
    if pkt.public_effect_possible and not pkt.rollback_or_retraction_required:
        raise ValidationError("public_export_without_rollback_or_retraction_requirement")
    if pkt.external_side_effect_possible and not pkt.rollback_or_retraction_required:
        raise ValidationError("external_export_without_rollback_or_retraction_requirement")
    if pkt.marketplace_effect_possible and not pkt.rollback_or_retraction_required:
        raise ValidationError("marketplace_export_without_rollback_or_retraction_requirement")
    if pkt.deployment_artifact_allowed:
        raise ValidationError("deployment_artifact_must_remain_false")
    if _is_risk(pkt.secret_risk_status) and not _is_clear(pkt.secret_risk_status):
        raise ValidationError("secret_risk_must_be_clear_for_export_progression")
    if (pkt.privacy_status and not _is_clear(pkt.privacy_status)) or (pkt.pii_risk_status and not _is_clear(pkt.pii_risk_status)):
        if pkt.document_access_required or pkt.pii_scrub_required or pkt.public_effect_possible or pkt.marketplace_effect_possible:
            raise ValidationError("private_or_pii_risk_blocks_export_progression")
    if _is_risk(pkt.poison_status) and not _is_clear(pkt.poison_status):
        raise ValidationError("poison_risk_blocks_export_progression")
    if _contains_claim_marker(pkt.artifact_summary) or _contains_claim_marker(pkt.export_scope_summary) or _contains_claim_marker(pkt.destination_summary) or _contains_claim_marker(pkt.safe_metadata):
        raise ValidationError("correctness_or_public_readiness_claims_not_allowed")
    if _contains_risk_marker(pkt.artifact_summary) and _is_risk(pkt.poison_status) and not _is_clear(pkt.poison_status):
        raise ValidationError("secret_or_poison_risk_must_remain_visible")

    return True


def _example_base(**kwargs: Any) -> ArtifactExportPacket:
    return build_artifact_export_packet_v1(**kwargs)


def build_initial_artifact_export_examples_v1() -> list[ArtifactExportPacket]:
    examples: list[ArtifactExportPacket] = [
        _example_base(
            artifact_export_packet_id="metadata_only_markdown_report_candidate_v1",
            export_request_class="report_export_request",
            artifact_target_class="markdown_document",
            artifact_ref="artifact_md_report_v1",
            artifact_summary="Metadata-only markdown report candidate for owner review.",
            artifact_provenance_ref="artifact_provenance_md_report_v1",
            export_scope_summary="Metadata-only markdown report; no export execution.",
            destination_summary="internal owner review only",
            owner_operator_workflow_packet_ref="workflow_owner_review_v1",
            claim_grounding_packet_ref="claim_grounding_md_report_v1",
            source_evidence_graph_ref="source_graph_md_report_v1",
            export_readiness_status="candidate_ready_for_owner_review",
            export_next_step="request_owner_review",
        ),
        _example_base(
            artifact_export_packet_id="local_save_blocked_v1",
            export_request_class="local_save_request",
            artifact_target_class="markdown_document",
            artifact_ref="artifact_local_save_v1",
            artifact_summary="Local save request remains blocked because helper cannot write files.",
            artifact_provenance_ref="artifact_provenance_local_save_v1",
            export_scope_summary="Local save blocked by metadata-only boundary.",
            destination_summary="local save blocked",
            export_readiness_status="blocked_missing_access_packet",
            export_next_step="blocked_no_safe_export",
        ),
        _example_base(
            artifact_export_packet_id="owner_handoff_requires_provenance_v1",
            export_request_class="owner_handoff_request",
            artifact_target_class="report_artifact",
            artifact_ref="artifact_owner_handoff_v1",
            artifact_summary="Owner handoff request requires provenance.",
            artifact_provenance_ref="artifact_provenance_owner_handoff_v1",
            export_scope_summary="Owner handoff review only; no export execution.",
            destination_summary="owner handoff",
            owner_review_required=True,
            export_readiness_status="candidate_ready_for_owner_review",
            export_next_step="request_owner_review",
        ),
        _example_base(
            artifact_export_packet_id="email_attachment_requires_action_authority_v1",
            export_request_class="email_attachment_request",
            artifact_target_class="pdf_document",
            artifact_ref="artifact_email_attachment_v1",
            artifact_summary="Email attachment request requires action authority and remains blocked.",
            artifact_provenance_ref="artifact_provenance_email_attachment_v1",
            action_authority_packet_ref="",
            export_scope_summary="Email attachment blocked until action authority exists.",
            destination_summary="email attachment blocked",
            export_readiness_status="blocked_missing_access_packet",
            export_next_step="defer_to_action_authority",
            external_side_effect_possible=True,
            rollback_or_retraction_required=True,
        ),
        _example_base(
            artifact_export_packet_id="public_publish_requires_review_and_retraction_v1",
            export_request_class="public_publish_request",
            artifact_target_class="public_website_asset",
            artifact_ref="artifact_public_publish_v1",
            artifact_summary="Public publish request requires public-claim review and retraction plan.",
            artifact_provenance_ref="artifact_provenance_public_publish_v1",
            claim_grounding_packet_ref="claim_grounding_public_publish_v1",
            rollback_packet_ref="rollback_public_publish_v1",
            public_claim_review_required=True,
            rollback_or_retraction_required=True,
            public_effect_possible=True,
            export_scope_summary="Public publish review only; no publication.",
            destination_summary="public publish blocked until review",
            export_readiness_status="candidate_ready_for_owner_review",
            export_next_step="request_public_claim_review",
        ),
        _example_base(
            artifact_export_packet_id="deployment_artifact_requires_validation_and_rollback_v1",
            export_request_class="deployment_artifact_request",
            artifact_target_class="configuration_file",
            artifact_ref="artifact_deployment_v1",
            artifact_summary="Deployment artifact requires validation and rollback plan.",
            artifact_provenance_ref="artifact_provenance_deployment_v1",
            validation_packet_ref="validation_deployment_v1",
            rollback_packet_ref="rollback_deployment_v1",
            validation_required=True,
            rollback_or_retraction_required=True,
            export_scope_summary="Deployment artifact review only; no deployment.",
            destination_summary="deployment artifact blocked until review",
            export_readiness_status="candidate_ready_for_operator_review",
            export_next_step="request_validation_packet",
        ),
        _example_base(
            artifact_export_packet_id="code_patch_export_requires_validation_and_provenance_v1",
            export_request_class="code_patch_export_request",
            artifact_target_class="patch_file",
            artifact_ref="artifact_patch_v1",
            artifact_summary="Code patch export requires validation and patch feedback provenance.",
            artifact_provenance_ref="artifact_provenance_patch_v1",
            patch_feedback_packet_ref="patch_feedback_patch_v1",
            validation_packet_ref="validation_patch_v1",
            validation_required=True,
            owner_operator_workflow_packet_ref="workflow_patch_review_v1",
            export_scope_summary="Patch export review only; no patch application.",
            destination_summary="patch export blocked until review",
            export_readiness_status="candidate_ready_for_operator_review",
            export_next_step="request_validation_packet",
        ),
        _example_base(
            artifact_export_packet_id="legal_document_requires_owner_and_privacy_review_v1",
            export_request_class="legal_document_export_request",
            artifact_target_class="legal_or_policy_artifact",
            artifact_ref="artifact_legal_v1",
            artifact_summary="Legal document export requires owner review and privacy check.",
            artifact_provenance_ref="artifact_provenance_legal_v1",
            document_access_packet_ref="document_access_legal_v1",
            privacy_status="clear",
            pii_risk_status="clear",
            owner_review_required=True,
            document_access_required=True,
            pii_scrub_required=True,
            export_scope_summary="Legal/policy review only; no handoff.",
            destination_summary="legal document blocked until review",
            export_readiness_status="candidate_ready_for_owner_review",
            export_next_step="request_document_access_packet",
        ),
        _example_base(
            artifact_export_packet_id="dataset_export_requires_pii_scrub_and_document_access_v1",
            export_request_class="dataset_export_request",
            artifact_target_class="dataset_artifact",
            artifact_ref="artifact_dataset_v1",
            artifact_summary="Dataset export requires PII scrub and document access packet.",
            artifact_provenance_ref="artifact_provenance_dataset_v1",
            document_access_packet_ref="document_access_dataset_v1",
            privacy_status="clear",
            pii_risk_status="clear",
            document_access_required=True,
            pii_scrub_required=True,
            operator_review_required=True,
            export_scope_summary="Dataset export review only; no data export.",
            destination_summary="dataset export blocked until review",
            export_readiness_status="candidate_ready_for_operator_review",
            export_next_step="request_document_access_packet",
        ),
        _example_base(
            artifact_export_packet_id="memory_export_blocked_v1",
            export_request_class="memory_export_request",
            artifact_target_class="json_metadata",
            artifact_ref="artifact_memory_v1",
            artifact_summary="Memory export requires a privacy boundary and remains blocked.",
            artifact_provenance_ref="artifact_provenance_memory_v1",
            privacy_status="blocked",
            pii_risk_status="blocked",
            document_access_required=True,
            pii_scrub_required=True,
            export_scope_summary="Memory export blocked by privacy boundary.",
            destination_summary="memory export blocked",
            export_readiness_status="blocked_missing_access_packet",
            export_next_step="request_document_access_packet",
        ),
        _example_base(
            artifact_export_packet_id="image_asset_requires_provenance_and_rights_summary_v1",
            export_request_class="report_export_request",
            artifact_target_class="image_asset",
            artifact_ref="artifact_image_v1",
            artifact_summary="Image asset export requires provenance and rights/source summary.",
            artifact_provenance_ref="artifact_provenance_image_v1",
            claim_grounding_packet_ref="claim_grounding_image_v1",
            source_evidence_graph_ref="source_graph_image_v1",
            export_scope_summary="Image asset review only; no export.",
            destination_summary="image asset candidate",
            export_readiness_status="candidate_ready_for_owner_review",
            export_next_step="request_owner_review",
        ),
        _example_base(
            artifact_export_packet_id="configuration_file_requires_validation_and_secret_review_v1",
            export_request_class="report_export_request",
            artifact_target_class="configuration_file",
            artifact_ref="artifact_config_v1",
            artifact_summary="Configuration file export requires validation and secret review.",
            artifact_provenance_ref="artifact_provenance_config_v1",
            validation_packet_ref="validation_config_v1",
            secret_review_required=True,
            secret_risk_status="clear",
            validation_required=True,
            operator_review_required=True,
            export_scope_summary="Configuration export review only; no config write.",
            destination_summary="configuration export blocked until review",
            export_readiness_status="candidate_ready_for_operator_review",
            export_next_step="request_validation_packet",
        ),
        _example_base(
            artifact_export_packet_id="artifact_marketplace_blocked_v1",
            export_request_class="artifact_marketplace_request",
            artifact_target_class="public_website_asset",
            artifact_ref="artifact_marketplace_v1",
            artifact_summary="Artifact marketplace request requires public, marketplace, and payment review and remains blocked.",
            artifact_provenance_ref="artifact_provenance_marketplace_v1",
            public_effect_possible=True,
            marketplace_effect_possible=True,
            rollback_or_retraction_required=True,
            export_scope_summary="Marketplace listing blocked pending review.",
            destination_summary="marketplace listing blocked",
            export_readiness_status="blocked_public_claim_risk",
            export_next_step="request_public_claim_review",
        ),
        _example_base(
            artifact_export_packet_id="poison_risk_artifact_blocked_v1",
            export_request_class="report_export_request",
            artifact_target_class="report_artifact",
            artifact_ref="artifact_poison_v1",
            artifact_summary="Poison-risk artifact is blocked.",
            artifact_provenance_ref="artifact_provenance_poison_v1",
            poison_status="poisoned",
            export_scope_summary="Poison-risk report blocked.",
            destination_summary="poison-risk artifact blocked",
            export_readiness_status="blocked_poison_risk",
            export_next_step="blocked_no_safe_export",
        ),
        _example_base(
            artifact_export_packet_id="unknown_target_request_fails_closed_v1",
            export_request_class="unknown_export_request",
            artifact_target_class="unknown_artifact_target",
            artifact_ref="artifact_unknown_v1",
            artifact_summary="Unknown target and request fail closed.",
            artifact_provenance_ref="",
            export_scope_summary="Unknown export request blocked.",
            destination_summary="unknown export blocked",
            export_readiness_status="blocked_unknown_request",
            export_next_step="blocked_no_safe_export",
        ),
    ]
    return examples
