import pytest

from weslr.decision_layer import DecisionLayer


SCENARIOS = [
    {
        "name": "safety_critical_override",
        "signals": [
            {"type": "contradiction_detected", "target": "critical_action"},
            {"type": "recurring_bottleneck_detected", "target": "critical_action"},
        ],
        "evidence_state": {
            "evidence_count": 2,
            "confidence_scores": [0.40, 0.45],
            "coverage_domains": ["general"],
        },
        "capability_blocks": [
            {
                "capability": "execute_high_risk",
                "action": "prohibit",
                "reason": "boundary_policy",
                "severity": "critical",
            }
        ],
        "governance_items": [
            {
                "title": "Override high-risk execution",
                "risk_level": "high",
                "recommended_action": "Operator override required",
                "proposal_id": "proposal-high-risk",
                "can_proceed": False,
                "blocking_reasons": ["capability boundary"],
            }
        ],
        "operator_state": {
            "active_bottlenecks": {},
            "next_workflow_recommendation": None,
        },
        "expect": {
            "needs_capability_block": True,
            "needs_governance": True,
            "next_actions_should_be_blocked": True,
            "confidence_max": 0.7,
        },
    },
    {
        "name": "low_risk_enrichment",
        "signals": [],
        "evidence_state": {
            "evidence_count": 4,
            "confidence_scores": [0.55, 0.60, 0.62, 0.58],
            "coverage_domains": ["general", "scientific"],
        },
        "capability_blocks": [],
        "governance_items": [],
        "operator_state": {
            "active_bottlenecks": {},
            "next_workflow_recommendation": {
                "selected_priority": "enrichment-task",
                "reason": "Low-risk enrichment ready",
            },
        },
        "expect": {
            "needs_capability_block": False,
            "needs_governance": False,
            "next_actions_should_be_blocked": False,
            "confidence_min": 0.5,
        },
    },
    {
        "name": "conflict_partial_coverage",
        "signals": [
            {"type": "contradiction_detected", "target": "state_change"},
            {"type": "evidence_gap_unexecuted_paths", "target": "state_change"},
        ],
        "evidence_state": {
            "evidence_count": 2,
            "confidence_scores": [0.48, 0.50],
            "coverage_domains": ["general"],
        },
        "capability_blocks": [
            {
                "capability": "modify_state",
                "action": "restrict",
                "reason": "restricted capability",
                "severity": "high",
            }
        ],
        "governance_items": [
            {
                "title": "Override restricted state change",
                "risk_level": "high",
                "recommended_action": "Operator approval required",
                "proposal_id": "proposal-restrict",
                "can_proceed": False,
                "blocking_reasons": ["restricted capability"],
            }
        ],
        "operator_state": {
            "active_bottlenecks": {},
            "next_workflow_recommendation": None,
        },
        "expect": {
            "needs_capability_block": True,
            "needs_governance": True,
            "next_actions_should_be_blocked": True,
            "confidence_max": 0.6,
        },
    },
]


def _textify(items):
    parts = []
    for i in items or []:
        if isinstance(i, dict):
            parts.append(f"{i.get('title', '')} {i.get('reason', '')} {i.get('recommended_action', '')}")
        else:
            parts.append(str(i))
    return "\n".join(parts).lower()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_compound_multisignal_capability_governance(monkeypatch, scenario):
    layer = DecisionLayer()

    # Deterministic state to avoid external file coupling
    monkeypatch.setattr(layer, "_load_operator_state", lambda: scenario.get("operator_state", {}))
    monkeypatch.setattr(layer, "_get_capability_blocks", lambda: scenario.get("capability_blocks", []))
    monkeypatch.setattr(layer, "_get_evidence_state", lambda: scenario.get("evidence_state", {}))
    monkeypatch.setattr(layer, "_get_governance_review_items", lambda: scenario.get("governance_items", []))
    monkeypatch.setattr(layer, "_get_escalation_items", lambda: [])

    output = layer.compute_with_signals({"background_signals": scenario.get("signals", [])})

    blocked_text = _textify(output.get("blocked_items", []))
    wm_text = _textify(output.get("what_matters_now", []))
    next_text = _textify(output.get("next_actions", []))
    approvals = output.get("approval_queue", [])
    confidence = output.get("confidence", 1.0)

    if scenario["expect"].get("needs_capability_block"):
        assert "capability" in blocked_text or "execute_high_risk" in blocked_text or "modify_state" in blocked_text, (
            f"{scenario['name']}: capability block should surface in blocked items"
        )
    else:
        assert blocked_text == "", f"{scenario['name']}: should have no blockers for low-risk path"

    if scenario["expect"].get("needs_governance"):
        assert len(approvals) > 0, f"{scenario['name']}: governance item should surface in approval_queue"
    else:
        assert approvals == [], f"{scenario['name']}: approval queue should be empty"

    if scenario["expect"].get("next_actions_should_be_blocked"):
        assert "run" not in next_text and "execute" not in next_text, (
            f"{scenario['name']}: execution-oriented next actions should be suppressed when blocked"
        )
    else:
        assert next_text != "", f"{scenario['name']}: should surface next actions for enrichment"

    if "confidence_max" in scenario["expect"]:
        assert confidence <= scenario["expect"]["confidence_max"], (
            f"{scenario['name']}: confidence should be capped when risk/blocks present"
        )
    if "confidence_min" in scenario["expect"]:
        assert confidence >= scenario["expect"]["confidence_min"], (
            f"{scenario['name']}: confidence should remain healthy for low-risk enrichment"
        )

    if scenario["expect"].get("needs_capability_block"):
        assert "block" in wm_text or "governance" in wm_text or "risk" in wm_text or approvals, (
            f"{scenario['name']}: visibility should reflect blockers/governance"
        )
