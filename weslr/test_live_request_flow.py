from weslr.chat_responder import handle_request


def test_live_request_flow_renders_decision_with_explanation():
    request = {
        "background_signals": [{"type": "stale_data", "target": "svc", "freshness_days": 9}],
        "scientific_guidance": [{"type": "underpowered_test", "target": "exp", "planned_samples": 100, "required_samples": 400}],
    }

    resp = handle_request(request, persona="engineer", domain="technical")

    content = resp.content.lower()
    assert "finding:" in content or "looks like" in content, "explanation lead should be applied"
    assert "blocked" in content, "blockers should be visible"
    # approvals may be empty; ensure wording doesn't hide approvals section when present
    assert "approval" in content or "awaiting" in content or "blocked" in content, "approvals/blockers visibility should remain"
    assert "confidence" in content or "signal strength" in content, "uncertainty/confidence should surface"
    # actions should be present even if empty list
    assert hasattr(resp, "actions"), "actions should be included on response"
