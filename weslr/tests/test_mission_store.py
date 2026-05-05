"""
WESLR Mission Store Tests

Tests for MissionStore: save, list, load_active, tenant isolation, update_status.
"""

import json
import os
import tempfile
import pytest

from weslr.mission_store import MissionStore
from weslr.schemas.mission import Mission, make_mission, generate_mission_id


@pytest.fixture
def temp_store():
    """Create a temporary store file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        store_path = f.name

    store = MissionStore(store_path=store_path)
    yield store

    # Cleanup
    if os.path.exists(store_path):
        os.unlink(store_path)


class TestMissionStore:
    """Tests for MissionStore."""

    def test_save_and_load(self, temp_store):
        """Test saving and loading a mission."""
        mission = make_mission(
            tenant_id="tenant-1",
            owner_user_id="user-1",
            title="Test Mission",
            research_goal="Test goal",
        )
        mission.status = "active"

        temp_store.save(mission)

        loaded = temp_store.list("tenant-1")
        assert len(loaded) == 1
        assert loaded[0].title == "Test Mission"
        assert loaded[0].tenant_id == "tenant-1"

    def test_list_filters_by_tenant(self, temp_store):
        """Test that list filters by tenant."""
        m1 = make_mission("tenant-1", "user-1", "Mission 1", "Goal 1")
        m1.status = "active"
        m2 = make_mission("tenant-2", "user-2", "Mission 2", "Goal 2")
        m2.status = "active"

        temp_store.save(m1)
        temp_store.save(m2)

        tenant1_missions = temp_store.list("tenant-1")
        assert len(tenant1_missions) == 1
        assert tenant1_missions[0].tenant_id == "tenant-1"

        tenant2_missions = temp_store.list("tenant-2")
        assert len(tenant2_missions) == 1
        assert tenant2_missions[0].tenant_id == "tenant-2"

    def test_list_filters_by_status(self, temp_store):
        """Test that list filters by status."""
        m1 = make_mission("tenant-1", "user-1", "Active Mission", "Goal")
        m1.status = "active"
        m2 = make_mission("tenant-1", "user-1", "Paused Mission", "Goal")
        m2.status = "paused"

        temp_store.save(m1)
        temp_store.save(m2)

        active = temp_store.list("tenant-1", status="active")
        assert len(active) == 1
        assert active[0].title == "Active Mission"

        paused = temp_store.list("tenant-1", status="paused")
        assert len(paused) == 1
        assert paused[0].title == "Paused Mission"

    def test_load_active(self, temp_store):
        """Test loading only active missions."""
        m1 = make_mission("tenant-1", "user-1", "Active", "Goal")
        m1.status = "active"
        m2 = make_mission("tenant-1", "user-1", "Paused", "Goal")
        m2.status = "paused"
        m3 = make_mission("tenant-1", "user-1", "Closed", "Goal")
        m3.status = "closed"

        temp_store.save(m1)
        temp_store.save(m2)
        temp_store.save(m3)

        active = temp_store.load_active("tenant-1")
        assert len(active) == 1
        assert active[0].title == "Active"

    def test_tenant_isolation(self, temp_store):
        """Test that one tenant cannot see another's missions."""
        m1 = make_mission("tenant-1", "user-1", "Private Mission 1", "Goal")
        m1.status = "active"
        m2 = make_mission("tenant-2", "user-2", "Private Mission 2", "Goal")
        m2.status = "active"

        temp_store.save(m1)
        temp_store.save(m2)

        # Tenant 1 sees only their mission
        t1 = temp_store.list("tenant-1")
        assert len(t1) == 1
        assert t1[0].mission_id == m1.mission_id

        # Tenant 2 sees only their mission
        t2 = temp_store.list("tenant-2")
        assert len(t2) == 1
        assert t2[0].mission_id == m2.mission_id

    def test_update_status(self, temp_store):
        """Test updating mission status."""
        mission = make_mission("tenant-1", "user-1", "Status Test", "Goal")
        mission.status = "active"
        temp_store.save(mission)

        # Update to paused
        result = temp_store.update_status(mission.mission_id, "tenant-1", "paused")
        assert result is True

        # Verify
        updated = temp_store.get(mission.mission_id, "tenant-1")
        assert updated is not None
        assert updated.status == "paused"

    def test_update_status_not_found(self, temp_store):
        """Test updating non-existent mission."""
        result = temp_store.update_status("non-existent-id", "tenant-1", "paused")
        assert result is False

    def test_update_status_invalid_status(self, temp_store):
        """Test updating with invalid status raises ValueError."""
        mission = make_mission("tenant-1", "user-1", "Invalid Status Test", "Goal")
        mission.status = "active"
        temp_store.save(mission)

        with pytest.raises(ValueError, match="status must be one of"):
            temp_store.update_status(mission.mission_id, "tenant-1", "invalid_status")

    def test_automatic_execution_false(self, temp_store):
        """Test that automatic_execution is always False on saved missions."""
        mission = make_mission("tenant-1", "user-1", "AutoExec Test", "Goal")
        mission.status = "active"

        # Verify it cannot be set to True
        with pytest.raises(ValueError, match="automatic_execution must be False"):
            Mission(
                mission_id=mission.mission_id,
                owner_user_id=mission.owner_user_id,
                tenant_id=mission.tenant_id,
                title=mission.title,
                research_goal=mission.research_goal,
                domain_tags=mission.domain_tags,
                allowed_sources=mission.allowed_sources,
                forbidden_outputs=mission.forbidden_outputs,
                safety_constraints=mission.safety_constraints,
                cadence_minutes=0,
                current_questions=[],
                hypotheses=[],
                evidence_links=[],
                candidate_suggestions=[],
                status="active",
                automatic_execution=True,  # Should fail
                operator_visible=True,
                public_user_visible=False,
                created_at=mission.created_at,
                last_reviewed_at=mission.last_reviewed_at,
                next_run_at="",
                mission_note="",
            )

    def test_get_mission(self, temp_store):
        """Test getting a specific mission by ID."""
        mission = make_mission("tenant-1", "user-1", "Get Test", "Goal")
        mission.status = "active"
        temp_store.save(mission)

        found = temp_store.get(mission.mission_id, "tenant-1")
        assert found is not None
        assert found.mission_id == mission.mission_id

    def test_get_mission_wrong_tenant(self, temp_store):
        """Test that wrong tenant cannot access mission."""
        mission = make_mission("tenant-1", "user-1", "Isolation Test", "Goal")
        mission.status = "active"
        temp_store.save(mission)

        # Wrong tenant
        found = temp_store.get(mission.mission_id, "tenant-999")
        assert found is None

    def test_count(self, temp_store):
        """Test mission count."""
        m1 = make_mission("tenant-1", "user-1", "Count 1", "Goal")
        m1.status = "active"
        m2 = make_mission("tenant-1", "user-1", "Count 2", "Goal")
        m2.status = "active"

        temp_store.save(m1)
        temp_store.save(m2)

        assert temp_store.count("tenant-1") == 2
        assert temp_store.count("tenant-1", status="active") == 2
        assert temp_store.count("tenant-1", status="paused") == 0

    def test_exists(self, temp_store):
        """Test mission existence check."""
        mission = make_mission("tenant-1", "user-1", "Exists Test", "Goal")
        mission.status = "active"
        temp_store.save(mission)

        assert temp_store.exists(mission.mission_id, "tenant-1") is True
        assert temp_store.exists("non-existent", "tenant-1") is False


