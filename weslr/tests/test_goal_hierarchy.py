"""Tests for Goal Hierarchy / Priority Framework Layer (v33)

Tests goal_hierarchy.py data models, manager, priority framework, and integration hooks.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.goal_hierarchy import (
    GoalScope,
    GoalPriority,
    GoalStatus,
    PriorityConflict,
    Goal,
    GoalHierarchy,
    GoalHierarchyManager,
    PriorityFramework,
    integrate_with_adaptive_guidance,
    integrate_with_outcome_feedback,
    integrate_with_operator_context,
)


class TestGoalModels(unittest.TestCase):
    """Test goal data models."""

    def test_goal_creation(self):
        """Test creating a goal."""
        goal = Goal(
            goal_id="goal-001",
            title="Complete project",
            description="Finish the main project deliverables",
            scope=GoalScope.USER.value,
            priority=GoalPriority.HIGH.value,
            status=GoalStatus.PENDING.value,
        )
        
        self.assertEqual(goal.goal_id, "goal-001")
        self.assertEqual(goal.title, "Complete project")
        self.assertEqual(goal.scope, GoalScope.USER.value)
        self.assertEqual(goal.priority, GoalPriority.HIGH.value)
        self.assertEqual(goal.status, GoalStatus.PENDING.value)

    def test_goal_update_status(self):
        """Test updating goal status."""
        goal = Goal(goal_id="goal-001", title="Test")
        
        goal.update_status(GoalStatus.IN_PROGRESS.value)
        self.assertEqual(goal.status, GoalStatus.IN_PROGRESS.value)
        
        goal.update_status(GoalStatus.COMPLETED.value)
        self.assertEqual(goal.status, GoalStatus.COMPLETED.value)
        self.assertIsNotNone(goal.actual_completion)

    def test_goal_get_completion_rate(self):
        """Test getting completion rate."""
        # Pending + low priority
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            status=GoalStatus.PENDING.value,
            priority=GoalPriority.LOW.value,
        )
        self.assertEqual(goal.get_completion_rate(), 0.0)
        
        # In progress + high priority
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            status=GoalStatus.IN_PROGRESS.value,
            priority=GoalPriority.HIGH.value,
        )
        self.assertEqual(goal.get_completion_rate(), 0.5 * 1.1)  # 0.55
        
        # Completed + critical
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            status=GoalStatus.COMPLETED.value,
            priority=GoalPriority.CRITICAL.value,
        )
        self.assertEqual(goal.get_completion_rate(), 1.0 * 1.2)  # 1.2, clamped to 1.0

    def test_goal_is_urgent(self):
        """Test checking if goal is urgent."""
        # Urgent - pending + critical
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            status=GoalStatus.PENDING.value,
            priority=GoalPriority.CRITICAL.value,
        )
        self.assertTrue(goal.is_urgent())
        
        # Not urgent - completed + low
        goal = Goal(
            goal_id="goal-002",
            title="Test",
            status=GoalStatus.COMPLETED.value,
            priority=GoalPriority.LOW.value,
        )
        self.assertFalse(goal.is_urgent())

    def test_goal_serialization(self):
        """Test goal to_dict/from_dict."""
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            scope=GoalScope.USER.value,
            priority=GoalPriority.HIGH.value,
        )
        
        goal_dict = goal.to_dict()
        goal2 = Goal.from_dict(goal_dict)
        
        self.assertEqual(goal.goal_id, goal2.goal_id)
        self.assertEqual(goal.title, goal2.title)


class TestGoalHierarchy(unittest.TestCase):
    """Test goal hierarchy data model."""

    def test_hierarchy_creation(self):
        """Test creating a hierarchy."""
        hierarchy = GoalHierarchy(hierarchy_id="hierarchy-001")
        
        self.assertEqual(hierarchy.hierarchy_id, "hierarchy-001")
        self.assertEqual(len(hierarchy.user_goals), 0)

    def test_hierarchy_add_goal(self):
        """Test adding a goal to hierarchy."""
        hierarchy = GoalHierarchy(hierarchy_id="hierarchy-001")
        
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            scope=GoalScope.USER.value,
        )
        hierarchy.add_goal(goal)
        
        self.assertIn("goal-001", hierarchy.user_goals)

    def test_hierarchy_get_goal(self):
        """Test getting a goal from hierarchy."""
        hierarchy = GoalHierarchy(hierarchy_id="hierarchy-001")
        
        user_goal = Goal(
            goal_id="goal-001",
            title="User Goal",
            scope=GoalScope.USER.value,
        )
        domain_goal = Goal(
            goal_id="goal-002",
            title="Domain Goal",
            scope=GoalScope.DOMAIN.value,
        )
        
        hierarchy.add_goal(user_goal)
        hierarchy.add_goal(domain_goal)
        
        self.assertEqual(hierarchy.get_goal("goal-001"), user_goal)
        self.assertEqual(hierarchy.get_goal("goal-002"), domain_goal)

    def test_hierarchy_remove_goal(self):
        """Test removing a goal from hierarchy."""
        hierarchy = GoalHierarchy(hierarchy_id="hierarchy-001")
        
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            scope=GoalScope.USER.value,
        )
        hierarchy.add_goal(goal)
        
        self.assertTrue(hierarchy.remove_goal("goal-001"))
        self.assertIsNone(hierarchy.get_goal("goal-001"))
        
        # Remove non-existent
        self.assertFalse(hierarchy.remove_goal("goal-002"))

    def test_hierarchy_get_prioritized_goals(self):
        """Test getting prioritized goals."""
        hierarchy = GoalHierarchy(hierarchy_id="hierarchy-001")
        
        # Add goals with different priorities
        goal1 = Goal(
            goal_id="goal-001",
            title="Low",
            priority=GoalPriority.LOW.value,
            status=GoalStatus.PENDING.value,
        )
        goal2 = Goal(
            goal_id="goal-002",
            title="High",
            priority=GoalPriority.HIGH.value,
            status=GoalStatus.PENDING.value,
        )
        
        hierarchy.add_goal(goal1)
        hierarchy.add_goal(goal2)
        
        priorities = hierarchy.get_prioritized_goals()
        
        # High priority should come first
        self.assertEqual(priorities[0].goal_id, "goal-002")
        self.assertEqual(priorities[1].goal_id, "goal-001")

    def test_hierarchy_detect_conflicts(self):
        """Test detecting conflicts in hierarchy."""
        hierarchy = GoalHierarchy(hierarchy_id="hierarchy-001", enable_conflict_detection=True)
        
        # Add two high-priority goals in same scope
        goal1 = Goal(
            goal_id="goal-001",
            title="Goal 1",
            scope=GoalScope.USER.value,
            priority=GoalPriority.CRITICAL.value,
        )
        goal2 = Goal(
            goal_id="goal-002",
            title="Goal 2",
            scope=GoalScope.USER.value,
            priority=GoalPriority.HIGH.value,
        )
        
        hierarchy.add_goal(goal1)
        hierarchy.add_goal(goal2)
        
        conflicts = hierarchy.detect_conflicts()
        
        self.assertGreater(len(conflicts), 0)

    def test_hierarchy_serialization(self):
        """Test hierarchy to_dict/from_dict."""
        hierarchy = GoalHierarchy(hierarchy_id="hierarchy-001")
        
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            scope=GoalScope.USER.value,
        )
        hierarchy.add_goal(goal)
        
        hierarchy_dict = hierarchy.to_dict()
        hierarchy2 = GoalHierarchy.from_dict(hierarchy_dict)
        
        self.assertEqual(hierarchy.hierarchy_id, hierarchy2.hierarchy_id)
        self.assertIn("goal-001", hierarchy2.user_goals)


class TestGoalHierarchyManager(unittest.TestCase):
    """Test goal hierarchy manager."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = GoalHierarchyManager(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_hierarchy(self):
        """Test creating a new hierarchy."""
        hierarchy = self.manager.create_hierarchy("hierarchy-001", "Test Hierarchy")
        
        self.assertIsNotNone(hierarchy)
        self.assertEqual(hierarchy.hierarchy_id, "hierarchy-001")

    def test_add_goal(self):
        """Test adding a goal to hierarchy."""
        self.manager.create_hierarchy("hierarchy-001")
        
        goal = Goal(
            goal_id="goal-001",
            title="Test",
            scope=GoalScope.USER.value,
        )
        
        result = self.manager.add_goal("hierarchy-001", goal)
        self.assertTrue(result)
        
        hierarchy = self.manager.get_hierarchy("hierarchy-001")
        self.assertIn("goal-001", hierarchy.user_goals)

    def test_detect_conflicts(self):
        """Test detecting conflicts."""
        self.manager.create_hierarchy("hierarchy-001")
        
        goal1 = Goal(
            goal_id="goal-001",
            title="Goal 1",
            scope=GoalScope.USER.value,
            priority=GoalPriority.CRITICAL.value,
        )
        goal2 = Goal(
            goal_id="goal-002",
            title="Goal 2",
            scope=GoalScope.USER.value,
            priority=GoalPriority.HIGH.value,
        )
        
        self.manager.add_goal("hierarchy-001", goal1)
        self.manager.add_goal("hierarchy-001", goal2)
        
        conflicts = self.manager.detect_conflicts("hierarchy-001")
        
        self.assertGreater(len(conflicts), 0)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        self.manager.create_hierarchy("hierarchy-001")
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["hierarchy_count"], 1)
        self.assertIn("hierarchies", manager_dict)


