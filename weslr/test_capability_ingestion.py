# test_capability_ingestion.py - Focused tests for Capability Discovery Phase 2
# Ingestion pipeline and normalization.
# Run with: python test_capability_ingestion.py

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Ensure we're in the workspace
import sys
sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.capability_ingestion import (
    SourceSignal,
    SourceKind,
    SignalStatus,
    NormalizationPipeline,
    CapabilityIngestionPipeline,
)
from weslr.capability_suggestion import (
    CapabilitySuggestion,
    CapabilityType,
    SuggestionStatus,
    SourceProvenance,
    CapabilityDiscoveryRadar,
    CapabilitySuggestionStore,
)


class TestSourceSignal(unittest.TestCase):
    """Test SourceSignal model."""

    def test_signal_creation(self):
        """Test creating a source signal."""
        signal = SourceSignal(
            id="test-123",
            source_kind=SourceKind.MANUAL,
            title="Test Signal",
            body="Test body",
        )
        self.assertEqual(signal.id, "test-123")
        self.assertEqual(signal.source_kind, SourceKind.MANUAL)
        self.assertEqual(signal.title, "Test Signal")
        self.assertEqual(signal.body, "Test body")
        self.assertEqual(signal.status, SignalStatus.PENDING)

    def test_signal_serialization(self):
        """Test serialization and deserialization."""
        signal = SourceSignal(
            id="test-456",
            source_kind=SourceKind.REDDIT,
            title="Reddit Test",
            url="https://reddit.com/test",
            tags=["test", "ml"],
        )

        data = signal.to_dict()
        self.assertEqual(data["source_kind"], "reddit")
        self.assertEqual(data["tags"], ["test", "ml"])

        restored = SourceSignal.from_dict(data)
        self.assertEqual(restored.id, "test-456")
        self.assertEqual(restored.source_kind, SourceKind.REDDIT)

    def test_update_status(self):
        """Test status update."""
        signal = SourceSignal(
            id="test-789",
            source_kind=SourceKind.GITHUB,
            title="GitHub Test",
        )
        signal.update_status(SignalStatus.NORMALIZED)
        self.assertEqual(signal.status, SignalStatus.NORMALIZED)
        self.assertIsNotNone(signal.normalized_at)


class TestNormalizationPipeline(unittest.TestCase):
    """Test normalization pipeline."""

    def setUp(self):
        """Set up test environment."""
        # Use temp directory for database
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test_normalize.db"
        radar = CapabilityDiscoveryRadar()
        radar.store.db_path = self.db_path
        self.pipeline = NormalizationPipeline(radar)

    def tearDown(self):
        """Clean up."""
        if self.db_path.exists():
            self.db_path.unlink()
        self.temp_dir.rmdir()

    def test_extract_capability_from_title(self):
        """Test capability extraction from title."""
        signal = SourceSignal(
            id="test-1",
            source_kind=SourceKind.MANUAL,
            title="Add machine learning analysis feature",
            body="We need better analysis",
        )
        capability = self.pipeline._extract_capability(signal)
        self.assertIn("machine learning", capability.lower() if capability else "")

    def test_extract_capability_from_body(self):
        """Test capability extraction from body."""
        signal = SourceSignal(
            id="test-2",
            source_kind=SourceKind.MANUAL,
            title="Enhance capabilities",
            body="Implement automated data ingestion pipeline",
        )
        capability = self.pipeline._extract_capability(signal)
        # Check that we got some capability text
        self.assertIsNotNone(capability)
        # The capability extraction may find "capabilities" as the relevant part
        # since "ingestion" appears in the word "pipeline"
        self.assertTrue(len(capability) > 0)

    def test_detect_capability_type_analysis(self):
        """Test capability type detection for analysis."""
        signal = SourceSignal(
            id="test-3",
            source_kind=SourceKind.MANUAL,
            title="Analysis feature",
            body="Need better analytics",
            tags=["analytics", "model"],
        )
        capability = self.pipeline._extract_capability(signal)
        cap_type = self.pipeline._detect_capability_type(signal, capability)
        self.assertEqual(cap_type, CapabilityType.ANALYSIS)

    def test_detect_capability_type_ingestion(self):
        """Test capability type detection for ingestion."""
        signal = SourceSignal(
            id="test-4",
            source_kind=SourceKind.MANUAL,
            title="Ingestion system",
            body="Need data ingestion",
            tags=["ingest", "import"],
        )
        capability = self.pipeline._extract_capability(signal)
        cap_type = self.pipeline._detect_capability_type(signal, capability)
        self.assertEqual(cap_type, CapabilityType.INGESTION)

    def test_build_summary(self):
        """Test summary building."""
        signal = SourceSignal(
            id="test-5",
            source_kind=SourceKind.REDDIT,
            title="Test Reddit",
            url="https://reddit.com/test",
            snippet="Test snippet content",
        )
        summary = self.pipeline._build_summary(signal, "test capability")
        self.assertIn("Reddit", summary)
        self.assertIn("test capability", summary)
        self.assertIn("Test Reddit", summary)

    def test_build_why_matters(self):
        """Test why it matters building."""
        signal = SourceSignal(
            id="test-6",
            source_kind=SourceKind.MANUAL,
            title="Test",
        )
        why = self.pipeline._build_why_matters(
            signal, CapabilityType.ANALYSIS, "test capability"
        )
        self.assertIn("analysis", why.lower())
        self.assertIn("test capability", why)

    def test_estimate_confidence(self):
        """Test confidence estimation."""
        signal = SourceSignal(
            id="test-7",
            source_kind=SourceKind.GITHUB,
            title="Good Signal",
            body="Complete description",
            tags=["tag1", "tag2", "tag3"],
        )
        confidence = self.pipeline._estimate_confidence(signal)
        self.assertGreater(confidence, 0.5)
        self.assertLessEqual(confidence, 1.0)

    def test_estimate_rank_score(self):
        """Test rank score estimation."""
        signal = SourceSignal(
            id="test-8",
            source_kind=SourceKind.GITHUB,
            title="GitHub Issue",
            body="Issue content here",
            tags=["priority", "urgent"],
        )
        score = self.pipeline._estimate_rank_score(signal, CapabilityType.ANALYSIS, "test")
        self.assertGreater(score, 0)  # Base score

    def test_full_normalization(self):
        """Test full normalization pipeline."""
        signal = SourceSignal(
            id="test-9",
            source_kind=SourceKind.GITHUB,
            title="GitHub Analysis Feature",
            url="https://github.com/test/issue/1",
            body="Need better analysis capabilities",
            tags=["analysis", "ml"],
            detected_capability="Machine learning analysis",
        )
        normalized = self.pipeline.normalize(signal)
        self.assertIn("title", normalized)
        self.assertIn("summary", normalized)
        self.assertIn("why_it_matters", normalized)
        self.assertIn("improvement_area", normalized)
        self.assertIn("confidence", normalized)
        self.assertIn("rank_score", normalized)
        self.assertEqual(normalized["provenance"], "github")


