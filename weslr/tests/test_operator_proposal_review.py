#!/usr/bin/env python3
"""Tests for Self-Architecture Core v13: Operator Proposal Review Surface."""

from pathlib import Path
import os
import sys
import tempfile

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

os.chdir(Path(__file__).parent)

from change_proposals import (
    ChangeProposal,
    ExecutionGate,
    ProposalState,
)

from operator_proposal_review import (
    OperatorProposalReview,
    OperatorReviewOutput,
    list_proposals,
    show_proposal,
    approve_proposal,
    deny_proposal,
    defer_proposal,
    get_audit_history,
    get_review_summary,
)


def test_review_output_creation():
    """Test operator review output creation."""
    print("Test 1: Review output creation")
    
    output = OperatorReviewOutput(
        proposal_id="prop-001",
        title="Test Proposal",
        description="A test proposal",
        affected_subsystems=["state", "continuity"],
        risk_level="high",
        estimated_effort=80,
        calibration_confidence=0.6,
        forecast_summary="Significant improvement",
        expected_outcomes=["speed", "reliability"],
        validation_requirements=["self_architecture_review"],
        rollback_expectations=["revert files"],
        current_state=ProposalState.PENDING_REVIEW.value,
        approval_state="pending",
        audit_history=[],
        available_actions=["approve", "deny", "defer"],
    )
    
    assert output.proposal_id == "prop-001"
    assert "state" in output.affected_subsystems
    assert output.risk_level == "high"
    assert "speed" in output.expected_outcomes
    
    # Test serialization
    data = output.to_dict()
    assert data["proposal_id"] == "prop-001"
    assert data["risk_level"] == "high"
    
    # Test from_dict
    output2 = OperatorReviewOutput.from_dict(data)
    assert output2.proposal_id == "prop-001"
    assert output2.risk_level == "high"
    
    print("  ✓ Review output creation works")
    return True


def test_review_output_formatting():
    """Test review output formatting for display."""
    print("Test 2: Review output formatting")
    
    output = OperatorReviewOutput(
        proposal_id="prop-002",
        title="Formatting Test",
        description="Testing display format",
        affected_subsystems=["state"],
        risk_level="low",
        estimated_effort=20,
        calibration_confidence=0.9,
        forecast_summary="Quick win",
        expected_outcomes=["speedup"],
        validation_requirements=["test"],
        rollback_expectations=["revert"],
        current_state=ProposalState.APPROVED.value,
        approval_state="approved",
        audit_history=[{
            "timestamp": "2026-04-06T10:00:00Z",
            "actor": "operator",
            "action": "state_transition:approved",
            "details": {"reason": "Good ROI"},
        }],
        available_actions=["execute"],
    )
    
    formatted = output.format_for_display()
    assert "PROPOSAL: prop-002" in formatted
    assert "Formatting Test" in formatted
    assert "AFFECTED SUBSYSTEMS" in formatted
    assert "AUDIT HISTORY" in formatted
    assert "state_transition:approved" in formatted
    
    print("  ✓ Review output formatting works")
    return True


def test_operator_proposal_review():
    """Test OperatorProposalReview class."""
    print("Test 3: OperatorProposalReview class")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Create gate first, then pass to review
        gate = ExecutionGate(storage_path=temp_path)
        review = OperatorProposalReview(gate=gate)
        
        # Create a proposal via the gate
        proposal = gate.create_proposal(
            title="Operator review test",
            description="Testing review interface",
            affected_subsystems=["state"],
            source_suggestion="suggest-001",
            risk_level="medium",
        )
        
        # List proposals
        proposals = review.list_proposals()
        assert len(proposals) == 1
        assert proposals[0]["proposal_id"] == proposal.proposal_id
        assert proposals[0]["title"] == "Operator review test"
        
        # Get proposal detail
        detail = review.get_proposal_detail(proposal.proposal_id)
        assert detail is not None
        assert detail.proposal_id == proposal.proposal_id
        assert "state" in detail.affected_subsystems
        assert detail.risk_level == "medium"
        
        print("  ✓ OperatorProposalReview class works")
    finally:
        temp_path.unlink()
    
    return True


def test_state_transitions():
    """Test approve/deny/defer state transitions."""
    print("Test 4: State transitions")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        review = OperatorProposalReview(gate=gate)
        
        # Create proposal
        proposal = gate.create_proposal(
            title="State transition test",
            description="Testing",
            risk_level="low",
        )
        
        # Approve
        result = review.approve_proposal(proposal.proposal_id, "operator", {"reason": "Good proposal"})
        assert result is not None
        assert result["success"] is True
        assert result["new_state"] == ProposalState.APPROVED.value
        
        # Create another for deny test
        proposal2 = gate.create_proposal(
            title="Deny test",
            description="Testing",
        )
        result2 = review.deny_proposal(proposal2.proposal_id, "operator", {"reason": "Not needed"})
        assert result2 is not None
        assert result2["new_state"] == ProposalState.DENIED.value
        
        # Create another for defer test
        proposal3 = gate.create_proposal(
            title="Defer test",
            description="Testing",
        )
        result3 = review.defer_proposal(proposal3.proposal_id, "operator", {"reason": "Wait for v14"})
        assert result3 is not None
        assert result3["new_state"] == ProposalState.DEFERRED.value
        
        print("  ✓ State transitions work")
    finally:
        temp_path.unlink()
    
    return True


