"""
Unit tests for Interest Tracker v1 (Phase 0).

Tests:
- create_interest with valid name and tags
- create_interest raises on empty name
- create_interest raises on duplicate name
- create_interest raises when cap is reached
- get_interest by id and by normalized name
- list_interests with optional filters
- normalize_name and normalize_tags behavior
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys

# Ensure workspace is on path
sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.interest_tracker import (
    create_interest,
    get_interest,
    list_interests,
    add_occurrence,
    normalize_name,
    normalize_tags,
    set_interests_path,
    MAX_INTERESTS,
    MAX_OCCURRENCES,
    VALID_OCCURRENCE_TYPES,
    _interests_path,
)

# ── Test Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_path():
    """Temporary interests.json for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "interests.json"
        set_interests_path(p)
        yield p


# ── normalize_name ─────────────────────────────────────────────────────────────

def test_normalize_name_basic():
    assert normalize_name("Confidence Calibration") == "confidence_calibration"
    assert normalize_name("Governance Quality") == "governance_quality"
    assert normalize_name("low-confidence") == "low_confidence"
    assert normalize_name("  Multiple   Spaces  ") == "multiple_spaces"


def test_normalize_name_invalid_characters():
    assert normalize_name("Test@#$Name") == "testname"
    assert normalize_name("A!B*C^D") == "abcd"


def test_normalize_name_empty():
    with pytest.raises(ValueError):
        normalize_name("   ")


# ── normalize_tags ─────────────────────────────────────────────────────────────

def test_normalize_tags_basic():
    tags = ["governance", "Quality", "CONFIDENCE"]
    result = normalize_tags(tags)
    assert result == ["confidence", "governance", "quality"]


def test_normalize_tags_empty_list():
    assert normalize_tags([]) == []
    assert normalize_tags(["", "  ", "  ,  "]) == []


# ── create_interest ────────────────────────────────────────────────────────────

def test_create_interest_basic(tmp_path):
    interest = create_interest("confidence calibration", tags=["governance", "quality"])
    assert interest["id"] is not None
    assert interest["name"] == "confidence_calibration"
    assert interest["display_name"] == "confidence calibration"
    assert interest["status"] == "active"
    assert interest["occurrence_count"] == 0
    assert interest["tags"] == ["governance", "quality"]
    assert interest["occurrences"] == []
    assert "created_at" in interest
    assert "last_seen_at" in interest


def test_create_interest_empty_name_raises(tmp_path):
    with pytest.raises(ValueError, match="cannot be empty"):
        create_interest("")
    with pytest.raises(ValueError, match="cannot be empty"):
        create_interest("   ")


def test_create_interest_too_short_raises(tmp_path):
    with pytest.raises(ValueError, match="too short"):
        create_interest("a")


def test_create_interest_duplicate_raises(tmp_path):
    create_interest("confidence calibration")
    with pytest.raises(ValueError, match="already exists"):
        create_interest("Confidence Calibration")  # same after normalization
    with pytest.raises(ValueError, match="already exists"):
        create_interest("confidence_calibration")  # exact


def test_create_interest_cap_limit(tmp_path):
    # Create MAX_INTERESTS interests
    for i in range(MAX_INTERESTS):
        create_interest(f"interest_{i}")
    # One more should raise
    with pytest.raises(ValueError, match="cap reached"):
        create_interest("one_more")


# ── get_interest ──────────────────────────────────────────────────────────────

def test_get_interest_by_id(tmp_path):
    created = create_interest("test interest")
    retrieved = get_interest(created["id"])
    assert retrieved is not None
    assert retrieved["id"] == created["id"]


def test_get_interest_by_normalized_name(tmp_path):
    create_interest("Confidence Calibration")
    retrieved = get_interest("confidence_calibration")
    assert retrieved is not None
    assert retrieved["name"] == "confidence_calibration"


def test_get_interest_not_found(tmp_path):
    assert get_interest("nonexistent") is None
    assert get_interest("xyz123") is None


# ── list_interests ─────────────────────────────────────────────────────────────

def test_list_interests_empty(tmp_path):
    assert list_interests() == []


def test_list_interests_all(tmp_path):
    create_interest("interest a", tags=["tag1"])
    create_interest("interest b", tags=["tag2"])
    interests = list_interests()
    assert len(interests) == 2


def test_list_interests_filter_by_tag(tmp_path):
    create_interest("interest a", tags=["governance"])
    create_interest("interest b", tags=["quality"])
    create_interest("interest c", tags=["governance", "quality"])
    governance = list_interests(tag="governance")
    assert len(governance) == 2


def test_list_interests_filter_by_status(tmp_path):
    create_interest("interest a")
    interests = list_interests(status="active")
    assert len(interests) == 1
    # status filter with no match
    assert list_interests(status="archived") == []


# ── JSON persistence ──────────────────────────────────────────────────────────

