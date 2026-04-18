#!/usr/bin/env python3
"""Tests for Self-Architecture Core v2: Operator-Coupled Evaluation."""

from pathlib import Path
import os
import sys

os.chdir(Path(__file__).parent)

from self_architecture import (
    SelfArchitecture,
    Subsystem,
    SubsystemType,
    FitnessGoal,
    map_radar_suggestion_to_proposal,
)


def test_evaluate_suggestion():
    """Test suggestion evaluation against architecture."""
    print("Test 1: Evaluate suggestion")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='capability_discovery',
        description='Capability discovery radar',
        subsystem_type=SubsystemType.CAPABILITY_DISCOVERY.value,
    ))
    arch.register_fitness_goal(FitnessGoal(
        id='goal-001',
        name='Performance Goal',
        description='Achieve sub-second discovery',
        subsystems=['capability_discovery'],
        success_criteria=['p99 < 1000ms'],
    ))
    
    # Mock radar suggestion
    class MockSuggestion:
        id = 'suggest-001'
        capability_type = type('CapabilityType', (), {'value': 'integration'})()
        title = 'Add integration capabilities'
        description = 'Better integration with external tools'
        priority = 40
    
    result = arch.evaluate_suggestion(MockSuggestion())
    
    assert result['suggestion_id'] == 'suggest-001'
    assert len(result['affected_subsystems']) > 0
    assert 'integration' in result['affected_subsystems'] or 'continuity' in result['affected_subsystems']
    assert result['architectural_fit'] in ('strong', 'moderate', 'weak')
    assert result['recommendation'] in ('accept', 'accept_with_conditions', 'pending', 'reject')
    assert result['timing'] in ('now', 'later', 'never')
    assert 'rationale' in result
    assert len(result['rationale']) > 0
    
    print("  ✓ Suggestion evaluation works")
    return True


def test_evaluate_all_suggestions():
    """Test batch evaluation of multiple suggestions."""
    print("Test 2: Evaluate all suggestions")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='capability_discovery',
        description='Capability discovery radar',
        subsystem_type=SubsystemType.CAPABILITY_DISCOVERY.value,
    ))
    
    # Mock multiple radar suggestions
    class MockSuggestion:
        def __init__(self, idx):
            self.id = f'suggest-{idx}'
            self.capability_type = type('CapabilityType', (), {'value': 'automation'})()
            self.title = f'Test suggestion {idx}'
            self.description = f'Description {idx}'
            self.priority = 30 + idx * 10
    
    suggestions = [MockSuggestion(i) for i in range(3)]
    
    results = arch.evaluate_all_suggestions(suggestions)
    
    assert len(results) == 3
    for i, result in enumerate(results):
        assert result['suggestion_id'] == f'suggest-{i}'
    
    print("  ✓ Batch evaluation works")
    return True


def test_integration_with_radar_mapping():
    """Test integration of radar suggestion to architecture mapping."""
    print("Test 3: Radar to architecture mapping")
    
    arch = SelfArchitecture()
    
    # Register subsystems that would be affected
    arch.register_subsystem(Subsystem(
        name='state',
        description='State management',
        subsystem_type='state',
    ))
    arch.register_subsystem(Subsystem(
        name='continuity',
        description='Continuity tracking',
        subsystem_type='other',
    ))
    
    # Register fitness goals
    arch.register_fitness_goal(FitnessGoal(
        id='goal-001',
        name='Reliability Goal',
        description='Maintain high availability',
        subsystems=['continuity'],
        success_criteria=['uptime > 99.9%'],
    ))
    
    # Mock radar suggestion
    class MockSuggestion:
        id = 'suggest-001'
        capability_type = type('CapabilityType', (), {'value': 'integration'})()
        title = 'Add integration capabilities'
        description = 'Better integration with external tools - strategic improvement'
        priority = 40
    
    result = arch.evaluate_suggestion(MockSuggestion())
    
    # Check that integration affects correct subsystems
    affected = result['affected_subsystems']
    assert 'state' in affected or 'continuity' in affected
    
    # Check fitness impact
    assert 'Reliability Goal' in result['fitness_impact']
    
    print("  ✓ Radar to architecture mapping works")
    return True


