"""Tests for Concept Graph Bridge Module.

Tests:
- Entity graph import to concepts
- Relationship import to links
- Evidence bridge creation
- Mapping preservation
"""

import sys
from pathlib import Path

# Add workspace root to path for imports
workspace_root = str(Path('/data/data/com.termux/files/home/.openclaw/workspace').resolve())
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

# Add weslr to path
weslr_path = str(Path('/data/data/com.termux/files/home/.openclaw/workspace/weslr').resolve())
if weslr_path not in sys.path:
    sys.path.insert(0, weslr_path)

import tempfile
import shutil
import json

# Import from workspace root - do entity_graph first
from entity_graph import EntityGraph, Entity, Relationship, ENTITY_GRAPH_PATH
# Now concept_graph imports should work
from concept_graph import Concept, Link, Evidence
from concept_graph.bridge import EntityGraphBridge, EvidenceBridge
from concept_graph import store as concept_store


def test_entity_graph_bridge_creation():
    """Test bridge initialization."""
    bridge = EntityGraphBridge()
    assert bridge is not None
    print("✓ test_entity_graph_bridge_creation passed")


def test_evidence_bridge_creation():
    """Test evidence bridge initialization."""
    bridge = EvidenceBridge()
    assert bridge is not None
    print("✓ test_evidence_bridge_creation passed")


def test_evidence_creation():
    """Test creating evidence from various sources."""
    bridge = EvidenceBridge()
    
    # From message - note: source_id overrides auto-generation
    ev = bridge.from_message_source("msg-123", "Test message content", source_id="test-source")
    assert ev.source_id == "test-source"
    assert ev.source_type == "message"
    assert ev.category == "source-backed"
    
    # Test auto-generation when source_id not provided
    ev2 = bridge.from_message_source("another-msg", "Content")
    assert ev2.source_id.startswith("msg-")
    
    # From file
    ev = bridge.from_file_source("test.txt", "File content")
    assert ev.source_id.startswith("file-")
    assert ev.source_type == "file"
    
    # From weather
    ev = bridge.from_weather_source("Rome", {"temp": 22, "condition": "sunny"})
    assert ev.source_type == "weather_service"
    
    # From model - this one creates cache entry
    ev = bridge.from_model_assertion("model-1", "Assertion content", "reasoning trace")
    assert ev.source_type == "model_reasoning"
    assert ev.category == "model-asserted"
    
    print("✓ test_evidence_creation passed")


def test_evidence_serialization():
    """Test evidence serialization and reconstruction."""
    bridge = EvidenceBridge()
    ev = bridge.from_message_source("msg-456", "Content")
    
    data = ev.to_dict()
    restored = Evidence.from_dict(data)
    
    assert restored.source_id == ev.source_id
    assert restored.content == ev.content
    print("✓ test_evidence_serialization passed")


def test_entity_graph_mapping():
    """Test entity graph mapping structure."""
    bridge = EntityGraphBridge()
    
    # Test type mappings
    assert bridge._map_entity_type("person") == "concept"
    assert bridge._map_entity_type("organization") == "concept"
    assert bridge._map_entity_type("object") == "entity"
    
    # Test relationship type mappings
    assert bridge._map_relationship_type("related_to") == "related_to"
    assert bridge._map_relationship_type("depends_on") == "depends_on"
    assert bridge._map_relationship_type("causes") == "causes"
    
    print("✓ test_entity_graph_mapping passed")


def test_evidence_cache():
    """Test evidence caching."""
    bridge = EvidenceBridge()
    
    # Clear cache first
    bridge.clear_cache()
    
    # Create and cache evidence
    ev = bridge.from_model_assertion("test-model", "Model assertion", "Reasoning")
    ev_id = ev.source_id  # Will be "model-test-model-<timestamp>"
    
    # Cache key is "model-" + model_id when source_id is not provided
    cache_key = f"model-test-model"
    
    # Load from cache - this reads what was just written
    cached = bridge.from_cache(cache_key)
    
    # Verify at least one cached entry exists with correct source_id
    assert len(cached) >= 1, f"Expected cached entries, got {len(cached)}"
    assert any(c.source_id == ev_id for c in cached), f"Expected source_id {ev_id} in cache"
    
    print("✓ test_evidence_cache passed")


def run_all_tests():
    """Run all bridge tests."""
    tests = [
        test_entity_graph_bridge_creation,
        test_evidence_bridge_creation,
        test_evidence_creation,
        test_evidence_serialization,
        test_entity_graph_mapping,
        test_evidence_cache,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n=== Concept Graph Bridge Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
