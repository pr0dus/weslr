"""Failing E2E scaffolds for background/scientific maturity.

These tests assert desired runtime behavior for maturity signals:
- Stale data / freshness failure (background)
- Evidence gap / unexecuted paths (background)
- Contradiction detected (background)
- Recurring bottleneck detected (background)
- Repeated override detected (background)
- Underpowered test / power insufficiency (scientific)
- Model drift required (scientific)
- Domain safety constraint required (scientific)
- Causal hypothesis required (scientific)
- Contradictory findings reconciliation required (scientific)
"""

import copy
import pytest

# Try to import future wiring hooks; fallback to no-op to keep tests runnable.
try:  # pragma: no cover
    from weslr.decision_layer import apply_background_signals, apply_scientific_guidance
except Exception:  # pragma: no cover
    def apply_background_signals(decision: dict, signals: list):
        return decision
    def apply_scientific_guidance(decision: dict, guidance: list):
        return decision


def _base_decision(title: str, confidence: float = 0.6) -> dict:
    return {
        "what_matters_now": [{"title": title, "confidence": confidence}],
        "blocked_items": [],
        "next_actions": [],
        "confidence": confidence,
        "provenance": {},
    }


class TestE2EMaturitySignals:
    def test_stale_data_background_signal(self):
        decision = _base_decision("service x reliability", confidence=0.6)
        signals = [
            {
                "type": "stale_data",
                "target": "service_x_metrics",
                "freshness_days": 8,
                "source": "telemetry_monitor",
            }
        ]

        updated = apply_background_signals(copy.deepcopy(decision), signals)

        assert updated.get("confidence", 1.0) < decision["confidence"], "confidence should drop on stale data"
        has_refresh_blocker = any("refresh" in str(item).lower() for item in updated.get("blocked_items", []))
        has_refresh_action = any("refresh" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_refresh_blocker or has_refresh_action, "should add refresh telemetry action/blocker"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "stale" in wm.lower() or "fresh" in wm.lower(), "should surface stale-data warning"

    def test_evidence_gap_unexecuted_paths(self):
        decision = _base_decision("module a reliability", confidence=0.65)
        signals = [
            {
                "type": "evidence_gap_unexecuted_paths",
                "target": "module_a",
                "paths": ["path1", "path2"],
                "source": "coverage_report",
            }
        ]

        updated = apply_background_signals(copy.deepcopy(decision), signals)

        assert updated.get("confidence", 1.0) < decision["confidence"], "confidence should drop on evidence gap"
        has_action = any("test" in str(item).lower() or "log" in str(item).lower() for item in updated.get("next_actions", []))
        has_blocker = any("test" in str(item).lower() or "log" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_action or has_blocker, "should add targeted test/log action/blocker"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "gap" in wm.lower() or "unexecuted" in wm.lower(), "should surface evidence gap rationale"

    def test_contradiction_detected(self):
        decision = _base_decision("service y status", confidence=0.7)
        signals = [
            {
                "type": "contradiction_detected",
                "target": "service_y",
                "details": "metric up but errors up",
                "source": "monitoring",
            }
        ]

        updated = apply_background_signals(copy.deepcopy(decision), signals)

        assert updated.get("confidence", 1.0) < decision["confidence"], "confidence should drop on contradiction"
        has_action = any("reconcile" in str(item).lower() or "review" in str(item).lower() for item in updated.get("next_actions", []))
        has_blocker = any("reconcile" in str(item).lower() or "review" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_action or has_blocker, "should add contradiction review/reconcile action/blocker"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "contradiction" in wm.lower() or "conflict" in wm.lower(), "should surface contradiction rationale"

    def test_recurring_bottleneck_detected(self):
        decision = _base_decision("queue latency", confidence=0.6)
        signals = [
            {
                "type": "recurring_bottleneck_detected",
                "target": "queue_service",
                "source": "bottleneck_monitor",
            }
        ]

        updated = apply_background_signals(copy.deepcopy(decision), signals)

        has_action = any("bottleneck" in str(item).lower() or "mitigate" in str(item).lower() for item in updated.get("next_actions", []))
        has_blocker = any("bottleneck" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_action or has_blocker, "should add bottleneck investigation/mitigation action"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "bottleneck" in wm.lower(), "should surface recurring bottleneck rationale"

    def test_underpowered_test_scientific_signal(self):
        decision = _base_decision("feature y experiment", confidence=0.7)
        guidance = [
            {
                "type": "underpowered_test",
                "target": "feature_y_experiment",
                "planned_samples": 500,
                "required_samples": 2000,
                "power": 0.8,
            }
        ]

        updated = apply_scientific_guidance(copy.deepcopy(decision), guidance)

        has_blocker = any("underpowered" in str(item).lower() or "power" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_blocker, "should add underpowered blocker/hold"
        has_action = any("sample" in str(item).lower() or "design" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_action, "should add action to increase sample size or redesign"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "power" in wm.lower() or "underpowered" in wm.lower(), "should surface underpowered rationale"
        lowered_confidence = updated.get("confidence", 1.0) <= decision["confidence"]
        has_hold_flag = any("hold" in str(item).lower() for item in updated.get("blocked_items", []))
        assert lowered_confidence or has_hold_flag, "should not allow promotion until power is sufficient"

    def test_model_drift_required(self):
        decision = _base_decision("model z deployment", confidence=0.75)
        guidance = [
            {
                "type": "model_drift_required",
                "target": "model_z",
                "drift_window": "7d",
                "source": "drift_monitor",
            }
        ]

        updated = apply_scientific_guidance(copy.deepcopy(decision), guidance)

        has_blocker = any("drift" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_blocker, "should add drift-required blocker/hold"
        has_action = any("drift" in str(item).lower() or "monitor" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_action, "should add drift-check action"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "drift" in wm.lower(), "should surface drift rationale"
        assert updated.get("confidence", 1.0) <= decision["confidence"], "confidence should not increase when drift check is required"

    def test_domain_safety_constraint_required(self):
        decision = _base_decision("pii handling change", confidence=0.7)
        guidance = [
            {
                "type": "domain_safety_constraint_required",
                "target": "pii_masking",
                "constraint": "requires masking check",
                "source": "safety_policy",
            }
        ]

        updated = apply_scientific_guidance(copy.deepcopy(decision), guidance)

        has_blocker = any("safety" in str(item).lower() or "constraint" in str(item).lower() or "compliance" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_blocker, "should add safety constraint blocker/hold"
        has_action = any("safety" in str(item).lower() or "mask" in str(item).lower() or "check" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_action, "should add safety-check action"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "safety" in wm.lower() or "constraint" in wm.lower(), "should surface safety rationale"
        assert updated.get("confidence", 1.0) <= decision["confidence"], "confidence should not increase when safety constraint is pending"

    def test_causal_hypothesis_required(self):
        decision = _base_decision("feature z correlation", confidence=0.65)
        guidance = [
            {
                "type": "causal_hypothesis_required",
                "target": "feature_z",
                "source": "analysis",
            }
        ]

        updated = apply_scientific_guidance(copy.deepcopy(decision), guidance)

        has_blocker = any("causal" in str(item).lower() or "hypothesis" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_blocker, "should add causal hypothesis blocker/hold"
        has_action = any("causal" in str(item).lower() or "validation" in str(item).lower() or "ablation" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_action, "should add causal validation action"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "causal" in wm.lower(), "should surface causal rationale"
        assert updated.get("confidence", 1.0) <= decision["confidence"], "confidence should not increase when causal hypothesis is pending"

    def test_contradictory_findings_reconciliation_required(self):
        decision = _base_decision("study abc results", confidence=0.7)
        guidance = [
            {
                "type": "contradictory_findings_reconciliation_required",
                "target": "study_abc",
                "source": "research_sync",
            }
        ]

        updated = apply_scientific_guidance(copy.deepcopy(decision), guidance)

        has_blocker = any("reconcile" in str(item).lower() or "conflict" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_blocker, "should add reconciliation blocker/hold"
        has_action = any("reconcile" in str(item).lower() or "compare" in str(item).lower() or "resolve" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_action, "should add reconciliation action"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "reconcile" in wm.lower() or "conflict" in wm.lower(), "should surface contradictory findings rationale"
        assert updated.get("confidence", 1.0) <= decision["confidence"], "confidence should not increase when findings conflict"

    def test_unresolved_aging_item_detected(self):
        decision = _base_decision("aging ticket", confidence=0.65)
        signals = [
            {
                "type": "unresolved_aging_item_detected",
                "target": "ticket-123",
                "age_days": 14,
                "source": "ops_review",
            }
        ]

        updated = apply_background_signals(copy.deepcopy(decision), signals)

        assert updated.get("confidence", 1.0) < decision["confidence"], "confidence should drop for aging item"
        has_blocker = any("aging" in str(item).lower() or "unresolved" in str(item).lower() for item in updated.get("blocked_items", []))
        has_action = any("review" in str(item).lower() or "resolve" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_blocker or has_action, "should add aging-item blocker/action"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "aging" in wm.lower() or "unresolved" in wm.lower(), "should surface aging-item rationale"

    def test_evidence_sufficiency_threshold_not_met(self):
        decision = _base_decision("release decision", confidence=0.7)
        guidance = [
            {
                "type": "evidence_sufficiency_threshold_not_met",
                "target": "release_candidate",
                "source": "evidence_review",
            }
        ]

        updated = apply_scientific_guidance(copy.deepcopy(decision), guidance)

        assert updated.get("confidence", 1.0) < decision["confidence"], "confidence should drop when threshold not met"
        has_blocker = any("threshold" in str(item).lower() or "evidence" in str(item).lower() for item in updated.get("blocked_items", []))
        has_action = any("evidence" in str(item).lower() or "gather" in str(item).lower() or "sufficiency" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_blocker or has_action, "should add evidence-threshold blocker/action"
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "threshold" in wm.lower() or "evidence" in wm.lower(), "should surface evidence-threshold rationale"


    def test_dedup_same_target_prefers_scientific_conflict(self):
        decision = _base_decision("study xyz", confidence=0.7)
        signals = [
            {"type": "contradiction_detected", "target": "study_xyz", "source": "ops"},
            {"type": "contradictory_findings_reconciliation_required", "target": "study_xyz", "source": "research"},
        ]
        updated = apply_background_signals(decision, signals)
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        # Only scientific conflict should remain; operational contradiction suppressed
        assert "operational contradiction" not in wm.lower(), "operational contradiction should be suppressed when scientific conflict exists"

    def test_no_dedup_when_targets_differ(self):
        decision = _base_decision("multi domain", confidence=0.7)
        signals = [
            {"type": "contradiction_detected", "target": "service_a", "source": "ops"},
            {"type": "contradictory_findings_reconciliation_required", "target": "study_b", "source": "research"},
        ]
        updated = apply_background_signals(decision, signals)
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "operational contradiction" in wm.lower(), "operational contradiction should show for service_a"
        assert "reconcile" in wm.lower() or "conflict" in wm.lower(), "scientific conflict should show for study_b"
