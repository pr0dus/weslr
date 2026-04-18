"""Unit tests for ProviderSuitability component.

Tests provider scoring and suitability analysis.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from request_intelligence.provider_suitability import (
    ProviderSuitability,
    ProviderType,
)


def test_provider_suitability_basic():
    """Test basic provider scoring."""
    scorer = ProviderSuitability()
    
    # Score embedded provider for basic request
    score = scorer.score(ProviderType.EMBEDDED, "What time is it?")
    
    assert score.provider_type == ProviderType.EMBEDDED
    assert score.score > 0
    assert score.confidence > 0
    assert score.evidence_score > 0
    print("✓ test_provider_suitability_basic passed")


def test_provider_suitability_best_provider():
    """Test getting best provider for request."""
    scorer = ProviderSuitability()
    
    # Get best provider for time query
    best = scorer.get_best_provider("What time is it?")
    
    assert best is not None
    assert best.provider_type in [ProviderType.EMBEDDED, ProviderType.EVIDENCE]
    print("✓ test_provider_suitability_best_provider passed")


def test_provider_suitability_all_providers():
    """Test scoring all providers."""
    scorer = ProviderSuitability()
    
    scores = scorer.score_all("Research the history of Rome")
    
    assert len(scores) > 0
    # Scores should be sorted by score descending
    for i in range(len(scores) - 1):
        assert scores[i].score >= scores[i + 1].score
    print("✓ test_provider_suitability_all_providers passed")


def test_provider_suitability_evidence_provider():
    """Test evidence provider selection."""
    scorer = ProviderSuitability()
    
    # Time query should select evidence provider
    best = scorer.get_best_provider("What time is it?")
    
    assert best is not None
    print("✓ test_provider_suitability_evidence_provider passed")


def test_provider_suitability_scores():
    """Test provider scores structure."""
    scorer = ProviderSuitability()
    
    score = scorer.score(ProviderType.OPENAI, "What time is it?")
    
    assert hasattr(score, "score")
    assert hasattr(score, "provider_type")
    assert hasattr(score, "provider_name")
    assert hasattr(score, "suitability_factors")
    
    factors = score.suitability_factors
    assert "capability" in factors
    assert "evidence" in factors
    assert "latency" in factors
    assert "quality" in factors
    print("✓ test_provider_suitability_scores passed")


def run_all_tests():
    """Run all provider suitability tests."""
    tests = [
        test_provider_suitability_basic,
        test_provider_suitability_best_provider,
        test_provider_suitability_all_providers,
        test_provider_suitability_evidence_provider,
        test_provider_suitability_scores,
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
    
    print(f"\n=== ProviderSuitability Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
