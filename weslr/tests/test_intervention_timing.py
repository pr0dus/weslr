"""Tests for Intervention Timing / Surfacing Policy Layer (v36)

Tests intervention_timing.py data models, manager, engine, and integration hooks.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.intervention_timing import (
    TimingStatus,
    TimingStrategy,
    RetryStrategy,
    TimingEvaluation,
    TimingPolicy,
    TimingRecord,
    TimingPolicyManager,
    TimingEngine,
    integrate_with_adaptive_guidance,
    integrate_with_longitudinal_patterns,
    integrate_with_household_context,
    integrate_with_compromise_explanation,
)


class TestTimingModels(unittest.TestCase):
    """Test timing data models."""

    def test_timing_evaluation_creation(self):
        """Test creating a timing evaluation."""
        evaluation = TimingEvaluation(
            evaluation_id="eval-001",
            intervention_id="intervention-001",
            suitability=0.8,
            status=TimingStatus.READY.value,
        )
        
        self.assertEqual(evaluation.evaluation_id, "eval-001")
        self.assertEqual(evaluation.suitability, 0.8)
        self.assertEqual(evaluation.status, TimingStatus.READY.value)

    def test_timing_evaluation_should_surface(self):
        """Test should_surface method."""
        # Ready, not in silent window
        evaluation = TimingEvaluation(
            evaluation_id="eval-001",
            intervention_id="intervention-001",
            status=TimingStatus.READY.value,
            in_silent_window=False,
        )
        self.assertTrue(evaluation.should_surface())
        
        # In cooldown
        evaluation = TimingEvaluation(
            evaluation_id="eval-002",
            intervention_id="intervention-001",
            status=TimingStatus.COOLDOWN.value,
        )
        self.assertFalse(evaluation.should_surface())
        
        # In silent window
        evaluation = TimingEvaluation(
            evaluation_id="eval-003",
            intervention_id="intervention-001",
            status=TimingStatus.READY.value,
            in_silent_window=True,
        )
        self.assertFalse(evaluation.should_surface())

    def test_timing_evaluation_apply_cooldown(self):
        """Test applying cooldown."""
        evaluation = TimingEvaluation(
            evaluation_id="eval-001",
            intervention_id="intervention-001",
        )
        
        evaluation.apply_cooldown(300, "Rejection occurred")
        
        self.assertEqual(evaluation.cooldown_reason, "Rejection occurred")
        self.assertIsNotNone(evaluation.cooldown_until)
        self.assertEqual(evaluation.status, TimingStatus.COOLDOWN.value)

    def test_timing_evaluation_serialization(self):
        """Test timing evaluation to_dict/from_dict."""
        evaluation = TimingEvaluation(
            evaluation_id="eval-001",
            intervention_id="intervention-001",
            suitability=0.8,
            status=TimingStatus.READY.value,
        )
        
        evaluation_dict = evaluation.to_dict()
        evaluation2 = TimingEvaluation.from_dict(evaluation_dict)
        
        self.assertEqual(evaluation.evaluation_id, evaluation2.evaluation_id)
        self.assertEqual(evaluation.suitability, evaluation2.suitability)

    def test_timing_policy_creation(self):
        """Test creating a timing policy."""
        policy = TimingPolicy(
            policy_id="policy-001",
            name="Default Policy",
        )
        
        self.assertEqual(policy.policy_id, "policy-001")
        self.assertTrue(policy.enable_silence_windows)
        self.assertIn(22, policy.quiet_hours)

    def test_timing_policy_is_in_silent_window(self):
        """Test checking silent window."""
        policy = TimingPolicy(
            policy_id="policy-001",
            enable_silence_windows=True,
            quiet_hours=[22, 23, 0, 1, 2, 3, 4, 5],
        )
        
        self.assertTrue(policy.is_in_silent_window(22))
        self.assertTrue(policy.is_in_silent_window(23))
        self.assertFalse(policy.is_in_silent_window(12))  # Noon
        
        # Disabled
        policy.enabled = False
        policy.enable_silence_windows = False
        self.assertFalse(policy.is_in_silent_window(22))

    def test_timing_policy_serialization(self):
        """Test timing policy to_dict/from_dict."""
        policy = TimingPolicy(
            policy_id="policy-001",
            name="Test Policy",
            default_delay_seconds=120,
        )
        
        policy_dict = policy.to_dict()
        policy2 = TimingPolicy.from_dict(policy_dict)
        
        self.assertEqual(policy.policy_id, policy2.policy_id)
        self.assertEqual(policy.default_delay_seconds, policy2.default_delay_seconds)

    def test_timing_record_creation(self):
        """Test creating a timing record."""
        record = TimingRecord(
            record_id="record-001",
            intervention_id="intervention-001",
        )
        
        self.assertEqual(record.record_id, "record-001")
        self.assertEqual(record.retry_count, 0)

    def test_timing_record_record_decision(self):
        """Test recording a decision."""
        record = TimingRecord(
            record_id="record-001",
            intervention_id="intervention-001",
        )
        
        decision = {"strategy": "delayed", "delay_seconds": 60}
        record.record_decision(decision)
        
        self.assertEqual(len(record.decisions), 1)
        self.assertEqual(record.last_decision, decision)

    def test_timing_record_record_retry(self):
        """Test recording a retry."""
        record = TimingRecord(
            record_id="record-001",
            intervention_id="intervention-001",
        )
        
        retry = {"attempt": 1, "delay_seconds": 60}
        record.record_retry(retry)
        
        self.assertEqual(record.retry_count, 1)
        self.assertEqual(len(record.retries), 1)

    def test_timing_record_serialization(self):
        """Test timing record to_dict/from_dict."""
        record = TimingRecord(
            record_id="record-001",
            intervention_id="intervention-001",
        )
        
        record_dict = record.to_dict()
        record2 = TimingRecord.from_dict(record_dict)
        
        self.assertEqual(record.record_id, record2.record_id)


class TestTimingPolicyManager(unittest.TestCase):
    """Test timing policy manager."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TimingPolicyManager(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_policy(self):
        """Test creating a timing policy."""
        policy = self.manager.create_policy("policy-001", "Test Policy")
        
        self.assertIsNotNone(policy)
        self.assertEqual(policy.policy_id, "policy-001")

    def test_get_policy(self):
        """Test getting a timing policy."""
        self.manager.create_policy("policy-001")
        
        policy = self.manager.get_policy("policy-001")
        self.assertIsNotNone(policy)

    def test_get_default_policy(self):
        """Test getting default policy."""
        policy = self.manager.get_default_policy()
        
        self.assertIsNotNone(policy)
        self.assertEqual(policy.policy_id, "default")

    def test_evaluate_timing(self):
        """Test evaluating timing."""
        policy = self.manager.create_policy("policy-001")
        
        evaluation = self.manager.evaluate_timing(
            "policy-001",
            "intervention-001",
            suitability=0.8,
            urgency=0.9,
        )
        
        self.assertIsNotNone(evaluation)
        self.assertEqual(evaluation.intervention_id, "intervention-001")

    def test_create_timing_record(self):
        """Test creating a timing record."""
        record = self.manager.create_timing_record("intervention-001")
        
        self.assertIsNotNone(record)
        self.assertEqual(record.intervention_id, "intervention-001")

    def test_record_decision(self):
        """Test recording a decision."""
        record = self.manager.create_timing_record("intervention-001")
        
        decision = {"strategy": "delayed", "delay_seconds": 60}
        result = self.manager.record_decision(record.record_id, decision)
        
        self.assertTrue(result)
        
        retrieved = self.manager.get_record(record.record_id)
        self.assertEqual(len(retrieved.decisions), 1)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        self.manager.create_policy("policy-001")
        self.manager.create_timing_record("intervention-001")
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["policy_count"], 1)
        self.assertEqual(manager_dict["record_count"], 1)


