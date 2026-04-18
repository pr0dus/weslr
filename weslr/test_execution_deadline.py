"""Tests for Execution Deadline / Timeout Propagation Layer (v67)

Behavioral tests for deadline tracking, expiry detection, and breach handling.
"""

import os
import sys
import unittest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.execution_deadline import (
    ExecutionDeadline,
    ExecutionDeadlineState,
    DeadlineStatus,
    FlowDeadlineTracker,
)


class TestExecutionDeadline(unittest.TestCase):
    """Test deadline model."""

    def test_creation_defaults(self):
        """Deadline created with required fields."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        
        self.assertEqual(deadline.deadline_id, "dl-1")
        self.assertEqual(deadline.flow_id, "flow-1")
        self.assertEqual(deadline.state, ExecutionDeadlineState.PENDING.value)

    def test_mark_active(self):
        """Deadline marked as active."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_active()
        
        self.assertEqual(deadline.state, ExecutionDeadlineState.ACTIVE.value)

    def test_mark_breached(self):
        """Deadline marked as breached."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_breached("Execution timeout")
        
        self.assertEqual(deadline.state, ExecutionDeadlineState.BREACHED.value)
        self.assertEqual(deadline.breach_reason, "Execution timeout")
        self.assertIsNotNone(deadline.breached_at)

    def test_mark_cancelled(self):
        """Deadline marked as cancelled."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_cancelled()
        
        self.assertEqual(deadline.state, ExecutionDeadlineState.CANCELLED.value)
        self.assertIsNotNone(deadline.cancelled_at)

    def test_mark_completed(self):
        """Deadline marked as completed."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_completed()
        
        self.assertEqual(deadline.state, ExecutionDeadlineState.COMPLETED.value)

    def test_is_active(self):
        """Active state detected."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_active()
        
        self.assertTrue(deadline.is_active())

    def test_is_breached(self):
        """Breached state detected."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_breached("Timeout")
        
        self.assertTrue(deadline.is_breached())

    def test_is_cancelled(self):
        """Cancelled state detected."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_cancelled()
        
        self.assertTrue(deadline.is_cancelled())

    def test_is_completed(self):
        """Completed state detected."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_completed()
        
        self.assertTrue(deadline.is_completed())

    def test_is_expired(self):
        """Expired deadline detected."""
        past = datetime.now(timezone.utc) - timedelta(seconds=10)
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=past,
            created_at=datetime.now(timezone.utc) - timedelta(seconds=310)
        )
        
        self.assertTrue(deadline.is_expired())

    def test_get_remaining_seconds(self):
        """Remaining seconds calculated."""
        future = datetime.now(timezone.utc) + timedelta(seconds=300)
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=future,
            created_at=datetime.now(timezone.utc)
        )
        
        remaining = deadline.get_remaining_seconds()
        self.assertGreater(remaining, 290)  # Allow some time for test execution

    def test_serialization(self):
        """Round-trip serialization works."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_active()
        
        data = deadline.to_dict()
        restored = ExecutionDeadline.from_dict(data)
        
        self.assertEqual(restored.deadline_id, "dl-1")
        self.assertEqual(restored.flow_id, "flow-1")
        self.assertEqual(restored.state, ExecutionDeadlineState.ACTIVE.value)


class TestDeadlineStatus(unittest.TestCase):
    """Test deadline status operations."""

    def test_check_if_breached(self):
        """Breached deadline detected."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        deadline.mark_breached("Timeout")
        
        status = DeadlineStatus()
        self.assertTrue(status.check_if_breached(deadline))

    def test_mark_breached(self):
        """Deadline breached via status."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        
        status = DeadlineStatus()
        status.mark_breached(deadline, "Timeout")
        
        self.assertTrue(deadline.is_breached())

    def test_mark_cancelled(self):
        """Deadline cancelled via status."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        
        status = DeadlineStatus()
        status.mark_cancelled(deadline)
        
        self.assertTrue(deadline.is_cancelled())

    def test_mark_completed(self):
        """Deadline completed via status."""
        deadline = ExecutionDeadline(
            deadline_id="dl-1",
            flow_id="flow-1",
            absolute_deadline=datetime.now(timezone.utc) + timedelta(seconds=300),
            created_at=datetime.now(timezone.utc)
        )
        
        status = DeadlineStatus()
        status.mark_completed(deadline)
        
        self.assertTrue(deadline.is_completed())


class TestFlowDeadlineTracker(unittest.TestCase):
    """Test flow deadline tracker."""

    def setUp(self):
        self.tracker = FlowDeadlineTracker()

    def test_create_deadline(self):
        """Deadline created for flow."""
        deadline = self.tracker.create_deadline("flow-1", seconds=300)
        
        self.assertIsNotNone(deadline.deadline_id)
        self.assertEqual(deadline.flow_id, "flow-1")
        self.assertEqual(deadline.state, ExecutionDeadlineState.PENDING.value)

    def test_get_deadline(self):
        """Deadline retrieved by ID."""
        deadline = self.tracker.create_deadline("flow-1", seconds=300)
        
        retrieved = self.tracker.get_deadline(deadline.deadline_id)
        self.assertEqual(retrieved, deadline)

    def test_get_deadline_for_flow(self):
        """Deadline retrieved for flow."""
        deadline = self.tracker.create_deadline("flow-1", seconds=300)
        
        retrieved = self.tracker.get_deadline_for_flow("flow-1")
        self.assertEqual(retrieved, deadline)

    def test_remove_deadline(self):
        """Deadline removed for flow."""
        deadline = self.tracker.create_deadline("flow-1", seconds=300)
        
        removed = self.tracker.remove_deadline("flow-1")
        self.assertEqual(removed, deadline)
        self.assertIsNone(self.tracker.get_deadline_for_flow("flow-1"))

    def test_mark_flow_deadline_breached(self):
        """Deadline breached for flow."""
        deadline = self.tracker.create_deadline("flow-1", seconds=300)
        
        self.tracker.mark_flow_deadline_breached("flow-1", "Execution timeout")
        
        self.assertTrue(deadline.is_breached())
        self.assertEqual(deadline.breach_reason, "Execution timeout")

    def test_mark_flow_deadline_cancelled(self):
        """Deadline cancelled for flow."""
        deadline = self.tracker.create_deadline("flow-1", seconds=300)
        
        self.tracker.mark_flow_deadline_cancelled("flow-1")
        
        self.assertTrue(deadline.is_cancelled())

    def test_mark_flow_deadline_completed(self):
        """Deadline completed for flow."""
        deadline = self.tracker.create_deadline("flow-1", seconds=300)
        
        self.tracker.mark_flow_deadline_completed("flow-1")
        
        self.assertTrue(deadline.is_completed())

    def test_get_stats(self):
        """Statistics retrieved."""
        self.tracker.create_deadline("flow-1", seconds=300)
        self.tracker.create_deadline("flow-2", seconds=300)
        self.tracker.create_deadline("flow-3", seconds=300)
        
        self.tracker.mark_flow_deadline_breached("flow-1", "Timeout")
        self.tracker.mark_flow_deadline_cancelled("flow-2")
        self.tracker.mark_flow_deadline_completed("flow-3")
        
        stats = self.tracker.get_stats()
        
        self.assertEqual(stats["total_deadlines"], 3)
        self.assertEqual(stats["breached_deadlines"], 1)
        self.assertEqual(stats["cancelled_deadlines"], 1)
        self.assertEqual(stats["completed_deadlines"], 1)


if __name__ == "__main__":
    unittest.main()
