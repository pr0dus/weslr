#!/usr/bin/env python3
"""Tests for Self-Architecture Core v4: Comparison and Tradeoff Engine."""

from pathlib import Path
import os
import sys

os.chdir(Path(__file__).parent)

from self_architecture import (
    TradeoffEngine,
    ComparisonOption,
    ComparisonResult,
)


def test_comparison_option_creation():
    """Test that comparison options can be created."""
    print("Test 1: Comparison option creation")
    
    opt = ComparisonOption(
        id='test-opt',
        title='Test improvement',
        description='A test option',
        affected_subsystems=['state', 'continuity'],
        risk='low',
        effort=30,
        strategic_value='moderate',
    )
    
    assert opt.id == 'test-opt'
    assert opt.title == 'Test improvement'
    assert 'state' in opt.affected_subsystems
    assert opt.risk == 'low'
    assert opt.effort == 30
    assert opt.strategic_value == 'moderate'
    assert opt.is_quick_win is False
    assert opt.is_strategic is False
    
    print("  ✓ Comparison option creation works")
    return True


def test_comparison_result_creation():
    """Test that comparison results can be created."""
    print("Test 2: Comparison result creation")
    
    opt1 = ComparisonOption(id='opt1', title='Option 1', description='First option')
    opt2 = ComparisonOption(id='opt2', title='Option 2', description='Second option')
    
    result = ComparisonResult(
        comparison_id='compare-001',
        options=[opt1, opt2],
        winner_id='opt1',
        winner_title='Option 1',
        tradeoff_summary='Option 1 is better',
        recommendation_timing='now',
    )
    
    assert result.comparison_id == 'compare-001'
    assert len(result.options) == 2
    assert result.winner_id == 'opt1'
    assert result.winner_title == 'Option 1'
    assert result.tradeoff_summary == 'Option 1 is better'
    assert result.recommendation_timing == 'now'
    
    print("  ✓ Comparison result creation works")
    return True


def test_to_dict_from_dict():
    """Test serialization/deserialization."""
    print("Test 3: Serialization/deserialization")
    
    opt = ComparisonOption(
        id='opt1',
        title='Test',
        description='Test option',
        affected_subsystems=['state'],
        risk='high',
        strategic_value='high',
        is_quick_win=True,
        is_strategic=False,
    )
    
    # Serialize
    data = opt.to_dict()
    assert data['id'] == 'opt1'
    assert data['title'] == 'Test'
    assert data['risk'] == 'high'
    assert data['is_quick_win'] is True
    
    # Deserialize
    opt2 = ComparisonOption.from_dict(data)
    assert opt2.id == 'opt1'
    assert opt2.title == 'Test'
    assert opt2.risk == 'high'
    assert opt2.is_quick_win is True
    
    print("  ✓ Serialization/deserialization works")
    return True


def test_tradeoff_engine_basic():
    """Test basic tradeoff engine functionality."""
    print("Test 4: Tradeoff engine basic functionality")
    
    opt1 = ComparisonOption(
        id='quick-win',
        title='Quick Fix',
        description='Small improvement',
        affected_subsystems=['state'],
        risk='low',
        implementation_effort=20,
        is_quick_win=True,
        strategic_value='moderate',
    )
    
    opt2 = ComparisonOption(
        id='strategic',
        title='Strategic Rewrite',
        description='Major refactor',
        affected_subsystems=['state', 'continuity'],
        risk='medium',
        implementation_effort=60,
        is_strategic=True,
        strategic_value='high',
    )
    
    engine = TradeoffEngine()
    result = engine.compare_options([opt1, opt2])
    
    # Check result structure
    assert result.comparison_id is not None
    assert len(result.options) == 2
    assert result.winner_id is not None
    assert result.tradeoff_summary != ""
    assert result.recommendation_timing in ('now', 'later', 'pending')
    
    # Check metrics
    assert result.best_for_quick_wins is not None
    assert result.best_for_strategic is not None
    assert result.lowest_risk is not None
    assert result.highest_value is not None
    
    print("  ✓ Tradeoff engine basic functionality works")
    return True


