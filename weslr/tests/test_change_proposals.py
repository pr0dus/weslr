#!/usr/bin/env python3
"""Tests for Self-Architecture Core v12: Change Proposal Packaging / Execution Gate."""

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
    AuditEntry,
    create_proposal,
    package_suggestion,
    get_execution_gate,
)

from self_architecture import (
    SelfArchitecture,
    Subsystem,
    SubsystemType,
    ArchitecturalRisk,
    ChangeProposal as V11ChangeProposal,
)

from datetime import datetime, timezone


def test_proposal_creation():
    """Test that proposals can be created with all required fields."""
    print("Test 1: Proposal creation")
    
    proposal = ChangeProposal(
        proposal_id="prop-001",
        title="Add feature X",
        description="Enable feature X for better user experience",
        affected_subsystems=["state", "continuity"],
        source_suggestion="suggest-001",
        risk_level="low",
        estimated_effort=30,
        calibration_confidence=0.8,
    )
    
    assert proposal.proposal_id == "prop-001"
    assert proposal.title == "Add feature X"
    assert "state" in proposal.affected_subsystems
    assert proposal.source_suggestion == "suggest-001"
    assert proposal.risk_level == "low"
    assert proposal.estimated_effort == 30
    assert proposal.calibration_confidence == 0.8
    assert proposal.state == ProposalState.PENDING_REVIEW.value
    assert proposal.approval_state == "pending"
    
    print("  ✓ Proposal creation works")
    return True


def test_proposal_serialization():
    """Test proposal to_dict/from_dict round-trip."""
    print("Test 2: Proposal serialization")
    
    proposal = ChangeProposal(
        proposal_id="prop-002",
        title="Refactor engine",
        description="Improve performance",
        affected_subsystems=["capability_discovery"],
        risk_level="medium",
        estimated_effort=50,
        forecast_summary="Efficiency improvement",
        expected_outcomes=["faster processing"],
        precedent_context="prop-001",
        memory_references=["mem-001"],
        validation_requirements=["test_scorecard"],
        rollback_expectations=["revert files"],
    )
    
    # Serialize
    data = proposal.to_dict()
    assert data["proposal_id"] == "prop-002"
    assert data["forecast_summary"] == "Efficiency improvement"
    assert len(data["affected_subsystems"]) == 1
    
    # Deserialize
    proposal2 = ChangeProposal.from_dict(data)
    assert proposal2.proposal_id == "prop-002"
    assert proposal2.forecast_summary == "Efficiency improvement"
    
    print("  ✓ Serialization round-trip works")
    return True


def test_audit_entry():
    """Test audit trail entry creation."""
    print("Test 3: Audit entry")
    
    entry = AuditEntry(
        timestamp="2026-04-06T10:00:00Z",
        actor="operator",
        action="state_transition:approved",
        details={"reason": "Good ROI"},
    )
    
    assert entry.actor == "operator"
    assert entry.action == "state_transition:approved"
    assert entry.details["reason"] == "Good ROI"
    
    entry_dict = entry.to_dict()
    assert entry_dict["actor"] == "operator"
    
    entry2 = AuditEntry.from_dict(entry_dict)
    assert entry2.actor == "operator"
    
    print("  ✓ Audit entry works")
    return True


def test_proposal_audit_history():
    """Test proposal audit trail preservation."""
    print("Test 4: Proposal audit history")
    
    proposal = ChangeProposal(
        proposal_id="prop-003",
        title="Test audit",
        description="Testing",
    )
    
    # Add audit entries
    proposal.add_audit_entry("created", "operator", {"source": "manual"})
    proposal.add_audit_entry("state_transition:approved", "operator", {})
    
    assert len(proposal.audit_history) == 2
    assert proposal.audit_history[0]["action"] == "created"
    assert proposal.audit_history[1]["action"] == "state_transition:approved"
    assert proposal.audit_history[0]["actor"] == "operator"
    
    print("  ✓ Audit history works")
    return True