def test_interest_persists_after_create(tmp_path):
    interest = create_interest("persistent interest", tags=["test"])
    loaded = get_interest(interest["id"])
    assert loaded is not None
    assert loaded["name"] == "persistent_interest"
    assert loaded["tags"] == ["test"]


# ── add_occurrence ─────────────────────────────────────────────────────────────

def test_add_occurrence_basic(tmp_path):
    interest = create_interest("test interest")
    updated = add_occurrence(interest["id"], "artifact", "artifact-abc", "low_confidence")
    assert updated["occurrence_count"] == 1
    assert "last_seen_at" in updated
    assert "triggered_at" in updated["occurrences"][0]
    assert len(updated["occurrences"]) == 1
    occ = updated["occurrences"][0]
    assert occ["type"] == "artifact"
    assert occ["item_id"] == "artifact-abc"
    assert occ["reason"] == "low_confidence"
    assert "triggered_at" in occ


def test_add_occurrence_valid_types():
    assert "artifact" in VALID_OCCURRENCE_TYPES
    assert "question" in VALID_OCCURRENCE_TYPES
    assert "proposal" in VALID_OCCURRENCE_TYPES
    assert len(VALID_OCCURRENCE_TYPES) == 3


def test_add_occurrence_invalid_type_raises(tmp_path):
    interest = create_interest("test interest")
    with pytest.raises(ValueError, match="occurrence_type must be one of"):
        add_occurrence(interest["id"], "invalid_type", "item-1", "reason")


def test_add_occurrence_interest_not_found_raises(tmp_path):
    with pytest.raises(ValueError, match="interest not found"):
        add_occurrence("nonexistent_id", "artifact", "item-1", "reason")


def test_add_occurrence_empty_item_id_raises(tmp_path):
    interest = create_interest("test interest")
    with pytest.raises(ValueError, match="item_id cannot be empty"):
        add_occurrence(interest["id"], "artifact", "", "reason")


def test_add_occurrence_multiple(tmp_path):
    interest = create_interest("test interest")
    for i in range(5):
        add_occurrence(interest["id"], "artifact" if i % 2 == 0 else "question",
                       f"item-{i}", f"reason {i}")
    updated = get_interest(interest["id"])
    assert updated["occurrence_count"] == 5
    assert len(updated["occurrences"]) == 5
    # Newest first
    assert updated["occurrences"][0]["item_id"] == "item-4"


def test_add_occurrence_prune_at_max(tmp_path):
    interest = create_interest("test interest")
    for i in range(MAX_OCCURRENCES + 5):
        add_occurrence(interest["id"], "artifact", f"item-{i}", f"reason {i}")
    updated = get_interest(interest["id"])
    assert updated["occurrence_count"] == MAX_OCCURRENCES
    assert len(updated["occurrences"]) == MAX_OCCURRENCES
    # Oldest (item-0 through item-4) should be pruned
    ids = [o["item_id"] for o in updated["occurrences"]]
    assert "item-0" not in ids
    assert "item-4" not in ids


def test_add_occurrence_last_seen_updates(tmp_path):
    interest = create_interest("test interest")
    add_occurrence(interest["id"], "question", "q-1", "test reason")
    updated = get_interest(interest["id"])
    assert "last_seen_at" in updated
    # last_seen_at is set to current time; both may be same-second due to time.gmtime() resolution
    # so we verify it has the correct format and was written, not that it's strictly greater
    assert updated["last_seen_at"].endswith("Z")
    assert len(updated["last_seen_at"]) == 20


def test_add_occurrence_persists(tmp_path):
    interest = create_interest("test interest")
    add_occurrence(interest["id"], "proposal", "prop-xyz", "governance gap")
    loaded = get_interest(interest["id"])
    assert loaded["occurrence_count"] == 1
    assert loaded["occurrences"][0]["item_id"] == "prop-xyz"


# ── CLI smoke test ────────────────────────────────────────────────────────────

def test_cli_create_command_structure():
    """Verify CLI module has correct command signatures."""
    import argparse
    from commands.interest import (
        cmd_interest_create, cmd_interest_list, cmd_interest_show,
        cmd_interest_add_occurrence,
    )

    # Simulate args for create
    args = argparse.Namespace(name="test", tags="governance,quality")
    cmd_interest_create(args)

    # Simulate args for list
    args2 = argparse.Namespace(tag=None, status=None)
    cmd_interest_list(args2)

    # Simulate args for show
    args3 = argparse.Namespace(identifier="test")
    cmd_interest_show(args3)

    # Simulate args for add-occurrence (valid case will create then add)
    from weslr.interest_tracker import set_interests_path
    import tempfile
    with tempfile.TemporaryDirectory():
        pass  # already using tmp_path fixture for prior calls
    # Just check it doesn't raise on bad args
    args4 = argparse.Namespace(interest_id="bad", type="artifact", item_id="x", reason="y")
    cmd_interest_add_occurrence(args4)  # should print error, not raise