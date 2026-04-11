import pytest

from weslr.decision_layer import DecisionLayer


SCENARIOS = [
    {
        "name": "operational_recovery_stale_conflict",
        "background_signals": [
            {"type": "stale_data", "target": "service_x", "freshness_days": 10},
            {"type": "contradiction_detected", "target": "service_x", "details": "metrics vs errors"},
        ],
        "scientific_guidance": [],
        "evidence_state": {
            "evidence_count": 3,
            "confidence_scores": [0.55, 0.58, 0.6],
            "coverage_domains": ["general", "ops"],
        },
        "capability_blocks": [],
        "governance_items": [],
        "operator_state": {
            "active_bottlenecks": {},
            "next_workflow_recommendation": None,
        },
        "expect": {
            "confidence_drop": True,
            "has_blockers": True,
            "has_next_actions": True,
            "approvals": False,
            "visibility_mentions": ["refresh", "reconcile"],
        },
    },
    {
        "name": "safety_critical_needs_approval",
        "background_signals": [],
        "scientific_guidance": [],
        "evidence_state": {
            "evidence_count": 1,
            "confidence_scores": [0.4],
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
                "title": "High-risk execution",
                "risk_level": "high",
                "recommended_action": "Operator approval required",
                "proposal_id": "proposal-highrisk",
                "can_proceed": False,
                "blocking_reasons": ["capability boundary"],
            }
        ],
        "operator_state": {
            "active_bottlenecks": {},
            "next_workflow_recommendation": None,
        },
        "expect": {
            "confidence_cap": 0.7,
            "has_blockers": True,
            "approvals": True,
            "suppress_execute_actions": True,
            "wm_mentions": ["capability", "block"],
        },
    },
    {
        "name": "low_risk_enrichment_path",
        "background_signals": [],
        "scientific_guidance": [],
        "evidence_state": {
            "evidence_count": 5,
            "confidence_scores": [0.55, 0.6, 0.62, 0.58, 0.6],
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
            "confidence_min": 0.5,
            "has_blockers": False,
            "approvals": False,
            "has_next_actions": True,
            "visibility_mentions": ["workflow", "enrichment"],
        },
    },
    {
        "name": "scientific_conflict_evidence_gap_governance_hold",
        "background_signals": [
            {"type": "contradiction_detected", "target": "model_a"},
        ],
        "scientific_guidance": [
            {"type": "contradictory_findings_reconciliation_required", "target": "model_a"},
            {"type": "evidence_sufficiency_threshold_not_met", "target": "model_a"},
        ],
        "evidence_state": {
            "evidence_count": 2,
            "confidence_scores": [0.45, 0.5],
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
                "title": "Restricted state change",
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
            "confidence_cap": 0.6,
            "has_blockers": True,
            "approvals": True,
            "has_next_actions": True,  # evidence gathering should appear
            "suppress_execute_actions": True,
            "visibility_mentions": ["reconcile", "evidence", "capability", "threshold"],
        },
    },
]


def _textify(items):
    return "\n".join(str(i) for i in items or []).lower()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_realistic_flows(monkeypatch, scenario):
    layer = DecisionLayer()

    # Deterministic state to avoid external file coupling
    monkeypatch.setattr(layer, "_load_operator_state", lambda: scenario.get("operator_state", {}))
    monkeypatch.setattr(layer, "_get_capability_blocks", lambda: scenario.get("capability_blocks", []))
    monkeypatch.setattr(layer, "_get_evidence_state", lambda: scenario.get("evidence_state", {}))
    monkeypatch.setattr(layer, "_get_governance_review_items", lambda: scenario.get("governance_items", []))
    monkeypatch.setattr(layer, "_get_escalation_items", lambda: [])

    output = layer.compute_with_signals({
        "background_signals": scenario.get("background_signals", []),
        "scientific_guidance": scenario.get("scientific_guidance", []),
    })

    blocked = _textify(output.get("blocked_items", []))
    wm = _textify(output.get("what_matters_now", []))
    next_actions = _textify(output.get("next_actions", []))
    approvals = output.get("approval_queue", [])
    conf = output.get("confidence", 1.0)
    visibility = "\n".join([wm, blocked, next_actions]).lower()

    if scenario["expect"].get("confidence_drop"):
        assert conf < 0.7, f"{scenario['name']}: expected confidence drop"
    if "confidence_cap" in scenario["expect"]:
        assert conf <= scenario["expect"]["confidence_cap"], f"{scenario['name']}: confidence should be capped"
    if "confidence_min" in scenario["expect"]:
        assert conf >= scenario["expect"]["confidence_min"], f"{scenario['name']}: confidence should stay healthy"

    if scenario["expect"].get("has_blockers"):
        assert blocked != "", f"{scenario['name']}: blockers should surface"
    else:
        assert blocked == "", f"{scenario['name']}: should have no blockers"

    if scenario["expect"].get("approvals"):
        assert len(approvals) > 0, f"{scenario['name']}: approval expected"
    else:
        assert approvals == [], f"{scenario['name']}: approval queue should be empty"

    if scenario["expect"].get("has_next_actions"):
        assert next_actions != "", f"{scenario['name']}: next actions expected"
    if scenario["expect"].get("suppress_execute_actions"):
        assert "run " not in next_actions and "execute" not in next_actions, f"{scenario['name']}: execution actions should be suppressed"

    for token in scenario["expect"].get("visibility_mentions", []):
        assert token in visibility, f"{scenario['name']}: expected '{token}' in visible surfaces"
