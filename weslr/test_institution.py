"""test_institution — L2/L3 linking validation tests.

Validates:
- role auto-linkage: store_role_timeline registers role under institution
- Layer 3 authorization bridge: is_authorized_for_role resolves via registry
"""

from __future__ import annotations

import pytest

from weslr import institution


@pytest.fixture(autouse=True)
def fresh_stores():
    """Clear all in-process stores before each test."""
    institution._INSTITUTIONS.clear()
    institution._ROLE_TIMELINES.clear()
    institution._INSTITUTION_ROLES.clear()
    yield


class TestRoleAutoLinkage:
    """Role timelines should auto-register with the institution on store."""

    def test_storing_role_auto_links_to_institution(self):
        """store_role_timeline adds the role_id to the institution registry."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead")
        institution.store_role_timeline(role)

        inst_after = institution.get_institution("inst-1")
        assert "role-eng" in inst_after["role_timeline_ids"]

    def test_list_institution_roles_returns_stored_role(self):
        """list_institution_roles reflects the auto-linked role."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-ops", "inst-1", "Ops Lead")
        institution.store_role_timeline(role)

        roles = institution.list_institution_roles("inst-1")
        assert len(roles) == 1
        assert roles[0]["role_id"] == "role-ops"


class TestAuthorizationBridge:
    """is_authorized_for_role resolves through Layer 3 governor registry."""

    def test_governor_is_authorized_for_assign(self):
        """A governor of the institution can perform assign on any role."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead")
        institution.store_role_timeline(role)

        assert institution.is_authorized_for_role(role, "gov-alice", "assign") is True

    def test_governor_is_authorized_for_vacate(self):
        """A governor can vacate any role."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead")
        institution.store_role_timeline(role)

        assert institution.is_authorized_for_role(role, "gov-alice", "vacate") is True

    def test_role_owner_is_authorized_for_assign(self):
        """A role owner who is not a governor can assign their own role."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead", role_owner_id="owner-bob")
        institution.store_role_timeline(role)

        assert institution.is_authorized_for_role(role, "owner-bob", "assign") is True

    def test_current_occupant_is_authorized_for_read(self):
        """The current occupant of a role can read it."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead")
        role = institution.assign_occupant(role, "human-carol")
        institution.store_role_timeline(role)

        assert institution.is_authorized_for_role(role, "human-carol", "read") is True

    def test_stranger_is_denied_read(self):
        """An unrelated timeline_id is denied read access."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead")
        institution.store_role_timeline(role)

        assert institution.is_authorized_for_role(role, "stranger-x", "read") is False

    def test_stranger_is_denied_write(self):
        """An unrelated timeline_id is denied write access."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead")
        institution.store_role_timeline(role)

        assert institution.is_authorized_for_role(role, "stranger-x", "write") is False

    def test_governor_denied_after_unbind(self):
        """A governor who has been unbound loses admin access."""
        inst = institution.new_institution("inst-1", "Test Corp", founding_governor_id="gov-alice")
        institution.store_institution(inst)
        inst = institution.bind_governor(inst, "gov-bob", bound_by="gov-alice")
        institution.store_institution(inst)

        role = institution.new_role_timeline("role-eng", "inst-1", "Engineering Lead")
        institution.store_role_timeline(role)

        assert institution.is_authorized_for_role(role, "gov-bob", "assign") is True

        inst = institution.unbind_governor(inst, "gov-bob", reason="resigned")
        # unbind auto-stores

        assert institution.is_authorized_for_role(role, "gov-bob", "assign") is False