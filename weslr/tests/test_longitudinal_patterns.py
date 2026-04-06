"""Tests for Longitudinal User Pattern / Routine Memory Layer (v28)

Tests longitudinal_patterns.py data models, storage, analyzer, and guidance adaptation.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.longitudinal_patterns import (
    PatternType,
    PatternStability,
    PatternObservation,
    PatternSummary,
    PatternMemory,
    PatternMemoryStorage,
    PatternAnalyzer,
    LongitudinalGuidanceAdapter,
    GuidanceAdaptationMode,
    integrate_with_profile,
    integrate_with_adaptive_guidance,
    integrate_with_narrative,
)


class TestPatternModels(unittest.TestCase):
    """Test pattern data models."""

    def test_pattern_observation_creation(self):
        """Test creating a pattern observation."""
        observation = PatternObservation(
            timestamp="2026-04-06T12:00:00Z",
            context={"task": "writing", "domain": "code"},
            outcome="accepted",
            confidence=0.8,
        )
        
        self.assertEqual(observation.timestamp, "2026-04-06T12:00:00Z")
        self.assertEqual(observation.context, {"task": "writing", "domain": "code"})
        self.assertEqual(observation.outcome, "accepted")
        self.assertEqual(observation.confidence, 0.8)

    def test_pattern_observation_serialization(self):
        """Test pattern observation to_dict/from_dict."""
        observation = PatternObservation(
            timestamp="2026-04-06T12:00:00Z",
            context={"task": "writing"},
            confidence=0.7,
        )
        
        obs_dict = observation.to_dict()
        observation2 = PatternObservation.from_dict(obs_dict)
        
        self.assertEqual(observation.timestamp, observation2.timestamp)
        self.assertEqual(observation.confidence, observation2.confidence)

    def test_pattern_summary_creation(self):
        """Test creating a pattern summary."""
        summary = PatternSummary(
            pattern_id="routine_abc12345",
            pattern_type=PatternType.ROUTINE.value,
            first_observed="2026-04-01T08:00:00Z",
            last_observed="2026-04-06T08:00:00Z",
            frequency=5,
            context_signature="abc12345",
        )
        
        self.assertEqual(summary.pattern_id, "routine_abc12345")
        self.assertEqual(summary.pattern_type, PatternType.ROUTINE.value)
        self.assertEqual(summary.frequency, 5)
        self.assertEqual(summary.context_signature, "abc12345")

    def test_pattern_summary_update_from_observation(self):
        """Test updating summary from observation."""
        summary = PatternSummary(
            pattern_id="test_12345678",
            pattern_type=PatternType.GOAL.value,
            first_observed="2026-04-01T08:00:00Z",
            last_observed="2026-04-01T08:00:00Z",
            frequency=4,  # Start at 4 so adding 1 makes it 5 (DEVELOPING threshold)
            average_confidence=0.6,
        )
        
        observation = PatternObservation(
            timestamp="2026-04-06T08:00:00Z",
            context={"task": "testing"},
            confidence=0.8,
        )
        
        summary.update_from_observation(observation)
        
        self.assertEqual(summary.frequency, 5)
        self.assertEqual(summary.last_observed, "2026-04-06T08:00:00Z")
        self.assertAlmostEqual(summary.average_confidence, 0.64, places=2)
        self.assertEqual(summary.stability, PatternStability.DEVELOPING.value)

    def test_pattern_summary_stability_transitions(self):
        """Test stability transitions based on frequency."""
        summary = PatternSummary(
            pattern_id="test_12345678",
            pattern_type=PatternType.GOAL.value,
            first_observed="2026-04-01T08:00:00Z",
            last_observed="2026-04-01T08:00:00Z",
            frequency=0,
        )
        
        # Fluid initially
        self.assertEqual(summary.stability, PatternStability.FLUID.value)
        
        # Develops at 5
        for _ in range(5):
            summary.update_from_observation(PatternObservation(
                timestamp="2026-04-01T08:00:00Z",
                context={},
                confidence=0.5,
            ))
        self.assertEqual(summary.stability, PatternStability.DEVELOPING.value)
        
        # Stable at 10
        for _ in range(5):
            summary.update_from_observation(PatternObservation(
                timestamp="2026-04-01T08:00:00Z",
                context={},
                confidence=0.5,
            ))
        self.assertEqual(summary.stability, PatternStability.STABLE.value)
        
        # Locked at 20
        for _ in range(10):
            summary.update_from_observation(PatternObservation(
                timestamp="2026-04-01T08:00:00Z",
                context={},
                confidence=0.5,
            ))
        self.assertEqual(summary.stability, PatternStability.LOCKED.value)

    def test_pattern_summary_serialization(self):
        """Test pattern summary to_dict/from_dict."""
        summary = PatternSummary(
            pattern_id="test_12345678",
            pattern_type=PatternType.GOAL.value,
            first_observed="2026-04-01T08:00:00Z",
            last_observed="2026-04-06T08:00:00Z",
            frequency=10,
            context_signature="abcdef12",
        )
        
        summary_dict = summary.to_dict()
        summary2 = PatternSummary.from_dict(summary_dict)
        
        self.assertEqual(summary.pattern_id, summary2.pattern_id)
        self.assertEqual(summary.frequency, summary2.frequency)

    def test_pattern_memory_creation(self):
        """Test creating pattern memory."""
        summary = PatternSummary(
            pattern_id="test_12345678",
            pattern_type=PatternType.ROUTINE.value,
            first_observed="2026-04-01T08:00:00Z",
            last_observed="2026-04-01T08:00:00Z",
        )
        
        memory = PatternMemory(
            summary=summary,
            observations=[],
        )
        
        self.assertEqual(memory.summary.pattern_id, "test_12345678")
        self.assertEqual(len(memory.observations), 0)

    def test_pattern_memory_add_observation(self):
        """Test adding observation to pattern memory."""
        summary = PatternSummary(
            pattern_id="test_12345678",
            pattern_type=PatternType.ROUTINE.value,
            first_observed="2026-04-01T08:00:00Z",
            last_observed="2026-04-01T08:00:00Z",
            frequency=0,
        )
        
        memory = PatternMemory(summary=summary, observations=[])
        
        observation = PatternObservation(
            timestamp="2026-04-06T08:00:00Z",
            context={"task": "testing"},
            confidence=0.7,
        )
        
        memory.add_observation(observation)
        
        self.assertEqual(len(memory.observations), 1)
        self.assertEqual(memory.summary.frequency, 1)


class TestPatternMemoryStorage(unittest.TestCase):
    """Test pattern memory storage."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = PatternMemoryStorage(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_pattern(self):
        """Test creating a new pattern."""
        context = {"task": "testing", "domain": "code"}
        
        pattern = self.storage.create_pattern(
            pattern_type=PatternType.ROUTINE.value,
            context=context,
        )
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.summary.pattern_type, PatternType.ROUTINE.value)

    def test_record_observation_creates_pattern(self):
        """Test that recording observation creates pattern if needed."""
        context = {"task": "testing", "domain": "code"}
        
        pattern = self.storage.record_observation(
            pattern_type=PatternType.ROUTINE.value,
            context=context,
        )
        
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.summary.frequency, 1)

    def test_find_patterns_by_type(self):
        """Test finding patterns by type."""
        context1 = {"task": "testing", "domain": "code"}
        context2 = {"task": "writing", "domain": "docs"}
        
        # Create multiple patterns of same type with different contexts
        self.storage.record_observation(
            pattern_type=PatternType.ROUTINE.value,
            context=context1,
        )
        self.storage.record_observation(
            pattern_type=PatternType.ROUTINE.value,
            context=context2,
        )
        
        patterns = self.storage.find_patterns_by_type(PatternType.ROUTINE.value)
        
        self.assertEqual(len(patterns), 2)

    def test_find_patterns_by_signature(self):
        """Test finding patterns by context signature."""
        context = {"task": "testing", "time_of_day": "morning"}
        
        pattern = self.storage.record_observation(
            pattern_type=PatternType.ROUTINE.value,
            context=context,
        )
        
        patterns = self.storage.find_patterns_by_signature(pattern.summary.context_signature)
        
        self.assertGreaterEqual(len(patterns), 1)

    def test_pattern_persistence(self):
        """Test that patterns are persisted to storage."""
        context = {"task": "testing"}
        
        pattern = self.storage.create_pattern(
            pattern_type=PatternType.ROUTINE.value,
            context=context,
        )
        
        pattern_id = pattern.summary.pattern_id
        
        # Create new storage instance (simulates reload)
        new_storage = PatternMemoryStorage(storage_path=self.temp_dir)
        
        loaded_pattern = new_storage.get_pattern(pattern_id)
        
        self.assertIsNotNone(loaded_pattern)
        self.assertEqual(loaded_pattern.summary.pattern_id, pattern_id)


