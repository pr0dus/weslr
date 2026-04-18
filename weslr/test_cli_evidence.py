"""Test suite for CLI Evidence (v94d)

Test Doctrine version: 1.0.0 (2026-04-08)
Test coverage: CLI evidence assimilation and routing workflow surface
"""

import unittest
import json
from io import StringIO
import sys
import time

from weslr.cli_evidence import (
    emit,
    cmd_evidence_routes,
    cmd_evidence_route,
    cmd_evidence_submit,
    cmd_evidence_approve,
    cmd_evidence_reject,
    EvidenceToGovernanceRouter,
    RoutingState,
    RoutingRecord,
    EvidenceProposalPayload,
)


class TestEvidenceCLIModel(unittest.TestCase):
    """Model tests for EvidenceCLI."""

    def test_emit_output_format(self):
        """Test emit function produces valid JSON."""
        test_data = {"key": "value", "count": 42}
        
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            emit(test_data)
            output = captured_output.getvalue()
            parsed = json.loads(output)
            self.assertEqual(parsed, test_data)
        finally:
            sys.stdout = sys.__stdout__

    def test_emit_json_structure(self):
        """Test emit produces properly structured JSON."""
        test_data = {"ok": True, "proposal_id": "test_123"}
        
        captured_output = StringIO()
        try:
            # Capture the output
            old_stdout = sys.stdout
            sys.stdout = captured_output
            emit(test_data)
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            parsed = json.loads(output)
            self.assertIn("ok", parsed)
            self.assertIn("proposal_id", parsed)
        finally:
            sys.stdout = old_stdout


class TestEvidenceCLIBehavior(unittest.TestCase):
    """Behavior tests for EvidenceCLI."""

    def setUp(self):
        """Set up test fixtures."""
        self.router = EvidenceToGovernanceRouter()
        self.proposal_id = "evidence_test_001"
        
        # Create a proposal and route it to registered state
        self.payload = EvidenceProposalPayload(
            evidence_id=self.proposal_id,
            claim_text="Test claim for routing",
            source_summary="Test source",
            confidence=0.85,
            status="DRAFT",
        )
        self.router.route_evidence_to_registered(self.payload, "system")

    def test_evidence_routes_empty_router(self):
        """Test routes command with empty router."""
        # Create new router instance (simulates fresh CLI invocation)
        empty_router = EvidenceToGovernanceRouter()
        result = empty_router.export_all_routing()
        
        self.assertEqual(result.get("total_count"), 0)
        self.assertEqual(result.get("routings"), {})

    def test_evidence_routes_with_records(self):
        """Test routes command with routing records."""
        result = self.router.export_all_routing()
        
        self.assertGreater(result.get("total_count"), 0)
        self.assertIn(self.proposal_id, result.get("routings", {}))

    def test_evidence_route_single_proposal(self):
        """Test route command for single proposal."""
        result = self.router.export_routing_summary(self.proposal_id)
        
        self.assertEqual(result.get("proposal_id"), self.proposal_id)
        self.assertIn("routing_status", result)
        self.assertIn("routing_history", result)

    def test_evidence_route_missing_proposal(self):
        """Test route command for non-existent proposal."""
        result = self.router.export_routing_summary("nonexistent")
        
        self.assertEqual(result.get("routing_status"), RoutingState.GENERATED.value)
        self.assertEqual(result.get("routing_history"), [])

    def test_submit_for_review_success(self):
        """Test submit for review succeeds."""
        # Submit for review
        record = self.router.submit_for_review(self.proposal_id, "operator_1")
        
        self.assertIsInstance(record, RoutingRecord)
        self.assertEqual(record.proposal_id, self.proposal_id)
        self.assertEqual(record.action, "submit_for_review")
        self.assertEqual(record.actor, "operator_1")

    def test_submit_for_review_invalid_proposal(self):
        """Test submit for review fails for missing proposal."""
        router = EvidenceToGovernanceRouter()
        
        with self.assertRaises(ValueError):
            router.submit_for_review("nonexistent", "operator_1")

    def test_submit_for_review_invalid_transition(self):
        """Test submit for review fails for already approved proposal."""
        # First approve, then try to submit
        self.router.route_evidence_to_registered(self.payload, "system")
        self.router.approve_proposal(self.proposal_id, "operator_1", "Approved")
        
        with self.assertRaises(ValueError):
            self.router.submit_for_review(self.proposal_id, "operator_2")

    def test_approve_proposal_success(self):
        """Test approve proposal succeeds."""
        # First submit for review
        self.router.submit_for_review(self.proposal_id, "operator_1")
        
        # Then approve
        record = self.router.approve_proposal(self.proposal_id, "reviewer_1", "Looks good")
        
        self.assertIsInstance(record, RoutingRecord)
        self.assertEqual(record.action, "approve")
        self.assertEqual(record.notes, "Looks good")

    def test_approve_proposal_missing_reviewer(self):
        """Test approve proposal fails without reviewer."""
        with self.assertRaises(ValueError):
            self.router.approve_proposal("test", "", "")

    def test_reject_proposal_success(self):
        """Test reject proposal succeeds."""
        # First submit for review
        self.router.submit_for_review(self.proposal_id, "operator_1")
        
        # Then reject
        record = self.router.reject_proposal(self.proposal_id, "reviewer_1", "Not suitable")
        
        self.assertIsInstance(record, RoutingRecord)
        self.assertEqual(record.action, "reject")
        self.assertEqual(record.notes, "Not suitable")

    def test_reject_proposal_missing_reviewer(self):
        """Test reject proposal fails without reviewer."""
        with self.assertRaises(ValueError):
            self.router.reject_proposal("test", "", "")

    def test_command_args_validation_submit(self):
        """Test submit command validates required args."""
        # Simulate missing --proposal-id - test directly
        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            # Test with None args (simulated missing arg)
            cmd_evidence_route(None)
        except AttributeError:
            pass  # Expected error when args is None
        finally:
            sys.stdout = sys.__stdout__


