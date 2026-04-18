#!/usr/bin/env python3
"""Tests for Self-Architecture Core v1."""

from pathlib import Path
import os
import sys

os.chdir(Path(__file__).parent)

from self_architecture import (
    SelfArchitecture,
    Subsystem,
    SubsystemType,
    SubsystemStatus,
    ArchitecturalRisk,
    ChangeProposal,
    ChangeType,
    FitnessGoal,
    Recommendation,
    RiskAssessor,
    ProposalEvaluator,
    map_radar_suggestion_to_proposal,
)


def test_subsystem_registration():
    """Test subsystem registration and metadata."""
    print("Test 1: Subsystem registration")
    
    arch = SelfArchitecture()
    
    subsystem = Subsystem(
        name="capability_discovery",
        description="Capability discovery radar",
        version="2.0.0",
        subsystem_type=SubsystemType.CAPABILITY_DISCOVERY.value,
        status=SubsystemStatus.ACTIVE.value,
        goals=["detect emerging capabilities", "track trends"],
        bottlenecks=["scalability", "latency"],
        lines_of_code=1500,
        owner="WESLR Team",
        tags=["radar", "discovery"],
    )
    
    registered = arch.register_subsystem(subsystem)
    
    assert registered.name == "capability_discovery"
    assert registered.version == "2.0.0"
    assert "capability_discovery" in arch.subsystems
    assert "discovery" in registered.tags
    
    print("  ✓ Subsystem registration works")
    return True


def test_dependency_graph():
    """Test dependency graph construction."""
    print("Test 2: Dependency graph")
    
    arch = SelfArchitecture()
    
    # Register subsystems with dependencies
    s1 = Subsystem(name="A", description="A depends on B")
    s1.depends_on = ["B"]
    
    s2 = Subsystem(name="B", description="B is depended on by A")
    s2.depended_by = ["A"]
    
    arch.register_subsystem(s1)
    arch.register_subsystem(s2)
    
    # Check dependency graph
    assert "B" in arch.dependency_graph
    assert "A" in arch.dependency_graph["B"]
    
    print("  ✓ Dependency graph works")
    return True


def test_risk_assessment():
    """Test risk assessment and mitigation."""
    print("Test 3: Risk assessment")
    
    # Test severity
    high_sev = RiskAssessor.assess_severity("Data corruption risk", "state")
    assert high_sev == "high"
    
    med_sev = RiskAssessor.assess_severity("Performance issue", "state")
    assert med_sev in ("medium", "high")
    
    low_sev = RiskAssessor.assess_severity("Minor improvement", "state")
    assert low_sev == "low"
    
    # Test mitigation generation
    mitigation = RiskAssessor.generate_mitigation("Breaking change", "state")
    assert mitigation is not None
    assert "migration" in mitigation.lower()
    
    print("  ✓ Risk assessment works")
    return True


def test_proposal_evaluation():
    """Test proposal evaluation logic."""
    print("Test 4: Proposal evaluation")
    
    arch = SelfArchitecture()
    evaluator = ProposalEvaluator(arch)
    
    # Test quick win
    prop1 = ChangeProposal(
        id="qw-001",
        title="Quick fix",
        description="Small improvement to state management",
    )
    evaluated1 = evaluator.evaluate(prop1)
    assert evaluated1.quick_win == True
    assert evaluated1.recommendation in ("accept", "accept_with_conditions")
    
    # Test strategic
    prop2 = ChangeProposal(
        id="str-001",
        title="Strategic refactoring",
        description="Strategic improvement to continuity layer",
        affected_subsystems=["continuity", "state"],
    )
    evaluated2 = evaluator.evaluate(prop2)
    assert evaluated2.strategic == True
    
    # Test speculative (too many subsystems)
    prop3 = ChangeProposal(
        id="spec-001",
        title="Large refactoring",
        description="Refactor multiple systems",
        affected_subsystems=["state", "continuity", "task", "file_ingestion"],
    )
    evaluated3 = evaluator.evaluate(prop3)
    assert evaluated3.speculative == True
    
    print("  ✓ Proposal evaluation works")
    return True


def test_radar_integration():
    """Test mapping radar suggestions to proposals."""
    print("Test 5: Radar integration")
    
    # Mock radar suggestion
    class MockSuggestion:
        capability_type = type('CapabilityType', (), {'value': 'automation'})()
        title = "Add automation capabilities"
        description = "Enable better automation workflows"
        created_at = "2026-04-06T00:00:00Z"
    
    prop = map_radar_suggestion_to_proposal(MockSuggestion(), "radar-001")
    
    assert prop.id == "radar-001"
    assert len(prop.affected_subsystems) > 0
    assert "automation" in prop.affected_subsystems or prop.change_type == "improvement"
    
    print("  ✓ Radar integration works")
    return True


def test_fitness_goals():
    """Test fitness goal registration and tracking."""
    print("Test 6: Fitness goals")
    
    arch = SelfArchitecture()
    
    goal = FitnessGoal(
        id="goal-001",
        name="Performance Goal",
        description="Achieve sub-second discovery",
        subsystems=["capability_discovery", "state"],
        success_criteria=["p99 < 1000ms", "throughput > 100/s"],
    )
    
    registered = arch.register_fitness_goal(goal)
    
    assert registered.id == "goal-001"
    assert "capability_discovery" in registered.subsystems
    assert "throughput > 100/s" in registered.success_criteria
    
    print("  ✓ Fitness goals work")
    return True


def test_backward_compatibility():
    """Test that old data structures work with new model."""
    print("Test 7: Backward compatibility")
    
    arch = SelfArchitecture()
    
    # Create arch from old-style dict
    old_data = {
        "subsystems": {
            "test": {
                "name": "test",
                "description": "test subsystem",
                "version": "1.0.0",
            }
        },
        "risks": {},
        "proposals": {},
        "fitness_goals": {},
        "dependency_graph": {},
    }
    
    restored = SelfArchitecture.from_dict(old_data)
    
    assert "test" in restored.subsystems
    assert restored.subsystems["test"].description == "test subsystem"
    
    print("  ✓ Backward compatibility works")
    return True


def test_recommendation_classification():
    """Test recommendation classification based on criteria."""
    print("Test 8: Recommendation classification")
    
    arch = SelfArchitecture()
    evaluator = ProposalEvaluator(arch)
    
    # Test quick win -> accept
    prop1 = ChangeProposal(
        id="quick-win",
        title="Quick win",
        description="Small improvement to state management",
    )
    prop1.quick_win = True
    evaluated1 = evaluator.evaluate(prop1)
    assert evaluated1.recommendation in (Recommendation.ACCEPT.value, Recommendation.ACCEPT_WITH_CONDITIONS.value)
    
    # Test high risk -> reject (breaking change)
    prop2 = ChangeProposal(
        id="high-risk",
        title="High risk change",
        description="Breaking change to security subsystem",
    )
    evaluated2 = evaluator.evaluate(prop2)
    # Check if risk context was set correctly
    assert "high" in (evaluated2.risk_context or "") or evaluated2.recommendation == Recommendation.REJECT.value
    
    print("  ✓ Recommendation classification works")
    return True


def run_all_tests():
    """Run all Self-Architecture tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE TESTS")
    print("=" * 60)
    
    tests = [
        test_subsystem_registration,
        test_dependency_graph,
        test_risk_assessment,
        test_proposal_evaluation,
        test_radar_integration,
        test_fitness_goals,
        test_backward_compatibility,
        test_recommendation_classification,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, "PASS"))
        except Exception as e:
            results.append((test.__name__, f"FAIL: {e}"))
            print(f"  ✗ {e}")
    
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
