"""Tests for Household / Multi-Person Context Layer (v29)

Tests household_context.py data models, manager, conflict detection, and integration hooks.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.household_context import (
    RecommendationScope,
    PersonRole,
    VisibilityPermission,
    ConflictStatus,
    HouseholdMember,
    SharedContext,
    HouseholdContext,
    HouseholdContextManager,
    HouseholdConflictDetector,
    integrate_with_profile,
    integrate_with_longitudinal_patterns,
    integrate_with_adaptive_guidance,
    integrate_with_narrative,
)


class TestHouseholdMember(unittest.TestCase):
    """Test household member data model."""

    def test_member_creation(self):
        """Test creating a household member."""
        member = HouseholdMember(
            person_id="person-001",
            name="Alice",
            role=PersonRole.ADULT.value,
            visibility_permission=VisibilityPermission.FAMILY.value,
        )
        
        self.assertEqual(member.person_id, "person-001")
        self.assertEqual(member.name, "Alice")
        self.assertEqual(member.role, PersonRole.ADULT.value)

    def test_member_can_share_routines(self):
        """Test routine sharing permission."""
        # Private permission - cannot share
        member = HouseholdMember(
            person_id="person-001",
            visibility_permission=VisibilityPermission.PRIVATE.value,
            share_routines=True,
        )
        self.assertFalse(member.can_share_routines())
        
        # Family permission with sharing enabled - can share
        member = HouseholdMember(
            person_id="person-001",
            visibility_permission=VisibilityPermission.FAMILY.value,
            share_routines=True,
        )
        self.assertTrue(member.can_share_routines())

    def test_member_get_shared_scope(self):
        """Test getting available shared scopes."""
        # Private member - only individual scope
        member = HouseholdMember(
            person_id="person-001",
            visibility_permission=VisibilityPermission.PRIVATE.value,
        )
        scopes = member.get_shared_scope()
        self.assertEqual(scopes, ["individual"])
        
        # Family member with sharing enabled
        member = HouseholdMember(
            person_id="person-001",
            visibility_permission=VisibilityPermission.FAMILY.value,
            share_routines=True,
        )
        scopes = member.get_shared_scope()
        self.assertIn("shared_routines", scopes)

    def test_member_serialization(self):
        """Test household member to_dict/from_dict."""
        member = HouseholdMember(
            person_id="person-001",
            name="Alice",
            role=PersonRole.ADULT.value,
        )
        
        member_dict = member.to_dict()
        member2 = HouseholdMember.from_dict(member_dict)
        
        self.assertEqual(member.person_id, member2.person_id)
        self.assertEqual(member.name, member2.name)


class TestSharedContext(unittest.TestCase):
    """Test shared context data model."""

    def test_context_creation(self):
        """Test creating a shared context."""
        context = SharedContext(
            context_id="context-001",
            context_type="routine",
            scope=RecommendationScope.HOUSEHOLD.value,
            members_involved=["person-001", "person-002"],
        )
        
        self.assertEqual(context.context_id, "context-001")
        self.assertEqual(context.context_type, "routine")
        self.assertEqual(len(context.members_involved), 2)

    def test_context_get_member_count(self):
        """Test getting member count for context."""
        context = SharedContext(
            context_id="context-001",
            context_type="goal",
            members_involved=["person-001", "person-002", "person-003"],
        )
        
        self.assertEqual(context.get_member_count(), 3)

    def test_context_should_hold_back_for_conflict(self):
        """Test conflict-based hold back behavior."""
        # No conflict
        context = SharedContext(
            context_id="context-001",
            context_type="routine",
            conflict_status=ConflictStatus.NONE.value,
        )
        self.assertFalse(context.should_hold_back_for_conflict())
        
        # Medium conflict
        context = SharedContext(
            context_id="context-002",
            context_type="routine",
            conflict_status=ConflictStatus.MEDIUM.value,
        )
        self.assertTrue(context.should_hold_back_for_conflict())
        
        # High conflict
        context = SharedContext(
            context_id="context-003",
            context_type="routine",
            conflict_status=ConflictStatus.HIGH.value,
        )
        self.assertTrue(context.should_hold_back_for_conflict())

    def test_context_serialization(self):
        """Test shared context to_dict/from_dict."""
        context = SharedContext(
            context_id="context-001",
            context_type="goal",
            title="Weekly Goals",
            members_involved=["person-001", "person-002"],
        )
        
        context_dict = context.to_dict()
        context2 = SharedContext.from_dict(context_dict)
        
        self.assertEqual(context.context_id, context2.context_id)
        self.assertEqual(context.title, context2.title)


class TestHouseholdContext(unittest.TestCase):
    """Test household context data model."""

    def test_household_creation(self):
        """Test creating a household."""
        household = HouseholdContext(
            household_id="household-001",
            name="Smith Family",
        )
        
        self.assertEqual(household.household_id, "household-001")
        self.assertEqual(household.name, "Smith Family")
        self.assertEqual(len(household.members), 0)

    def test_household_add_member(self):
        """Test adding a member to household."""
        household = HouseholdContext(household_id="household-001")
        
        member = HouseholdMember(
            person_id="person-001",
            name="Alice",
        )
        household.add_member(member)
        
        self.assertEqual(len(household.members), 1)
        self.assertIn("person-001", household.members)

    def test_household_remove_member(self):
        """Test removing a member from household."""
        household = HouseholdContext(household_id="household-001")
        
        member = HouseholdMember(person_id="person-001", name="Alice")
        household.add_member(member)
        
        self.assertTrue(household.remove_member("person-001"))
        self.assertEqual(len(household.members), 0)
        
        # Remove non-existent member
        self.assertFalse(household.remove_member("person-002"))

    def test_household_create_shared_context(self):
        """Test creating a shared context in household."""
        household = HouseholdContext(household_id="household-001")
        
        context = household.create_shared_context(
            context_type="routine",
            members_involved=["person-001", "person-002"],
        )
        
        self.assertIsNotNone(context)
        self.assertIn(context.context_id, household.shared_contexts)

    def test_household_update_conflict_status(self):
        """Test updating conflict status."""
        household = HouseholdContext(household_id="household-001")
        
        context = household.create_shared_context(
            context_type="routine",
            members_involved=["person-001", "person-002"],
        )
        
        result = household.update_conflict_status(
            context.context_id,
            ConflictStatus.MEDIUM.value,
            "Members have scheduling conflicts",
        )
        
        self.assertTrue(result)
        self.assertEqual(context.conflict_status, ConflictStatus.MEDIUM.value)

    def test_household_get_shared_contexts_for_member(self):
        """Test getting shared contexts for a member."""
        household = HouseholdContext(
            household_id="household-001",
            enable_shared_contexts=True,
        )
        
        member = HouseholdMember(
            person_id="person-001",
            visibility_permission=VisibilityPermission.FAMILY.value,
            share_routines=True,
        )
        household.add_member(member)
        
        context = household.create_shared_context(
            context_type="routine",
            members_involved=["person-001"],
        )
        
        contexts = household.get_shared_contexts_for_member("person-001")
        self.assertGreater(len(contexts), 0)

    def test_household_serialization(self):
        """Test household to_dict/from_dict."""
        household = HouseholdContext(
            household_id="household-001",
            name="Smith Family",
        )
        
        member = HouseholdMember(person_id="person-001", name="Alice")
        household.add_member(member)
        
        household_dict = household.to_dict()
        household2 = HouseholdContext.from_dict(household_dict)
        
        self.assertEqual(household.household_id, household2.household_id)
        self.assertEqual(len(household.members), len(household2.members))


class TestHouseholdContextManager(unittest.TestCase):
    """Test household context manager."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = HouseholdContextManager(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_household(self):
        """Test creating a new household."""
        household = self.manager.create_household("household-001", "Test Family")
        
        self.assertIsNotNone(household)
        self.assertEqual(household.household_id, "household-001")

    def test_add_member_to_household(self):
        """Test adding a member to a household."""
        self.manager.create_household("household-001")
        
        member = self.manager.add_member_to_household("household-001", "person-001", "Alice")
        
        self.assertIsNotNone(member)
        self.assertEqual(member.person_id, "person-001")

    def test_get_member(self):
        """Test getting a member from a household."""
        self.manager.create_household("household-001")
        self.manager.add_member_to_household("household-001", "person-001", "Alice")
        
        member = self.manager.get_member("household-001", "person-001")
        
        self.assertIsNotNone(member)
        self.assertEqual(member.name, "Alice")

    def test_create_shared_context(self):
        """Test creating a shared context."""
        self.manager.create_household("household-001")
        
        context = self.manager.create_shared_context(
            "household-001",
            "routine",
            ["person-001", "person-002"],
        )
        
        self.assertIsNotNone(context)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        self.manager.create_household("household-001", "Test Family")
        self.manager.add_member_to_household("household-001", "person-001", "Alice")
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["household_count"], 1)
        self.assertIn("households", manager_dict)


