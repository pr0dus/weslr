"""Tests for Unified Continuity / Context Consolidation Layer (v30)

Tests unified_continuity.py data models, manager, and integration hooks.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from weslr.unified_continuity import (
    ContinuityScope,
    ContinuityStatus,
    ConsolidatedContinuity,
    ContinuitySnapshot,
    UnifiedContinuityManager,
    integrate_with_narrative,
    integrate_with_adaptive_guidance,
    integrate_with_governance,
    integrate_with_operator_review,
)


class TestContinuityModels(unittest.TestCase):
    """Test unified continuity data models."""

    def test_consolidated_continuity_creation(self):
        """Test creating a consolidated continuity state."""
        continuity = ConsolidatedContinuity(
            continuity_id="continuity-001",
            scope=ContinuityScope.SESSION.value,
        )
        
        self.assertEqual(continuity.continuity_id, "continuity-001")
        self.assertEqual(continuity.scope, ContinuityScope.SESSION.value)
        self.assertEqual(continuity.confidence, 0.5)

    def test_consolidated_continuity_add_source(self):
        """Test adding source to continuity."""
        continuity = ConsolidatedContinuity(continuity_id="continuity-001")
        
        continuity.add_source("profile", {"key": "value"})
        
        self.assertIn("profile", continuity.consolidated_from)
        self.assertEqual(len(continuity.consolidation_log), 1)

    def test_consolidated_continuity_update_confidence(self):
        """Test updating confidence level."""
        continuity = ConsolidatedContinuity(continuity_id="continuity-001")
        
        continuity.update_confidence(0.8)
        self.assertEqual(continuity.confidence, 0.8)
        
        # Clamp to max
        continuity.update_confidence(1.5)
        self.assertEqual(continuity.confidence, 1.0)
        
        # Clamp to min
        continuity.update_confidence(-0.5)
        self.assertEqual(continuity.confidence, 0.0)

    def test_consolidated_continuity_pause_resume(self):
        """Test pause and resume states."""
        continuity = ConsolidatedContinuity(continuity_id="continuity-001")
        
        self.assertEqual(continuity.status, ContinuityStatus.ACTIVE.value)
        
        continuity.pause()
        self.assertEqual(continuity.status, ContinuityStatus.PAUSED.value)
        
        continuity.resume()
        self.assertEqual(continuity.status, ContinuityStatus.RESUMED.value)

    def test_consolidated_continuity_is_expired(self):
        """Test expiration check."""
        # New continuity should not be expired
        continuity = ConsolidatedContinuity(continuity_id="continuity-001")
        self.assertFalse(continuity.is_expired(24.0))
        
        # Simulate old continuity
        from datetime import datetime, timezone, timedelta
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat().replace("+00:00", "Z")
        continuity.created_at = old_time
        self.assertTrue(continuity.is_expired(24.0))

    def test_consolidated_continuity_get_summary(self):
        """Test getting summary."""
        continuity = ConsolidatedContinuity(continuity_id="continuity-001")
        continuity.add_source("profile", {})
        continuity.add_source("patterns", {})
        
        summary = continuity.get_summary()
        
        self.assertEqual(summary["continuity_id"], "continuity-001")
        self.assertEqual(summary["sources"], 2)
        self.assertEqual(len(summary["sources_list"]), 2)

    def test_consolidated_continuity_serialization(self):
        """Test continuity to_dict/from_dict."""
        continuity = ConsolidatedContinuity(continuity_id="continuity-001")
        continuity.add_source("profile", {"key": "value"})
        
        continuity_dict = continuity.to_dict()
        continuity2 = ConsolidatedContinuity.from_dict(continuity_dict)
        
        self.assertEqual(continuity.continuity_id, continuity2.continuity_id)
        self.assertEqual(continuity.confidence, continuity2.confidence)

    def test_continuity_snapshot_creation(self):
        """Test creating a continuity snapshot."""
        snapshot = ContinuitySnapshot(
            continuity_id="continuity-001",
            snapshot_id="snapshot-001",
        )
        
        self.assertEqual(snapshot.continuity_id, "continuity-001")
        self.assertEqual(snapshot.snapshot_id, "snapshot-001")

    def test_continuity_snapshot_set_expiration(self):
        """Test setting expiration."""
        snapshot = ContinuitySnapshot(
            continuity_id="continuity-001",
            snapshot_id="snapshot-001",
        )
        
        snapshot.set_expiration(hours=24.0)
        
        self.assertIsNotNone(snapshot.expires_at)
        self.assertNotEqual(snapshot.expires_at, snapshot.created_at)

    def test_continuity_snapshot_serialization(self):
        """Test snapshot to_dict/from_dict."""
        snapshot = ContinuitySnapshot(
            continuity_id="continuity-001",
            snapshot_id="snapshot-001",
            current_context="test",
        )
        
        snapshot_dict = snapshot.to_dict()
        snapshot2 = ContinuitySnapshot.from_dict(snapshot_dict)
        
        self.assertEqual(snapshot.continuity_id, snapshot2.continuity_id)
        self.assertEqual(snapshot.current_context, snapshot2.current_context)


class TestUnifiedContinuityManager(unittest.TestCase):
    """Test unified continuity manager."""

    def setUp(self):
        """Set up test storage in temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = UnifiedContinuityManager(storage_path=self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_continuity(self):
        """Test creating a new continuity state."""
        continuity = self.manager.create_continuity("continuity-001")
        
        self.assertIsNotNone(continuity)
        self.assertEqual(continuity.continuity_id, "continuity-001")

    def test_consolidate_profile(self):
        """Test consolidating profile state."""
        self.manager.create_continuity("continuity-001")
        
        profile_state = {"profile_id": "profile-001"}
        self.manager.consolidate_profile("continuity-001", profile_state)
        
        continuity = self.manager.get_continuity()
        self.assertEqual(continuity.profile_state, profile_state)
        self.assertIn("profile", continuity.consolidated_from)

    def test_consolidate_patterns(self):
        """Test consolidating pattern state."""
        self.manager.create_continuity("continuity-001")
        
        pattern_state = {"pattern_count": 5}
        self.manager.consolidate_patterns("continuity-001", pattern_state)
        
        continuity = self.manager.get_continuity()
        self.assertEqual(continuity.pattern_state, pattern_state)

    def test_consolidate_household(self):
        """Test consolidating household state."""
        self.manager.create_continuity("continuity-001")
        
        household_state = {"household_id": "household-001"}
        self.manager.consolidate_household("continuity-001", household_state)
        
        continuity = self.manager.get_continuity()
        self.assertEqual(continuity.household_state, household_state)

    def test_consolidate_domain(self):
        """Test consolidating domain state."""
        self.manager.create_continuity("continuity-001")
        
        domain_state = {"domain_id": "domain-001"}
        self.manager.consolidate_domain("continuity-001", domain_state)
        
        continuity = self.manager.get_continuity()
        self.assertEqual(continuity.domain_state, domain_state)

    def test_consolidate_governance(self):
        """Test consolidating governance state."""
        self.manager.create_continuity("continuity-001")
        
        governance_state = {"proposal_id": "proposal-001"}
        self.manager.consolidate_governance("continuity-001", governance_state)
        
        continuity = self.manager.get_continuity()
        self.assertEqual(continuity.governance_state, governance_state)

    def test_consolidate_evidence(self):
        """Test consolidating evidence state."""
        self.manager.create_continuity("continuity-001")
        
        evidence_state = {"evidence_id": "evidence-001"}
        self.manager.consolidate_evidence("continuity-001", evidence_state)
        
        continuity = self.manager.get_continuity()
        self.assertEqual(continuity.evidence_state, evidence_state)

    def test_pause_and_resume_continuity(self):
        """Test pausing and resuming continuity."""
        self.manager.create_continuity("continuity-001")
        
        self.assertTrue(self.manager.pause_continuity("continuity-001"))
        continuity = self.manager.get_continuity()
        self.assertEqual(continuity.status, ContinuityStatus.PAUSED.value)
        
        self.assertTrue(self.manager.resume_continuity("continuity-001"))
        self.assertEqual(continuity.status, ContinuityStatus.RESUMED.value)

    def test_take_and_restore_snapshot(self):
        """Test taking and restoring a snapshot."""
        self.manager.create_continuity("continuity-001")
        
        snapshot = self.manager.take_snapshot("continuity-001", "snapshot-001")
        
        self.assertIsNotNone(snapshot)
        self.assertIn("snapshot-001", self.manager.snapshots)
        
        # Modify continuity after snapshot
        self.manager.consolidate_profile("continuity-001", {"profile_id": "profile-001"})
        
        # Restore snapshot
        self.assertTrue(self.manager.restore_snapshot("snapshot-001"))
        
        continuity = self.manager.get_continuity()
        self.assertIsNone(continuity.profile_state)  # Back to snapshot state

    def test_expire_snapshots(self):
        """Test expiring old snapshots."""
        self.manager.create_continuity("continuity-001")
        
        # Create old snapshot (by modifying created_at)
        snapshot = self.manager.take_snapshot("continuity-001", "snapshot-001")
        snapshot.created_at = "2020-01-01T00:00:00Z"
        snapshot.expires_at = "2020-01-01T01:00:00Z"
        
        # Expire
        expired = self.manager.expire_snapshots()
        
        self.assertIn("snapshot-001", expired)
        self.assertNotIn("snapshot-001", self.manager.snapshots)

    def test_manager_serialization(self):
        """Test manager to_dict."""
        self.manager.create_continuity("continuity-001")
        self.manager.consolidate_profile("continuity-001", {"profile_id": "profile-001"})
        
        manager_dict = self.manager.to_dict()
        
        self.assertEqual(manager_dict["continuity_count"], 1)
        self.assertIn("current_continuity", manager_dict)
        self.assertEqual(manager_dict["snapshot_count"], 0)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for narrative, adaptive guidance, governance, and operator review."""

    def test_integrate_with_narrative_adds_continuity_context(self):
        """Test that integration adds continuity context to narrative."""
        narrative_dict = {
            "narrative_id": "narr-001",
        }
        
        result = integrate_with_narrative(narrative_dict)
        
        self.assertIn("continuity_context", result)
        self.assertIn("continuity_source", result)

    def test_integrate_with_adaptive_guidance_adds_continuity_insights(self):
        """Test that integration adds continuity insights to guidance."""
        guidance_dict = {
            "guidance_id": "guidance-001",
        }
        
        result = integrate_with_adaptive_guidance(guidance_dict)
        
        self.assertIn("continuity_context", result)
        self.assertIn("confidence_from_continuity", result)
        self.assertEqual(result["confidence_from_continuity"], 0.0)

    def test_integrate_with_governance_adds_continuity_snapshot(self):
        """Test that integration adds continuity snapshot to governance."""
        governance_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_governance(governance_dict)
        
        self.assertIn("continuity_snapshot_id", result)
        self.assertEqual(result["continuity_snapshot_id"], None)
        self.assertEqual(result["continuity_scope"], ContinuityScope.SESSION.value)

    def test_integrate_with_operator_review_adds_continuity_state(self):
        """Test that integration adds continuity state to operator review."""
        review_dict = {
            "proposal_id": "proposal-001",
        }
        
        result = integrate_with_operator_review(review_dict)
        
        self.assertIn("continuity_state", result)
        self.assertIn("continuity_confidence", result)
        self.assertFalse(result["can_resume_continuity"])

    def test_integrate_hooks_preserve_existing(self):
        """Test that integration hooks preserve existing continuity context."""
        governance_dict = {
            "proposal_id": "proposal-001",
            "continuity_snapshot_id": "snapshot-001",
            "continuity_scope": ContinuityScope.HOUSEHOLD.value,
        }
        
        result = integrate_with_governance(governance_dict)
        
        self.assertEqual(result["continuity_snapshot_id"], "snapshot-001")
        self.assertEqual(result["continuity_scope"], ContinuityScope.HOUSEHOLD.value)


if __name__ == "__main__":
    unittest.main()
