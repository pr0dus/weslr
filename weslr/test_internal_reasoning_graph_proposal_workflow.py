"""Tests for Internal Reasoning Graph Proposal Workflow

Test Doctrine v1
Test Doctrine version: 1.0.0 (2026-04-08)
"""

from __future__ import annotations

import time
import unittest

from weslr.internal_reasoning_graph.governance import (
    GovernanceDecision,
    ProposalGovernanceEngine,
)
from weslr.internal_reasoning_graph.proposal_workflow import (
    ProposalWorkflow,
    WorkflowRecord,
    WorkflowState,
    ProposalWorkflowState,
)
from weslr.internal_reasoning_graph.validation import (
    ProposalValidationEngine,
    ValidationStatus,
)


class MockNode:
    """Mock node for testing."""
    def __init__(self, node_id):
        self.id = node_id
        self.name = "Test Proposal"
        self.description = "Test proposal description"
        self.node_type = "proposal"
        self.metadata = {}
        self.status = "active"
        self.updated_at = int(time.time())


class TestProposalWorkflowModel(unittest.TestCase):
    """Model tests for Proposal Workflow."""
    
    def test_proposal_workflow_state_serialization(self):
        """Test ProposalWorkflowState serialization/deserialization."""
        state = ProposalWorkflowState(
            proposal_id="proposal-1",
            current_state=WorkflowState.APPROVED,
            validation_status=ValidationStatus.VALID,
            review_status="approved",
        )
        
        serialized = state.to_dict()
        self.assertEqual(serialized["proposal_id"], "proposal-1")
        self.assertEqual(serialized["current_state"], "approved")
        self.assertEqual(serialized["validation_status"], "valid")
        self.assertEqual(serialized["review_status"], "approved")
        
        # Test from_dict
        restored = ProposalWorkflowState.from_dict(serialized)
        self.assertEqual(restored.proposal_id, "proposal-1")
        self.assertEqual(restored.current_state, WorkflowState.APPROVED)
    
    def test_workflow_record_serialization(self):
        """Test WorkflowRecord serialization/deserialization."""
        record = WorkflowRecord(
            proposal_id="proposal-1",
            timestamp=1234567890,
            from_state=WorkflowState.REVIEWING,
            to_state=WorkflowState.APPROVED,
            actor="operator-1",
            action="approve_proposal",
            notes="Approved by operator",
        )
        
        serialized = record.to_dict()
        self.assertEqual(serialized["proposal_id"], "proposal-1")
        self.assertEqual(serialized["from_state"], "reviewing")
        self.assertEqual(serialized["to_state"], "approved")
        self.assertEqual(serialized["actor"], "operator-1")
        self.assertEqual(serialized["action"], "approve_proposal")
        
        # Test from_dict
        restored = WorkflowRecord.from_dict(serialized)
        self.assertEqual(restored.proposal_id, "proposal-1")
        self.assertEqual(restored.action, "approve_proposal")


class TestProposalWorkflowBehavior(unittest.TestCase):
    """Behavior tests for Proposal Workflow."""
    
    def setUp(self):
        self.governance = ProposalGovernanceEngine()
        self.validation = ProposalValidationEngine()
        self.workflow = ProposalWorkflow(
            governance_engine=self.governance,
            validation_engine=self.validation,
        )
    
    def test_route_proposal(self):
        """Test routing proposal - automatic."""
        node = MockNode("proposal-1")
        
        # Route should work
        record = self.workflow.route_proposal("proposal-1", actor="system")
        
        self.assertEqual(record.proposal_id, "proposal-1")
        self.assertEqual(record.from_state, WorkflowState.DRAFT)
        self.assertEqual(record.to_state, WorkflowState.SUBMITTED)
    
    def test_submit_for_review(self):
        """Test submitting for review - operator-triggered only."""
        node = MockNode("proposal-1")
        
        # Route first
        self.workflow.route_proposal("proposal-1", actor="system")
        
        # Then submit for review
        review_record = self.workflow.submit_for_review("proposal-1", "operator-1")
        
        self.assertEqual(review_record.proposal_id, "proposal-1")
        self.assertEqual(review_record.reviewer, "operator-1")
        self.assertEqual(review_record.decision, GovernanceDecision.PENDING)
    
    def test_approve_proposal(self):
        """Test approving proposal - operator-triggered only."""
        node = MockNode("proposal-1")
        
        # Route and submit for review first
        self.workflow.route_proposal("proposal-1", actor="system")
        self.workflow.submit_for_review("proposal-1", "operator-1")
        
        # Then approve
        review_record = self.workflow.approve_proposal("proposal-1", "operator-1", notes="Approved")
        
        self.assertEqual(review_record.proposal_id, "proposal-1")
        self.assertEqual(review_record.decision, GovernanceDecision.APPROVED)
    
    def test_reject_proposal(self):
        """Test rejecting proposal - operator-triggered only."""
        node = MockNode("proposal-1")
        
        # Route and submit for review first
        self.workflow.route_proposal("proposal-1", actor="system")
        self.workflow.submit_for_review("proposal-1", "operator-1")
        
        # Then reject
        review_record = self.workflow.reject_proposal("proposal-1", "operator-1", notes="Rejected")
        
        self.assertEqual(review_record.proposal_id, "proposal-1")
        self.assertEqual(review_record.decision, GovernanceDecision.REJECTED)
    
    def test_get_proposal_status(self):
        """Test getting proposal status - read-only query."""
        node = MockNode("proposal-1")
        
        # Route and approve
        self.workflow.route_proposal("proposal-1", actor="system")
        self.workflow.submit_for_review("proposal-1", "operator-1")
        self.workflow.approve_proposal("proposal-1", "operator-1", notes="Approved")
        
        # Get status
        status = self.workflow.get_proposal_status("proposal-1")
        
        self.assertEqual(status["proposal_id"], "proposal-1")
        self.assertEqual(status["state"], "approved")
        self.assertEqual(status["review_status"], "approved")
    
    def test_export_proposal_workflow(self):
        """Test exporting proposal workflow - operator-readable + machine-readable."""
        node = MockNode("proposal-1")
        
        # Create workflow
        self.workflow.route_proposal("proposal-1", actor="system")
        self.workflow.submit_for_review("proposal-1", "operator-1")
        self.workflow.approve_proposal("proposal-1", "operator-1", notes="Approved")
        
        # Export
        exported = self.workflow.export_proposal_workflow("proposal-1")
        
        self.assertIn("proposal_id", exported)
        self.assertIn("state", exported)
        self.assertIn("history", exported)
        self.assertIn("reviews", exported)
    
    def test_export_all_workflows(self):
        """Test exporting all workflows - operator-readable + machine-readable."""
        # Create multiple workflows
        self.workflow.route_proposal("proposal-1", actor="system")
        self.workflow.route_proposal("proposal-2", actor="system")
        
        exported = self.workflow.export_all_workflows()
        
        self.assertIn("workflows", exported)
        self.assertIn("total_count", exported)
        self.assertGreaterEqual(exported["total_count"], 2)


