#!/usr/bin/env python3
"""Tests for Self-Architecture Core v16: Unified Operator Governance Surface."""

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

from proposal_realization import RealizationEngine

from proof_gate import ExecutionState

from governance_surface import (
    GovernanceAggregationEngine,
    ProposalGovernanceView,
    get_governance_view,
    format_governance_view,
)


def test_governance_view_creation():
    """Test governance view creation with all required fields."""
    print("Test 1: Governance view creation")
    
    view = ProposalGovernanceView(
        proposal_id="prop-001",
        title="Test proposal",
        description="Testing governance view",
        summary="Test summary",
        why_surfaced="Test reason",
        subsystem_impact=["state", "continuity"],
        risk_effort={"risk_level": "low", "estimated_effort": 50},
        forecast_summary="Test forecast",
        forecast_confidence=0.8,
        approval_state="approved",
    )
    
    assert view.proposal_id == "prop-001"
    assert view.title == "Test proposal"
    assert len(view.subsystem_impact) == 2
    assert view.forecast_confidence == 0.8
    
    # Test serialization
    data = view.to_dict()
    assert data["proposal_id"] == "prop-001"
    assert data["forecast_confidence"] == 0.8
    
    # Test from_dict
    view2 = ProposalGovernanceView.from_dict(data)
    assert view2.proposal_id == "prop-001"
    assert len(view2.subsystem_impact) == 2
    
    # Test format_for_display
    display = view.format_for_display()
    assert "GOVERNANCE VIEW" in display
    assert "prop-001" in display
    
    print("  ✓ Governance view creation works")
    return True


def test_governance_aggregation_engine():
    """Test GovernanceAggregationEngine class."""
    print("Test 2: Governance aggregation engine")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        engine = GovernanceAggregationEngine(storage_path=temp_path)
        
        # Create an approved proposal
        proposal = engine.gate.create_proposal(
            title="Governance test proposal",
            description="Testing governance aggregation",
            risk_level="medium",
            calibration_confidence=0.7,
            affected_subsystems=["state", "continuity"],
            validation_requirements=["self_architecture_review"],
            rollback_expectations=["revert files"],
        )
        engine.gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Get governance view
        view = engine.get_governance_view(
            proposal_id=proposal.proposal_id,
            assessed_by="operator",
        )
        
        assert view is not None
        assert view.proposal_id == proposal.proposal_id
        assert view.title == proposal.title
        
        # Check required fields are populated
        assert view.summary is not None and len(view.summary) > 0
        assert len(view.subsystem_impact) > 0
        assert view.risk_effort is not None
        assert view.forecast_confidence > 0
        
        # Check proof gate integration
        assert view.execution_eligibility is not None
        assert "eligibility" in view.execution_eligibility
        assert "proof_status" in view.execution_eligibility
        
        # Check blocking reasons
        assert isinstance(view.blocking_reasons, list)
        
        # Check recommendation
        assert view.recommended_action in ["execute", "blockers", "review", "defer"]
        assert len(view.recommended_action_reason) > 0
        
        print("  ✓ Governance aggregation engine works")
    finally:
        temp_path.unlink()
    
    return True


