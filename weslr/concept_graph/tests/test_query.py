"""Tests for Concept Graph Query Engine.

Tests:
- Path tracing
- Central concepts
- Source attribution
- Recent concepts
- Staleness report
"""

import sys
from pathlib import Path

# Add workspace to path for imports
workspace = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, workspace)
sys.path.insert(0, str(Path(workspace) / "weslr"))

import tempfile
import shutil
import time as time_module

from concept_graph import Concept, Link, Evidence
from concept_graph import store, query


def test_path_tracing():
    """Test path tracing between concepts."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        # Create chain: A -> B -> C
        evidence = Evidence(
            source_id="msg-001",
            source_type="message",
            content="Link",
            confidence=0.9,
            timestamp=int(time_module.time()),
            category="inferred",
        )
        
        link1 = Link(
            source_id="A",
            target_id="B",
            link_type="related_to",
            confidence=0.8,
            reason="A related to B",
            evidence=[evidence],
            created_at=int(time_module.time()),
            updated_at=int(time_module.time()),
        )
        
        link2 = Link(
            source_id="B",
            target_id="C",
            link_type="part_of",
            confidence=0.7,
            reason="B part of C",
            evidence=[evidence],
            created_at=int(time_module.time()),
            updated_at=int(time_module.time()),
        )
        
        s.save_link(link1)
        s.save_link(link2)
        
        # Query
        q = query.ConceptGraphQueryEngine(store=s)
        path = q.trace_path("A", "C")
        
        # A should be in path (DFS finds it via A->B->C)
        assert "A" in path
        assert "C" in path
        
        print("✓ test_path_tracing passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_shortest_path():
    """Test shortest path using BFS."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        evidence = Evidence(
            source_id="msg-001",
            source_type="message",
            content="Link",
            confidence=0.9,
            timestamp=int(time_module.time()),
            category="inferred",
        )
        
        link1 = Link(
            source_id="X",
            target_id="Y",
            link_type="related_to",
            confidence=0.8,
            reason="X related to Y",
            evidence=[evidence],
            created_at=int(time_module.time()),
            updated_at=int(time_module.time()),
        )
        
        s.save_link(link1)
        
        q = query.ConceptGraphQueryEngine(store=s)
        path = q.shortest_path("X", "Y")
        
        assert "X" in path
        assert "Y" in path
        
        print("✓ test_shortest_path passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_source_attribution():
    """Test source attribution for a concept."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        evidence = Evidence(
            source_id="msg-001",
            source_type="message",
            content="Supporting evidence",
            confidence=0.85,
            timestamp=int(time_module.time()),
            category="source-backed",
        )
        
        concept = Concept(
            id="test-concept",
            name="Test Concept",
            type="concept",
        )
        concept.add_evidence(evidence)
        
        s.save_concept(concept)
        
        q = query.ConceptGraphQueryEngine(store=s)
        sources = q.sources_supporting("test-concept")
        
        assert len(sources) == 1
        assert sources[0].source_id == "msg-001"
        assert sources[0].category == "source-backed"
        
        print("✓ test_source_attribution passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_recent_concepts():
    """Test recent concepts filter."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        now = int(time_module.time())
        
        recent = Concept(
            id="recent",
            name="Recent Concept",
            type="concept",
            created_at=now,
            last_updated=now,
        )
        
        old = Concept(
            id="old",
            name="Old Concept",
            type="concept",
            created_at=now - 1000000,
            last_updated=now - 1000000,
        )
        
        s.save_concept(recent)
        s.save_concept(old)
        
        # Filter recent (last 7 days)
        q = query.ConceptGraphQueryEngine(store=s)
        recent_concepts = q.recent_concepts(days=7)
        
        # Should include recent, should not include old
        recent_ids = [c.id for c in recent_concepts]
        assert "recent" in recent_ids
        assert "old" not in recent_ids
        
        print("✓ test_recent_concepts passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_staleness_report():
    """Test staleness report generation."""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        s = store.ConceptGraphStore(graph_dir=temp_dir)
        
        old_time = int(time_module.time() - 1000000)  # Stale
        
        evidence = Evidence(
            source_id="msg-001",
            source_type="message",
            content="Link",
            confidence=0.9,
            timestamp=old_time,
            category="inferred",
        )
        
        link = Link(
            source_id="A",
            target_id="B",
            link_type="related_to",
            confidence=0.8,
            reason="Stale link",
            evidence=[evidence],
            created_at=old_time,
            updated_at=old_time,
        )
        
        s.save_link(link)
        
        q = query.ConceptGraphQueryEngine(store=s)
        report = q.staleness_report()
        
        assert "links" in report
        assert "stale" in report["links"]
        
        print("✓ test_staleness_report passed")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests():
    """Run all query tests."""
    tests = [
        test_path_tracing,
        test_shortest_path,
        test_source_attribution,
        test_recent_concepts,
        test_staleness_report,
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
    
    print(f"\n=== Concept Graph Query Engine Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