class TestProposalWorkflowIntegration(unittest.TestCase):
    """Integration tests for Proposal Workflow."""
    
    def test_full_workflow_lifecycle(self):
        """Test full workflow lifecycle: draft -> submitted -> reviewing -> approved."""
        governance = ProposalGovernanceEngine()
        validation = ProposalValidationEngine()
        workflow = ProposalWorkflow(
            governance_engine=governance,
            validation_engine=validation,
        )
        
        node = MockNode("proposal-1")
        
        # Route
        workflow.route_proposal("proposal-1", actor="system")
        
        # Submit for review (transitions to REVIEWING state)
        workflow.submit_for_review("proposal-1", "operator-1")
        
        # Validate (must happen after submitting for review, when state is REVIEWING)
        workflow.validate_proposal("proposal-1", actor="system")
        
        # Approve
        workflow.approve_proposal("proposal-1", "operator-1", notes="Approved")
        
        # Verify final state
        status = workflow.get_proposal_status("proposal-1")
        self.assertEqual(status["state"], "approved")
        self.assertEqual(status["review_status"], "approved")
    
    def test_rejected_workflow_lifecycle(self):
        """Test rejected workflow lifecycle: draft -> submitted -> reviewing -> rejected."""
        governance = ProposalGovernanceEngine()
        validation = ProposalValidationEngine()
        workflow = ProposalWorkflow(
            governance_engine=governance,
            validation_engine=validation,
        )
        
        node = MockNode("proposal-1")
        
        # Route
        workflow.route_proposal("proposal-1", actor="system")
        
        # Submit for review (transitions to REVIEWING state)
        workflow.submit_for_review("proposal-1", "operator-1")
        
        # Validate (must happen after submitting for review)
        workflow.validate_proposal("proposal-1", actor="system")
        
        # Reject
        workflow.reject_proposal("proposal-1", "operator-1", notes="Rejected")
        
        # Verify final state
        status = workflow.get_proposal_status("proposal-1")
        self.assertEqual(status["state"], "rejected")
        self.assertEqual(status["review_status"], "rejected")


class TestProposalWorkflowBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for Proposal Workflow."""
    
    def test_old_state_serialization(self):
        """Test old state serialization format still works."""
        # Old format (missing review_status)
        old_data = {
            "proposal_id": "proposal-1",
            "current_state": "reviewing",
            "validation_status": "pending",
            "created_at": 1234567890,
            "updated_at": 1234567900,
        }
        
        restored = ProposalWorkflowState.from_dict(old_data)
        self.assertEqual(restored.proposal_id, "proposal-1")
        self.assertEqual(restored.current_state, WorkflowState.REVIEWING)
        self.assertEqual(restored.review_status, "pending")  # Default value


class TestProposalWorkflowBoundaryConditions(unittest.TestCase):
    """Boundary condition tests for Proposal Workflow."""
    
    def test_submit_without_route_fails(self):
        """Test submitting for review without routing fails."""
        workflow = ProposalWorkflow()
        
        with self.assertRaises(ValueError):
            workflow.submit_for_review("proposal-1", "operator-1")
    
    def test_approve_without_review_fails(self):
        """Test approving without submitting for review fails."""
        workflow = ProposalWorkflow()
        workflow.route_proposal("proposal-1", actor="system")
        
        with self.assertRaises(ValueError):
            workflow.approve_proposal("proposal-1", "operator-1")
    
    def test_auto_application_blocked(self):
        """Test that auto-application is always blocked by policy."""
        workflow = ProposalWorkflow()
        
        can_apply = workflow.can_apply("proposal-1")
        self.assertEqual(can_apply, False)


if __name__ == "__main__":
    unittest.main()
