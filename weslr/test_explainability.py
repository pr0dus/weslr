# test_explainability.py - Behavioral tests for final_decision_explainability layer
# Additive only, operator-first, reversible, governed.

from __future__ import annotations

import json
import unittest
from dataclasses import asdict

from weslr import final_decision_explainability
from weslr import final_decision_composer
from weslr import recommendation_delivery
from weslr import recommendation_presentation_mode


class TestExplanationSection(unittest.TestCase):
    """Tests for ExplanationSection data model."""

    def test_creation(self):
        section = final_decision_explainability.ExplanationSection(
            section_id="test",
            section_title="Test Section",
            section_content="Test content",
            section_order=1
        )
        self.assertEqual(section.section_id, "test")
        self.assertEqual(section.section_title, "Test Section")
        self.assertEqual(section.section_content, "Test content")
        self.assertEqual(section.section_order, 1)

    def test_to_dict(self):
        section = final_decision_explainability.ExplanationSection(
            section_id="test",
            section_title="Test Section",
            section_content="Test content",
            section_order=1
        )
        result = section.to_dict()
        self.assertEqual(result["section_id"], "test")
        self.assertEqual(result["section_title"], "Test Section")
        self.assertEqual(result["section_content"], "Test content")
        self.assertEqual(result["section_order"], 1)
        self.assertFalse(result["is_optional"])


class TestExplanationBundle(unittest.TestCase):
    """Tests for ExplanationBundle data model."""

    def setUp(self):
        self.decision_summary = final_decision_explainability.ExplanationSection(
            section_id="summary", section_title="Decision Summary", section_content="Summary", section_order=1
        )
        self.primary_rationale = final_decision_explainability.ExplanationSection(
            section_id="rationale", section_title="Primary Rationale", section_content="Rationale", section_order=2
        )
        self.evidence_summary = final_decision_explainability.ExplanationSection(
            section_id="evidence", section_title="Evidence Summary", section_content="Evidence", section_order=3
        )
        self.blocked_alternatives = final_decision_explainability.ExplanationSection(
            section_id="alternatives", section_title="Blocked Alternatives", section_content="Alternatives", section_order=4
        )
        self.governing_rules = final_decision_explainability.ExplanationSection(
            section_id="rules", section_title="Governing Rules", section_content="Rules", section_order=5
        )

    def test_creation(self):
        bundle = final_decision_explainability.ExplanationBundle(
            bundle_id="exp-test",
            recommendation_id="rec-1",
            recommendation_type="action",
            decision_summary=self.decision_summary,
            primary_rationale=self.primary_rationale,
            evidence_summary=self.evidence_summary,
            blocked_alternatives=self.blocked_alternatives,
            governing_rules=self.governing_rules
        )
        self.assertEqual(bundle.bundle_id, "exp-test")
        self.assertEqual(bundle.recommendation_id, "rec-1")
        self.assertEqual(bundle.recommendation_type, "action")
        self.assertEqual(len(bundle.to_dict()), 12)  # All required fields + metadata + optional

    def test_to_json(self):
        bundle = final_decision_explainability.ExplanationBundle(
            bundle_id="exp-test",
            recommendation_id="rec-1",
            recommendation_type="action",
            decision_summary=self.decision_summary,
            primary_rationale=self.primary_rationale,
            evidence_summary=self.evidence_summary,
            blocked_alternatives=self.blocked_alternatives,
            governing_rules=self.governing_rules
        )
        json_str = bundle.to_json()
        self.assertIn("exp-test", json_str)
        self.assertIn("rec-1", json_str)
        data = json.loads(json_str)
        self.assertEqual(data["bundle_id"], "exp-test")

    def test_to_markdown(self):
        bundle = final_decision_explainability.ExplanationBundle(
            bundle_id="exp-test",
            recommendation_id="rec-1",
            recommendation_type="action",
            decision_summary=self.decision_summary,
            primary_rationale=self.primary_rationale,
            evidence_summary=self.evidence_summary,
            blocked_alternatives=self.blocked_alternatives,
            governing_rules=self.governing_rules
        )
        md = bundle.to_markdown()
        self.assertIn("# Recommendation: rec-1", md)
        self.assertIn("## Decision Summary", md)
        self.assertIn("## Primary Rationale", md)

    def test_to_text(self):
        bundle = final_decision_explainability.ExplanationBundle(
            bundle_id="exp-test",
            recommendation_id="rec-1",
            recommendation_type="action",
            decision_summary=self.decision_summary,
            primary_rationale=self.primary_rationale,
            evidence_summary=self.evidence_summary,
            blocked_alternatives=self.blocked_alternatives,
            governing_rules=self.governing_rules
        )
        text = bundle.to_text()
        self.assertIn("Recommendation: rec-1", text)
        self.assertIn("--- Decision Summary ---", text)


