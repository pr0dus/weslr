#!/usr/bin/env python3
"""Tests for Self-Architecture Core v3: Review Surface Integration."""

from pathlib import Path
import os
import sys

os.chdir(Path(__file__).parent)

from self_architecture import (
    SelfArchitecture,
    Subsystem,
    SubsystemType,
    map_radar_suggestion_to_proposal,
)
from capability_suggestion import (
    CapabilitySuggestion,
    SuggestionStatus,
    SourceProvenance,
    CapabilityType,
)
from datetime import datetime, timezone


def test_enriched_review_output_structure():
    """Test that enriched review output has required structure."""
    print("Test 1: Enriched review output structure")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='capability_discovery',
        description='Capability discovery radar',
        subsystem_type=SubsystemType.CAPABILITY_DISCOVERY.value,
    ))
    
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    suggestion = CapabilitySuggestion(
        id='suggest-001',
        title='Add integration capabilities',
        description='Better integration with external tools',
        capability_type=CapabilityType.INTEGRATION,
        status=SuggestionStatus.NEW,
        provenance=SourceProvenance.GITHUB,
        created_at=now,
        updated_at=now,
        priority=40,
    )
    
    result = arch.get_enriched_review_output(suggestion)
    
    # Check top-level keys
    assert 'suggestion_id' in result
    assert 'title' in result
    assert 'description' in result
    
    # Check self_architecture
    assert 'self_architecture' in result
    sa = result['self_architecture']
    assert 'affected_subsystems' in sa
    assert 'architectural_fit' in sa
    assert 'risk_level' in sa
    assert 'fitness_impact' in sa
    assert 'recommendation' in sa
    assert 'rationale' in sa
    assert 'timing' in sa
    
    # Check classification
    assert 'classification' in result
    cl = result['classification']
    assert 'quick_win' in cl
    assert 'strategic' in cl
    assert 'speculative' in cl
    
    # Check decision_support
    assert 'decision_support' in result
    ds = result['decision_support']
    assert 'classification' in ds
    assert 'risk_level' in ds
    assert 'decision_recommendation' in ds
    
    # Check metadata
    assert 'priority' in result
    assert 'created_at' in result
    
    print("  ✓ Enriched review output structure works")
    return True


def test_self_architecture_judgment():
    """Test that self-architecture judgment is included."""
    print("Test 2: Self-architecture judgment")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='capability_discovery',
        description='Capability discovery radar',
        subsystem_type=SubsystemType.CAPABILITY_DISCOVERY.value,
    ))
    
    class MockSuggestion:
        id = 'suggest-001'
        title = 'Add automation'
        description = 'Add automation capabilities'
        capability_type = type('CapabilityType', (), {'value': 'automation'})()
        priority = 40
        created_at = '2026-04-06T00:00:00Z'
    
    result = arch.get_enriched_review_output(MockSuggestion())
    
    sa = result['self_architecture']
    
    # Check all judgment fields
    assert len(sa['affected_subsystems']) > 0
    assert sa['architectural_fit'] in ('strong', 'moderate', 'weak')
    assert sa['risk_level'] in ('low', 'medium', 'high')
    assert sa['recommendation'] in ('accept', 'accept_with_conditions', 'pending', 'reject')
    assert sa['timing'] in ('now', 'later', 'never')
    assert len(sa['rationale']) > 10
    
    print("  ✓ Self-architecture judgment works")
    return True


def test_decision_support_integration():
    """Test that decision support is integrated."""
    print("Test 3: Decision support integration")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='state',
        description='State management',
        subsystem_type='state',
    ))
    
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    suggestion = CapabilitySuggestion(
        id='suggest-001',
        title='State improvement',
        description='Better state management',
        capability_type=CapabilityType.STORAGE,
        status=SuggestionStatus.NEW,
        provenance=SourceProvenance.REDDIT,
        created_at=now,
        updated_at=now,
        priority=30,
    )
    
    result = arch.get_enriched_review_output(suggestion)
    ds = result['decision_support']
    
    # Check decision support fields exist
    assert 'classification' in ds
    assert 'risk_level' in ds
    assert 'decision_recommendation' in ds
    
    # Decision support should have valid values
    assert ds['risk_level'] in ('low', 'medium', 'high')
    assert ds['decision_recommendation'] in ('accept', 'pending', 'denied', 'snoozed')
    
    print("  ✓ Decision support integration works")
    return True


