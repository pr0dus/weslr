# test_adapters.py - Tests for Reddit and GitHub adapters
# Phase 3: Minimal real-source adapters
# Run with: python test_adapters.py

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

# Ensure we're in the workspace
import sys
sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.adapters.reddit_adapter import RedditAdapter, RedditSignal
from weslr.adapters.github_adapter import GitHubAdapter, GitHubSignal
from weslr.capability_ingestion import (
    SourceSignal,
    SourceKind,
    SignalStatus,
    CapabilityIngestionPipeline,
)
from weslr.capability_suggestion import (
    CapabilityDiscoveryRadar,
    CapabilitySuggestionStore,
    SourceProvenance,
)


# ============================================================================
# TEST DATA
# ============================================================================

REDDIT_TEST_DATA = {
    "subreddit": "technology",
    "title": "Need better capability discovery tools",
    "url": "https://reddit.com/r/technology/comments/abc123/need_better_capabilities",
    "body": "Current tools are too complex. We need a simpler capability discovery radar.",
    "author": "test_user",
    "upvotes": 42,
    "timestamp": "2026-04-05T10:30:00Z",
    "tags": ["capability", "discovery", "tools"],
    "detected_capability": "capability discovery radar"
}

GITHUB_TEST_DATA = {
    "repo": "openclaw/openclaw",
    "title": "Add capability discovery radar Phase 3",
    "url": "https://github.com/openclaw/openclaw/issues/42",
    "body": "Implement minimal adapters for Reddit and GitHub to populate the capability queue.",
    "author": "test_user",
    "labels": ["enhancement", "phase3"],
    "stars": 5,
    "activity": 10,
    "timestamp": "2026-04-05T14:00:00Z",
    "detected_capability": "capability discovery adapters"
}


# ============================================================================
# TEST REDDIT ADAPTER
# ============================================================================

