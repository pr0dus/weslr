from weslr.lineage_diff import diff_lineage


def sample_lineage(conf=0.5, status="pending", chk="c1", adequacy=None):
    return {
        "proposal_id": "p1",
        "workspace_id": "ws1",
        "user_id": "u1",
        "confidence": conf,
        "current_status": status,
        "linked_checkpoint": chk,
        "status_history": [
            {"to_status": status, "timestamp": "t1"}
        ],
        "audit_log": [
            {"action": "view", "timestamp": "t0"}
        ],
        "adequacy": adequacy,
    }


def test_diff_lineage_flags_confidence_drop_and_checkpoint_change():
    a = sample_lineage(conf=0.6, status="pending", chk="c1")
    b = sample_lineage(conf=0.4, status="under_review", chk="c2")
    diff = diff_lineage(a, b)
    assert "confidence_regression" in diff["flags"]
    assert "status_change" in diff["flags"]
    assert "checkpoint_change" in diff["flags"]


def test_diff_lineage_handles_adequacy_change():
    a = sample_lineage(adequacy={"reason": "none"})
    b = sample_lineage(adequacy={"reason": "repetition"})
    diff = diff_lineage(a, b)
    assert diff["field_diffs"]["adequacy"]["from"]["reason"] == "none"
    assert diff["field_diffs"]["adequacy"]["to"]["reason"] == "repetition"


def test_diff_lineage_status_audit_added_removed():
    a = sample_lineage()
    b = sample_lineage()
    b["status_history"].append({"to_status": "approved", "timestamp": "t2"})
    b["audit_log"].append({"action": "review", "timestamp": "t2"})
    diff = diff_lineage(a, b)
    assert diff["status_history_diff"]["added"]
    assert not diff["status_history_diff"]["removed"]
    assert diff["audit_diff"]["added"]
    assert not diff["audit_diff"]["removed"]