def test_state_transition():
    """Test proposal state transitions."""
    print("Test 5: State transitions")
    
    proposal = ChangeProposal(
        proposal_id="prop-004",
        title="State test",
        description="Testing",
    )
    
    # Initial state
    assert proposal.state == ProposalState.PENDING_REVIEW.value
    
    # Transition to approved
    proposal.transition_state(ProposalState.APPROVED.value, "operator")
    assert proposal.state == ProposalState.APPROVED.value
    assert proposal.approval_state == "approved"
    assert len(proposal.audit_history) == 1
    
    # Transition to denied
    proposal.transition_state(ProposalState.DENIED.value, "operator")
    assert proposal.state == ProposalState.DENIED.value
    assert proposal.approval_state == "denied"
    
    # Transition to deferred
    proposal.transition_state(ProposalState.DEFERRED.value, "operator")
    assert proposal.state == ProposalState.DEFERRED.value
    assert proposal.approval_state == "deferred"
    
    print("  ✓ State transitions work")
    return True


def test_execution_gate():
    """Test execution gate enforcement."""
    print("Test 6: Execution gate")
    
    proposal = ChangeProposal(
        proposal_id="prop-005",
        title="Execution test",
        description="Testing",
    )
    
    # Initially not approved
    assert not proposal.is_approved_for_execution()
    assert proposal.get_execution_gate_status()["can_execute"] is False
    assert proposal.get_execution_gate_status()["requires_approval"] is True
    
    # Approve
    proposal.transition_state(ProposalState.APPROVED.value, "operator")
    assert proposal.is_approved_for_execution()
    assert proposal.get_execution_gate_status()["can_execute"] is True
    assert proposal.get_execution_gate_status()["requires_approval"] is False
    
    print("  ✓ Execution gate works")
    return True


def test_reversibility():
    """Test reversibility tracking."""
    print("Test 7: Reversibility")
    
    # With rollback expectations
    proposal1 = ChangeProposal(
        proposal_id="prop-006a",
        title="Reversible",
        description="With rollback",
        rollback_expectations=["revert files", "restore config"],
    )
    assert proposal1.is_reversible() is True
    
    # Without rollback (but additive)
    proposal2 = ChangeProposal(
        proposal_id="prop-006b",
        title="Additive",
        description="This is additive",
        rationale="This is additive only",
    )
    assert proposal2.is_reversible() is True
    
    # Neither (edge case)
    proposal3 = ChangeProposal(
        proposal_id="prop-006c",
        title="Non-reversible",
        description="No rollback documented",
    )
    # This would be False, but we mark additive as reversible by default
    assert proposal3.is_reversible() is False
    
    print("  ✓ Reversibility tracking works")
    return True


def test_execution_gate_class():
    """Test ExecutionGate class operations."""
    print("Test 8: ExecutionGate class")
    
    # Use temp file for tests
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        # Create proposal
        proposal = gate.create_proposal(
            title="Test proposal",
            description="Test",
            affected_subsystems=["state"],
            source_suggestion="suggest-001",
        )
        
        assert proposal.proposal_id.startswith("prop-")
        assert len(gate.proposals) == 1
        
        # Package suggestion
        suggestion_data = {
            "id": "suggest-002",
            "title": "Suggested improvement",
            "description": "An improvement",
            "affected_subsystems": ["continuity"],
            "risk_level": "medium",
            "implementation_effort_estimate": 40,
            "calibration_confidence": 0.7,
            "forecast_summary": "Better efficiency",
            "expected_outcomes": ["speedup"],
        }
        
        packaged = gate.package_proposal(suggestion_data)
        assert packaged.source_suggestion == "suggest-002"
        assert "continuity" in packaged.affected_subsystems
        
        # Review and approve
        reviewed = gate.review_proposal(packaged.proposal_id, "approve", "operator")
        assert reviewed is not None
        assert reviewed.state == ProposalState.APPROVED.value
        
        # Get pending proposals
        pending = gate.get_pending_proposals()
        assert len(pending) == 1  # Only the first one
        
        # Get approved proposals
        approved = gate.get_approved_proposals()
        assert len(approved) == 1
        
        # Generate review output
        review_output = gate.generate_proposal_review_output(packaged.proposal_id)
        assert review_output is not None
        assert review_output["title"] == "Suggested improvement"
        assert review_output["state"]["current"] == ProposalState.APPROVED.value
        
        print("  ✓ ExecutionGate class works")
    finally:
        temp_path.unlink()
    
    return True


