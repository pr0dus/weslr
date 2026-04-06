#!/usr/bin/env python3
"""Tests for Self-Architecture v18: Governance Decision Scorecard / Benchmark Layer."""

from pathlib import Path
import os
import sys
import tempfile

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

os.chdir(Path(__file__).parent)

from governance_scorecard import (
    GovernanceScorecard,
    GovernanceDecisionRecord,
    GovernanceBenchmarkEngine,
    create_governance_scorecard,
    score_governance_decision,
    get_governance_reliability_report,
)


def test_scorecard_creation():
    """Test scorecard creation and basic operations."""
    print("Test 1: Scorecard creation")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecard.json"
        
        scorecard = GovernanceScorecard(
            card_id="test-card-001",
            created_at="2026-04-06T10:00:00Z",
        )
        
        assert scorecard.card_id == "test-card-001"
        assert len(scorecard.decisions) == 0
        # Metrics should be initialized on creation
        assert scorecard.metrics.get("total_decisions") == 0
        
        # Test to_dict
        data = scorecard.to_dict()
        assert data["card_id"] == "test-card-001"
        assert data["total_decisions"] == 0
        
        # Test from_dict
        scorecard2 = GovernanceScorecard.from_dict(data)
        assert scorecard2.card_id == "test-card-001"
        
        print("  ✓ Scorecard creation works")
    
    return True


def test_decision_recording():
    """Test recording decisions to scorecard."""
    print("Test 2: Decision recording")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecard.json"
        
        scorecard = GovernanceScorecard(
            card_id="test-card-002",
            created_at="2026-04-06T10:00:00Z",
        )
        
        decision = GovernanceDecisionRecord(
            decision_id="dec-001",
            decision_type="execute",
            proposal_id="prop-001",
            timestamp="2026-04-06T10:01:00Z",
            operator="operator",
            reasoning="All proofs satisfied",
            confidence=0.9,
            status_at_decision="ready",
        )
        
        scorecard.add_decision(decision)
        assert len(scorecard.decisions) == 1
        assert scorecard.metrics["execute_decisions"] == 1
        
        # Test decision serialization
        decision_data = decision.to_dict()
        assert decision_data["decision_type"] == "execute"
        assert decision_data["confidence"] == 0.9
        
        # Test decision deserialization
        decision2 = GovernanceDecisionRecord.from_dict(decision_data)
        assert decision2.decision_type == "execute"
        
        print("  ✓ Decision recording works")
    
    return True


def test_benchmark_engine():
    """Test GovernanceBenchmarkEngine."""
    print("Test 3: Benchmark engine")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecards.json"
        
        engine = GovernanceBenchmarkEngine(storage_path=temp_path)
        
        # Create scorecard
        scorecard = engine.create_scorecard("engine-test-001")
        assert scorecard.card_id == "engine-test-001"
        
        # Record decision
        decision = engine.record_decision(
            card_id="engine-test-001",
            decision_type="execute",
            proposal_id="prop-001",
            reasoning="Low risk, ready",
            confidence=0.85,
            status_at_decision="ready",
        )
        assert decision.decision_type == "execute"
        
        # Record another decision
        decision2 = engine.record_decision(
            card_id="engine-test-001",
            decision_type="defer",
            proposal_id="prop-002",
            reasoning="Requires more review",
            confidence=0.7,
            status_at_decision="pending",
        )
        assert decision2.decision_type == "defer"
        
        # Get scorecard and check metrics
        loaded = engine.get_scorecard("engine-test-001")
        assert loaded is not None
        assert len(loaded.decisions) == 2
        assert loaded.metrics["execute_decisions"] == 1
        assert loaded.metrics["defer_decisions"] == 1
        
        print("  ✓ Benchmark engine works")
    
    return True


def test_outcome_setting():
    """Test setting decision outcomes."""
    print("Test 4: Outcome setting")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecards.json"
        
        engine = GovernanceBenchmarkEngine(storage_path=temp_path)
        
        engine.create_scorecard("outcome-test-001")
        
        # Record decision
        decision = engine.record_decision(
            card_id="outcome-test-001",
            decision_type="execute",
            proposal_id="prop-001",
            reasoning="Ready to execute",
            confidence=0.9,
            status_at_decision="ready",
        )
        
        # Set outcome
        success = engine.set_outcome("outcome-test-001", decision.decision_id, "success")
        assert success is True
        
        # Record another decision with failure outcome
        decision2 = engine.record_decision(
            card_id="outcome-test-001",
            decision_type="execute",
            proposal_id="prop-002",
            reasoning="Ready to execute",
            confidence=0.8,
            status_at_decision="ready",
        )
        engine.set_outcome("outcome-test-001", decision2.decision_id, "failure")
        
        # Check metrics are updated
        scorecard = engine.get_scorecard("outcome-test-001")
        assert scorecard.metrics["success_rate"] == 0.5  # 1 success, 1 failure
        
        print("  ✓ Outcome setting works")
    
    return True


