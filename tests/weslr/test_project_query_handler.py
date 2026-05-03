"""
test_project_query_handler.py

Tests for WESLR Project Query Handler V1.
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
    _ACTIVE_PROJECT_STORE,
)
from weslr.fact_extractor import append_fact_assertion, load_facts
from weslr.project_query_handler import handle_project_command


@pytest.fixture(autouse=True)
def clean_store():
    _ACTIVE_PROJECT_STORE.clear()
    yield
    _ACTIVE_PROJECT_STORE.clear()


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
def temp_facts():
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


# ─── Helpers ─────────────────────────────────────────────────────────────────

def register_and_activate(name, registry_path, session_id):
    result = register_project(name, f"desc for {name}", "arthur", registry_path=registry_path)
    pid = result["project"]["project_id"]
    set_active_project(pid, session_id, registry_path=registry_path)
    return pid


# ─── create project ────────────────────────────────────────────────────────────

class TestCreateProject:
    def test_create_project_simple(self, temp_registry, session_id):
        result = handle_project_command(
            "create project Phoenix",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is True
        assert result["command"] == "create_project"
        assert result["result"]["status"] == "registered"
        assert result["result"]["name"] == "Phoenix"
        assert result["result"]["project_id"].startswith("PRJ-")

    def test_create_project_with_description(self, temp_registry, session_id):
        result = handle_project_command(
            "create project Phoenix with description Test new materials for propulsion",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is True
        assert result["result"]["description"] == "Test new materials for propulsion"

    def test_create_project_duplicate_raises(self, temp_registry, session_id):
        handle_project_command(
            "create project Alpha",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        result2 = handle_project_command(
            "create project Alpha",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result2["handled"] is True
        assert result2["error"] is not None
        assert "already exists" in result2["error"]

    def test_create_project_new_alias(self, temp_registry, session_id):
        result = handle_project_command(
            "new project Beta",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is True
        assert result["command"] == "create_project"
        assert result["result"]["name"] == "Beta"


# ─── list projects ─────────────────────────────────────────────────────────────

class TestListProjects:
    def test_list_projects_empty(self, temp_registry, session_id):
        result = handle_project_command(
            "list projects",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is True
        assert result["command"] == "list_projects"
        assert result["result"]["count"] == 0
        assert result["result"]["projects"] == []

    def test_list_projects_returns_all(self, temp_registry, session_id):
        handle_project_command("create project Alpha", session_id=session_id, owner_user_id="arthur", registry_path=temp_registry)
        handle_project_command("create project Beta", session_id=session_id, owner_user_id="arthur", registry_path=temp_registry)
        result = handle_project_command(
            "list projects",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["result"]["count"] == 2
        names = [p["name"] for p in result["result"]["projects"]]
        assert "Alpha" in names
        assert "Beta" in names

    def test_list_show_alias(self, temp_registry, session_id):
        result = handle_project_command(
            "show project",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is True
        assert result["command"] == "list_projects"


# ─── switch to project ────────────────────────────────────────────────────────

class TestSwitchProject:
    def test_switch_to_project_by_name(self, temp_registry, session_id):
        handle_project_command("create project Gamma", session_id=session_id, owner_user_id="arthur", registry_path=temp_registry)
        result = handle_project_command(
            "switch to project Gamma",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is True
        assert result["command"] == "switch_project"
        assert result["result"]["status"] == "active"
        assert get_active_project(session_id) is not None

    def test_switch_to_project_unknown(self, temp_registry, session_id):
        result = handle_project_command(
            "switch to project NotExist999",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is True
        assert result["error"] is not None
        assert "not found" in result["error"]


# ─── project knowledge query ───────────────────────────────────────────────────

class TestProjectKnowledge:
    def test_project_knowledge_no_facts(self, temp_registry, temp_facts, session_id):
        pid = register_and_activate("Delta", temp_registry, session_id)
        result = handle_project_command(
            "what does project Delta know about robotic arm",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
            fact_store_path=temp_facts,
        )
        assert result["handled"] is True
        assert result["command"] == "project_knowledge"
        assert result["result"]["count"] == 0

    def test_project_knowledge_with_facts(self, temp_registry, temp_facts, session_id):
        pid = register_and_activate("Epsilon", temp_registry, session_id)
        # Append some scoped facts
        append_fact_assertion(
            {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"},
            "ref1",
            project_id=pid,
            fact_store_path=temp_facts,
        )
        append_fact_assertion(
            {"subject": "arthur", "predicate": "tested", "object": "gripper_calibration"},
            "ref2",
            project_id=pid,
            fact_store_path=temp_facts,
        )
        result = handle_project_command(
            "what does project Epsilon know about robotic arm",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
            fact_store_path=temp_facts,
        )
        assert result["handled"] is True
        assert result["result"]["count"] >= 1
        # At least one fact should mention robotic_arm
        fact_texts = [f"{f['subject']} {f['predicate']} {f['object']}" for f in result["result"]["facts"]]
        assert any("robotic_arm" in t for t in fact_texts)

    def test_project_knowledge_unknown_project(self, temp_registry, temp_facts, session_id):
        result = handle_project_command(
            "what does project NonExistent know about AI",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
            fact_store_path=temp_facts,
        )
        assert result["handled"] is True
        assert result["error"] is not None

    def test_project_knowledge_all_facts(self, temp_registry, temp_facts, session_id):
        pid = register_and_activate("Zeta", temp_registry, session_id)
        append_fact_assertion(
            {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"},
            "ref1",
            project_id=pid,
            fact_store_path=temp_facts,
        )
        result = handle_project_command(
            "what does project Zeta know",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
            fact_store_path=temp_facts,
        )
        assert result["handled"] is True
        assert result["command"] == "project_knowledge_all"
        assert result["result"]["count"] == 1

    def test_project_knowledge_active_project_it(self, temp_registry, temp_facts, session_id):
        pid = register_and_activate("Eta", temp_registry, session_id)
        append_fact_assertion(
            {"subject": "arthur", "predicate": "discussed", "object": "calibration"},
            "ref1",
            project_id=pid,
            fact_store_path=temp_facts,
        )
        # "it" refers to the active project
        result = handle_project_command(
            "what does project it know about calibration",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
            fact_store_path=temp_facts,
        )
        assert result["handled"] is True
        assert result["result"]["count"] == 1

    def test_not_handled(self, temp_registry, session_id):
        result = handle_project_command(
            "what is the weather today",
            session_id=session_id,
            owner_user_id="arthur",
            registry_path=temp_registry,
        )
        assert result["handled"] is False
        assert result["command"] == "unknown"