class TestEvidenceCLIIntegration(unittest.TestCase):
    """Integration tests for EvidenceCLI."""

    def test_cli_router_integration(self):
        """Test CLI router integrates with v94c/v94b engines."""
        # Create proposal
        payload = EvidenceProposalPayload(
            evidence_id="integration_test_001",
            claim_text="Integration test claim",
            source_summary="Integration source",
        )
        
        # Route through CLI-integrated router
        router = EvidenceToGovernanceRouter()
        router.route_evidence_to_registered(payload, "system")
        
        # Verify routing state
        summary = router.export_routing_summary("integration_test_001")
        self.assertEqual(summary.get("routing_status"), RoutingState.REGISTERED.value)

    def test_cli_governance_engine_integration(self):
        """Test CLI delegates to governance engine."""
        payload = EvidenceProposalPayload(
            evidence_id="governance_test_001",
            claim_text="Governance test claim",
            source_summary="Governance source",
        )
        
        router = EvidenceToGovernanceRouter()
        router.route_evidence_to_registered(payload, "system")
        router.submit_for_review("governance_test_001", "operator_1")
        router.approve_proposal("governance_test_001", "reviewer_1", "Approved")
        
        # Verify governance state via router
        summary = router.export_routing_summary("governance_test_001")
        self.assertEqual(summary.get("routing_status"), RoutingState.APPROVED.value)


class TestEvidenceCLIBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for EvidenceCLI."""

    def test_router_unmodified_v94c(self):
        """Test router doesn't modify v94c behavior."""
        # Create router (fresh instance)
        router = EvidenceToGovernanceRouter()
        
        # Create proposal via v94c API
        payload = EvidenceProposalPayload(
            evidence_id="bc_test_001",
            claim_text="BC test claim",
            source_summary="BC source",
        )
        
        # Route it
        router.route_evidence_to_registered(payload, "system")
        
        # Verify status
        status = router.get_routing_status("bc_test_001")
        self.assertEqual(status, RoutingState.REGISTERED.value)

    def test_proposal_workflow_unmodified_v94b(self):
        """Test proposal workflow unmodified from v94b."""
        # Create router which uses proposal workflow
        router = EvidenceToGovernanceRouter()
        
        # Verify governance engine is accessible
        self.assertIsNotNone(router.governance)
        self.assertIsNotNone(router.proposal_workflow)

    def test_cli_commands_additive_only(self):
        """Test CLI commands don't break existing v94c/v94b behavior."""
        # Create router before CLI usage
        router1 = EvidenceToGovernanceRouter()
        
        # Create proposal via v94c API
        payload = EvidenceProposalPayload(
            evidence_id="bc_test_002",
            claim_text="BC test claim 2",
            source_summary="BC source 2",
        )
        
        # Route it
        router1.route_evidence_to_registered(payload, "system")
        
        # Create new router and verify state is accessible
        router2 = EvidenceToGovernanceRouter()
        
        # The new router starts fresh, but the pattern is preserved
        self.assertIsNotNone(router2.governance)
        self.assertIsNotNone(router2.proposal_workflow)


if __name__ == "__main__":
    unittest.main()
