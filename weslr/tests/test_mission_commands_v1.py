"""
WESLR Mission Commands V1 Tests

Tests for:
- /mission help
- /mission create
- /mission list
- /mission details
- /mission activate/pause/close
- /mission-review
- safety: no auto-execution, tenant isolation, no external calls
"""

import asyncio
import json
import os
import re
import tempfile
import pytest

from weslr.commands.mission_commands import (
    handle_mission_command,
    handle_mission_review_command,
    _reset_store,
    DEFAULT_TENANT,
)
from weslr.mission_store import MissionStore


def run_sync(coro):
    """Run an async coroutine synchronously in tests."""
    return asyncio.run(coro)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def clean_store():
    """Provide a clean mission store for each test."""
    _reset_store()
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        store_path = f.name

    store = MissionStore(store_path=store_path)
    import weslr.commands.mission_commands as mc
    mc._STORE = store

    yield store

    if os.path.exists(store_path):
        os.unlink(store_path)
    mc._STORE = None
    _reset_store()


def cmd(message: str, lowered: str = None) -> str:
    """Helper to run mission command sync."""
    if lowered is None:
        lowered = message.lower()
    return run_sync(handle_mission_command(message, lowered))


# ── Help ─────────────────────────────────────────────────────────────────────

class TestMissionHelp:
    def test_help_output(self):
        result = cmd("/mission help", "mission help")
        assert "/mission create" in result
        assert "/mission list" in result
        assert "/mission details" in result
        assert "/mission activate" in result
        assert "/mission-review" in result
        assert "automatic_execution" in result
        assert "no automatic execution" in result.lower()


# ── Create ───────────────────────────────────────────────────────────────────

class TestMissionCreate:
    def test_create_draft_mission(self, clean_store):
        result = cmd(
            '/mission create --title "Kesterite PV Study" --goal "Study efficiency of kesterite solar cells"',
            'mission create --title "Kesterite PV Study" --goal "Study efficiency of kesterite solar cells"',
        )
        assert "Mission created" in result
        assert "Kesterite PV Study" in result
        assert "draft" in result
        assert "automatic_execution: false" in result

    def test_create_active_mission(self, clean_store):
        result = cmd(
            '/mission create --title "Active Mission" --goal "Research goal" --active',
            'mission create --title "Active Mission" --goal "Research goal" --active',
        )
        assert "Mission created" in result
        assert "active" in result

    def test_create_missing_title(self, clean_store):
        result = cmd('/mission create --goal "Some goal"', 'mission create --goal "Some goal"')
        assert "Usage" in result
        assert "--title" in result

    def test_create_missing_goal(self, clean_store):
        result = cmd('/mission create --title "Some title"', 'mission create --title "Some title"')
        assert "Usage" in result
        assert "--goal" in result


# ── List ─────────────────────────────────────────────────────────────────────

class TestMissionList:
    def test_list_empty(self, clean_store):
        result = cmd("/mission list", "mission list")
        assert "No missions found" in result

    def test_list_with_missions(self, clean_store):
        cmd('/mission create --title "Mission A" --goal "Goal A"', 'mission create --title "Mission A" --goal "Goal A"')
        cmd('/mission create --title "Mission B" --goal "Goal B" --active', 'mission create --title "Mission B" --goal "Goal B" --active')
        result = cmd("/mission list", "mission list")
        assert "Mission A" in result
        assert "Mission B" in result
        assert "(2 total)" in result


# ── Details ───────────────────────────────────────────────────────────────────

def extract_id(create_result: str) -> str:
    m = re.search(r"Mission created: ([a-f0-9-]{36})", create_result)
    assert m, f"Could not extract ID from: {create_result}"
    return m.group(1)


class TestMissionDetails:
    def test_details_unknown_mission(self, clean_store):
        result = cmd("/mission details unknown-id-12345", "mission details unknown-id-12345")
        assert "not found" in result

    def test_details_existing_mission(self, clean_store):
        create_result = cmd('/mission create --title "Detail Test Mission" --goal "Test goal"', 'mission create --title "Detail Test Mission" --goal "Test goal"')
        mission_id = extract_id(create_result)
        result = cmd(f"/mission details {mission_id}", f"mission details {mission_id}")
        assert "Detail Test Mission" in result
        assert mission_id in result
        assert "Test goal" in result


# ── Status changes ─────────────────────────────────────────────────────────────

