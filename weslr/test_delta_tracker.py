from weslr.delta_tracker import diff_decisions, delta_is_empty
from weslr.chat_responder import render_decision_for_operator


def test_blocked_to_approved_delta():
    prev = {
        "blocked_items": [{"title": "Execute", "reason": "Approval"}],
        "approval_queue": [{"title": "Approval: execute", "reason": "Risk"}],
        "next_actions": [{"title": "Prepare rollback"}],
        "evidence_gaps": ["No rollback test"],
        "confidence": 0.5,
    }
    curr = {
        "blocked_items": [],
        "approval_queue": [],
        "next_actions": [{"title": "Execute rollout"}, {"title": "Run rollback drill"}],
        "evidence_gaps": [],
        "confidence": 0.6,
    }

    delta = diff_decisions(prev, curr)
    assert delta["unblocked"], "blocked items should be unblocked"
    assert delta["approvals_granted"], "approval should be marked granted"
    assert delta["next_actions_change"]["added"], "new next actions should be detected"
    assert delta["evidence_gaps_change"]["removed"], "gap removal should be captured"
    assert abs(delta["confidence_change"]["delta"] - 0.1) < 1e-6


def test_no_delta_is_empty():
    prev = {"what_matters_now": [{"title": "A", "reason": "r"}], "confidence": 0.4}
    curr = {"what_matters_now": [{"title": "A", "reason": "r"}], "confidence": 0.4}
    delta = diff_decisions(prev, curr)
    assert delta_is_empty(delta)


def test_render_includes_since_last_time_when_delta_present():
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

    resp = render_decision_for_operator(curr, previous_decision=prev)
    content = resp.content.lower()
    assert "since last time" in content
    assert "approvals granted" in content or "approval" in content
    assert "blocked" in content
    assert "confidence" in content
