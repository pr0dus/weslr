#!/usr/bin/env python3
"""Tests for Self-Architecture Core v15: Execution Readiness / Proof Gate."""

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

from proof_gate import (
    ProofGateEngine,
    ExecutionReadiness,
    ProofItem,
    ProofType,
    ProofStatus,
    ExecutionState,
    evaluate_readiness,
    get_execution_eligibility,
    explain_blocking_reasons,
)


def test_execution_readiness_creation():
    """Test execution readiness creation with all required fields."""
    print("Test 1: Execution readiness creation")
    
    readiness = ExecutionReadiness(
        plan_id="plan-001",
        proposal_id="prop-001",
        required_proofs=[ProofType.VALIDATION.value, ProofType.RISK_ASSESSMENT.value],
        satisfied_proofs=[ProofType.VALIDATION.value],
        missing_proofs=[ProofType.RISK_ASSESSMENT.value],
        validation_coverage=0.8,
        rollback_coverage=0.7,
        risk_bounded=True,
        assessed_by="operator",
    )
    
    assert readiness.plan_id == "plan-001"
    assert len(readiness.required_proofs) == 2
    assert len(readiness.satisfied_proofs) == 1
    assert len(readiness.missing_proofs) == 1
    assert readiness.validation_coverage == 0.8
    
    # Test serialization
    data = readiness.to_dict()
    assert data["plan_id"] == "plan-001"
    assert data["validation_coverage"] == 0.8
    
    # Test from_dict
    readiness2 = ExecutionReadiness.from_dict(data)
    assert readiness2.plan_id == "plan-001"
    assert len(readiness2.required_proofs) == 2
    
    print("  ✓ Execution readiness creation works")
    return True


def test_proof_item():
    """Test proof item creation and status management."""
    print("Test 2: Proof item")
    
    item = ProofItem(
        proof_id="proof-001",
        proof_type=ProofType.VALIDATION.value,
        description="Validation check",
    )
    
    assert item.proof_id == "proof-001"
    assert item.proof_type == ProofType.VALIDATION.value
    assert item.status == ProofStatus.NOT_REQUESTED.value
    
    # Mark satisfied
    item.mark_satisfied("operator", "test evidence")
    assert item.status == ProofStatus.SATISFIED.value
    assert item.satisfied_at is not None
    assert item.verified_by == "operator"
    assert item.evidence == "test evidence"
    
    # Test to_dict
    data = item.to_dict()
    assert data["proof_id"] == "proof-001"
    assert data["verified_by"] == "operator"
    
    # Mark failed
    item.mark_failed("operator")
    assert item.status == ProofStatus.FAILED.value
    assert item.failed_at is not None
    
    print("  ✓ Proof item works")
    return True


