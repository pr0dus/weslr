"""Tests for Outcome Feedback / Real-World Calibration Layer (v32)

Tests outcome_feedback.py data models, manager, calibration engine, and integration hooks.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.outcome_feedback import (
    RecommendationStatus,
    OutcomeQuality,
    ConfidenceAdjustment,
    RecommendationFeedback,
    FeedbackSummary,
    CalibrationRecord,
    OutcomeFeedbackManager,
    CalibrationEngine,
    integrate_with_adaptive_guidance,
    integrate_with_longitudinal_patterns,
    integrate_with_operator_context,
)


class TestFeedbackModels(unittest.TestCase):
    """Test feedback data models."""

    def test_recommendation_feedback_creation(self):
        """Test creating a recommendation feedback."""
        feedback = RecommendationFeedback(
            feedback_id="fb-001",
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            outcome_quality=OutcomeQuality.GOOD.value,
            satisfaction=0.8,
        )
        
        self.assertEqual(feedback.feedback_id, "fb-001")
        self.assertEqual(feedback.recommendation_id, "rec-001")
        self.assertEqual(feedback.status, RecommendationStatus.FOLLOWED.value)

    def test_recommendation_feedback_apply_calibration(self):
        """Test applying calibration to feedback."""
        feedback = RecommendationFeedback(
            feedback_id="fb-001",
            recommendation_id="rec-001",
        )
        
        feedback.apply_calibration(0.1, "Feedback showed good outcomes")
        
        self.assertEqual(feedback.confidence_adjustment, 0.1)
        self.assertIsNotNone(feedback.calibration_timestamp)
        self.assertEqual(feedback.adjustment_direction, ConfidenceAdjustment.INCREASE.value)

    def test_recommendation_feedback_serialization(self):
        """Test recommendation feedback to_dict/from_dict."""
        feedback = RecommendationFeedback(
            feedback_id="fb-001",
            recommendation_id="rec-001",
            status=RecommendationStatus.IGNORED.value,
        )
        
        feedback_dict = feedback.to_dict()
        feedback2 = RecommendationFeedback.from_dict(feedback_dict)
        
        self.assertEqual(feedback.feedback_id, feedback2.feedback_id)
        self.assertEqual(feedback.status, feedback2.status)

    def test_feedback_summary_creation(self):
        """Test creating a feedback summary."""
        summary = FeedbackSummary(recommendation_id="rec-001")
        
        self.assertEqual(summary.recommendation_id, "rec-001")
        self.assertEqual(summary.feedback_count, 0)

    def test_feedback_summary_update_from_feedback(self):
        """Test updating summary from feedback."""
        summary = FeedbackSummary(recommendation_id="rec-001")
        
        feedback = RecommendationFeedback(
            feedback_id="fb-001",
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            outcome_quality=OutcomeQuality.GOOD.value,
            satisfaction=0.8,
            confidence_adjustment=0.1,
            stress_delta=-0.2,
        )
        
        summary.update_from_feedback(feedback)
        
        self.assertEqual(summary.feedback_count, 1)
        self.assertEqual(summary.status_counts.get(RecommendationStatus.FOLLOWED.value), 1)
        self.assertEqual(summary.average_outcome_quality, 0.8)
        self.assertEqual(summary.average_satisfaction, 0.8)

    def test_feedback_summary_serialization(self):
        """Test feedback summary to_dict/from_dict."""
        summary = FeedbackSummary(recommendation_id="rec-001")
        
        summary_dict = summary.to_dict()
        summary2 = FeedbackSummary.from_dict(summary_dict)
        
        self.assertEqual(summary.recommendation_id, summary2.recommendation_id)

    def test_calibration_record_creation(self):
        """Test creating a calibration record."""
        record = CalibrationRecord(
            record_id="cal-001",
            recommendation_id="rec-001",
            adjustment_amount=0.15,
            adjustment_reason="Good outcomes observed",
        )
        
        self.assertEqual(record.record_id, "cal-001")
        self.assertEqual(record.adjustment_amount, 0.15)
        self.assertEqual(record.adjustment_reason, "Good outcomes observed")

    def test_calibration_record_serialization(self):
        """Test calibration record to_dict/from_dict."""
        record = CalibrationRecord(
            record_id="cal-001",
            recommendation_id="rec-001",
            adjustment_amount=0.15,
            adjustment_reason="Good outcomes observed",
        )
        
        record_dict = record.to_dict()
        record2 = CalibrationRecord.from_dict(record_dict)
        
        self.assertEqual(record.record_id, record2.record_id)


class TestOutcomeFeedbackManager(unittest.TestCase):
    """Test outcome feedback manager."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = OutcomeFeedbackManager(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_feedback(self):
        """Test recording feedback."""
        feedback = self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            outcome_quality=OutcomeQuality.GOOD.value,
            satisfaction=0.8,
        )
        
        self.assertIsNotNone(feedback)
        self.assertIn(feedback.feedback_id, self.manager.feedback)

    def test_apply_calibration(self):
        """Test applying calibration."""
        record = self.manager.apply_calibration(
            recommendation_id="rec-001",
            adjustment_amount=0.1,
            reason="Good outcomes observed",
        )
        
        self.assertIsNotNone(record)
        self.assertIn(record, self.manager.calibration_records)

    def test_get_summary(self):
        """Test getting feedback summary."""
        feedback = self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
        )
        
        summary = self.manager.get_summary("rec-001")
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.feedback_count, 1)

    def test_get_feedback(self):
        """Test getting feedback by ID."""
        feedback = self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.IGNORED.value,
        )
        
        retrieved = self.manager.get_feedback(feedback.feedback_id)
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.feedback_id, feedback.feedback_id)

    def test_get_all_feedback_for_recommendation(self):
        """Test getting all feedback for a recommendation."""
        self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
        )
        self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.IGNORED.value,
        )
        
        feedbacks = self.manager.get_all_feedback_for_recommendation("rec-001")
        
        self.assertEqual(len(feedbacks), 2)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
        )
        self.manager.apply_calibration(
            recommendation_id="rec-001",
            adjustment_amount=0.1,
            reason="Good outcomes",
        )
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["feedback_count"], 1)
        self.assertEqual(manager_dict["summary_count"], 1)
        self.assertEqual(manager_dict["calibration_count"], 1)


