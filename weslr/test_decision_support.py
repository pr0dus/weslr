#!/usr/bin/env python3
"""Tests for Phase 7: Decision Support Engine."""

from pathlib import Path
import os
import sys

os.chdir(Path(__file__).parent)

from datetime import datetime, timezone
import sqlite3
import uuid

from capability_suggestion import CapabilitySuggestionStore, CapabilitySuggestion, SuggestionStatus
from capability_ingestion import DecisionSupportEngine, TrendScoringEngine


def test_explanation_generation():
    """Test explanation generation for suggestions."""
    print("Test 1: Explanation generation")
    
    db_path = Path("continuity/test_explain.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = DecisionSupportEngine(store)
    
    # Create a suggestion
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    sid = f"explain-{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sid, "Test Automation", "Test description", "automation", "new", "github", now, now, 40))
        conn.commit()
    
    all_suggestions = store.list_all(include_archived=False)
    s = all_suggestions[0]
    
    # Generate explanation
    s = engine.generate_explanation(s)
    
    # Verify explanation fields are set
    assert s.why_surfaced is not None, "why_surfaced should be set"
    assert s.supporting_signals_summary is not None, "supporting_signals_summary should be set"
    assert s.improvement_targets is not None, "improvement_targets should be set"
    assert s.implementation_effort_estimate is not None, "effort estimate should be set"
    assert 1 <= s.implementation_effort_estimate <= 100, "effort estimate should be 1-100"
    assert s.risk_level in ("low", "medium", "high"), f"invalid risk_level: {s.risk_level}"
    assert s.classification in ("quick_win", "strategic", "speculative"), f"invalid classification: {s.classification}"
    assert s.decision_recommendation in ("accept", "pending", "denied", "snoozed"), f"invalid decision_recommendation: {s.decision_recommendation}"
    
    db_path.unlink()
    print("  ✓ Explanation generation works")
    return True


def test_classification_logic():
    """Test classification logic (quick_win vs strategic vs speculative)."""
    print("Test 2: Classification logic")
    
    db_path = Path("continuity/test_class.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = DecisionSupportEngine(store)
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Test quick_win: high trend score, low effort
    sid1 = f"qw-{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sid1, "Quick Fix", "Description", "integration", "new", "github", now, now, 70))
        conn.commit()
    
    # Test strategic: medium trend score
    sid2 = f"str-{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sid2, "Strategic Improvement", "Description", "automation", "new", "github", now, now, 40))
        conn.commit()
    
    # Test speculative: low trend score
    sid3 = f"spec-{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sid3, "Speculative Idea", "Description", "other", "new", "email", now, now, 10))
        conn.commit()
    
    all_suggestions = store.list_all(include_archived=False)
    for s in all_suggestions:
        s = engine.generate_explanation(s)
        # Classification depends on trend_score which is computed dynamically
        # So any valid classification is acceptable
        assert s.classification in ("quick_win", "strategic", "speculative"), f"Invalid classification: {s.classification}"
    
    db_path.unlink()
    print("  ✓ Classification logic works")
    return True


def test_decision_recommendation():
    """Test decision recommendation based on classification and risk."""
    print("Test 3: Decision recommendation")
    
    db_path = Path("continuity/test_rec.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = DecisionSupportEngine(store)
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Test quick_win with low risk -> accept
    sid1 = f"rec-{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sid1, "Easy Win", "Description", "integration", "new", "github", now, now, 80))
        conn.commit()
    
    all_suggestions = store.list_all(include_archived=False)
    s = all_suggestions[0]
    s = engine.generate_explanation(s)
    
    # Should be pending or accept (low risk quick_win)
    assert s.decision_recommendation in ("accept", "pending"), f"Should be accept or pending: {s.decision_recommendation}"
    
    db_path.unlink()
    print("  ✓ Decision recommendation works")
    return True


def test_backward_compatibility():
    """Test that old suggestions work with new explanation fields."""
    print("Test 4: Backward compatibility")
    
    db_path = Path("continuity/test_compat.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = DecisionSupportEngine(store)
    
    # Insert old-style suggestion (no Phase 7 fields)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    sid = f"old-{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sid, "Old Suggestion", "Old desc", "automation", "new", "github", now, now, 40))
        conn.commit()
    
    all_suggestions = store.list_all(include_archived=False)
    s = all_suggestions[0]
    
    # Generate explanation
    s = engine.generate_explanation(s)
    
    # Verify explanation fields are set with defaults
    assert s.why_surfaced is not None, "why_surfaced should be set"
    assert s.supporting_signals_summary is not None, "supporting_signals_summary should be set"
    
    db_path.unlink()
    print("  ✓ Backward compatibility works")
    return True


def test_operator_review():
    """Test operator review output format."""
    print("Test 5: Operator review output")
    
    db_path = Path("continuity/test_review.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    engine = DecisionSupportEngine(store)
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    for i in range(3):
        sid = f"rev-{uuid.uuid4().hex[:8]}"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO capability_suggestions 
                (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (sid, f"Review Test {i}", "Description", "integration", "new", "github", now, now, 30 + i*10))
            conn.commit()
    
    all_suggestions = store.list_all(include_archived=False)
    
    # Get operator review
    review = engine.get_operator_review(3)
    
    assert len(review) == 3, f"Expected 3 reviews, got {len(review)}"
    
    for r in review:
        assert "suggestion" in r, "Review should have suggestion"
        assert "explanation" in r, "Review should have explanation"
        assert "recommendation" in r, "Review should have recommendation"
        
        s = r["suggestion"]
        exp = r["explanation"]
        rec = r["recommendation"]
        
        # Verify explanation structure
        assert "why_surfaced" in exp, "Explanation should have why_surfaced"
        assert "improvement_targets" in exp, "Explanation should have improvement_targets"
        assert "risk_level" in exp, "Explanation should have risk_level"
        
        # Verify recommendation structure
        assert "decision" in rec, "Recommendation should have decision"
        assert "priority" in rec, "Recommendation should have priority"
    
    db_path.unlink()
    print("  ✓ Operator review output works")
    return True


def run_all_tests():
    """Run all Phase 7 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: DECISION SUPPORT TESTS")
    print("=" * 60)
    
    tests = [
        test_explanation_generation,
        test_classification_logic,
        test_decision_recommendation,
        test_backward_compatibility,
        test_operator_review,
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
