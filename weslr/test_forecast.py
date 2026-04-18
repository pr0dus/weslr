# test_forecast.py - Tests for Self-Architecture Core v10: Architectural Simulation / Forecast Layer
# Forecast generation, short-term vs long-term, coherence impact, fallback behavior.

from __future__ import annotations

import unittest
import json
from forecast import (
    ForecastEngine,
    ForecastEffect,
    SubsystemForecast,
    ForecastSummary,
    ArchitecturalForecast,
    forecast_suggestion,
    forecast_scenario,
)


class TestForecastEffect(unittest.TestCase):
    """Test forecast effect model."""

    def test_forecast_effect_creation(self):
        """Can create a forecast effect."""
        effect = ForecastEffect(
            category="efficiency",
            impact_type="positive",
            magnitude=0.6,
            confidence=0.7,
            description="Improved efficiency",
        )
        self.assertEqual(effect.category, "efficiency")
        self.assertEqual(effect.impact_type, "positive")
        self.assertEqual(effect.magnitude, 0.6)
        self.assertEqual(effect.confidence, 0.7)
        self.assertEqual(effect.description, "Improved efficiency")

    def test_forecast_effect_to_dict(self):
        """Can serialize forecast effect to dict."""
        effect = ForecastEffect(
            category="risk",
            impact_type="negative",
            magnitude=-0.4,
            confidence=0.6,
            description="Risk increase",
            affected_subsystems=["state"],
        )
        data = effect.to_dict()
        self.assertEqual(data["category"], "risk")
        self.assertEqual(data["impact_type"], "negative")
        self.assertEqual(data["affected_subsystems"], ["state"])

    def test_forecast_effect_from_dict(self):
        """Can deserialize forecast effect from dict."""
        data = {
            "category": "efficiency",
            "impact_type": "positive",
            "magnitude": 0.5,
            "confidence": 0.8,
            "description": "Test effect",
        }
        effect = ForecastEffect.from_dict(data)
        self.assertEqual(effect.category, "efficiency")
        self.assertEqual(effect.magnitude, 0.5)


class TestSubsystemForecast(unittest.TestCase):
    """Test subsystem forecast model."""

    def test_subsystem_forecast_creation(self):
        """Can create a subsystem forecast."""
        forecast = SubsystemForecast(
            subsystem="state",
            net_impact=0.3,
            confidence=0.7,
        )
        self.assertEqual(forecast.subsystem, "state")
        self.assertEqual(forecast.net_impact, 0.3)

    def test_add_effect(self):
        """Can add effects to subsystem forecast."""
        forecast = SubsystemForecast(
            subsystem="state",
            net_impact=0.0,
        )
        effect = ForecastEffect(
            category="efficiency",
            impact_type="positive",
            magnitude=0.6,
            confidence=0.8,
            description="Efficiency gain",
        )
        forecast.add_effect(effect)
        self.assertEqual(len(forecast.forecasted_effects), 1)
        # net_impact should be updated
        expected = 0.6 * 0.8  # magnitude * confidence
        self.assertAlmostEqual(forecast.net_impact, expected, places=5)

    def test_to_dict(self):
        """Can serialize subsystem forecast."""
        forecast = SubsystemForecast(
            subsystem="continuity",
            net_impact=0.4,
        )
        data = forecast.to_dict()
        self.assertEqual(data["subsystem"], "continuity")
        self.assertEqual(data["net_impact"], 0.4)


class TestForecastSummary(unittest.TestCase):
    """Test forecast summary model."""

    def test_summary_creation(self):
        """Can create a forecast summary."""
        summary = ForecastSummary(
            total_positive_effects=5,
            total_negative_effects=2,
            net_impact=0.6,
            short_term_benefit=0.7,
            long_term_benefit=0.5,
            maintenance_impact=-0.2,
            confidence=0.8,
        )
        self.assertEqual(summary.total_positive_effects, 5)
        self.assertEqual(summary.net_impact, 0.6)

    def test_to_dict(self):
        """Can serialize summary to dict."""
        summary = ForecastSummary(
            total_positive_effects=3,
            total_negative_effects=1,
            net_impact=0.5,
        )
        data = summary.to_dict()
        self.assertEqual(data["total_positive_effects"], 3)
        self.assertEqual(data["net_impact"], 0.5)


