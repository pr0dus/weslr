"""
test_project_registry.py

Tests for WESLR Project Registry V1.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from weslr.project_registry import (
    register_project,
    list_projects,
    get_project,
    set_active_project,
    get_active_project,
    clear_active_project,
    _normalize_project_name,
    DEFAULT_REGISTRY_PATH,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_registry():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def session_id():
    return "test-session-001"


@pytest.fixture(autouse=True)
def clean_active_store():
    """Clear _ACTIVE_PROJECT_STORE before and after each test for isolation."""
    from weslr import project_registry as pr
    pr._ACTIVE_PROJECT_STORE.clear()
    yield
    pr._ACTIVE_PROJECT_STORE.clear()


# ─── _normalize_project_name ─────────────────────────────────────────────────

class TestNormalizeProjectName:
    def test_lowercase(self):
        assert _normalize_project_name("Project Phoenix") == "project_phoenix"

    def test_underscores_replaced(self):
        assert _normalize_project_name("project-phoenix") == "project_phoenix"

    def test_collapse_multi_underscore(self):
        assert _normalize_project_name("project___phoenix") == "project_phoenix"

    def test_strip_edge_underscores(self):
        assert _normalize_project_name("_project_phoenix_") == "project_phoenix"

    def test_empty(self):
        assert _normalize_project_name("") == ""
        assert _normalize_project_name(None) == ""


# ─── register_project ────────────────────────────────────────────────────────

class TestRegisterProject:
    def test_registers_new_project(self, temp_registry):
        result = register_project(
            name="Project Phoenix",
            description="Test new materials for propulsion",
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["status"] == "registered"
        project = result["project"]
        assert project["project_id"].startswith("PRJ-")
        assert project["name"] == "Project Phoenix"
        assert project["description"] == "Test new materials for propulsion"
        assert project["owner_user_id"] == "arthur"
        assert project["automatic_action"] is False
        assert project["hidden_learning"] is False
        assert project["raw_prompt_stored"] is False

    def test_project_id_unique_increments(self, temp_registry):
        r1 = register_project("Alpha", "desc", "arthur", registry_path=temp_registry)
        r2 = register_project("Beta", "desc", "arthur", registry_path=temp_registry)
        assert r1["project"]["project_id"] != r2["project"]["project_id"]

    def test_duplicate_name_same_owner_raises(self, temp_registry):
        register_project("Phoenix", "desc", "arthur", registry_path=temp_registry)
        with pytest.raises(ValueError, match="already exists"):
            register_project("Phoenix", "desc2", "arthur", registry_path=temp_registry)

    def test_same_name_different_owner_allowed(self, temp_registry):
        register_project("Phoenix", "desc", "arthur", registry_path=temp_registry)
        # Should not raise — different owner
        r2 = register_project("Phoenix", "desc", "bob", registry_path=temp_registry)
        assert r2["status"] == "registered"

    def test_empty_name_raises(self, temp_registry):
        with pytest.raises(ValueError, match="required"):
            register_project("", "desc", "arthur", registry_path=temp_registry)
        with pytest.raises(ValueError, match="required"):
            register_project("   ", "desc", "arthur", registry_path=temp_registry)

    def test_written_to_jsonl(self, temp_registry):
        register_project("Gamma", "desc gamma", "arthur", registry_path=temp_registry)
        with open(temp_registry) as f:
            records = [json.loads(line) for line in f if line.strip()]
        assert len(records) == 1
        assert records[0]["record_type"] == "project_registration_v1"
        assert records[0]["authority"] == "project_registry_only"


# ─── list_projects ───────────────────────────────────────────────────────────

class TestListProjects:
    def test_empty_registry(self, temp_registry):
        assert list_projects(registry_path=temp_registry) == []

    def test_returns_all_projects_recent_first(self, temp_registry):
        register_project("Alpha", "", "arthur", registry_path=temp_registry)
        register_project("Beta", "", "arthur", registry_path=temp_registry)
        register_project("Gamma", "", "arthur", registry_path=temp_registry)
        results = list_projects(registry_path=temp_registry)
        assert len(results) == 3
        # Most recent first
        assert results[0]["name"] == "Gamma"

    def test_filter_by_owner(self, temp_registry):
        register_project("Alpha", "", "arthur", registry_path=temp_registry)
        register_project("Beta", "", "bob", registry_path=temp_registry)
        results = list_projects(owner_user_id="arthur", registry_path=temp_registry)
        assert len(results) == 1
        assert results[0]["owner_user_id"] == "arthur"

    def test_nonexistent_path(self):
        assert list_projects(registry_path="/nonexistent/path.jsonl") == []


# ─── get_project ─────────────────────────────────────────────────────────────

class TestGetProject:
    def test_returns_project_by_id(self, temp_registry):
        result = register_project("Delta", "desc", "arthur", registry_path=temp_registry)
        pid = result["project"]["project_id"]
        proj = get_project(pid, registry_path=temp_registry)
        assert proj is not None
        assert proj["project_id"] == pid
        assert proj["name"] == "Delta"

    def test_returns_none_for_unknown_id(self, temp_registry):
        assert get_project("PRJ-99999999-999", registry_path=temp_registry) is None

    def test_nonexistent_path(self):
        assert get_project("PRJ-999", registry_path="/nonexistent") is None


# ─── Active project management ───────────────────────────────────────────────

class TestActiveProject:
    def test_set_and_get_active(self, temp_registry, session_id):
        result = register_project("Epsilon", "desc", "arthur", registry_path=temp_registry)
        pid = result["project"]["project_id"]
        set_result = set_active_project(pid, session_id, registry_path=temp_registry)
        assert set_result["status"] == "active"
        assert get_active_project(session_id) == pid

    def test_set_active_unknown_project(self, session_id):
        result = set_active_project("PRJ-99999999-999", session_id)
        assert result["status"] == "not_found"
        assert get_active_project(session_id) is None

    def test_clear_active_project(self, temp_registry, session_id):
        result = register_project("Zeta", "desc", "arthur", registry_path=temp_registry)
        pid = result["project"]["project_id"]
        set_active_project(pid, session_id)
        clear_active_project(session_id)
        assert get_active_project(session_id) is None

    def test_different_sessions_independent(self, temp_registry):
        r1 = register_project("Eta", "desc", "arthur", registry_path=temp_registry)
        r2 = register_project("Theta", "desc", "arthur", registry_path=temp_registry)
        pid1 = r1["project"]["project_id"]
        pid2 = r2["project"]["project_id"]
        set_active_project(pid1, "session-A", registry_path=temp_registry)
        set_active_project(pid2, "session-B", registry_path=temp_registry)
        assert get_active_project("session-A") == pid1
        assert get_active_project("session-B") == pid2

    def test_get_active_none_if_not_set(self):
        assert get_active_project("nonexistent-session") is None