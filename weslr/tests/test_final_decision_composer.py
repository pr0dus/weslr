# test_final_decision_composer.py - Tests for v51 Final Decision Composer
# Tests recommendation assembly, coherence, blocking, and backward compatibility.
# Additive only, transparent, reversible. No repo drift.

from __future__ import annotations

import json
import os
import tempfile
import unittest

from final_decision_composer import (
    FinalDecisionComposer,
    FinalRecommendation,
    RecommendationBundle,
    ActiveTension,
    GoverningRule,
    BlockedAlternativeEntry,
    ConfidenceLevel,
    TimingPosture,
    TrustPosture,
    EscalationRequirement,
    RecoveryPath,
)


class TestFinalDecisionComposer(unittest.TestCase):
    """Tests for FinalDecisionComposer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.composer = FinalDecisionComposer(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_recommendation_bundle_creation(self):
        """Test RecommendationBundle creation and serialization."""
        bundle = RecommendationBundle(
            evidence_ids=["ev1", "ev2"],
            evidence_sources=["source_a", "source_b"],
            confidence=0.8,
            confidence_basis="Multiple consistent sources",
            supporting_factors=["consistent evidence", "high reliability"],
            opposing_factors=["minor contradiction"],
        )
        
        bundle_dict = bundle.to_dict()
        self.assertEqual(bundle_dict["confidence"], 0.8)
        self.assertEqual(len(bundle_dict["evidence_ids"]), 2)
        
        # Test round-trip
        bundle_restored = RecommendationBundle.from_dict(bundle_dict)
        self.assertEqual(bundle_restored.confidence, bundle.confidence)
    
    def test_active_tension_creation(self):
        """Test ActiveTension creation and serialization."""
        tension = ActiveTension(
            tension_id="tens_001",
            tension_type="safety_vs_efficiency",
            resolution="prioritized safety with monitoring",
            affected_rules=["rule_001", "rule_002"],
        )
        
        tension_dict = tension.to_dict()
        self.assertEqual(tension_dict["tension_type"], "safety_vs_efficiency")
        
        # Test round-trip
        tension_restored = ActiveTension.from_dict(tension_dict)
        self.assertEqual(tension_restored.tension_id, tension.tension_id)
    
    def test_governing_rule_creation(self):
        """Test GoverningRule creation and serialization."""
        rule = GoverningRule(
            rule_id="rule_001",
            rule_type="safety_strictness",
            rule_value="strict",
            precedence_level="high",
            override_type="blocking",
        )
        
        rule_dict = rule.to_dict()
        self.assertEqual(rule_dict["rule_type"], "safety_strictness")
        self.assertEqual(rule_dict["precedence_level"], "high")
        
        # Test round-trip
        rule_restored = GoverningRule.from_dict(rule_dict)
        self.assertEqual(rule_restored.rule_id, rule.rule_id)
    
    def test_blocked_alternative_entry_creation(self):
        """Test BlockedAlternativeEntry creation and serialization."""
        blocked = BlockedAlternativeEntry(
            alternative_id="alt_001",
            alternative_type="alternative_path",
            blocked_reason="conflicts with safety invariant",
            softened_by="modified_path_v2",
            reevaluation_trigger="after_safety_review",
        )
        
        blocked_dict = blocked.to_dict()
        self.assertEqual(blocked_dict["blocked_reason"], "conflicts with safety invariant")
        
        # Test round-trip
        blocked_restored = BlockedAlternativeEntry.from_dict(blocked_dict)
        self.assertEqual(blocked_restored.alternative_id, blocked.alternative_id)
    
    def test_final_recommendation_creation(self):
        """Test FinalRecommendation creation and serialization."""
        bundle = RecommendationBundle(
            evidence_ids=["ev1"],
            evidence_sources=["source_a"],
            confidence=0.85,
            confidence_basis="Strong evidence",
        )
        
        tension = ActiveTension(
            tension_id="tens_001",
            tension_type="safety_vs_efficiency",
            resolution="prioritized safety",
        )
        
        rule = GoverningRule(
            rule_id="rule_001",
            rule_type="safety_strictness",
            rule_value="strict",
        )
        
        blocked = BlockedAlternativeEntry(
            alternative_id="alt_001",
            alternative_type="alternative_path",
            blocked_reason="conflicts with invariant",
        )
        
        # When creating FinalRecommendation directly, confidence_level is not auto-computed
        # It's computed in assemble_recommendation method when guidance context is provided
        recommendation = FinalRecommendation(
            recommendation_id="rec_001",
            recommendation_type="action",
            recommendation_text="Implement safety-first approach",
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH.value,  # Set explicitly since no guidance context
            confidence_bundle=bundle,
            timing_posture=TimingPosture.SHORT_TERM.value,
            trust_posture=TrustPosture.ENHANCED.value,
            active_tensions=[tension.to_dict()],
            governing_rules=[rule.to_dict()],
            blocked_alternatives=[blocked.to_dict()],
            recovery_path=RecoveryPath.GRADUAL_REVERT.value,
            recovery_description="Gradual rollback with monitoring",
            recovery_triggers=["error_rate > 5%", "latency > 100ms"],
            escalation_required=EscalationRequirement.OPERATOR.value,
            escalation_reason="Requires operator review for safety changes",
            escalation_path="operator_review_queue",
            explanation_bundle={"reason": "safety_first"},
        )
        
        rec_dict = recommendation.to_dict()
        self.assertEqual(rec_dict["recommendation_type"], "action")
        self.assertEqual(rec_dict["confidence_level"], ConfidenceLevel.HIGH.value)
        self.assertEqual(rec_dict["timing_posture"], TimingPosture.SHORT_TERM.value)
        
        # Test round-trip
        rec_restored = FinalRecommendation.from_dict(rec_dict)
        self.assertEqual(rec_restored.recommendation_id, recommendation.recommendation_id)
    
    def test_assemble_recommendation(self):
        """Test assemble_recommendation with all context layers."""
        guidance_context = {
            "evidence_quality": {
                "confidence": 0.9,
                "confidence_basis": "High confidence from multiple sources",
                "supporting_sources": ["source_a", "source_b"],
                "supporting_factors": ["consistent evidence", "high reliability"],
            },
            "timing_posture": "short_term",
            "due_by": "2026-04-07T12:00:00Z",
        }
        
        policy_context = {
            "active_tensions": [
                {
                    "tension_id": "tens_001",
                    "tension_type": "safety_vs_efficiency",
                    "resolution": "prioritized safety with monitoring",
                    "affected_rules": ["rule_001"],
                }
            ],
            "governing_rules": [
                {
                    "rule_id": "rule_001",
                    "rule_type": "safety_strictness",
                    "rule_value": "strict",
                    "precedence_level": "high",
                }
            ],
            "blocked_alternatives": [
                {
                    "alternative_id": "alt_001",
                    "alternative_type": "alternative_path",
                    "blocked_reason": "conflicts with safety invariant",
                }
            ],
        }
        
        governance_context = {
            "recovery_path": "gradual_revert",
            "recovery_description": "Gradual rollback with monitoring",
            "recovery_triggers": ["error_rate > 5%", "latency > 100ms"],
            "escalation_required": "operator",
            "escalation_reason": "Safety-critical change",
            "escalation_path": "operator_review_queue",
        }
        
        operator_context = {
            "trust_posture": "enhanced",
            "trust_basis": "High confidence and consistent history",
            "reliability_mode": "normal",
        }
        
        recommendation = self.composer.assemble_recommendation(
            recommendation_type="action",
            recommendation_text="Implement safety-first approach with monitoring",
            guidance_context=guidance_context,
            policy_context=policy_context,
            governance_context=governance_context,
            operator_context=operator_context,
            created_by="test_operator",
        )
        
        self.assertEqual(recommendation.confidence, 0.9)
        self.assertEqual(recommendation.confidence_level, ConfidenceLevel.VERY_HIGH.value)
        self.assertEqual(recommendation.timing_posture, TimingPosture.SHORT_TERM.value)
        self.assertEqual(recommendation.trust_posture, TrustPosture.ENHANCED.value)
        self.assertEqual(recommendation.recovery_path, RecoveryPath.GRADUAL_REVERT.value)
        self.assertEqual(recommendation.escalation_required, EscalationRequirement.OPERATOR.value)
        self.assertEqual(len(recommendation.active_tensions), 1)
        self.assertEqual(len(recommendation.governing_rules), 1)
        self.assertEqual(len(recommendation.blocked_alternatives), 1)
        self.assertIn("final_decision_composer_v51", recommendation.explanation_bundle.get("source", ""))
    
    def test_compose_from_adaptive_guidance(self):
        """Test compose_from_adaptive_guidance shortcut."""
        guidance_context = {
            "evidence_quality": {
                "confidence": 0.75,
                "confidence_basis": "Moderate confidence",
            },
            "timing_posture": "medium_term",
        }
        
        recommendation = self.composer.compose_from_adaptive_guidance(
            guidance_context=guidance_context,
            recommendation_text="Consider medium-term approach",
        )
        
        self.assertEqual(recommendation.confidence, 0.75)
        self.assertEqual(recommendation.confidence_level, ConfidenceLevel.HIGH.value)
        self.assertEqual(recommendation.timing_posture, TimingPosture.MEDIUM_TERM.value)
    
    def test_compose_from_policy_conflict(self):
        """Test compose_from_policy_conflict shortcut."""
        policy_context = {
            "active_tensions": [
                {
                    "tension_id": "tens_001",
                    "tension_type": "speed_vs_quality",
                    "resolution": "prioritized quality",
                }
            ],
            "governing_rules": [
                {
                    "rule_id": "rule_001",
                    "rule_type": "quality_strictness",
                    "rule_value": "high",
                }
            ],
        }
        
        recommendation = self.composer.compose_from_policy_conflict(
            policy_context=policy_context,
            recommendation_text="Prioritize quality over speed",
        )
        
        self.assertEqual(len(recommendation.active_tensions), 1)
        self.assertEqual(len(recommendation.governing_rules), 1)
        self.assertEqual(recommendation.explanation_bundle.get("policy", {}).get("governing_rules_count"), 1)
    
    def test_compose_from_governance(self):
        """Test compose_from_governance shortcut."""
        governance_context = {
            "recovery_path": "auto_revert",
            "escalation_required": "senior",
        }
        
        recommendation = self.composer.compose_from_governance(
            governance_context=governance_context,
            recommendation_text="Escalate to senior operator",
        )
        
        self.assertEqual(recommendation.recovery_path, RecoveryPath.AUTO_REVERT.value)
        self.assertEqual(recommendation.escalation_required, EscalationRequirement.SENIOR.value)
    
    def test_compose_from_operator_context(self):
        """Test compose_from_operator_context shortcut."""
        operator_context = {
            "trust_posture": "cautious",
            "reliability_mode": "strict",
        }
        
        recommendation = self.composer.compose_from_operator_context(
            operator_context=operator_context,
            recommendation_text="Proceed with caution",
        )
        
        self.assertEqual(recommendation.trust_posture, TrustPosture.CAUTIOUS.value)
        self.assertEqual(recommendation.explanation_bundle.get("operator", {}).get("reliability_mode"), "strict")
    
    def test_get_latest_recommendation(self):
        """Test get_latest_recommendation."""
        # Create first recommendation
        rec1 = self.composer.assemble_recommendation(
            recommendation_type="action",
            recommendation_text="First recommendation",
        )
        
        # Create second recommendation
        rec2 = self.composer.assemble_recommendation(
            recommendation_type="action",
            recommendation_text="Second recommendation",
        )
        
        latest = self.composer.get_latest_recommendation()
        self.assertEqual(latest.recommendation_id, rec2.recommendation_id)
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        rec = self.composer.assemble_recommendation(
            recommendation_type="action",
            recommendation_text="Test recommendation",
        )
        
        composer_dict = self.composer.to_dict()
        self.assertEqual(composer_dict["recommendation_count"], 1)
        self.assertIn(rec.recommendation_id, composer_dict["recommendations"])
    
    def test_integration_with_adaptive_guidance(self):
        """Test integration hook with adaptive guidance."""
        guidance_dict = {"existing_key": "existing_value"}
        
        from final_decision_composer import integrate_with_adaptive_guidance
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("final_decision_context", result)
        self.assertIsNone(result["final_decision_context"])
    
    def test_integration_with_policy_conflict_resolution(self):
        """Test integration hook with policy conflict resolution."""
        policy_dict = {"existing_key": "existing_value"}
        
        from final_decision_composer import integrate_with_policy_conflict_resolution
        result = integrate_with_policy_conflict_resolution(
            policy_dict,
            composer=self.composer,
        )
        
        self.assertIn("final_decision_context", result)
        self.assertIsNotNone(result["final_decision_context"])
        self.assertIn("composer_storage_path", result["final_decision_context"])
    
    def test_integration_with_governance_surface(self):
        """Test integration hook with governance surface."""
        governance_dict = {"existing_key": "existing_value"}
        
        from final_decision_composer import integrate_with_governance_surface
        result = integrate_with_governance_surface(
            governance_dict,
            composer=self.composer,
        )
        
        self.assertIn("final_decision_context", result)
        self.assertIsNotNone(result["final_decision_context"])
        self.assertIn("composer_storage_path", result["final_decision_context"])
    
    def test_integration_with_unified_operator_context(self):
        """Test integration hook with unified operator context."""
        operator_dict = {"existing_key": "existing_value"}
        
        from final_decision_composer import integrate_with_unified_operator_context
        result = integrate_with_unified_operator_context(
            operator_dict,
            composer=self.composer,
        )
        
        self.assertIn("final_decision_context", result)
        self.assertIsNotNone(result["final_decision_context"])
        self.assertIn("composer_storage_path", result["final_decision_context"])


if __name__ == "__main__":
    unittest.main()
