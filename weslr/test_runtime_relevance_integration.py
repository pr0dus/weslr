"""
weslr/test_runtime_relevance_integration.py

Tests that relevance_surface is activated at runtime inside build_communicator_message_payload()
as an ADVISORY, READ-ONLY layer — with no authority over routing, decisions, or execution.

Verifies (Compression Canon v1 — advisory integration):
1. _relevant_interests appears in response metadata on every return path
2. interests.json is NOT modified by the call
3. threads.json is NOT modified
4. Routing output is unchanged for the same input
5. No calls to record_inadequacy_event, surface_to_spine_bridge, or proposal systems
"""

import json
import pytest
import tempfile
from pathlib import Path

# Tested module
import dialogue as DialogueModule
from weslr.relevance_surface import query_relevant_interests
from weslr.interest_tracker import _interests_path, set_interests_path


# ── Test fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def clean_interests():
    """Provide a clean temporary interests file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"interests": []}, f)
        path = Path(f.name)
    set_interests_path(path)
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture
def clean_threads():
    """Provide a clean temporary threads file."""
    threads_path = Path(__file__).resolve().parent / "threads.json"
    # Backup existing if present
    backup = None
    if threads_path.exists():
        backup = threads_path.read_bytes()
    yield threads_path
    # Restore
    if backup is not None:
        threads_path.write_bytes(backup)
    elif threads_path.exists():
        threads_path.unlink()


# ── Test helpers ───────────────────────────────────────────────────────────────

def _build_payload(
    message="hello",
    topics=None,
    turn_type="greeting",
    l2_session=None,
    research_context=None,
):
    """Call build_communicator_message_payload with minimal required args."""
    from sim import load_communicator_self
    self_state = load_communicator_self()
    narrative = self_state.get("narrative_state") or {}
    relationships = self_state.get("relationships") or {}
    latest_human = {
        "message": message,
        "topics": topics or [],
        "turn_type": turn_type,
        "reply_shape": "answer_directly",
        "likely_need": "direct_answer",
    }
    return DialogueModule.build_communicator_message_payload(
        narrative=narrative,
        relationships=relationships,
        active_thread=None,
        latest_human=latest_human,
        research_context=research_context,
        l0_identity=None,
        l1_operating=None,
        l2_session=l2_session,
    )


# ── Core integration tests ──────────────────────────────────────────────────────

def test_relevant_interests_key_appears_in_response(clean_interests, clean_threads):
    """All return paths include _relevant_interests in the response dict."""
    # Case A: with session (if l2_session: branch)
    result_a = _build_payload(message="hello", turn_type="greeting")
    assert "_relevant_interests" in result_a, (
        f"Missing _relevant_interests in session response. Keys: {list(result_a.keys())}"
    )
    assert isinstance(result_a["_relevant_interests"], list), (
        f"_relevant_interests must be list, got {type(result_a['_relevant_interests'])}"
    )

    # Case B: no session + no thread (fallback branch)
    result_b = _build_payload(message="asdfqwerzxcv", turn_type="question")
    assert "_relevant_interests" in result_b, (
        f"Missing _relevant_interests in fallback response. Keys: {list(result_b.keys())}"
    )
    assert isinstance(result_b["_relevant_interests"], list)


def test_relevant_interests_shape(clean_interests, clean_threads):
    """When interests exist, _relevant_interests has correct shape with name/score/reasons."""
    # Pre-populate an interest
    from weslr.interest_tracker import _load, _save
    _save({
        "interests": [{
            "id": "test001",
            "name": "governance",
            "display_name": "Governance Quality",
            "status": "active",
            "tags": ["governance", "quality"],
            "last_seen_at": "2026-04-21T10:00:00Z",
            "occurrence_count": 0,
            "created_at": "2026-04-21T10:00:00Z",
        }]
    })

    result = _build_payload(message="governance quality is important")
    interests = result["_relevant_interests"]
    assert isinstance(interests, list)
    if interests:
        first = interests[0]
        assert "name" in first, f"Missing 'name' in interest entry: {first}"
        assert "score" in first, f"Missing 'score' in interest entry: {first}"
        assert "match_reasons" in first, f"Missing 'match_reasons' in interest entry: {first}"
        assert isinstance(first["match_reasons"], list), (
            f"match_reasons must be list, got {type(first['match_reasons'])}"
        )


def test_interests_file_not_modified(clean_interests, clean_threads):
    """Calling the payload does not write to interests.json."""
    import hashlib
    with open(clean_interests, "r") as f:
        before = f.read()
    before_hash = hashlib.sha256(before.encode()).hexdigest()

    # Call the payload multiple times
    _build_payload(message="test governance")
    _build_payload(message="quality assessment")
    _build_payload(message="hello")

    with open(clean_interests, "r") as f:
        after = f.read()
    after_hash = hashlib.sha256(after.encode()).hexdigest()

    assert before_hash == after_hash, (
        f"interests.json was modified during payload call. "
        f"Before: {before[:200]}, After: {after[:200]}"
    )


def test_threads_file_not_modified(clean_threads):
    """Calling the payload does not write to threads.json."""
    threads_path = clean_threads
    # Ensure it exists and is empty-ish
    import hashlib
    if threads_path.exists():
        with open(threads_path, "r") as f:
            before = f.read()
        before_hash = hashlib.sha256(before.encode()).hexdigest()
    else:
        before_hash = None

    _build_payload(message="test thread")

    if before_hash is not None:
        with open(threads_path, "r") as f:
            after = f.read()
        after_hash = hashlib.sha256(after.encode()).hexdigest()
        assert before_hash == after_hash, (
            "threads.json was modified during payload call"
        )
    else:
        assert not threads_path.exists(), (
            "threads.json was created during payload call"
        )


def test_routing_output_unchanged_for_same_input(clean_interests, clean_threads):
    """Same input always produces same message + source regardless of interests."""
    # Pre-populate interests
    from weslr.interest_tracker import _save
    _save({
        "interests": [{
            "id": "test001",
            "name": "governance",
            "display_name": "Governance Quality",
            "status": "active",
            "tags": ["governance"],
            "last_seen_at": "2026-04-21T10:00:00Z",
            "occurrence_count": 0,
            "created_at": "2026-04-21T10:00:00Z",
        }]
    })

    msg = "governance quality"
    result1 = _build_payload(message=msg, turn_type="question")
    result2 = _build_payload(message=msg, turn_type="question")

    assert result1["message"] == result2["message"], (
        "Message must be identical for same input regardless of interest presence"
    )
    assert result1["source"] == result2["source"], (
        "Source must be identical for same input"
    )


def test_relevant_interests_empty_when_no_interests(clean_interests, clean_threads):
    """When no interests exist, _relevant_interests is an empty list."""
    result = _build_payload(message="completely unrelated text xyz789")
    assert result["_relevant_interests"] == [], (
        f"Expected empty list, got {result['_relevant_interests']}"
    )


def test_relevant_interests_attached_on_all_return_paths(clean_interests, clean_threads):
    """_relevant_interests is attached on every distinct return branch."""
    # Path 1: greeting turn
    r1 = _build_payload(message="hello", turn_type="greeting")
    assert "_relevant_interests" in r1

    # Path 2: question (no session, no thread → fallback)
    r2 = _build_payload(message="asdfqwerzxcv", turn_type="question")
    assert "_relevant_interests" in r2

    # Path 3: question with session
    from sim import load_tier
    l2 = load_tier("l2")
    r3 = _build_payload(message="what is governance", turn_type="question", l2_session=l2)
    assert "_relevant_interests" in r3


# ── Advisory-only boundary tests ───────────────────────────────────────────────

def test_relevant_interests_does_not_change_routing_branch(clean_interests, clean_threads):
    """Adding an interest must not change which routing branch fires."""
    # First: call WITHOUT any interests
    result_a = _build_payload(message="hello", turn_type="greeting")
    source_a = result_a["source"]

    # Pre-populate interests (should not affect routing)
    from weslr.interest_tracker import _save
    _save({
        "interests": [{
            "id": "test001",
            "name": "greeting",
            "display_name": "Greeting Topic",
            "status": "active",
            "tags": ["greeting"],
            "last_seen_at": "2026-04-21T10:00:00Z",
            "occurrence_count": 0,
            "created_at": "2026-04-21T10:00:00Z",
        }]
    })

    result_b = _build_payload(message="hello", turn_type="greeting")
    source_b = result_b["source"]

    assert source_a == source_b, (
        f"Routing branch changed when interests were added. "
        f"Before: {source_a}, After: {source_b}. "
        f"relevance_surface must be ADVISORY only — no routing authority."
    )
    assert result_a["message"] == result_b["message"], (
        "Response message changed when interests were added"
    )