class TestRedditAdapter(unittest.TestCase):
    """Test Reddit adapter."""

    def setUp(self):
        """Set up test environment."""
        self.adapter = RedditAdapter()

    def test_from_dict_basic(self):
        """Test basic from_dict conversion."""
        signal = self.adapter.from_dict(REDDIT_TEST_DATA)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.source_kind, SourceKind.REDDIT)
        self.assertEqual(signal.title, REDDIT_TEST_DATA["title"])
        self.assertEqual(signal.url, REDDIT_TEST_DATA["url"])
        self.assertEqual(signal.body, REDDIT_TEST_DATA["body"])
        self.assertEqual(signal.provenance, "reddit:technology")
        self.assertEqual(signal.detected_capability, "capability discovery radar")

    def test_from_dict_with_tags(self):
        """Test from_dict with tags."""
        signal = self.adapter.from_dict(REDDIT_TEST_DATA)
        self.assertEqual(signal.tags, ["capability", "discovery", "tools"])

    def test_from_dict_missing_required(self):
        """Test from_dict with missing required fields."""
        incomplete = {"subreddit": "test", "title": "Test"}
        signal = self.adapter.from_dict(incomplete)
        self.assertIsNone(signal)

    def test_from_reddit_signal(self):
        """Test from_reddit_signal conversion."""
        reddit_signal = RedditSignal(
            subreddit="technology",
            title="Test Signal",
            url="https://reddit.com/test",
            body="Test body",
            tags=["tag1"],
            detected_capability="test capability",
        )
        
        signal = self.adapter.from_reddit_signal(reddit_signal)
        self.assertEqual(signal.source_kind, SourceKind.REDDIT)
        self.assertEqual(signal.title, "Test Signal")
        self.assertEqual(signal.provenance, "reddit:technology")
        self.assertEqual(signal.detected_capability, "test capability")

    def test_extract_subreddit_from_url(self):
        """Test subreddit extraction from URL."""
        url = "https://reddit.com/r/technology/comments/abc123"
        subreddit = self.adapter.extract_subreddit_from_url(url)
        self.assertEqual(subreddit, "technology")

    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        ts = "2026-04-05T10:30:00Z"
        parsed = self.adapter.parse_timestamp(ts)
        self.assertEqual(parsed, "2026-04-05T10:30:00Z")

    def test_from_file(self):
        """Test loading from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "reddit_test.json"
            with open(path, "w") as f:
                json.dump([REDDIT_TEST_DATA], f)
            
            signals = self.adapter.from_file(path)
            self.assertEqual(len(signals), 1)
            self.assertEqual(signals[0].title, REDDIT_TEST_DATA["title"])


# ============================================================================
# TEST GITHUB ADAPTER
# ============================================================================

class TestGitHubAdapter(unittest.TestCase):
    """Test GitHub adapter."""

    def setUp(self):
        """Set up test environment."""
        self.adapter = GitHubAdapter()

    def test_from_dict_basic(self):
        """Test basic from_dict conversion."""
        signal = self.adapter.from_dict(GITHUB_TEST_DATA)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.source_kind, SourceKind.GITHUB)
        self.assertEqual(signal.title, GITHUB_TEST_DATA["title"])
        self.assertEqual(signal.url, GITHUB_TEST_DATA["url"])
        self.assertEqual(signal.body, GITHUB_TEST_DATA["body"])
        self.assertEqual(signal.provenance, "github:openclaw/openclaw")
        self.assertEqual(signal.detected_capability, "capability discovery adapters")

    def test_from_dict_with_labels(self):
        """Test from_dict with labels (tags)."""
        signal = self.adapter.from_dict(GITHUB_TEST_DATA)
        self.assertEqual(signal.tags, ["enhancement", "phase3"])

    def test_from_dict_missing_required(self):
        """Test from_dict with missing required fields."""
        incomplete = {"repo": "test/test", "title": "Test"}
        signal = self.adapter.from_dict(incomplete)
        self.assertIsNone(signal)

    def test_from_github_signal(self):
        """Test from_github_signal conversion."""
        github_signal = GitHubSignal(
            repo="openclaw/openclaw",
            title="Test Signal",
            url="https://github.com/test/issue/1",
            body="Test body",
            labels=["bug"],
            detected_capability="bug tracking",
        )
        
        signal = self.adapter.from_github_signal(github_signal)
        self.assertEqual(signal.source_kind, SourceKind.GITHUB)
        self.assertEqual(signal.title, "Test Signal")
        self.assertEqual(signal.provenance, "github:openclaw/openclaw")
        self.assertEqual(signal.detected_capability, "bug tracking")

    def test_extract_repo_from_url(self):
        """Test repo extraction from URL."""
        url = "https://github.com/openclaw/openclaw/issues/42"
        repo = self.adapter.extract_repo_from_url(url)
        self.assertEqual(repo, "openclaw/openclaw")

    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        ts = "2026-04-05T14:00:00Z"
        parsed = self.adapter.parse_timestamp(ts)
        self.assertEqual(parsed, "2026-04-05T14:00:00Z")

    def test_from_file(self):
        """Test loading from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "github_test.json"
            with open(path, "w") as f:
                json.dump([GITHUB_TEST_DATA], f)
            
            signals = self.adapter.from_file(path)
            self.assertEqual(len(signals), 1)
            self.assertEqual(signals[0].title, GITHUB_TEST_DATA["title"])


# ============================================================================
# TEST PIPELINE INTEGRATION
# ============================================================================

