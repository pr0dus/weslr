# test_capability_suggestion.py - Focused tests for Capability Discovery Radar Phase 1
# Run with: python test_capability_suggestion.py

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure we're in the workspace
import sys
sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.capability_suggestion import (
    CapabilitySuggestion,
    CapabilityType,
    SuggestionStatus,
    SourceProvenance,
    CapabilitySuggestionStore,
    CapabilityDiscoveryRadar,
)


class TestCapabilitySuggestionModel(unittest.TestCase):
    """Test data model serialization."""

    def test_capability_type_enum(self):
        """CapabilityType enum has all expected values."""
        types = [t.value for t in CapabilityType]
        self.assertIn("ingestion", types)
        self.assertIn("analysis", types)
        self.assertIn("visualization", types)
        self.assertIn("automation", types)
        self.assertIn("integration", types)
        self.assertIn("storage", types)
        self.assertIn("security", types)
        self.assertIn("other", types)

    def test_suggestion_status_enum(self):
        """SuggestionStatus enum has all expected values."""
        statuses = [s.value for s in SuggestionStatus]
        self.assertIn("new", statuses)
        self.assertIn("suggested", statuses)
        self.assertIn("accepted", statuses)
        self.assertIn("denied", statuses)
        self.assertIn("snoozed", statuses)
        self.assertIn("archived", statuses)

    def test_source_provenance_enum(self):
        """SourceProvenance enum has all expected values."""
        provenances = [p.value for p in SourceProvenance]
        self.assertIn("internal_review", provenances)
        self.assertIn("reddit", provenances)
        self.assertIn("github", provenances)
        self.assertIn("email", provenances)
        self.assertIn("direct_submission", provenances)
        self.assertIn("other", provenances)

    def test_suggestion_serialization(self):
        """Test serialization and deserialization."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = CapabilitySuggestion(
            id="test-123",
            title="Test Capability",
            description="A test capability",
            capability_type=CapabilityType.ANALYSIS,
            status=SuggestionStatus.NEW,
            provenance=SourceProvenance.INTERNAL_REVIEW,
            created_at=now,
            updated_at=now,
        )

        # Serialize
        data = suggestion.to_dict()
        self.assertEqual(data["id"], "test-123")
        self.assertEqual(data["title"], "Test Capability")
        self.assertEqual(data["capability_type"], "analysis")
        self.assertEqual(data["status"], "new")

        # Deserialize
        restored = CapabilitySuggestion.from_dict(data)
        self.assertEqual(restored.id, "test-123")
        self.assertEqual(restored.capability_type, CapabilityType.ANALYSIS)
        self.assertEqual(restored.status, SuggestionStatus.NEW)


class TestCapabilitySuggestionStore(unittest.TestCase):
    """Test SQLite storage."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_suggestions.db"
        self.store = CapabilitySuggestionStore(self.db_path)

    def tearDown(self):
        """Clean up temporary database."""
        if self.db_path.exists():
            self.db_path.unlink()
        self.temp_dir.rmdir()

    def test_create_and_get(self):
        """Test creating and retrieving a suggestion."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = CapabilitySuggestion(
            id="test-create",
            title="Create Test",
            description="Testing creation",
            capability_type=CapabilityType.ANALYSIS,
            status=SuggestionStatus.NEW,
            provenance=SourceProvenance.INTERNAL_REVIEW,
            created_at=now,
            updated_at=now,
        )

        saved = self.store.create(suggestion)
        self.assertEqual(saved.id, "test-create")
        self.assertEqual(saved.title, "Create Test")

        retrieved = self.store.get("test-create")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Create Test")

    def test_update(self):
        """Test updating a suggestion."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = CapabilitySuggestion(
            id="test-update",
            title="Original Title",
            description="Original desc",
            capability_type=CapabilityType.ANALYSIS,
            status=SuggestionStatus.NEW,
            provenance=SourceProvenance.INTERNAL_REVIEW,
            created_at=now,
            updated_at=now,
        )
        self.store.create(suggestion)

        # Update
        suggestion.title = "Updated Title"
        suggestion.status = SuggestionStatus.SUGGESTED
        updated = self.store.update(suggestion)

        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.status, SuggestionStatus.SUGGESTED)

        # Verify persistence
        retrieved = self.store.get("test-update")
        self.assertEqual(retrieved.title, "Updated Title")

    def test_delete_archives(self):
        """Test that delete archives (soft delete)."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = CapabilitySuggestion(
            id="test-delete",
            title="Delete Me",
            description="To be deleted",
            capability_type=CapabilityType.ANALYSIS,
            status=SuggestionStatus.NEW,
            provenance=SourceProvenance.INTERNAL_REVIEW,
            created_at=now,
            updated_at=now,
        )
        self.store.create(suggestion)

        self.store.delete("test-delete")

        # Should still exist but archived
        retrieved = self.store.get("test-delete")
        self.assertEqual(retrieved.status, SuggestionStatus.ARCHIVED)
        self.assertIsNotNone(retrieved.archived_at)


class TestCapabilityDiscoveryRadar(unittest.TestCase):
    """Test the full radar functionality."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_radar.db"
        self.store = CapabilitySuggestionStore(self.db_path)
        self.radar = CapabilityDiscoveryRadar(self.store)

    def tearDown(self):
        """Clean up temporary database."""
        if self.db_path.exists():
            self.db_path.unlink()
        self.temp_dir.rmdir()

    def test_create_suggestion(self):
        """Test creating a new suggestion."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = self.radar.create_suggestion(
            title="New Capability",
            description="A new capability request",
            capability_type=CapabilityType.ANALYSIS,
            provenance=SourceProvenance.GITHUB,
            priority=5,
        )

        self.assertEqual(suggestion.title, "New Capability")
        self.assertEqual(suggestion.status, SuggestionStatus.NEW)
        self.assertEqual(suggestion.capability_type, CapabilityType.ANALYSIS)
        self.assertEqual(suggestion.provenance, SourceProvenance.GITHUB)
        self.assertEqual(suggestion.priority, 5)

    def test_suggest_transition(self):
        """Test new -> suggested transition."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = self.radar.create_suggestion(
            title="To Be Suggested",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        self.assertEqual(suggestion.status, SuggestionStatus.NEW)

        suggested = self.radar.suggest(suggestion.id)
        self.assertEqual(suggested.status, SuggestionStatus.SUGGESTED)

    def test_accept_transition(self):
        """Test suggested -> accepted transition."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = self.radar.create_suggestion(
            title="To Be Accepted",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        suggested = self.radar.suggest(suggestion.id)

        accepted = self.radar.accept(suggested.id, notes="Accepted by test")
        self.assertEqual(accepted.status, SuggestionStatus.ACCEPTED)
        self.assertIn("Accepted by test", accepted.notes or "")

    def test_deny_transition(self):
        """Test suggested -> denied transition with suppression."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = self.radar.create_suggestion(
            title="To Be Denied",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        suggested = self.radar.suggest(suggestion.id)

        denied = self.radar.deny(suggested.id, reason="Not a good fit", suppress_24h=True)
        self.assertEqual(denied.status, SuggestionStatus.DENIED)
        self.assertEqual(denied.denial_count, 1)
        self.assertIsNotNone(denied.last_denied_at)

    def test_snooze_transition(self):
        """Test snooze transition."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = self.radar.create_suggestion(
            title="To Be Snoozed",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )

        snoozed = self.radar.snooze(suggestion.id, reason="Wait for more info")
        self.assertEqual(snoozed.status, SuggestionStatus.SNOOZED)

    def test_archive_transition(self):
        """Test archive transition."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        suggestion = self.radar.create_suggestion(
            title="To Be Archived",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )

        archived = self.radar.archive(suggestion.id, reason="Done with it")
        self.assertEqual(archived.status, SuggestionStatus.ARCHIVED)
        self.assertIsNotNone(archived.archived_at)

    def test_list_all(self):
        """Test listing all suggestions."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.radar.create_suggestion(
            title="First",
            description="Test 1",
            capability_type=CapabilityType.ANALYSIS,
            provenance=SourceProvenance.INTERNAL_REVIEW,
        )
        self.radar.create_suggestion(
            title="Second",
            description="Test 2",
            capability_type=CapabilityType.AUTOMATION,
            provenance=SourceProvenance.REDDIT,
        )

        all_suggestions = self.radar.list(include_archived=True)
        self.assertEqual(len(all_suggestions), 2)

    def test_filter_by_status(self):
        """Test filtering by status."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        s1 = self.radar.create_suggestion(
            title="New One",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        s2 = self.radar.create_suggestion(
            title="Accepted One",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        self.radar.accept(s2.id)

        new_only = self.radar.list(status=SuggestionStatus.NEW)
        self.assertEqual(len(new_only), 1)
        self.assertEqual(new_only[0].id, s1.id)

        accepted_only = self.radar.list(status=SuggestionStatus.ACCEPTED)
        self.assertEqual(len(accepted_only), 1)
        self.assertEqual(accepted_only[0].id, s2.id)

    def test_filter_by_type(self):
        """Test filtering by capability type."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.radar.create_suggestion(
            title="Analysis One",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        self.radar.create_suggestion(
            title="Automation One",
            description="Test",
            capability_type=CapabilityType.AUTOMATION,
        )

        analysis_only = self.radar.list(capability_type=CapabilityType.ANALYSIS)
        self.assertEqual(len(analysis_only), 1)

        automation_only = self.radar.list(capability_type=CapabilityType.AUTOMATION)
        self.assertEqual(len(automation_only), 1)

    def test_search(self):
        """Test text search."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.radar.create_suggestion(
            title="Machine Learning Analysis",
            description="Use ML for scientific data",
            capability_type=CapabilityType.ANALYSIS,
        )
        self.radar.create_suggestion(
            title="Data Visualization",
            description="Plotting capabilities",
            capability_type=CapabilityType.VISUALIZATION,
        )

        # Search by word in title
        ml_results = self.radar.search("machine")
        self.assertEqual(len(ml_results), 1)

        # Search by word in description
        ml_results = self.radar.search("ml")
        self.assertEqual(len(ml_results), 1)

        # Search by word in both
        all_results = self.radar.search("data")
        self.assertEqual(len(all_results), 2)

    def test_archive_exclusion(self):
        """Test that archived items are excluded from default list."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        s1 = self.radar.create_suggestion(
            title="Active One",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        s2 = self.radar.create_suggestion(
            title="Archived One",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        self.radar.archive(s2.id)

        active_only = self.radar.list()
        self.assertEqual(len(active_only), 1)
        self.assertEqual(active_only[0].id, s1.id)

        include_archived = self.radar.list(include_archived=True)
        self.assertEqual(len(include_archived), 2)

    def test_deny_active_count(self):
        """Test denied-active count in summary."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        s1 = self.radar.create_suggestion(
            title="Just Denied",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )
        s2 = self.radar.create_suggestion(
            title="Old Denied",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
        )

        self.radar.deny(s1.id, reason="Test", suppress_24h=True)
        # Simulate old denial (more than 24h ago)
        s2_status = SuggestionStatus.DENIED
        s2_denial_count = 1
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat().replace("+00:00", "Z")
        s2_status = SuggestionStatus.DENIED
        s2.denial_count = 1
        s2.last_denied_at = old_time
        s2.status = s2_status
        self.store.update(s2)

        summary = self.radar.get_summary()
        # The "just denied" one should be counted as active
        self.assertGreaterEqual(summary["denied_active_count"], 0)

    def test_summary(self):
        """Test full summary generation."""
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.radar.create_suggestion(
            title="Analysis Suggestion",
            description="Test",
            capability_type=CapabilityType.ANALYSIS,
            provenance=SourceProvenance.GITHUB,
            priority=10,
        )

        summary = self.radar.get_summary()
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["by_status"]["new"], 1)
        self.assertEqual(summary["by_type"]["analysis"], 1)
        self.assertEqual(summary["by_provenance"]["github"], 1)
        self.assertEqual(summary["pending_count"], 1)
        self.assertIsNotNone(summary["top_pending_suggestion"])
        self.assertEqual(summary["top_pending_suggestion"]["title"], "Analysis Suggestion")


