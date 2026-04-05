"""Unit tests for RequestIntelligence - Classifier component.

Tests classification of requests into categories.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from request_intelligence.classifier import RequestClassifier, RoutingCategory, EvidenceCategory


def test_classifier_basic_time():
    """Test classifier with basic time query."""
    classifier = RequestClassifier()
    
    result = classifier.classify("What time is it?")
    
    assert result.primary_routing == RoutingCategory.LOCAL, f"Expected LOCAL, got {result.primary_routing}"
    assert EvidenceCategory.TIME in result.evidence_requirements, "Should require TIME evidence"
    assert result.confidence >= 0.7, "Confidence should be >= 0.7"
    print("✓ test_classifier_basic_time passed")


def test_classifier_weather_query():
    """Test classifier with weather query."""
    classifier = RequestClassifier()
    
    result = classifier.classify("What's the weather in Rome?")
    
    assert result.primary_routing == RoutingCategory.LOCAL, f"Expected LOCAL, got {result.primary_routing}"
    assert EvidenceCategory.WEATHER in result.evidence_requirements, "Should require WEATHER evidence"
    print("✓ test_classifier_weather_query passed")


def test_classifier_research_query():
    """Test classifier with research query."""
    classifier = RequestClassifier()
    
    result = classifier.classify("Research the history of Rome")
    
    assert result.primary_routing == RoutingCategory.RESEARCH, f"Expected RESEARCH, got {result.primary_routing}"
    print("✓ test_classifier_research_query passed")


def test_classifier_factual_query():
    """Test classifier with factual query.
    
    Note: "who is" is classified as LOCAL because it's a common factual question
    that can be answered with local context or cached data.
    For questions requiring external evidence, use specific data queries like "population".
    """
    classifier = RequestClassifier()
    
    result = classifier.classify("Who is the president of Italy?")
    
    # "who is" is classified as LOCAL due to BASIC keyword matching
    # This is acceptable for simple factual questions
    assert result.primary_routing == RoutingCategory.LOCAL, f"Expected LOCAL, got {result.primary_routing}"
    print("✓ test_classifier_factual_query passed")


def test_classifier_calculation():
    """Test classifier with calculation query."""
    classifier = RequestClassifier()
    
    result = classifier.classify("Calculate 25 * 4 + 10")
    
    assert result.primary_routing == RoutingCategory.LOCAL, f"Expected LOCAL, got {result.primary_routing}"
    print("✓ test_classifier_calculation passed")


def run_all_tests():
    """Run all classifier tests."""
    tests = [
        test_classifier_basic_time,
        test_classifier_weather_query,
        test_classifier_research_query,
        test_classifier_factual_query,
        test_classifier_calculation,
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
    
    print(f"\n=== Classifier Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
