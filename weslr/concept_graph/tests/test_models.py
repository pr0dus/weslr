"""Unit tests for Concept Graph Models.

Tests:
- Concept serialization
- Link serialization
- Evidence serialization
- Backlink derivation
"""

import sys
from pathlib import Path

# Add workspace to path for imports
workspace = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, workspace)
sys.path.insert(0, str(Path(workspace) / "weslr"))

from concept_graph import Concept, Link, Evidence, Backlink
from concept_graph import get_link_types, get_evidence_categories
import time


def test_concept_creation():
    """Test basic concept creation."""
    concept = Concept(
        id="test-001",
        name="Test Concept",
        type="concept",
        description="A test concept for verification",
        tags=["test", "verification"],
    )
    
    assert concept.id == "test-001"
    assert concept.name == "Test Concept"
    assert concept.type == "concept"
    assert "test" in concept.tags
    assert "verification" in concept.tags
    print("✓ test_concept_creation passed")


def test_concept_serialization():
    """Test concept to_dict/from_dict."""
    concept = Concept(
        id="test-002",
        name="Serialization Test",
        type="entity",
        aliases=["alt1", "alt2"],
        tags=["tag1"],
    )
    
    # Serialize
    data = concept.to_dict()
    
    # Verify structure
    assert data["id"] == "test-002"
    assert data["name"] == "Serialization Test"
    assert data["type"] == "entity"
    assert len(data["aliases"]) == 2
    
    # Deserialize
    restored = Concept.from_dict(data)
    assert restored.id == concept.id
    assert restored.name == concept.name
    assert len(restored.aliases) == len(concept.aliases)
    print("✓ test_concept_serialization passed")


def test_evidence_creation():
    """Test evidence creation with all fields."""
    evidence = Evidence(
        source_id="test-message-123",
        source_type="message",
        content="This is supporting evidence",
        confidence=0.85,
        timestamp=int(time.time() - 3600),  # 1 hour ago
        category="source-backed",
        traceable=True,
        reason="Extracted from user message",
    )
    
    assert evidence.source_id == "test-message-123"
    assert evidence.source_type == "message"
    assert evidence.confidence == 0.85
    assert evidence.category == "source-backed"
    assert evidence.traceable is True
    print("✓ test_evidence_creation passed")


def test_evidence_serialization():
    """Test evidence serialization."""
    import time as time_module
    
    evidence = Evidence(
        source_id="file-456",
        source_type="file",
        content="Evidence from file",
        confidence=0.9,
        timestamp=int(time_module.time()),
        category="source-backed",
    )
    
    data = evidence.to_dict()
    restored = Evidence.from_dict(data)
    
    assert restored.source_id == evidence.source_id
    assert restored.source_type == evidence.source_type
    assert restored.confidence == evidence.confidence
    print("✓ test_evidence_serialization passed")


def test_link_creation():
    """Test link creation."""
    evidence = Evidence(
        source_id="msg-789",
        source_type="message",
        content="Link supported by this",
        confidence=0.75,
        timestamp=int(time.time()),
        category="inferred",
    )
    
    link = Link(
        source_id="concept-A",
        target_id="concept-B",
        link_type="related_to",
        confidence=0.8,
        reason="Inferred from context similarity",
        evidence=[evidence],
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    
    assert link.source_id == "concept-A"
    assert link.target_id == "concept-B"
    assert link.link_type == "related_to"
    assert link.confidence == 0.8
    assert len(link.evidence) == 1
    print("✓ test_link_creation passed")


def test_link_serialization():
    """Test link serialization and backlink derivation."""
    evidence = Evidence(
        source_id="msg-001",
        source_type="message",
        content="Supporting evidence",
        confidence=0.9,
        timestamp=int(time.time()),
        category="source-backed",
    )
    
    link = Link(
        source_id="concept-X",
        target_id="concept-Y",
        link_type="depends_on",
        confidence=0.85,
        reason="Requires Y for X to work",
        evidence=[evidence],
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    
    # Serialize
    data = link.to_dict()
    restored = Link.from_dict(data)
    
    assert restored.source_id == link.source_id
    assert restored.target_id == link.target_id
    assert restored.link_type == link.link_type
    
    # Test backlink derivation
    backlink = link.get_backlink()
    assert backlink.source_id == "concept-X"
    assert backlink.target_id == "concept-Y"
    assert backlink.link_type == "depends_on"
    print("✓ test_link_serialization passed")


def test_backlink_derivation():
    """Test backlink creation from link."""
    link = Link(
        source_id="A",
        target_id="B",
        link_type="part_of",
        confidence=0.7,
        reason="A is part of B",
        evidence=[],
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    
    backlink = link.get_backlink()
    
    assert backlink.source_id == "A"
    assert backlink.target_id == "B"
    assert backlink.link_type == "part_of"
    assert backlink.reason == "A is part of B"
    print("✓ test_backlink_derivation passed")


def test_concept_evidence_management():
    """Test adding evidence to concept."""
    concept = Concept(
        id="test-003",
        name="Evidence Test",
        type="concept",
    )
    
    evidence = Evidence(
        source_id="msg-002",
        source_type="message",
        content="New evidence",
        confidence=0.8,
        timestamp=int(time.time()),
        category="user-provided",
    )
    
    concept.add_evidence(evidence)
    
    assert len(concept.evidence) == 1
    assert concept.evidence[0].source_id == "msg-002"
    print("✓ test_concept_evidence_management passed")


def test_concept_link_management():
    """Test adding links to concept."""
    concept = Concept(
        id="test-004",
        name="Link Test",
        type="concept",
    )
    
    evidence = Evidence(
        source_id="msg-003",
        source_type="message",
        content="Link evidence",
        confidence=0.9,
        timestamp=int(time.time()),
        category="inferred",
    )
    
    link = Link(
        source_id="test-004",
        target_id="related-concept",
        link_type="related_to",
        confidence=0.85,
        reason="Related by topic",
        evidence=[evidence],
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    
    concept.add_link(link)
    
    assert len(concept.links) == 1
    assert concept.links[0].target_id == "related-concept"
    print("✓ test_concept_link_management passed")


def run_all_tests():
    """Run all model tests."""
    import time
    
    tests = [
        test_concept_creation,
        test_concept_serialization,
        test_evidence_creation,
        test_evidence_serialization,
        test_link_creation,
        test_link_serialization,
        test_backlink_derivation,
        test_concept_evidence_management,
        test_concept_link_management,
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
    
    print(f"\n=== Concept Graph Models Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
