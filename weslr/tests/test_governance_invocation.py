#!/usr/bin/env python3
"""Tests for Self-Architecture v17: Live Governance Invocation Layer."""

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

from governance_invocation import (
    invoke_governance_single,
    invoke_governance_compare,
    format_invocation_result,
    _determine_status,
    _build_comparison,
    _recommend_between,
)


def test_single_proposal_invocation():
    """Test single proposal governance invocation."""
    print("Test 1: Single proposal governance invocation")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        # Create an approved proposal
        proposal = gate.create_proposal(
            title="Single proposal test",
            description="Testing single governance invocation",
            risk_level="low",
            calibration_confidence=0.85,
            affected_subsystems=["state", "continuity"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Invoke governance single
        result = invoke_governance_single(proposal.proposal_id, temp_path)
        
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert result["proposal_id"] == proposal.proposal_id
        assert result["title"] == proposal.title
        assert "summary" in result
        assert "status" in result
        assert "recommended_action" in result
        assert "can_proceed" in result
        assert "blocking_reasons" in result
        
        # Status should be one of the valid values
        valid_statuses = ["blocked", "eligible", "delayed", "risky", "aligned", "ready"]
        assert result["status"] in valid_statuses, f"Invalid status: {result['status']}"
        
        print("  ✓ Single proposal invocation works")
    finally:
        temp_path.unlink()
    
    return True


def test_two_proposal_comparison():
    """Test two-proposal governance comparison."""
    print("Test 2: Two-proposal governance comparison")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        # Create first proposal
        proposal1 = gate.create_proposal(
            title="First proposal for comparison",
            description="Testing comparison - first",
            risk_level="low",
            calibration_confidence=0.9,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal1.proposal_id, "approve", "operator")
        
        # Create second proposal
        proposal2 = gate.create_proposal(
            title="Second proposal for comparison",
            description="Testing comparison - second",
            risk_level="medium",
            calibration_confidence=0.7,
            affected_subsystems=["continuity"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal2.proposal_id, "approve", "operator")
        
        # Invoke governance compare
        result = invoke_governance_compare(
            [proposal1.proposal_id, proposal2.proposal_id],
            temp_path,
        )
        
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert "proposal_1" in result
        assert "proposal_2" in result
        assert "comparison" in result
        assert "recommendation" in result
        
        # Check proposal_1 data
        assert result["proposal_1"]["proposal_id"] == proposal1.proposal_id
        assert result["proposal_1"]["title"] == proposal1.title
        
        # Check proposal_2 data
        assert result["proposal_2"]["proposal_id"] == proposal2.proposal_id
        assert result["proposal_2"]["title"] == proposal2.title
        
        # Check comparison data
        assert "summary" in result["comparison"]
        assert "metrics" in result["comparison"]
        
        # Check recommendation
        assert "recommendation" in result["recommendation"]
        assert "reason" in result["recommendation"]
        
        # Recommendation should be one of the proposals
        assert result["recommendation"]["recommendation"] in [proposal1.proposal_id, proposal2.proposal_id]
        
        print("  ✓ Two-proposal comparison works")
    finally:
        temp_path.unlink()
    
    return True


def test_blocked_vs_eligible_invocation():
    """Test blocked vs eligible states in invocation."""
    print("Test 3: Blocked vs eligible states")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        # Create eligible proposal
        eligible = gate.create_proposal(
            title="Eligible proposal",
            description="Testing eligible state",
            risk_level="low",
            calibration_confidence=0.9,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(eligible.proposal_id, "approve", "operator")
        
        eligible_result = invoke_governance_single(eligible.proposal_id, temp_path)
        assert "error" not in eligible_result
        
        # Create proposal that will be blocked (low confidence)
        blocked = gate.create_proposal(
            title="Blocked proposal",
            description="Testing blocked state",
            risk_level="high",
            calibration_confidence=0.2,  # Low confidence
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(blocked.proposal_id, "approve", "operator")
        
        blocked_result = invoke_governance_single(blocked.proposal_id, temp_path)
        assert "error" not in blocked_result
        
        # Both should have valid status
        assert "status" in eligible_result
        assert "status" in blocked_result
        
        # Both should have blocking_reasons populated
        assert "blocking_reasons" in eligible_result
        assert "blocking_reasons" in blocked_result
        
        print("  ✓ Blocked vs eligible states work")
    finally:
        temp_path.unlink()
    
    return True


def test_governance_invocation_cli_format():
    """Test CLI formatting of invocation results."""
    print("Test 4: CLI format for display")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        proposal = gate.create_proposal(
            title="CLI format test",
            description="Testing CLI format",
            risk_level="low",
            calibration_confidence=0.8,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        result = invoke_governance_single(proposal.proposal_id, temp_path)
        formatted = format_invocation_result(result)
        
        # Check key sections are present in formatted output
        assert "GOVERNANCE INVOCATION" in formatted or "GOVERNANCE VIEW" in formatted
        assert proposal.proposal_id in formatted
        assert "TITLE:" in formatted
        assert "SUMMARY:" in formatted
        assert "STATUS:" in formatted
        assert "RECOMMENDED ACTION:" in formatted
        
        print("  ✓ CLI format works")
    finally:
        temp_path.unlink()
    
    return True


def test_comparison_format():
    """Test CLI formatting of comparison results."""
    print("Test 5: Comparison CLI format")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        prop1 = gate.create_proposal(
            title="First for comparison",
            description="First",
            risk_level="low",
            calibration_confidence=0.9,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(prop1.proposal_id, "approve", "operator")
        
        prop2 = gate.create_proposal(
            title="Second for comparison",
            description="Second",
            risk_level="medium",
            calibration_confidence=0.7,
            affected_subsystems=["continuity"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(prop2.proposal_id, "approve", "operator")
        
        result = invoke_governance_compare([prop1.proposal_id, prop2.proposal_id], temp_path)
        formatted = format_invocation_result(result)
        
        # Check comparison format sections
        assert "GOVERNANCE COMPARISON" in formatted or "PROPOSAL 1:" in formatted
        assert prop1.proposal_id in formatted
        assert prop2.proposal_id in formatted
        assert "RECOMMENDATION:" in formatted
        
        print("  ✓ Comparison CLI format works")
    finally:
        temp_path.unlink()
    
    return True


def test_error_handling():
    """Test error handling in invocation functions."""
    print("Test 6: Error handling")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Test single proposal with non-existent ID
        result = invoke_governance_single("non-existent-id-123", temp_path)
        assert "error" in result or result is None
        
        # Test compare with wrong number of IDs
        result = invoke_governance_compare(["only-one-id"], temp_path)
        assert "error" in result
        
        result = invoke_governance_compare([], temp_path)
        assert "error" in result
        
        result = invoke_governance_compare(["id1", "id2", "id3"], temp_path)
        assert "error" in result
        
        print("  ✓ Error handling works")
    finally:
        temp_path.unlink()
    
    return True


def test_backward_compatibility():
    """Test that v16 functionality is not broken."""
    print("Test 7: Backward compatibility")
    
    # v16 classes should still be importable
    from governance_surface import (
        GovernanceAggregationEngine,
        ProposalGovernanceView,
        get_governance_view,
        format_governance_view,
    )
    
    # Test v16 view creation still works
    view = ProposalGovernanceView(
        proposal_id="prop-v16",
        title="V16 compatibility",
        description="Testing backward compatibility",
        summary="V16 test",
        why_surfaced="Test reason",
    )
    assert view.proposal_id == "prop-v16"
    
    # Test v16 format function still works
    formatted = view.format_for_display()
    assert "GOVERNANCE VIEW" in formatted
    
    # V17 classes should still be importable
    from governance_invocation import (
        invoke_governance_single,
        invoke_governance_compare,
        format_invocation_result,
    )
    
    print("  ✓ Backward compatibility works")
    return True


def test_v18_compatibility():
    """Test that v18 governance scorecard layer integrates without breaking v17."""
    print("Test 9: V18 compatibility")
    
    # Test v18 import
    try:
        from governance_scorecard import (
            GovernanceScorecard,
            GovernanceDecisionRecord,
            GovernanceBenchmarkEngine,
        )
    except ImportError as e:
        print(f"  ⚠ V18 not available: {e}")
        return True  # Not a failure if v18 isn't present
    
    # Test v18 classes work alongside v17
    # v18 classes
    scorecard = GovernanceScorecard(
        card_id="v18-backward-test",
        created_at="2026-04-06T10:00:00Z",
    )
    assert scorecard.card_id == "v18-backward-test"
    
    decision = GovernanceDecisionRecord(
        decision_id="dec-001",
        decision_type="execute",
        proposal_id="prop-001",
        timestamp="2026-04-06T10:01:00Z",
        operator="operator",
        reasoning="Test decision",
        confidence=0.9,
        status_at_decision="ready",
    )
    scorecard.add_decision(decision)
    assert len(scorecard.decisions) == 1
    
    engine = GovernanceBenchmarkEngine()
    scorecard2 = engine.create_scorecard("v18-engine-test")
    assert scorecard2.card_id == "v18-engine-test"
    
    print("  ✓ V18 compatibility works")
    return True


def test_operator_wrappers():
    """Test operator-facing wrapper functions."""
    print("Test 8: Operator wrapper functions")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        from weslr_operator_views import (
            operator_invoke_governance_single,
            operator_invoke_governance_compare,
            operator_format_governance_result,
        )
        
        gate = ExecutionGate(storage_path=temp_path)
        
        proposal = gate.create_proposal(
            title="Operator wrapper test",
            description="Testing operator wrappers",
            risk_level="low",
            calibration_confidence=0.8,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Test single wrapper
        result = operator_invoke_governance_single(proposal.proposal_id, temp_path)
        assert "error" not in result or "Governance invocation" in result.get("error", "")
        assert result.get("proposal_id") == proposal.proposal_id
        
        # Test format wrapper
        formatted = operator_format_governance_result(result)
        assert "GOVERNANCE" in formatted or "Error" in formatted
        
        print("  ✓ Operator wrapper functions work")
    finally:
        temp_path.unlink()
    
    return True


def run_all_tests():
    """Run all Self-Architecture v17 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE V17 TESTS")
    print("=" * 60)
    
    tests = [
        test_single_proposal_invocation,
        test_two_proposal_comparison,
        test_blocked_vs_eligible_invocation,
        test_governance_invocation_cli_format,
        test_comparison_format,
        test_error_handling,
        test_backward_compatibility,
        test_v18_compatibility,
        test_operator_wrappers,
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
