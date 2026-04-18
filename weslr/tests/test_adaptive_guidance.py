"""Tests for Adaptive Guidance / Recommendation Context Layer (v27)

Tests adaptive_guidance.py data models, engine, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.adaptive_guidance import (
    RecommendationStrength,
    GuidanceContextMode,
    EvidenceQuality,
    UserProfileContext,
    GuidanceContext,
    AdaptiveGuidanceEngine,
    integrate_with_narrative,
    integrate_with_operator_review,
    integrate_with_governance_view,
    integrate_with_proposal_realization,
)


class TestGuidanceContextModels(unittest.TestCase):
    """Test adaptive guidance data models."""

    def test_evidence_quality_creation(self):
        """Test creating an evidence quality assessment."""
        quality = EvidenceQuality(
            confidence=0.85,
            confidence_source="analysis",
            confidence_basis="Multiple data points converge on this finding",
            evidence_count=5,
            supporting_sources=["source-001", "source-002"],
            is_consistent=True,
            has_counter_evidence=False,
        )
        
        self.assertEqual(quality.confidence, 0.85)
        self.assertEqual(quality.confidence_source, "analysis")
        self.assertEqual(quality.evidence_count, 5)
        self.assertEqual(len(quality.supporting_sources), 2)

    def test_evidence_quality_get_strength(self):
        """Test getting recommendation strength from evidence quality."""
        # Low confidence (< 0.4)
        quality = EvidenceQuality(confidence=0.3)
        self.assertEqual(quality.get_strength(), RecommendationStrength.WEAK.value)
        
        # Moderate confidence (>= 0.4, < 0.7)
        quality = EvidenceQuality(confidence=0.55)
        self.assertEqual(quality.get_strength(), RecommendationStrength.MODERATE.value)
        
        # High confidence (>= 0.7, < 0.9)
        quality = EvidenceQuality(confidence=0.8)
        self.assertEqual(quality.get_strength(), RecommendationStrength.STRONG.value)
        
        # Very high confidence (>= 0.9)
        quality = EvidenceQuality(confidence=0.92)
        self.assertEqual(quality.get_strength(), RecommendationStrength.DEFAULT.value)

    def test_evidence_quality_serialization(self):
        """Test evidence quality to_dict/from_dict."""
        quality = EvidenceQuality(
            confidence=0.75,
            confidence_source="measurement",
            evidence_count=3,
        )
        
        quality_dict = quality.to_dict()
        quality2 = EvidenceQuality.from_dict(quality_dict)
        
        self.assertEqual(quality.confidence, quality2.confidence)
        self.assertEqual(quality.confidence_source, quality2.confidence_source)

    def test_user_profile_context_creation(self):
        """Test creating a user profile context."""
        profile = UserProfileContext(
            communication_style="detailed",
            domain_familiarity="advanced",
            guidance_tolerance="supportive",
            max_suggestions_per_session=10,
        )
        
        self.assertEqual(profile.communication_style, "detailed")
        self.assertEqual(profile.domain_familiarity, "advanced")
        self.assertEqual(profile.guidance_tolerance, "supportive")

    def test_user_profile_can_suggest(self):
        """Test checking if user can receive suggestions."""
        # Independent user
        profile = UserProfileContext(guidance_tolerance="independent")
        self.assertFalse(profile.can_suggest())
        
        # Guided user
        profile = UserProfileContext(guidance_tolerance="guided")
        self.assertTrue(profile.can_suggest())
        
        # Supportive user
        profile = UserProfileContext(guidance_tolerance="supportive")
        self.assertTrue(profile.can_suggest())

    def test_user_profile_get_max_suggestions(self):
        """Test getting max suggestions from user profile."""
        profile = UserProfileContext(guidance_tolerance="independent")
        self.assertEqual(profile.get_max_suggestions(), 2)
        
        profile = UserProfileContext(guidance_tolerance="guided")
        self.assertEqual(profile.get_max_suggestions(), 5)
        
        profile = UserProfileContext(guidance_tolerance="supportive")
        self.assertEqual(profile.get_max_suggestions(), 10)

    def test_user_profile_serialization(self):
        """Test user profile to_dict/from_dict."""
        profile = UserProfileContext(
            communication_style="analytical",
            domain_familiarity="expert",
        )
        
        profile_dict = profile.to_dict()
        profile2 = UserProfileContext.from_dict(profile_dict)
        
        self.assertEqual(profile.communication_style, profile2.communication_style)
        self.assertEqual(profile.domain_familiarity, profile2.domain_familiarity)

    def test_guidance_context_creation(self):
        """Test creating a guidance context."""
        profile = UserProfileContext(
            communication_style="concise",
            guidance_tolerance="guided",
        )
        quality = EvidenceQuality(
            confidence=0.8,
            confidence_source="analysis",
        )
        
        context = GuidanceContext(
            user_profile=profile,
            evidence_quality=quality,
            safety_approved=True,
        )
        
        self.assertIsNotNone(context.user_profile)
        self.assertIsNotNone(context.evidence_quality)
        self.assertTrue(context.safety_approved)

    def test_guidance_context_get_effective_strength(self):
        """Test getting effective recommendation strength."""
        profile = UserProfileContext(guidance_tolerance="guided")
        quality = EvidenceQuality(confidence=0.3)  # Weak
        
        context = GuidanceContext(
            user_profile=profile,
            evidence_quality=quality,
            hold_back_if_weak=True,
        )
        
        self.assertEqual(context.get_effective_strength(), RecommendationStrength.WEAK.value)

    def test_guidance_context_with_safety_block(self):
        """Test guidance context with safety block."""
        profile = UserProfileContext(guidance_tolerance="guided")
        quality = EvidenceQuality(confidence=0.9)  # Strong
        
        context = GuidanceContext(
            user_profile=profile,
            evidence_quality=quality,
            safety_blocked=True,
        )
        
        self.assertEqual(context.get_effective_strength(), RecommendationStrength.WEAK.value)

    def test_guidance_context_should_output(self):
        """Test if guidance context should produce output."""
        # Valid context with explanation should output
        profile = UserProfileContext(guidance_tolerance="guided")
        quality = EvidenceQuality(confidence=0.7)
        
        context = GuidanceContext(
            user_profile=profile,
            evidence_quality=quality,
            safety_approved=True,
            explanation_basis="Data analysis shows trend",
            can_silence=False,  # Don't allow silencing
        )
        
        self.assertTrue(context.should_output())

    def test_guidance_context_should_explain(self):
        """Test if guidance context should include explanation."""
        # With explanation basis and non-concise style
        profile = UserProfileContext(communication_style="detailed")
        quality = EvidenceQuality(confidence=0.7)
        
        context = GuidanceContext(
            user_profile=profile,
            evidence_quality=quality,
            explanation_basis="Trend analysis",
        )
        
        self.assertTrue(context.should_explain())

    def test_guidance_context_get_recommendation_hint(self):
        """Test getting recommendation hint."""
        quality = EvidenceQuality(confidence=0.8)  # Above 0.7, < 0.9 for STRONG
        
        context = GuidanceContext(evidence_quality=quality)
        hint = context.get_recommendation_hint()
        
        self.assertIn("recommended", hint.lower())
        
        weak_quality = EvidenceQuality(confidence=0.3)
        weak_context = GuidanceContext(evidence_quality=weak_quality)
        weak_hint = weak_context.get_recommendation_hint()
        
        self.assertIn("informational", weak_hint.lower())

    def test_guidance_context_serialization(self):
        """Test guidance context to_dict/from_dict."""
        profile = UserProfileContext(
            communication_style="analytical",
            domain_familiarity="expert",
        )
        quality = EvidenceQuality(confidence=0.8)
        
        context = GuidanceContext(
            user_profile=profile,
            evidence_quality=quality,
            safety_approved=True,
        )
        
        context_dict = context.to_dict()
        context2 = GuidanceContext.from_dict(context_dict)
        
        self.assertEqual(context.safety_approved, context2.safety_approved)
        self.assertEqual(
            context.user_profile.communication_style,
            context2.user_profile.communication_style
        )


class TestAdaptiveGuidanceEngine(unittest.TestCase):
    """Test adaptive guidance engine."""

    def test_create_context(self):
        """Test creating a guidance context via engine."""
        engine = AdaptiveGuidanceEngine()
        profile = UserProfileContext(guidance_tolerance="guided")
        
        context = engine.create_context(
            "context-001",
            user_profile=profile,
        )
        
        self.assertEqual(context.user_profile, profile)

    def test_assess_recommendation(self):
        """Test assessing a recommendation."""
        engine = AdaptiveGuidanceEngine()
        profile = UserProfileContext(guidance_tolerance="guided")
        
        engine.create_context(
            "context-001",
            user_profile=profile,
        )
        
        context = engine.assess_recommendation("context-001", evidence_confidence=0.75)
        
        self.assertEqual(context.evidence_quality.confidence, 0.75)
        self.assertIsNotNone(context.assessed_at)

    def test_get_recommendation_hint(self):
        """Test getting recommendation hint."""
        engine = AdaptiveGuidanceEngine()
        quality = EvidenceQuality(confidence=0.85)
        
        engine.create_context(
            "context-001",
            evidence_quality=quality,
        )
        
        hint = engine.get_recommendation_hint("context-001")
        self.assertIn("recommended", hint.lower())

    def test_engine_serialization(self):
        """Test engine to_dict."""
        engine = AdaptiveGuidanceEngine()
        profile = UserProfileContext(guidance_tolerance="guided")
        quality = EvidenceQuality(confidence=0.8)
        
        engine.create_context(
            "context-001",
            user_profile=profile,
            evidence_quality=quality,
        )
        
        engine_dict = engine.to_dict()
        
        self.assertEqual(engine_dict["context_count"], 1)
        self.assertIn("contexts", engine_dict)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for narrative, operator review, governance, and realization."""

    def test_integrate_with_narrative_adds_guidance_fields(self):
        """Test that integration adds guidance fields to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("guidance_hint", result)
        self.assertIn("explanation_basis", result)
        self.assertTrue(result["can_silence"])
        self.assertEqual(result["recommendation_strength"], RecommendationStrength.DEFAULT.value)

    def test_integrate_with_operator_review_adds_guidance_context(self):
        """Test that integration adds guidance context to operator review."""
        review_dict = {
            "proposal_id": "prop-001",
        }
        
        result = integrate_with_operator_review(review_dict)
        
        self.assertIn("guidance_context", result)
        self.assertIn("recommendation_hint", result)
        self.assertFalse(result["can_hold_back"])

    def test_integrate_with_governance_view_adds_guidance_context(self):
        """Test that integration adds guidance context to governance."""
        governance_dict = {
            "proposal_id": "prop-001",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("guidance_hint", result)
        self.assertIn("explanation_available", result)
        self.assertFalse(result["explanation_available"])
        self.assertEqual(result["recommendation_strength"], RecommendationStrength.DEFAULT.value)

    def test_integrate_with_proposal_realization_adds_guidance_context(self):
        """Test that integration adds guidance context to proposal realization."""
        realization_dict = {
            "plan_id": "plan-001",
        }
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertIn("guidance_hint", result)
        self.assertIn("explanation_basis", result)
        self.assertFalse(result["can_hold_back"])

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing guidance context."""
        governance_dict = {
            "proposal_id": "prop-001",
            "guidance_hint": "This is a strong recommendation",
            "explanation_available": True,
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertEqual(result["guidance_hint"], "This is a strong recommendation")
        self.assertTrue(result["explanation_available"])


if __name__ == "__main__":
    unittest.main()
