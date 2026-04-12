from __future__ import annotations
from typing import Dict, List, Iterable, Optional
from copy import deepcopy
from .model import LineageRecord, LineageOrigin, StatusEntry, AuditEntry, Status
from .validators import (
    validate_origin,
    validate_status_entry,
    validate_audit_entry,
    validate_lineage_record,
    ensure_no_mutation_attempt,
    ensure_append_only,
    ValidationError,
)
from .permissions import PermissionBackend, assert_can_view, assert_can_change_status


class LineageStorage:
    """In-memory append-only storage for first slice (no external effects)."""

    def __init__(self, permission_backend: PermissionBackend):
        self._records: Dict[str, LineageRecord] = {}
        self._perm = permission_backend

    # creation
    def create_lineage(self, origin: LineageOrigin, initial_status: Status) -> LineageRecord:
        if origin.proposal_id in self._records:
            raise ValidationError("lineage already exists")
        validate_origin(origin)
        record = LineageRecord(origin=origin, current_status=initial_status, status_history=[], audit_log=[])
        validate_lineage_record(record)
        self._records[origin.proposal_id] = record
        return deepcopy(record)

    # append status
    def append_status(self, user_id: str, entry: StatusEntry) -> LineageRecord:
        record = self._get_record(entry.proposal_id)
        assert_can_change_status(self._perm, user_id, record.origin.workspace_id)
        validate_status_entry(entry, record.origin, record.current_status)
        new_history = record.status_history + [entry]
        ensure_append_only(record.status_history, len(new_history))
        record.status_history = new_history
        record.current_status = entry.to_status
        validate_lineage_record(record)
        return deepcopy(record)

    # audit on view
    def get(self, user_id: str, proposal_id: str) -> LineageRecord:
        record = self._get_record(proposal_id)
        assert_can_view(self._perm, user_id, record.origin.workspace_id)
        audit = AuditEntry(
            proposal_id=proposal_id,
            action="view",
            actor=user_id,
            timestamp=self._perm.now(),
            context=None,
        )
        self._append_audit(record, audit)
        return deepcopy(record)

    # filtered reads
    def query(
        self,
        user_id: str,
        *,
        proposal_id: Optional[str] = None,
        source_loop_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        user_filter: Optional[str] = None,
        status: Optional[Status] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> List[LineageRecord]:
        records = []
        for rec in self._records.values():
            if proposal_id and rec.origin.proposal_id != proposal_id:
                continue
            if source_loop_id and rec.origin.source_loop_id != source_loop_id:
                continue
            if workspace_id and rec.origin.workspace_id != workspace_id:
                continue
            if user_filter and rec.origin.user_id != user_filter:
                continue
            if status and rec.current_status != status:
                continue
            if since and rec.origin.timestamp < since:
                continue
            if until and rec.origin.timestamp > until:
                continue
            assert_can_view(self._perm, user_id, rec.origin.workspace_id)
            audit = AuditEntry(
                proposal_id=rec.origin.proposal_id,
                action="view",
                actor=user_id,
                timestamp=self._perm.now(),
                context="query",
            )
            self._append_audit(rec, audit)
            records.append(deepcopy(rec))
        return records

    def _append_audit(self, record: LineageRecord, audit: AuditEntry):
        validate_audit_entry(audit, record.origin)
        record.audit_log = record.audit_log + [audit]

    def _get_record(self, proposal_id: str) -> LineageRecord:
        if proposal_id not in self._records:
            raise KeyError("lineage not found")
        return self._records[proposal_id]
