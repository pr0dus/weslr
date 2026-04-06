"""Tests for Multi-Timescale Planning / Trajectory Layer (v38)

Tests multi_timescale_planning.py data models, manager, and integration hooks.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.multi_timescale_planning import (
    HorizonType,
    HorizonPriority,
    HorizonConflictType,
    HorizonEntry,
    Trajectory,
    HorizonConflict,
    TrajectoryManager,
    integrate_with_goal_hierarchy,
    integrate_with_adaptive_guidance,
    integrate_with_intervention_timing,
    integrate_with_trust_dynamics,
)


class TestHorizonEntry(unittest.TestCase):
    """Test horizon entry data model."""

    def test_initial_state(self):
        """Test initial horizon entry state."""
        entry = HorizonEntry(
            entry_id="entry-001",
            title="Test Entry",
        )
        
        self.assertEqual(entry.entry_id, "entry-001")
        self.assertEqual(entry.horizon_type, HorizonType.SHORT_TERM.value)
        self.assertEqual(entry.title, "Test Entry")

    def test_horizon_type_enum(self):
        """Test getting horizon type as enum."""
        entry = HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.IMMEDIATE.value)
        self.assertEqual(entry.get_horizon_enum(), HorizonType.IMMEDIATE)

    def test_horizon_type_transitions(self):
        """Test all horizon types."""
        for horizon_type in [HorizonType.IMMEDIATE, HorizonType.SHORT_TERM, 
                           HorizonType.MEDIUM_TERM, HorizonType.LONG_TERM]:
            entry = HorizonEntry(entry_id="entry-001", horizon_type=horizon_type.value)
            self.assertEqual(entry.get_horizon_enum(), horizon_type)

    def test_is_overdue(self):
        """Test overdue detection."""
        entry = HorizonEntry(
            entry_id="entry-001",
            deadline_at="2020-01-01T00:00:00Z",  # Past
            priority=HorizonPriority.HIGH.value,
        )
        self.assertTrue(entry.is_overdue())

    def test_get_time_remaining(self):
        """Test time remaining calculation."""
        # Future deadline
        entry = HorizonEntry(
            entry_id="entry-001",
            deadline_at="2030-01-01T00:00:00Z",
        )
        remaining = entry.get_time_remaining_seconds()
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0)

    def test_serialization(self):
        """Test horizon entry to_dict/from_dict."""
        entry = HorizonEntry(
            entry_id="entry-001",
            horizon_type=HorizonType.SHORT_TERM.value,
            title="Test",
            depends_on=["dep-001"],
        )
        
        entry_dict = entry.to_dict()
        entry2 = HorizonEntry.from_dict(entry_dict)
        
        self.assertEqual(entry.entry_id, entry2.entry_id)
        self.assertEqual(entry.title, entry2.title)
        self.assertEqual(entry.depends_on, entry2.depends_on)


class TestTrajectory(unittest.TestCase):
    """Test trajectory data model."""

    def test_initial_state(self):
        """Test initial trajectory state."""
        trajectory = Trajectory(trajectory_id="traj-001")
        
        self.assertEqual(trajectory.trajectory_id, "traj-001")
        self.assertEqual(len(trajectory.entries), 0)

    def test_add_entry(self):
        """Test adding an entry."""
        trajectory = Trajectory(trajectory_id="traj-001")
        
        entry = HorizonEntry(entry_id="entry-001")
        trajectory.add_entry(entry)
        
        self.assertEqual(len(trajectory.entries), 1)
        self.assertEqual(trajectory.entries[0].entry_id, "entry-001")

    def test_get_entries_by_horizon(self):
        """Test getting entries by horizon type."""
        trajectory = Trajectory(trajectory_id="traj-001")
        
        trajectory.add_entry(HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.SHORT_TERM.value))
        trajectory.add_entry(HorizonEntry(entry_id="entry-002", horizon_type=HorizonType.SHORT_TERM.value))
        trajectory.add_entry(HorizonEntry(entry_id="entry-003", horizon_type=HorizonType.LONG_TERM.value))
        
        short_term = trajectory.get_entries_by_horizon(HorizonType.SHORT_TERM.value)
        self.assertEqual(len(short_term), 2)
        
        long_term = trajectory.get_entries_by_horizon(HorizonType.LONG_TERM.value)
        self.assertEqual(len(long_term), 1)

    def test_count_entries(self):
        """Test counting entries by horizon."""
        trajectory = Trajectory(trajectory_id="traj-001")
        
        trajectory.add_entry(HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.SHORT_TERM.value))
        trajectory.add_entry(HorizonEntry(entry_id="entry-002", horizon_type=HorizonType.MEDIUM_TERM.value))
        trajectory.add_entry(HorizonEntry(entry_id="entry-003", horizon_type=HorizonType.MEDIUM_TERM.value))
        
        counts = trajectory.count_entries()
        
        self.assertEqual(counts[HorizonType.SHORT_TERM.value], 1)
        self.assertEqual(counts[HorizonType.MEDIUM_TERM.value], 2)
        self.assertEqual(counts[HorizonType.LONG_TERM.value], 0)
        self.assertEqual(counts[HorizonType.IMMEDIATE.value], 0)

    def test_get_horizon_summary(self):
        """Test horizon summary."""
        trajectory = Trajectory(trajectory_id="traj-001")
        
        trajectory.add_entry(HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.SHORT_TERM.value))
        trajectory.add_entry(HorizonEntry(entry_id="entry-002", horizon_type=HorizonType.MEDIUM_TERM.value))
        
        summary = trajectory.get_horizon_summary()
        
        self.assertEqual(summary["short_term_count"], 1)
        self.assertEqual(summary["medium_term_count"], 1)
        self.assertEqual(summary["total_entries"], 2)

    def test_serialization(self):
        """Test trajectory to_dict/from_dict."""
        trajectory = Trajectory(trajectory_id="traj-001", name="Test Trajectory")
        
        entry = HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.SHORT_TERM.value)
        trajectory.add_entry(entry)
        
        trajectory_dict = trajectory.to_dict()
        trajectory2 = Trajectory.from_dict(trajectory_dict)
        
        self.assertEqual(trajectory.trajectory_id, trajectory2.trajectory_id)
        self.assertEqual(trajectory.name, trajectory2.name)
        self.assertEqual(len(trajectory2.entries), 1)


class TestHorizonConflict(unittest.TestCase):
    """Test horizon conflict data model."""

    def test_initial_state(self):
        """Test initial conflict state."""
        conflict = HorizonConflict(
            conflict_id="conflict-001",
            trajectory_id="traj-001",
            entry_a_id="entry-001",
            entry_b_id="entry-002",
        )
        
        self.assertEqual(conflict.conflict_id, "conflict-001")
        self.assertEqual(conflict.entry_a_id, "entry-001")
        self.assertEqual(conflict.entry_b_id, "entry-002")
        self.assertFalse(conflict.is_resolved)

    def test_resolve_conflict(self):
        """Test resolving a conflict."""
        conflict = HorizonConflict(
            conflict_id="conflict-001",
            trajectory_id="traj-001",
            entry_a_id="entry-001",
            entry_b_id="entry-002",
        )
        
        conflict.resolve("Resolved by adjusting deadlines")
        
        self.assertTrue(conflict.is_resolved)
        self.assertIsNotNone(conflict.resolved_at)
        self.assertEqual(conflict.resolution_description, "Resolved by adjusting deadlines")

    def test_serialization(self):
        """Test conflict to_dict/from_dict."""
        conflict = HorizonConflict(
            conflict_id="conflict-001",
            trajectory_id="traj-001",
            entry_a_id="entry-001",
            entry_b_id="entry-002",
            severity=0.8,
            description="Timing conflict",
        )
        
        conflict_dict = conflict.to_dict()
        conflict2 = HorizonConflict.from_dict(conflict_dict)
        
        self.assertEqual(conflict.conflict_id, conflict2.conflict_id)
        self.assertEqual(conflict.severity, conflict2.severity)
        self.assertEqual(conflict.description, conflict2.description)


class TestTrajectoryManager(unittest.TestCase):
    """Test trajectory manager."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TrajectoryManager(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_trajectory(self):
        """Test creating a trajectory."""
        trajectory = self.manager.create_trajectory("traj-001", "Test Trajectory")
        
        self.assertIsNotNone(trajectory)
        self.assertEqual(trajectory.trajectory_id, "traj-001")
        self.assertEqual(trajectory.name, "Test Trajectory")

    def test_get_trajectory(self):
        """Test getting a trajectory."""
        self.manager.create_trajectory("traj-001")
        
        trajectory = self.manager.get_trajectory("traj-001")
        self.assertIsNotNone(trajectory)

    def test_get_default_trajectory(self):
        """Test getting default trajectory."""
        trajectory = self.manager.get_default_trajectory()
        
        self.assertIsNotNone(trajectory)
        self.assertEqual(trajectory.trajectory_id, "default")

    def test_add_entry(self):
        """Test adding an entry."""
        entry = HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.SHORT_TERM.value)
        self.manager.add_entry("traj-001", entry)
        
        trajectory = self.manager.get_trajectory("traj-001")
        self.assertEqual(len(trajectory.entries), 1)

    def test_create_immediate_entry(self):
        """Test creating an immediate entry."""
        entry = self.manager.create_immediate_entry(
            "traj-001",
            title="Immediate Action",
            target_action="Do something now",
            urgency=0.9,
        )
        
        self.assertEqual(entry.horizon_type, HorizonType.IMMEDIATE.value)
        self.assertEqual(entry.title, "Immediate Action")
        self.assertEqual(entry.urgency, 0.9)

    def test_create_short_term_entry(self):
        """Test creating a short-term entry."""
        entry = self.manager.create_short_term_entry(
            "traj-001",
            title="Short Term Plan",
            deadline_at="2030-01-01T00:00:00Z",
            priority=HorizonPriority.HIGH.value,
        )
        
        self.assertEqual(entry.horizon_type, HorizonType.SHORT_TERM.value)
        self.assertEqual(entry.title, "Short Term Plan")
        self.assertEqual(entry.deadline_at, "2030-01-01T00:00:00Z")
        self.assertEqual(entry.priority, HorizonPriority.HIGH.value)

    def test_create_medium_term_entry(self):
        """Test creating a medium-term entry."""
        entry = self.manager.create_medium_term_entry(
            "traj-001",
            title="Medium Term Habit",
            duration_seconds=86400,
            priority=HorizonPriority.HIGH.value,
        )
        
        self.assertEqual(entry.horizon_type, HorizonType.MEDIUM_TERM.value)
        self.assertEqual(entry.duration_seconds, 86400)

    def test_create_long_term_entry(self):
        """Test creating a long-term entry."""
        entry = self.manager.create_long_term_entry(
            "traj-001",
            title="Long Term Goal",
            source="inference",
        )
        
        self.assertEqual(entry.horizon_type, HorizonType.LONG_TERM.value)
        self.assertEqual(entry.source, "inference")

    def test_detect_conflicts(self):
        """Test conflict detection."""
        trajectory = self.manager.create_trajectory("traj-001")
        
        entry1 = HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.SHORT_TERM.value)
        entry2 = HorizonEntry(entry_id="entry-002", horizon_type=HorizonType.MEDIUM_TERM.value)
        entry2.depends_on = ["entry-001"]
        
        trajectory.add_entry(entry1)
        trajectory.add_entry(entry2)
        
        self.manager.add_entry("traj-001", entry1)
        self.manager.add_entry("traj-001", entry2)
        
        # Basic test - conflicts are detected when dependencies form circular patterns
        conflicts = self.manager.detect_conflicts("traj-001")
        self.assertIsNotNone(conflicts)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        trajectory = self.manager.create_trajectory("traj-001")
        entry = HorizonEntry(entry_id="entry-001", horizon_type=HorizonType.SHORT_TERM.value)
        trajectory.add_entry(entry)
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["trajectory_count"], 1)
        self.assertIn("trajectories", manager_dict)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for goal hierarchy, adaptive guidance, intervention timing, and trust dynamics."""

    def test_integrate_with_goal_hierarchy_adds_trajectory_context(self):
        """Test that integration adds trajectory context to goal hierarchy."""
        hierarchy_dict = {
            "goal_id": "goal-001",
        }
        
        result = integrate_with_goal_hierarchy(hierarchy_dict)
        
        self.assertIn("trajectory_id", result)
        self.assertIn("horizon_type", result)
        self.assertEqual(result["horizon_type"], HorizonType.SHORT_TERM.value)
        self.assertIn("trajectory_confidence", result)

    def test_integrate_with_adaptive_guidance_adds_trajectory_context(self):
        """Test that integration adds trajectory context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("trajectory_id", result)
        self.assertIn("recommendation_horizon", result)
        self.assertIn("horizon_conflicts", result)

    def test_integrate_with_intervention_timing_adds_trajectory_context(self):
        """Test that integration adds trajectory context to intervention timing."""
        timing_dict = {
            "timing_id": "timing-001",
        }
        
        result = integrate_with_intervention_timing(timing_dict)
        
        self.assertIn("trajectory_id", result)
        self.assertIn("trajectory_priority", result)
        self.assertIn("trajectory_urgency", result)

    def test_integrate_with_trust_dynamics_adds_trajectory_context(self):
        """Test that integration adds trajectory context to trust dynamics."""
        trust_dict = {
            "trust_id": "trust-001",
        }
        
        result = integrate_with_trust_dynamics(trust_dict)
        
        self.assertIn("trajectory_id", result)
        self.assertIn("trajectory_transparency", result)
        self.assertEqual(result["trajectory_transparency"], "standard")

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing trajectory context."""
        guidance_dict = {
            "guidance_id": "guidance-001",
            "trajectory_id": "traj-custom",
            "recommendation_horizon": "immediate",
            "horizon_conflicts": [{"entry_a": "1", "entry_b": "2"}],
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertEqual(result["trajectory_id"], "traj-custom")
        self.assertEqual(result["recommendation_horizon"], "immediate")
        self.assertEqual(len(result["horizon_conflicts"]), 1)


if __name__ == "__main__":
    unittest.main()
