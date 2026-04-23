# test_thread_tracker.py — Tests for Thread Tracker v1 (Slice 0)

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr import thread_tracker


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def tmp_threads(tmp_path, monkeypatch):
    """Point thread_tracker storage to a temp file for isolation."""
    f = tmp_path / "threads.json"
    monkeypatch.setattr(thread_tracker, "STORAGE_PATH", str(f))
    # Also patch in the module
    thread_tracker.STORAGE_PATH = Path(str(f))
    # Reset to empty
    thread_tracker._save({"threads": []})
    yield str(f)
    # No teardown needed — tmp_path cleans up


# ============================================================================
# CORE API TESTS
# ============================================================================

def test_create_thread_returns_dict(tmp_threads):
    t = thread_tracker.create_thread("My first thread")
    assert t is not None
    assert "id" in t
    assert t["name"] == "My first thread"
    assert t["state"] == "active"
    assert t["items"] == []
    assert "created_at" in t
    assert "updated_at" in t


def test_create_thread_id_is_unique(tmp_threads):
    t1 = thread_tracker.create_thread("Thread 1")
    t2 = thread_tracker.create_thread("Thread 2")
    assert t1["id"] != t2["id"]


def test_create_thread_name_truncated_at_100(tmp_threads):
    long_name = "x" * 200
    t = thread_tracker.create_thread(long_name)
    assert t is not None
    assert len(t["name"]) == 100


def test_create_thread_persists(tmp_threads):
    t = thread_tracker.create_thread("Persisted thread")
    assert t is not None
    # Reload from disk
    with open(tmp_threads) as f:
        data = json.load(f)
    assert len(data["threads"]) == 1
    assert data["threads"][0]["name"] == "Persisted thread"


def test_get_thread_returns_thread(tmp_threads):
    t = thread_tracker.create_thread("Find me")
    assert t is not None
    found = thread_tracker.get_thread(t["id"])
    assert found is not None
    assert found["id"] == t["id"]
    assert found["name"] == "Find me"


def test_get_thread_returns_none_for_unknown(tmp_threads):
    found = thread_tracker.get_thread("thr-doesnotexist")
    assert found is None


def test_list_threads_returns_all(tmp_threads):
    for i in range(3):
        thread_tracker.create_thread(f"Thread {i}")
    threads = thread_tracker.list_threads()
    assert len(threads) == 3


def test_list_threads_filters_by_state(tmp_threads):
    t1 = thread_tracker.create_thread("Active thread")
    thread_tracker.set_state(t1["id"], "active")
    t2 = thread_tracker.create_thread("Resolved thread")
    thread_tracker.set_state(t2["id"], "resolved")
    assert len(thread_tracker.list_threads(state="active")) == 1
    assert len(thread_tracker.list_threads(state="resolved")) == 1


def test_list_threads_respects_limit(tmp_threads):
    for _ in range(5):
        thread_tracker.create_thread("Thread")
    assert len(thread_tracker.list_threads(limit=3)) == 3


def test_list_threads_sorted_by_updated_at(tmp_threads):
    import time
    t1 = thread_tracker.create_thread("First")
    t2 = thread_tracker.create_thread("Second")
    thread_tracker.set_state(t1["id"], "dormant")  # Updates updated_at
    # Small delay to ensure different timestamps
    threads = thread_tracker.list_threads()
    assert threads[0]["id"] == t1["id"]  # Most recently updated first


def test_set_state_updates(tmp_threads):
    t = thread_tracker.create_thread("State test")
    assert t["state"] == "active"
    ok = thread_tracker.set_state(t["id"], "resolved")
    assert ok is True
    updated = thread_tracker.get_thread(t["id"])
    assert updated["state"] == "resolved"


def test_set_state_rejects_invalid_state(tmp_threads):
    t = thread_tracker.create_thread("Invalid state test")
    ok = thread_tracker.set_state(t["id"], "not_a_state")
    assert ok is False


def test_set_state_returns_false_for_unknown(tmp_threads):
    ok = thread_tracker.set_state("thr-unknown", "resolved")
    assert ok is False


