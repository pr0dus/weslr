import pytest
from weslr.cognitive_dialogue import (
    DialogueState,
    explain_inadequacy,
    propose_improvement,
    handle_operator_response,
    attach_lineage,
    record_exchange,
)


def test_explain_inadequacy_includes_evidence_and_lineage():
    resp = explain_inadequacy("weak answer", ["low confidence"], ["log:missed context"], {"proposal_id": "p1"})
    assert resp["type"] == "inadequacy_explanation"
    assert "log:missed context" in resp["evidence"]
    assert resp["lineage_ref"]["proposal_id"] == "p1"


def test_propose_improvement_carries_risk_and_rollback():
    prop = propose_improvement(["low confidence"], "add reflection step", risk="low", rollback="disable reflection")
    assert prop["risk"] == "low"
    assert "rollback" in prop
    assert prop["requires_approval"] is True


def test_handle_operator_response_includes_gate_and_risk():
    prop = propose_improvement([], "refine reply", risk="medium", rollback="revert to checkpoint")
    r1 = handle_operator_response(prop, "approve")
    assert r1["approved"] is True
    assert r1["approval_gate_reminder"]
    assert r1["risk"] == "medium"
    assert r1["rollback"] == "revert to checkpoint"
    r2 = handle_operator_response(prop, "refine", refinement="shorter")
    assert r2["refined"] is True
    assert r2["refinement"] == "shorter"


def test_dialogue_state_lineage_and_exchange():
    st = DialogueState(persona="tester", domain="general")
    attach_lineage(st, {"proposal_id": "p1"})
    record_exchange(st, "hello", {"response": "hi"})
    assert st.lineage_refs[0]["proposal_id"] == "p1"
    assert st.exchanges[0]["user"] == "hello"


def test_invalid_operator_action():
    prop = propose_improvement([], "refine reply")
    with pytest.raises(ValueError):
        handle_operator_response(prop, "invalid")