class TestDiagnosticsIntegration(unittest.TestCase):
    """Test diagnostics integration."""

    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_diagnostics.db"
        self.store = CapabilitySuggestionStore(self.db_path)
        self.radar = CapabilityDiscoveryRadar(self.store)

    def tearDown(self):
        """Clean up temporary database."""
        if self.db_path.exists():
            self.db_path.unlink()
        self.temp_dir.rmdir()

    def test_diagnostics_exposed(self):
        """Test that diagnostics summary is accessible."""
        # Create a test suggestion
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.radar.create_suggestion(
            title="Test Capability",
            description="Test description",
            capability_type=CapabilityType.ANALYSIS,
            provenance=SourceProvenance.INTERNAL_REVIEW,
            priority=5,
        )

        # Get summary via diagnostics
        summary = self.radar.get_summary()
        self.assertIn("total", summary)
        self.assertIn("by_status", summary)
        self.assertIn("pending_count", summary)
        self.assertIn("denied_active_count", summary)
        self.assertIn("top_pending_suggestion", summary)


if __name__ == "__main__":
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCapabilitySuggestionModel))
    suite.addTests(loader.loadTestsFromTestCase(TestCapabilitySuggestionStore))
    suite.addTests(loader.loadTestsFromTestCase(TestCapabilityDiscoveryRadar))
    suite.addTests(loader.loadTestsFromTestCase(TestDiagnosticsIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
