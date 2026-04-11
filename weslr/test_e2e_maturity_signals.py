"""Failing E2E scaffolds for background/scientific maturity.

These tests assert desired runtime behavior for maturity signals:
- Stale data / freshness failure (background)
- Evidence gap / unexecuted paths (background)
- Underpowered test / power insufficiency (scientific)
- Model drift required (scientific)
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

        # Expect confidence reduction
        assert updated.get("confidence", 1.0) < decision["confidence"], "confidence should drop on stale data"
        # Expect blocker or next action referencing refresh
        has_refresh_blocker = any("refresh" in str(item).lower() for item in updated.get("blocked_items", []))
        has_refresh_action = any("refresh" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_refresh_blocker or has_refresh_action, "should add refresh telemetry action/blocker"
        # Expect visibility message
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

        # Expect confidence reduction
        assert updated.get("confidence", 1.0) < decision["confidence"], "confidence should drop on evidence gap"
        # Expect action/blocker to run targeted tests/logs
        has_action = any("test" in str(item).lower() or "log" in str(item).lower() for item in updated.get("next_actions", []))
        has_blocker = any("test" in str(item).lower() or "log" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_action or has_blocker, "should add targeted test/log action/blocker"
        # Expect visibility message
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "gap" in wm.lower() or "unexecuted" in wm.lower(), "should surface evidence gap rationale"

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

        # Expect blocker/hold
        has_blocker = any("underpowered" in str(item).lower() or "power" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_blocker, "should add underpowered blocker/hold"
        # Expect next action to increase samples or redesign
        has_action = any("sample" in str(item).lower() or "design" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_action, "should add action to increase sample size or redesign"
        # Expect visibility message
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "power" in wm.lower() or "underpowered" in wm.lower(), "should surface underpowered rationale"
        # Expect promotion/approval held via lowered confidence or explicit hold
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

        # Expect blocker/hold for drift check
        has_blocker = any("drift" in str(item).lower() for item in updated.get("blocked_items", []))
        assert has_blocker, "should add drift-required blocker/hold"
        # Expect next action to run drift detection
        has_action = any("drift" in str(item).lower() or "monitor" in str(item).lower() for item in updated.get("next_actions", []))
        assert has_action, "should add drift-check action"
        # Expect visibility message
        wm = "\n".join(str(x) for x in updated.get("what_matters_now", []))
        assert "drift" in wm.lower(), "should surface drift rationale"
        # Confidence should not increase; may drop or hold
        assert updated.get("confidence", 1.0) <= decision["confidence"], "confidence should not increase when drift check is required"
