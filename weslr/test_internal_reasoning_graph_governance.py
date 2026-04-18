"""Tests for Internal Reasoning Graph Governance Engine

Test Doctrine v1
Test Doctrine version: 1.0.0 (2026-04-08)
"""

from __future__ import annotations

import time
import unittest

from weslr.internal_reasoning_graph.governance import (
    GovernanceAction,
    GovernanceDecision,
    GovernanceEngineState,
    ProposalGovernanceEngine,
    ProposalHistoryRecord,
    ProposalReviewRecord,
    ProposalStatus,
)


class TestGovernanceEngineModel(unittest.TestCase):
    """Model tests for Governance Engine."""
    
    def test_governance_engine_state_serialization(self):
        """Test GovernanceEngineState serialization/deserialization."""
        state = GovernanceEngineState(
            enabled=True,
            require_operator_review=True,
            require_operator_approval=True,
            allow_auto_application=False,
        )
        
        serialized = state.to_dict()
        self.assertEqual(serialized["enabled"], True)
        self.assertEqual(serialized["require_operator_review"], True)
        self.assertEqual(serialized["require_operator_approval"], True)
        self.assertEqual(serialized["allow_auto_application"], False)
        
        # Test from_dict
        restored = GovernanceEngineState.from_dict(serialized)
        self.assertEqual(restored.enabled, True)
        self.assertEqual(restored.require_operator_review, True)
        self.assertEqual(restored.require_operator_approval, True)
        self.assertEqual(restored.allow_auto_application, False)
    
    def test_proposal_review_record_serialization(self):
        """Test ProposalReviewRecord serialization/deserialization."""
        record = ProposalReviewRecord(
            proposal_id="proposal-1",
            decision=GovernanceDecision.APPROVED,
            _reviewer="operator-1",
            timestamp=1234567890,
            notes="Approved by operator",
        )
        
        serialized = record.to_dict()
        self.assertEqual(serialized["proposal_id"], "proposal-1")
        self.assertEqual(serialized["reviewer"], "operator-1")
        self.assertEqual(serialized["decision"], "approved")
        self.assertEqual(serialized["timestamp"], 1234567890)
        self.assertEqual(serialized["notes"], "Approved by operator")
        
        # Test from_dict
        restored = ProposalReviewRecord.from_dict(serialized)
        self.assertEqual(restored.proposal_id, "proposal-1")
        self.assertEqual(restored.reviewer, "operator-1")
        self.assertEqual(restored.decision, GovernanceDecision.APPROVED)
    
    def test_proposal_history_record_serialization(self):
        """Test ProposalHistoryRecord serialization/deserialization."""
        record = ProposalHistoryRecord(
            proposal_id="proposal-1",
            timestamp=1234567890,
            status=ProposalStatus.APPROVED.value,
            actor="operator-1",
            action=GovernanceAction.APPROVE,
            notes="Approved by operator",
        )
        
        serialized = record.to_dict()
        self.assertEqual(serialized["proposal_id"], "proposal-1")
        self.assertEqual(serialized["timestamp"], 1234567890)
        self.assertEqual(serialized["status"], ProposalStatus.APPROVED.value)
        self.assertEqual(serialized["actor"], "operator-1")
        self.assertEqual(serialized["action"], "approve")
        
        # Test from_dict
        restored = ProposalHistoryRecord.from_dict(serialized)
        self.assertEqual(restored.proposal_id, "proposal-1")
        self.assertEqual(restored.action, GovernanceAction.APPROVE)