def test_tradeoff_engine_multiple_options():
    """Test tradeoff engine with more than two options."""
    print("Test 5: Multiple options comparison")
    
    options = [
        ComparisonOption(
            id='opt1',
            title='Option 1',
            description='Low effort',
            affected_subsystems=['state'],
            risk='low',
            implementation_effort=20,
            is_quick_win=True,
        ),
        ComparisonOption(
            id='opt2',
            title='Option 2',
            description='Balanced',
            affected_subsystems=['state', 'continuity'],
            risk='medium',
            implementation_effort=50,
            strategic_value='moderate',
        ),
        ComparisonOption(
            id='opt3',
            title='Option 3',
            description='Strategic',
            affected_subsystems=['state', 'continuity', 'file_ingestion'],
            risk='medium',
            implementation_effort=70,
            is_strategic=True,
            strategic_value='high',
        ),
    ]
    
    engine = TradeoffEngine()
    result = engine.compare_options(options)
    
    assert len(result.options) == 3
    assert result.winner_id is not None
    assert 'why_option_a_beats_b' in result.__dict__
    
    print("  ✓ Multiple options comparison works")
    return True


def test_tradeoff_engine_single_option():
    """Test tradeoff engine with single option."""
    print("Test 6: Single option comparison")
    
    opt = ComparisonOption(
        id='only-option',
        title='Only Option',
        description='Only option available',
        affected_subsystems=['state'],
        risk='low',
        strategic_value='moderate',
    )
    
    engine = TradeoffEngine()
    result = engine.compare_options([opt])
    
    assert len(result.options) == 1
    assert result.winner_id == 'only-option'
    assert 'Only one option' in result.tradeoff_summary
    
    print("  ✓ Single option comparison works")
    return True


def test_tradeoff_engine_empty_options():
    """Test tradeoff engine with no options."""
    print("Test 7: Empty options comparison")
    
    engine = TradeoffEngine()
    result = engine.compare_options([])
    
    assert len(result.options) == 0
    assert result.tradeoff_summary == "No options to compare"
    
    print("  ✓ Empty options comparison works")
    return True


def test_comparison_output_format():
    """Test operator-facing comparison output format."""
    print("Test 8: Comparison output format")
    
    opt1 = ComparisonOption(
        id='opt1',
        title='Option 1',
        description='First option',
        affected_subsystems=['state'],
        risk='low',
        implementation_effort=30,
        is_quick_win=True,
    )
    
    opt2 = ComparisonOption(
        id='opt2',
        title='Option 2',
        description='Second option',
        affected_subsystems=['state', 'continuity'],
        risk='high',
        implementation_effort=70,
        is_strategic=True,
        strategic_value='high',
    )
    
    engine = TradeoffEngine()
    result = engine.compare_options([opt1, opt2])
    output = engine.get_comparison_output(result)
    
    # Check output structure
    assert 'comparison_id' in output
    assert 'options' in output
    assert 'winner' in output
    assert 'tradeoff_summary' in output
    assert 'recommendation_timing' in output
    assert 'comparison_details' in output
    assert 'tradeoff_reasons' in output
    
    # Check winner structure
    assert 'id' in output['winner']
    assert 'title' in output['winner']
    
    # Check comparison details
    details = output['comparison_details']
    assert 'best_for_quick_wins' in details
    assert 'best_for_strategic' in details
    assert 'lowest_risk' in details
    assert 'highest_value' in details
    
    print("  ✓ Comparison output format works")
    return True