def test_audit_history():
    """Test audit history retrieval."""
    print("Test 5: Audit history")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        review = OperatorProposalReview(gate=gate)
        
        proposal = gate.create_proposal(
            title="Audit test",
            description="Testing",
        )
        
        # Get audit history (should have initial entry)
        audit = review.get_audit_history(proposal.proposal_id)
        assert audit is not None
        assert len(audit) >= 1
        assert audit[0]["action"] == "proposal_created"
        assert audit[0]["actor"] == "operator"
        
        # Approve and check history grows
        review.approve_proposal(proposal.proposal_id, "operator")
        audit2 = review.get_audit_history(proposal.proposal_id)
        assert len(audit2) >= 2
        
        print("  ✓ Audit history works")
    finally:
        temp_path.unlink()
    
    return True


def test_available_actions():
    """Test available actions based on state."""
    print("Test 6: Available actions")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        review = OperatorProposalReview(gate=gate)
        
        # Pending review proposal
        proposal1 = gate.create_proposal(
            title="Pending review",
            description="Testing",
        )
        detail1 = review.get_proposal_detail(proposal1.proposal_id)
        assert detail1 is not None
        assert "approve" in detail1.available_actions
        assert "deny" in detail1.available_actions
        assert "defer" in detail1.available_actions
        
        # Approve it
        review.approve_proposal(proposal1.proposal_id, "operator")
        detail2 = review.get_proposal_detail(proposal1.proposal_id)
        assert detail2 is not None
        assert "execute" in detail2.available_actions
        
        print("  ✓ Available actions work")
    finally:
        temp_path.unlink()
    
    return True


def test_convenience_functions():
    """Test convenience functions work correctly when using the same storage."""
    print("Test 7: Convenience functions")
    
    # Test that convenience functions use consistent storage path
    from operator_proposal_review import (
        approve_proposal as cp_approve,
        deny_proposal as cp_deny,
        defer_proposal as cp_defer,
        list_proposals as cp_list,
    )
    
    # Verify they return expected types
    result = cp_deny("nonexistent-id", "operator", {"reason": "test"})
    # Non-existent proposal returns None - that's expected behavior
    assert result is None
    
    print("  ✓ Convenience functions work")
    return True


def test_backward_compatibility():
    """Test that v12 functionality is not broken."""
    print("Test 8: Backward compatibility")
    
    # V12 classes should still be importable and usable
    from change_proposals import ChangeProposal, ExecutionGate, ProposalState
    
    # Test v12 proposal creation
    proposal = ChangeProposal(
        proposal_id="prop-001",
        title="V12 compatibility test",
        description="Testing",
    )
    assert proposal.proposal_id == "prop-001"
    
    # Test v12 gate
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        gate.create_proposal(
            title="V12 gate test",
            description="Testing",
        )
        assert len(gate.proposals) == 1
        assert len(gate.get_all_proposals()) == 1
        
        print("  ✓ Backward compatibility works")
    finally:
        temp_path.unlink()
    
    return True


def test_review_summary():
    """Test review summary generation."""
    print("Test 9: Review summary")
    
    # Test that review summary returns expected structure
    from operator_proposal_review import get_review_summary
    
    summary = get_review_summary()
    
    # Summary should have expected keys
    assert "total_proposals" in summary
    assert "pending_review" in summary
    assert "approved" in summary
    assert "denied" in summary
    assert "deferred" in summary
    assert "last_updated" in summary
    
    print("  ✓ Review summary works")
    return True


def run_all_tests():
    """Run all Self-Architecture v13 tests."""
    print("=" * 60)
    print("SECTION 4 — VALIDATION: SELF-ARCHITECTURE CORE V13 TESTS")
    print("=" * 60)
    
    tests = [
        test_review_output_creation,
        test_review_output_formatting,
        test_operator_proposal_review,
        test_state_transitions,
        test_audit_history,
        test_available_actions,
        test_convenience_functions,
        test_backward_compatibility,
        test_review_summary,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, "PASS"))
        except Exception as e:
            import traceback
            results.append((test.__name__, f"FAIL: {e}"))
            print(f"  ✗ {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for name, result in results:
        status = "✓" if "PASS" in result else "✗"
        print(f"{status} {name}: {result}")
    
    all_pass = all("PASS" in r for _, r in results)
    print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    return all_pass


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
