"""Tests for Adaptive Personalization Profile Layer (v24)

Tests personalization_profile.py data models, engine, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.personalization_profile import (
    CommunicationStyle,
    DomainFamiliarity,
    PlanningDepth,
    LearningPace,
    RoutineStability,
    GuidanceTolerance,
    ProfileField,
    PersonalizationProfile,
    PersonalizationEngine,
    apply_profile_to_narrative,
    apply_profile_to_recommendation,
    integrate_with_governance_context,
    integrate_with_proposal_realization,
)


class TestPersonalizationProfileModels(unittest.TestCase):
    """Test personalization profile data models."""

    def test_profile_field_creation(self):
        """Test creating a profile field."""
        field = ProfileField(
            field_name="communication_style",
            value=CommunicationStyle.CONCISE.value,
            confidence_source="user_feedback",
        )
        
        self.assertEqual(field.field_name, "communication_style")
        self.assertEqual(field.value, CommunicationStyle.CONCISE.value)
        self.assertEqual(field.confidence_source, "user_feedback")
        self.assertEqual(field.confidence, 0.5)
        self.assertEqual(field.evidence_count, 0)

    def test_profile_field_update(self):
        """Test updating a profile field."""
        field = ProfileField(
            field_name="domain_familiarity",
            value=DomainFamiliarity.BEGINNER.value,
        )
        
        original_confidence = field.confidence
        field.update(DomainFamiliarity.INTERMEDIATE.value, "observed_pattern")
        
        self.assertEqual(field.value, DomainFamiliarity.INTERMEDIATE.value)
        self.assertEqual(field.evidence_count, 1)
        self.assertGreater(field.confidence, original_confidence)
        self.assertIsNotNone(field.last_updated)

    def test_profile_field_serialization(self):
        """Test profile field to_dict/from_dict."""
        field = ProfileField(
            field_name="planning_depth",
            value=PlanningDepth.BALANCED.value,
            confidence_source="expert_default",
        )
        
        field_dict = field.to_dict()
        field2 = ProfileField.from_dict(field_dict)
        
        self.assertEqual(field.field_name, field2.field_name)
        self.assertEqual(field.value, field2.value)
        self.assertEqual(field.confidence, field2.confidence)

    def test_profile_creation(self):
        """Test creating a personalization profile."""
        profile = PersonalizationProfile()
        
        self.assertEqual(profile.communication_style, CommunicationStyle.MIXED.value)
        self.assertEqual(profile.domain_familiarity, DomainFamiliarity.HYBRID.value)
        self.assertEqual(profile.planning_depth, PlanningDepth.BALANCED.value)
        self.assertEqual(profile.learning_pace, LearningPace.STEADY.value)
        self.assertEqual(profile.routine_stability, RoutineStability.MODERATE_STABILITY.value)
        self.assertEqual(profile.guidance_tolerance, GuidanceTolerance.GUIDED.value)

    def test_profile_field_set(self):
        """Test setting a profile field."""
        profile = PersonalizationProfile()
        profile.set_field("communication_style", CommunicationStyle.DETAILED.value)
        
        self.assertEqual(profile.communication_style, CommunicationStyle.DETAILED.value)
        field = profile.get_field("communication_style")
        self.assertIsNotNone(field)
        self.assertEqual(field.value, CommunicationStyle.DETAILED.value)

    def test_profile_field_update(self):
        """Test updating a profile field via update_field."""
        profile = PersonalizationProfile()
        # First update creates the field with evidence_count=0
        profile.update_field("domain_familiarity", DomainFamiliarity.ADVANCED.value)
        
        field = profile.get_field("domain_familiarity")
        self.assertEqual(field.value, DomainFamiliarity.ADVANCED.value)
        # First update creates field - evidence_count stays at 0 (field created, not updated)
        self.assertEqual(field.evidence_count, 0)
        
        # Second update increments evidence_count
        profile.update_field("domain_familiarity", DomainFamiliarity.EXPERT.value)
        field = profile.get_field("domain_familiarity")
        self.assertEqual(field.evidence_count, 1)

    def test_profile_confidence_tracking(self):
        """Test confidence tracking across updates."""
        profile = PersonalizationProfile()
        
        # Initial confidence should be 0.5
        field = profile.get_field("learning_pace")
        if field is None:
            profile.set_field("learning_pace", LearningPace.RAPID.value)
            field = profile.get_field("learning_pace")
        
        initial_confidence = field.confidence
        
        # Update multiple times
        for _ in range(10):
            profile.update_field("learning_pace", LearningPace.RAPID.value)
        
        field = profile.get_field("learning_pace")
        self.assertIsNotNone(field)
        # Confidence should increase with evidence (saturate at 0.95)
        self.assertGreater(field.confidence, initial_confidence)
        self.assertLessEqual(field.confidence, 0.95)

    def test_profile_serialization(self):
        """Test profile to_dict/from_dict."""
        profile = PersonalizationProfile()
        profile.set_field("communication_style", CommunicationStyle.ANALYTICAL.value)
        profile.set_field("planning_depth", PlanningDepth.THOROUGH.value)
        
        profile_dict = profile.to_dict()
        profile2 = PersonalizationProfile.from_dict(profile_dict)
        
        self.assertEqual(profile2.communication_style, CommunicationStyle.ANALYTICAL.value)
        self.assertEqual(profile2.planning_depth, PlanningDepth.THOROUGH.value)

    def test_profile_summary(self):
        """Test profile summary generation."""
        profile = PersonalizationProfile()
        profile.set_field("guidance_tolerance", GuidanceTolerance.INDEPENDENT.value)
        
        summary = profile.get_profile_summary()
        
        self.assertEqual(summary["communication_style"], CommunicationStyle.MIXED.value)
        self.assertEqual(summary["guidance_tolerance"], GuidanceTolerance.INDEPENDENT.value)
        self.assertIn("average_confidence", summary)
        self.assertIn("field_count", summary)


class TestProfileHints(unittest.TestCase):
    """Test profile hint generation."""

    def test_communication_hint_concise(self):
        """Test communication hint for concise style."""
        profile = PersonalizationProfile()
        profile.set_field("communication_style", CommunicationStyle.CONCISE.value)
        
        hint = profile.get_communication_hint()
        self.assertIn("brief", hint)
        self.assertIn("direct", hint)

    def test_communication_hint_detailed(self):
        """Test communication hint for detailed style."""
        profile = PersonalizationProfile()
        profile.set_field("communication_style", CommunicationStyle.DETAILED.value)
        
        hint = profile.get_communication_hint()
        self.assertIn("thorough", hint)
        self.assertIn("context", hint)

    def test_communication_hint_analytical(self):
        """Test communication hint for analytical style."""
        profile = PersonalizationProfile()
        profile.set_field("communication_style", CommunicationStyle.ANALYTICAL.value)
        
        hint = profile.get_communication_hint()
        self.assertIn("structured", hint)
        self.assertIn("data", hint)

    def test_domain_hint_beginner(self):
        """Test domain hint for beginner familiarity."""
        profile = PersonalizationProfile()
        profile.set_field("domain_familiarity", DomainFamiliarity.BEGINNER.value)
        
        hint = profile.get_domain_hint()
        self.assertIn("foundational", hint)

    def test_domain_hint_expert(self):
        """Test domain hint for expert familiarity."""
        profile = PersonalizationProfile()
        profile.set_field("domain_familiarity", DomainFamiliarity.EXPERT.value)
        
        hint = profile.get_domain_hint()
        self.assertIn("skip fundamentals", hint)

    def test_planning_hint_sketchy(self):
        """Test planning hint for sketchy depth."""
        profile = PersonalizationProfile()
        profile.set_field("planning_depth", PlanningDepth.SKETCHY.value)
        
        hint = profile.get_planning_hint()
        self.assertIn("high-level", hint)

    def test_planning_hint_microscopic(self):
        """Test planning hint for microscopic depth."""
        profile = PersonalizationProfile()
        profile.set_field("planning_depth", PlanningDepth.MICROSCOPIC.value)
        
        hint = profile.get_planning_hint()
        self.assertIn("detailed", hint)

    def test_suggestion_cap_independent(self):
        """Test suggestion cap for independent user."""
        profile = PersonalizationProfile()
        profile.set_field("guidance_tolerance", GuidanceTolerance.INDEPENDENT.value)
        
        self.assertEqual(profile.get_suggestion_cap(), 2)

    def test_suggestion_cap_guided(self):
        """Test suggestion cap for guided user."""
        profile = PersonalizationProfile()
        profile.set_field("guidance_tolerance", GuidanceTolerance.GUIDED.value)
        
        self.assertEqual(profile.get_suggestion_cap(), 5)

    def test_suggestion_cap_supportive(self):
        """Test suggestion cap for supportive user."""
        profile = PersonalizationProfile()
        profile.set_field("guidance_tolerance", GuidanceTolerance.SUPPORTIVE.value)
        
        self.assertEqual(profile.get_suggestion_cap(), 10)


class TestPersonalizationEngine(unittest.TestCase):
    """Test personalization engine."""

    def test_create_profile(self):
        """Test creating a profile via engine."""
        engine = PersonalizationEngine()
        profile = engine.create_profile("user-001")
        
        self.assertEqual(profile.communication_style, CommunicationStyle.MIXED.value)

    def test_get_profile(self):
        """Test retrieving a profile via engine."""
        engine = PersonalizationEngine()
        engine.create_profile("user-001")
        
        profile = engine.get_profile("user-001")
        self.assertIsNotNone(profile)
        
        nonexistent = engine.get_profile("user-999")
        self.assertIsNone(nonexistent)

    def test_update_profile(self):
        """Test updating a profile via engine."""
        engine = PersonalizationEngine()
        profile = engine.update_profile("user-001", "communication_style", CommunicationStyle.DETAILED.value)
        
        self.assertEqual(profile.communication_style, CommunicationStyle.DETAILED.value)
        self.assertEqual(engine.get_profile("user-001"), profile)

    def test_profile_engine_serialization(self):
        """Test engine to_dict."""
        engine = PersonalizationEngine()
        engine.create_profile("user-001")
        engine.update_profile("user-001", "planning_depth", PlanningDepth.THOROUGH.value)
        
        engine_dict = engine.to_dict()
        
        self.assertIn("profile_count", engine_dict)
        self.assertEqual(engine_dict["profile_count"], 1)
        self.assertIn("profiles", engine_dict)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for narratives, recommendations, governance, and realization."""

    def test_apply_profile_to_narrative_adds_context(self):
        """Test that integration adds profile context to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
            "title": "Test narrative",
        }
        
        profile = PersonalizationProfile()
        profile.set_field("communication_style", CommunicationStyle.DETAILED.value)
        
        result = apply_profile_to_narrative(narrative_dict, profile)
        
        self.assertIn("profile_hint", result)
        self.assertIn("communication_hint", result)
        self.assertIn("domain_hint", result)
        self.assertIn("planning_hint", result)
        self.assertEqual(result["communication_hint"], profile.get_communication_hint())

    def test_apply_profile_to_narrative_without_profile(self):
        """Test narrative integration without profile."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = apply_profile_to_narrative(narrative_dict)
        
        self.assertNotIn("profile_hint", result)  # No profile, no profile_hint
        self.assertEqual(result, narrative_dict)  # Unchanged

    def test_apply_profile_to_recommendation_adds_context(self):
        """Test that integration adds profile context to recommendation."""
        recommendation_dict = {
            "recommendation_id": "rec-001",
            "title": "Test recommendation",
            "suggestion_count": 0,
        }
        
        profile = PersonalizationProfile()
        profile.set_field("guidance_tolerance", GuidanceTolerance.INDEPENDENT.value)
        
        result = apply_profile_to_recommendation(recommendation_dict, profile)
        
        self.assertIn("profile_context", result)
        self.assertIn("suggestion_cap", result)
        self.assertEqual(result["suggestion_cap"], 2)
        self.assertEqual(result["suggestions_remaining"], 2)

    def test_apply_profile_to_recommendation_preserves_count(self):
        """Test that suggestion count is preserved and decremented."""
        recommendation_dict = {
            "recommendation_id": "rec-001",
            "suggestion_count": 3,
        }
        
        profile = PersonalizationProfile()
        
        result = apply_profile_to_recommendation(recommendation_dict, profile)
        
        self.assertEqual(result["suggestions_remaining"], 2)  # 5 - 3 = 2

    def test_integrate_with_governance_context_adds_profile(self):
        """Test that integration adds profile context to governance."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        profile = PersonalizationProfile()
        profile.set_field("domain_familiarity", DomainFamiliarity.EXPERT.value)
        
        result = integrate_with_governance_context(governance_dict, profile)
        
        self.assertIn("user_profile_hint", result)
        self.assertIn("preferred_communication", result)
        self.assertEqual(result["domain_familiarity"], DomainFamiliarity.EXPERT.value)

    def test_integrate_with_governance_context_without_profile(self):
        """Test governance integration without profile."""
        governance_dict = {"proposal_id": "prop-001"}
        
        result = integrate_with_governance_context(governance_dict)
        
        self.assertNotIn("user_profile_hint", result)
        self.assertEqual(result, governance_dict)

    def test_integrate_with_proposal_realization_adds_context(self):
        """Test that integration adds profile context to proposal realization."""
        realization_dict = {
            "plan_id": "plan-001",
            "proposal_id": "prop-001",
        }
        
        profile = PersonalizationProfile()
        profile.set_field("learning_pace", LearningPace.RAPID.value)
        
        result = integrate_with_proposal_realization(realization_dict, profile)
        
        self.assertIn("user_profile_context", result)
        self.assertIn("planning_depth_preference", result)
        self.assertEqual(result["learning_pace_preference"], LearningPace.RAPID.value)

    def test_integrate_with_proposal_realization_without_profile(self):
        """Test proposal realization integration without profile."""
        realization_dict = {"plan_id": "plan-001"}
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertNotIn("user_profile_context", result)
        self.assertEqual(result, realization_dict)


if __name__ == "__main__":
    unittest.main()