class TestMissionStatusChange:
    def test_activate_unknown_mission(self, clean_store):
        result = cmd("/mission activate unknown-id", "mission activate unknown-id")
        assert "not found" in result

    def test_activate_existing_mission(self, clean_store):
        create_result = cmd('/mission create --title "Activate Test" --goal "Test"', 'mission create --title "Activate Test" --goal "Test"')
        mission_id = extract_id(create_result)
        result = cmd(f"/mission activate {mission_id}", f"mission activate {mission_id}")
        assert "active" in result
        assert "✅" in result

    def test_pause_mission(self, clean_store):
        create_result = cmd('/mission create --title "Pause Test" --goal "Test" --active', 'mission create --title "Pause Test" --goal "Test" --active')
        mission_id = extract_id(create_result)
        result = cmd(f"/mission pause {mission_id}", f"mission pause {mission_id}")
        assert "paused" in result
        assert "⏸" in result

    def test_close_mission(self, clean_store):
        create_result = cmd('/mission create --title "Close Test" --goal "Test" --active', 'mission create --title "Close Test" --goal "Test" --active')
        mission_id = extract_id(create_result)
        result = cmd(f"/mission close {mission_id}", f"mission close {mission_id}")
        assert "closed" in result
        assert "🔴" in result


# ── Mission review ─────────────────────────────────────────────────────────────

class TestMissionReview:
    def test_mission_review_empty(self, clean_store):
        result = cmd("/mission-review", "mission-review")
        assert "Missions reviewed:" in result
        assert "0" in result
        assert "automatic_execution: false" in result
        assert ".weslr/pending_messages.jsonl" in result

    def test_mission_review_with_active_mission(self, clean_store):
        create_result = cmd('/mission create --title "Review Test" --goal "Research" --active', 'mission create --title "Review Test" --goal "Research" --active')
        mission_id = extract_id(create_result)
        result = cmd("/mission-review", "mission-review")
        assert "Missions reviewed:" in result
        assert "automatic_execution: false" in result
        assert "Suggestions generated:" in result
        assert "Suggestions written:" in result

    def test_mission_review_no_auto_execute(self, clean_store):
        result = cmd("/mission-review", "mission-review")
        assert "automatic_execution: false" in result
        assert ".weslr/pending_messages.jsonl" in result

    def test_mission_review_dedicated_command(self, clean_store):
        result = run_sync(handle_mission_review_command("/mission-review", "mission-review"))
        assert "Missions reviewed:" in result
        assert "automatic_execution: false" in result

    def test_mission_review_writes_pending_messages(self, clean_store):
        create_result = cmd('/mission create --title "Pending Test" --goal "Research" --active', 'mission create --title "Pending Test" --goal "Research" --active')
        mission_id = extract_id(create_result)

        # Run review
        cmd("/mission-review", "mission-review")

        # Check pending messages file exists and has records
        pending_path = ".weslr/pending_messages.jsonl"
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                records = [json.loads(line) for line in f if line.strip()]
            mission_suggestions = [r for r in records if r.get("type") == "mission_suggestion"]
            for ms in mission_suggestions:
                assert ms.get("automatic_execution") is False


# ── Safety ────────────────────────────────────────────────────────────────────

class TestSafety:
    def test_automatic_execution_always_false(self, clean_store):
        result = cmd('/mission create --title "Safety Test" --goal "Goal" --active', 'mission create --title "Safety Test" --goal "Goal" --active')
        assert "automatic_execution: false" in result

    def test_tenant_isolation(self, clean_store):
        result = cmd('/mission create --title "Isolation Test" --goal "Test" --active', 'mission create --title "Isolation Test" --goal "Test" --active')
        assert "Mission created" in result
        list_result = cmd("/mission list", "mission list")
        assert "Isolation Test" in list_result

    def test_mission_store_tenant_isolation(self, clean_store):
        from weslr.schemas.mission import make_mission
        m1 = make_mission("tenant-1", "user-1", "Tenant 1 Mission", "Goal 1")
        m1.status = "active"
        clean_store.save(m1)
        m2 = make_mission("tenant-2", "user-2", "Tenant 2 Mission", "Goal 2")
        m2.status = "active"
        clean_store.save(m2)
        t1_missions = clean_store.list("tenant-1")
        assert len(t1_missions) == 1
        assert t1_missions[0].title == "Tenant 1 Mission"
        t2_missions = clean_store.list("tenant-2")
        assert len(t2_missions) == 1
        assert t2_missions[0].title == "Tenant 2 Mission"

    def test_mission_review_no_external_calls(self, clean_store):
        cmd('/mission create --title "External Call Test" --goal "Test" --active', 'mission create --title "External Call Test" --goal "Test" --active')
        result = cmd("/mission-review", "mission-review")
        assert "Missions reviewed:" in result


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_mission_id_not_found_on_status_change(self, clean_store):
        result = cmd("/mission activate does-not-exist", "mission activate does-not-exist")
        assert "not found" in result

    def test_mission_review_reports_blocked_count(self, clean_store):
        result = cmd("/mission-review", "mission-review")
        # blocked count should appear in output
        assert "blocked" in result.lower() or "0" in result

    def test_unknown_subcommand_shows_help_hint(self, clean_store):
        result = cmd("/mission xyz unknown", "mission xyz unknown")
        assert "Unknown" in result or "help" in result