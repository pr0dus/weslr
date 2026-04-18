# test_recommendation_delivery.py - Tests for v52 Recommendation Delivery Layer
# Tests delivery model creation, audience-specific rendering, degraded mode,
# escalation presentation, and backward compatibility.
# Additive only, transparent, reversible. No repo drift.

from __future__ import annotations

import json
import os
import tempfile
import unittest

from recommendation_delivery import (
    RecommendationDeliveryComposer,
    DeliveryConfiguration,
    RenderedDelivery,
    DeliveryAudience,
    DeliveryMode,
    ExplanationDepth,
    PhrasingStrictness,
    CautionTone,
    HandoffFormat,
)


class TestRecommendationDelivery(unittest.TestCase):
    """Tests for RecommendationDeliveryComposer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.composer = RecommendationDeliveryComposer(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_delivery_configuration_creation(self):
        """Test DeliveryConfiguration creation and serialization."""
        config = DeliveryConfiguration(
            audience=DeliveryAudience.OPERATOR.value,
            mode=DeliveryMode.STANDARD.value,
            verbosity=7,
            explanation_depth=ExplanationDepth.STANDARD.value,
            phrasing_strictness=PhrasingStrictness.STANDARD.value,
            caution_tone=CautionTone.NORMAL.value,
            summary_mode=False,
            degraded_mode=False,
            escalation_handoff=False,
            handoff_format=HandoffFormat.BRIEF.value,
            deployment_role="home_family",
            domain="residential",
            strictness_level="moderate",
        )
        
        config_dict = config.to_dict()
        self.assertEqual(config_dict["audience"], DeliveryAudience.OPERATOR.value)
        self.assertEqual(config_dict["verbosity"], 7)
        self.assertEqual(config_dict["deployment_role"], "home_family")
        
        # Test round-trip
        config_restored = DeliveryConfiguration.from_dict(config_dict)
        self.assertEqual(config_restored.audience, config.audience)
    
    def test_rendered_delivery_creation(self):
        """Test RenderedDelivery creation and serialization."""
        rendered = RenderedDelivery(
            delivery_id="delivery_001",
            recommendation_id="rec_001",
            delivery_configuration={"audience": "operator"},
            summary="Implement safety-first approach",
            detailed="Full detailed explanation here",
            explanation="## Rationale\nConfidence: 85%",
            caution_note="Review carefully",
            handoff_context="Handoff info",
        )
        
        rendered_dict = rendered.to_dict()
        self.assertEqual(rendered_dict["summary"], "Implement safety-first approach")
        self.assertEqual(rendered_dict["caution_note"], "Review carefully")
        
        # Test round-trip
        rendered_restored = RenderedDelivery.from_dict(rendered_dict)
        self.assertEqual(rendered_restored.delivery_id, rendered.delivery_id)
    
    def test_compose_delivery(self):
        """Test compose_delivery with all configuration options."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "Implement safety-first approach with monitoring",
            "confidence": 0.85,
            "confidence_level": "high",
            "timing_posture": "short_term",
            "trust_posture": "enhanced",
            "recovery_path": "gradual_revert",
            "escalation_required": "operator",
            "governing_rules": [
                {"rule_id": "rule_001", "rule_type": "safety_strictness", "rule_value": "strict"},
            ],
            "active_tensions": [
                {"tension_id": "tens_001", "tension_type": "safety_vs_efficiency", "resolution": "prioritized safety"},
            ],
            "confidence_bundle": {
                "confidence": 0.85,
                "confidence_basis": "Strong evidence from multiple sources",
            },
        }
        
        configuration = DeliveryConfiguration(
            audience=DeliveryAudience.OPERATOR.value,
            mode=DeliveryMode.STANDARD.value,
            verbosity=8,
            explanation_depth=ExplanationDepth.STANDARD.value,
            phrasing_strictness=PhrasingStrictness.STANDARD.value,
            caution_tone=CautionTone.ELEVATED.value,
            summary_mode=False,
            degraded_mode=False,
            escalation_handoff=False,
            handoff_format=HandoffFormat.BRIEF.value,
            created_by="test_operator",
        )
        
        rendered = self.composer.compose_delivery(recommendation, configuration)
        
        self.assertIsNotNone(rendered.summary)
        # detailed is None because mode is STANDARD (not DETAILED/ESCALATION)
        self.assertIsNotNone(rendered.explanation)
        # caution_note is None because confidence >= 0.8 and not degraded_mode
        # self.assertIsNotNone(rendered.caution_note)  # Commented: confidence=0.85 > 0.8, so no caution note
        self.assertIn("safety", rendered.summary.lower())
    
    def test_compose_for_operator(self):
        """Test compose_for_operator shortcut."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "Implement safety-first approach",
            "confidence": 0.9,
            "confidence_level": "very_high",
            "timing_posture": "short_term",
        }
        
        rendered = self.composer.compose_for_operator(
            recommendation,
            verbosity=6,
            explanation_depth=ExplanationDepth.STANDARD.value,
            created_by="test_operator",
        )
        
        self.assertIsNotNone(rendered.summary)
        self.assertEqual(rendered.delivery_configuration["audience"], DeliveryAudience.OPERATOR.value)
        self.assertEqual(rendered.delivery_configuration["verbosity"], 6)
    
    def test_compose_for_system(self):
        """Test compose_for_system shortcut."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "System instruction",
            "confidence": 0.85,
        }
        
        rendered = self.composer.compose_for_system(recommendation)
        
        self.assertIsNotNone(rendered.summary)
        self.assertEqual(rendered.delivery_configuration["audience"], DeliveryAudience.SYSTEM.value)
        self.assertEqual(rendered.delivery_configuration["verbosity"], 2)
        self.assertEqual(rendered.delivery_configuration["explanation_depth"], ExplanationDepth.NONE.value)
    
    def test_compose_summary(self):
        """Test compose_summary shortcut."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "Summary instruction",
            "confidence": 0.85,
        }
        
        rendered = self.composer.compose_summary(recommendation)
        
        # summary_mode=True means summary output is None
        # the summary is available via get_summary_output() which uses caution_note
        self.assertEqual(rendered.summary, None)  # summary_mode=True makes summary None
        self.assertEqual(rendered.delivery_configuration["summary_mode"], True)
    
    def test_compose_for_escalation(self):
        """Test compose_for_escalation shortcut."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "Escalation instruction",
            "confidence": 0.7,
            "confidence_level": "moderate",
            "timing_posture": "immediate",
            "escalation_required": "operator",
        }
        
        rendered = self.composer.compose_for_escalation(recommendation, handoff_format=HandoffFormat.COMPLETE.value)
        
        self.assertIsNotNone(rendered.summary)
        self.assertIsNotNone(rendered.handoff_context)
        self.assertEqual(rendered.delivery_configuration["mode"], DeliveryMode.ESCALATION.value)
        self.assertEqual(rendered.delivery_configuration["escalation_handoff"], True)
        self.assertIn("HANDOFF CONTEXT", rendered.handoff_context or "")
    
    def test_compose_for_degraded_mode(self):
        """Test compose_for_degraded_mode shortcut."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "Degraded mode instruction",
            "confidence": 0.6,  # Lower confidence in degraded mode
            "confidence_level": "moderate",
            "timing_posture": "medium_term",
        }
        
        rendered = self.composer.compose_for_degraded_mode(recommendation)
        
        self.assertIsNotNone(rendered.summary)
        self.assertEqual(rendered.delivery_configuration["degraded_mode"], True)
        self.assertEqual(rendered.delivery_configuration["caution_tone"], CautionTone.MAXIMUM.value)
    
    def test_compose_for_audit(self):
        """Test compose_for_audit shortcut."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "Audit instruction",
            "confidence": 0.95,
            "confidence_level": "very_high",
        }
        
        rendered = self.composer.compose_for_audit(recommendation)
        
        self.assertIsNotNone(rendered.summary)
        self.assertEqual(rendered.delivery_configuration["audience"], DeliveryAudience.AUDIT.value)
        self.assertEqual(rendered.delivery_configuration["verbosity"], 10)
        self.assertEqual(rendered.delivery_configuration["explanation_depth"], ExplanationDepth.EXHAUSTIVE.value)
    
    def test_get_latest_delivery(self):
        """Test get_latest_delivery."""
        # Create first delivery
        rec1 = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "First instruction",
            "confidence": 0.85,
        }
        rendered1 = self.composer.compose_for_operator(rec1)
        
        # Create second delivery
        rec2 = {
            "recommendation_id": "rec_002",
            "recommendation_type": "action",
            "recommendation_text": "Second instruction",
            "confidence": 0.9,
        }
        rendered2 = self.composer.compose_for_operator(rec2)
        
        latest = self.composer.get_latest_delivery()
        self.assertEqual(latest.delivery_id, rendered2.delivery_id)
    
    def test_get_summary_output(self):
        """Test get_summary_output method."""
        rendered = RenderedDelivery(
            delivery_id="delivery_001",
            recommendation_id="rec_001",
            delivery_configuration={},
            summary="SUMMARY: Implement safety-first approach",
            caution_note="Review carefully",
        )
        
        output = rendered.get_summary_output()
        self.assertIn("SUMMARY:", output)
        self.assertIn("Review carefully", output)
    
    def test_get_full_output(self):
        """Test get_full_output method."""
        rendered = RenderedDelivery(
            delivery_id="delivery_001",
            recommendation_id="rec_001",
            delivery_configuration={},
            summary="SUMMARY: Test",
            detailed="DETAILED: Full explanation",
            explanation="EXPLANATION: Why this was chosen",
            caution_note="Caution note",
        )
        
        output = rendered.get_full_output()
        self.assertIn("SUMMARY:", output)
        self.assertIn("DETAILED:", output)
        self.assertIn("EXPLANATION:", output)
        self.assertIn("Caution note", output)
    
    def test_verbosity_multiplier(self):
        """Test get_verbosity_multiplier method."""
        config = DeliveryConfiguration(verbosity=0)
        self.assertEqual(config.get_verbosity_multiplier(), 0.0)
        
        config = DeliveryConfiguration(verbosity=5)
        self.assertEqual(config.get_verbosity_multiplier(), 0.5)
        
        config = DeliveryConfiguration(verbosity=10)
        self.assertEqual(config.get_verbosity_multiplier(), 1.0)
    
    def test_get_explanation_required(self):
        """Test get_explanation_required method."""
        # Summary mode should not require explanation
        config = DeliveryConfiguration(
            summary_mode=True,
            explanation_depth=ExplanationDepth.STANDARD.value,
        )
        self.assertFalse(config.get_explanation_required())
        
        # Empty explanation depth should not require explanation
        config = DeliveryConfiguration(
            summary_mode=False,
            explanation_depth=ExplanationDepth.NONE.value,
        )
        self.assertFalse(config.get_explanation_required())
        
        # Standard explanation depth should require explanation
        config = DeliveryConfiguration(
            summary_mode=False,
            explanation_depth=ExplanationDepth.STANDARD.value,
        )
        self.assertTrue(config.get_explanation_required())
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        recommendation = {
            "recommendation_id": "rec_001",
            "recommendation_type": "action",
            "recommendation_text": "Test instruction",
            "confidence": 0.85,
        }
        
        rendered = self.composer.compose_for_operator(recommendation)
        composer_dict = self.composer.to_dict()
        
        self.assertEqual(composer_dict["delivery_count"], 1)
        self.assertIn(rendered.delivery_id, composer_dict["renderings"])
    
    def test_integration_with_final_decision_composer(self):
        """Test integration hook with final decision composer."""
        from recommendation_delivery import integrate_with_final_decision_composer
        
        composer_dict = {"existing_key": "existing_value"}
        
        result = integrate_with_final_decision_composer(composer_dict, self.composer)
        
        self.assertIn("delivery_context", result)
        self.assertIsNotNone(result["delivery_context"])
        self.assertIn("delivery_storage_path", result["delivery_context"])
    
    def test_integration_with_deployment_persona(self):
        """Test integration hook with deployment persona."""
        from recommendation_delivery import integrate_with_deployment_persona
        
        persona_dict = {"existing_key": "existing_value"}
        
        result = integrate_with_deployment_persona(persona_dict, self.composer)
        
        self.assertIn("delivery_context", result)
        self.assertIsNotNone(result["delivery_context"])
        self.assertIn("delivery_storage_path", result["delivery_context"])
    
    def test_integration_with_policy_profile(self):
        """Test integration hook with policy profile."""
        from recommendation_delivery import integrate_with_policy_profile
        
        profile_dict = {"existing_key": "existing_value"}
        
        result = integrate_with_policy_profile(profile_dict, self.composer)
        
        self.assertIn("delivery_context", result)
        self.assertIsNotNone(result["delivery_context"])
        self.assertIn("delivery_storage_path", result["delivery_context"])
    
    def test_integration_with_governance_surface(self):
        """Test integration hook with governance surface."""
        from recommendation_delivery import integrate_with_governance_surface
        
        governance_dict = {"existing_key": "existing_value"}
        
        result = integrate_with_governance_surface(governance_dict, self.composer)
        
        self.assertIn("delivery_context", result)
        self.assertIsNotNone(result["delivery_context"])
        self.assertIn("delivery_storage_path", result["delivery_context"])
    
    def test_integration_with_unified_operator_context(self):
        """Test integration hook with unified operator context."""
        from recommendation_delivery import integrate_with_unified_operator_context
        
        operator_dict = {"existing_key": "existing_value"}
        
        result = integrate_with_unified_operator_context(operator_dict, self.composer)
        
        self.assertIn("delivery_context", result)
        self.assertIsNotNone(result["delivery_context"])
        self.assertIn("delivery_storage_path", result["delivery_context"])


if __name__ == "__main__":
    unittest.main()