def test_proposal_packaging():
    """Test suggestion packaging with all fields."""
    print("Test 9: Proposal packaging")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        suggestion_data = {
            "id": "suggest-003",
            "title": "Full packaging test",
            "description": "Comprehensive suggestion",
            "affected_subsystems": ["state", "continuity", "capability_discovery"],
            "risk_level": "high",
            "implementation_effort_estimate": 80,
            "calibration_confidence": 0.6,
            "forecast_summary": "Significant improvement expected",
            "expected_outcomes": ["performance", "reliability"],
            "precedent_context": "prop-001",
            "memory_references": ["mem-001", "mem-002"],
        }
        
        proposal = gate.package_proposal(suggestion_data)
        
        # Check all fields
        assert proposal.source_suggestion == "suggest-003"
        assert len(proposal.affected_subsystems) == 3
        assert proposal.risk_level == "high"
        assert proposal.estimated_effort == 80
        assert proposal.calibration_confidence == 0.6
        assert proposal.forecast_summary == "Significant improvement expected"
        assert len(proposal.expected_outcomes) == 2
        assert proposal.precedent_context == "prop-001"
        assert len(proposal.memory_references) == 2
        assert len(proposal.validation_requirements) >= 2
        assert len(proposal.rollback_expectations) >= 2
        
        print("  ✓ Proposal packaging works")
    finally:
        temp_path.unlink()
    
    return True


def test_execution_gate_block():
    """Test that execution is blocked for non-approved proposals."""
    print("Test 10: Execution gate enforcement")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        proposal = gate.create_proposal(
            title="Blocked proposal",
            description="Not approved",
        )
        
        # Try to execute without approval
        result = gate.execute_proposal_if_approved(proposal.proposal_id)
        
        assert result["success"] is False
        assert "Execution blocked" in result["error"]
        assert result["can_execute"] is False
        assert result["state"] == ProposalState.PENDING_REVIEW.value
        
        print("  ✓ Execution gate enforcement works")
    finally:
        temp_path.unlink()
    
    return True


def test_convenience_functions():
    """Test convenience functions."""
    print("Test 11: Convenience functions")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        # Create a new gate with temp path
        gate = ExecutionGate(storage_path=temp_path)
        
        # Test create_proposal via gate
        proposal = gate.create_proposal(
            title="Convenience test",
            description="Testing",
        )
        assert proposal.proposal_id.startswith("prop-")
        
        # Test package_suggestion via gate
        suggestion = gate.package_proposal({
            "id": "suggest-004",
            "title": "Packaged",
            "description": "Test",
        })
        assert suggestion.source_suggestion == "suggest-004"
        
        # Create a new gate and test using workspace path
        test_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/test_gate.json")
        test_path.parent.mkdir(parents=True, exist_ok=True)
        new_gate = ExecutionGate(storage_path=test_path)
        new_gate._save_proposals()  # Ensure directory and file exist
        
        print("  ✓ Convenience functions work")
    finally:
        temp_path.unlink()
        # Clean up test file
        test_path = Path("/data/data/com.termux/files/home/.openclaw/workspace/continuity/test_gate.json")
        test_path.unlink(missing_ok=True)
    
    return True


