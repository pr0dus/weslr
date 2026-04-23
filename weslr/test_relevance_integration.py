"""
Integration tests for _derive_relevant_interests (Phase 3).

Tests:
- returns empty list when no interests exist
- returns metadata field when relevant interests exist
- returns empty list when artifact has no queryable fields
- interests.json unchanged before/after call
- existing artifact response fields unchanged except _relevant_interests
- no state writes from integration
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.interest_tracker import (
    create_interest, set_interests_path,
)
from weslr.relevance_surface import query_relevant_interests


@pytest.fixture
def tmp_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "interests.json"
        set_interests_path(p)
        yield p


# ── Integration tests for _derive_relevant_interests ─────────────────────────

def test_returns_empty_list_when_no_interests(tmp_path):
    """When no interests exist, _derive_relevant_interests returns []."""
    from sim import _derive_relevant_interests

    artifact_meta = {
        "title": "governance quality report",
        "niche_theme": "quality",
        "problem_statement": "governance gaps",
    }
    result = _derive_relevant_interests(artifact_meta)
    assert result == []


def test_returns_metadata_field_when_relevant_interests_exist(tmp_path):
    """When interests match artifact fields, _derive_relevant_interests returns scored list."""
    from sim import _derive_relevant_interests

    # Create an interest that will match governance quality
    interest = create_interest("governance quality", tags=["governance", "quality"])

    artifact_meta = {
        "title": "governance quality report",
        "niche_theme": "quality assurance",
        "problem_statement": "governance gaps in system",
    }
    result = _derive_relevant_interests(artifact_meta)
    assert isinstance(result, list)
    assert len(result) >= 1
    # Check structure of returned items
    first = result[0]
    assert "id" in first
    assert "name" in first
    assert "display_name" in first
    assert "score" in first
    assert "match_reasons" in first
    assert "last_seen_at" in first
    assert "occurrence_count" in first
    assert "tags" in first


def test_returns_empty_when_artifact_has_no_queryable_fields(tmp_path):
    """When artifact has no useful text fields, returns empty list."""
    from sim import _derive_relevant_interests

    artifact_meta = {
        "id": "some-id",
        # No title, niche_theme, problem_statement, family, or target_user
        "scores": {"internal_score": 0.8},
    }
    result = _derive_relevant_interests(artifact_meta)
    assert result == []


def test_interests_json_unchanged_before_after(tmp_path):
    """Calling _derive_relevant_interests does not modify interests.json."""
    from sim import _derive_relevant_interests

    interest = create_interest("test interest", tags=["test"])

    # Read before
    with open(tmp_path) as f:
        before = json.load(f)

    # Call function multiple times
    artifact_meta = {"title": "test title"}
    _derive_relevant_interests(artifact_meta)
    _derive_relevant_interests(artifact_meta)

    # Read after
    with open(tmp_path) as f:
        after = json.load(f)

    assert before == after


def test_derive_relevant_interests_read_only_never_writes(tmp_path):
    """Verify that _derive_relevant_interests never creates interests or occurrences."""
    from sim import _derive_relevant_interests

    # Create one interest
    interest = create_interest("existing interest", tags=["test"])

    # Call function — it should not create new interests
    artifact_meta = {"title": "some artifact title"}
    _derive_relevant_interests(artifact_meta)

    # Check interests.json still has exactly 1 interest
    with open(tmp_path) as f:
        data = json.load(f)
    assert len(data["interests"]) == 1
    assert data["interests"][0]["occurrence_count"] == 0


def test_metadata_field_added_but_response_structure_unchanged(tmp_path):
    """Confirm _derive_relevant_interests returns a list, not a dict, for easy field attach."""
    from sim import _derive_relevant_interests

    create_interest("test", tags=["test"])
    artifact_meta = {"title": "test title"}
    result = _derive_relevant_interests(artifact_meta)
    # Should be a list (to attach as _relevant_interests array field)
    assert isinstance(result, list)
    # Each item should be a dict
    for item in result:
        assert isinstance(item, dict)


def test_empty_query_returns_empty(tmp_path):
    """When all artifact fields are empty strings, returns []."""
    from sim import _derive_relevant_interests

    artifact_meta = {
        "title": "",
        "niche_theme": "",
        "problem_statement": "",
        "family": "",
        "target_user": "",
    }
    result = _derive_relevant_interests(artifact_meta)
    assert result == []


def test_none_fields_handled_gracefully(tmp_path):
    """None values in artifact fields should be skipped gracefully."""
    from sim import _derive_relevant_interests

    artifact_meta = {
        "title": None,
        "niche_theme": "quality",
        "problem_statement": None,
        "family": "",
        "target_user": None,
    }
    result = _derive_relevant_interests(artifact_meta)
    # Should not raise — returns empty or list depending on matching interests
    assert isinstance(result, list)


def test_score_derivation_matches_direct_relevance_surface_call(tmp_path):
    """Verify that _derive_relevant_interests produces the same results as calling
    query_relevant_interests directly with the same inputs."""
    from sim import _derive_relevant_interests

    create_interest("governance transparency", tags=["governance", "transparency"])

    artifact_meta = {
        "title": "governance report",
        "niche_theme": "governance",
        "problem_statement": "transparency in decisions",
    }

    integrated_result = _derive_relevant_interests(artifact_meta)
    direct_result = query_relevant_interests(
        text="governance report governance transparency in decisions",
        tags=None,
        top_n=3,
        status="active",
    )

    # Both should return non-empty (matching interest exists)
    assert len(integrated_result) >= 1
    assert len(direct_result) >= 1
    # First result id should match (same interest ranked highest)
    assert integrated_result[0]["id"] == direct_result[0]["id"]