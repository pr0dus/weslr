"""Standalone test runner for operator_lifecycle.py tests"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import directly without going through tests/__init__.py
import unittest
from weslr.operator_lifecycle import (
    LifecycleStatus,
    TransitionType,
    TimelineVisibility,
    LifecycleTransition,
    LifecycleRollbackPoint,
    LifecycleTimeline,
    OperatorLifecycleEngine,
    integrate_with_state_transition,
    integrate_with_audit_ledger,
    integrate_with_audit_replay,
    integrate_with_operator_views,
)


class TestLifecycleModels(unittest.TestCase):
    """Test operator lifecycle data models."""

    def test_lifecycle_transition_creation(self):
        """Test creating a lifecycle transition."""
        transition = LifecycleTransition(
            transition_id="transition-001",
            transition_type="proposal_approved",
            timestamp="2026-04-06T17:53:00Z",
        )
        
        self.assertEqual(transition.transition_id, "transition-001")
        self.assertEqual(transition.transition_type, "proposal_approved")
        self.assertEqual(transition.source, "system")

    def test_lifecycle_transition_serialization(self):
        """Test lifecycle transition to_dict/from_dict."""
        transition = LifecycleTransition(
            transition_id="transition-001",
            transition_type="proposal_approved",
            timestamp="2026-04-06T17:53:00Z",
            from_state={"status": "pending"},
            to_state={"status": "approved"},
        )
        
        transition_dict = transition.to_dict()
        transition2 = LifecycleTransition.from_dict(transition_dict)
        
        self.assertEqual(transition.transition_id, transition2.transition_id)
        self.assertEqual(transition.from_state, transition2.from_state)

    def test_lifecycle_rollback_point_creation(self):
        """Test creating a rollback point."""
        current_time = "2026-04-06T17:53:00Z"
        rollback = LifecycleRollbackPoint(
            rollback_id="rollback-001",
            transition_id="transition-001",
            timestamp=current_time,
            state_snapshot={"status": "pending"},
        )
        
        self.assertEqual(rollback.rollback_id, "rollback-001")
        self.assertEqual(rollback.transition_id, "transition-001")
        self.assertEqual(rollback.rollback_type, "full")
        self.assertEqual(rollback.state_snapshot, {"status": "pending"})

    def test_lifecycle_rollback_point_serialization(self):
        """Test rollback point to_dict/from_dict."""
        current_time = "2026-04-06T17:53:00Z"
        rollback = LifecycleRollbackPoint(
            rollback_id="rollback-001",
            transition_id="transition-001",
            timestamp=current_time,
            state_snapshot={"status": "pending"},
            rollback_type="partial",
            can_revert=True,
            notes="Test rollback",
        )
        
        rollback_dict = rollback.to_dict()
        rollback2 = LifecycleRollbackPoint.from_dict(rollback_dict)
        
        self.assertEqual(rollback.rollback_id, rollback2.rollback_id)
        self.assertEqual(rollback.rollback_type, rollback2.rollback_type)

    def test_lifecycle_timeline_creation(self):
        """Test creating a lifecycle timeline."""
        timeline = LifecycleTimeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        self.assertEqual(timeline.timeline_id, "timeline-001")
        self.assertEqual(timeline.status, "initiated")
        self.assertEqual(timeline.transition_count, 0)

    def test_lifecycle_timeline_add_transition(self):
        """Test adding transitions to timeline."""
        timeline = LifecycleTimeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        transition = {
            "transition_id": "t1",
            "transition_type": "proposal_created",
            "timestamp": "2026-04-06T17:53:00Z",
        }
        timeline.add_transition(transition)
        
        self.assertEqual(timeline.transition_count, 1)
        self.assertEqual(len(timeline.transitions), 1)

    def test_lifecycle_timeline_add_rollback_point(self):
        """Test adding rollback points to timeline."""
        timeline = LifecycleTimeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        rollback = {
            "rollback_id": "r1",
            "transition_id": "t1",
            "timestamp": "2026-04-06T17:53:00Z",
            "state_snapshot": {"status": "pending"},
        }
        timeline.add_rollback_point(rollback)
        
        self.assertEqual(len(timeline.rollback_points), 1)

    def test_lifecycle_timeline_get_next_allowed_states(self):
        """Test getting next allowed states."""
        timeline = LifecycleTimeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
            status="active",
        )
        
        allowed = timeline.get_next_allowed_states()
        
        self.assertIn("resolved", allowed)
        self.assertIn("paused", allowed)
        self.assertIn("escalated", allowed)

    def test_lifecycle_timeline_generate_summary(self):
        """Test generating timeline summary."""
        timeline = LifecycleTimeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        # Add multiple transitions
        timeline.add_transition({
            "transition_id": "t1",
            "transition_type": "proposal_created",
            "timestamp": "2026-04-06T17:53:00Z",
        })
        timeline.add_transition({
            "transition_id": "t2",
            "transition_type": "proposal_approved",
            "timestamp": "2026-04-06T17:54:00Z",
        })
        timeline.add_transition({
            "transition_id": "t3",
            "transition_type": "proposal_approved",
            "timestamp": "2026-04-06T17:55:00Z",
        })
        
        summary = timeline.generate_summary()
        
        self.assertIn("Transitions:", summary)
        self.assertIn("proposal_created(1)", summary)
        self.assertIn("proposal_approved(2)", summary)

    def test_lifecycle_timeline_serialization(self):
        """Test timeline to_dict/from_dict."""
        timeline = LifecycleTimeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
            status="active",
        )
        
        timeline_dict = timeline.to_dict()
        timeline2 = LifecycleTimeline.from_dict(timeline_dict)
        
        self.assertEqual(timeline.timeline_id, timeline2.timeline_id)
        self.assertEqual(timeline.status, timeline2.status)


class TestOperatorLifecycleEngine(unittest.TestCase):
    """Test operator lifecycle engine."""

    def setUp(self):
        """Set up test engine."""
        self.engine = OperatorLifecycleEngine(
            storage_path="/tmp/test_lifecycle_engine"
        )

    def tearDown(self):
        """Clean up test engine."""
        import shutil
        import os
        
        storage_path = "/tmp/test_lifecycle_engine"
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)

    def test_create_timeline(self):
        """Test creating a new timeline."""
        timeline = self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        self.assertIsNotNone(timeline)
        self.assertEqual(timeline.timeline_id, "timeline-001")
        self.assertEqual(timeline.affected_object_id, "proposal-001")

    def test_get_timeline(self):
        """Test getting a timeline by ID."""
        self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        retrieved = self.engine.get_timeline("timeline-001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.timeline_id, "timeline-001")

    def test_get_timeline_by_object(self):
        """Test getting a timeline by affected object ID."""
        self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        retrieved = self.engine.get_timeline_by_object("proposal-001")
        self.assertIsNotNone(retrieved)

    def test_record_transition(self):
        """Test recording a transition."""
        self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        transition = self.engine.record_transition(
            timeline_id="timeline-001",
            transition_type="proposal_approved",
            approval_status="approved",
            author="operator-001",
        )
        
        self.assertIsNotNone(transition)
        self.assertEqual(transition.transition_type, "proposal_approved")

    def test_record_rollback_point(self):
        """Test recording a rollback point."""
        self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        self.engine.record_transition(
            timeline_id="timeline-001",
            transition_type="proposal_approved",
        )
        
        rollback = self.engine.record_rollback_point(
            timeline_id="timeline-001",
            transition_id="transition-0",
            state_snapshot={"status": "pending"},
        )
        
        self.assertIsNotNone(rollback)
        self.assertEqual(rollback.rollback_type, "full")

    def test_update_status(self):
        """Test updating timeline status."""
        self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        self.engine.update_status(
            timeline_id="timeline-001",
            status="active",
            current_state={"status": "active"},
            allowed_transitions=["resolved", "paused"],
        )
        
        timeline = self.engine.get_timeline("timeline-001")
        self.assertEqual(timeline.status, "active")
        self.assertEqual(timeline.current_state["status"], "active")

    def test_get_timeline_summary(self):
        """Test getting timeline summary."""
        self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        summary = self.engine.get_timeline_summary("timeline-001")
        
        self.assertEqual(summary["timeline_id"], "timeline-001")
        self.assertEqual(summary["transition_count"], 0)
        self.assertEqual(summary["timeline_exists"], True)

    def test_engine_serialization(self):
        """Test engine to_dict."""
        self.engine.create_timeline(
            timeline_id="timeline-001",
            affected_object_id="proposal-001",
            affected_object_type="proposal",
        )
        
        engine_dict = self.engine.to_dict()
        
        self.assertEqual(engine_dict["timeline_count"], 1)
        self.assertIn("timeline-001", engine_dict["timelines"])


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for state transitions, audit, replay, and operator views."""

    def test_integrate_with_state_transition_adds_lifecycle_context(self):
        """Test that integration adds lifecycle context to state transition."""
        state_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_state_transition(state_dict)
        
        self.assertIn("lifecycle_context", result)
        self.assertIsNone(result["lifecycle_context"])

    def test_integrate_with_audit_ledger_adds_lifecycle_context(self):
        """Test that integration adds lifecycle context to audit ledger."""
        audit_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_audit_ledger(audit_dict)
        
        self.assertIn("lifecycle_context", result)
        self.assertIsNone(result["lifecycle_context"])

    def test_integrate_with_audit_replay_adds_lifecycle_context(self):
        """Test that integration adds lifecycle context to audit replay."""
        replay_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_audit_replay(replay_dict)
        
        self.assertIn("lifecycle_context", result)
        self.assertIsNone(result["lifecycle_context"])

    def test_integrate_with_operator_views_adds_lifecycle_context(self):
        """Test that integration adds lifecycle context to operator views."""
        operator_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_operator_views(operator_dict)
        
        self.assertIn("lifecycle_context", result)
        self.assertIsNone(result["lifecycle_context"])

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing lifecycle context."""
        audit_dict = {
            "proposal_id": "proposal-001",
            "lifecycle_context": {"existing": "data"},
        }
        
        result = integrate_with_audit_ledger(audit_dict)
        
        self.assertEqual(result["lifecycle_context"]["existing"], "data")


if __name__ == "__main__":
    print("=" * 70)
    print("Running Operator Lifecycle / Timeline Surface v48 Tests")
    print("=" * 70)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestLifecycleModels))
    suite.addTests(loader.loadTestsFromTestCase(TestOperatorLifecycleEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationHooks))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.testsRun > 0 and len(result.failures) == 0 and len(result.errors) == 0:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed or had errors")
    
    print("=" * 70)
