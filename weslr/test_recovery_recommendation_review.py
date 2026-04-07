"""Test suite for v77 Recovery Recommendation Review Surface.

Tests:
  - RecoveryRecommendationReviewSurface basic behavior
  - Correlation filtering by flow/request/handshake/deadline IDs
  - Confidence presentation as guidance (not certainty)
  - Alternative recommendation visibility
  - Safe-next-action summary
  - Integration with v75 service
  - Backward compatibility with v72-v76 exports
"""

from __future__ import annotations

import json
import unittest

from weslr.recovery_recommendation_review import (
    RecoveryRecommendationReviewSurface,
    integrate_with_v75_service,
)


class MockRecoveryRecommendationService:
    """Mock v75 service for integration testing."""
    
    def __init__(self):
        self._recommendations: dict = {}
    
    def add_recommendation(self, rec: dict):
        rec_id = rec.get("recommendation_id", "")
        if rec_id:
            self._recommendations[rec_id] = rec
    
    def get_all_recommendations(self):
        return list(self._recommendations.values())


# ============================================================================
# TEST RECOVERY RECOMMENDATION REVIEW SURFACE
# ============================================================================


class TestRecoveryRecommendationReviewSurface(unittest.TestCase):
    """Test RecoveryRecommendationReviewSurface basic behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.surface = RecoveryRecommendationReviewSurface()
        self.recommendations = [
            {
                "recommendation_id": "recovery_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Proposal was rejected by validation gates",
                "contributing_factors": ["Trust threshold not met", "Health check failed"],
                "recovery_hint": "Review rejection reason and address blocking criteria",
                "confidence": "medium",
                "hint_certainty": "suggestion",
                "correlation_ids": {
                    "flow_id": "flow_abc123",
                    "request_id": "req_xyz789",
                },
                "generated_at": "2026-04-07T10:00:00Z",
            },
            {
                "recommendation_id": "recovery_2",
                "stage": "handshake",
                "failure_type": "handshake_failed",
                "likely_cause": "Handshake failed during protocol exchange",
                "contributing_factors": ["Protocol version mismatch", "Capability negotiation failed"],
                "recovery_hint": "Verify node protocol compatibility and capability registration",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {
                    "handshake_id": "hs_def456",
                    "flow_id": "flow_abc123",
                },
                "generated_at": "2026-04-07T10:01:00Z",
            },
            {
                "recommendation_id": "recovery_3",
                "stage": "envelope",
                "failure_type": "envelope_gate_failed",
                "likely_cause": "Execution envelope failed gate validation",
                "contributing_factors": ["Trust gate failed", "Health gate failed"],
                "recovery_hint": "Review gate failure logs and address blocking criteria",
                "confidence": "low",
                "hint_certainty": "suggestion",
                "correlation_ids": {
                    "deadline_id": "dl_ghi789",
                },
                "generated_at": "2026-04-07T10:02:00Z",
            },
        ]
    
    def test_creation_and_empty_state(self):
        """Test surface creation with no recommendations."""
        summary = self.surface.get_recommendation_summary()
        
        self.assertEqual(summary["total_recommendations"], 0)
        self.assertEqual(summary["confidence_distribution"], {})
        self.assertIsNone(summary["most_common_cause"])
        self.assertEqual(summary["recommended_actions"], [])
        self.assertFalse(summary["correlation_ids_present"])
    
    def test_load_recommendations(self):
        """Test loading recommendations into review surface."""
        self.surface.load_recommendations(self.recommendations)
        
        summary = self.surface.get_recommendation_summary()
        
        self.assertEqual(summary["total_recommendations"], 3)
        self.assertIn("flow_id", summary["correlation_summary"])
        self.assertEqual(summary["correlation_summary"]["flow_id"], 2)
    
    def test_get_recommendation_summary(self):
        """Test summary generation with multiple recommendations."""
        self.surface.load_recommendations(self.recommendations)
        
        summary = self.surface.get_recommendation_summary()
        
        self.assertEqual(summary["total_recommendations"], 3)
        self.assertIn("medium", summary["confidence_distribution"])
        self.assertIn("high", summary["confidence_distribution"])
        self.assertIn("low", summary["confidence_distribution"])
        self.assertTrue(summary["correlation_ids_present"])
        self.assertEqual(summary["correlation_summary"]["flow_id"], 2)
    
    def test_get_alternative_recommendations(self):
        """Test alternative recommendation view."""
        self.surface.load_recommendations(self.recommendations)
        
        alternatives = self.surface.get_alternative_recommendations()
        
        self.assertEqual(len(alternatives), 3)
        self.assertEqual(alternatives[0]["recommendation_id"], "recovery_1")
        self.assertEqual(alternatives[1]["recommendation_id"], "recovery_2")
        self.assertEqual(alternatives[2]["recommendation_id"], "recovery_3")
    
    def test_get_safe_next_action_no_recommendations(self):
        """Test safe next action with no recommendations."""
        result = self.surface.get_safe_next_action()
        
        self.assertIsNone(result["recommended_action"])
        self.assertEqual(result["risk_level"], "unknown")
        self.assertEqual(result["required_verification"], [])
        self.assertEqual(result["fallback_options"], [])
    
    def test_get_safe_next_action_with_recommendations(self):
        """Test safe next action with recommendations loaded."""
        self.surface.load_recommendations(self.recommendations)
        
        result = self.surface.get_safe_next_action()
        
        self.assertIsNotNone(result["recommended_action"])
        # Risk level determined by confidence distribution (high conf = low risk)
        self.assertIn(result["risk_level"], ["low", "medium", "high", "unknown"])
        self.assertIn(result["risk_level"], ["low", "medium", "high"])
        self.assertGreater(len(result["required_verification"]), 0)
        self.assertEqual(len(result["fallback_options"]), 4)
    
    def test_get_safe_next_action_risk_low(self):
        """Test risk level when high confidence is present."""
        high_conf_recs = [
            {
                "recommendation_id": "recovery_high",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Proposal was rejected",
                "contributing_factors": ["Validation failed"],
                "recovery_hint": "Address validation criteria",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ]
        self.surface.load_recommendations(high_conf_recs)
        
        result = self.surface.get_safe_next_action()
        
        self.assertEqual(result["risk_level"], "low")
    
    def test_get_safe_next_action_risk_high(self):
        """Test risk level when only low confidence is present."""
        low_conf_recs = [
            {
                "recommendation_id": "recovery_low",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Unknown cause",
                "contributing_factors": ["Insufficient data"],
                "recovery_hint": "Review logs",
                "confidence": "low",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ]
        self.surface.load_recommendations(low_conf_recs)
        
        result = self.surface.get_safe_next_action()
        
        self.assertEqual(result["risk_level"], "high")
    
    def test_get_confidence_guidance_no_recommendations(self):
        """Test confidence guidance with no recommendations."""
        result = self.surface.get_confidence_guidance()
        
        self.assertEqual(result["distribution"], {})
        self.assertEqual(result["meaning"], "No recommendations loaded")
        self.assertEqual(result["recommendations_by_confidence"], {})
    
    def test_get_confidence_guidance_with_recommendations(self):
        """Test confidence guidance with recommendations."""
        self.surface.load_recommendations(self.recommendations)
        
        result = self.surface.get_confidence_guidance()
        
        self.assertIn("medium", result["distribution"])
        self.assertIn("high", result["distribution"])
        self.assertIn("low", result["distribution"])
        # Confidence meaning clarifies guidance vs certainty
        meaning_lower = result["meaning"].lower()
        self.assertTrue("confidence" in meaning_lower and "reliability" in meaning_lower)
        self.assertIn("recovery_1", result["recommendations_by_confidence"]["medium"][0]["recommendation_id"])
    
    def test_get_recommendation_json(self):
        """Test machine-readable JSON export."""
        self.surface.load_recommendations(self.recommendations)
        
        json_str = self.surface.get_recommendation_json()
        data = json.loads(json_str)
        
        self.assertEqual(data["review_surface_version"], "v77")
        self.assertIn("export_timestamp", data)
        self.assertIn("summary", data)
        self.assertIn("alternatives", data)
        self.assertIn("safe_next_action", data)
        self.assertIn("confidence_guidance", data)
        self.assertIn("recommendations_by_id", data)
        self.assertEqual(len(data["recommendations_by_id"]), 3)
    
    def test_json_includes_hint_certainty(self):
        """Test that JSON export includes hint_certainty marker."""
        self.surface.load_recommendations(self.recommendations)
        
        json_str = self.surface.get_recommendation_json()
        data = json.loads(json_str)
        
        for rec in data["recommendations_by_id"].values():
            self.assertEqual(rec["hint_certainty"], "suggestion")


class TestRecoveryRecommendationReviewCorrelation(unittest.TestCase):
    """Test correlation filtering by flow/request/handshake/deadline IDs."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.surface = RecoveryRecommendationReviewSurface()
        self.recommendations = [
            {
                "recommendation_id": "recovery_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Proposal rejected",
                "contributing_factors": [],
                "recovery_hint": "Review rejection reason",
                "confidence": "medium",
                "hint_certainty": "suggestion",
                "correlation_ids": {
                    "flow_id": "flow_abc123",
                    "request_id": "req_xyz789",
                },
                "generated_at": "2026-04-07T10:00:00Z",
            },
            {
                "recommendation_id": "recovery_2",
                "stage": "handshake",
                "failure_type": "handshake_failed",
                "likely_cause": "Handshake failed",
                "contributing_factors": [],
                "recovery_hint": "Verify protocol compatibility",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {
                    "handshake_id": "hs_def456",
                    "flow_id": "flow_abc123",
                },
                "generated_at": "2026-04-07T10:01:00Z",
            },
            {
                "recommendation_id": "recovery_3",
                "stage": "envelope",
                "failure_type": "envelope_gate_failed",
                "likely_cause": "Gate failed",
                "contributing_factors": [],
                "recovery_hint": "Review gate logs",
                "confidence": "low",
                "hint_certainty": "suggestion",
                "correlation_ids": {
                    "deadline_id": "dl_ghi789",
                },
                "generated_at": "2026-04-07T10:02:00Z",
            },
        ]
        self.surface.load_recommendations(self.recommendations)
    
    def test_correlation_filter_flow_id(self):
        """Test filtering by flow_id."""
        filtered = self.surface.get_correlated_recommendations(flow_id="flow_abc123")
        
        self.assertEqual(len(filtered), 2)
        rec_ids = [r["recommendation_id"] for r in filtered]
        self.assertIn("recovery_1", rec_ids)
        self.assertIn("recovery_2", rec_ids)
    
    def test_correlation_filter_request_id(self):
        """Test filtering by request_id."""
        filtered = self.surface.get_correlated_recommendations(request_id="req_xyz789")
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["recommendation_id"], "recovery_1")
    
    def test_correlation_filter_handshake_id(self):
        """Test filtering by handshake_id."""
        filtered = self.surface.get_correlated_recommendations(handshake_id="hs_def456")
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["recommendation_id"], "recovery_2")
    
    def test_correlation_filter_deadline_id(self):
        """Test filtering by deadline_id."""
        filtered = self.surface.get_correlated_recommendations(deadline_id="dl_ghi789")
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["recommendation_id"], "recovery_3")
    
    def test_correlation_filter_no_filter_returns_all(self):
        """Test that no filter returns all recommendations."""
        filtered = self.surface.get_correlated_recommendations()
        
        self.assertEqual(len(filtered), 3)