class TestMissionSchema:
    """Tests for Mission schema validation."""

    def test_required_fields(self):
        """Test that missing required fields raise ValueError."""
        with pytest.raises(ValueError, match="Missing required fields"):
            Mission.from_dict({
                "mission_id": "test-id",
                # Missing all other required fields
            })

    def test_valid_mission(self):
        """Test creating a valid mission."""
        mission = make_mission("tenant-1", "user-1", "Schema Test", "Goal")
        assert mission.mission_id is not None
        assert mission.automatic_execution is False

    def test_to_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        mission = make_mission("tenant-1", "user-1", "JSON Test", "Goal")
        mission.status = "active"

        json_str = mission.to_json()
        loaded = Mission.from_json(json_str)

        assert loaded.mission_id == mission.mission_id
        assert loaded.title == mission.title
        assert loaded.automatic_execution is False

    def test_invalid_status(self):
        """Test that invalid status raises ValueError."""
        with pytest.raises(ValueError, match="status must be one of"):
            Mission(
                mission_id="test-id",
                owner_user_id="user-1",
                tenant_id="tenant-1",
                title="Test",
                research_goal="Goal",
                domain_tags=[],
                allowed_sources=[],
                forbidden_outputs=[],
                safety_constraints=[],
                cadence_minutes=0,
                current_questions=[],
                hypotheses=[],
                evidence_links=[],
                candidate_suggestions=[],
                status="invalid_status",
                automatic_execution=False,
                operator_visible=True,
                public_user_visible=False,
                created_at="2026-05-04T00:00:00Z",
                last_reviewed_at="2026-05-04T00:00:00Z",
                next_run_at="",
                mission_note="",
            )

class TestUpdateMission:
    """Tests for MissionStore.update_mission field updates."""

    def test_update_mission_add_questions(self, temp_store):
        """Test updating current_questions via update_mission."""
        mission = make_mission("tenant-1", "user-1", "Field Update Test", "Goal")
        mission.status = "active"
        temp_store.save(mission)

        result = temp_store.update_mission(mission.mission_id, "tenant-1", {"current_questions": ["What is the bandgap?"]})
        assert result is True
        updated = temp_store.get(mission.mission_id, "tenant-1")
        assert updated.current_questions == ["What is the bandgap?"]

    def test_update_mission_append_questions(self, temp_store):
        """Test that update replaces the list, not appends."""
        mission = make_mission("tenant-1", "user-1", "Append Test", "Goal")
        mission.status = "active"
        mission.current_questions = ["Q1?"]
        temp_store.save(mission)


        temp_store.update_mission(mission.mission_id, "tenant-1", {"current_questions": ["Q1?", "Q2?"]})
        updated = temp_store.get(mission.mission_id, "tenant-1")
        assert updated.current_questions == ["Q1?", "Q2?"]

    def test_update_mission_domain_tags(self, temp_store):
        """Test updating domain_tags."""
        mission = make_mission("tenant-1", "user-1", "Domain Test", "Goal")
        mission.status = "active"
        temp_store.save(mission)

        result = temp_store.update_mission(mission.mission_id, "tenant-1", {"domain_tags": ["materials", "physics"]})
        assert result is True
        updated = temp_store.get(mission.mission_id, "tenant-1")
        assert updated.domain_tags == ["materials", "physics"]

    def test_update_mission_not_found(self, temp_store):
        """Test update on non-existent mission returns False."""
        result = temp_store.update_mission("non-existent-id", "tenant-1", {"current_questions": ["Test?"]})
        assert result is False

    def test_update_mission_wrong_tenant(self, temp_store):
        """Test update is isolated to tenant."""
        mission = make_mission("tenant-1", "user-1", "Tenant Update Test", "Goal")
        temp_store.save(mission)


        result = temp_store.update_mission(mission.mission_id, "tenant-2", {"current_questions": ["Hack?"]})
        assert result is False
        # Verify original tenant is unaffected
        original = temp_store.get(mission.mission_id, "tenant-1")
        assert original.current_questions == []