class TestCalibrationEngine(unittest.TestCase):
    """Test calibration engine."""

    def setUp(self):
        """Set up test manager and engine."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = OutcomeFeedbackManager(storage_path=self.temp_dir)
        self.engine = CalibrationEngine(self.manager)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_calibration_impact_no_feedback(self):
        """Test calibration impact when no feedback exists."""
        impact = self.engine.get_calibration_impact("rec-001")
        
        self.assertFalse(impact["has_calibration"])

    def test_get_calibration_impact_with_feedback(self):
        """Test calibration impact with feedback."""
        feedback = self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            outcome_quality=OutcomeQuality.GOOD.value,
            satisfaction=0.9,
        )
        
        # Add another feedback for averaging
        feedback2 = self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            outcome_quality=OutcomeQuality.EXCELLENT.value,
            satisfaction=1.0,
        )
        
        impact = self.engine.get_calibration_impact("rec-001")
        
        self.assertTrue(impact["has_calibration"])
        self.assertEqual(impact["feedback_count"], 2)

    def test_adjust_recommendation_confidence(self):
        """Test adjusting confidence based on calibration."""
        self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            confidence_adjustment=0.1,
            calibration_reason="Good outcomes",
        )
        self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            confidence_adjustment=0.1,
            calibration_reason="Good outcomes",
        )
        
        adjusted = self.engine.adjust_recommendation_confidence("rec-001", 0.7)
        
        # Adjusted should be 0.7 + 0.1 = 0.8
        self.assertAlmostEqual(adjusted, 0.8, places=5)

    def test_get_future_recommendation_quality(self):
        """Test getting future recommendation quality prediction."""
        self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            confidence_adjustment=0.1,
            calibration_reason="Good outcomes",
        )
        self.manager.record_feedback(
            recommendation_id="rec-001",
            status=RecommendationStatus.FOLLOWED.value,
            confidence_adjustment=0.1,
            calibration_reason="Good outcomes",
        )
        
        quality = self.engine.get_future_recommendation_quality("rec-001", 0.7)
        
        self.assertIn("adjusted_confidence", quality)
        self.assertAlmostEqual(quality["adjusted_confidence"], 0.8, places=5)
        self.assertIn("expected_outcome", quality)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for adaptive guidance, longitudinal patterns, and operator context."""

    def test_integrate_with_adaptive_guidance_adds_feedback_context(self):
        """Test that integration adds feedback context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("feedback_available", result)
        self.assertIn("calibration_impact", result)
        self.assertIn("adjusted_confidence", result)

    def test_integrate_with_longitudinal_patterns_adds_feedback_context(self):
        """Test that integration adds feedback context to longitudinal patterns."""
        patterns_dict = {
            "pattern_id": "pattern-001",
        }
        
        result = integrate_with_longitudinal_patterns(patterns_dict)
        
        self.assertIn("feedback_impact", result)
        self.assertIn("calibration_history", result)

    def test_integrate_with_operator_context_adds_feedback_context(self):
        """Test that integration adds feedback context to operator context."""
        context_dict = {
            "surface_id": "surface-001",
        }
        
        result = integrate_with_operator_context(context_dict)
        
        self.assertIn("feedback_available", result)
        self.assertIn("calibration_summary", result)
        self.assertIn("reliability_from_feedback", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing feedback context."""
        guidance_dict = {
            "guidance_id": "guidance-001",
            "feedback_available": True,
            "calibration_impact": 0.15,
            "adjusted_confidence": 0.85,
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertTrue(result["feedback_available"])
        self.assertEqual(result["calibration_impact"], 0.15)
        self.assertEqual(result["adjusted_confidence"], 0.85)


if __name__ == "__main__":
    unittest.main()
