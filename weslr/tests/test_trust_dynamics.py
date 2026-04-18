"""Tests for Trust / Relationship Dynamics Layer (v37)

Tests trust_dynamics.py data models, manager, and integration hooks.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.trust_dynamics import (
    TrustLevel,
    FrictionLevel,
    GuidanceMode,
    RecoveryState,
    TrustMetrics,
    FrictionFactors,
    RelationshipState,
    TrustStateManager,
    integrate_with_adaptive_guidance,
    integrate_with_outcome_feedback,
    integrate_with_intervention_timing,
    integrate_with_compromise_explanation,
)


class TestTrustMetrics(unittest.TestCase):
    """Test trust metrics data model."""

    def test_initial_state(self):
        """Test initial trust metrics state."""
        metrics = TrustMetrics()
        
        self.assertEqual(metrics.trust_score, 0.5)
        self.assertEqual(metrics.trust_level, TrustLevel.MODERATE.value)
        self.assertEqual(metrics.total_interactions, 0)

    def test_update_from_positive_interaction(self):
        """Test updating metrics from positive interaction."""
        metrics = TrustMetrics()
        
        metrics.update_from_interaction(is_positive=True)
        
        self.assertEqual(metrics.total_interactions, 1)
        self.assertEqual(metrics.positive_interactions, 1)
        # Initial score remains until we have enough data (>= 3 interactions)
        self.assertEqual(metrics.trust_score, 0.5)
        # But trust level still updates based on initial conditions
        self.assertEqual(metrics.trust_level, TrustLevel.MODERATE.value)

    def test_update_from_positive_interaction_after_three(self):
        """Test updating metrics from positive interaction after establishing history."""
        metrics = TrustMetrics()
        
        # Establish initial history
        for _ in range(3):
            metrics.update_from_interaction(is_positive=True)
        
        self.assertEqual(metrics.total_interactions, 3)
        self.assertEqual(metrics.positive_interactions, 3)
        self.assertEqual(metrics.trust_score, 1.0)
        self.assertEqual(metrics.trust_level, TrustLevel.HIGH.value)

    def test_update_from_negative_interaction(self):
        """Test updating metrics from negative interaction."""
        metrics = TrustMetrics()
        
        # Start with some interactions to get meaningful ratio
        metrics.update_from_interaction(is_positive=True)
        metrics.update_from_interaction(is_positive=True)
        metrics.update_from_interaction(is_positive=False)
        
        self.assertEqual(metrics.total_interactions, 3)
        self.assertEqual(metrics.positive_interactions, 2)
        self.assertEqual(metrics.negative_interactions, 1)
        self.assertEqual(metrics.trust_score, 2/3)
        self.assertEqual(metrics.trust_level, TrustLevel.MODERATE.value)

    def test_trust_level_boundaries(self):
        """Test trust level transitions at boundaries."""
        # High trust (>= 0.7)
        metrics = TrustMetrics()
        metrics.trust_score = 0.75
        metrics._update_trust_level()
        self.assertEqual(metrics.trust_level, TrustLevel.HIGH.value)
        
        # Moderate trust (>= 0.4, < 0.7)
        metrics.trust_score = 0.5
        metrics._update_trust_level()
        self.assertEqual(metrics.trust_level, TrustLevel.MODERATE.value)
        
        # Low trust (< 0.4)
        metrics.trust_score = 0.3
        metrics._update_trust_level()
        self.assertEqual(metrics.trust_level, TrustLevel.LOW.value)

    def test_serialization(self):
        """Test trust metrics to_dict/from_dict."""
        metrics = TrustMetrics(
            trust_score=0.75,
            total_interactions=5,
            positive_interactions=4,
        )
        
        metrics_dict = metrics.to_dict()
        metrics2 = TrustMetrics.from_dict(metrics_dict)
        
        self.assertEqual(metrics.trust_score, metrics2.trust_score)
        self.assertEqual(metrics.total_interactions, metrics2.total_interactions)
        self.assertEqual(metrics.positive_interactions, metrics2.positive_interactions)


class TestFrictionFactors(unittest.TestCase):
    """Test friction factors data model."""

    def test_initial_state(self):
        """Test initial friction state."""
        factors = FrictionFactors()
        
        self.assertEqual(factors.friction_score, 0.0)
        self.assertEqual(factors.friction_level, FrictionLevel.LOW.value)
        self.assertFalse(factors.has_resistance_markers)

    def test_record_rejection(self):
        """Test recording a rejection."""
        factors = FrictionFactors()
        
        factors.record_rejection(reason="Timing issue")
        
        self.assertEqual(factors.rejected_suggestions, 1)
        self.assertIsNotNone(factors.last_friction_event_at)
        self.assertIn("Timing issue", factors.resistance_reasons)

    def test_resistance_markers(self):
        """Test resistance marker detection."""
        factors = FrictionFactors()
        
        # Multiple rejections to trigger high friction
        for _ in range(5):
            factors.record_rejection("Pending")
        
        self.assertEqual(factors.friction_level, FrictionLevel.RESISTANCE.value)
        self.assertTrue(factors.has_resistance_markers)

    def test_serialization(self):
        """Test friction factors to_dict/from_dict."""
        factors = FrictionFactors(
            rejected_suggestions=3,
            ignored_recommendations=2,
            clarification_requests=1,
        )
        
        factors_dict = factors.to_dict()
        factors2 = FrictionFactors.from_dict(factors_dict)
        
        self.assertEqual(factors.rejected_suggestions, factors2.rejected_suggestions)
        self.assertEqual(factors.ignored_recommendations, factors2.ignored_recommendations)


class TestRelationshipState(unittest.TestCase):
    """Test relationship state data model."""

    def test_initial_state(self):
        """Test initial relationship state."""
        state = RelationshipState(relationship_id="test-001")
        
        self.assertEqual(state.relationship_id, "test-001")
        self.assertEqual(state.guidance_mode, GuidanceMode.BALANCED.value)
        self.assertEqual(state.explanation_depth, 2)
        self.assertEqual(state.recovery_state, RecoveryState.STABLE.value)

    def test_record_positive_interaction(self):
        """Test recording a positive interaction."""
        state = RelationshipState(relationship_id="test-001")
        
        state.record_interaction(is_positive=True)
        
        self.assertEqual(state.trust_metrics.total_interactions, 1)
        self.assertEqual(state.trust_metrics.positive_interactions, 1)
        self.assertEqual(state.friction_factors.friction_score, 0.0)

    def test_record_negative_interaction(self):
        """Test recording a negative interaction."""
        state = RelationshipState(relationship_id="test-001")
        
        # Start with some positive interactions
        state.record_interaction(is_positive=True)
        state.record_interaction(is_positive=True)
        state.record_interaction(is_positive=True)
        
        # Then a negative one
        state.record_interaction(is_positive=False, reason="Rejected suggestion")
        
        self.assertEqual(state.trust_metrics.negative_interactions, 1)
        self.assertEqual(state.friction_factors.rejected_suggestions, 1)

    def test_guidance_mode_adaptation(self):
        """Test guidance mode adaptation based on trust/friction."""
        state = RelationshipState(relationship_id="test-001")
        
        # High trust, low friction -> concise guidance
        for _ in range(5):
            state.record_interaction(is_positive=True)
        
        self.assertEqual(state.guidance_mode, GuidanceMode.CONCISE.value)
        self.assertEqual(state.explanation_depth, 1)
        self.assertEqual(state.proactivity_score, 0.8)

        # Add friction -> more cautious guidance
        state.record_interaction(is_positive=False, reason="Rejected")
        state.record_interaction(is_positive=False, reason="Rejected")
        
        self.assertIn(state.guidance_mode, [GuidanceMode.BALANCED.value, GuidanceMode.REASSURING.value])

    def test_recovery_state(self):
        """Test recovery state transitions."""
        state = RelationshipState(relationship_id="test-001")
        
        # Create friction
        for _ in range(3):
            state.record_interaction(is_positive=False, reason="Rejected")
        
        self.assertEqual(state.recovery_state, RecoveryState.RECOVERING.value)
        self.assertIsNotNone(state.recovery_started_at)

    def test_serialization(self):
        """Test relationship state to_dict/from_dict."""
        state = RelationshipState(relationship_id="test-001")
        state.record_interaction(is_positive=True)
        
        state_dict = state.to_dict()
        state2 = RelationshipState.from_dict(state_dict)
        
        self.assertEqual(state.relationship_id, state2.relationship_id)
        self.assertEqual(state.trust_metrics.total_interactions, state2.trust_metrics.total_interactions)


class TestTrustStateManager(unittest.TestCase):
    """Test trust state manager."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TrustStateManager(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_relationship(self):
        """Test creating a relationship state."""
        state = self.manager.create_relationship("test-001")
        
        self.assertIsNotNone(state)
        self.assertEqual(state.relationship_id, "test-001")

    def test_get_relationship(self):
        """Test getting a relationship state."""
        self.manager.create_relationship("test-001")
        
        state = self.manager.get_relationship("test-001")
        self.assertIsNotNone(state)

    def test_get_default_relationship(self):
        """Test getting default relationship."""
        state = self.manager.get_default_relationship()
        
        self.assertIsNotNone(state)
        self.assertEqual(state.relationship_id, "default")

    def test_record_interaction(self):
        """Test recording an interaction."""
        state = self.manager.record_interaction("test-001", is_positive=True)
        
        self.assertEqual(state.trust_metrics.positive_interactions, 1)

    def test_record_positive_interaction(self):
        """Test convenience method for positive interaction."""
        state = self.manager.record_positive_interaction("test-001")
        
        self.assertEqual(state.trust_metrics.positive_interactions, 1)

    def test_record_negative_interaction(self):
        """Test convenience method for negative interaction."""
        state = self.manager.record_negative_interaction("test-001", reason="Rejected")
        
        self.assertEqual(state.trust_metrics.negative_interactions, 1)
        self.assertEqual(state.friction_factors.rejected_suggestions, 1)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        self.manager.create_relationship("test-001")
        self.manager.record_positive_interaction("test-001")
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["relationship_count"], 1)
        self.assertIn("relationships", manager_dict)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for adaptive guidance, outcome feedback, intervention timing, and compromise explanation."""

    def test_integrate_with_adaptive_guidance_adds_relationship_context(self):
        """Test that integration adds relationship context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("relationship_context", result)
        self.assertIn("guidance_mode", result)
        self.assertEqual(result["guidance_mode"], GuidanceMode.BALANCED.value)
        self.assertEqual(result["explanation_depth"], 2)

    def test_integrate_with_outcome_feedback_adds_relationship_context(self):
        """Test that integration adds relationship context to outcome feedback."""
        feedback_dict = {
            "feedback_id": "feedback-001",
        }
        
        result = integrate_with_outcome_feedback(feedback_dict)
        
        self.assertIn("relationship_id", result)
        self.assertIn("trust_impact", result)
        self.assertIn("friction_impact", result)

    def test_integrate_with_intervention_timing_adds_relationship_context(self):
        """Test that integration adds relationship context to intervention timing."""
        timing_dict = {
            "timing_id": "timing-001",
        }
        
        result = integrate_with_intervention_timing(timing_dict)
        
        self.assertIn("relationship_id", result)
        self.assertIn("caution_level", result)
        self.assertEqual(result["caution_level"], "normal")
        self.assertIn("proactive_readiness", result)

    def test_integrate_with_compromise_explanation_adds_relationship_context(self):
        """Test that integration adds relationship context to compromise explanation."""
        explanation_dict = {
            "explanation_id": "exp-001",
        }
        
        result = integrate_with_compromise_explanation(explanation_dict)
        
        self.assertIn("relationship_id", result)
        self.assertIn("explanation_burden", result)
        self.assertEqual(result["explanation_burden"], "standard")

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing relationship context."""
        guidance_dict = {
            "guidance_id": "guidance-001",
            "relationship_context": {"trust_score": 0.8},
            "guidance_mode": "concise",
            "explanation_depth": 1,
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertEqual(result["relationship_context"], {"trust_score": 0.8})
        self.assertEqual(result["guidance_mode"], "concise")
        self.assertEqual(result["explanation_depth"], 1)


if __name__ == "__main__":
    unittest.main()