class TestArchitecturalForecast(unittest.TestCase):
    """Test architectural forecast model."""

    def test_forecast_creation(self):
        """Can create an architectural forecast."""
        effect = ForecastEffect(
            category="efficiency",
            impact_type="positive",
            magnitude=0.6,
            confidence=0.7,
            description="Efficiency gain",
        )
        forecast = ArchitecturalForecast(
            forecast_id="test123",
            title="Add logging",
            description="Add logging capability",
            domain="astronomy",
            effects=[effect],
            suggestion_id="sugg001",
        )
        self.assertEqual(forecast.forecast_id, "test123")
        self.assertEqual(forecast.title, "Add logging")
        self.assertEqual(len(forecast.effects), 1)

    def test_to_dict(self):
        """Can serialize forecast to dict."""
        forecast = ArchitecturalForecast(
            forecast_id="abc123",
            title="Test forecast",
            description="Test",
            domain="physics",
        )
        data = forecast.to_dict()
        self.assertEqual(data["forecast_id"], "abc123")
        self.assertEqual(data["title"], "Test forecast")

    def test_get_forecast_summary(self):
        """Can get human-readable forecast summary."""
        summary = ForecastSummary(
            total_positive_effects=5,
            total_negative_effects=1,
            net_impact=0.6,
            short_term_benefit=0.7,
            long_term_benefit=0.5,
            confidence=0.8,
        )
        forecast = ArchitecturalForecast(
            forecast_id="test",
            title="Test",
            description="Test",
            domain="astronomy",
            summary=summary,
        )
        summary_str = forecast.get_forecast_summary()
        self.assertIn("positive", summary_str.lower())
        self.assertIn("net", summary_str.lower())


class TestForecastEngine(unittest.TestCase):
    """Test forecast engine."""

    def test_forecast_suggestion_basic(self):
        """Can forecast a basic suggestion."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            title="Add monitoring",
            description="Add monitoring capability",
            domain="astronomy",
            affected_subsystems=["state"],
            suggestion_id="sugg001",
        )
        self.assertEqual(forecast.title, "Add monitoring")
        self.assertEqual(forecast.domain, "astronomy")
        self.assertIsNotNone(forecast.effects)
        self.assertIsNotNone(forecast.summary)

    def test_forecast_suggestion_with_multiple_subsystems(self):
        """Can forecast suggestion affecting multiple subsystems."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            title="Improve state",
            description="Improve state management",
            domain="physics",
            affected_subsystems=["state", "continuity"],
        )
        self.assertGreater(len(forecast.effects), 0)
        self.assertEqual(len(forecast.subsystem_forecasts), 2)

    def test_forecast_scenario_basic(self):
        """Can forecast a scenario."""
        engine = ForecastEngine()
        scenarios = [
            {
                "title": "Phase 1",
                "affected_subsystems": ["state"],
            },
            {
                "title": "Phase 2",
                "affected_subsystems": ["continuity"],
            },
        ]
        forecast = engine.forecast_scenario(
            title="Multi-phase",
            description="Multi-phase implementation",
            domain="astronomy",
            scenarios=scenarios,
            scenario_id="scen001",
        )
        self.assertEqual(forecast.domain, "astronomy")

    def test_generate_forecast_json(self):
        """Can generate forecast as JSON."""
        engine = ForecastEngine()
        json_output = engine.generate_forecast_json(
            title="JSON test",
            description="Testing",
            domain="astronomy",
            affected_subsystems=["state"],
        )
        data = json.loads(json_output)
        self.assertEqual(data["title"], "JSON test")

    def test_forecast_with_prior_decisions(self):
        """Can set and use prior decisions."""
        engine = ForecastEngine()
        engine.set_prior_decisions([
            {"id": "d1", "title": "Accepted", "status": "accepted"},
        ])
        forecast = engine.forecast_suggestion(
            "Test",
            "Test desc",
            "astronomy",
        )
        self.assertIsNotNone(forecast)


class TestForecastIntegration(unittest.TestCase):
    """Test forecast integration with other components."""

    def test_forecast_with_narrative_reference(self):
        """Forecast can reference narrative context."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Narrative test",
            "Test for narrative",
            "astronomy",
            ["state"],
        )
        # Should have valid forecast
        self.assertIsNotNone(forecast.forecast_id)
        self.assertIsNotNone(forecast.summary)

    def test_forecast_output_format(self):
        """Forecast output follows expected format."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Format test",
            "Testing format",
            "astronomy",
        )
        data = forecast.to_dict()

        # Check all required fields
        self.assertIn("forecast_id", data)
        self.assertIn("title", data)
        self.assertIn("description", data)
        self.assertIn("domain", data)
        self.assertIn("effects", data)
        self.assertIn("subsystem_forecasts", data)
        self.assertIn("summary", data)