def test_classification_consistency():
    """Test that classification fields are consistent."""
    print("Test 4: Classification consistency")
    
    arch = SelfArchitecture()
    
    class MockSuggestion:
        id = 'suggest-001'
        capability_type = type('CapabilityType', (), {'value': 'automation'})()
        title = 'Quick automation fix'
        description = 'Small improvement to automation workflow'
        priority = 50
    
    result = arch.evaluate_suggestion(MockSuggestion())
    
    # Check classification structure
    classification = result['classification']
    assert 'quick_win' in classification
    assert 'strategic' in classification
    assert 'speculative' in classification
    
    # Ensure boolean values
    assert isinstance(classification['quick_win'], bool)
    assert isinstance(classification['strategic'], bool)
    assert isinstance(classification['speculative'], bool)
    
    print("  ✓ Classification consistency works")
    return True


def test_rationale_generation():
    """Test that rationales are generated for evaluations."""
    print("Test 5: Rationale generation")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='capability_discovery',
        description='Capability discovery radar',
        subsystem_type='capability_discovery',
    ))
    
    class MockSuggestion:
        id = 'suggest-001'
        capability_type = type('CapabilityType', (), {'value': 'analysis'})()
        title = 'Improve analysis capabilities'
        description = 'Better analysis of detected capabilities'
        priority = 40
    
    result = arch.evaluate_suggestion(MockSuggestion())
    
    # Check rationale is present and non-empty
    assert 'rationale' in result
    assert isinstance(result['rationale'], str)
    assert len(result['rationale']) > 10  # Reasonable length
    
    print("  ✓ Rationale generation works")
    return True


def test_timing_classification():
    """Test timing classification based on recommendation."""
    print("Test 6: Timing classification")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='state',
        description='State management',
        subsystem_type='state',
    ))
    
    class MockSuggestion:
        id = 'suggest-001'
        capability_type = type('CapabilityType', (), {'value': 'security'})()
        title = 'Security improvement'
        description = 'Minor security enhancement'
        priority = 30
    
    result = arch.evaluate_suggestion(MockSuggestion())
    
    # Check timing is one of valid values
    assert result['timing'] in ('now', 'later', 'never')
    
    # Timing should correlate with recommendation
    rec = result['recommendation']
    timing = result['timing']
    
    # If recommendation is reject, timing should be never
    if rec == 'reject':
        assert timing == 'never'
    
    print("  ✓ Timing classification works")
    return True


def test_backward_compatibility():
    """Test that old architecture data still works."""
    print("Test 7: Backward compatibility")
    
    arch = SelfArchitecture()
    
    # Register old-style subsystem (no type)
    arch.register_subsystem(Subsystem(
        name='old_subsystem',
        description='Legacy subsystem',
    ))
    
    # Evaluate a suggestion against old architecture
    class MockSuggestion:
        id = 'suggest-001'
        capability_type = type('CapabilityType', (), {'value': 'other'})()
        title = 'Other capability'
        description = 'Other capability improvement'
        priority = 30
    
    result = arch.evaluate_suggestion(MockSuggestion())
    
    # Should succeed even with old architecture
    assert result['suggestion_id'] == 'suggest-001'
    
    print("  ✓ Backward compatibility works")
    return True


def test_risk_assessment_in_evaluation():
    """Test that risk is assessed during evaluation."""
    print("Test 8: Risk assessment in evaluation")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='state',
        description='State management',
        subsystem_type='state',
    ))
    
    class MockSuggestion:
        id = 'suggest-001'
        capability_type = type('CapabilityType', (), {'value': 'security'})()
        title = 'Breaking security change'
        description = 'Major breaking change to security subsystem'
        priority = 40
    
    result = arch.evaluate_suggestion(MockSuggestion())
    
    # Risk should be assessed
    assert 'risk_level' in result
    assert result['risk_level'] in ('low', 'medium', 'high')
    
    print("  ✓ Risk assessment in evaluation works")
    return True


def run_all_tests():
    """Run all Self-Architecture v2 tests."""
    print("=" * 60)
    print("SECTION 4 — VALIDATION: SELF-ARCHITECTURE CORE V2 TESTS")
    print("=" * 60)
    
    tests = [
        test_evaluate_suggestion,
        test_evaluate_all_suggestions,
        test_integration_with_radar_mapping,
        test_classification_consistency,
        test_rationale_generation,
        test_timing_classification,
        test_backward_compatibility,
        test_risk_assessment_in_evaluation,
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