class TestGovernanceEngineBehavior(unittest.TestCase):
    """Behavior tests for Governance Engine."""
    
    def setUp(self):
        self.engine = ProposalGovernanceEngine()
        self.timestamp = int(time.time())
    
    def test_register_proposal(self):
        """Test proposal registration - automatic, no approval needed."""
        # Create a mock proposal node (minimal)
        class MockNode:
            def __init__(self, node_id):
                self.id = node_id
                self.metadata = {}
                self.status = "active"
                self.updated_at = int(time.time())
        
        node = MockNode("proposal-1")
        node.metadata["governance_status"] = ProposalStatus.PENDING.value
        node.status = "proposed"
        
        # Register should work without error
        result = self.engine.register_proposal(node, actor="system")
        
        # Check governance status updated
        self.assertEqual(result.metadata["governance_status"], ProposalStatus.PENDING.value)
        self.assertEqual(result.status, "proposed")
    
    def test_submit_for_review(self):
        """Test submitting for review - operator-triggered only."""
        record = self.engine.submit_for_review("proposal-1", "operator-1", timestamp=self.timestamp)
        
        self.assertEqual(record.proposal_id, "proposal-1")
        self.assertEqual(record.reviewer, "operator-1")
        self.assertEqual(record.decision, GovernanceDecision.PENDING)
        self.assertEqual(record.timestamp, self.timestamp)
    
    def test_approve_proposal(self):
        """Test approving proposal - operator-triggered only."""
        record = self.engine.approve_proposal("proposal-1", "operator-1", notes="Approved", timestamp=self.timestamp)
        
        self.assertEqual(record.proposal_id, "proposal-1")
        self.assertEqual(record.reviewer, "operator-1")
        self.assertEqual(record.decision, GovernanceDecision.APPROVED)
        self.assertEqual(record.timestamp, self.timestamp)
    
    def test_reject_proposal(self):
        """Test rejecting proposal - operator-triggered only."""
        record = self.engine.reject_proposal("proposal-1", "operator-1", notes="Rejected", timestamp=self.timestamp)
        
        self.assertEqual(record.proposal_id, "proposal-1")
        self.assertEqual(record.reviewer, "operator-1")
        self.assertEqual(record.decision, GovernanceDecision.REJECTED)
        self.assertEqual(record.timestamp, self.timestamp)
    
    def test_get_proposal_status(self):
        """Test getting proposal status - read-only query."""
        # First create history record
        self.engine.approve_proposal("proposal-1", "operator-1", timestamp=self.timestamp)
        
        # Get status - should return last recorded status
        status = self.engine.get_proposal_status("proposal-1")
        self.assertEqual(status, ProposalStatus.APPROVED.value)
    
    def test_get_proposal_history(self):
        """Test getting proposal history - read-only query."""
        self.engine.approve_proposal("proposal-1", "operator-1", timestamp=self.timestamp)
        self.engine.reject_proposal("proposal-2", "operator-2", timestamp=self.timestamp)
        
        history = self.engine.get_proposal_history("proposal-1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].proposal_id, "proposal-1")
        self.assertEqual(history[0].action, GovernanceAction.APPROVE)
    
    def test_export_governance_summary(self):
        """Test exporting governance summary - operator-readable + machine-readable."""
        self.engine.approve_proposal("proposal-1", "operator-1", timestamp=self.timestamp)
        self.engine.reject_proposal("proposal-2", "operator-2", timestamp=self.timestamp)
        
        summary = self.engine.export_governance_summary()
        
        self.assertIn("state", summary)
        self.assertIn("review_count", summary)
        self.assertIn("history_count", summary)
        self.assertEqual(summary["review_count"], 2)
        self.assertEqual(summary["history_count"], 2)


class TestGovernanceEngineIntegration(unittest.TestCase):
    """Integration tests for Governance Engine."""
    
    def test_engine_state_persistence(self):
        """Test governance engine state can be serialized and restored."""
        state = GovernanceEngineState(
            enabled=False,
            require_operator_review=False,
            require_operator_approval=False,
            allow_auto_application=True,
        )
        
        # Serialize and restore
        serialized = state.to_dict()
        restored = GovernanceEngineState.from_dict(serialized)
        
        # Verify all values preserved
        self.assertEqual(restored.enabled, False)
        self.assertEqual(restored.require_operator_review, False)
        self.assertEqual(restored.require_operator_approval, False)
        self.assertEqual(restored.allow_auto_application, True)
    
    def test_governance_engine_with_custom_state(self):
        """Test governance engine with custom state."""
        state = GovernanceEngineState(
            enabled=True,
            require_operator_review=True,
            require_operator_approval=True,
            allow_auto_application=False,
        )
        engine = ProposalGovernanceEngine(state=state)
        
        # Verify state is set
        self.assertEqual(engine.state.enabled, True)
        self.assertEqual(engine.state.require_operator_review, True)
        self.assertEqual(engine.state.require_operator_approval, True)
        self.assertEqual(engine.state.allow_auto_application, False)


class TestGovernanceEngineBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for Governance Engine."""
    
    def test_old_state_serialization(self):
        """Test old state serialization format still works."""
        # Old format (missing allow_auto_application)
        old_data = {
            "enabled": True,
            "require_operator_review": True,
            "require_operator_approval": True,
        }
        
        restored = GovernanceEngineState.from_dict(old_data)
        self.assertEqual(restored.enabled, True)
        self.assertEqual(restored.require_operator_review, True)
        self.assertEqual(restored.require_operator_approval, True)
        self.assertEqual(restored.allow_auto_application, False)  # Default value
    
    def test_old_review_record_serialization(self):
        """Test old review record format still works."""
        # Old format (missing reviewer field, using reviewed_by)
        old_data = {
            "proposal_id": "proposal-1",
            "reviewed_by": "operator-1",
            "decision": "approved",
            "timestamp": 1234567890,
            "notes": "Approved",
        }
        
        restored = ProposalReviewRecord.from_dict(old_data)
        self.assertEqual(restored.proposal_id, "proposal-1")
        self.assertEqual(restored.decision, GovernanceDecision.APPROVED)


class TestGovernanceEngineBoundaryConditions(unittest.TestCase):
    """Boundary condition tests for Governance Engine."""
    
    def test_auto_application_blocked(self):
        """Test that auto-application is always blocked by policy."""
        engine = ProposalGovernanceEngine()
        
        # Can never apply automatically
        can_apply = engine.can_apply("proposal-1")
        self.assertEqual(can_apply, False)
    
    def test_review_required_by_default(self):
        """Test that operator review is required by default."""
        engine = ProposalGovernanceEngine()
        
        self.assertTrue(engine.state.require_operator_review)
        self.assertTrue(engine.state.require_operator_approval)


if __name__ == "__main__":
    unittest.main()