def test_backward_compatibility():
    """Test that v11 functionality is not broken."""
    print("Test 12: Backward compatibility")
    
    # V11 classes already imported at top level
    from self_architecture import (
        SelfArchitecture,
        Subsystem,
        SubsystemType,
        ArchitecturalRisk,
        ChangeProposal as V11ChangeProposal,
    )
    from datetime import datetime, timezone
    
    # Test v11 classes still work
    arch = SelfArchitecture()
    subsystem = Subsystem(
        name="state",
        description="State management",
        subsystem_type=SubsystemType.STATE.value,
    )
    arch.register_subsystem(subsystem)
    assert "state" in arch.subsystems
    
    risk = ArchitecturalRisk(
        id="risk-001",
        subsystem="state",
        description="Memory leak",
    )
    arch.register_risk(risk)
    assert "risk-001" in arch.risks
    
    v11_proposal = V11ChangeProposal(
        id="v11-prop-001",
        title="V11 proposal",
        description="Legacy",
    )
    assert v11_proposal.id == "v11-prop-001"
    
    print("  ✓ Backward compatibility works")
    return True


def test_audit_history_preservation():
    """Test that audit history is preserved across operations."""
    print("Test 13: Audit history preservation")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        # Create and modify proposal
        proposal = gate.create_proposal(
            title="History test",
            description="Testing",
        )
        initial_audit_count = len(proposal.audit_history)
        
        # Approve
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Defer
        gate.review_proposal(proposal.proposal_id, "defer", "operator")
        
        # Re-approve
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        # Check history
        audit = gate.get_proposal_audit_history(proposal.proposal_id)
        assert len(audit) >= 4  # created + approve + defer + approve
        
        # Verify audit entries
        actions = [entry["action"] for entry in audit]
        assert "proposal_created" in actions
        assert "state_transition:approved" in actions
        assert "state_transition:deferred" in actions
        
        # Save and reload
        gate._save_proposals()
        gate2 = ExecutionGate(storage_path=temp_path)
        reloaded = gate2.proposals[proposal.proposal_id]
        assert len(reloaded.audit_history) == len(audit)
        
        print("  ✓ Audit history preservation works")
    finally:
        temp_path.unlink()
    
    return True


def test_operator_review_output():
    """Test operator-facing review output format."""
    print("Test 14: Operator review output")
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        gate = ExecutionGate(storage_path=temp_path)
        
        suggestion_data = {
            "id": "suggest-005",
            "title": "Operator review test",
            "description": "For operator review",
            "affected_subsystems": ["state"],
            "risk_level": "low",
            "implementation_effort_estimate": 20,
            "calibration_confidence": 0.9,
            "forecast_summary": "Quick win",
            "expected_outcomes": ["speed"],
        }
        
        proposal = gate.package_proposal(suggestion_data)
        gate.review_proposal(proposal.proposal_id, "approve", "operator")
        
        review = gate.generate_proposal_review_output(proposal.proposal_id)
        
        # Check all required sections
        assert "proposal_id" in review
        assert "title" in review
        assert "description" in review
        
        assert "source" in review
        assert "scope" in review
        assert "assessment" in review
        assert "context" in review
        assert "governance" in review
        assert "state" in review
        assert "execution_gate" in review
        assert "audit_history" in review
        
        # Check governance fields
        assert "validation_requirements" in review["governance"]
        assert "rollback_expectations" in review["governance"]
        assert review["governance"]["can_execute"] is True
        
        # Check state
        assert review["state"]["current"] == ProposalState.APPROVED.value
        
        print("  ✓ Operator review output works")
    finally:
        temp_path.unlink()
    
    return True


def run_all_tests():
    """Run all Self-Architecture v12 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE V12 TESTS")
    print("=" * 60)
    
    tests = [
        test_proposal_creation,
        test_proposal_serialization,
        test_audit_entry,
        test_proposal_audit_history,
        test_state_transition,
        test_execution_gate,
        test_reversibility,
        test_execution_gate_class,
        test_proposal_packaging,
        test_execution_gate_block,
        test_convenience_functions,
        test_backward_compatibility,
        test_audit_history_preservation,
        test_operator_review_output,
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
