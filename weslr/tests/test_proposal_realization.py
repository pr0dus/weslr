#!/usr/bin/env python3
"""Tests for Self-Architecture Core v14: Proposal Realization / Safe Execution Planning Layer."""

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

from proposal_realization import (
    RealizationPlan,
    RealizationEngine,
    Blocker,
    RollbackCheckpoint,
    RealizationPhase,
    ReadinessState,
    BlockerType,
    build_realization_plan,
    approve_realization_plan,
    get_realization_summary,
)


def test_realization_plan_creation():
    """Test realization plan creation with all required fields."""
    print("Test 1: Realization plan creation")
    
    plan = RealizationPlan(
        plan_id="plan-001",
        proposal_id="prop-001",
        title="Test Realization",
        description="A test realization plan",
        affected_subsystems=["state", "continuity"],
        impacted_modules=["state.py", "continuity.py"],
        phases=["preparation", "implementation", "validation"],
        current_phase=RealizationPhase.PREPARATION.value,
        validation_requirements=["self_architecture_review", "impact_analysis"],
        rollback_expectations=["revert files", "restore config"],
        prepared_by="operator",
    )
    
    assert plan.plan_id == "plan-001"
    assert plan.proposal_id == "prop-001"
    assert "state" in plan.affected_subsystems
    assert "state.py" in plan.impacted_modules
    assert "preparation" in plan.phases
    
    # Test serialization
    data = plan.to_dict()
    assert data["plan_id"] == "plan-001"
    assert data["affected_subsystems"] == ["state", "continuity"]
    
    # Test from_dict
    plan2 = RealizationPlan.from_dict(data)
    assert plan2.plan_id == "plan-001"
    assert "state" in plan2.affected_subsystems
    
    print("  ✓ Realization plan creation works")
    return True


def test_blocker_management():
    """Test blocker creation and resolution."""
    print("Test 2: Blocker management")
    
    plan = RealizationPlan(
        plan_id="plan-002",
        proposal_id="prop-002",
        title="Blocker test",
        description="Testing blockers",
    )
    
    # Add a blocker
    blocker = plan.add_blocker(
        blocker_type=BlockerType.RISK.value,
        description="High risk change",
        severity="high",
    )
    
    assert len(plan.blockers) == 1
    assert plan.blocker_count == 1
    assert plan.blocker_count_by_severity.get("high", 0) == 1
    
    # Update readiness
    plan.update_readiness()
    assert plan.readiness_state == ReadinessState.READY_WITH_BLOCKERS.value
    
    # Resolve the blocker
    resolved = plan.resolve_blocker(blocker.blocker_id)
    assert resolved is True
    assert plan.blocker_count_by_severity.get("high", 0) == 1  # Still counted until reassessment
    
    # Re-check readiness
    plan.update_readiness()
    assert plan.blockers[0]["resolved"] is True
    
    print("  ✓ Blocker management works")
    return True


def test_rollback_checkpoints():
    """Test rollback checkpoint creation and verification."""
    print("Test 3: Rollback checkpoints")
    
    plan = RealizationPlan(
        plan_id="plan-003",
        proposal_id="prop-003",
        title="Checkpoint test",
        description="Testing rollback",
        affected_subsystems=["state"],
        rollback_expectations=["revert files"],
    )
    
    # Add checkpoints
    checkpoint1 = plan.add_checkpoint(
        description="Pre-change checkpoint",
        trigger="before",
        file_patterns=["state.py"],
    )
    
    checkpoint2 = plan.add_checkpoint(
        description="Post-change checkpoint",
        trigger="after",
        file_patterns=["state.py", "continuity.py"],
    )
    
    assert len(plan.rollback_checkpoints) == 2
    assert plan.rollback_checkpoints[0]["description"] == "Pre-change checkpoint"
    assert plan.rollback_checkpoints[0]["trigger"] == "before"
    assert plan.rollback_checkpoints[1]["trigger"] == "after"
    
    # Verify checkpoint
    verified = plan.verify_checkpoint(checkpoint1.checkpoint_id)
    assert verified is True
    assert plan.rollback_checkpoints[0]["verified"] is True
    assert plan.rollback_checkpoints[0]["verified_at"] is not None
    
    print("  ✓ Rollback checkpoints work")
    return True


def test_phases_and_approval():
    """Test implementation phases and approval."""
    print("Test 4: Phases and approval")
    
    plan = RealizationPlan(
        plan_id="plan-004",
        proposal_id="prop-004",
        title="Phases test",
        description="Testing phases",
    )
    
    # Add phases
    plan.add_phase("preparation", "Setup phase")
    plan.add_phase("implementation", "Build phase")
    plan.add_phase("validation", "Test phase")
    plan.add_phase("monitoring", "Watch phase")
    
    assert len(plan.phases) == 4
    assert len(plan.approval_points) == 4
    
    # Approve a phase
    approved = plan.approve_phase("implementation", "operator")
    assert approved is True
    assert plan.approval_points[1]["approved"] is True
    assert plan.approval_points[1]["approved_by"] == "operator"
    
    # Try to approve non-existent phase
    not_approved = plan.approve_phase("nonexistent", "operator")
    assert not_approved is False
    
    print("  ✓ Phases and approval work")
    return True