def test_proof_gate_engine():
    """Test ProofGateEngine class."""
    print("Test 3: ProofGateEngine class")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = ProofGateEngine(execution_gate=gate)
        
        # Create an approved proposal
        proposal = gate.create_proposal(
            title="Proof gate test",
            description="Testing proof gate",
            risk_level="medium",
            calibration_confidence=0.7,
            affected_subsystems=["state", "continuity"],
            validation_requirements=["self_architecture_review"],
            rollback_expectations=["revert files"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Evaluate readiness
        readiness = engine.evaluate_readiness(
            plan_id="plan-test",
            proposal_id=proposal.proposal_id,
            assessed_by="operator",
        )
        
        assert readiness is not None
        assert readiness.plan_id == "plan-test"
        assert readiness.proposal_id == proposal.proposal_id
        
        # Check required proofs exist
        assert len(readiness.required_proofs) > 0
        
        # Check state classification
        assert readiness.readiness_state in [
            ExecutionState.ELIGIBLE.value,
            ExecutionState.BLOCKED.value,
            ExecutionState.PENDING_PROOF.value,
        ]
        
        print("  ✓ ProofGateEngine class works")
    finally:
        temp_path.unlink()
    
    return True


def test_execution_eligibility():
    """Test execution eligibility determination."""
    print("Test 4: Execution eligibility")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = ProofGateEngine(execution_gate=gate)
        
        # Create an approved proposal with good metrics
        proposal = gate.create_proposal(
            title="Eligible proposal",
            description="Testing eligibility",
            risk_level="low",
            calibration_confidence=0.8,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Get eligibility
        eligibility = engine.get_execution_eligibility(
            plan_id="plan-test",
            proposal_id=proposal.proposal_id,
        )
        
        assert eligibility is not None
        assert "eligibility" in eligibility
        assert "proof_status" in eligibility
        assert "coverage" in eligibility
        assert "risk" in eligibility
        assert "can_proceed" in eligibility
        
        # Should be eligible or pending proof
        assert eligibility["eligibility"] in [ExecutionState.ELIGIBLE.value, ExecutionState.PENDING_PROOF.value]
        
        # Check proof status
        assert "total" in eligibility["proof_status"]
        assert "satisfied" in eligibility["proof_status"]
        assert eligibility["proof_status"]["total"] > 0
        
        # Check coverage
        assert "validation" in eligibility["coverage"]
        assert "rollback" in eligibility["coverage"]
        
        # Check risk
        assert "bounded" in eligibility["risk"]
        assert "max_severity" in eligibility["risk"]
        
        print("  ✓ Execution eligibility works")
    finally:
        temp_path.unlink()
    
    return True


def test_blocking_reasons():
    """Test blocking reasons identification."""
    print("Test 5: Blocking reasons")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = ProofGateEngine(execution_gate=gate)
        
        # Create an approved proposal with low confidence (should block)
        proposal = gate.create_proposal(
            title="Blocked proposal",
            description="Testing blocking",
            risk_level="medium",
            calibration_confidence=0.3,  # Low confidence
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Get blocking reasons
        explanation = engine.explain_blocking_reasons(
            plan_id="plan-blocked",
            proposal_id=proposal.proposal_id,
        )
        
        assert explanation is not None
        # Low confidence should be a blocking reason
        assert "confidence" in explanation.lower() or "proof" in explanation.lower()
        
        print("  ✓ Blocking reasons work")
    finally:
        temp_path.unlink()
    
    return True


def test_risk_bounded():
    """Test risk bounded/unbounded classification."""
    print("Test 6: Risk bounded")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = ProofGateEngine(execution_gate=gate)
        
        # Create proposal with high risk
        proposal = gate.create_proposal(
            title="High risk proposal",
            description="Testing high risk",
            risk_level="high",
            calibration_confidence=0.7,
            affected_subsystems=["state"],
            validation_requirements=["test"],
            rollback_expectations=["revert"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Get eligibility
        eligibility = engine.get_execution_eligibility(
            plan_id="plan-high-risk",
            proposal_id=proposal.proposal_id,
        )
        
        assert eligibility["risk"]["bounded"] is False
        assert eligibility["risk"]["max_severity"] == "high"
        
        # Should be blocked
        assert eligibility["eligibility"] == ExecutionState.BLOCKED.value
        assert "risk" in eligibility["readiness_reason"].lower()
        
        print("  ✓ Risk bounded works")
    finally:
        temp_path.unlink()
    
    return True


def test_coverage_metrics():
    """Test coverage metrics calculation."""
    print("Test 7: Coverage metrics")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        engine = ProofGateEngine(execution_gate=gate)
        
        # Create proposal with good metrics
        proposal = gate.create_proposal(
            title="Coverage test",
            description="Testing coverage",
            risk_level="low",
            calibration_confidence=0.9,
            affected_subsystems=["state", "continuity"],
            validation_requirements=["test1", "test2"],
            rollback_expectations=["revert1", "revert2"],
        )
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Get eligibility
        eligibility = engine.get_execution_eligibility(
            plan_id="plan-coverage",
            proposal_id=proposal.proposal_id,
        )
        
        # Check coverage is calculated
        assert "validation" in eligibility["coverage"]
        assert "rollback" in eligibility["coverage"]
        assert isinstance(eligibility["coverage"]["validation"], float)
        assert isinstance(eligibility["coverage"]["rollback"], float)
        
        # Coverage should be > 0
        assert eligibility["coverage"]["validation"] > 0
        assert eligibility["coverage"]["rollback"] > 0
        
        print("  ✓ Coverage metrics work")
    finally:
        temp_path.unlink()
    
    return True


def test_backward_compatibility():
    """Test that v14 functionality is not broken."""
    print("Test 8: Backward compatibility")
    
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
    
    print("  ✓ Backward compatibility works")
    return True


def run_all_tests():
    """Run all Self-Architecture v15 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE V15 TESTS")
    print("=" * 60)
    
    tests = [
        test_execution_readiness_creation,
        test_proof_item,
        test_proof_gate_engine,
        test_execution_eligibility,
        test_blocking_reasons,
        test_risk_bounded,
        test_coverage_metrics,
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