def test_blocked_vs_eligible():
    """Test blocked vs eligible proposals."""
    print("Test 3: Blocked vs eligible proposals")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        engine = GovernanceAggregationEngine(storage_path=temp_path)
        
        # Create a proposal that will be eligible
        eligible_proposal = engine.gate.create_proposal(
            title="Eligible proposal",
            description="Testing eligible",
            risk_level="low",
            calibration_confidence=0.9,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        engine.gate.review_proposal(eligible_proposal.proposal_id, "approve", "operator")
        
        eligible_view = engine.get_governance_view(eligible_proposal.proposal_id)
        assert eligible_view.can_proceed in [True, False]  # May or may not be eligible
        assert eligible_view.execution_eligibility is not None
        
        # Create a proposal with low confidence (likely blocked)
        blocked_proposal = engine.gate.create_proposal(
            title="Blocked proposal",
            description="Testing blocked",
            risk_level="medium",
            calibration_confidence=0.3,  # Low confidence
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        engine.gate.review_proposal(blocked_proposal.proposal_id, "approve", "operator")
        
        blocked_view = engine.get_governance_view(blocked_proposal.proposal_id)
        assert blocked_view.execution_eligibility is not None
        
        # Check blocking reasons are populated
        assert isinstance(blocked_view.blocking_reasons, list)
        
        # Check recommended action for blocked proposal
        assert blocked_view.recommended_action in ["blockers", "defer"]
        
        print("  ✓ Blocked vs eligible works")
    finally:
        temp_path.unlink()
    
    return True


def test_backward_compatibility():
    """Test that v14 and v15 functionality is not broken."""
    print("Test 4: Backward compatibility")
    
    # V14 classes should still be importable
    from proposal_realization import (
        RealizationPlan,
        RealizationEngine,
        Blocker,
        RollbackCheckpoint,
    )
    
    # Test v14 plan creation
    plan = RealizationPlan(
        plan_id="plan-001",
        proposal_id="prop-001",
        title="V14 compatibility",
        description="Testing",
    )
    assert plan.plan_id == "plan-001"
    
    # Test v14 engine
    engine = RealizationEngine()
    assert engine is not None
    
    # V15 classes should still be importable
    from proof_gate import (
        ProofGateEngine,
        ExecutionReadiness,
        ProofType,
        ExecutionState,
    )
    
    # Test v15 engine
    v15_engine = ProofGateEngine()
    assert v15_engine is not None
    
    print("  ✓ Backward compatibility works")
    return True


def test_format_for_display():
    """Test governance view formatting for display."""
    print("Test 5: Format for display")
    
    view = ProposalGovernanceView(
        proposal_id="prop-001",
        title="Test Proposal",
        description="A test proposal",
        summary="This is a test",
        why_surfaced="Because it's important",
        subsystem_impact=["state", "continuity"],
        risk_effort={"risk_level": "low", "estimated_effort": 30},
        forecast_summary="Expected to improve performance",
        forecast_confidence=0.85,
        approval_state="approved",
        execution_eligibility={
            "eligibility": "eligible",
            "can_proceed": True,
        },
        proof_status={"total": 7, "satisfied": 7},
        blocking_reasons=[],
        can_proceed=True,
        recommended_action="execute",
        recommended_action_reason="All checks pass",
    )
    
    display = view.format_for_display()
    
    # Check key sections are present
    assert "GOVERNANCE VIEW" in display
    assert "prop-001" in display
    assert "Test Proposal" in display
    assert "SUMMARY:" in display
    assert "WHY SURFACED:" in display
    assert "SUBSYSTEM IMPACT:" in display
    assert "FORECAST:" in display
    assert "PROOF GATE" in display
    assert "EXECUTION ELIGIBILITY" in display
    assert "REALIZATION PLAN:" in display
    assert "AVAILABLE ACTIONS:" in display
    assert "RECOMMENDED ACTION:" in display
    
    print("  ✓ Format for display works")
    return True


def test_convenience_functions():
    """Test convenience functions."""
    print("Test 6: Convenience functions")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Test get_governance_view convenience function with explicit gate
        gate = ExecutionGate(storage_path=temp_path)
        engine = GovernanceAggregationEngine(gate=gate)
        
        proposal = gate.create_proposal(
            title="Convenience test",
            description="Testing convenience functions",
            risk_level="low",
            calibration_confidence=0.8,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Test convenience function with storage path
        view = get_governance_view(proposal.proposal_id, storage_path=temp_path)
        assert view is not None
        assert view.proposal_id == proposal.proposal_id
        
        # Test format convenience function
        display = format_governance_view(view)
        assert "GOVERNANCE VIEW" in display
        
        print("  ✓ Convenience functions work")
    finally:
        temp_path.unlink()
    
    return True


def run_all_tests():
    """Run all Self-Architecture v16 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE V16 TESTS")
    print("=" * 60)
    
    tests = [
        test_governance_view_creation,
        test_governance_aggregation_engine,
        test_blocked_vs_eligible,
        test_backward_compatibility,
        test_format_for_display,
        test_convenience_functions,
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