class TestFinalDecisionExplainabilityEngine(unittest.TestCase):
    """Tests for FinalDecisionExplainabilityEngine."""

    def setUp(self):
        self.engine = final_decision_explainability.FinalDecisionExplainabilityEngine()

    def _create_test_recommendation(self) -> final_decision_composer.FinalRecommendation:
        """Create a test recommendation with all optional fields."""
        return final_decision_composer.FinalRecommendation(
            recommendation_id="rec-001",
            recommendation_type="action",
            recommendation_text="Take action A",
            confidence=0.85,
            confidence_level="high",
            confidence_bundle=final_decision_composer.RecommendationBundle(
                confidence=0.85,
                confidence_basis="Strong evidence from multiple sources",
                supporting_factors=["Evidence 1", "Evidence 2"],
                opposing_factors=["Weak signal 1"]
            ),
            timing_posture="short_term",
            due_by="2026-04-10T09:00:00Z",
            trust_posture="enhanced",
            trust_basis="Consistent historical pattern",
            active_tensions=[{
                "tension_id": "tension-1",
                "tension_type": "speed_vs_quality",
                "resolution": "Prioritized quality with acceptable speed",
                "affected_rules": ["quality_gate", "speed_minimum"],
                "outcome": "resolved"
            }],
            governing_rules=[{
                "rule_id": "rule-1",
                "rule_type": "safety_strictness",
                "rule_value": "high",
                "precedence_level": "high",
                "override_type": "none"
            }],
            blocked_alternatives=[{
                "alternative_id": "alt-1",
                "alternative_type": "alternative_path",
                "blocked_reason": "Violates safety constraint",
                "softened_by": "mitigated_risk",
                "reevaluation_trigger": "q3_2026_review"
            }],
            recovery_path="auto_revert",
            recovery_description="Automatic revert if anomalies detected",
            recovery_triggers=["anomaly_detected", "threshold_exceeded"],
            escalation_required="operator"
        )

    def test_generate_explanation_standard(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation, depth="standard", format_="text")

        self.assertEqual(bundle.recommendation_id, "rec-001")
        self.assertEqual(bundle.explanation_depth, "standard")
        self.assertEqual(bundle.explanation_format, "text")

        # Check required sections exist
        self.assertIsNotNone(bundle.decision_summary)
        self.assertIsNotNone(bundle.primary_rationale)
        self.assertIsNotNone(bundle.evidence_summary)
        self.assertIsNotNone(bundle.blocked_alternatives)
        self.assertIsNotNone(bundle.governing_rules)

    def test_generate_explanation_with_optional_sections(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation, depth="enhanced")

        # Check optional sections are included
        self.assertIsNotNone(bundle.trust_timing_influence)
        self.assertIsNotNone(bundle.recovery_path)
        self.assertIsNotNone(bundle.escalation_handoff)
        self.assertIsNotNone(bundle.concise_why_summary)

    def test_to_markdown_format(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        md = bundle.to_markdown()

        self.assertIn("# Recommendation: rec-001", md)
        self.assertIn("## Decision Summary", md)
        self.assertIn("## Primary Rationale", md)
        self.assertIn("## Evidence Summary", md)
        self.assertIn("## Blocked / Softened Alternatives", md)
        self.assertIn("## Governing Rules", md)

    def test_to_text_format(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        text = bundle.to_text()

        self.assertIn("Recommendation: rec-001", text)
        self.assertIn("--- Decision Summary ---", text)

    def test_concise_why_summary(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation, depth="enhanced")
        why_summary = bundle.concise_why_summary

        self.assertIsNotNone(why_summary)
        self.assertIn("**Decision**: Take action A", why_summary.section_content)
        self.assertIn("85%", why_summary.section_content)

    def test_generate_explanation_minimal_depth(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation, depth="minimal")

        # Minimal depth should omit concise_why_summary
        self.assertIsNone(bundle.concise_why_summary)

    def test_engine_reuse(self):
        recommendation = self._create_test_recommendation()
        bundle1 = self.engine.generate_explanation(recommendation)
        bundle2 = self.engine.generate_explanation(recommendation)

        self.assertEqual(bundle1.recommendation_id, bundle2.recommendation_id)
        self.assertEqual(bundle1.bundle_id, bundle2.bundle_id)
        self.assertEqual(bundle1.decision_summary.section_content, bundle2.decision_summary.section_content)


class TestExplanationDeliveryApplier(unittest.TestCase):
    """Tests for ExplanationDeliveryApplier."""

    def setUp(self):
        self.engine = final_decision_explainability.FinalDecisionExplainabilityEngine()
        self.applier = final_decision_explainability.ExplanationDeliveryApplier(self.engine)

    def _create_test_recommendation(self) -> final_decision_composer.FinalRecommendation:
        return final_decision_composer.FinalRecommendation(
            recommendation_id="rec-001",
            recommendation_type="action",
            recommendation_text="Take action A",
            confidence=0.85,
            confidence_level="high",
            confidence_bundle=final_decision_composer.RecommendationBundle(
                confidence=0.85,
                confidence_basis="Strong evidence"
            ),
            timing_posture="short_term",
            trust_posture="enhanced",
            trust_basis="Consistent pattern",
            governing_rules=[{
                "rule_id": "rule-1",
                "rule_type": "safety_strictness",
                "rule_value": "high"
            }],
            blocked_alternatives=[{
                "alternative_id": "alt-1",
                "alternative_type": "alternative_path",
                "blocked_reason": "Violates safety constraint"
            }],
            recovery_path="none"
        )

    def test_apply_delivery_mode_summary(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        delivery_config = recommendation_delivery.DeliveryConfiguration(
            audience="operator",
            mode="summary"
        )

        output = self.applier.apply_delivery_mode(bundle, delivery_config)
        # Summary mode should return only decision summary content
        self.assertIn("**Recommendation**: Take action A", output)
        self.assertNotIn("## Primary Rationale", output)

    def test_apply_delivery_mode_detailed(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        delivery_config = recommendation_delivery.DeliveryConfiguration(
            audience="operator",
            mode="detailed"
        )

        output = self.applier.apply_delivery_mode(bundle, delivery_config)
        # Detailed mode should return markdown
        self.assertIn("# Recommendation: rec-001", output)
        self.assertIn("## Primary Rationale", output)

    def test_apply_delivery_mode_standard(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        delivery_config = recommendation_delivery.DeliveryConfiguration(
            audience="operator",
            mode="standard"
        )

        output = self.applier.apply_delivery_mode(bundle, delivery_config)
        # Standard mode should return text format
        self.assertIn("Recommendation: rec-001", output)
        self.assertIn("--- Decision Summary ---", output)

    def test_apply_presentation_mode_summary(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        presentation_config = recommendation_presentation_mode.PresentationConfiguration(
            context="operator_direct",
            mode="summary"
        )

        output = self.applier.apply_presentation_mode(bundle, presentation_config)
        self.assertIn("**Recommendation**: Take action A", output)

    def test_apply_presentation_mode_structured(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        presentation_config = recommendation_presentation_mode.PresentationConfiguration(
            context="system_integration",
            mode="structured"
        )

        output = self.applier.apply_presentation_mode(bundle, presentation_config)
        data = json.loads(output)
        self.assertEqual(data["bundle_id"], bundle.bundle_id)
        self.assertEqual(data["recommendation_id"], "rec-001")

    def test_apply_presentation_mode_narrative(self):
        recommendation = self._create_test_recommendation()
        bundle = self.engine.generate_explanation(recommendation)
        presentation_config = recommendation_presentation_mode.PresentationConfiguration(
            context="operator_report",
            mode="narrative"
        )

        output = self.applier.apply_presentation_mode(bundle, presentation_config)
        self.assertIn("## Recommendation: rec-001", output)
        self.assertIn("**Why this decision?**", output)
        self.assertIn("**What does this mean?**", output)


class TestEndToEndFlow(unittest.TestCase):
    """End-to-end flow tests for explainability layer."""

    def test_full_recommendation_to_explanation(self):
        """Test complete flow from recommendation to explanation bundle."""
        # Create a recommendation with full data
        recommendation = final_decision_composer.FinalRecommendation(
            recommendation_id="rec-001",
            recommendation_type="action",
            recommendation_text="Deploy hotfix to production",
            confidence=0.92,
            confidence_level="very_high",
            timing_posture="immediate",
            trust_posture="full",
            trust_basis="Multiple independent verifications",
            governing_rules=[{
                "rule_id": "hotfix-policy",
                "rule_type": "deployment_strictness",
                "rule_value": "hotfix_expedited"
            }],
            blocked_alternatives=[{
                "alternative_id": "alt-full-test",
                "alternative_type": "full_test_cycle",
                "blocked_reason": "Time constraints; hotfix path approved"
            }],
            recovery_path="auto_revert",
            recovery_description="Auto-revert if error rate exceeds 1%",
            recovery_triggers=["error_rate_1pct", "latency_200ms"],
            escalation_required="operator"
        )

        engine = final_decision_explainability.FinalDecisionExplainabilityEngine()
        bundle = engine.generate_explanation(recommendation, depth="enhanced", format_="markdown")

        # Verify all required sections
        self.assertEqual(bundle.recommendation_id, "rec-001")
        self.assertIsNotNone(bundle.decision_summary)
        self.assertIsNotNone(bundle.primary_rationale)
        self.assertIsNotNone(bundle.evidence_summary)
        self.assertIsNotNone(bundle.blocked_alternatives)
        self.assertIsNotNone(bundle.governing_rules)

        # Verify optional sections for enhanced depth
        self.assertIsNotNone(bundle.trust_timing_influence)
        self.assertIsNotNone(bundle.recovery_path)
        self.assertIsNotNone(bundle.escalation_handoff)
        self.assertIsNotNone(bundle.concise_why_summary)

        # Verify markdown output
        md = bundle.to_markdown()
        self.assertIn("# Recommendation: rec-001", md)
        self.assertIn("## Decision Summary", md)
        self.assertIn("## Primary Rationale", md)
        self.assertIn("## Evidence Summary", md)
        self.assertIn("## Blocked / Softened Alternatives", md)
        self.assertIn("## Governing Rules", md)
        self.assertIn("## Trust / Timing Influence", md)
        self.assertIn("## Recovery Path", md)
        self.assertIn("## Escalation / Handoff", md)
        self.assertIn("## Concise Operator-Readable", md)


if __name__ == "__main__":
    unittest.main()
