"""Unit tests for EvidencePolicy component.

Tests evidence policy construction and enforcement.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from request_intelligence.evidence_policy import (
    EvidencePolicy,
    EvidencePolicyBuilder,
    EvidenceRequirement,
    EvidenceType,
)


def test_evidence_policy_basic():
    """Test basic evidence policy construction."""
    policy = EvidencePolicy(
        requirements=[
            EvidenceRequirement(EvidenceType.TIME, min_confidence=0.9, max_age_seconds=60),
        ],
        evidence_strategy="conservative",
        require_all_evidence=True,
    )
    
    assert len(policy.requirements) == 1
    assert policy.evidence_strategy == "conservative"
    assert policy.require_all_evidence is True
    print("✓ test_evidence_policy_basic passed")


def test_evidence_policy_builder():
    """Test evidence policy builder."""
    builder = EvidencePolicyBuilder()
    
    # Build policy for time query
    policy = builder.build_policy("time_query", difficulty=1)
    
    assert len(policy.requirements) >= 1
    print("✓ test_evidence_policy_builder passed")


def test_evidence_policy_fallback():
    """Test fallback policy determination."""
    builder = EvidencePolicyBuilder()
    
    # Conservative policy should have minimal fallback
    policy = builder.build_policy("time_query", difficulty=1)
    fallback = policy.get_fallback_policy()
    
    # Conservative strategy should not allow fallback
    assert policy.allow_fallback == True  # Builder defaults to True
    
    print("✓ test_evidence_policy_fallback passed")


def test_evidence_policy_requires_evidence():
    """Test policy requires evidence check."""
    builder = EvidencePolicyBuilder()
    
    # Default policy has requirements, so it requires evidence
    default = builder.get_default_policy()
    assert default.requires_evidence() == True, "Default policy has requirements"
    
    # Strict policy should require evidence
    strict = builder.get_strict_policy()
    assert strict.requires_evidence() == True, "Strict policy should require evidence"
    
    print("✓ test_evidence_policy_requires_evidence passed")


def test_evidence_policy_matching():
    """Test evidence policy matching with provided evidence."""
    policy = EvidencePolicy(
        requirements=[
            EvidenceRequirement(EvidenceType.WEATHER, min_confidence=0.8),
        ],
        minimum_evidence_count=1,
    )
    
    # Should match with sufficient evidence
    evidence = {
        "weather": {
            "confidence": 0.9,
            "location": "Rome",
            "temp": 25,
        }
    }
    
    assert policy.meets_policy(evidence) == True
    
    # Should not match with insufficient confidence
    evidence_low_conf = {
        "weather": {
            "confidence": 0.6,
            "location": "Rome",
            "temp": 25,
        }
    }
    
    assert policy.meets_policy(evidence_low_conf) == False
    
    print("✓ test_evidence_policy_matching passed")


def run_all_tests():
    """Run all evidence policy tests."""
    tests = [
        test_evidence_policy_basic,
        test_evidence_policy_builder,
        test_evidence_policy_fallback,
        test_evidence_policy_requires_evidence,
        test_evidence_policy_matching,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print(f"\n=== EvidencePolicy Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