def test_add_item_appends_to_thread(tmp_threads):
    t = thread_tracker.create_thread("Item test")
    ok = thread_tracker.add_item(
        thread_id=t["id"],
        item_type="artifact",
        item_id="artifact-001",
        link_type="explicit",
        added_by="operator",
    )
    assert ok is True
    updated = thread_tracker.get_thread(t["id"])
    assert len(updated["items"]) == 1
    assert updated["items"][0]["item_id"] == "artifact-001"


def test_add_item_rejects_invalid_type(tmp_threads):
    t = thread_tracker.create_thread("Invalid type test")
    ok = thread_tracker.add_item(
        thread_id=t["id"],
        item_type="invalid",
        item_id="x",
        link_type="explicit",
        added_by="operator",
    )
    assert ok is False


def test_add_item_rejects_invalid_link_type(tmp_threads):
    t = thread_tracker.create_thread("Invalid link test")
    ok = thread_tracker.add_item(
        thread_id=t["id"],
        item_type="artifact",
        item_id="x",
        link_type="guessed",
        added_by="operator",
    )
    assert ok is False


def test_add_item_returns_false_for_unknown_thread(tmp_threads):
    ok = thread_tracker.add_item(
        thread_id="thr-doesnotexist",
        item_type="artifact",
        item_id="x",
        link_type="explicit",
        added_by="operator",
    )
    assert ok is False


def test_add_item_sets_timestamp(tmp_threads):
    t = thread_tracker.create_thread("Timestamp test")
    thread_tracker.add_item(
        thread_id=t["id"],
        item_type="question",
        item_id="question-001",
        link_type="explicit",
        added_by="operator",
    )
    updated = thread_tracker.get_thread(t["id"])
    assert updated["items"][0]["added_at"] != ""


def test_add_item_truncates_note_at_500(tmp_threads):
    t = thread_tracker.create_thread("Note truncate test")
    long_note = "n" * 600
    thread_tracker.add_item(
        thread_id=t["id"],
        item_type="note",
        item_id="note-001",
        link_type="explicit",
        added_by="operator",
        note=long_note,
    )
    updated = thread_tracker.get_thread(t["id"])
    assert len(updated["items"][0]["note"]) == 500


def test_add_item_updates_thread_timestamp(tmp_threads):
    t = thread_tracker.create_thread("Update time test")
    import time
    time.sleep(0.01)
    original = t["updated_at"]
    thread_tracker.add_item(
        thread_id=t["id"],
        item_type="artifact",
        item_id="artifact-x",
        link_type="explicit",
        added_by="operator",
    )
    updated = thread_tracker.get_thread(t["id"])
    assert updated["updated_at"] != original


def test_remove_thread(tmp_threads):
    t = thread_tracker.create_thread("To be removed")
    ok = thread_tracker.remove_thread(t["id"])
    assert ok is True
    assert thread_tracker.get_thread(t["id"]) is None


def test_remove_thread_returns_false_for_unknown(tmp_threads):
    ok = thread_tracker.remove_thread("thr-unknown")
    assert ok is False


def test_get_thread_count(tmp_threads):
    assert thread_tracker.get_thread_count() == 0
    thread_tracker.create_thread("One")
    thread_tracker.create_thread("Two")
    assert thread_tracker.get_thread_count() == 2


def test_get_threads_summary(tmp_threads):
    t1 = thread_tracker.create_thread("A")
    thread_tracker.set_state(t1["id"], "resolved")
    thread_tracker.create_thread("B")
    thread_tracker.create_thread("C")
    summary = thread_tracker.get_threads_summary()
    assert summary["resolved"] == 1
    assert summary["active"] == 2
    assert summary["dormant"] == 0


# ============================================================================
# BOUNDARY TESTS
# ============================================================================

def test_max_threads_limit(tmp_threads):
    """At 100 threads, next create returns None."""
    # Create 100 threads
    for i in range(100):
        t = thread_tracker.create_thread(f"Thread {i}")
        assert t is not None, f"Failed at {i}"
    # Next should fail
    t_over = thread_tracker.create_thread("Over limit")
    assert t_over is None
    # But we can still get existing threads
    assert thread_tracker.get_thread_count() == 100