def test_classification_consistency():
    """Test that classifications are consistent."""
    print("Test 4: Classification consistency")
    
    arch = SelfArchitecture()
    
    class MockSuggestion:
        id = 'suggest-001'
        title = 'Quick improvement'
        description = 'Small improvement'
        capability_type = type('CapabilityType', (), {'value': 'analysis'})()
        priority = 50
    
    result = arch.get_enriched_review_output(MockSuggestion())
    
    cl = result['classification']
    
    # All three should be present
    assert 'quick_win' in cl
    assert 'strategic' in cl
    assert 'speculative' in cl
    
    # Should be boolean
    assert isinstance(cl['quick_win'], bool)
    assert isinstance(cl['strategic'], bool)
    assert isinstance(cl['speculative'], bool)
    
    # At most one should be true (mutually exclusive classification)
    total = sum([cl['quick_win'], cl['strategic'], cl['speculative']])
    assert total <= 1, "Classifications should be mutually exclusive"
    
    print("  ✓ Classification consistency works")
    return True


def test_fallback_behavior():
    """Test fallback behavior when evaluation fails."""
    print("Test 5: Fallback behavior")
    
    arch = SelfArchitecture()
    
    # No subsystems registered - edge case
    class MockSuggestion:
        id = 'suggest-001'
        title = 'Test'
        description = 'Test'
        capability_type = type('CapabilityType', (), {'value': 'other'})()
        priority = 30
    
    result = arch.get_enriched_review_output(MockSuggestion())
    
    # Should still return valid structure
    assert 'self_architecture' in result
    assert 'affected_subsystems' in result['self_architecture']
    assert 'recommendation' in result['self_architecture']
    assert 'rationale' in result['self_architecture']
    
    print("  ✓ Fallback behavior works")
    return True


def test_backward_compatibility():
    """Test backward compatibility with old suggestion objects."""
    print("Test 6: Backward compatibility")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='capability_discovery',
        description='Capability discovery radar',
    ))
    
    # Old-style suggestion with minimal attributes
    class OldStyleSuggestion:
        id = 'suggest-001'
        title = 'Old suggestion'
        description = 'Old suggestion description'
    
    result = arch.get_enriched_review_output(OldStyleSuggestion())
    
    # Should handle gracefully
    assert 'suggestion_id' in result
    assert 'title' in result
    assert 'self_architecture' in result
    assert 'recommendation' in result['self_architecture']
    
    print("  ✓ Backward compatibility works")
    return True


def test_affected_subsystems_mapping():
    """Test that affected subsystems are correctly mapped."""
    print("Test 7: Affected subsystems mapping")
    
    arch = SelfArchitecture()
    
    # Register specific subsystems
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
    
    class MockSuggestion:
        id = 'suggest-001'
        title = 'Integration improvement'
        description = 'Better integration'
        capability_type = type('CapabilityType', (), {'value': 'integration'})()
        priority = 40
    
    result = arch.get_enriched_review_output(MockSuggestion())
    
    affected = result['self_architecture']['affected_subsystems']
    
    # Integration affects state and continuity
    assert 'state' in affected
    assert 'continuity' in affected
    
    print("  ✓ Affected subsystems mapping works")
    return True


def test_rationale_generation():
    """Test that rationales are generated."""
    print("Test 8: Rationale generation")
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='capability_discovery',
        description='Capability discovery radar',
    ))
    arch.register_subsystem(Subsystem(
        name='state',
        description='State management',
    ))
    
    class MockSuggestion:
        id = 'suggest-001'
        title = 'State improvement'
        description = 'Better state management - improvement'
        capability_type = type('CapabilityType', (), {'value': 'storage'})()
        priority = 40
    
    result = arch.get_enriched_review_output(MockSuggestion())
    
    rationale = result['self_architecture']['rationale']
    
    # Rationale should be non-empty string
    assert isinstance(rationale, str)
    assert len(rationale) > 10
    
    # Should contain meaningful information
    assert 'Architectural' in rationale or 'affects' in rationale
    
    print("  ✓ Rationale generation works")
    return True


def run_all_tests():
    """Run all Self-Architecture v3 tests."""
    print("=" * 60)
    print("SECTION 4 — VALIDATION: SELF-ARCHITECTURE CORE V3 TESTS")
    print("=" * 60)
    
    tests = [
        test_enriched_review_output_structure,
        test_self_architecture_judgment,
        test_decision_support_integration,
        test_classification_consistency,
        test_fallback_behavior,
        test_backward_compatibility,
        test_affected_subsystems_mapping,
        test_rationale_generation,
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
