from weslr.chat_responder import render_decision_for_operator


def test_render_decision_for_operator_includes_explanation_style():
    decision = {
        "confidence": 0.62,
        "what_matters_now": [
            {"title": "Escalation: safety risk", "reason": "Requires operator review", "confidence": 0.6}
        ],
        "blocked_items": [
            {"title": "Capability block: execute_high_risk", "reason": "boundary_policy"}
        ],
        "next_actions": ["Review/reconcile conflicting operational signals for service_x"],
        "approval_queue": [
            {"title": "Approval required: High-risk execution", "reason": "Operator approval required"}
        ],
    }

    resp = render_decision_for_operator(decision, persona="engineer", domain="technical")

    content = resp.content.lower()
    # ExplanationSession prefixes with lead text (e.g., "Finding:" or "It looks like")
    assert "finding:" in content or "looks like" in content, "explanation lead should be applied"
    assert "blocked" in content, "blocked state should remain visible"
    assert "approval" in content or "awaiting" in content, "approvals should remain visible"
    assert "confidence" in content or "signal strength" in content, "uncertainty/confidence should surface"