def test_max_items_per_thread_prunes_oldest(tmp_threads):
    t = thread_tracker.create_thread("Item limit test")
    # Add 201 items (over the 200 limit)
    for i in range(201):
        thread_tracker.add_item(
            thread_id=t["id"],
            item_type="artifact",
            item_id=f"art-{i:03d}",
            link_type="explicit",
            added_by="operator",
        )
    updated = thread_tracker.get_thread(t["id"])
    assert len(updated["items"]) == 200
    # Oldest (art-000) should be gone
    item_ids = [item["item_id"] for item in updated["items"]]
    assert "art-000" not in item_ids
    assert "art-200" in item_ids


# ============================================================================
# ISOLATION TESTS
# ============================================================================

def test_interests_json_untouched(tmp_threads):
    """Thread operations must not affect interests.json."""
    interests_path = Path(__file__).parent.parent / "weslr" / "interests.json"
    # Read interests path if it exists
    before = None
    if interests_path.exists():
        with open(interests_path) as f:
            before = f.read()
    # Do thread operations
    thread_tracker.create_thread("Isolation test")
    # Verify interests unchanged
    if interests_path.exists():
        with open(interests_path) as f:
            after = f.read()
        assert before == after


def test_relevance_surface_not_touched(tmp_threads):
    """Thread operations must not affect relevance_surface.py behavior."""
    from weslr import relevance_surface
    # relevance_surface is read-only in this test
    result = relevance_surface.query_relevant_interests("test", None, top_n=3)
    assert isinstance(result, list)  # Should not raise


# ============================================================================
# READ SURFACE TESTS (Slice 1)
# ============================================================================

def test_get_threads_for_item_empty_when_no_matches(tmp_threads):
    """Item not in any thread returns empty list."""
    from weslr.thread_tracker import get_threads_for_item
    result = get_threads_for_item("artifact-orphan")
    assert result == []


def test_get_threads_for_item_single_thread(tmp_threads):
    """Artifact in one thread returns that thread reference."""
    from weslr.thread_tracker import get_threads_for_item, create_thread, add_item
    t = create_thread("Test thread")
    add_item(t["id"], "artifact", "artifact-001", "explicit", "operator")
    refs = get_threads_for_item("artifact-001")
    assert len(refs) == 1
    assert refs[0]["thread_id"] == t["id"]
    assert refs[0]["thread_name"] == "Test thread"
    assert refs[0]["link_type"] == "explicit"
    assert refs[0]["added_by"] == "operator"


def test_get_threads_for_item_multiple_threads(tmp_threads):
    """Artifact in multiple threads returns all thread references."""
    from weslr.thread_tracker import get_threads_for_item, create_thread, add_item
    t1 = create_thread("Thread one")
    t2 = create_thread("Thread two")
    add_item(t1["id"], "artifact", "shared-artifact", "explicit", "operator")
    add_item(t2["id"], "artifact", "shared-artifact", "explicit", "operator")
    refs = get_threads_for_item("shared-artifact")
    assert len(refs) == 2
    ref_ids = {r["thread_id"] for r in refs}
    assert ref_ids == {t1["id"], t2["id"]}


def test_get_threads_for_item_infers_thread_state(tmp_threads):
    """Reference includes current thread state."""
    from weslr.thread_tracker import get_threads_for_item, create_thread, add_item, set_state
    t = create_thread("State test")
    set_state(t["id"], "resolved")
    add_item(t["id"], "artifact", "artifact-resolved", "explicit", "operator")
    refs = get_threads_for_item("artifact-resolved")
    assert refs[0]["state"] == "resolved"


def test_get_threads_for_item_returns_added_at(tmp_threads):
    """Reference includes when item was added to thread."""
    from weslr.thread_tracker import get_threads_for_item, create_thread, add_item
    t = create_thread("Timestamp test")
    add_item(t["id"], "question", "question-001", "explicit", "operator")
    refs = get_threads_for_item("question-001")
    assert refs[0]["added_at"] != ""
    assert "T" in refs[0]["added_at"]  # ISO8601 format