class TestRecoveryRecommendationReviewConfidence(unittest.TestCase):
    """Test confidence presentation as operator guidance (not certainty)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.surface = RecoveryRecommendationReviewSurface()
    
    def test_confidence_distribution(self):
        """Test confidence distribution in summary."""
        recommendations = [
            {
                "recommendation_id": "rec_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "contributing_factors": [],
                "recovery_hint": "Address criteria",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
            {
                "recommendation_id": "rec_2",
                "stage": "proposal",
                "failure_type": "proposal_expired",
                "likely_cause": "Expired",
                "contributing_factors": [],
                "recovery_hint": "Increase TTL",
                "confidence": "medium",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:01:00Z",
            },
        ]
        self.surface.load_recommendations(recommendations)
        
        summary = self.surface.get_recommendation_summary()
        conf_dist = summary["confidence_distribution"]
        
        self.assertEqual(conf_dist.get("high"), 1)
        self.assertEqual(conf_dist.get("medium"), 1)
    
    def test_confidence_meaning_not_certainty(self):
        """Test that confidence meaning clarifies it's guidance, not certainty."""
        recommendations = [
            {
                "recommendation_id": "rec_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "contributing_factors": [],
                "recovery_hint": "Address criteria",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ]
        self.surface.load_recommendations(recommendations)
        
        guidance = self.surface.get_confidence_guidance()
        
        # Meaning should clarify guidance vs certainty
        meaning_lower = guidance["meaning"].lower()
        self.assertTrue("reliability" in meaning_lower or "confidence" in meaning_lower)
        self.assertTrue("not guaranteed" in meaning_lower or "operator" in meaning_lower or "verify" in meaning_lower)
    
    def test_recommendations_by_confidence_included(self):
        """Test that recommendations are grouped by confidence level."""
        recommendations = [
            {
                "recommendation_id": "rec_high",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "contributing_factors": [],
                "recovery_hint": "Address criteria",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
            {
                "recommendation_id": "rec_low",
                "stage": "handshake",
                "failure_type": "handshake_failed",
                "likely_cause": "Failed",
                "contributing_factors": [],
                "recovery_hint": "Check compatibility",
                "confidence": "low",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:01:00Z",
            },
        ]
        self.surface.load_recommendations(recommendations)
        
        guidance = self.surface.get_confidence_guidance()
        
        self.assertIn("high", guidance["recommendations_by_confidence"])
        self.assertIn("low", guidance["recommendations_by_confidence"])
        self.assertEqual(len(guidance["recommendations_by_confidence"]["high"]), 1)
        self.assertEqual(len(guidance["recommendations_by_confidence"]["low"]), 1)


class TestRecoveryRecommendationReviewAlternatives(unittest.TestCase):
    """Test alternative recommendation visibility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.surface = RecoveryRecommendationReviewSurface()
        self.recommendations = [
            {
                "recommendation_id": "recovery_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "contributing_factors": [],
                "recovery_hint": "Review criteria",
                "confidence": "medium",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
            {
                "recommendation_id": "recovery_2",
                "stage": "handshake",
                "failure_type": "handshake_failed",
                "likely_cause": "Failed",
                "contributing_factors": [],
                "recovery_hint": "Check compatibility",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:01:00Z",
            },
        ]
        self.surface.load_recommendations(self.recommendations)
    
    def test_alternatives_return_all(self):
        """Test that alternatives include all recommendations."""
        alternatives = self.surface.get_alternative_recommendations()
        
        self.assertEqual(len(alternatives), 2)
        rec_ids = [a["recommendation_id"] for a in alternatives]
        self.assertIn("recovery_1", rec_ids)
        self.assertIn("recovery_2", rec_ids)
    
    def test_alternatives_include_full_data(self):
        """Test that alternatives include full recommendation data."""
        alternatives = self.surface.get_alternative_recommendations()
        
        for alt in alternatives:
            self.assertIn("recommendation_id", alt)
            self.assertIn("likely_cause", alt)
            self.assertIn("recovery_hint", alt)
            self.assertIn("confidence", alt)


class TestRecoveryRecommendationReviewSafeNextAction(unittest.TestCase):
    """Test safe-next-action summary."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.surface = RecoveryRecommendationReviewSurface()
        self.recommendations = [
            {
                "recommendation_id": "recovery_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "contributing_factors": [],
                "recovery_hint": "Address validation criteria",
                "confidence": "medium",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ]
        self.surface.load_recommendations(self.recommendations)
    
    def test_safe_next_action_has_recommended_action(self):
        """Test that safe next action has recommended action."""
        result = self.surface.get_safe_next_action()
        
        self.assertIsNotNone(result["recommended_action"])
    
    def test_safe_next_action_has_risk_level(self):
        """Test that safe next action has risk level."""
        result = self.surface.get_safe_next_action()
        
        self.assertIn(result["risk_level"], ["low", "medium", "high", "unknown"])
    
    def test_safe_next_action_has_required_verification(self):
        """Test that safe next action has required verification steps."""
        result = self.surface.get_safe_next_action()
        
        self.assertGreater(len(result["required_verification"]), 0)
    
    def test_safe_next_action_has_fallback_options(self):
        """Test that safe next action has fallback options."""
        result = self.surface.get_safe_next_action()
        
        self.assertGreater(len(result["fallback_options"]), 0)
    
    def test_fallback_options_include_retry(self):
        """Test that fallback options include retry option."""
        result = self.surface.get_safe_next_action()
        
        self.assertIn("retry", " ".join(result["fallback_options"]).lower())


class TestRecoveryRecommendationReviewIntegration(unittest.TestCase):
    """Test integration with v75 service and backward compatibility."""
    
    def test_integrate_with_v75_service(self):
        """Test integration with v75 RecoveryRecommendationService."""
        v75_service = MockRecoveryRecommendationService()
        v75_service.add_recommendation({
            "recommendation_id": "rec_1",
            "stage": "proposal",
            "failure_type": "proposal_rejected",
            "likely_cause": "Rejected",
            "contributing_factors": [],
            "recovery_hint": "Address criteria",
            "confidence": "medium",
            "hint_certainty": "suggestion",
            "correlation_ids": {},
            "generated_at": "2026-04-07T10:00:00Z",
        })
        
        review_surface = integrate_with_v75_service(v75_service)
        
        summary = review_surface.get_recommendation_summary()
        self.assertEqual(summary["total_recommendations"], 1)
    
    def test_empty_service_integration(self):
        """Test integration with empty v75 service."""
        v75_service = MockRecoveryRecommendationService()
        
        review_surface = integrate_with_v75_service(v75_service)
        
        summary = review_surface.get_recommendation_summary()
        self.assertEqual(summary["total_recommendations"], 0)


class TestRecoveryRecommendationReviewBackwardCompat(unittest.TestCase):
    """Test backward compatibility with v72-v76 exports."""
    
    def test_backward_compat_with_v76_export_format(self):
        """Test compatibility with v76 export format."""
        # v76 format (before v77 review surface)
        v76_recommendations = [
            {
                "export_id": "rec_export_12345678",
                "recommendation_id": "recovery_1",
                "timestamp": "2026-04-07T10:00:00Z",
                "correlation_ids": {
                    "flow_id": "flow_abc123",
                },
                "recommendation_data": {
                    "stage": "proposal",
                    "failure_type": "proposal_rejected",
                    "likely_cause": "Rejected",
                    "contributing_factors": [],
                    "recovery_hint": "Address criteria",
                    "confidence": "medium",
                    "hint_certainty": "suggestion",
                },
                "failure_classification": None,
                "recovery_hint": "Address criteria",
                "confidence_level": "medium",
                "confidence_explanation": "Operator guidance level: medium.",
            },
        ]
        
        # Extract recommendation data for review surface
        review_surface = RecoveryRecommendationReviewSurface()
        recommendations = [
            {
                "recommendation_id": rec["recommendation_id"],
                "stage": rec["recommendation_data"]["stage"],
                "failure_type": rec["recommendation_data"]["failure_type"],
                "likely_cause": rec["recommendation_data"]["likely_cause"],
                "contributing_factors": rec["recommendation_data"]["contributing_factors"],
                "recovery_hint": rec["recommendation_data"]["recovery_hint"],
                "confidence": rec["recommendation_data"]["confidence"],
                "hint_certainty": rec["recommendation_data"]["hint_certainty"],
                "correlation_ids": rec["correlation_ids"],
                "generated_at": rec["timestamp"],
            }
            for rec in v76_recommendations
        ]
        
        review_surface.load_recommendations(recommendations)
        
        summary = review_surface.get_recommendation_summary()
        self.assertEqual(summary["total_recommendations"], 1)
        self.assertTrue(summary["correlation_ids_present"])
    
    def test_backward_compat_with_v75_service_format(self):
        """Test compatibility with v75 service recommendation format."""
        # v75 service output format
        v75_recommendations = [
            {
                "recommendation_id": "recovery_1",
                "stage": "proposal",
                "failure_type": "proposal_rejected",
                "likely_cause": "Rejected",
                "contributing_factors": ["Trust threshold not met"],
                "recovery_hint": "Review rejection reason",
                "confidence": "medium",
                "hint_certainty": "suggestion",
                "correlation_ids": {
                    "flow_id": "flow_abc123",
                    "request_id": "req_xyz789",
                },
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ]
        
        review_surface = RecoveryRecommendationReviewSurface()
        review_surface.load_recommendations(v75_recommendations)
        
        summary = review_surface.get_recommendation_summary()
        self.assertEqual(summary["total_recommendations"], 1)
        self.assertEqual(summary["correlation_summary"]["flow_id"], 1)
        self.assertEqual(summary["correlation_summary"]["request_id"], 1)
    
    def test_backward_compat_with_v74_fallback_format(self):
        """Test compatibility with v74 fallback trace format."""
        # v74 format (fallback trace with recovery hints)
        v74_recommendations = [
            {
                "recommendation_id": "recovery_1",
                "stage": "handshake",
                "failure_type": "handshake_failed",
                "likely_cause": "Protocol mismatch",
                "contributing_factors": [],
                "recovery_hint": "Verify protocol compatibility",
                "confidence": "high",
                "hint_certainty": "suggestion",
                "correlation_ids": {},
                "generated_at": "2026-04-07T10:00:00Z",
            },
        ]
        
        review_surface = RecoveryRecommendationReviewSurface()
        review_surface.load_recommendations(v74_recommendations)
        
        result = review_surface.get_safe_next_action()
        self.assertIsNotNone(result["recommended_action"])
        self.assertIn("retry", " ".join(result["fallback_options"]).lower())


# ============================================================================
# MAIN
# ============================================================================


if __name__ == "__main__":
    unittest.main()
