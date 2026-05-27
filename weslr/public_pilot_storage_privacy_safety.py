"""Public pilot storage/privacy safety helpers V1.

Pure helper functions for the reviewed public-pilot storage/privacy boundary.
No file IO, provider calls, queue processing, or runtime wiring is performed here.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

REDACTION_TOKEN = "[redacted_public_pilot_private_text]"

CONSENT_FIELDS = (
    "storage_consent",
    "contact_storage_consent",
    "feedback_storage_consent",
    "suggestion_storage_consent",
    "project_review_storage_consent",
    "upstream_public_sharing_consent",
    "testimonial_consent",
    "ocw_operator_access_consent",
    "revoked",
)

DENIED_AUTHORITY_FIELDS = (
    "contact_export",
    "public_testimonial_use",
    "upstream_submission",
    "queue_processing",
    "runtime_behavior",
    "final_answer_behavior",
    "public_launch",
    "product_readiness_claim",
    "intelligence_claim",
    "turing_claim",
    "certification_claim",
    "roadmap_approval",
    "promotion_approval",
    "release_gate_bypass",
)

RAW_PRIVATE_TEXT_PATTERNS = (
    re.compile(r"\b(secret|password|passwd|token|api[_ -]?key|credential|private key)\b", re.IGNORECASE),
    re.compile(r"\b(customer data|private project|internal project|confidential|proprietary)\b", re.IGNORECASE),
    re.compile(r"\b(address|phone number|passport|social security|ssn)\b", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{8,}"),
    re.compile(r"bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
)


def _json_safe(value: Any) -> bool:
    try:
        json.dumps(value, sort_keys=True)
        return True
    except (TypeError, ValueError):
        return False


def _bool(value: Any) -> bool:
    return value is True


def normalize_public_pilot_consent_metadata_v1(metadata: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    """Return JSON-safe consent metadata with sensitive authorities false by default."""
    source = dict(metadata or {})
    source.update(overrides)
    normalized = {field: _bool(source.get(field, False)) for field in CONSENT_FIELDS}
    normalized["schema_version"] = str(source.get("schema_version", "public_pilot_consent_metadata_v1"))
    normalized["consent_scope"] = str(source.get("consent_scope", "public_pilot_storage"))
    normalized["denied_authority"] = dict(source.get("denied_authority") or {})
    for field in DENIED_AUTHORITY_FIELDS:
        normalized["denied_authority"][field] = _bool(normalized["denied_authority"].get(field, False))
    return normalized


def validate_public_pilot_denied_authority_v1(denied_authority: dict[str, Any] | None) -> list[str]:
    """Validate denied authority fields. Missing fields are treated as denied/false."""
    errors: list[str] = []
    if denied_authority is None:
        return errors
    if not isinstance(denied_authority, dict) or not _json_safe(denied_authority):
        return ["denied authority metadata must be JSON-safe object"]
    for field in DENIED_AUTHORITY_FIELDS:
        if denied_authority.get(field) is True:
            errors.append(f"denied authority field must remain false: {field}")
    return errors


def validate_public_pilot_consent_metadata_v1(
    metadata: dict[str, Any] | None,
    *,
    require_contact_storage: bool = False,
    require_feedback_storage: bool = False,
    require_suggestion_storage: bool = False,
    require_project_review_storage: bool = False,
) -> list[str]:
    """Validate public-pilot consent metadata and fail closed on missing/revoked consent."""
    if not isinstance(metadata, dict):
        return ["public pilot consent metadata is required"]
    if not _json_safe(metadata):
        return ["public pilot consent metadata must be JSON-safe"]

    normalized = normalize_public_pilot_consent_metadata_v1(metadata)
    errors: list[str] = []
    if normalized["revoked"]:
        errors.append("public pilot consent has been revoked")
    if not normalized["storage_consent"]:
        errors.append("storage consent is required for public-pilot storage")
    if require_contact_storage and not normalized["contact_storage_consent"]:
        errors.append("contact storage consent is required for public-pilot contact storage")
    if require_feedback_storage and not normalized["feedback_storage_consent"]:
        errors.append("feedback storage consent is required for public-pilot feedback storage")
    if require_suggestion_storage and not normalized["suggestion_storage_consent"]:
        errors.append("suggestion storage consent is required for public-pilot suggestion storage")
    if require_project_review_storage and not normalized["project_review_storage_consent"]:
        errors.append("project-review storage consent is required for public-pilot project-review storage")
    errors.extend(validate_public_pilot_denied_authority_v1(normalized.get("denied_authority")))
    return errors


def require_public_pilot_storage_consent_v1(metadata: dict[str, Any] | None, **requirements: Any) -> dict[str, Any]:
    """Return normalized metadata or raise ValueError on unsafe/missing consent."""
    errors = validate_public_pilot_consent_metadata_v1(metadata, **requirements)
    if errors:
        raise ValueError("; ".join(errors))
    return normalize_public_pilot_consent_metadata_v1(metadata)


def _contains_raw_private_text(value: str) -> bool:
    return any(pattern.search(value) for pattern in RAW_PRIVATE_TEXT_PATTERNS)


def reject_public_pilot_raw_private_text_v1(value: Any, *, field_name: str = "text") -> None:
    """Raise if raw private markers are present in public-pilot text."""
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text or null")
    if _contains_raw_private_text(value):
        raise ValueError(f"{field_name} contains raw private/sensitive markers")


def redact_public_pilot_text_v1(value: Any, *, max_length: int = 160) -> str:
    """Return a bounded redacted text summary without exposing raw private markers."""
    if value is None:
        return ""
    text = str(value)
    for pattern in RAW_PRIVATE_TEXT_PATTERNS:
        text = pattern.sub(REDACTION_TOKEN, text)
    text = " ".join(text.split())
    if len(text) > max_length:
        text = text[: max_length - 1].rstrip() + "…"
    return text


def safe_public_pilot_summary_v1(payload: dict[str, Any] | None, *, text_fields: tuple[str, ...] = ()) -> dict[str, Any]:
    """Return metadata/count-only summary with optional redacted field presence."""
    data = dict(payload or {})
    summary: dict[str, Any] = {
        "schema_version": "public_pilot_safe_summary_v1",
        "field_count": len(data),
        "text_field_count": 0,
        "redacted_text_fields": [],
        "contains_raw_values": False,
        "summary_mode": "metadata_redacted_count_only",
    }
    for field in text_fields:
        if data.get(field) not in (None, ""):
            summary["text_field_count"] += 1
            summary["redacted_text_fields"].append(field)
    return summary


def reject_public_pilot_dot_weslr_path_v1(path: str | Path, *, public_pilot_mode: bool = True) -> None:
    """Fail closed on .weslr path authority in public-pilot mode without touching the path."""
    if not public_pilot_mode:
        return
    path_text = str(path)
    parts = Path(path_text).parts
    if ".weslr" in parts or path_text.startswith(".weslr/") or "/.weslr/" in path_text or path_text.endswith("/.weslr"):
        raise ValueError(".weslr path authority is denied for public-pilot flows")


def minimize_public_pilot_identifier_v1(value: str | None, *, label: str) -> str | None:
    """Return a stable non-raw identifier label for public-pilot-safe writes."""
    if value in (None, ""):
        return None
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
    return f"{label}_sha256:{digest}"


QUARANTINED_PUBLIC_PILOT_SURFACE_LABELS = (
    "continuity/suggestion_box/" "requests" ".json",
    "continuity/suggestion_box/" "continuity" ".json",
    "continuity/pilot_signals/" "user_events" ".json",
    "continuity/pilot_signals/" "interventions" ".json",
    "continuity/pilot_signals/" "redteam_events" ".json",
    "review_queue" ".json",
    ".weslr/advisor_review_queue" ".jsonl",
)


def validate_public_pilot_quarantine_authorization_v1(metadata: dict[str, Any] | None) -> list[str]:
    """Validate quarantine bypass metadata without IO; missing metadata fails closed."""
    if not isinstance(metadata, dict):
        return ["public pilot quarantine authorization metadata is required"]
    if not _json_safe(metadata):
        return ["public pilot quarantine authorization metadata must be JSON-safe"]
    errors = validate_public_pilot_denied_authority_v1(metadata.get("denied_authority"))
    if metadata.get("revoked") is True:
        errors.append("public pilot quarantine authorization has been revoked")
    if metadata.get("test_safe_storage") is not True:
        errors.append("test_safe_storage authorization is required")
    if metadata.get("synthetic_temp_path") is not True:
        errors.append("synthetic_temp_path authorization is required")
    for field in ("raw_display", "raw_export", "queue_processing", "promotion", "runtime_behavior", "final_answer_behavior", "public_launch"):
        if metadata.get(field) is True:
            errors.append(f"quarantine authority must remain false: {field}")
    return errors


def _public_pilot_surface_label(path_or_surface: str | Path) -> str:
    return str(path_or_surface).replace("\\", "/")


def is_public_pilot_storage_surface_quarantined_v1(
    path_or_surface: str | Path,
    *,
    public_pilot_mode: bool = False,
    authorization_metadata: dict[str, Any] | None = None,
) -> bool:
    """Return True when a public-pilot storage surface must fail closed."""
    if not public_pilot_mode:
        return False
    label = _public_pilot_surface_label(path_or_surface)
    if ".weslr" in Path(label).parts or label.startswith(".weslr/") or "/.weslr/" in label:
        return True
    normalized = label.lstrip("./")
    risky = (
        normalized in QUARANTINED_PUBLIC_PILOT_SURFACE_LABELS
        or normalized == "continuity/suggestion_box"
        or normalized.startswith("continuity/suggestion_box/")
        or normalized == "continuity/pilot_signals"
        or normalized.startswith("continuity/pilot_signals/")
        or normalized.endswith("review_queue.json")
    )
    if not risky:
        return False
    return bool(validate_public_pilot_quarantine_authorization_v1(authorization_metadata))


def build_public_pilot_quarantine_result_v1(
    surface: str,
    reason_labels: list[str] | tuple[str, ...],
    *,
    path_label: str | None = None,
) -> dict[str, Any]:
    """Return JSON-safe blocked/quarantined metadata with no raw record values."""
    safe_reasons = [str(reason) for reason in reason_labels]
    return {
        "schema_version": "public_pilot_user_data_storage_quarantine_v1",
        "surface": str(surface),
        "path_label": str(path_label or surface),
        "quarantined": True,
        "blocked": True,
        "reason_labels": safe_reasons,
        "raw_records_read": False,
        "raw_records_included": False,
        "raw_display_allowed": False,
        "raw_export_allowed": False,
        "queue_processing_allowed": False,
        "promotion_allowed": False,
        "runtime_behavior_allowed": False,
        "final_answer_behavior_allowed": False,
        "public_launch_allowed": False,
    }


def require_public_pilot_storage_surface_not_quarantined_v1(
    path_or_surface: str | Path,
    *,
    public_pilot_mode: bool = False,
    authorization_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Raise ValueError when a public-pilot surface is quarantined."""
    if is_public_pilot_storage_surface_quarantined_v1(
        path_or_surface,
        public_pilot_mode=public_pilot_mode,
        authorization_metadata=authorization_metadata,
    ):
        result = build_public_pilot_quarantine_result_v1(
            "public_pilot_user_data_storage",
            ["public_pilot_storage_surface_quarantined"],
            path_label=_public_pilot_surface_label(path_or_surface),
        )
        raise ValueError(json.dumps(result, sort_keys=True))
    return {"quarantined": False, "blocked": False, "path_label": _public_pilot_surface_label(path_or_surface)}

