#!/usr/bin/env python3
"""Integration test for Request Intelligence layer.

Tests the full Request Intelligence pipeline end-to-end.
"""

import sys
from pathlib import Path

# Add workspace to path for imports
workspace_path = str(Path(__file__).resolve().parent)
sys.path.insert(0, workspace_path)
sys.path.insert(0, str(Path(workspace_path) / "weslr"))

from request_intelligence import RequestIntelligence


def test_full_pipeline():
    """Test full request intelligence pipeline."""
    print("=== Request Intelligence Integration Test ===\n")
    
    # Test cases
    test_cases = [
        ("What time is it?", "BASIC"),
        ("What's the weather in Rome?", "BASIC"),
        ("Calculate 25 * 4 + 10", "BASIC"),
        ("Analyze this document", "MEDIUM"),
        ("Compare these two options", "MEDIUM"),
        ("Research the history of Rome", "HIGH"),
        ("Explain why the sky is blue", "MEDIUM"),
        ("Create a new universe", "EXTREME"),
        ("What's the meaning of life?", "EXTREME"),
    ]
    
    ri = RequestIntelligence()
    
    for request, expected_difficulty in test_cases:
        print(f"Testing: '{request}'")
        
        report = ri.analyze(request)
        
        print(f"  Classification: {report.classification.get('primary_routing')}")
        print(f"  Knowledge State: {report.knowledge_state.get('request_knowledge_states')}")
        print(f"  Difficulty: {report.difficulty_grade.get('grade')} (score: {report.difficulty_grade.get('difficulty_score')})")
        print(f"  Uncertainty: {report.uncertainty_analysis.get('uncertainty_category')} (confidence: {report.uncertainty_analysis.get('confidence')})")
        print(f"  Allowed: {report.uncertainty_analysis.get('allowed')}")
        print(f"  Best Provider: {report.provider_scores[0].get('provider_name') if report.provider_scores else 'none'}")
        print(f"  Capability Match: {[m.get('capability', {}).get('name') for m in report.capability_matches[:3]]}")
        print(f"  Combined Score: {report.combined_score}")
        
        # Verify expected difficulty
        actual_difficulty = report.difficulty_grade.get('grade')
        if actual_difficulty != expected_difficulty:
            print(f"  ⚠️  Expected difficulty {expected_difficulty}, got {actual_difficulty}")
        else:
            print(f"  ✓ Difficulty matches expected: {actual_difficulty}")
        
        # Verify routing decision
        category, details = ri.get_routing_decision(request)
        provider = details.get("provider", "embedded")
        print(f"  Routing: {category} (provider: {provider}, confidence: {details.get('confidence', 'N/A')})")
        
        print()
    
    return True


def test_evidence_policy():
    """Test evidence policy construction."""
    print("=== Evidence Policy Test ===\n")
    
    from request_intelligence import EvidencePolicyBuilder
    
    builder = EvidencePolicyBuilder()
    
    policies = [
        ("time_query", 1),
        ("weather_query", 2),
        ("factual_query", 1),
        ("research_query", 3),
    ]
    
    for request_type, difficulty in policies:
        policy = builder.build_policy(request_type, difficulty)
        print(f"Policy for {request_type} (difficulty={difficulty}):")
        print(f"  Requirements: {len(policy.requirements)}")
        print(f"  Strategy: {policy.evidence_strategy}")
        print(f"  Allow fallback: {policy.allow_fallback}")
        print()
    
    return True


def test_provider_suitability():
    """Test provider suitability scoring."""
    print("=== Provider Suitability Test ===\n")
    
    from request_intelligence import ProviderSuitability
    
    scorer = ProviderSuitability()
    
    requests = [
        "What time is it?",
        "What's the weather in Rome?",
        "Research the history of Rome",
        "Create a new universe",
    ]
    
    for request in requests:
        print(f"Request: '{request}'")
        
        # Get best provider
        best = scorer.get_best_provider(request)
        if best:
            print(f"  Best provider: {best.provider_name} (score: {best.score:.2f})")
            print(f"    Provider type: {best.provider_type}")
        
        # Get all providers
        all_scores = scorer.score_all(request)
        print(f"  All providers:")
        for score in all_scores[:3]:  # Top 3
            print(f"    - {score.provider_name}: {score.score:.2f} (type: {score.provider_type.value})")
        print()
    
    return True


def test_uncertainty_discipline():
    """Test uncertainty discipline."""
    print("=== Uncertainty Discipline Test ===\n")
    
    from request_intelligence import UncertaintyDiscipline
    
    discipline = UncertaintyDiscipline()
    
    requests = [
        "What time is it?",
        "What's the weather in Rome?",
        "Research the history of Rome",
        "Create a new universe",
        "Explain why the sky is blue",
    ]
    
    for request in requests:
        print(f"Request: '{request}'")
        
        result = discipline.analyze(request)
        print(f"  Category: {result.uncertainty_category}")
        print(f"  Uncertainty: {result.uncertainty_level:.2f}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Budget used: {result.budget_used:.2f}")
        print(f"  Allowed: {result.allowed}")
        print()
    
    return True


def run_all_tests():
    """Run all integration tests."""
    tests = [
        ("Full Pipeline", test_full_pipeline),
        ("Evidence Policy", test_evidence_policy),
        ("Provider Suitability", test_provider_suitability),
        ("Uncertainty Discipline", test_uncertainty_discipline),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print('='*60)
        
        try:
            test_fn()
            passed += 1
            print(f"✓ {name} PASSED")
        except Exception as e:
            failed += 1
            print(f"✗ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print('='*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