def test_tradeoff_reasoning():
    """Test that tradeoff reasoning is generated."""
    print("Test 9: Tradeoff reasoning")
    
    opt1 = ComparisonOption(
        id='opt1',
        title='Option 1',
        description='First option',
        affected_subsystems=['state'],
        risk='low',
        implementation_effort=30,
        is_quick_win=True,
        strategic_value='moderate',
    )
    
    opt2 = ComparisonOption(
        id='opt2',
        title='Option 2',
        description='Second option',
        affected_subsystems=['state', 'continuity'],
        risk='high',
        implementation_effort=70,
        is_strategic=True,
        strategic_value='high',
    )
    
    engine = TradeoffEngine()
    result = engine.compare_options([opt1, opt2])
    
    # Check that tradeoff reasons exist
    assert len(result.why_option_a_beats_b) > 0
    
    # Check format of reasons
    for key, reason in result.why_option_a_beats_b.items():
        assert isinstance(key, str)
        assert isinstance(reason, str)
        assert len(reason) > 0
    
    print("  ✓ Tradeoff reasoning works")
    return True


def test_consistent_ranking():
    """Test that ranking is consistent across runs."""
    print("Test 10: Consistent ranking")
    
    opt1 = ComparisonOption(
        id='opt1',
        title='Option 1',
        description='First option',
        affected_subsystems=['state'],
        risk='low',
        implementation_effort=30,
        is_quick_win=True,
        strategic_value='moderate',
    )
    
    opt2 = ComparisonOption(
        id='opt2',
        title='Option 2',
        description='Second option',
        affected_subsystems=['state', 'continuity'],
        risk='high',
        implementation_effort=70,
        is_strategic=True,
        strategic_value='high',
    )
    
    engine = TradeoffEngine()
    
    # Run twice
    result1 = engine.compare_options([opt1, opt2])
    result2 = engine.compare_options([opt1, opt2])
    
    # Results should be consistent
    assert result1.winner_id == result2.winner_id
    assert result1.tradeoff_summary == result2.tradeoff_summary
    assert result1.recommendation_timing == result2.recommendation_timing
    
    print("  ✓ Consistent ranking works")
    return True


def test_fallback_behavior():
    """Test fallback behavior with missing fields."""
    print("Test 11: Fallback behavior")
    
    # Options with minimal fields
    opt1 = ComparisonOption(
        id='minimal',
        title='Minimal',
        description='A',
    )
    
    opt2 = ComparisonOption(
        id='minimal2',
        title='Minimal2',
        description='B',
    )
    
    engine = TradeoffEngine()
    result = engine.compare_options([opt1, opt2])
    
    # Should still produce valid result
    assert result.comparison_id is not None
    assert result.winner_id is not None
    assert result.tradeoff_summary != ""
    
    print("  ✓ Fallback behavior works")
    return True


def test_backwards_compatibility():
    """Test that existing functionality is not broken."""
    print("Test 12: Backwards compatibility")
    
    # Ensure old classes still work
    from self_architecture import SelfArchitecture, Subsystem, SubsystemType
    from datetime import datetime, timezone
    
    arch = SelfArchitecture()
    arch.register_subsystem(Subsystem(
        name='state',
        description='State management',
        subsystem_type=SubsystemType.STATE.value,
    ))
    
    assert 'state' in arch.subsystems
    assert arch.subsystems['state'].name == 'state'
    
    print("  ✓ Backwards compatibility works")
    return True


def run_all_tests():
    """Run all Self-Architecture v4 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: SELF-ARCHITECTURE CORE V4 TESTS")
    print("=" * 60)
    
    tests = [
        test_comparison_option_creation,
        test_comparison_result_creation,
        test_to_dict_from_dict,
        test_tradeoff_engine_basic,
        test_tradeoff_engine_multiple_options,
        test_tradeoff_engine_single_option,
        test_tradeoff_engine_empty_options,
        test_comparison_output_format,
        test_tradeoff_reasoning,
        test_consistent_ranking,
        test_fallback_behavior,
        test_backwards_compatibility,
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