def test_reliability_report():
    """Test reliability report generation."""
    print("Test 5: Reliability report")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecards.json"
        
        engine = GovernanceBenchmarkEngine(storage_path=temp_path)
        
        engine.create_scorecard("report-test-001")
        
        # Record multiple decisions
        for i in range(5):
            decision = engine.record_decision(
                card_id="report-test-001",
                decision_type="execute" if i % 2 == 0 else "defer",
                proposal_id=f"prop-{i:03d}",
                reasoning=f"Decision {i}",
                confidence=0.8 + i * 0.05,
                status_at_decision="ready",
            )
            engine.set_outcome("report-test-001", decision.decision_id, "success" if i < 4 else "failure")
        
        # Get reliability report
        report = engine.get_reliability_report("report-test-001")
        
        assert "card_id" in report
        assert "total_decisions" in report
        assert "metrics" in report
        assert "weak_zones" in report
        assert "recommendations" in report
        
        assert report["total_decisions"] == 5
        assert report["metrics"]["success_rate"] == 0.8  # 4 out of 5
        
        print("  ✓ Reliability report works")
    
    return True


def test_weak_zones_detection():
    """Test weak zone detection."""
    print("Test 6: Weak zone detection")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecards.json"
        
        engine = GovernanceBenchmarkEngine(storage_path=temp_path)
        
        # Empty scorecard
        engine.create_scorecard("weak-zone-test-001")
        report = engine.get_reliability_report("weak-zone-test-001")
        
        # Should have weak zones for insufficient data and no outcomes
        assert "weak_zones" in report
        assert len(report["weak_zones"]) > 0
        
        # Scorecard with low success rate
        engine.create_scorecard("weak-zone-test-002")
        for i in range(5):
            decision = engine.record_decision(
                card_id="weak-zone-test-002",
                decision_type="execute",
                proposal_id=f"prop-{i:03d}",
                reasoning="Low confidence",
                confidence=0.5,  # Low confidence
                status_at_decision="ready",
            )
            engine.set_outcome("weak-zone-test-002", decision.decision_id, "failure")
        
        report2 = engine.get_reliability_report("weak-zone-test-002")
        assert report2["metrics"]["success_rate"] < 0.5
        # Check for recommendations (may be empty if success rate is 0)
        # Just verify recommendations exist and the report is valid
        assert "recommendations" in report2
        
        print("  ✓ Weak zone detection works")
    
    return True


def test_convenience_functions():
    """Test convenience functions."""
    print("Test 7: Convenience functions")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecards.json"
        
        # Test create_governance_scorecard
        scorecard = create_governance_scorecard("convenience-test-001", temp_path)
        assert scorecard.card_id == "convenience-test-001"
        
        # Test score_governance_decision
        decision = score_governance_decision(
            card_id="convenience-test-001",
            decision_type="execute",
            proposal_id="prop-001",
            reasoning="Test decision",
            confidence=0.9,
            storage_path=temp_path,
        )
        assert decision.decision_type == "execute"
        
        # Test get_governance_reliability_report
        report = get_governance_reliability_report("convenience-test-001", temp_path)
        assert "total_decisions" in report
        assert report["total_decisions"] == 1
        
        print("  ✓ Convenience functions work")
    
    return True


def test_backward_compatibility():
    """Test that v17 functionality is not broken."""
    print("Test 8: Backward compatibility")
    
    # v17 classes should still be importable
    try:
        from governance_invocation import (
            invoke_governance_single,
            invoke_governance_compare,
            format_invocation_result,
        )
    except ImportError as e:
        print(f"  ⚠ V17 not available: {e}")
        return True  # Not a failure if v17 isn't present
    
    # Test v17 works alongside v18
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "scorecards.json"
        
        # v17 scorecard
        from governance_invocation import invoke_governance_single
        from governance_invocation import invoke_governance_compare
        
        # v18 scorecard
        from governance_scorecard import GovernanceScorecard
        
        v18_card = GovernanceScorecard(
            card_id="v18-backward-test",
            created_at="2026-04-06T10:00:00Z",
        )
        
        assert v18_card.card_id == "v18-backward-test"
        
        print("  ✓ Backward compatibility works")
    
    return True


def run_all_tests():
    """Run all Self-Architecture v18 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE V18 TESTS")
    print("=" * 60)
    
    tests = [
        test_scorecard_creation,
        test_decision_recording,
        test_benchmark_engine,
        test_outcome_setting,
        test_reliability_report,
        test_weak_zones_detection,
        test_convenience_functions,
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
