"""Tests for Compromise / Why-Not Explanation Layer (v35)

Tests compromise_explanation.py data models, generator, summarizer, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.compromise_explanation import (
    ExplanationType,
    ExplanationStatus,
    Explanation,
    ExplanationSet,
    ExplanationGenerator,
    ExplanationSummarizer,
    integrate_with_adaptive_guidance,
    integrate_with_narrative,
    integrate_with_operator_context,
    integrate_with_governance_view,
)


class TestExplanationModels(unittest.TestCase):
    """Test explanation data models."""

    def test_explanation_creation(self):
        """Test creating an explanation."""
        explanation = Explanation(
            explanation_id="exp-001",
            explanation_type=ExplanationType.COMPROMISE.value,
            recommendation_id="rec-001",
            explanation_text="Compromise explanation",
            rationale="Balancing competing priorities",
        )
        
        self.assertEqual(explanation.explanation_id, "exp-001")
        self.assertEqual(explanation.explanation_type, ExplanationType.COMPROMISE.value)
        self.assertEqual(explanation.status, ExplanationStatus.GENERATED.value)

    def test_explanation_set_status(self):
        """Test setting explanation status."""
        explanation = Explanation(
            explanation_id="exp-001",
            explanation_type=ExplanationType.COMPROMISE.value,
            recommendation_id="rec-001",
            explanation_text="Compromise explanation",
            rationale="Balancing competing priorities",
        )
        
        self.assertEqual(explanation.status, ExplanationStatus.GENERATED.value)
        
        explanation.set_status(ExplanationStatus.REVIEWED.value)
        self.assertEqual(explanation.status, ExplanationStatus.REVIEWED.value)
        self.assertIsNotNone(explanation.reviewed_at)
        
        explanation.set_status(ExplanationStatus.USED.value)
        self.assertEqual(explanation.status, ExplanationStatus.USED.value)
        self.assertIsNotNone(explanation.used_at)

    def test_explanation_serialization(self):
        """Test explanation to_dict/from_dict."""
        explanation = Explanation(
            explanation_id="exp-001",
            explanation_type=ExplanationType.COMPROMISE.value,
            recommendation_id="rec-001",
            explanation_text="Compromise explanation",
            rationale="Balancing competing priorities",
            confidence=0.8,
        )
        
        explanation_dict = explanation.to_dict()
        explanation2 = Explanation.from_dict(explanation_dict)
        
        self.assertEqual(explanation.explanation_id, explanation2.explanation_id)
        self.assertEqual(explanation.confidence, explanation2.confidence)

    def test_explanation_set_creation(self):
        """Test creating an explanation set."""
        explanation_set = ExplanationSet(
            explanation_set_id="set-001",
            recommendation_id="rec-001",
        )
        
        self.assertEqual(explanation_set.explanation_set_id, "set-001")
        self.assertEqual(explanation_set.recommendation_id, "rec-001")
        self.assertEqual(len(explanation_set.explanations), 0)

    def test_explanation_set_add_explanation(self):
        """Test adding explanation to set."""
        explanation_set = ExplanationSet(
            explanation_set_id="set-001",
            recommendation_id="rec-001",
        )
        
        explanation = Explanation(
            explanation_id="exp-001",
            explanation_type=ExplanationType.COMPROMISE.value,
            recommendation_id="rec-001",
            explanation_text="Compromise explanation",
            rationale="Balancing competing priorities",
        )
        
        explanation_set.add_explanation(explanation)
        
        self.assertEqual(len(explanation_set.explanations), 1)

    def test_explanation_set_exclude_always(self):
        """Test excluding explanations from set."""
        explanation_set = ExplanationSet(
            explanation_set_id="set-001",
            recommendation_id="rec-001",
            exclude_always=["exp-001"],
        )
        
        explanation1 = Explanation(
            explanation_id="exp-001",
            explanation_type=ExplanationType.COMPROMISE.value,
            recommendation_id="rec-001",
            explanation_text="Compromise explanation",
            rationale="Balancing competing priorities",
        )
        
        explanation2 = Explanation(
            explanation_id="exp-002",
            explanation_type=ExplanationType.WHY_NOT_STRONGER.value,
            recommendation_id="rec-001",
            explanation_text="Stronger explanation",
            rationale="Higher priority not available",
        )
        
        explanation_set.add_explanation(explanation1)
        explanation_set.add_explanation(explanation2)
        
        active = explanation_set.get_active_explanations()
        
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].explanation_id, "exp-002")

    def test_explanation_set_serialization(self):
        """Test explanation set to_dict/from_dict."""
        explanation_set = ExplanationSet(
            explanation_set_id="set-001",
            recommendation_id="rec-001",
        )
        
        explanation_set_dict = explanation_set.to_dict()
        explanation_set2 = ExplanationSet.from_dict(explanation_set_dict)
        
        self.assertEqual(explanation_set.explanation_set_id, explanation_set2.explanation_set_id)


class TestExplanationGenerator(unittest.TestCase):
    """Test explanation generator."""

    def setUp(self):
        """Set up test generator."""
        self.generator = ExplanationGenerator()

    def test_generate_compromise_explanation(self):
        """Test generating compromise explanation."""
        explanation = self.generator.generate_compromise_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Would cause safety issues",
            compromise_rationale="Balancing safety and functionality",
            confidence=0.8,
        )
        
        self.assertIsNotNone(explanation)
        self.assertEqual(explanation.explanation_type, ExplanationType.COMPROMISE.value)
        self.assertIn("compromise", explanation.explanation_text.lower())
        self.assertIn("stronger", explanation.stronger_explanation.lower())

    def test_generate_why_not_stronger_explanation(self):
        """Test generating why-not stronger explanation."""
        explanation = self.generator.generate_why_not_stronger_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Would cause safety issues",
        )
        
        self.assertIsNotNone(explanation)
        self.assertEqual(explanation.explanation_type, ExplanationType.WHY_NOT_STRONGER.value)
        self.assertIn("stronger", explanation.explanation_text.lower())

    def test_generate_hold_back_explanation(self):
        """Test generating hold-back explanation."""
        explanation = self.generator.generate_hold_back_explanation(
            recommendation_id="rec-001",
            blocked_recommendation="strong_recommendation",
            blocked_reason="Safety concerns",
            tension_id="tension-001",
        )
        
        self.assertIsNotNone(explanation)
        self.assertEqual(explanation.explanation_type, ExplanationType.HOLD_BACK.value)
        self.assertIn("held back", explanation.explanation_text.lower())
        self.assertEqual(explanation.tension_id, "tension-001")

    def test_generate_alternative_explanation(self):
        """Test generating alternative explanation."""
        explanation = self.generator.generate_alternative_explanation(
            recommendation_id="rec-001",
            chosen_alternative="moderate_recommendation",
            blocked_alternative="strong_recommendation",
            blocked_reason="Would cause safety issues",
        )
        
        self.assertIsNotNone(explanation)
        self.assertEqual(explanation.explanation_type, ExplanationType.WHY_NOT_ALTERNATIVE.value)

    def test_create_explanation_set(self):
        """Test creating explanation set."""
        explanation_set = self.generator.create_explanation_set("rec-001")
        
        self.assertIsNotNone(explanation_set)
        self.assertEqual(explanation_set.recommendation_id, "rec-001")

    def test_add_explanation_to_set(self):
        """Test adding explanation to set."""
        explanation_set = self.generator.create_explanation_set("rec-001")
        explanation = self.generator.generate_compromise_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Safety issues",
            compromise_rationale="Balancing competing priorities",
        )
        
        result = self.generator.add_explanation_to_set(explanation_set.explanation_set_id, explanation)
        self.assertTrue(result)
        
        retrieved = self.generator.get_explanation_set(explanation_set.explanation_set_id)
        self.assertEqual(len(retrieved.explanations), 1)

    def test_get_explanation(self):
        """Test getting explanation by ID."""
        explanation = self.generator.generate_compromise_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Safety issues",
            compromise_rationale="Balancing competing priorities",
        )
        
        retrieved = self.generator.get_explanation(explanation.explanation_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.explanation_id, explanation.explanation_id)

    def test_get_all_explanations_for_recommendation(self):
        """Test getting all explanations for a recommendation."""
        # Create explanation set and add explanations to it
        explanation_set = self.generator.create_explanation_set("rec-001")
        
        explanation1 = self.generator.generate_compromise_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Safety issues",
            compromise_rationale="Balancing competing priorities",
        )
        self.generator.add_explanation_to_set(explanation_set.explanation_set_id, explanation1)
        
        explanation2 = self.generator.generate_why_not_stronger_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Safety issues",
        )
        self.generator.add_explanation_to_set(explanation_set.explanation_set_id, explanation2)
        
        explanations = self.generator.get_all_explanations_for_recommendation("rec-001")
        self.assertEqual(len(explanations), 2)

    def test_generator_serialization(self):
        """Test generator to_dict."""
        self.generator.generate_compromise_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Safety issues",
            compromise_rationale="Balancing competing priorities",
        )
        
        generator_dict = self.generator.to_dict()
        
        self.assertEqual(generator_dict["explanation_count"], 1)
        self.assertEqual(generator_dict["explanation_set_count"], 0)


class TestExplanationSummarizer(unittest.TestCase):
    """Test explanation summarizer."""

    def setUp(self):
        """Set up test generator and summarizer."""
        self.generator = ExplanationGenerator()
        self.summarizer = ExplanationSummarizer()

    def test_summarize_explanation_set(self):
        """Test summarizing explanation set."""
        explanation_set = self.generator.create_explanation_set("rec-001")
        
        explanation = self.generator.generate_compromise_explanation(
            recommendation_id="rec-001",
            chosen_recommendation="moderate_recommendation",
            stronger_recommendation="strong_recommendation",
            stronger_reason="Safety issues",
            compromise_rationale="Balancing competing priorities",
        )
        self.generator.add_explanation_to_set(explanation_set.explanation_set_id, explanation)
        
        summary = self.summarizer.summarize_explanation_set(explanation_set)
        
        self.assertIn("explanation", summary["summary"].lower())
        self.assertEqual(summary["explanation_count"], 1)
        self.assertIn(ExplanationType.COMPROMISE.value, summary["explanation_types"])

    def test_summarize_empty_explanation_set(self):
        """Test summarizing empty explanation set."""
        explanation_set = self.generator.create_explanation_set("rec-001")
        
        summary = self.summarizer.summarize_explanation_set(explanation_set)
        
        self.assertIn("no explanations", summary["summary"].lower())
        self.assertEqual(summary["explanation_count"], 0)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for adaptive guidance, narrative, operator context, and governance view."""

    def test_integrate_with_adaptive_guidance_adds_explanation_context(self):
        """Test that integration adds explanation context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("explanation_available", result)
        self.assertIn("explanation_set_id", result)
        self.assertIn("compromise_explanation", result)
        self.assertIn("hold_back_explanation", result)

    def test_integrate_with_narrative_adds_explanation_context(self):
        """Test that integration adds explanation context to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("explanation_basis", result)
        self.assertIn("compromise_explanation", result)
        self.assertIn("hold_back_explanation", result)

    def test_integrate_with_operator_context_adds_explanation_context(self):
        """Test that integration adds explanation context to operator context."""
        context_dict = {
            "surface_id": "surface-001",
        }
        
        result = integrate_with_operator_context(context_dict)
        
        self.assertIn("explanation_available", result)
        self.assertIn("explanation_count", result)
        self.assertIn("explanation_types", result)

    def test_integrate_with_governance_view_adds_explanation_context(self):
        """Test that integration adds explanation context to governance view."""
        governance_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("explanation_available", result)
        self.assertIn("explanation_summary", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing explanation context."""
        guidance_dict = {
            "guidance_id": "guidance-001",
            "explanation_available": True,
            "explanation_set_id": "set-001",
            "compromise_explanation": "Balance explanation",
            "hold_back_explanation": "Safety explanation",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertTrue(result["explanation_available"])
        self.assertEqual(result["explanation_set_id"], "set-001")
        self.assertEqual(result["compromise_explanation"], "Balance explanation")
        self.assertEqual(result["hold_back_explanation"], "Safety explanation")


if __name__ == "__main__":
    unittest.main()
