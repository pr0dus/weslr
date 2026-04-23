"""
Tests for _derive_suggestions (Relevance Slice A1 — suggestion surface as metadata).

Verifies:
- suggestions appear when relevant interests exist
- suggestions are consistent and structured
- no state writes occur
- confidence derived correctly
- no state changes to interests.json before/after
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.interest_tracker import create_interest, set_interests_path
from sim import _derive_suggestions


@pytest.fixture
def tmp_interests():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "interests.json"
        set_interests_path(p)
        # Initialize empty registry so file exists even without create_interest call
        with open(p, "w") as f:
            json.dump({"interests": []}, f)
        yield p


# ── _derive_suggestions — empty when no relevant interests ──────────────────────

def test_empty_when_no_interests(tmp_interests):
    artifact_meta = {"id": "artifact-1", "title": "Test Artifact"}
    result = _derive_suggestions(artifact_meta, [])
    assert result == []


def test_empty_when_relevance_scores_zero(tmp_interests):
    create_interest("unrelated", tags=["other"])
    artifact_meta = {"id": "artifact-1", "title": "Test Artifact"}

    # Interest with score 0 — should not produce suggestion
    zero_score_interests = [
        {"id": "abc", "name": "unrelated", "display_name": "Unrelated",
         "score": 0, "match_reasons": ["no eligible signal"], "tags": []}
    ]
    result = _derive_suggestions(artifact_meta, zero_score_interests)
    assert result == []


# ── _derive_suggestions — suggestion object shape ─────────────────────────────

def test_suggestion_object_shape(tmp_interests):
    interest = create_interest("governance quality", tags=["governance", "quality"])

    artifact_meta = {"id": "artifact-xyz", "title": "Governance Quality Report"}
    relevance_result = [
        {
            "id": interest["id"],
            "name": "governance_quality",
            "display_name": "governance quality",
            "score": 6,
            "match_reasons": ["matched tag: governance", "matched tag: quality",
                            "recent activity within 48 hours"],
            "tags": ["governance", "quality"],
            "occurrence_count": 0,
            "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    assert len(suggestions) == 1

    s = suggestions[0]
    assert "type" in s
    assert s["type"] == "interest_occurrence"
    assert "message" in s
    assert isinstance(s["message"], str)
    assert len(s["message"]) > 10  # non-empty message
    assert "confidence" in s
    assert isinstance(s["confidence"], float)
    assert 0.0 <= s["confidence"] <= 1.0
    assert "reasons" in s
    assert isinstance(s["reasons"], list)
    assert "action" in s
    assert isinstance(s["action"], dict)
    assert s["action"].get("requires_approval") is True


def test_suggestion_message_content(tmp_interests):
    interest = create_interest("confidence calibration", tags=["calibration"])

    artifact_meta = {"id": "artifact-1", "title": "Calibration Report"}
    relevance_result = [
        {
            "id": interest["id"],
            "name": "confidence_calibration",
            "display_name": "confidence calibration",
            "score": 5,
            "match_reasons": ["matched tag: calibration"],
            "tags": ["calibration"],
            "occurrence_count": 0,
            "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    msg = suggestions[0]["message"]
    assert "confidence calibration" in msg
    assert "record an occurrence" in msg.lower() or "occurrence" in msg.lower()


# ── _derive_suggestions — confidence derivation ───────────────────────────────

def test_confidence_derived_from_score(tmp_interests):
    interest = create_interest("test", tags=["test"])

    artifact_meta = {"id": "a1", "title": "Test"}
    # Score 5 out of max ~11 → confidence ~0.45
    relevance_result = [
        {
            "id": interest["id"], "name": "test", "display_name": "test",
            "score": 5, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    conf = suggestions[0]["confidence"]
    assert 0.3 < conf < 0.7  # score 5 / 11 ≈ 0.45


def test_confidence_capped_at_1(tmp_interests):
    interest = create_interest("test", tags=["test"])

    artifact_meta = {"id": "a1", "title": "Test"}
    # Score 20 (impossible with current signals, but test cap)
    relevance_result = [
        {
            "id": interest["id"], "name": "test", "display_name": "test",
            "score": 20, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    conf = suggestions[0]["confidence"]
    assert conf <= 1.0


# ── _derive_suggestions — action structure ────────────────────────────────────

def test_action_has_correct_command(tmp_interests):
    interest = create_interest("quality tracking", tags=["quality"])

    artifact_meta = {"id": "artifact-99", "title": "Quality Report"}
    relevance_result = [
        {
            "id": interest["id"], "name": "quality_tracking",
            "display_name": "quality tracking",
            "score": 4, "match_reasons": ["matched tag: quality"],
            "tags": ["quality"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    action = suggestions[0]["action"]
    assert action.get("command") == "record_occurrence"
    assert action.get("interest_id") == interest["id"]
    assert action.get("interest_name") == "quality_tracking"
    assert action.get("item_id") == "artifact-99"
    assert action.get("requires_approval") is True


# ── _derive_suggestions — no state writes ─────────────────────────────────────

def test_no_state_writes_to_interests_json(tmp_interests):
    interest = create_interest("test interest", tags=["test"])

    # Read before
    with open(tmp_interests) as f:
        before = json.load(f)

    artifact_meta = {"id": "a1", "title": "Test Artifact"}
    relevance_result = [
        {
            "id": interest["id"], "name": "test_interest",
            "display_name": "test interest",
            "score": 4, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    # Call multiple times — no writes expected
    for _ in range(3):
        _derive_suggestions(artifact_meta, relevance_result)

    # Read after
    with open(tmp_interests) as f:
        after = json.load(f)

    assert before == after


def test_no_interest_creation_on_suggestion_call(tmp_interests):
    """Calling _derive_suggestions must not create new interests."""
    artifact_meta = {"id": "a1", "title": "Test"}
    relevance_result = []  # empty

    _derive_suggestions(artifact_meta, relevance_result)

    with open(str(tmp_interests)) as f:
        data = json.load(f)
    # Should still have 0 interests (no interest was created)
    assert len(data["interests"]) == 0


# ── _derive_suggestions — reasons passed through ──────────────────────────────

def test_reasons_passed_through(tmp_interests):
    interest = create_interest("calibration", tags=["calibration"])

    artifact_meta = {"id": "a1", "title": "Calibration Study"}
    relevance_result = [
        {
            "id": interest["id"], "name": "calibration",
            "display_name": "calibration",
            "score": 5,
            "match_reasons": [
                "matched tag: calibration",
                "query text contains tag: calibration",
                "recent activity within 48 hours",
            ],
            "tags": ["calibration"],
            "occurrence_count": 0,
            "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    reasons = suggestions[0]["reasons"]
    assert len(reasons) == 3
    assert "matched tag: calibration" in reasons


# ── _derive_suggestions — multiple interests produce multiple suggestions ──────

def test_multiple_interests_multiple_suggestions(tmp_interests):
    interest1 = create_interest("governance", tags=["governance"])
    interest2 = create_interest("quality", tags=["quality"])

    artifact_meta = {"id": "a1", "title": "Governance and Quality Review"}
    relevance_result = [
        {
            "id": interest1["id"], "name": "governance",
            "display_name": "governance",
            "score": 5, "match_reasons": ["matched tag: governance"],
            "tags": ["governance"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        },
        {
            "id": interest2["id"], "name": "quality",
            "display_name": "quality",
            "score": 4, "match_reasons": ["matched tag: quality"],
            "tags": ["quality"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        },
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    assert len(suggestions) == 2
    interest_names = {s["action"]["interest_name"] for s in suggestions}
    assert "governance" in interest_names
    assert "quality" in interest_names


# ── _derive_suggestions — item_id from title when no id ───────────────────────

def test_item_id_falls_back_to_title(tmp_interests):
    interest = create_interest("test", tags=["test"])

    artifact_meta = {"title": "My Important Report"}  # no "id" field
    relevance_result = [
        {
            "id": interest["id"], "name": "test",
            "display_name": "test",
            "score": 4, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    assert suggestions[0]["action"]["item_id"] == "My Important Report"


# ── Ephemeral cooldown tests ─────────────────────────────────────────────────

def test_first_call_appears(tmp_interests):
    """First call for a given interest_id + item_id should surface."""
    interest = create_interest("test interest", tags=["test"])

    artifact_meta = {"id": "artifact-1", "title": "Test Artifact"}
    relevance_result = [
        {
            "id": interest["id"], "name": "test_interest",
            "display_name": "test interest",
            "score": 5, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    # Clear any prior cooldown state
    from sim import _derive_suggestions
    _derive_suggestions._cooldown_store = {}

    suggestions = _derive_suggestions(artifact_meta, relevance_result)
    assert len(suggestions) == 1


def test_repeated_call_suppressed_within_cooldown(tmp_interests):
    """Second call for same interest_id + item_id should be suppressed for 12h."""
    interest = create_interest("test interest", tags=["test"])

    artifact_meta = {"id": "artifact-1", "title": "Test Artifact"}
    relevance_result = [
        {
            "id": interest["id"], "name": "test_interest",
            "display_name": "test interest",
            "score": 5, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    from sim import _derive_suggestions
    _derive_suggestions._cooldown_store = {}

    # First call — should appear
    suggestions1 = _derive_suggestions(artifact_meta, relevance_result)
    assert len(suggestions1) == 1

    # Second call — should be suppressed (within cooldown)
    suggestions2 = _derive_suggestions(artifact_meta, relevance_result)
    assert len(suggestions2) == 0, "Should be suppressed by 12h cooldown"


def test_different_item_id_still_surfaces(tmp_interests):
    """Different artifact (different item_id) should not be suppressed."""
    interest = create_interest("test interest", tags=["test"])

    relevance_result = [
        {
            "id": interest["id"], "name": "test_interest",
            "display_name": "test interest",
            "score": 5, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    from sim import _derive_suggestions
    _derive_suggestions._cooldown_store = {}

    # First artifact
    artifact1 = {"id": "artifact-1", "title": "Artifact 1"}
    suggestions1 = _derive_suggestions(artifact1, relevance_result)
    assert len(suggestions1) == 1

    # Different artifact — should NOT be suppressed
    artifact2 = {"id": "artifact-2", "title": "Artifact 2"}
    suggestions2 = _derive_suggestions(artifact2, relevance_result)
    assert len(suggestions2) == 1, "Different item_id should not be suppressed"


def test_different_interest_id_still_surfaces(tmp_interests):
    """Different interest for same artifact should not be suppressed."""
    interest1 = create_interest("interest one", tags=["test"])
    interest2 = create_interest("interest two", tags=["test"])

    artifact_meta = {"id": "artifact-1", "title": "Test Artifact"}

    from sim import _derive_suggestions
    _derive_suggestions._cooldown_store = {}

    # First interest for artifact
    rel1 = [
        {
            "id": interest1["id"], "name": "interest_one",
            "display_name": "interest one",
            "score": 5, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]
    suggestions1 = _derive_suggestions(artifact_meta, rel1)
    assert len(suggestions1) == 1

    # Second different interest for same artifact — should NOT be suppressed
    rel2 = [
        {
            "id": interest2["id"], "name": "interest_two",
            "display_name": "interest two",
            "score": 4, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]
    suggestions2 = _derive_suggestions(artifact_meta, rel2)
    assert len(suggestions2) == 1, "Different interest_id should not be suppressed"


def test_cooldown_expiry_allows_suggestion_again(tmp_interests):
    """After cooldown expires, suggestion should appear again."""
    interest = create_interest("test interest", tags=["test"])

    artifact_meta = {"id": "artifact-1", "title": "Test Artifact"}
    relevance_result = [
        {
            "id": interest["id"], "name": "test_interest",
            "display_name": "test interest",
            "score": 5, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    from sim import _derive_suggestions
    _derive_suggestions._cooldown_store = {}

    # First call — should appear
    suggestions1 = _derive_suggestions(artifact_meta, relevance_result)
    assert len(suggestions1) == 1

    # Manually advance cooldown by setting timestamp to 13 hours ago
    cooldown_key = f"{interest['id']}:artifact-1:interest_occurrence"
    import time
    _derive_suggestions._cooldown_store[cooldown_key] = time.time() - (13 * 3600)

    # This call should succeed since cooldown has expired
    suggestions2 = _derive_suggestions(artifact_meta, relevance_result)
    assert len(suggestions2) == 1, "Suggestion should reappear after cooldown expires"


def test_cooldown_store_ephemeral_not_persisted(tmp_interests):
    """Cooldown store is in-memory only — not written to interests.json."""
    interest = create_interest("test interest", tags=["test"])

    artifact_meta = {"id": "artifact-1", "title": "Test Artifact"}
    relevance_result = [
        {
            "id": interest["id"], "name": "test_interest",
            "display_name": "test interest",
            "score": 5, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    from sim import _derive_suggestions
    _derive_suggestions._cooldown_store = {}

    # Read interests.json before
    with open(str(tmp_interests)) as f:
        before = json.load(f)

    # Call multiple times
    _derive_suggestions(artifact_meta, relevance_result)
    _derive_suggestions(artifact_meta, relevance_result)
    _derive_suggestions(artifact_meta, relevance_result)

    # Read after
    with open(str(tmp_interests)) as f:
        after = json.load(f)

    assert before == after, "interests.json must not be modified by suggestion calls"


def test_no_state_writes_interest_count_unchanged(tmp_interests):
    """Verify that cooldown and suggestion calls do not create interests."""
    interest = create_interest("test", tags=["test"])

    artifact_meta = {"id": "artifact-1", "title": "Test"}
    relevance_result = [
        {
            "id": interest["id"], "name": "test",
            "display_name": "test",
            "score": 4, "match_reasons": ["matched tag: test"],
            "tags": ["test"], "occurrence_count": 0, "last_seen_at": "2026-04-20T12:00:00Z",
        }
    ]

    from sim import _derive_suggestions
    _derive_suggestions._cooldown_store = {}

    _derive_suggestions(artifact_meta, relevance_result)
    _derive_suggestions(artifact_meta, relevance_result)

    with open(str(tmp_interests)) as f:
        data = json.load(f)
    assert len(data["interests"]) == 1, "No new interests should be created"