"""Tests for Tension / Tradeoff Resolution Layer (v34)

Tests tension_resolution.py data models, engine, resolver, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.tension_resolution import (
    TensionType,
    ResolutionStrategy,
    SeverityLevel,
    HoldBackCondition,
    Tension,
    TensionSet,
    TensionResolutionEngine,
    TensionResolver,
    integrate_with_goal_hierarchy,
    integrate_with_adaptive_guidance,
    integrate_with_operator_context,
    integrate_with_outcome_feedback,
)


class TestTensionModels(unittest.TestCase):
    """Test tension data models."""

    def test_tension_creation(self):
        """Test creating a tension."""
        tension = Tension(
            tension_id="tension-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="user_preference",
            factor_b="safety_constraint",
            factor_a_type="preference",
            factor_b_type="constraint",
            description="User prefers speed over safety",
            severity=SeverityLevel.MEDIUM.value,
        )
        
        self.assertEqual(tension.tension_id, "tension-001")
        self.assertEqual(tension.tension_type, TensionType.GOAL_CONFLICT.value)
        self.assertEqual(tension.severity, SeverityLevel.MEDIUM.value)

    def test_tension_apply_resolution(self):
        """Test applying resolution to tension."""
        tension = Tension(
            tension_id="tension-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="speed",
            factor_b="safety",
            description="Speed vs safety",
        )
        
        self.assertFalse(tension.is_resolved())
        
        tension.apply_resolution(ResolutionStrategy.COMPROMISE.value, "Balance speed and safety")
        
        self.assertTrue(tension.is_resolved())
        self.assertEqual(tension.resolution_strategy, ResolutionStrategy.COMPROMISE.value)
        self.assertIsNotNone(tension.resolved_at)

    def test_tension_serialization(self):
        """Test tension to_dict/from_dict."""
        tension = Tension(
            tension_id="tension-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="speed",
            factor_b="safety",
            description="Speed vs safety",
        )
        
        tension_dict = tension.to_dict()
        tension2 = Tension.from_dict(tension_dict)
        
        self.assertEqual(tension.tension_id, tension2.tension_id)
        self.assertEqual(tension.description, tension2.description)

    def test_tension_set_creation(self):
        """Test creating a tension set."""
        tension_set = TensionSet(
            tension_set_id="set-001",
            recommendation_id="rec-001",
        )
        
        self.assertEqual(tension_set.tension_set_id, "set-001")
        self.assertEqual(tension_set.recommendation_id, "rec-001")
        self.assertEqual(len(tension_set.tensions), 0)

    def test_tension_set_add_tension(self):
        """Test adding tension to set."""
        tension_set = TensionSet(
            tension_set_id="set-001",
            recommendation_id="rec-001",
        )
        
        tension = Tension(
            tension_id="tension-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="a",
            factor_b="b",
            factor_a_type="type_a",
            factor_b_type="type_b",
            description="Test",
        )
        
        tension_set.add_tension(tension)
        
        self.assertEqual(len(tension_set.tensions), 1)
        self.assertTrue(tension_set.has_unresolved)
        self.assertEqual(tension_set.highest_severity, SeverityLevel.LOW.value)

    def test_tension_set_get_unresolved(self):
        """Test getting unresolved tensions."""
        tension_set = TensionSet(
            tension_set_id="set-001",
            recommendation_id="rec-001",
        )
        
        tension1 = Tension(
            tension_id="tension-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="a",
            factor_b="b",
            description="Unresolved",
        )
        
        tension2 = Tension(
            tension_id="tension-002",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="c",
            factor_b="d",
            description="Resolved",
        )
        tension2.apply_resolution(ResolutionStrategy.COMPROMISE.value, "Resolved")
        
        tension_set.add_tension(tension1)
        tension_set.add_tension(tension2)
        
        unresolved = tension_set.get_unresolved_tensions()
        
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0].tension_id, "tension-001")

    def test_tension_set_get_hold_back_conditions(self):
        """Test getting hold-back conditions."""
        tension_set = TensionSet(
            tension_set_id="set-001",
            recommendation_id="rec-001",
            enable_hold_back=True,
        )
        
        # Add unresolved tension
        tension = Tension(
            tension_id="tension-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="a",
            factor_b="b",
            description="Conflict",
            severity=SeverityLevel.HIGH.value,
        )
        tension_set.add_tension(tension)
        
        conditions = tension_set.get_hold_back_conditions()
        
        self.assertIn(HoldBackCondition.TENSION_UNRESOLVED.value, conditions)

    def test_tension_set_serialization(self):
        """Test tension set to_dict/from_dict."""
        tension_set = TensionSet(
            tension_set_id="set-001",
            recommendation_id="rec-001",
        )
        
        tension_set_dict = tension_set.to_dict()
        tension_set2 = TensionSet.from_dict(tension_set_dict)
        
        self.assertEqual(tension_set.tension_set_id, tension_set2.tension_set_id)


class TestTensionResolutionEngine(unittest.TestCase):
    """Test tension resolution engine."""

    def setUp(self):
        """Set up test engine."""
        self.engine = TensionResolutionEngine()

    def test_detect_tension(self):
        """Test detecting a tension."""
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="speed",
            factor_b="safety",
            factor_a_type="preference",
            factor_b_type="constraint",
            description="Speed vs safety",
            severity=SeverityLevel.MEDIUM.value,
        )
        
        self.assertIsNotNone(tension)
        self.assertIn(tension.tension_id, self.engine.tensions)

    def test_create_tension_set(self):
        """Test creating a tension set."""
        tension_set = self.engine.create_tension_set("rec-001")
        
        self.assertIsNotNone(tension_set)
        self.assertIn(tension_set.tension_set_id, self.engine.tension_sets)

    def test_add_tension_to_set(self):
        """Test adding tension to set."""
        tension_set = self.engine.create_tension_set("rec-001")
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="a",
            factor_b="b",
            factor_a_type="type_a",
            factor_b_type="type_b",
            description="Test",
        )
        
        self.engine.add_tension_to_set(tension_set.tension_set_id, tension)
        
        retrieved = self.engine.get_tension_set(tension_set.tension_set_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved.tensions), 1)

    def test_apply_resolution(self):
        """Test applying resolution."""
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="a",
            factor_b="b",
            description="Test",
        )
        
        # Create a tension set and add the tension
        tension_set = self.engine.create_tension_set("rec-001")
        self.engine.add_tension_to_set(tension_set.tension_set_id, tension)
        
        result = self.engine.apply_resolution(
            tension_set.tension_set_id,
            tension.tension_id,
            ResolutionStrategy.COMPROMISE.value,
            "Resolved by compromise",
        )
        
        self.assertTrue(result)
        self.assertTrue(tension.is_resolved())

    def test_get_hold_back_status(self):
        """Test getting hold-back status."""
        tension_set = self.engine.create_tension_set("rec-001")
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="a",
            factor_b="b",
            factor_a_type="type_a",
            factor_b_type="type_b",
            description="Test",
            severity=SeverityLevel.HIGH.value,
        )
        self.engine.add_tension_to_set(tension_set.tension_set_id, tension)
        
        status = self.engine.get_hold_back_status(tension_set.tension_set_id)
        
        self.assertTrue(status["hold_back"])
        self.assertIn("unresolved", status["recommendation"].lower())


class TestTensionResolver(unittest.TestCase):
    """Test tension resolver."""

    def setUp(self):
        """Set up test engine and resolver."""
        self.engine = TensionResolutionEngine()
        self.resolver = TensionResolver(self.engine)

    def test_resolve_goal_conflict_priority_a(self):
        """Test resolving goal conflict with priority A."""
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.GOAL_CONFLICT.value,
            factor_a="high_priority_goal",
            factor_b="low_priority_goal",
            description="Priority conflict",
        )
        
        result = self.resolver.resolve_goal_conflict(tension, 0.9, 0.3)
        
        self.assertEqual(result["strategy"], ResolutionStrategy.PRIORITY_OVERRIDE.value)

    def test_resolve_safety_preference_high_risk(self):
        """Test resolving safety vs preference with high risk."""
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.SAFETY_PREFERENCE.value,
            factor_a="user_preference",
            factor_b="safety_constraint",
            description="Safety preference conflict",
        )
        
        result = self.resolver.resolve_safety_preference(tension, 0.8, 0.5)
        
        self.assertEqual(result["strategy"], ResolutionStrategy.REJECT.value)

    def test_resolve_short_long_term_long_term_priority(self):
        """Test resolving short-term vs long-term with long-term priority."""
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.SHORT_LONG_TERM.value,
            factor_a="short_term",
            factor_b="long_term",
            description="Timeframe conflict",
        )
        
        result = self.resolver.resolve_short_long_term(tension, 0.5, 0.8)
        
        self.assertEqual(result["strategy"], ResolutionStrategy.DEFER.value)

    def test_resolve_household_individual_household_priority(self):
        """Test resolving household vs individual with household priority."""
        tension = self.engine.detect_tension(
            recommendation_id="rec-001",
            tension_type=TensionType.HOUSEHOLD_INDIVIDUAL.value,
            factor_a="household_benefit",
            factor_b="individual_benefit",
            description="Scope conflict",
        )
        
        result = self.resolver.resolve_household_individual(tension, 0.7, 0.3, 0.8)
        
        self.assertEqual(result["strategy"], ResolutionStrategy.PRIORITY_OVERRIDE.value)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for goal hierarchy, adaptive guidance, operator context, and outcome feedback."""

    def test_integrate_with_goal_hierarchy_adds_tension_context(self):
        """Test that integration adds tension context to goal hierarchy."""
        hierarchy_dict = {
            "hierarchy_id": "hierarchy-001",
        }
        
        result = integrate_with_goal_hierarchy(hierarchy_dict)
        
        self.assertIn("active_tensions", result)
        self.assertTrue(result["tension_resolver_available"])

    def test_integrate_with_adaptive_guidance_adds_tension_context(self):
        """Test that integration adds tension context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("tension_resolved", result)
        self.assertIn("tension_hold_back", result)
        self.assertIn("resolution_strategy", result)

    def test_integrate_with_operator_context_adds_tension_context(self):
        """Test that integration adds tension context to operator context."""
        context_dict = {
            "surface_id": "surface-001",
        }
        
        result = integrate_with_operator_context(context_dict)
        
        self.assertIn("tensions_detected", result)
        self.assertIn("hold_back_active", result)
        self.assertIn("resolved_tensions", result)

    def test_integrate_with_outcome_feedback_adds_tension_context(self):
        """Test that integration adds tension context to outcome feedback."""
        feedback_dict = {
            "feedback_id": "fb-001",
        }
        
        result = integrate_with_outcome_feedback(feedback_dict)
        
        self.assertIn("tension_context", result)
        self.assertIn("resolution_applied", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing tension context."""
        hierarchy_dict = {
            "hierarchy_id": "hierarchy-001",
            "active_tensions": ["tension-001", "tension-002"],
            "tension_resolver_available": False,
        }
        
        result = integrate_with_goal_hierarchy(hierarchy_dict)
        
        self.assertEqual(len(result["active_tensions"]), 2)
        self.assertFalse(result["tension_resolver_available"])


if __name__ == "__main__":
    unittest.main()
