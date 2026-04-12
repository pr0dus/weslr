import pytest
from types import SimpleNamespace
from weslr.lineage.model import LineageOrigin, StatusEntry, Status
from weslr.lineage.storage import LineageStorage
from weslr.lineage.validators import ValidationError


def origin():
    return LineageOrigin(
        proposal_id="p1",
        source_loop_id="loop1",
        workspace_id="ws1",
        user_id="u1",
        trigger_reason="coverage_gap",
        originating_evidence_signal="signalA",
        timestamp="2026-04-12T10:00:00Z",
        confidence=0.7,
        linked_checkpoint="chk1",
    )


def perm_backend(view=True, change=True):
    return SimpleNamespace(
        can_view_lineage=lambda u, w: view,
        can_change_status=lambda u, w: change,
        now=lambda: "2026-04-12T10:05:00Z",
    )


def test_create_and_get_lineage():
    storage = LineageStorage(perm_backend())
    storage.create_lineage(origin(), Status.PENDING)
    rec = storage.get("u1", "p1")
    assert rec.origin.proposal_id == "p1"
    assert rec.current_status == Status.PENDING
    assert len(rec.audit_log) == 1


def test_append_status():
    storage = LineageStorage(perm_backend())
    storage.create_lineage(origin(), Status.PENDING)
    storage.append_status("u1", StatusEntry(proposal_id="p1", from_status=Status.PENDING, to_status=Status.UNDER_REVIEW, actor="u1", timestamp="2026-04-12T10:02:00Z"))
    rec = storage.get("u1", "p1")
    assert rec.current_status == Status.UNDER_REVIEW
    assert len(rec.status_history) == 1


def test_append_status_invalid_transition():
    storage = LineageStorage(perm_backend())
    storage.create_lineage(origin(), Status.PENDING)
    with pytest.raises(ValidationError):
        storage.append_status("u1", StatusEntry(proposal_id="p1", from_status=Status.UNDER_REVIEW, to_status=Status.PENDING, actor="u1", timestamp="2026-04-12T10:02:00Z"))


def test_permission_view_denied():
    storage = LineageStorage(perm_backend(view=False))
    storage.create_lineage(origin(), Status.PENDING)
    with pytest.raises(PermissionError):
        storage.get("u2", "p1")


def test_permission_status_denied():
    storage = LineageStorage(perm_backend(change=False))
    storage.create_lineage(origin(), Status.PENDING)
    with pytest.raises(PermissionError):
        storage.append_status("u2", StatusEntry(proposal_id="p1", from_status=Status.PENDING, to_status=Status.APPROVED, actor="u2", timestamp="2026-04-12T10:02:00Z"))


def test_query_filters_and_audit():
    storage = LineageStorage(perm_backend())
    storage.create_lineage(origin(), Status.PENDING)
    res = storage.query("u1", workspace_id="ws1")
    assert len(res) == 1
    assert len(res[0].audit_log) == 1  # view audit from query