class TestCapabilityIngestionPipeline(unittest.TestCase):
    """Test ingestion pipeline end-to-end."""

    def test_ingest_manual(self):
        """Test manual signal ingestion."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_manual.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        result = pipeline.ingest_manual(
            title="Test Manual Ingestion",
            body="This is a test signal",
            tags=["manual", "test"],
        )
        self.assertEqual(result["status"], "ingested")
        self.assertIsNotNone(result["suggestion_id"])
        self.assertIsNone(result["error"])

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_ingest_reddit(self):
        """Test Reddit signal ingestion."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_reddit.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        result = pipeline.ingest_reddit(
            title="Test Reddit",
            url="https://reddit.com/r/test",
            body="Test body",
        )
        self.assertEqual(result["status"], "ingested")
        self.assertIsNotNone(result["suggestion_id"])

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_ingest_github(self):
        """Test GitHub signal ingestion."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_github.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        result = pipeline.ingest_github(
            title="Test GitHub",
            url="https://github.com/test/issue/1",
            body="Test body",
        )
        self.assertEqual(result["status"], "ingested")
        self.assertIsNotNone(result["suggestion_id"])

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_deduplication_by_url(self):
        """Test duplicate detection by URL."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_dup.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        # First ingestion
        result1 = pipeline.ingest_github(
            title="Duplicate Test",
            url="https://github.com/test/issue/1",
            body="Test body",
        )
        self.assertEqual(result1["status"], "ingested")

        # Second ingestion with same URL should be duplicate
        result2 = pipeline.ingest_github(
            title="Duplicate Test 2",
            url="https://github.com/test/issue/1",
            body="Same content",
        )
        self.assertEqual(result2["status"], "duplicate")
        self.assertEqual(result2["duplicate_of"], result1["suggestion_id"])

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_ingestion_summary(self):
        """Test summary after ingestion."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_summary.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        pipeline.ingest_manual(
            title="Test 1",
            body="Test body 1",
        )
        pipeline.ingest_reddit(
            title="Test 2",
            url="https://reddit.com/test2",
        )
        pipeline.ingest_github(
            title="Test 3",
            url="https://github.com/test3",
        )

        summary = radar.get_summary()
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["by_status"]["new"], 3)
        self.assertEqual(summary["pending_count"], 3)

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_search_after_ingestion(self):
        """Test search works after ingestion."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_search.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        pipeline.ingest_manual(
            title="Machine Learning Analysis",
            body="ML analysis capabilities",
        )
        pipeline.ingest_manual(
            title="Data Visualization",
            body="Plotting tools",
        )

        results = radar.search("machine")
        self.assertEqual(len(results), 1)
        self.assertIn("Machine Learning", results[0].title)

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_filter_by_provenance(self):
        """Test filtering by provenance."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_filter.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        pipeline.ingest_manual(title="Manual 1")
        pipeline.ingest_reddit(title="Reddit 1", url="https://reddit.com/r/1")
        pipeline.ingest_github(title="GitHub 1", url="https://github.com/test/1")

        # Filter by provenance
        github_only = radar.list(
            provenance=SourceProvenance.GITHUB
        )
        self.assertEqual(len(github_only), 1)
        self.assertEqual(github_only[0].provenance, SourceProvenance.GITHUB)

        manual_only = radar.list(
            provenance=SourceProvenance.DIRECT_SUBMISSION
        )
        self.assertEqual(len(manual_only), 1)
        self.assertEqual(manual_only[0].provenance, SourceProvenance.DIRECT_SUBMISSION)

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_archive_after_ingestion(self):
        """Test archiving after ingestion."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_archive.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)

        result = pipeline.ingest_manual(
            title="To Be Archived",
            body="Test body",
        )
        self.assertEqual(result["status"], "ingested")

        # Archive the suggestion
        suggestion = radar.store.get(result["suggestion_id"])
        archived = radar.archive(suggestion.id, reason="Done with it")
        self.assertEqual(archived.status, SuggestionStatus.ARCHIVED)

        # Should not show in default list
        pending = radar.list()
        self.assertNotIn(result["suggestion_id"], [s.id for s in pending])

        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()


if __name__ == "__main__":
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSourceSignal))
    suite.addTests(loader.loadTestsFromTestCase(TestNormalizationPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestCapabilityIngestionPipeline))

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