PUBLIC_PILOT_REMOVAL_KINDS = ("deletion", "revocation")
PUBLIC_PILOT_REMOVAL_SCOPES = (
    "contact",
    "feedback",
    "suggestion",
    "project_review",
    "queue_item",
    "consent",
    "future_use",
    "export",
    "backup",
    "anonymization",
    "purge",
)
PUBLIC_PILOT_REMOVAL_SCOPE_ALIASES = {
    "project-review": "project_review",
    "project review": "project_review",
    "queue-item": "queue_item",
    "future-use": "future_use",
    "future use": "future_use",
    "contact-removal": "contact",
    "feedback-removal": "feedback",
    "suggestion-removal": "suggestion",
    "project-review-removal": "project_review",
}
_PUBLIC_PILOT_REMOVAL_RAW_FIELDS = {
    "contact_email",
    "contact_value",
    "email",
    "phone",
    "address",
    "name",
    "location",
    "feedback_text",
    "suggestion_text",
    "project_review_text",
    "problem_statement",
    "requested_capability",
    "additional_notes",
    "raw_prompt",
    "prompt",
    "message",
    "user_input",
    "raw_message",
}


def _normalize_public_pilot_removal_scopes_v1(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        raw_items = [part.strip() for part in re.split(r"[,;|]", value) if part.strip()]
    elif isinstance(value, (list, tuple, set, frozenset)):
        raw_items = [str(item).strip() for item in value if str(item).strip()]
    else:
        raise ValueError("scope must be text or a JSON-safe list of text labels")

    normalized: list[str] = []
    for item in raw_items:
        label = PUBLIC_PILOT_REMOVAL_SCOPE_ALIASES.get(item.lower(), item.lower().replace(" ", "_").replace("-", "_"))
        if label not in PUBLIC_PILOT_REMOVAL_SCOPES:
            raise ValueError(f"unsupported public-pilot removal scope: {item}")
        normalized.append(label)
    return sorted(dict.fromkeys(normalized))


def _public_pilot_authority_errors_v1(metadata: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(metadata, dict):
        return ["public pilot metadata is required"]
    denied = metadata.get("denied_authority")
    if denied is not None:
        errors.extend(validate_public_pilot_denied_authority_v1(denied))
    for field in DENIED_AUTHORITY_FIELDS:
        if metadata.get(field) is True:
            errors.append(f"denied authority field must remain false: {field}")
    return errors


def _normalize_public_pilot_removal_metadata_v1(metadata: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = dict(metadata or {})
    source.update(overrides)
    request_kind = str(source.get("request_kind", "deletion")).strip().lower()
    if request_kind not in PUBLIC_PILOT_REMOVAL_KINDS:
        request_kind = "deletion"
    scopes = _normalize_public_pilot_removal_scopes_v1(source.get("scope") or source.get("scopes"))
    requester = source.get("requester") or source.get("requester_id") or source.get("subject")
    surface = source.get("surface") or source.get("surface_label")
    reason = source.get("reason") or source.get("removal_reason")
    normalized = {
        "schema_version": str(source.get("schema_version", "public_pilot_removal_request_v1")),
        "request_kind": request_kind,
        "requester": minimize_public_pilot_identifier_v1(requester, label="requester"),
        "surface": minimize_public_pilot_identifier_v1(surface, label="surface"),
        "scope": scopes,
        "reason": redact_public_pilot_text_v1(reason, max_length=96) if reason is not None else "",
        "contact_removal_requested": "contact" in scopes,
        "feedback_removal_requested": "feedback" in scopes,
        "suggestion_removal_requested": "suggestion" in scopes,
        "project_review_removal_requested": "project_review" in scopes,
        "queue_item_suppression_requested": "queue_item" in scopes,
        "consent_revocation_requested": request_kind == "revocation" or "consent" in scopes,
        "future_use_suppression_requested": bool(source.get("future_use_suppression", True)) or request_kind == "revocation",
        "purge_requested": bool(source.get("purge_requested", False)) or "purge" in scopes,
        "anonymization_requested": bool(source.get("anonymization_requested", False)) or "anonymization" in scopes,
        "backup_export_pending": bool(source.get("backup_export_pending", False)) or "backup" in scopes or "export" in scopes,
        "synthetic_test_safe_storage": bool(source.get("synthetic_test_safe_storage", False)),
        "test_safe_storage": bool(source.get("test_safe_storage", False)),
        "real_deletion_allowed": False,
        "raw_user_text_included": False,
        "raw_contact_value_included": False,
        "display_allowed": False,
        "export_allowed": False,
        "promotion_allowed": False,
        "queue_processing_allowed": False,
        "runtime_behavior_allowed": False,
        "final_answer_behavior_allowed": False,
        "public_launch_allowed": False,
        "denied_authority": dict(source.get("denied_authority") or {}),
    }
    for field in DENIED_AUTHORITY_FIELDS:
        normalized["denied_authority"][field] = _bool(normalized["denied_authority"].get(field, False))
    return normalized


def validate_public_pilot_deletion_request_v1(metadata: dict[str, Any] | None) -> list[str]:
    if not isinstance(metadata, dict):
        return ["public pilot deletion request metadata is required"]
    if not _json_safe(metadata):
        return ["public pilot deletion request metadata must be JSON-safe"]
    normalized = _normalize_public_pilot_removal_metadata_v1(metadata)
    errors: list[str] = []
    if normalized["request_kind"] != "deletion":
        errors.append("deletion request kind must be deletion")
    if not normalized["requester"]:
        errors.append("requester metadata is required")
    if not normalized["surface"]:
        errors.append("surface metadata is required")
    if not normalized["scope"]:
        errors.append("scope metadata is required")
    if not normalized["reason"]:
        errors.append("reason metadata is required")
    errors.extend(_public_pilot_authority_errors_v1(normalized))
    return errors


def validate_public_pilot_revocation_request_v1(metadata: dict[str, Any] | None) -> list[str]:
    if not isinstance(metadata, dict):
        return ["public pilot revocation request metadata is required"]
    if not _json_safe(metadata):
        return ["public pilot revocation request metadata must be JSON-safe"]
    normalized = _normalize_public_pilot_removal_metadata_v1(metadata, request_kind="revocation")
    errors: list[str] = []
    if not normalized["requester"]:
        errors.append("requester metadata is required")
    if not normalized["surface"]:
        errors.append("surface metadata is required")
    if not normalized["scope"]:
        errors.append("scope metadata is required")
    if not normalized["reason"]:
        errors.append("reason metadata is required")
    if not normalized["consent_revocation_requested"]:
        errors.append("revocation request must revoke consent or future use")
    errors.extend(_public_pilot_authority_errors_v1(normalized))
    return errors


def build_public_pilot_deletion_request_v1(metadata: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    normalized = _normalize_public_pilot_removal_metadata_v1(metadata, **overrides)
    errors = validate_public_pilot_deletion_request_v1(normalized)
    return {
        **normalized,
        "schema_version": "public_pilot_deletion_request_v1",
        "blocked": bool(errors),
        "validated": not bool(errors),
        "validation_errors": errors,
        "real_deletion_allowed": False,
    }


def build_public_pilot_revocation_request_v1(metadata: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    normalized = _normalize_public_pilot_removal_metadata_v1(metadata, request_kind="revocation", **overrides)
    errors = validate_public_pilot_revocation_request_v1(normalized)
    return {
        **normalized,
        "schema_version": "public_pilot_revocation_request_v1",
        "blocked": bool(errors),
        "validated": not bool(errors),
        "validation_errors": errors,
        "real_deletion_allowed": False,
        "future_use_suppression_requested": True,
    }


def validate_public_pilot_suppression_marker_v1(metadata: dict[str, Any] | None) -> list[str]:
    if not isinstance(metadata, dict):
        return ["public pilot suppression marker metadata is required"]
    if not _json_safe(metadata):
        return ["public pilot suppression marker metadata must be JSON-safe"]
    normalized = _normalize_public_pilot_removal_metadata_v1(metadata)
    errors: list[str] = []
    if not normalized["requester"]:
        errors.append("requester metadata is required")
    if not normalized["surface"]:
        errors.append("surface metadata is required")
    if not normalized["scope"]:
        errors.append("scope metadata is required")
    if not normalized["reason"]:
        errors.append("reason metadata is required")
    errors.extend(_public_pilot_authority_errors_v1(normalized))
    return errors


def build_public_pilot_suppression_marker_v1(metadata: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    normalized = _normalize_public_pilot_removal_metadata_v1(metadata, **overrides)
    errors = validate_public_pilot_suppression_marker_v1(normalized)
    return {
        "schema_version": "public_pilot_suppression_marker_v1",
        "requester": normalized.get("requester"),
        "surface": normalized.get("surface"),
        "scope": normalized.get("scope", []),
        "reason": normalized.get("reason", ""),
        "display_allowed": False,
        "export_allowed": False,
        "promotion_allowed": False,
        "queue_processing_allowed": False,
        "raw_records_read": False,
        "raw_records_included": False,
        "raw_display_allowed": False,
        "raw_export_allowed": False,
        "runtime_behavior_allowed": False,
        "final_answer_behavior_allowed": False,
        "public_launch_allowed": False,
        "future_use_suppressed": True,
        "real_deletion_allowed": False,
        "contact_removal_requested": normalized.get("contact_removal_requested", False),
        "feedback_removal_requested": normalized.get("feedback_removal_requested", False),
        "suggestion_removal_requested": normalized.get("suggestion_removal_requested", False),
        "project_review_removal_requested": normalized.get("project_review_removal_requested", False),
        "queue_item_suppression_requested": normalized.get("queue_item_suppression_requested", False),
        "consent_revocation_requested": normalized.get("consent_revocation_requested", False),
        "purge_requested": normalized.get("purge_requested", False),
        "anonymization_requested": normalized.get("anonymization_requested", False),
        "backup_export_pending": normalized.get("backup_export_pending", False),
        "blocked": bool(errors),
        "validated": not bool(errors),
        "validation_errors": errors,
    }


def apply_public_pilot_suppression_to_metadata_v1(
    metadata: dict[str, Any] | None,
    suppression_marker: dict[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    source = dict(metadata or {})
    source.update(overrides)
    marker = suppression_marker or build_public_pilot_suppression_marker_v1(source)
    if not _json_safe(source) or not _json_safe(marker):
        return {
            "schema_version": "public_pilot_suppression_applied_v1",
            "blocked": True,
            "validation_errors": ["public pilot suppression metadata must be JSON-safe"],
            "display_allowed": False,
            "export_allowed": False,
            "promotion_allowed": False,
            "queue_processing_allowed": False,
            "raw_records_read": False,
            "raw_records_included": False,
            "future_use_suppressed": True,
            "real_deletion_allowed": False,
        }
    sanitized = {
        "schema_version": "public_pilot_suppression_applied_v1",
        "suppressed": True,
        "display_allowed": False,
        "export_allowed": False,
        "promotion_allowed": False,
        "queue_processing_allowed": False,
        "raw_records_read": False,
        "raw_records_included": False,
        "raw_display_allowed": False,
        "raw_export_allowed": False,
        "runtime_behavior_allowed": False,
        "final_answer_behavior_allowed": False,
        "public_launch_allowed": False,
        "future_use_suppressed": True,
        "real_deletion_allowed": False,
        "requester": marker.get("requester"),
        "surface": marker.get("surface"),
        "scope": marker.get("scope", []),
        "reason": marker.get("reason", ""),
        "suppression_marker": {
            "schema_version": marker.get("schema_version", "public_pilot_suppression_marker_v1"),
            "requester": marker.get("requester"),
            "surface": marker.get("surface"),
            "scope": marker.get("scope", []),
            "display_allowed": False,
            "export_allowed": False,
            "promotion_allowed": False,
            "queue_processing_allowed": False,
            "future_use_suppressed": True,
            "real_deletion_allowed": False,
        },
        "validation_errors": [],
        "blocked": bool(marker.get("blocked", False)),
        "validated": bool(marker.get("validated", True)),
    }
    def _sanitize(value: Any) -> Any:
        if isinstance(value, str):
            return REDACTION_TOKEN
        if isinstance(value, dict):
            return {str(k): _sanitize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_sanitize(item) for item in value]
        if isinstance(value, tuple):
            return [_sanitize(item) for item in value]
        if isinstance(value, set):
            return sorted(_sanitize(item) for item in value)
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return REDACTION_TOKEN

    preserved_keys = {"requester", "surface", "scope", "reason", "suppression_marker", "display_allowed", "export_allowed", "promotion_allowed", "queue_processing_allowed", "raw_records_read", "raw_records_included", "raw_display_allowed", "raw_export_allowed", "runtime_behavior_allowed", "final_answer_behavior_allowed", "public_launch_allowed", "future_use_suppressed", "real_deletion_allowed", "blocked", "validated", "validation_errors", "schema_version", "suppressed"}
    for key, value in source.items():
        if key in preserved_keys:
            continue
        if key in _PUBLIC_PILOT_REMOVAL_RAW_FIELDS:
            sanitized[key] = REDACTION_TOKEN if value not in (None, "") else ""
        else:
            sanitized[key] = _sanitize(value)
    return sanitized


def build_public_pilot_removal_receipt_v1(metadata: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = dict(metadata or {})
    source.update(overrides)
    request_kind = str(source.get("request_kind", "deletion")).strip().lower()
    if request_kind not in PUBLIC_PILOT_REMOVAL_KINDS:
        request_kind = "deletion"
    normalized = _normalize_public_pilot_removal_metadata_v1(source, request_kind=request_kind)
    errors = validate_public_pilot_deletion_request_v1(normalized) if request_kind == "deletion" else validate_public_pilot_revocation_request_v1(normalized)
    synthetic_context = bool(normalized.get("synthetic_test_safe_storage")) and bool(normalized.get("test_safe_storage"))
    receipt_basis = {
        "requester": normalized.get("requester"),
        "surface": normalized.get("surface"),
        "scope": normalized.get("scope", []),
        "reason": normalized.get("reason", ""),
        "kind": request_kind,
    }
    return {
        "schema_version": "public_pilot_removal_receipt_v1",
        "request_kind": request_kind,
        "receipt_id": hashlib.sha256(json.dumps(receipt_basis, sort_keys=True).encode("utf-8")).hexdigest()[:16],
        "requester": normalized.get("requester"),
        "surface": normalized.get("surface"),
        "scope": normalized.get("scope", []),
        "reason_summary": normalized.get("reason", ""),
        "contact_removal_requested": normalized.get("contact_removal_requested", False),
        "feedback_removal_requested": normalized.get("feedback_removal_requested", False),
        "suggestion_removal_requested": normalized.get("suggestion_removal_requested", False),
        "project_review_removal_requested": normalized.get("project_review_removal_requested", False),
        "queue_item_suppression_requested": normalized.get("queue_item_suppression_requested", False),
        "consent_revocation_requested": normalized.get("consent_revocation_requested", False),
        "future_use_suppression_requested": normalized.get("future_use_suppression_requested", False),
        "purge_requested": normalized.get("purge_requested", False),
        "anonymization_requested": normalized.get("anonymization_requested", False),
        "backup_export_pending": normalized.get("backup_export_pending", False),
        "real_deletion_allowed": False,
        "synthetic_test_safe_storage": synthetic_context,
        "test_safe_storage": bool(normalized.get("test_safe_storage", False)),
        "raw_user_text_included": False,
        "raw_contact_value_included": False,
        "display_allowed": False,
        "export_allowed": False,
        "promotion_allowed": False,
        "queue_processing_allowed": False,
        "runtime_behavior_allowed": False,
        "final_answer_behavior_allowed": False,
        "public_launch_allowed": False,
        "blocked": bool(errors),
        "validated": not bool(errors),
        "validation_errors": errors,
    }
