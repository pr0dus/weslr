from __future__ import annotations
from typing import Iterable
from .model import LineageOrigin, LineageRecord, StatusEntry, AuditEntry, Status


REQUIRED_ORIGIN_FIELDS = (
    "proposal_id",
    "source_loop_id",
    "workspace_id",
    "user_id",
    "trigger_reason",
    "originating_evidence_signal",
    "timestamp",
    "confidence",
    "linked_checkpoint",
)


class ValidationError(ValueError):
    pass


def _non_empty(value: str, field: str):
    if not value:
        raise ValidationError(f"{field} required")


def validate_origin(origin: LineageOrigin):
    for field in REQUIRED_ORIGIN_FIELDS:
        _non_empty(getattr(origin, field), field)
    if not isinstance(origin.confidence, (int, float)):
        raise ValidationError("confidence must be numeric")
    if origin.confidence < 0 or origin.confidence > 1:
        raise ValidationError("confidence must be between 0 and 1")


def validate_status_entry(entry: StatusEntry, immutable_origin: LineageOrigin, current_status: Status | None):
    if entry.proposal_id != immutable_origin.proposal_id:
        raise ValidationError("proposal_id mismatch")
    if entry.from_status is not None and current_status and entry.from_status != current_status:
        raise ValidationError("from_status does not match current status")
    if entry.to_status == entry.from_status:
        raise ValidationError("status did not change")


def validate_audit_entry(entry: AuditEntry, immutable_origin: LineageOrigin):
    if entry.proposal_id != immutable_origin.proposal_id:
        raise ValidationError("proposal_id mismatch")


def validate_lineage_record(record: LineageRecord):
    validate_origin(record.origin)
    # ensure status history aligns
    last_status = None
    for idx, s in enumerate(record.status_history):
        validate_status_entry(s, record.origin, last_status)
        last_status = s.to_status
    if record.current_status != last_status and last_status is not None:
        raise ValidationError("current_status must match last status entry")


def ensure_no_mutation_attempt(current_origin: LineageOrigin, new_origin: LineageOrigin):
    if current_origin != new_origin:
        raise ValidationError("immutable origin block cannot change")


def ensure_append_only(existing: Iterable, candidate_len: int):
    if candidate_len < len(list(existing)):
        raise ValidationError("append-only violation")