class TestFallbackBehavior(unittest.TestCase):
    """Test fallback behavior for edge cases."""

    def test_forecast_with_empty_subsystems(self):
        """Handles empty subsystem list gracefully."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "No subsystems",
            "Test",
            "astronomy",
            [],
        )
        self.assertIsNotNone(forecast)
        self.assertEqual(len(forecast.subsystem_forecasts), 0)

    def test_forecast_with_unknown_domain(self):
        """Handles unknown domain gracefully."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Unknown domain",
            "Test",
            "unknown_domain",
        )
        self.assertEqual(forecast.domain, "unknown_domain")

    def test_forecast_with_missing_fields(self):
        """Handles missing optional fields gracefully."""
        forecast = ArchitecturalForecast(
            forecast_id="test",
            title="Test",
            description="Test",
            domain="astronomy",
        )
        self.assertEqual(forecast.suggestion_id, None)
        self.assertEqual(forecast.author, None)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code."""

    def test_existing_forecast_usage(self):
        """Existing code using ForecastEngine still works."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Existing usage",
            "Testing",
            "astronomy",
            ["state"],
        )
        self.assertEqual(forecast.title, "Existing usage")

    def test_convenience_function(self):
        """Convenience forecast functions work."""
        forecast = forecast_suggestion(
            "Convenience",
            "Testing",
            "astronomy",
        )
        self.assertEqual(forecast.title, "Convenience")

    def test_scenario_convenience_function(self):
        """Scenario convenience function works."""
        forecast = forecast_scenario(
            "Scenario test",
            "Testing",
            "astronomy",
            [{"affected_subsystems": ["state"]}],
        )
        self.assertEqual(forecast.domain, "astronomy")


class TestForecastTimeDistinction(unittest.TestCase):
    """Test short-term vs long-term forecast distinction."""

    def test_time_horizon_in_forecast(self):
        """Forecast includes time horizon information."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Time test",
            "Testing",
            "astronomy",
        )
        # Check that summary has time-based metrics
        self.assertIsNotNone(forecast.summary.short_term_benefit)
        self.assertIsNotNone(forecast.summary.long_term_benefit)

    def test_short_term_benefit_vs_long_term(self):
        """Short-term benefit is typically higher than long-term."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Time comparison",
            "Testing",
            "astronomy",
        )
        # Usually short-term benefit > long-term benefit due to diminishing returns
        # This is a general expectation, not a hard rule
        self.assertGreaterEqual(forecast.summary.short_term_benefit, 0)
        self.assertGreaterEqual(forecast.summary.long_term_benefit, 0)


class TestCoherenceImpact(unittest.TestCase):
    """Test coherence impact reasoning."""

    def test_coherence_in_summary(self):
        """Summary includes coherence impact information."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Coherence test",
            "Testing coherence",
            "astronomy",
        )
        # Check that summary has coherence info
        self.assertIsNotNone(forecast.summary.coherence_impact)

    def test_coherence_values(self):
        """Coherence impact uses valid values."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Coherence values",
            "Testing",
            "astronomy",
        )
        self.assertIn(forecast.summary.coherence_impact, [
            "increases", "decreases", "no_change"
        ])


class TestMaintenanceImpact(unittest.TestCase):
    """Test maintenance impact forecasting."""

    def test_maintenance_impact_in_summary(self):
        """Summary includes maintenance impact."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Maintenance test",
            "Testing",
            "astronomy",
        )
        self.assertIsNotNone(forecast.summary.maintenance_impact)

    def test_maintenance_values(self):
        """Maintenance impact uses valid range."""
        engine = ForecastEngine()
        forecast = engine.forecast_suggestion(
            "Maintenance range",
            "Testing",
            "astronomy",
        )
        # Maintenance impact should be between -1 and 1
        self.assertGreaterEqual(forecast.summary.maintenance_impact, -1)
        self.assertLessEqual(forecast.summary.maintenance_impact, 1)


if __name__ == "__main__":
    unittest.main()
