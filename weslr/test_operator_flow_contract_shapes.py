from weslr.chat_responder import format_status_summary


def _sample_decision():
    return {
        "confidence": 0.55,
        "what_matters_now": [
            {
                "title": "Stale telemetry",
                "reason": "Telemetry is stale beyond threshold",
                "confidence": 0.55,
                "provenance": {
                    "memory_context": {"has_memory_context": True, "signal": "Past incident: stale telemetry led to blind spots"},
                    "concept_context": {"has_concept_context": True, "signal": "Decision quality drops with stale metrics"},
                },
                "source_modules": ["ops_reasoner"],
            }
        ],
        "blocked_items": [
            {
                "title": "Refresh telemetry",
                "reason": "Evidence gap until recent data collected",
                "source_modules": ["ops_reasoner"],
                "recommended_action": "Refresh metrics pipeline",
            }
        ],
        "next_actions": [
            {
                "title": "Run telemetry refresh",
                "reason": "Needed to close evidence gap",
                "gated_by": "approval-refresh",
                "provenance": {
                    "concept_context": {"has_concept_context": True, "signal": "Refresh aligns with risk window"}
                },
            }
        ],
        "approval_queue": [
            {
                "title": "Approval: telemetry refresh",
                "reason": "Change touches shared pipeline",
                "risk_level": "medium",
                "recommended_action": "Approve controlled refresh window",
            }
        ],
        "evidence_gaps": ["Stale telemetry window"],
    }


def test_status_summary_matches_operator_contract_sections():
    decision = _sample_decision()
    summary = format_status_summary(decision, mode="detailed")

    assert "Status summary (operator contract):" in summary
    assert "What matters now:" in summary
    assert "Blocked items" in summary
    assert "Approval queue" in summary
    assert "Next actions" in summary
    assert "Evidence/uncertainty:" in summary
    assert "confidence" in summary.lower()
    assert "To unblock" in summary
    assert "Next after approval" in summary


def test_short_mode_omits_provenance_details():
    decision = _sample_decision()
    summary = format_status_summary(decision, mode="short")

    assert "What matters now:" in summary
    assert "Next actions (ordered):" in summary
    assert "Provenance:" not in summary
    assert "gated by" in summary.lower()
