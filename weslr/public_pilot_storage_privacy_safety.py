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
