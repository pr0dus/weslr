import pytest
from weslr.cognitive_dialogue import (
    DialogueState,
    explain_inadequacy,
    propose_improvement,
    handle_operator_response,
    attach_lineage,
    record_exchange,
)


def test_explain_inadequacy_includes_findings_and_lineage():
    resp = explain_inadequacy("weak answer", ["low confidence"], {"proposal_id": "p1"})
    assert resp["type"] == "inadequacy_explanation"
    assert "low confidence" in resp["findings"]
    assert resp["lineage_ref"]["proposal_id"] == "p1"


def test_propose_improvement_requires_approval():
    prop = propose_improvement(["low confidence"], "add reflection step")
    assert prop["requires_approval"] is True
    assert prop["type"] == "improvement_proposal"


def test_handle_operator_response_approve_deny_refine():
    prop = propose_improvement([], "refine reply")
    r1 = handle_operator_response(prop, "approve")
    assert r1["approved"] is True
    r2 = handle_operator_response(prop, "deny")
    assert r2["approved"] is False
    r3 = handle_operator_response(prop, "refine", refinement="shorter")
    assert r3["refined"] is True
    assert r3["refinement"] == "shorter"


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
