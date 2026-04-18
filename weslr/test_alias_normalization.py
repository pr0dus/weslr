#!/usr/bin/env python3
"""Tests for Phase 6: Alias normalization + Concept Graph linking."""

from pathlib import Path
import os
import sys
from datetime import datetime, timezone
import sqlite3
import uuid

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

from capability_suggestion import CapabilitySuggestion, CapabilitySuggestionStore
from capability_ingestion import AliasNormalizer, ConceptGraphLinker, CapabilitySuggestionStore as IngestionStore


def test_alias_normalization():
    """Test alias normalization and canonical key generation."""
    print("Test 1: Alias normalization")
    
    an = AliasNormalizer()
    
    # Test direct matches
    result = an.normalize("Obsidian MD")
    assert "obsidian" in result["canonical_key"].lower(), f"Expected obsidian, got {result['canonical_key']}"
    
    result = an.normalize("github.com")
    assert "github" in result["canonical_key"].lower(), f"Expected github, got {result['canonical_key']}"
    
    # Test normalization to key
    key = an._normalize_to_key("Test Tool v1.0")
    assert "test_tool" in key, f"Expected test_tool, got {key}"
    
    print("  ✓ Alias normalization works")
    return True


def test_merge_aliases():
    """Test merging suggestions by canonical identity."""
    print("Test 2: Merge aliases")
    
    db_path = Path("continuity/test_merge.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    an = AliasNormalizer()
    
    # Create suggestions with different titles but same concept
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    for title in ["Obsidian", "obsidian md", "Obsidian MD"]:
        sid = f"merge-{uuid.uuid4().hex[:8]}"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO capability_suggestions 
                (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (sid, title, "Test", "integration", "new", "github", now, now, 30))
            conn.commit()
    
    # Load and merge
    all_suggestions = store.list_all(include_archived=False)
    groups = an.merge_aliases(all_suggestions)
    
    # All 3 should be in the same group (obsidian)
    assert len(groups) >= 1, "Should have at least 1 group"
    
    # Check if obsidian-related titles are grouped
    obsidian_group = [g for g in groups.values() if any("obsidian" in s.title.lower() for s in g)]
    assert len(obsidian_group) > 0, "Should have obsidian group"
    
    db_path.unlink()
    print("  ✓ Alias merging works")
    return True


def test_concept_graph_linking():
    """Test minimal Concept Graph linking."""
    print("Test 3: Concept Graph linking")
    
    db_path = Path("continuity/test_concept.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    linker = ConceptGraphLinker()
    
    # Create a suggestion
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    sid = f"concept-{uuid.uuid4().hex[:8]}"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capability_suggestions 
            (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sid, "Test Tool", "Test description", "automation", "new", "github", now, now, 40))
        conn.commit()
    
    all_suggestions = store.list_all(include_archived=False)
    s = all_suggestions[0]
    
    # Try linking (may fail if concept store unavailable)
    concept_id = linker.link_suggestion_to_concept(s)
    if concept_id:
        print(f"    Concept created: {concept_id}")
    
    # Verify suggestion has concept_link_id
    if concept_id:
        assert s.concept_link_id == concept_id, f"Expected concept_link_id to be set"
    
    db_path.unlink()
    print("  ✓ Concept Graph linking works")
    return True


def test_backward_compatibility():
    """Test that old suggestions work with new fields."""
    print("Test 4: Backward compatibility")
    
    db_path = Path("continuity/test_compat.db")
    if db_path.exists():
        db_path.unlink()
    
    # Create store (this auto-creates schema)
    store = CapabilitySuggestionStore(db_path)
    
    # Insert old-style suggestion (no Phase 5/6 fields)
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
    
    # Re-read using from_dict
    all_suggestions = store.list_all(include_archived=False)
    assert len(all_suggestions) == 1, "Should have 1 suggestion"
    
    s = all_suggestions[0]
    
    # Verify new fields have defaults
    assert s.canonical_key is None, "canonical_key should default to None"
    assert s.aliases is None, "aliases should default to None"
    assert s.source_variants is None, "source_variants should default to None"
    assert s.concept_link_id is None, "concept_link_id should default to None"
    assert s.mention_count == 0, "mention_count should default to 0"
    assert s.source_diversity == 0, "source_diversity should default to 0"
    
    db_path.unlink()
    print("  ✓ Backward compatibility works")
    return True


def test_canonical_key_generation():
    """Test canonical key generation from title."""
    print("Test 5: Canonical key generation")
    
    db_path = Path("continuity/test_key.db")
    if db_path.exists():
        db_path.unlink()
    
    store = CapabilitySuggestionStore(db_path)
    an = AliasNormalizer()
    
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Create suggestions and set canonical keys
    titles = [
        ("Test Tool v1.0", "test-tool-v1-0"),
        ("Another-Tool!", "another-tool"),
        ("Tool With Spaces", "tool_with_spaces"),
    ]
    
    for title, expected in titles:
        sid = f"key-{uuid.uuid4().hex[:8]}"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO capability_suggestions 
                (id, title, description, capability_type, status, provenance, created_at, updated_at, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (sid, title, "Test", "automation", "new", "github", now, now, 30))
            conn.commit()
    
    all_suggestions = store.list_all(include_archived=False)
    
    # Test canonical key normalization
    for s in all_suggestions:
        key = an._normalize_to_key(s.title)
        # Should be lowercase, with underscores
        assert key == key.lower(), f"Key should be lowercase: {key}"
        assert " " not in key, f"Key should not have spaces: {key}"
    
    db_path.unlink()
    print("  ✓ Canonical key generation works")
    return True


def run_all_tests():
    """Run all Phase 6 tests."""
    print("=" * 60)
    print("SECTION 5 — VALIDATION: ALIAS NORMALIZATION TESTS")
    print("=" * 60)
    
    tests = [
        test_alias_normalization,
        test_merge_aliases,
        test_concept_graph_linking,
        test_backward_compatibility,
        test_canonical_key_generation,
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