class TestAdapterPipelineIntegration(unittest.TestCase):
    """Test adapters with ingestion pipeline."""

    def test_reddit_ingestion(self):
        """Test Reddit adapter through full pipeline."""
        # Setup
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_pipeline.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)
        
        adapter = RedditAdapter()
        signal = adapter.from_dict(REDDIT_TEST_DATA)
        
        # Ingest
        result = pipeline.ingest_signal(signal)
        
        # Verify
        self.assertEqual(result["status"], "ingested")
        self.assertIsNotNone(result["suggestion_id"])
        
        # Check provenance
        suggestion = radar.store.get(result["suggestion_id"])
        self.assertEqual(suggestion.provenance, SourceProvenance.REDDIT)
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_github_ingestion(self):
        """Test GitHub adapter through full pipeline."""
        # Setup
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_pipeline.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)
        
        adapter = GitHubAdapter()
        signal = adapter.from_dict(GITHUB_TEST_DATA)
        
        # Ingest
        result = pipeline.ingest_signal(signal)
        
        # Verify
        self.assertEqual(result["status"], "ingested")
        self.assertIsNotNone(result["suggestion_id"])
        
        # Check provenance
        suggestion = radar.store.get(result["suggestion_id"])
        self.assertEqual(suggestion.provenance, SourceProvenance.GITHUB)
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_both_ingestions_coexist(self):
        """Test both adapters can ingest simultaneously."""
        # Setup
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_coexist.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)
        
        # Ingest both
        reddit_adapter = RedditAdapter()
        github_adapter = GitHubAdapter()
        
        reddit_signal = reddit_adapter.from_dict(REDDIT_TEST_DATA)
        github_signal = github_adapter.from_dict(GITHUB_TEST_DATA)
        
        reddit_result = pipeline.ingest_signal(reddit_signal)
        github_result = pipeline.ingest_signal(github_signal)
        
        # Verify both ingested
        self.assertEqual(reddit_result["status"], "ingested")
        self.assertEqual(github_result["status"], "ingested")
        
        # Check summary
        summary = radar.get_summary()
        self.assertEqual(summary["total"], 2)
        
        # Verify provenances
        suggestions = radar.list()
        provenances = [s.provenance for s in suggestions]
        self.assertIn(SourceProvenance.REDDIT, provenances)
        self.assertIn(SourceProvenance.GITHUB, provenances)
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()

    def test_provenance_preservation(self):
        """Test that provenance is preserved through the pipeline."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_provenance.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        pipeline = CapabilityIngestionPipeline(radar)
        
        # Ingest from each adapter
        reddit_adapter = RedditAdapter()
        github_adapter = GitHubAdapter()
        
        reddit_signal = reddit_adapter.from_dict(REDDIT_TEST_DATA)
        github_signal = github_adapter.from_dict(GITHUB_TEST_DATA)
        
        pipeline.ingest_signal(reddit_signal)
        pipeline.ingest_signal(github_signal)
        
        # Get all suggestions and check provenance
        suggestions = radar.list()
        for s in suggestions:
            if s.provenance == SourceProvenance.REDDIT:
                # Check that the Reddit signal's provenance info is preserved
                # The provenance is in the normalized notes field
                self.assertIsNotNone(s.notes)
                self.assertIn("reddit", s.notes.lower())
            elif s.provenance == SourceProvenance.GITHUB:
                # Check that the GitHub signal's provenance info is preserved
                self.assertIsNotNone(s.notes)
                self.assertIn("github", s.notes.lower())
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()


# ============================================================================
# TEST DETECTED_CAPABILITY HANDLING
# ============================================================================

class TestDetectedCapability(unittest.TestCase):
    """Test detected_capability field handling."""

    def test_reddit_detected_capability(self):
        """Test Reddit adapter preserves detected_capability."""
        adapter = RedditAdapter()
        signal = adapter.from_dict(REDDIT_TEST_DATA)
        self.assertEqual(signal.detected_capability, "capability discovery radar")

    def test_github_detected_capability(self):
        """Test GitHub adapter preserves detected_capability."""
        adapter = GitHubAdapter()
        signal = adapter.from_dict(GITHUB_TEST_DATA)
        self.assertEqual(signal.detected_capability, "capability discovery adapters")

    def test_normalized_capability_text(self):
        """Test detected_capability is used in normalization."""
        temp_dir = Path(tempfile.mkdtemp())
        db_path = temp_dir / "test_cap.db"
        store = CapabilitySuggestionStore(db_path)
        radar = CapabilityDiscoveryRadar(store)
        
        # Create signals with detected_capability
        reddit_signal = SourceSignal(
            id="reddit-test-cap",
            source_kind=SourceKind.REDDIT,
            title="Test",
            url="https://reddit.com/test",
            detected_capability="machine learning analysis",
            tags=["ml", "analysis"],
        )
        
        github_signal = SourceSignal(
            id="github-test-cap",
            source_kind=SourceKind.GITHUB,
            title="Test",
            url="https://github.com/test",
            detected_capability="automated testing",
            tags=["testing", "automation"],
        )
        
        # Normalize
        from weslr.capability_ingestion import NormalizationPipeline
        pipeline = NormalizationPipeline(radar)
        
        reddit_norm = pipeline.normalize(reddit_signal)
        github_norm = pipeline.normalize(github_signal)
        
        # Check capability text is in normalization output
        self.assertIn("machine learning", reddit_norm["summary"].lower())
        self.assertIn("automated testing", github_norm["summary"].lower())
        
        # Cleanup
        if db_path.exists():
            db_path.unlink()
        temp_dir.rmdir()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRedditAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestGitHubAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestAdapterPipelineIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDetectedCapability))
    
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