def test_readiness_assessment():
    """Test readiness state classification."""
    print("Test 5: Readiness assessment")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = RealizationEngine(execution_gate=gate)
        
        # Create an approved proposal
        proposal = gate.create_proposal(
            title="Ready proposal",
            description="Testing",
            risk_level="low",
            calibration_confidence=0.9,
            affected_subsystems=["state"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Build realization plan
        plan = engine.build_realization_plan(proposal.proposal_id)
        
        assert plan is not None
        assert plan.readiness_state in [ReadinessState.READY.value, ReadinessState.READY_WITH_BLOCKERS.value]
        
        # Check readiness status
        status = plan.get_readiness_status()
        assert "readiness_state" in status
        assert "readiness_reason" in status
        assert "can_proceed" in status
        
        print("  ✓ Readiness assessment works")
    finally:
        temp_path.unlink()
    
    return True


def test_realization_engine():
    """Test RealizationEngine class."""
    print("Test 6: RealizationEngine class")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = RealizationEngine(execution_gate=gate)
        
        # Create an approved proposal
        proposal = gate.create_proposal(
            title="Engine test",
            description="Testing engine",
            risk_level="medium",
            calibration_confidence=0.7,
            affected_subsystems=["state", "continuity"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Build plan
        plan = engine.build_realization_plan(proposal.proposal_id)
        
        assert plan is not None
        assert plan.plan_id.startswith("plan-")
        assert plan.proposal_id == proposal.proposal_id
        assert "state" in plan.affected_subsystems
        assert "continuity" in plan.affected_subsystems
        assert len(plan.impacted_modules) > 0
        assert len(plan.rollback_checkpoints) > 0
        
        # Generate summary
        summary = engine.generate_realization_summary(plan)
        assert "plan_id" in summary
        assert "readiness" in summary
        assert "impact" in summary
        assert "phases" in summary
        assert "can_proceed" in summary
        
        # Check approval
        approval = engine.approve_plan(plan.plan_id, "operator")
        assert approval is not None
        assert approval["success"] is True
        assert approval["approved_by"] == "operator"
        
        print("  ✓ RealizationEngine class works")
    finally:
        temp_path.unlink()
    
    return True


def test_blocker_types():
    """Test different blocker types."""
    print("Test 7: Blocker types")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = RealizationEngine(execution_gate=gate)
        
        # Create proposal with high risk
        proposal = gate.create_proposal(
            title="High risk test",
            description="Testing high risk",
            risk_level="high",
            calibration_confidence=0.3,
            estimated_effort=90,
            forecast_summary=None,
            affected_subsystems=["state", "continuity", "capability_discovery", "file_ingestion"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Build plan and check blockers
        plan = engine.build_realization_plan(proposal.proposal_id)
        
        assert plan is not None
        assert plan.blocker_count > 0
        
        # Check blocker types
        blocker_types = [b["blocker_type"] for b in plan.blockers]
        assert BlockerType.RISK.value in blocker_types
        assert BlockerType.RESOURCE.value in blocker_types
        assert BlockerType.VALIDATION.value in blocker_types
        assert BlockerType.CONFIGURATION.value in blocker_types
        
        print("  ✓ Blocker types work")
    finally:
        temp_path.unlink()
    
    return True


def test_impact_mapping():
    """Test subsystem to module/file mapping."""
    print("Test 8: Impact mapping")
    
    engine = RealizationEngine()
    
    # Test known subsystems
    modules = engine._map_subsystems_to_modules(["state", "continuity"])
    assert "state.py" in modules
    assert "continuity.py" in modules
    
    # Test unknown subsystems
    modules2 = engine._map_subsystems_to_modules(["unknown_subsystem"])
    assert "unknown_subsystem.py" in modules2
    
    # Test file mapping
    files = engine._map_subsystems_to_files(["state"])
    assert "state.py" in files
    
    print("  ✓ Impact mapping works")
    return True


def test_backward_compatibility():
    """Test that v13 functionality is not broken."""
    print("Test 9: Backward compatibility")
    
    # V13 classes should still be importable
    from operator_proposal_review import OperatorProposalReview
    
    # V12 classes should still be importable
    from change_proposals import ChangeProposal, ExecutionGate, ProposalState
    
    # Test v12 proposal still works
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        proposal = gate.create_proposal(
            title="V12 compatibility",
            description="Testing",
        )
        assert proposal.proposal_id.startswith("prop-")
        
        # Test v13 review
        review = OperatorProposalReview(gate=gate)
        proposals = review.list_proposals()
        assert len(proposals) >= 1
        
        print("  ✓ Backward compatibility works")
    finally:
        temp_path.unlink()
    
    return True


def run_all_tests():
    """Run all Self-Architecture v14 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE V14 TESTS")
    print("=" * 60)
    
    tests = [
        test_realization_plan_creation,
        test_blocker_management,
        test_rollback_checkpoints,
        test_phases_and_approval,
        test_readiness_assessment,
        test_realization_engine,
        test_blocker_types,
        test_impact_mapping,
        test_backward_compatibility,
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
