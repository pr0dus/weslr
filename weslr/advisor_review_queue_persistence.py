"""WESLR Advisor Review Queue Persistence Schema V1.

Dataclasses, validation helpers, and safe explicit-path JSONL helper functions
for advisor-review queue persistence records. This module does not implement
daemon behavior, scheduling, database behavior, model calls, advisor calls,
prompt mutation, provider activation, automatic implementation, or
runtime/config changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re
import tempfile

from .public_pilot_storage_privacy_safety import reject_public_pilot_dot_weslr_path_v1


ALLOWED_STORAGE_FORMATS = {"jsonl", "json", "unknown"}
ALLOWED_PERSISTENCE_EVENT_TYPES = {
    "queue_item_created",
    "status_update_requested",
    "operator_decision_recorded",
    "queue_item_archived",
    "queue_item_loaded",
    "queue_summary_requested",
    "unknown",
}
ALLOWED_OPERATOR_DECISIONS = {"pending_review", "approved", "approved_with_changes", "rejected", "deferred"}
QUEUE_ITEM_EVENT_TYPES = {"queue_item_created", "status_update_requested", "operator_decision_recorded", "queue_item_archived"}

UNSAFE_PERSISTENCE_SAFETY_FLAG_FIELDS = {
    "queue_file_write_attempted": "queue file write attempted",
    "queue_file_read_attempted": "queue file read attempted",
    "database_write_attempted": "database write attempted",
    "external_model_call_attempted": "external model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "runtime_config_change_attempted": "runtime/config change attempted",
    "memory_mutation_attempted": "memory mutation attempted",
    "governance_override_attempted": "governance override attempted",
    "self_approval_attempted": "self approval attempted",
    "raw_benchmark_text_included": "raw benchmark text included",
    "secrets_included": "secrets included",
    "private_user_data_included": "private user data included",
    "answer_selection_attempted": "answer selection attempted",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "official_score_claimed": "official score claimed",
}

SENSITIVE_TEXT_PATTERNS = {
    "possible API key": re.compile(r"api[_ -]?key|sk-[A-Za-z0-9]|AIza[0-9A-Za-z_-]", re.IGNORECASE),
    "possible token": re.compile(r"\btoken\b|token[_ -]?[A-Za-z0-9_-]*|bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    "possible secret": re.compile(r"\bsecret\b|secret[_ -]?[A-Za-z0-9_-]*|password\s*[:=]", re.IGNORECASE),
    "possible raw benchmark text": re.compile(r"raw benchmark|benchmark text|question stem|passage:", re.IGNORECASE),
    "possible answer key": re.compile(r"answer[_ -]?key|official solution|correct answer", re.IGNORECASE),
    "possible official score": re.compile(r"official score|benchmark score", re.IGNORECASE),
    "possible private user data": re.compile(r"private user data|ssn|social security|passport", re.IGNORECASE),
}
SUMMARY_REDACTION = "[redacted]"


@dataclass
class AdvisorQueuePersistenceSafetyFlags:
    queue_file_write_attempted: bool = False
    queue_file_read_attempted: bool = False
    database_write_attempted: bool = False
    external_model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    runtime_config_change_attempted: bool = False
    memory_mutation_attempted: bool = False
    governance_override_attempted: bool = False
    self_approval_attempted: bool = False
    raw_benchmark_text_included: bool = False
    secrets_included: bool = False
    private_user_data_included: bool = False
    answer_selection_attempted: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False


@dataclass
class AdvisorQueuePersistencePathPolicy:
    schema_version: str = "1.0"
    queue_path: str = ".weslr/advisor_review_queue.jsonl"
    storage_format: str = "jsonl"
    append_only_required: bool = True
    redaction_required: bool = True
    operator_approval_required: bool = True
    allow_absolute_paths: bool = False
    allow_path_traversal: bool = False
    allow_external_storage: bool = False
    institution_storage_policy: str = "local_only_default"
    retention_policy: str = "unspecified"


@dataclass
class AdvisorQueuePersistenceEvent:
    schema_version: str = "1.0"
    event_id: str = ""
    event_type: str = "unknown"
    queue_item_id: str = ""
    queue_item_snapshot: dict[str, Any] = field(default_factory=dict)
    previous_status: str = ""
    new_status: str = ""
    operator_decision: str = "pending_review"
    redacted_summary: str = ""
    created_at: str = ""
    actor: str = "operator_or_system"
    safety_flags: AdvisorQueuePersistenceSafetyFlags = field(default_factory=AdvisorQueuePersistenceSafetyFlags)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_empty_persistence_path_policy(**overrides: Any) -> AdvisorQueuePersistencePathPolicy:
    policy = AdvisorQueuePersistencePathPolicy()
    for key, value in overrides.items():
        if not hasattr(policy, key):
            raise ValueError(f"unknown persistence path policy field: {key}")
        setattr(policy, key, value)
    return policy


def create_empty_persistence_event(
    event_id: str = "",
    event_type: str = "unknown",
    queue_item_id: str = "",
    **overrides: Any,
) -> AdvisorQueuePersistenceEvent:
    event = AdvisorQueuePersistenceEvent(
        event_id=event_id,
        event_type=event_type,
        queue_item_id=queue_item_id,
        created_at=_utc_now(),
    )
    for key, value in overrides.items():
        if not hasattr(event, key):
            raise ValueError(f"unknown persistence event field: {key}")
        setattr(event, key, value)
    return event


def persistence_path_policy_to_dict(policy: AdvisorQueuePersistencePathPolicy) -> dict[str, Any]:
    return asdict(policy)


def persistence_path_policy_from_dict(data: dict[str, Any]) -> AdvisorQueuePersistencePathPolicy:
    return AdvisorQueuePersistencePathPolicy(**dict(data))


def persistence_event_to_dict(event: AdvisorQueuePersistenceEvent) -> dict[str, Any]:
    return asdict(event)


def persistence_event_from_dict(data: dict[str, Any]) -> AdvisorQueuePersistenceEvent:
    payload = dict(data)
    flags = payload.get("safety_flags")
    if isinstance(flags, AdvisorQueuePersistenceSafetyFlags):
        payload["safety_flags"] = flags
    elif isinstance(flags, dict):
        payload["safety_flags"] = AdvisorQueuePersistenceSafetyFlags(**flags)
    elif flags is None:
        payload["safety_flags"] = AdvisorQueuePersistenceSafetyFlags()
    return AdvisorQueuePersistenceEvent(**payload)


def _safety_flag_errors(flags: AdvisorQueuePersistenceSafetyFlags) -> list[str]:
    return [label for field_name, label in UNSAFE_PERSISTENCE_SAFETY_FLAG_FIELDS.items() if getattr(flags, field_name)]


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for key, nested in value.items():
            values.extend(_string_values(key))
            values.extend(_string_values(nested))
        return values
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for nested in value:
            values.extend(_string_values(nested))
        return values
    return []


def _detect_sensitive_text(values: list[str]) -> list[str]:
    joined = "\n".join(values)
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS.values():
        redacted = pattern.sub(SUMMARY_REDACTION, redacted)
    return redacted


def validate_persistence_path_policy(policy: AdvisorQueuePersistencePathPolicy) -> list[str]:
    errors: list[str] = []
    if policy.storage_format not in ALLOWED_STORAGE_FORMATS:
        errors.append("invalid storage_format")
    if policy.append_only_required is False:
        errors.append("append_only_required must remain true")
    if policy.redaction_required is False:
        errors.append("redaction_required must remain true")
    if policy.operator_approval_required is False:
        errors.append("operator_approval_required must remain true")
    if policy.allow_absolute_paths:
        errors.append("absolute paths must remain disallowed")
    if policy.allow_path_traversal:
        errors.append("path traversal must remain disallowed")
    if policy.allow_external_storage:
        errors.append("external storage must remain disallowed")
    for finding in _detect_sensitive_text(_string_values(asdict(policy))):
        errors.append(finding)
    return errors


def validate_persistence_event(event: AdvisorQueuePersistenceEvent) -> list[str]:
    errors: list[str] = []
    if not event.event_id.strip():
        errors.append("missing event_id")
    if event.event_type not in ALLOWED_PERSISTENCE_EVENT_TYPES:
        errors.append("invalid event_type")
    if event.event_type in QUEUE_ITEM_EVENT_TYPES and not event.queue_item_id.strip():
        errors.append("missing queue_item_id")
    if event.operator_decision not in ALLOWED_OPERATOR_DECISIONS:
        errors.append("invalid operator_decision")
    errors.extend(_safety_flag_errors(event.safety_flags))
    for finding in _detect_sensitive_text([event.event_id, event.event_type, event.queue_item_id, event.previous_status, event.new_status, event.operator_decision, event.redacted_summary, event.created_at, event.actor]):
        errors.append(finding)
    for finding in _detect_sensitive_text(_string_values(event.queue_item_snapshot)):
        errors.append(finding)
    return errors


def summarize_persistence_path_policy(policy: AdvisorQueuePersistencePathPolicy) -> dict[str, Any]:
    validation_errors = validate_persistence_path_policy(policy)
    return {
        "schema_version": policy.schema_version,
        "queue_path": _redact_text(policy.queue_path),
        "storage_format": policy.storage_format,
        "append_only_required": policy.append_only_required,
        "redaction_required": policy.redaction_required,
        "operator_approval_required": policy.operator_approval_required,
        "allow_absolute_paths": policy.allow_absolute_paths,
        "allow_path_traversal": policy.allow_path_traversal,
        "allow_external_storage": policy.allow_external_storage,
        "institution_storage_policy": _redact_text(policy.institution_storage_policy),
        "retention_policy": _redact_text(policy.retention_policy),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text(_string_values(asdict(policy)))),
        "summary_mode": "redacted_count_only",
    }


def summarize_persistence_event(event: AdvisorQueuePersistenceEvent) -> dict[str, Any]:
    validation_errors = validate_persistence_event(event)
    return {
        "schema_version": event.schema_version,
        "event_id": _redact_text(event.event_id),
        "event_type": event.event_type,
        "queue_item_id": _redact_text(event.queue_item_id),
        "queue_item_snapshot_field_count": len(event.queue_item_snapshot),
        "previous_status_present": bool(event.previous_status),
        "new_status_present": bool(event.new_status),
        "operator_decision": event.operator_decision,
        "redacted_summary": _redact_text(event.redacted_summary),
        "created_at_present": bool(event.created_at),
        "actor": _redact_text(event.actor),
        "safety_error_count": len(_safety_flag_errors(event.safety_flags)),
        "validation_error_count": len(validation_errors),
        "contains_redactions": bool(_detect_sensitive_text(_string_values(asdict(event)))),
        "persistence_performed": False,
        "queue_file_created": False,
        "external_model_calls_made": False,
        "runtime_changes_made": False,
        "answer_selection": False,
        "truth_claim": False,
        "official_score": False,
        "summary_mode": "redacted_count_only",
    }


def validate_queue_storage_path(
    path: str | Path,
    policy: AdvisorQueuePersistencePathPolicy | None = None,
    *,
    public_pilot_mode: bool = False,
) -> list[str]:
    """Validate a queue storage path without reading or writing it."""
    active_policy = policy or create_empty_persistence_path_policy()
    errors = validate_persistence_path_policy(active_policy)
    path_obj = Path(path)
    path_text = str(path)

    if ".." in path_obj.parts:
        errors.append("path traversal is not allowed")
    if path_obj.is_absolute() and not active_policy.allow_absolute_paths:
        try:
            temp_root = Path(tempfile.gettempdir()).resolve()
            resolved = path_obj.resolve(strict=False)
            if temp_root not in (resolved, *resolved.parents):
                errors.append("absolute paths are not allowed")
        except (OSError, RuntimeError):
            errors.append("absolute paths are not allowed")
    if "://" in path_text or path_text.startswith(("s3:", "gs:", "http:", "https:")):
        errors.append("external storage paths are not allowed")
    if not path_text.strip():
        errors.append("missing queue storage path")
    try:
        reject_public_pilot_dot_weslr_path_v1(path_text, public_pilot_mode=public_pilot_mode)
    except ValueError as exc:
        errors.append(str(exc))

    return errors


def append_persistence_event(
    path: str | Path,
    event: AdvisorQueuePersistenceEvent | dict[str, Any],
    policy: AdvisorQueuePersistencePathPolicy | None = None,
    *,
    public_pilot_mode: bool = False,
) -> dict[str, Any]:
    """Append one validated JSONL event to an explicit path."""
    active_policy = policy or create_empty_persistence_path_policy()
    queue_path = Path(path)
    persistence_event = event if isinstance(event, AdvisorQueuePersistenceEvent) else persistence_event_from_dict(event)
    errors = validate_queue_storage_path(queue_path, active_policy, public_pilot_mode=public_pilot_mode)
    errors.extend(validate_persistence_event(persistence_event))
    if errors:
        return {
            "success": False,
            "validation_errors": errors,
            "event_id": persistence_event.event_id,
            "persistence_performed": False,
            "external_model_calls_made": False,
            "runtime_changes_made": False,
            "answer_selection": False,
            "truth_claim": False,
            "official_score": False,
        }

    if queue_path.parent and str(queue_path) != active_policy.queue_path:
        queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(persistence_event_to_dict(persistence_event), ensure_ascii=False, sort_keys=True) + "\n")

    return {
        "success": True,
        "validation_errors": [],
        "event_id": persistence_event.event_id,
        "persistence_performed": True,
        "external_model_calls_made": False,
        "runtime_changes_made": False,
        "answer_selection": False,
        "truth_claim": False,
        "official_score": False,
    }


def load_persistence_events(
    path: str | Path,
    policy: AdvisorQueuePersistencePathPolicy | None = None,
    *,
    public_pilot_mode: bool = False,
) -> dict[str, Any]:
    """Load validated JSONL events from an explicit path."""
    active_policy = policy or create_empty_persistence_path_policy()
    queue_path = Path(path)
    path_errors = validate_queue_storage_path(queue_path, active_policy, public_pilot_mode=public_pilot_mode)
    if path_errors:
        return {"events": [], "validation_errors": path_errors, "load_errors": path_errors}
    if not queue_path.exists():
        return {"events": [], "validation_errors": [], "load_errors": []}

    events: list[AdvisorQueuePersistenceEvent] = []
    validation_errors: list[str] = []
    try:
        with queue_path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    event = persistence_event_from_dict(json.loads(stripped))
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    validation_errors.append(f"line[{index}]: invalid json event: {exc}")
                    continue
                event_errors = validate_persistence_event(event)
                if event_errors:
                    validation_errors.extend(f"line[{index}]: {error}" for error in event_errors)
                    continue
                events.append(event)
    except (FileNotFoundError, PermissionError, OSError) as exc:
        validation_errors.append(f"read failed: {exc}")

    return {"events": events, "validation_errors": validation_errors, "load_errors": validation_errors}


def summarize_persistence_events(events: list[AdvisorQueuePersistenceEvent] | list[dict[str, Any]]) -> dict[str, Any]:
    """Return redacted/count-only summary statistics for persistence events."""
    by_event_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_operator_decision: dict[str, int] = {}
    validation_error_count = 0
    redaction_count = 0
    normalized_events: list[AdvisorQueuePersistenceEvent] = []
    for event in events:
        normalized = event if isinstance(event, AdvisorQueuePersistenceEvent) else persistence_event_from_dict(event)
        normalized_events.append(normalized)
        by_event_type[normalized.event_type] = by_event_type.get(normalized.event_type, 0) + 1
        status_key = normalized.new_status or normalized.previous_status or "unknown"
        by_status[status_key] = by_status.get(status_key, 0) + 1
        by_operator_decision[normalized.operator_decision] = by_operator_decision.get(normalized.operator_decision, 0) + 1
        validation_error_count += len(validate_persistence_event(normalized))
        redaction_count += int(bool(_detect_sensitive_text(_string_values(asdict(normalized)))))

    return {
        "event_count": len(normalized_events),
        "event_type_counts": dict(sorted(by_event_type.items())),
        "status_counts": dict(sorted(by_status.items())),
        "operator_decision_counts": dict(sorted(by_operator_decision.items())),
        "validation_error_count": validation_error_count,
        "redaction_count": redaction_count,
        "persistence_performed": False,
        "external_model_calls_made": False,
        "runtime_changes_made": False,
        "answer_selection": False,
        "truth_claim": False,
        "official_score": False,
        "summary_mode": "redacted_count_only",
    }


def create_status_update_event(
    queue_item_id: str,
    previous_status: str,
    new_status: str,
    operator_decision: str,
    actor: str = "operator",
) -> AdvisorQueuePersistenceEvent:
    """Create an in-memory status update event without writing it."""
    return create_empty_persistence_event(
        event_id=f"status_update:{queue_item_id}:{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        event_type="status_update_requested",
        queue_item_id=queue_item_id,
        previous_status=previous_status,
        new_status=new_status,
        operator_decision=operator_decision,
        actor=actor,
        redacted_summary="status update requested",
    )

