"""Tests for Concept Graph Runtime Write Bridge.

Tests:
- Weather result write
- Time result write
- Unsupported outcome write
- Bounded reflection write
- Deduplication (no duplicate writes)
"""

import sys
from pathlib import Path

# Add workspace root to path for imports
workspace_root = str(Path('/data/data/com.termux/files/home/.openclaw/workspace').resolve())
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

# Add weslr path for concept_graph imports
weslr_path = str(Path('/data/data/com.termux/files/home/.openclaw/workspace/weslr').resolve())
if weslr_path not in sys.path:
    sys.path.insert(0, weslr_path)

import tempfile
import shutil
import json
import os

from concept_graph import Concept, Evidence
from concept_graph.bridge import RuntimeWriteBridge


def test_weather_write():
    """Test weather result write."""
    bridge = RuntimeWriteBridge()
    
    # Clear write log for clean test
    if bridge.runtime_write_log_path.exists():
        bridge.runtime_write_log_path.unlink()
    
    weather_data = {
        "location": "Rome",
        "temp_c": 22,
        "temp_f": 72,
        "weather_desc": "Sunny",
    }
    
    result = bridge.write_weather_result("Rome", weather_data)
    
    assert result.get("skipped") == False
    assert "concept_id" in result
    assert result.get("evidence_count") >= 1
    
    print("✓ test_weather_write passed")


def test_time_write():
    """Test time result write."""
    bridge = RuntimeWriteBridge()
    
    # Clear write log for clean test
    if bridge.runtime_write_log_path.exists():
        bridge.runtime_write_log_path.unlink()
    
    result = bridge.write_time_result()
    
    assert result.get("skipped") == False
    assert "concept_id" in result
    assert result.get("evidence_count") >= 1
    
    print("✓ test_time_write passed")


def test_unsupported_write():
    """Test unsupported outcome write."""
    bridge = RuntimeWriteBridge()
    
    # Clear write log for clean test
    if bridge.runtime_write_log_path.exists():
        bridge.runtime_write_log_path.unlink()
    
    result = bridge.write_unsupported_outcome(
        query="What is the population of Mars?",
        reason="No local evidence source for population data",
    )
    
    assert result.get("skipped") == False
    assert "concept_id" in result
    assert result.get("evidence_count") >= 1
    
    print("✓ test_unsupported_write passed")


def test_reflection_write():
    """Test bounded reflection write."""
    bridge = RuntimeWriteBridge()
    
    # Clear write log for clean test
    if bridge.runtime_write_log_path.exists():
        bridge.runtime_write_log_path.unlink()
    
    thought_data = {
        "kind": "inner_thought",
        "role": "builder",
        "summary": "Current time: 2026-04-05.",
        "concern": "Time tracking.",
        "intent": "Maintain awareness.",
        "should_speak": False,
        "self_mod_hint": "",
    }
    
    result = bridge.write_bounded_reflection("builder", thought_data)
    
    assert result.get("skipped") == False
    assert "concept_id" in result
    assert result.get("evidence_count") >= 1
    
    print("✓ test_reflection_write passed")


def test_deduplication():
    """Test that duplicate events are skipped."""
    bridge = RuntimeWriteBridge()
    
    # Clear write log for clean test
    if bridge.runtime_write_log_path.exists():
        bridge.runtime_write_log_path.unlink()
    
    # First write
    result1 = bridge.write_time_result(source_id="test-dedup-1")
    assert result1.get("skipped") == False
    
    # Second write with same source_id should be skipped
    result2 = bridge.write_time_result(source_id="test-dedup-1")
    assert result2.get("skipped") == True
    assert result2.get("reason") == "duplicate"
    
    print("✓ test_deduplication passed")


def test_evidence_categories():
    """Test that evidence categories are preserved."""
    bridge = RuntimeWriteBridge()
    
    # Clear write log for clean test
    if bridge.runtime_write_log_path.exists():
        bridge.runtime_write_log_path.unlink()
    
    # Weather should be source-backed
    weather_data = {
        "location": "Rome",
        "temp_c": 22,
        "weather_desc": "Sunny",
    }
    result = bridge.write_weather_result("Rome", weather_data)
    
    assert result.get("skipped") == False
    assert "concept_id" in result
    
    # Load the concept to check evidence
    store = bridge._get_graph_store()
    concept = store.load_concept(result["concept_id"])
    
    assert concept is not None
    assert len(concept.evidence) >= 1
    
    # Check evidence categories
    categories = [e.category for e in concept.evidence]
    assert "source-backed" in categories or "model-asserted" in categories
    
    print("✓ test_evidence_categories passed")


def test_runtime_write_log():
    """Test that write log is created."""
    bridge = RuntimeWriteBridge()
    log_path = bridge.runtime_write_log_path
    
    # Should exist after writes
    assert log_path.exists()
    
    # Should contain writes
    content = json.loads(log_path.read_text())
    assert "writes" in content
    assert "last_run" in content
    
    print("✓ test_runtime_write_log passed")


def run_all_tests():
    """Run all runtime write tests."""
    tests = [
        test_weather_write,
        test_time_write,
        test_unsupported_write,
        test_reflection_write,
        test_deduplication,
        test_evidence_categories,
        test_runtime_write_log,
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
    
    print(f"\n=== Runtime Write Bridge Tests ===")
    print(f"PASSED: {passed}/{len(tests)}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
