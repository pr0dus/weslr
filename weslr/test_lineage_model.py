import pytest
from weslr.lineage.model import (
    LineageOrigin,
    LineageRecord,
    StatusEntry,
    AuditEntry,
    Status,
)
from weslr.lineage.validators import (
    validate_origin,
    validate_status_entry,
    validate_audit_entry,
    validate_lineage_record,
    ValidationError,
)


def sample_origin():
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


def test_validate_origin_ok():
    validate_origin(sample_origin())


def test_validate_origin_confidence_bounds():
    with pytest.raises(ValidationError):
        validate_origin(sample_origin().__class__(**{**sample_origin().__dict__, "confidence": 2}))


def test_lineage_record_status_alignment():
    origin = sample_origin()
    s1 = StatusEntry(proposal_id="p1", from_status=None, to_status=Status.PENDING, actor="u1", timestamp="2026-04-12T10:01:00Z")
    s2 = StatusEntry(proposal_id="p1", from_status=Status.PENDING, to_status=Status.UNDER_REVIEW, actor="u2", timestamp="2026-04-12T10:02:00Z")
    record = LineageRecord(origin=origin, current_status=Status.UNDER_REVIEW, status_history=[s1, s2])
    validate_lineage_record(record)


def test_lineage_record_status_mismatch():
    origin = sample_origin()
    s1 = StatusEntry(proposal_id="p1", from_status=None, to_status=Status.PENDING, actor="u1", timestamp="2026-04-12T10:01:00Z")
    record = LineageRecord(origin=origin, current_status=Status.UNDER_REVIEW, status_history=[s1])
    with pytest.raises(ValidationError):
        validate_lineage_record(record)


def test_audit_entry_proposal_mismatch():
    origin = sample_origin()
    audit = AuditEntry(proposal_id="other", action="view", actor="u1", timestamp="2026-04-12T10:03:00Z")
    with pytest.raises(ValidationError):
        validate_audit_entry(audit, origin)

def test_origin_from_change_proposal_reuses_id_and_timestamp():
    class DummyProposal:
        def __init__(self):
            self.proposal_id = "p123"
            self.created_at = "2026-04-12T09:00:00Z"
            self.evidence_confidence = 0.55
            self.source_scenario = "loopX"

    origin = LineageOrigin.from_change_proposal(
        DummyProposal(),
        workspace_id="ws1",
        user_id="u1",
        trigger_reason="coverage_gap",
        originating_evidence_signal="signalA",
        linked_checkpoint="chk1",
    )
    assert origin.proposal_id == "p123"
    assert origin.timestamp == "2026-04-12T09:00:00Z"
    assert origin.confidence == 0.55
    assert origin.source_loop_id == "loopX"