class TestPriorityFramework(unittest.TestCase):
    """Test priority framework."""

    def setUp(self):
        """Set up test manager and framework."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = GoalHierarchyManager(storage_path=self.temp_dir)
        self.framework = PriorityFramework(self.manager)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_evaluate_recommendation_no_hierarchy(self):
        """Test evaluation when no hierarchy exists."""
        result = self.framework.evaluate_recommendation(
            "hierarchy-001",
            {"recommendation_id": "rec-001"},
        )
        
        self.assertEqual(result["alignment_score"], 0.0)
        self.assertEqual(result["conflict_count"], 0)

    def test_evaluate_recommendation_with_hierarchy(self):
        """Test evaluation with hierarchy."""
        self.manager.create_hierarchy("hierarchy-001")
        
        result = self.framework.evaluate_recommendation(
            "hierarchy-001",
            {"recommendation_id": "rec-001", "scope": GoalScope.USER.value},
        )
        
        self.assertIn("alignment_score", result)
        self.assertIn("recommendation", result)

    def test_evaluate_recommendation_with_conflicts(self):
        """Test evaluation when conflicts exist."""
        self.manager.create_hierarchy("hierarchy-001")
        
        # Add conflicting goals
        goal1 = Goal(
            goal_id="goal-001",
            title="Critical Goal",
            scope=GoalScope.USER.value,
            priority=GoalPriority.CRITICAL.value,
        )
        goal2 = Goal(
            goal_id="goal-002",
            title="Another Critical Goal",
            scope=GoalScope.USER.value,
            priority=GoalPriority.HIGH.value,
        )
        
        self.manager.add_goal("hierarchy-001", goal1)
        self.manager.add_goal("hierarchy-001", goal2)
        
        result = self.framework.evaluate_recommendation(
            "hierarchy-001",
            {"recommendation_id": "rec-001", "scope": GoalScope.USER.value},
        )
        
        self.assertGreater(result["conflict_count"], 0)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for adaptive guidance, outcome feedback, and operator context."""

    def test_integrate_with_adaptive_guidance_adds_goal_context(self):
        """Test that integration adds goal context to adaptive guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("goal_alignment", result)
        self.assertIn("conflict_with_goals", result)
        self.assertEqual(result["recommendation_scope"], GoalScope.USER.value)

    def test_integrate_with_outcome_feedback_adds_goal_context(self):
        """Test that integration adds goal context to outcome feedback."""
        feedback_dict = {
            "feedback_id": "fb-001",
        }
        
        result = integrate_with_outcome_feedback(feedback_dict)
        
        self.assertIn("goal_alignment", result)
        self.assertIn("goal_conflicts", result)

    def test_integrate_with_operator_context_adds_goal_context(self):
        """Test that integration adds goal context to operator context."""
        context_dict = {
            "surface_id": "surface-001",
        }
        
        result = integrate_with_operator_context(context_dict)
        
        self.assertIn("goal_hierarchy_available", result)
        self.assertIn("active_conflicts", result)
        self.assertIn("top_priorities", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing goal context."""
        guidance_dict = {
            "guidance_id": "guidance-001",
            "goal_alignment": 0.85,
            "conflict_with_goals": True,
            "recommendation_scope": GoalScope.HOUSEHOLD.value,
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertEqual(result["goal_alignment"], 0.85)
        self.assertTrue(result["conflict_with_goals"])
        self.assertEqual(result["recommendation_scope"], GoalScope.HOUSEHOLD.value)


if __name__ == "__main__":
    unittest.main()
