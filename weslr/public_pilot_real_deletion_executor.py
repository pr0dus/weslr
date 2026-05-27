"""Public-pilot real deletion executor V1.

This module provides a narrow, fail-closed executor contract for public-pilot
storage surfaces. It supports synthetic temp files in tests, but blocks real
continuity, `.weslr`, queue, and database paths by default.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .public_pilot_storage_privacy_safety import (
    REDACTION_TOKEN,
    minimize_public_pilot_identifier_v1,
    redact_public_pilot_text_v1,
    reject_public_pilot_dot_weslr_path_v1,
    validate_public_pilot_denied_authority_v1,
)


SUPPORTED_PUBLIC_PILOT_DELETION_SURFACES = {
    "suggestion_requests_json",
    "suggestion_continuity_json",
    "pilot_user_events_json",
    "pilot_interventions_json",
    "pilot_redteam_events_json",
    "review_queue_json",
    "advisor_queue_jsonl",
}

JSON_SURFACES = {
    "suggestion_requests_json",
    "suggestion_continuity_json",
    "pilot_user_events_json",
    "pilot_interventions_json",
    "pilot_redteam_events_json",
    "review_queue_json",
}

JSONL_SURFACES = {"advisor_queue_jsonl"}

BLOCKED_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}
BLOCKED_PATH_TOKENS = ("..", "*", "?", "[", "]", "{", "}")
BLOCKED_REPO_SURFACE_TOKENS = (
    "continuity/suggestion_box/requests.json",
    "continuity/suggestion_box/continuity.json",
    "continuity/pilot_signals/user_events.json",
    "continuity/pilot_signals/interventions.json",
    "continuity/pilot_signals/redteam_events.json",
    "review_queue.json",
    ".weslr/advisor_review_queue.jsonl",
)
COLLECTION_KEYS = ("records", "items", "events", "entries")
RECORD_ID_FIELDS = ("record_id", "event_id", "id", "queue_item_id", "metadata_id", "request_id")
SAFE_SCOPE_LABELS = (
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


@dataclass(frozen=True)
class PublicPilotRealDeletionPlanResult:
    schema_version: str
    plan_id: str
    path: str
    surface_scope: str
    classified_surface_scope: str
    target_id: str
    target_id_label: str
    requester_label: str
    reason_label: str
    scope: tuple[str, ...]
    operator_authorized: bool
    dry_run: bool
    test_safe_storage: bool
    synthetic_temp_path: bool
    future_real_execution_authorization: bool
    real_execution_allowed: bool
    blocked: bool
    validated: bool
    validation_errors: tuple[str, ...]


@dataclass(frozen=True)
class PublicPilotRealDeletionExecutionResult:
    schema_version: str
    blocked: bool
    validated: bool
    dry_run: bool
    surface_scope: str
    classified_surface_scope: str
    path: str
    target_id: str
    matches_count: int
    changed_count: int
    suppressed_count: int
    deleted_count: int
    receipt: dict[str, Any]
    audit_event: dict[str, Any]
    validation_errors: tuple[str, ...]
    real_execution_allowed: bool


def _json_safe(value: Any) -> bool:
    try:
        json.dumps(value, sort_keys=True)
        return True
    except (TypeError, ValueError):
        return False


def _text_hash(value: Any, *, prefix: str) -> str:
    payload = "" if value is None else str(value)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_sha256:{digest}"


def _normalize_path_text(path_or_surface: str | Path) -> str:
    return str(path_or_surface).replace("\\", "/")


def _has_glob_tokens(path_text: str) -> bool:
    return any(token in path_text for token in BLOCKED_PATH_TOKENS)


def _is_blocked_repo_path(path_text: str) -> bool:
    normalized = _normalize_path_text(path_text)
    if normalized.startswith(".weslr/") or "/.weslr/" in normalized or normalized.endswith("/.weslr"):
        return True
    if normalized.startswith("continuity/") or "/continuity/" in normalized:
        return True
    if normalized.endswith("review_queue.json") or normalized.endswith("advisor_review_queue.jsonl"):
        return True
    return False


def _looks_like_directory(path_text: str) -> bool:
    if path_text.endswith(("/", "\\")):
        return True
    suffix = Path(path_text).suffix.lower()
    return suffix == ""


def _path_extension(path_text: str) -> str:
    return Path(path_text).suffix.lower()


def _normalize_scope_labels(value: Any) -> list[str]:
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
        label = item.lower().replace(" ", "_").replace("-", "_")
        if label not in SAFE_SCOPE_LABELS:
            raise ValueError(f"unsupported public-pilot deletion scope: {item}")
        normalized.append(label)
    return sorted(dict.fromkeys(normalized))


def classify_public_pilot_deletion_surface_v1(path_or_surface: str | Path) -> str:
    """Classify a public-pilot deletion surface from a path-like label only."""
    label = _normalize_path_text(path_or_surface)
    if label.endswith("review_queue.json"):
        return "review_queue_json"
    if label.endswith("advisor_review_queue.jsonl"):
        return "advisor_queue_jsonl"
    if "continuity/suggestion_box/requests.json" in label:
        return "suggestion_requests_json"
    if "continuity/suggestion_box/continuity.json" in label:
        return "suggestion_continuity_json"
    if "continuity/pilot_signals/user_events.json" in label:
        return "pilot_user_events_json"
    if "continuity/pilot_signals/interventions.json" in label:
        return "pilot_interventions_json"
    if "continuity/pilot_signals/redteam_events.json" in label:
        return "pilot_redteam_events_json"
    if Path(label).suffix.lower() in BLOCKED_EXTENSIONS:
        return "unknown_or_blocked"
    return "unknown_or_blocked"


def redact_public_pilot_deletion_audit_metadata_v1(metadata: dict[str, Any] | None) -> dict[str, Any]:
    """Return a safe audit summary with raw content removed or hashed."""
    source = dict(metadata or {})
    safe: dict[str, Any] = {}
    for key, value in source.items():
        if key in {"schema_version", "surface_scope", "classified_surface_scope", "operation_mode", "status", "blocked_reason_code"}:
            safe[key] = str(value)
        elif key in {"path", "target_id", "requester", "reason", "reason_summary"}:
            safe[f"{key}_label"] = _text_hash(value, prefix=key)
        elif key in {"requester_label", "target_id_label", "path_label", "plan_id", "receipt_id", "audit_id"}:
            safe[key] = str(value)
        elif key in {"matches_count", "changed_count", "suppressed_count", "deleted_count", "dry_run", "blocked", "validated", "real_execution_allowed", "operator_authorized", "test_safe_storage", "synthetic_temp_path", "future_real_execution_authorization", "real_deletion_allowed", "raw_user_text_included", "raw_contact_value_included", "display_allowed", "export_allowed", "promotion_allowed", "queue_processing_allowed", "runtime_behavior_allowed", "final_answer_behavior_allowed", "public_launch_allowed"}:
            safe[key] = value
        elif key == "scope":
            if isinstance(value, (list, tuple, set, frozenset)):
                safe[key] = [str(item) for item in value]
            elif value is None:
                safe[key] = []
            else:
                safe[key] = [str(value)]
        elif key == "validation_errors":
            safe[key] = [str(item) for item in value] if isinstance(value, (list, tuple, set, frozenset)) else [str(value)]
        elif isinstance(value, (bool, int, float)) or value is None:
            safe[key] = value
        elif isinstance(value, (list, tuple, set, frozenset)):
            safe[key] = [_text_hash(item, prefix=key) if isinstance(item, str) else item for item in value]
        else:
            safe[key] = _text_hash(value, prefix=key)
    return safe


def _path_validation_errors(path_text: str, surface_scope: str, *, test_safe_storage: bool, synthetic_temp_path: bool, future_real_execution_authorization: bool) -> list[str]:
    errors: list[str] = []
    if not path_text:
        errors.append("storage path metadata is required")
        return errors
    if _has_glob_tokens(path_text):
        errors.append("glob deletion is denied")
    if any(token in path_text for token in ("../", "..\\", "/..", "\\..")) or Path(path_text).parts and any(part == ".." for part in Path(path_text).parts):
        errors.append("path traversal is denied")
    if _looks_like_directory(path_text):
        errors.append("directory deletion is denied")
    if ".weslr" in Path(path_text).parts or "/.weslr/" in path_text or path_text.startswith(".weslr/"):
        errors.append(".weslr path authority is denied")
    if any(path_text.endswith(token) or token in path_text for token in BLOCKED_REPO_SURFACE_TOKENS):
        errors.append("real continuity paths are blocked")
    if Path(path_text).suffix.lower() in BLOCKED_EXTENSIONS:
        errors.append("blocked_db_surface_not_supported_v1")
    if surface_scope in JSONL_SURFACES and _path_extension(path_text) not in {".jsonl"}:
        errors.append("surface scope and path format must be JSONL")
    if surface_scope in JSON_SURFACES and _path_extension(path_text) not in {".json"}:
        errors.append("surface scope and path format must be JSON")
    if not test_safe_storage or not synthetic_temp_path:
        errors.append("test-safe synthetic execution authorization is required")
    if future_real_execution_authorization:
        errors.append("real continuity execution is not supported in this lane")
    return errors


def validate_public_pilot_real_deletion_plan_v1(plan: dict[str, Any] | None) -> list[str]:
    if not isinstance(plan, dict):
        return ["public pilot real deletion plan metadata is required"]
    if not _json_safe(plan):
        return ["public pilot real deletion plan metadata must be JSON-safe"]

    errors: list[str] = []
    if not bool(plan.get("operator_authorized", False)):
        errors.append("operator authorization is required")
    requester_value = plan.get("requester") or plan.get("requester_label")
    if not requester_value:
        errors.append("requester metadata is required")
    if not plan.get("surface_scope"):
        errors.append("surface scope metadata is required")
    target_value = plan.get("target_id") or plan.get("target_id_label")
    if not target_value:
        errors.append("target metadata id is required")
    if not plan.get("scope"):
        errors.append("scope metadata is required")
    reason_value = plan.get("reason") or plan.get("reason_label")
    if not reason_value:
        errors.append("reason metadata is required")

    surface_scope = str(plan.get("surface_scope", "unknown_or_blocked"))
    if surface_scope not in SUPPORTED_PUBLIC_PILOT_DELETION_SURFACES:
        errors.append("unknown or blocked surface scope")

    classified = classify_public_pilot_deletion_surface_v1(plan.get("path", ""))
    if classified != "unknown_or_blocked" and classified != surface_scope:
        errors.append("surface scope does not match classified path")

    errors.extend(validate_public_pilot_denied_authority_v1(plan.get("denied_authority")))
    errors.extend(
        _path_validation_errors(
            str(plan.get("path", "")),
            surface_scope,
            test_safe_storage=bool(plan.get("test_safe_storage", False)),
            synthetic_temp_path=bool(plan.get("synthetic_temp_path", False)),
            future_real_execution_authorization=bool(plan.get("future_real_execution_authorization", False)),
        )
    )
    if surface_scope == "unknown_or_blocked":
        errors.append("unknown or blocked surface scope")
    return errors


def build_public_pilot_real_deletion_plan_v1(metadata: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = dict(metadata or {})
    source.update(overrides)
    raw_scope = _normalize_scope_labels(source.get("scope"))
    surface_scope = str(source.get("surface_scope", "unknown_or_blocked"))
    plan = {
        "schema_version": "public_pilot_real_deletion_plan_v1",
        "path": str(source.get("path", "")),
        "surface_scope": surface_scope,
        "classified_surface_scope": classify_public_pilot_deletion_surface_v1(str(source.get("path", ""))),
        "target_id": str(source.get("target_id", "")),
        "target_id_label": _text_hash(source.get("target_id", ""), prefix="target"),
        "requester_label": _text_hash(source.get("requester", ""), prefix="requester"),
        "reason_label": _text_hash(source.get("reason", ""), prefix="reason"),
        "scope": tuple(raw_scope),
        "operator_authorized": bool(source.get("operator_authorized", False)),
        "dry_run": bool(source.get("dry_run", False)),
        "test_safe_storage": bool(source.get("test_safe_storage", False)),
        "synthetic_temp_path": bool(source.get("synthetic_temp_path", False)),
        "future_real_execution_authorization": bool(source.get("future_real_execution_authorization", False)),
        "real_execution_allowed": False,
        "blocked": False,
        "validated": False,
        "validation_errors": tuple(),
        "denied_authority": dict(source.get("denied_authority") or {}),
    }
    errors = validate_public_pilot_real_deletion_plan_v1({**source, "scope": raw_scope})
    plan.update(
        {
            "blocked": bool(errors),
            "validated": not bool(errors),
            "validation_errors": tuple(errors),
        }
    )
    return plan


def _candidate_record_ids(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return []
    candidates: list[str] = []
    for field in RECORD_ID_FIELDS:
        value = record.get(field)
        if value not in (None, ""):
            candidates.append(str(value))
    return candidates


def _match_record(record: Any, target_id: str) -> bool:
    if not target_id:
        return False
    if isinstance(record, dict):
        if str(record.get("record_id", "")) == target_id:
            return True
        if str(record.get("event_id", "")) == target_id:
            return True
        if str(record.get("id", "")) == target_id:
            return True
        if str(record.get("queue_item_id", "")) == target_id:
            return True
        if str(record.get("metadata_id", "")) == target_id:
            return True
        if str(record.get("request_id", "")) == target_id:
            return True
        return False
    return str(record) == target_id


def _prune_json_list(payload: list[Any], target_id: str) -> tuple[list[Any], int]:
    kept: list[Any] = []
    removed = 0
    for item in payload:
        if _match_record(item, target_id):
            removed += 1
        else:
            kept.append(item)
    return kept, removed


def _prune_json_mapping(payload: dict[str, Any], target_id: str) -> tuple[dict[str, Any], int]:
    if _match_record(payload, target_id):
        return {}, 1

    kept = dict(payload)
    removed = 0
    for key in list(kept.keys()):
        value = kept[key]
        if key == target_id or _match_record(value, target_id):
            del kept[key]
            removed += 1
            continue
        if key in COLLECTION_KEYS and isinstance(value, list):
            filtered, count = _prune_json_list(value, target_id)
            kept[key] = filtered
            removed += count
        elif key in COLLECTION_KEYS and isinstance(value, dict):
            nested, count = _prune_json_mapping(value, target_id)
            kept[key] = nested
            removed += count
    return kept, removed


def _prune_json_payload(payload: Any, target_id: str) -> tuple[Any, int]:
    if isinstance(payload, list):
        return _prune_json_list(payload, target_id)
    if isinstance(payload, dict):
        return _prune_json_mapping(payload, target_id)
    if _match_record(payload, target_id):
        return None, 1
    return payload, 0


def _prune_jsonl_lines(text: str, target_id: str) -> tuple[str, int]:
    lines = text.splitlines()
    kept_lines: list[str] = []
    removed = 0
    for line in lines:
        if not line.strip():
            kept_lines.append(line)
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("JSONL payload must contain JSON objects per line") from exc
        if _match_record(record, target_id):
            removed += 1
        else:
            kept_lines.append(line)
    suffix = "\n" if text.endswith("\n") and kept_lines else ""
    return "\n".join(kept_lines) + suffix, removed


def build_public_pilot_real_deletion_receipt_v1(
    plan: dict[str, Any] | None = None,
    execution_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = dict(plan or {})
    summary = dict(execution_summary or {})
    receipt_basis = {
        "schema_version": normalized.get("schema_version", "public_pilot_real_deletion_plan_v1"),
        "surface_scope": normalized.get("surface_scope", "unknown_or_blocked"),
        "path": normalized.get("path", ""),
        "target_id": normalized.get("target_id", ""),
        "requester": normalized.get("requester_label", normalized.get("requester", "")),
        "reason": normalized.get("reason_label", normalized.get("reason", "")),
        "dry_run": bool(normalized.get("dry_run", False)),
    }
    receipt_id = hashlib.sha256(json.dumps(receipt_basis, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    result = {
        "schema_version": "public_pilot_real_deletion_receipt_v1",
        "receipt_id": receipt_id,
        "plan_id": str(normalized.get("plan_id", _text_hash(receipt_basis, prefix="plan"))),
        "surface_scope": str(normalized.get("surface_scope", "unknown_or_blocked")),
        "classified_surface_scope": str(normalized.get("classified_surface_scope", "unknown_or_blocked")),
        "path_label": _text_hash(normalized.get("path", ""), prefix="path"),
        "target_id_label": str(normalized.get("target_id_label", _text_hash(normalized.get("target_id", ""), prefix="target"))),
        "requester_label": str(normalized.get("requester_label", _text_hash(normalized.get("requester", ""), prefix="requester"))),
        "reason_label": str(normalized.get("reason_label", _text_hash(normalized.get("reason", ""), prefix="reason"))),
        "scope": list(normalized.get("scope", ())),
        "dry_run": bool(normalized.get("dry_run", False)),
        "matches_count": int(summary.get("matches_count", 0)),
        "changed_count": int(summary.get("changed_count", 0)),
        "suppressed_count": int(summary.get("suppressed_count", 0)),
        "deleted_count": int(summary.get("deleted_count", 0)),
        "blocked": bool(summary.get("blocked", normalized.get("blocked", False))),
        "validated": bool(summary.get("validated", normalized.get("validated", False))),
        "real_execution_allowed": False,
        "raw_user_text_included": False,
        "raw_contact_value_included": False,
        "display_allowed": False,
        "export_allowed": False,
        "promotion_allowed": False,
        "queue_processing_allowed": False,
        "runtime_behavior_allowed": False,
        "final_answer_behavior_allowed": False,
        "public_launch_allowed": False,
        "test_safe_storage": bool(normalized.get("test_safe_storage", False)),
        "synthetic_temp_path": bool(normalized.get("synthetic_temp_path", False)),
        "future_real_execution_authorization": bool(normalized.get("future_real_execution_authorization", False)),
        "validation_errors": list(summary.get("validation_errors", normalized.get("validation_errors", ()))),
    }
    return redact_public_pilot_deletion_audit_metadata_v1(result)


def validate_public_pilot_real_deletion_receipt_v1(receipt: dict[str, Any] | None) -> list[str]:
    if not isinstance(receipt, dict):
        return ["public pilot real deletion receipt metadata is required"]
    if not _json_safe(receipt):
        return ["public pilot real deletion receipt metadata must be JSON-safe"]
    errors: list[str] = []
    if receipt.get("raw_user_text_included") is not False:
        errors.append("receipt must not expose raw user text")
    if receipt.get("raw_contact_value_included") is not False:
        errors.append("receipt must not expose raw contact values")
    for field in ("display_allowed", "export_allowed", "promotion_allowed", "queue_processing_allowed", "runtime_behavior_allowed", "final_answer_behavior_allowed", "public_launch_allowed", "real_execution_allowed"):
        if receipt.get(field) is not False:
            errors.append(f"receipt authority must remain false: {field}")
    if not str(receipt.get("surface_scope", "")):
        errors.append("surface scope metadata is required")
    if not str(receipt.get("path_label", "")):
        errors.append("path label metadata is required")
    return errors


def build_public_pilot_real_deletion_audit_event_v1(
    plan: dict[str, Any] | None = None,
    execution_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = dict(plan or {})
    summary = dict(execution_summary or {})
    audit_basis = {
        "schema_version": normalized.get("schema_version", "public_pilot_real_deletion_plan_v1"),
        "surface_scope": normalized.get("surface_scope", "unknown_or_blocked"),
        "path": normalized.get("path", ""),
        "target_id": normalized.get("target_id", ""),
        "requester": normalized.get("requester_label", normalized.get("requester", "")),
        "reason": normalized.get("reason_label", normalized.get("reason", "")),
        "matches_count": int(summary.get("matches_count", 0)),
        "changed_count": int(summary.get("changed_count", 0)),
        "dry_run": bool(normalized.get("dry_run", False)),
    }
    audit_id = hashlib.sha256(json.dumps(audit_basis, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    event = {
        "schema_version": "public_pilot_real_deletion_audit_event_v1",
        "audit_id": audit_id,
        "plan_id": str(normalized.get("plan_id", _text_hash(audit_basis, prefix="plan"))),
        "surface_scope": str(normalized.get("surface_scope", "unknown_or_blocked")),
        "classified_surface_scope": str(normalized.get("classified_surface_scope", "unknown_or_blocked")),
        "path_label": _text_hash(normalized.get("path", ""), prefix="path"),
        "target_id_label": str(normalized.get("target_id_label", _text_hash(normalized.get("target_id", ""), prefix="target"))),
        "requester_label": str(normalized.get("requester_label", _text_hash(normalized.get("requester", ""), prefix="requester"))),
        "reason_label": str(normalized.get("reason_label", _text_hash(normalized.get("reason", ""), prefix="reason"))),
        "scope": list(normalized.get("scope", ())),
        "dry_run": bool(normalized.get("dry_run", False)),
        "matches_count": int(summary.get("matches_count", 0)),
        "changed_count": int(summary.get("changed_count", 0)),
        "suppressed_count": int(summary.get("suppressed_count", 0)),
        "deleted_count": int(summary.get("deleted_count", 0)),
        "blocked": bool(summary.get("blocked", normalized.get("blocked", False))),
        "validated": bool(summary.get("validated", normalized.get("validated", False))),
        "raw_user_text_included": False,
        "raw_contact_value_included": False,
        "display_allowed": False,
        "export_allowed": False,
        "promotion_allowed": False,
        "queue_processing_allowed": False,
        "runtime_behavior_allowed": False,
        "final_answer_behavior_allowed": False,
        "public_launch_allowed": False,
        "real_execution_allowed": False,
        "test_safe_storage": bool(normalized.get("test_safe_storage", False)),
        "synthetic_temp_path": bool(normalized.get("synthetic_temp_path", False)),
        "future_real_execution_authorization": bool(normalized.get("future_real_execution_authorization", False)),
        "validation_errors": list(summary.get("validation_errors", normalized.get("validation_errors", ()))),
        "blocked_reason_code": "" if not summary.get("validation_errors") else "validation_failed",
    }
    return redact_public_pilot_deletion_audit_metadata_v1(event)


def _read_json_payload(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_payload(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _execute_synthetic_json_plan(path: Path, target_id: str, dry_run: bool) -> tuple[int, int]:
    payload = _read_json_payload(path)
    updated, matches = _prune_json_payload(payload, target_id)
    if not dry_run:
        _write_json_payload(path, updated)
    changed = 0 if dry_run else matches
    return matches, changed


def _execute_synthetic_jsonl_plan(path: Path, target_id: str, dry_run: bool) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    updated, matches = _prune_jsonl_lines(text, target_id)
    if not dry_run:
        path.write_text(updated, encoding="utf-8")
    changed = 0 if dry_run else matches
    return matches, changed


def execute_public_pilot_real_deletion_plan_v1(plan: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    source = dict(plan or {})
    source.update(overrides)
    if (
        isinstance(source, dict)
        and source.get("schema_version") == "public_pilot_real_deletion_plan_v1"
        and "validated" in source
        and "validation_errors" in source
    ):
        normalized = dict(source)
    else:
        normalized = build_public_pilot_real_deletion_plan_v1(source)
    validation_errors = list(normalized.get("validation_errors", ()))
    if validation_errors:
        summary = {
            "blocked": True,
            "validated": False,
            "validation_errors": validation_errors,
            "matches_count": 0,
            "changed_count": 0,
            "suppressed_count": 0,
            "deleted_count": 0,
        }
        receipt = build_public_pilot_real_deletion_receipt_v1(normalized, summary)
        audit_event = build_public_pilot_real_deletion_audit_event_v1(normalized, summary)
        return {
            "schema_version": "public_pilot_real_deletion_execution_result_v1",
            "blocked": True,
            "validated": False,
            "dry_run": bool(normalized.get("dry_run", False)),
            "surface_scope": normalized.get("surface_scope", "unknown_or_blocked"),
            "classified_surface_scope": normalized.get("classified_surface_scope", "unknown_or_blocked"),
            "path_label": _text_hash(normalized.get("path", ""), prefix="path"),
            "target_id_label": str(normalized.get("target_id_label", _text_hash(normalized.get("target_id", ""), prefix="target"))),
            "requester_label": str(normalized.get("requester_label", _text_hash(normalized.get("requester", ""), prefix="requester"))),
            "matches_count": 0,
            "changed_count": 0,
            "suppressed_count": 0,
            "deleted_count": 0,
            "receipt": receipt,
            "audit_event": audit_event,
            "validation_errors": tuple(validation_errors),
            "real_execution_allowed": False,
        }

    path = Path(str(normalized["path"]))
    if not path.exists():
        summary = {
            "blocked": True,
            "validated": False,
            "validation_errors": ["storage path does not exist"],
            "matches_count": 0,
            "changed_count": 0,
            "suppressed_count": 0,
            "deleted_count": 0,
        }
        receipt = build_public_pilot_real_deletion_receipt_v1(normalized, summary)
        audit_event = build_public_pilot_real_deletion_audit_event_v1(normalized, summary)
        return {
            "schema_version": "public_pilot_real_deletion_execution_result_v1",
            "blocked": True,
            "validated": False,
            "dry_run": bool(normalized.get("dry_run", False)),
            "surface_scope": normalized.get("surface_scope", "unknown_or_blocked"),
            "classified_surface_scope": normalized.get("classified_surface_scope", "unknown_or_blocked"),
            "path_label": _text_hash(normalized.get("path", ""), prefix="path"),
            "target_id_label": str(normalized.get("target_id_label", _text_hash(normalized.get("target_id", ""), prefix="target"))),
            "requester_label": str(normalized.get("requester_label", _text_hash(normalized.get("requester", ""), prefix="requester"))),
            "matches_count": 0,
            "changed_count": 0,
            "suppressed_count": 0,
            "deleted_count": 0,
            "receipt": receipt,
            "audit_event": audit_event,
            "validation_errors": ("storage path does not exist",),
            "real_execution_allowed": False,
        }

    dry_run = bool(normalized.get("dry_run", False))
    surface_scope = str(normalized.get("surface_scope", "unknown_or_blocked"))
    target_id = str(normalized.get("target_id", ""))
    if surface_scope in JSONL_SURFACES:
        matches_count, changed_count = _execute_synthetic_jsonl_plan(path, target_id, dry_run)
    else:
        matches_count, changed_count = _execute_synthetic_json_plan(path, target_id, dry_run)
    summary = {
        "blocked": False,
        "validated": True,
        "validation_errors": [],
        "matches_count": matches_count,
        "changed_count": changed_count,
        "suppressed_count": changed_count,
        "deleted_count": changed_count,
    }
    receipt = build_public_pilot_real_deletion_receipt_v1(normalized, summary)
    audit_event = build_public_pilot_real_deletion_audit_event_v1(normalized, summary)
    return {
        "schema_version": "public_pilot_real_deletion_execution_result_v1",
        "blocked": False,
        "validated": True,
        "dry_run": dry_run,
        "surface_scope": surface_scope,
        "classified_surface_scope": normalized.get("classified_surface_scope", "unknown_or_blocked"),
        "path_label": _text_hash(normalized.get("path", ""), prefix="path"),
        "target_id_label": str(normalized.get("target_id_label", _text_hash(target_id, prefix="target"))),
        "requester_label": str(normalized.get("requester_label", _text_hash(normalized.get("requester", ""), prefix="requester"))),
        "matches_count": matches_count,
        "changed_count": changed_count,
        "suppressed_count": changed_count,
        "deleted_count": changed_count,
        "receipt": receipt,
        "audit_event": audit_event,
        "validation_errors": (),
        "real_execution_allowed": False,
    }


__all__ = [
    "SUPPORTED_PUBLIC_PILOT_DELETION_SURFACES",
    "classify_public_pilot_deletion_surface_v1",
    "redact_public_pilot_deletion_audit_metadata_v1",
    "build_public_pilot_real_deletion_plan_v1",
    "validate_public_pilot_real_deletion_plan_v1",
    "execute_public_pilot_real_deletion_plan_v1",
    "build_public_pilot_real_deletion_audit_event_v1",
    "build_public_pilot_real_deletion_receipt_v1",
    "validate_public_pilot_real_deletion_receipt_v1",
]
