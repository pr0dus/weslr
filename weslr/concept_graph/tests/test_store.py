"""Tests for Concept Graph Store and Index.

Tests:
- Save/load concepts
- Save/load links
- Index creation
- Index derived backlinks
- Session handling
"""

import sys
from pathlib import Path

# Add workspace to path for imports
workspace = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, workspace)
sys.path.insert(0, str(Path(workspace) / "weslr"))

import tempfile
import shutil

from concept_graph import Concept, Link, Evidence
from concept_graph import store, index
import time as time_module


def test_concept_save_load():
    """Test saving and loading a concept."""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create store with temp directory
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        # Create concept
        concept = Concept(
            id="test-001",
            name="Test Concept",
            type="concept",
            description="A test concept",
            tags=["test"],
        )
        
        # Save
        s.save_concept(concept)
        
        # Load
        loaded = s.load_concept("test-001")
        
        assert loaded is not None
        assert loaded.id == "test-001"
        assert loaded.name == "Test Concept"
        assert "test" in loaded.tags
        
        print("✓ test_concept_save_load passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_link_save_load():
    """Test saving and loading a link."""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create store with temp directory
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        # Create evidence and link
        evidence = Evidence(
            source_id="msg-001",
            source_type="message",
            content="Supporting evidence",
            confidence=0.9,
            timestamp=int(time_module.time()),
            category="source-backed",
        )
        
        link = Link(
            source_id="concept-A",
            target_id="concept-B",
            link_type="related_to",
            confidence=0.85,
            reason="Related by topic",
            evidence=[evidence],
            created_at=int(time_module.time()),
            updated_at=int(time_module.time()),
        )
        
        # Save
        s.save_link(link)
        
        # Load
        loaded = s.load_link("concept-A", "concept-B", "related_to")
        
        assert loaded is not None
        assert loaded.source_id == "concept-A"
        assert loaded.target_id == "concept-B"
        assert loaded.link_type == "related_to"
        
        print("✓ test_link_save_load passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_index_creation():
    """Test index creation from concepts and links."""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create store with temp directory
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        # Create concepts and links
        c1 = Concept(id="c1", name="Concept A", type="concept")
        c2 = Concept(id="c2", name="Concept B", type="concept")
        
        evidence = Evidence(
            source_id="msg-001",
            source_type="message",
            content="Link evidence",
            confidence=0.9,
            timestamp=int(time_module.time()),
            category="inferred",
        )
        
        link = Link(
            source_id="c1",
            target_id="c2",
            link_type="related_to",
            confidence=0.85,
            reason="Related",
            evidence=[evidence],
            created_at=int(time_module.time()),
            updated_at=int(time_module.time()),
        )
        
        # Save
        s.save_concept(c1)
        s.save_concept(c2)
        s.save_link(link)
        
        # Load
        s.load()
        
        # Create index
        idx = index.ConceptGraphIndex()
        idx_data = idx.build_full_index(
            list(s._concept_cache.values()),
            list(s._link_cache.values()),
        )
        
        # Verify basic structure
        assert "by_name" in idx_data
        assert "by_type" in idx_data
        assert "by_tag" in idx_data
        assert "backlinks" in idx_data
        
        assert "by_name" in idx_data
        assert "by_type" in idx_data
        assert "by_tag" in idx_data
        assert "backlinks" in idx_data
        
        # Check by_name
        assert "Concept A" in idx_data["by_name"]
        assert idx_data["by_name"]["Concept A"] == "c1"
        
        # Check backlinks
        assert "c2" in idx_data["backlinks"]
        assert len(idx_data["backlinks"]["c2"]) == 1
        
        print("✓ test_index_creation passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_index_derived_backlinks():
    """Test that backlinks are derived from links."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        c1 = Concept(id="c1", name="Source", type="concept")
        c2 = Concept(id="c2", name="Target", type="concept")
        
        evidence = Evidence(
            source_id="msg-001",
            source_type="message",
            content="Link",
            confidence=0.9,
            timestamp=int(time_module.time()),
            category="inferred",
        )
        
        link = Link(
            source_id="c1",
            target_id="c2",
            link_type="part_of",
            confidence=0.8,
            reason="Source is part of Target",
            evidence=[evidence],
            created_at=int(time_module.time()),
            updated_at=int(time_module.time()),
        )
        
        s.save_link(link)
        s.load()
        
        # Compute backlinks
        idx = index.ConceptGraphIndex()
        backlinks = idx.compute_backlinks(list(s._link_cache.values()))
        
        # c2 should have a backlink from c1
        assert "c2" in backlinks
        assert len(backlinks["c2"]) == 1
        assert backlinks["c2"][0]["source_id"] == "c1"
        assert backlinks["c2"][0]["link_type"] == "part_of"
        
        print("✓ test_index_derived_backlinks passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_graph_statistics():
    """Test graph statistics computation."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        # Create concepts
        c1 = Concept(id="c1", name="A", type="concept", tags=["tag1"])
        c2 = Concept(id="c2", name="B", type="entity", tags=["tag1", "tag2"])
        c3 = Concept(id="c3", name="C", type="concept")
        
        s.save_concept(c1)
        s.save_concept(c2)
        s.save_concept(c3)
        
        # Load and count
        s.load()
        
        assert len(s._concept_cache) == 3
        assert s.get_concept_count() == 3
        
        print("✓ test_graph_statistics passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests():
    """Run all store/index tests."""
    import time
    
    tests = [
        test_concept_save_load,
        test_link_save_load,
        test_index_creation,
        test_index_derived_backlinks,
        test_graph_statistics,
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n=== Concept Graph Store/Index Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
