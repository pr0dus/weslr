"""Capability Discovery Radar - Phase 2 Tests.

Tests for:
- Seed source pack
- Seed ingestion pipeline
- Operator review loop
- Provenance preservation
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure we're in the workspace
sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.capability_discovery import (
    SeedSource,
    SeedKind,
    SeedStatus,
    get_seed_pack,
    get_enabled_seeds,
    SeedIngestionPipeline,
    OperatorReviewLoop,
    CapabilityStore,
    CapabilitySuggestion,
    CapabilityType,
    SuggestionStatus,
    SourceProvenance,
)


class TestSeedSource(unittest.TestCase):
    """Test SeedSource model."""

    def test_seed_creation(self):
        """Test creating a seed source."""
        seed = SeedSource(
            id="test-123",
            name="Test Source",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/test",
            tags=["test"],
        )
        self.assertEqual(seed.id, "test-123")
        self.assertEqual(seed.name, "Test Source")
        self.assertEqual(seed.kind, SeedKind.GITHUB_REPO)
        self.assertTrue(seed.enabled)
        self.assertEqual(seed.tags, ["test"])

    def test_seed_serialization(self):
        """Test serialization and deserialization."""
        seed = SeedSource(
            id="test-456",
            name="GitHub Test",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/test",
            tags=["test"],
        )
        data = seed.to_dict()
        self.assertEqual(data["id"], "test-456")
        self.assertEqual(data["kind"], "github_repo")

        restored = SeedSource.from_dict(data)
        self.assertEqual(restored.id, "test-456")
        self.assertEqual(restored.kind, SeedKind.GITHUB_REPO)

    def test_seed_enable_disable(self):
        """Test enable/disable."""
        seed = SeedSource(
            id="test-789",
            name="Test",
            kind=SeedKind.OTHER,
            enabled=False,
        )
        self.assertFalse(seed.enabled)
        seed.enable()
        self.assertTrue(seed.enabled)
        seed.disable()
        self.assertFalse(seed.enabled)


class TestSeedPack(unittest.TestCase):
    """Test seed source pack."""

    def test_get_seed_pack(self):
        """Test getting the full seed pack."""
        pack = get_seed_pack()
        self.assertGreater(len(pack), 0)

    def test_get_enabled_seeds(self):
        """Test getting only enabled seeds."""
        enabled = get_enabled_seeds()
        self.assertGreater(len(enabled), 0)

        # All should be enabled
        for seed in enabled:
            self.assertTrue(seed.enabled)

    def test_seed_pack_categories(self):
        """Test seed pack has expected categories."""
        pack = get_seed_pack()
        kinds = set(s.kind for s in pack)
        self.assertIn(SeedKind.REDDIT_COMMUNITY, kinds)
        self.assertIn(SeedKind.GITHUB_REPO, kinds)
        self.assertIn(SeedKind.SCIENCE_SOURCE, kinds)
        self.assertIn(SeedKind.PKM_ANCHOR, kinds)


class TestSeedIngestionPipeline(unittest.TestCase):
    """Test seed ingestion pipeline."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_seed.db"
        self.store = CapabilityStore(self.db_path)

    def tearDown(self):
        """Clean up."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_seed_to_signal(self):
        """Test converting a seed to signal."""
        from weslr.capability_discovery.seed_ingestion import SeedIngestionPipeline

        pipeline = SeedIngestionPipeline(self.store)
        seed = SeedSource(
            id="test-seed",
            name="Test Seed",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/test",
            tags=["test"],
        )
        signal = pipeline.seed_to_signal(seed)
        self.assertEqual(signal.source_kind.value, "other")
        self.assertEqual(signal.title, "Test Seed")

    def test_ingest_single_seed(self):
        """Test ingesting a single seed."""
        from weslr.capability_discovery.seed_ingestion import SeedIngestionPipeline

        pipeline = SeedIngestionPipeline(self.store)
        seed = SeedSource(
            id="test-seed-1",
            name="Test Seed 1",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/test/1",
            tags=["test"],
        )
        result = pipeline.ingest_seed(seed)
        self.assertEqual(result["status"], "ingested")
        self.assertIsNotNone(result["suggestion_id"])

    def test_ingest_all_enabled(self):
        """Test ingesting all enabled seeds."""
        from weslr.capability_discovery.seed_ingestion import SeedIngestionPipeline

        pipeline = SeedIngestionPipeline(self.store)
        results = pipeline.ingest_all_enabled()
        self.assertGreater(len(results), 0)
        # Allow ingested or duplicate status (due to title similarity)
        for r in results:
            self.assertIn(r["status"], ["ingested", "duplicate"])


class TestOperatorReviewLoop(unittest.TestCase):
    """Test operator review loop."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_review.db"
        self.store = CapabilityStore(self.db_path)

    def tearDown(self):
        """Clean up."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_list_latest_signals(self):
        """Test listing latest signals."""
        from weslr.capability_discovery.review import OperatorReviewLoop

        # First create some suggestions
        for i in range(3):
            suggestion = CapabilitySuggestion(
                title=f"Test Suggestion {i}",
                capability_type=CapabilityType.OTHER,
                summary=f"Summary {i}",
                why_it_matters=f"Why {i}",
                improvement_area=f"Improvement {i}",
                provenance=[],
                confidence=0.5,
                rank_score=i * 10,
                status=SuggestionStatus.NEW,
                tags=[],
                mentions_count=1,
                source_diversity=1,
            )
            self.store.create_suggestion(suggestion)

        review = OperatorReviewLoop(self.store)
        latest = review.list_latest_signals()
        self.assertEqual(len(latest), 3)

    def test_list_pending(self):
        """Test listing pending suggestions."""
        from weslr.capability_discovery.review import OperatorReviewLoop

        # Create some suggestions
        for i in range(5):
            suggestion = CapabilitySuggestion(
                title=f"Test Suggestion {i}",
                capability_type=CapabilityType.OTHER,
                summary=f"Summary {i}",
                why_it_matters=f"Why {i}",
                improvement_area=f"Improvement {i}",
                provenance=[],
                confidence=0.5,
                rank_score=i * 10,
                status=SuggestionStatus.NEW,
                tags=[],
                mentions_count=1,
                source_diversity=1,
            )
            self.store.create_suggestion(suggestion)

        # Archive some
        all_suggestions = self.store.list_suggestions()
        if len(all_suggestions) >= 2:
            self.store.update_suggestion(all_suggestions[0])
            self.store.update_suggestion(all_suggestions[1])

        review = OperatorReviewLoop(self.store)
        pending = review.list_pending()
        self.assertEqual(len(pending), 5)

    def test_get_summary(self):
        """Test getting summary."""
        from weslr.capability_discovery.review import OperatorReviewLoop

        review = OperatorReviewLoop(self.store)
        summary = review.get_summary()
        self.assertIn("total", summary)
        self.assertIn("by_status", summary)
        self.assertIn("pending_count", summary)

    def test_accept_suggestion(self):
        """Test accepting a suggestion."""
        from weslr.capability_discovery.review import OperatorReviewLoop
        from weslr.capability_discovery.data_model import CapabilitySuggestion, CapabilityType, SuggestionStatus

        # Create a suggestion
        suggestion = CapabilitySuggestion(
            title="Test to Accept",
            capability_type=CapabilityType.OTHER,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Improvement",
            provenance=[],
            confidence=0.5,
            rank_score=50,
            status=SuggestionStatus.NEW,
            tags=[],
            mentions_count=1,
            source_diversity=1,
        )
        self.store.create_suggestion(suggestion)

        review = OperatorReviewLoop(self.store)
        accepted = review.accept_suggestion(suggestion.id)
        self.assertEqual(accepted.status, SuggestionStatus.ACCEPTED)

    def test_deny_suggestion(self):
        """Test denying a suggestion."""
        from weslr.capability_discovery.review import OperatorReviewLoop
        from weslr.capability_discovery.data_model import CapabilitySuggestion, CapabilityType, SuggestionStatus

        # Create a suggestion
        suggestion = CapabilitySuggestion(
            title="Test to Deny",
            capability_type=CapabilityType.OTHER,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Improvement",
            provenance=[],
            confidence=0.5,
            rank_score=50,
            status=SuggestionStatus.NEW,
            tags=[],
            mentions_count=1,
            source_diversity=1,
        )
        self.store.create_suggestion(suggestion)

        review = OperatorReviewLoop(self.store)
        denied = review.deny_suggestion(suggestion.id, reason="Test denial")
        self.assertEqual(denied.status, SuggestionStatus.DENIED)

    def test_archive_suggestion(self):
        """Test archiving a suggestion."""
        from weslr.capability_discovery.review import OperatorReviewLoop
        from weslr.capability_discovery.data_model import CapabilitySuggestion, CapabilityType, SuggestionStatus

        # Create a suggestion
        suggestion = CapabilitySuggestion(
            title="Test to Archive",
            capability_type=CapabilityType.OTHER,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Improvement",
            provenance=[],
            confidence=0.5,
            rank_score=50,
            status=SuggestionStatus.NEW,
            tags=[],
            mentions_count=1,
            source_diversity=1,
        )
        self.store.create_suggestion(suggestion)

        review = OperatorReviewLoop(self.store)
        archived = review.archive_suggestion(suggestion.id)
        self.assertEqual(archived.status, SuggestionStatus.ARCHIVED)


class TestProvenancePreservation(unittest.TestCase):
    """Test provenance preservation through ingestion."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_provenance.db"
        self.store = CapabilityStore(self.db_path)

    def tearDown(self):
        """Clean up."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_seed_ingestion_preserves_provenance(self):
        """Test that seed ingestion preserves provenance."""
        from weslr.capability_discovery.seed_ingestion import SeedIngestionPipeline

        pipeline = SeedIngestionPipeline(self.store)
        seed = SeedSource(
            id="test-prov-1",
            name="Test Provenance",
            kind=SeedKind.GITHUB_REPO,
            url="https://github.com/test/repo",
            tags=["test", "github"],
        )
        result = pipeline.ingest_seed(seed)

        # Verify suggestion was created
        self.assertEqual(result["status"], "ingested")
        self.assertIsNotNone(result["suggestion_id"])

        # Verify provenance in store
        suggestion = self.store.get_suggestion(result["suggestion_id"])
        self.assertIsNotNone(suggestion)
        self.assertGreater(len(suggestion.provenance), 0)
        self.assertEqual(suggestion.provenance[0].signal_type, "other")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSeedSource))
    suite.addTests(loader.loadTestsFromTestCase(TestSeedPack))
    suite.addTests(loader.loadTestsFromTestCase(TestSeedIngestionPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestOperatorReviewLoop))
    suite.addTests(loader.loadTestsFromTestCase(TestProvenancePreservation))

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
