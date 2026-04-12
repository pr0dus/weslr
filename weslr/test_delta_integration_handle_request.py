from unittest.mock import patch

from weslr.chat_responder import handle_request


def test_handle_request_uses_previous_decision_for_delta():
    prev = {
        "confidence": 0.5,
        "what_matters_now": [{"title": "Risk", "reason": "Approval"}],
        "approval_queue": [{"title": "Approval: Risk", "reason": "Policy"}],
        "blocked_items": [{"title": "Execute", "reason": "Approval"}],
        "next_actions": [{"title": "Prep"}],
        "evidence_gaps": ["Missing test"],
    }
    curr = {
        "confidence": 0.6,
        "what_matters_now": [{"title": "Risk", "reason": "Approved"}],
        "approval_queue": [],
        "blocked_items": [],
        "next_actions": [{"title": "Execute"}],
        "evidence_gaps": [],
    }

    with patch('weslr.decision_layer.DecisionLayer') as MockLayer:
        inst = MockLayer.return_value
        inst.compute_with_signals.return_value = curr
        resp = handle_request({"previous_decision": prev}, persona="general user", domain="general")

    content = resp.content.lower()
    assert "since last time" in content
    assert "approvals granted" in content or "approval" in content
    assert "blocked" in content
    assert "confidence" in content