class TestPatternAnalyzer(unittest.TestCase):
    """Test pattern analyzer."""

    def setUp(self):
        """Set up test storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = PatternMemoryStorage(storage_path=self.temp_dir)
        self.analyzer = PatternAnalyzer(self.storage)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyze_pattern_insufficient_data(self):
        """Test analyzing pattern with insufficient data."""
        context = {"task": "testing"}
        pattern = self.storage.create_pattern(
            pattern_type=PatternType.ROUTINE.value,
            context=context,
        )
        
        # Add one more observation
        self.storage.record_observation(
            pattern_type=PatternType.ROUTINE.value,
            context=context,
        )
        
        analysis = self.analyzer.analyze_pattern(pattern.summary.pattern_id)
        
        self.assertEqual(analysis["frequency"], 2)
        self.assertEqual(analysis["stability"], PatternStability.FLUID.value)

    def test_analyze_pattern_with_observations(self):
        """Test analyzing pattern with multiple observations."""
        context = {"task": "testing", "domain": "code"}
        
        # Create pattern (creates 1 observation)
        pattern = self.storage.create_pattern(
            pattern_type=PatternType.SUCCESSFUL_GUIDANCE.value,
            context=context,
        )
        
        # Add 4 more observations (total 5)
        for i in range(4):
            self.storage.record_observation(
                pattern_type=PatternType.SUCCESSFUL_GUIDANCE.value,
                context=context,
                outcome="accepted" if i < 3 else "ignored",
            )
        
        analysis = self.analyzer.analyze_pattern(pattern.summary.pattern_id)
        
        self.assertEqual(analysis["frequency"], 5)
        self.assertIn("regularity", analysis)
        self.assertIn("outcome_distribution", analysis)


class TestLongitudinalGuidanceAdapter(unittest.TestCase):
    """Test longitudinal guidance adapter."""

    def setUp(self):
        """Set up test storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = PatternMemoryStorage(storage_path=self.temp_dir)
        self.adapter = LongitudinalGuidanceAdapter(self.storage)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_guidance_adaptation_no_patterns(self):
        """Test getting adaptation when no patterns exist."""
        context = {"task": "testing", "domain": "code"}
        
        adaptation = self.adapter.get_guidance_adaptation(context)
        
        self.assertEqual(adaptation["adaptation_count"], 0)
        self.assertFalse(adaptation["should_hold_back"])

    def test_record_successful_guidance(self):
        """Test recording successful guidance."""
        context = {"task": "testing", "domain": "code"}
        
        pattern_id = self.adapter.record_successful_guidance(context)
        
        patterns = self.storage.find_patterns_by_type(PatternType.SUCCESSFUL_GUIDANCE.value)
        self.assertEqual(len(patterns), 1)
        
        analysis = self.adapter.pattern_analyzer.analyze_pattern(pattern_id)
        outcome_dist = analysis.get("outcome_distribution", {})
        self.assertEqual(outcome_dist.get("accepted"), 1)

    def test_record_ignored_guidance(self):
        """Test recording ignored guidance."""
        context = {"task": "testing", "domain": "code"}
        
        pattern_id = self.adapter.record_ignored_guidance(context)
        
        patterns = self.storage.find_patterns_by_type(PatternType.IGNORED_GUIDANCE.value)
        self.assertEqual(len(patterns), 1)
        
        analysis = self.adapter.pattern_analyzer.analyze_pattern(pattern_id)
        outcome_dist = analysis.get("outcome_distribution", {})
        self.assertEqual(outcome_dist.get("ignored"), 1)

    def test_get_guidance_adaptation_with_overload(self):
        """Test getting adaptation with overload pattern."""
        context = {"task": "testing", "domain": "code"}
        
        # Record overload pattern
        self.adapter.record_overload(context)
        
        # Get adaptation (should detect overload)
        adaptation = self.adapter.get_guidance_adaptation(context)
        
        self.assertGreater(adaptation["adaptation_count"], 0)
        self.assertTrue(adaptation["should_hold_back"])

    def test_guidance_adaptation_with_successful_pattern(self):
        """Test adaptation boost from successful patterns."""
        context = {"task": "testing", "domain": "code"}
        
        # Record successful guidance
        self.adapter.record_successful_guidance(context)
        
        # Get adaptation (should show confidence boost)
        adaptation = self.adapter.get_guidance_adaptation(context)
        
        # Should have confidence boost
        self.assertGreater(adaptation["confidence_boost"], 0)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for profile, adaptive guidance, and narrative."""

    def test_integrate_with_profile_adds_pattern_fields(self):
        """Test that integration adds pattern fields to profile."""
        profile_dict = {
            "profile_id": "profile-001",
        }
        
        result = integrate_with_profile(profile_dict)
        
        self.assertIn("pattern_memory_enabled", result)
        self.assertTrue(result["pattern_memory_enabled"])
        self.assertIn("pattern_adaptation_mode", result)
        self.assertEqual(result["pattern_adaptation_mode"], GuidanceAdaptationMode.ACTIVE.value)

    def test_integrate_with_adaptive_guidance_adds_pattern_context(self):
        """Test that integration adds pattern context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("pattern_context", result)
        self.assertIn("confidence_boost_from_patterns", result)
        self.assertFalse(result["should_hold_back"])

    def test_integrate_with_narrative_adds_pattern_basis(self):
        """Test that integration adds pattern basis to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("pattern_basis", result)
        self.assertIn("confidence_from_patterns", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing pattern context."""
        profile_dict = {
            "profile_id": "profile-001",
            "pattern_memory_enabled": False,
            "pattern_adaptation_mode": GuidanceAdaptationMode.OFF.value,
        }
        
        result = integrate_with_profile(profile_dict)
        
        self.assertFalse(result["pattern_memory_enabled"])
        self.assertEqual(result["pattern_adaptation_mode"], GuidanceAdaptationMode.OFF.value)


if __name__ == "__main__":
    unittest.main()
