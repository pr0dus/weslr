#!/usr/bin/env python3
"""Tests for Phase 5: Trend scoring engine."""

from pathlib import Path
import os
import sys

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

from datetime import datetime, timezone
import uuid

from capability_ingestion import (
    CapabilitySuggestionStore,
    TrendScoringEngine,
    CapabilitySuggestion,
    SuggestionStatus,
    CapabilityType,
    SourceProvenance,
    SourceSignal,
    SourceKind,
)
from capability_suggestion import CapabilitySuggestion as CapSuggestion


def test_trend_scoring_basic():
    """Test basic trend scoring functionality."""
    print("Test 1: Basic trend scoring")
    
    # Create temp store
    db_path = Path("continuity/test_basic.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = TrendScoringEngine(store)
    
    # Create a suggestion
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    s = CapabilitySuggestion(
        id=f"test-{uuid.uuid4().hex[:8]}",
        title="Test automation",
        description="Automate workflows",
        capability_type=CapabilityType.AUTOMATION,
        status=SuggestionStatus.NEW,
        provenance=SourceProvenance.GITHUB,
        created_at=now,
        updated_at=now,
        priority=40,
    )
    
    # Update trend metrics
    engine.update_trend_metrics(s)
    
    # Verify metrics
    assert s.last_seen is not None, "last_seen should be set"
    assert s.science_relevance_score is not None, "science_relevance_score should be set"
    assert s.science_relevance_score > 0, "science_relevance_score should be > 0"
    
    # Compute trend score
    score_data = engine.compute_trend_score(s)
    
    assert "trend_score" in score_data, "trend_score should be present"
    assert "rank_explanation" in score_data, "rank_explanation should be present"
    assert "confidence" in score_data, "confidence should be present"
    assert 0 <= score_data["trend_score"] <= 100, "trend_score should be 0-100"
    
    db_path.unlink()
    print("  ✓ Basic scoring works")
    return True


def test_source_diversity():
    """Test source diversity counting."""
    print("Test 2: Source diversity counting")
    
    db_path = Path("continuity/test_diversity.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = TrendScoringEngine(store)
    
    # Insert suggestions from different provenances
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    for i, prov in enumerate([SourceProvenance.GITHUB, SourceProvenance.REDDIT, SourceProvenance.EMAIL]):
        s = CapabilitySuggestion(
            id=f"div-{uuid.uuid4().hex[:8]}",
            title=f"Diversity Test {i}",
            description=f"Test {i}",
            capability_type=CapabilityType.OTHER,
            status=SuggestionStatus.NEW,
            provenance=prov,
            created_at=now,
            updated_at=now,
            priority=30,
        )
        store.create(s)
    
    # Count diversity
    all_suggestions = store.list_all(include_archived=False)
    diversity = engine._count_source_diversity(all_suggestions)
    
    assert diversity == 3, f"Expected 3 provenances, got {diversity}"
    
    db_path.unlink()
    print("  ✓ Source diversity counting works")
    return True


def test_global_diversity_in_score():
    """Test that global diversity affects trend scores."""
    print("Test 3: Global diversity affects scores")
    
    db_path = Path("continuity/test_global.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = TrendScoringEngine(store)
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Create 3 suggestions from 3 different provenances
    provenances = [SourceProvenance.GITHUB, SourceProvenance.REDDIT, SourceProvenance.EMAIL]
    suggestions = []
    for i, prov in enumerate(provenances):
        s = CapabilitySuggestion(
            id=f"global-{uuid.uuid4().hex[:8]}",
            title=f"Global Test {i}",
            description=f"Test {i}",
            capability_type=CapabilityType.OTHER,
            status=SuggestionStatus.NEW,
            provenance=prov,
            created_at=now,
            updated_at=now,
            priority=30,
        )
        store.create(s)
        suggestions.append(s)
    
    # Score with global diversity
    global_diversity = engine._count_source_diversity(suggestions)
    assert global_diversity == 3, f"Expected global diversity 3, got {global_diversity}"
    
    for s in suggestions:
        engine.update_trend_metrics(s)
        score_data = engine.compute_trend_score(s, global_diversity)
        
        # With 3 provenances, diversity component should be 75 (3 * 25)
        assert score_data["trend_score"] > 50, f"Score should be > 50 with 3 provenances, got {score_data['trend_score']}"
    
    db_path.unlink()
    print("  ✓ Global diversity affects scores correctly")
    return True


def test_backward_compatibility():
    """Test that old suggestions without trend fields still work."""
    print("Test 4: Backward compatibility")
    
    db_path = Path("continuity/test_compat.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    
    # Manually insert old-style suggestion (no trend fields)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    import sqlite3
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"old-{uuid.uuid4().hex[:8]}",
            "Old Suggestion",
            "Old description",
            "automation",
            "new",
            "github",
            now,
            now,
            40
        ))
        conn.commit()
    
    # Re-read using from_dict (simulates loading from DB)
    all_suggestions = store.list_all(include_archived=False)
    assert len(all_suggestions) == 1
    
    s = all_suggestions[0]
    
    # Verify new fields have defaults
    assert s.mention_count == 0, "mention_count should default to 0"
    assert s.source_diversity == 0, "source_diversity should default to 0"
    assert s.last_seen is None, "last_seen should default to None"
    assert s.first_seen is None, "first_seen should default to None"
    
    # Test that scoring works with old suggestion
    engine = TrendScoringEngine(store)
    engine.update_trend_metrics(s)
    
    # Update some fields during processing
    assert s.last_seen is not None, "last_seen should be set after update"
    
    db_path.unlink()
    print("  ✓ Backward compatibility works")
    return True


def test_get_top_trending():
    """Test get_top_trending returns sorted results."""
    print("Test 5: Get top trending")
    
    db_path = Path("continuity/test_top.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = TrendScoringEngine(store)
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    provenances = [SourceProvenance.GITHUB, SourceProvenance.REDDIT]
    
    # Create suggestions with different priorities
    for i, priority in enumerate([20, 50, 30]):
        s = CapabilitySuggestion(
            id=f"top-{uuid.uuid4().hex[:8]}",
            title=f"Top Test {i}",
            description=f"Test {i}",
            capability_type=CapabilityType.OTHER,
            status=SuggestionStatus.NEW,
            provenance=provenances[i % 2],
            created_at=now,
            updated_at=now,
            priority=priority,
        )
        store.create(s)
    
    # Get top trending
    top = engine.get_top_trending(2)
    
    assert len(top) == 2, f"Expected 2 results, got {len(top)}"
    # Should be sorted by trend_score descending
    assert top[0].trend_score >= top[1].trend_score, "Results should be sorted by trend_score descending"
    
    db_path.unlink()
    print("  ✓ Get top trending works")
    return True


def run_all_tests():
    """Run all Phase 5 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: TREND SCORING ENGINE TESTS")
    print("=" * 60)
    
    tests = [
        test_trend_scoring_basic,
        test_source_diversity,
        test_global_diversity_in_score,
        test_backward_compatibility,
        test_get_top_trending,
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