class TestTimingEngine(unittest.TestCase):
    """Test timing engine."""

    def setUp(self):
        """Set up test manager and engine."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TimingPolicyManager(storage_path=self.temp_dir)
        self.engine = TimingEngine(self.manager)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_should_intervene_policy_disabled(self):
        """Test intervention when policy disabled."""
        policy = self.manager.create_policy("policy-001")
        policy.enabled = False
        
        result = self.engine.should_intervene("intervention-001", "policy-001")
        
        self.assertFalse(result["should_intervene"])
        self.assertEqual(result["status"], TimingStatus.STOPPED.value)

    def test_should_intervene_ready(self):
        """Test intervention when ready."""
        result = self.engine.should_intervene("intervention-001")
        
        self.assertTrue(result["should_intervene"])
        self.assertEqual(result["status"], TimingStatus.READY.value)

    def test_should_intervene_silent_window(self):
        """Test intervention during silent window."""
        result = self.engine.should_intervene("intervention-001")
        
        # Check if in silent window (22-05 hours UTC)
        now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
        hour = now.hour
        
        # If in silent window (22-05 UTC), should be silent
        if 22 <= hour or hour <= 5:
            self.assertFalse(result["should_intervene"])
            self.assertEqual(result["status"], TimingStatus.SILENT.value)

    def test_should_intervene_max_retries(self):
        """Test intervention when max retries reached."""
        result = self.engine.should_intervene(
            "intervention-001",
            retry_count=5,  # Exceeds max of 3
        )
        
        self.assertFalse(result["should_intervene"])
        self.assertEqual(result["status"], TimingStatus.STOPPED.value)

    def test_get_retry_delay(self):
        """Test getting retry delay."""
        base_delay = 60
        
        # First retry
        delay1 = self.engine.get_retry_delay(0, base_delay)
        self.assertEqual(delay1, base_delay)
        
        # Second retry (escalated)
        delay2 = self.engine.get_retry_delay(1, base_delay)
        self.assertEqual(delay2, base_delay * 2)
        
        # Third retry (escalated)
        delay3 = self.engine.get_retry_delay(2, base_delay)
        self.assertEqual(delay3, base_delay * 4)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for adaptive guidance, longitudinal patterns, household context, and compromise explanation."""

    def test_integrate_with_adaptive_guidance_adds_timing_context(self):
        """Test that integration adds timing context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("timing_evaluation", result)
        self.assertIn("delay_seconds", result)
        self.assertIn("in_silent_window", result)
        self.assertTrue(result["should_intervene"])

    def test_integrate_with_longitudinal_patterns_adds_timing_context(self):
        """Test that integration adds timing context to longitudinal patterns."""
        patterns_dict = {
            "pattern_id": "pattern-001",
        }
        
        result = integrate_with_longitudinal_patterns(patterns_dict)
        
        self.assertIn("timing_context", result)
        self.assertIn("retry_count", result)
        self.assertIn("last_retry_delay", result)

    def test_integrate_with_household_context_adds_timing_context(self):
        """Test that integration adds timing context to household context."""
        household_dict = {
            "household_id": "household-001",
        }
        
        result = integrate_with_household_context(household_dict)
        
        self.assertIn("timing_policy", result)
        self.assertIn("quiet_hours", result)
        self.assertIn("interruption_cost", result)

    def test_integrate_with_compromise_explanation_adds_timing_context(self):
        """Test that integration adds timing context to compromise explanation."""
        explanation_dict = {
            "explanation_id": "exp-001",
        }
        
        result = integrate_with_compromise_explanation(explanation_dict)
        
        self.assertIn("timing_rationale", result)
        self.assertIn("delay_explanation", result)
        self.assertIn("silent_window_explanation", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing timing context."""
        guidance_dict = {
            "guidance_id": "guidance-001",
            "timing_evaluation": {"suitability": 0.8},
            "delay_seconds": 120,
            "in_silent_window": True,
            "should_intervene": False,
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertEqual(result["timing_evaluation"], {"suitability": 0.8})
        self.assertEqual(result["delay_seconds"], 120)
        self.assertTrue(result["in_silent_window"])
        self.assertFalse(result["should_intervene"])


if __name__ == "__main__":
    unittest.main()