class TestHouseholdConflictDetector(unittest.TestCase):
    """Test household conflict detector."""

    def setUp(self):
        """Set up test manager."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = HouseholdContextManager(storage_path=self.temp_dir)
        self.detector = HouseholdConflictDetector(self.manager)
        self.manager.create_household("household-001", "Test Family")
        self.manager.add_member_to_household("household-001", "person-001", "Alice")
        self.manager.add_member_to_household("household-001", "person-002", "Bob")
        self.manager.add_member_to_household("household-001", "person-003", "Charlie")
        self.manager.add_member_to_household("household-001", "person-004", "Diana")

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_conflict_none(self):
        """Test conflict detection with no conflict."""
        context = self.manager.create_shared_context(
            "household-001",
            "routine",
            ["person-001"],
        )
        
        result = self.detector.detect_conflict("household-001", context.context_id)
        
        self.assertIsNone(result)

    def test_detect_conflict_low(self):
        """Test conflict detection with low member count."""
        context = self.manager.create_shared_context(
            "household-001",
            "routine",
            ["person-001", "person-002"],
        )
        
        result = self.detector.detect_conflict("household-001", context.context_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["detected_conflict_status"], ConflictStatus.LOW.value)

    def test_detect_conflict_medium(self):
        """Test conflict detection with medium member count."""
        context = self.manager.create_shared_context(
            "household-001",
            "routine",
            ["person-001", "person-002", "person-003", "person-004"],
        )
        
        result = self.detector.detect_conflict("household-001", context.context_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["detected_conflict_status"], ConflictStatus.MEDIUM.value)

    def test_auto_detect_household_conflicts(self):
        """Test auto-detecting conflicts across household."""
        # Create multiple contexts
        self.manager.create_shared_context(
            "household-001",
            "routine",
            ["person-001", "person-002", "person-003", "person-004"],
        )
        self.manager.create_shared_context(
            "household-001",
            "goal",
            ["person-001", "person-002"],
        )
        
        results = self.detector.auto_detect_household_conflicts("household-001")
        
        self.assertGreater(len(results), 0)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for profile, longitudinal patterns, adaptive guidance, and narrative."""

    def test_integrate_with_profile_adds_household_fields(self):
        """Test that integration adds household fields to profile."""
        profile_dict = {
            "profile_id": "profile-001",
        }
        
        result = integrate_with_profile(profile_dict)
        
        self.assertIn("household_id", result)
        self.assertIn("household_role", result)
        self.assertFalse(result["share_with_household"])

    def test_integrate_with_longitudinal_patterns_adds_household_context(self):
        """Test that integration adds household context to patterns."""
        patterns_dict = {
            "pattern_id": "pattern-001",
        }
        
        result = integrate_with_longitudinal_patterns(patterns_dict)
        
        self.assertIn("household_context", result)
        self.assertIn("is_shared_context", result)
        self.assertFalse(result["is_shared_context"])

    def test_integrate_with_adaptive_guidance_adds_household_scope(self):
        """Test that integration adds household scope to guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("household_scope", result)
        self.assertIn("conflict_sensitive", result)
        self.assertFalse(result["conflict_sensitive"])

    def test_integrate_with_narrative_adds_household_basis(self):
        """Test that integration adds household basis to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("household_basis", result)
        self.assertIn("shared_with_household", result)

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing household context."""
        profile_dict = {
            "profile_id": "profile-001",
            "household_id": "household-001",
            "household_role": "parent",
            "share_with_household": True,
        }
        
        result = integrate_with_profile(profile_dict)
        
        self.assertEqual(result["household_id"], "household-001")
        self.assertEqual(result["household_role"], "parent")
        self.assertTrue(result["share_with_household"])


if __name__ == "__main__":
    unittest.main()
