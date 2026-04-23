# test_thread_read_surface.py — Tests for _thread_refs in explain_item (Slice 1)

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr import thread_tracker


# ============================================================================
# FIXTURE
# ============================================================================

@pytest.fixture
def tmp_threads(tmp_path, monkeypatch):
    """Point thread_tracker storage to a temp file."""
    f = tmp_path / "threads.json"
    monkeypatch.setattr(thread_tracker, "STORAGE_PATH", str(f))
    thread_tracker.STORAGE_PATH = Path(str(f))
    thread_tracker._save({"threads": []})
    yield str(f)


# ============================================================================
# SIM.PY _get_thread_refs INTEGRATION TESTS
# ============================================================================

def test_thread_refs_empty_when_no_threads(tmp_threads):
    """_get_thread_refs returns [] when artifact is in no threads."""
    from sim import _get_thread_refs
    result = _get_thread_refs("artifact-orphan")
    assert result == []


def test_thread_refs_single_thread(tmp_threads):
    """Artifact linked to one thread appears in _thread_refs."""
    from sim import _get_thread_refs
    t = thread_tracker.create_thread("Single thread")
    thread_tracker.add_item(t["id"], "artifact", "artifact-001", "explicit", "operator")
    refs = _get_thread_refs("artifact-001")
    assert len(refs) == 1
    assert refs[0]["thread_id"] == t["id"]
    assert refs[0]["thread_name"] == "Single thread"


def test_thread_refs_multiple_threads(tmp_threads):
    """Artifact linked to multiple threads returns all refs."""
    from sim import _get_thread_refs
    t1 = thread_tracker.create_thread("Thread A")
    t2 = thread_tracker.create_thread("Thread B")
    thread_tracker.add_item(t1["id"], "artifact", "artifact-shared", "explicit", "operator")
    thread_tracker.add_item(t2["id"], "artifact", "artifact-shared", "explicit", "operator")
    refs = _get_thread_refs("artifact-shared")
    assert len(refs) == 2


def test_thread_refs_artifact_not_linked(tmp_threads):
    """Artifact not in any thread returns empty list."""
    from sim import _get_thread_refs
    thread_tracker.create_thread("Other thread")
    refs = _get_thread_refs("artifact-orphan")
    assert refs == []


def test_thread_refs_different_item_type(tmp_threads):
    """Only exact item_id match — different item types are separate."""
    from sim import _get_thread_refs
    t = thread_tracker.create_thread("Type test")
    thread_tracker.add_item(t["id"], "artifact", "artifact-x", "explicit", "operator")
    thread_tracker.add_item(t["id"], "question", "question-x", "explicit", "operator")
    artifact_refs = _get_thread_refs("artifact-x")
    question_refs = _get_thread_refs("question-x")
    assert len(artifact_refs) == 1
    assert len(question_refs) == 1
    assert artifact_refs[0]["item_id"] == "artifact-x"
    assert question_refs[0]["item_id"] == "question-x"


def test_thread_refs_inferred_link_type(tmp_threads):
    """inferred link types are returned with correct link_type field."""
    from sim import _get_thread_refs
    t = thread_tracker.create_thread("Inferred link test")
    thread_tracker.add_item(t["id"], "artifact", "artifact-inferred", "inferred", "integration:test")
    refs = _get_thread_refs("artifact-inferred")
    assert refs[0]["link_type"] == "inferred"
    assert refs[0]["added_by"] == "integration:test"


def test_thread_refs_no_writes(tmp_threads):
    """_get_thread_refs does not write to threads.json."""
    from sim import _get_thread_refs
    t = thread_tracker.create_thread("No-write test")
    with open(tmp_threads) as f:
        before = json.load(f)
    _get_thread_refs("artifact-nonexistent")
    with open(tmp_threads) as f:
        after = json.load(f)
    assert before == after


def test_thread_refs_does_not_create_threads(tmp_threads):
    """Calling _get_thread_refs never creates a thread."""
    from sim import _get_thread_refs
    initial_count = thread_tracker.get_thread_count()
    _get_thread_refs("artifact-any")
    _get_thread_refs("artifact-other")
    assert thread_tracker.get_thread_count() == initial_count


def test_thread_refs_does_not_add_items(tmp_threads):
    """_get_thread_refs never adds items to any thread."""
    from sim import _get_thread_refs
    t = thread_tracker.create_thread("Item write test")
    initial_items = len(thread_tracker.get_thread(t["id"])["items"])
    _get_thread_refs("artifact-any")
    updated = thread_tracker.get_thread(t["id"])
    assert len(updated["items"]) == initial_items
