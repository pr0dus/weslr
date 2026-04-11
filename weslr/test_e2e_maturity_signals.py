"""Failing E2E scaffolds for background/scientific maturity.

These tests assert desired runtime behavior for two approved cases:
- Stale data / freshness failure (background analysis)
- Underpowered test / power insufficiency (scientific reasoning)

They currently fail until runtime wiring is implemented.
"""

import copy
import pytest

# Try to import future wiring hooks; fallback to no-op to keep tests runnable.
try:  # pragma: no cover
    from weslr.decision_layer import apply_background_signals
except Exception:  # pragma: no cover
    def apply_background_signals(decision: dict, signals: list):
        return decision

try:  # pragma: no cover
    from weslr.decision_layer import apply_scientific_guidance
except Exception:  # pragma: no cover
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
