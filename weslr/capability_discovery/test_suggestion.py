"""Capability Discovery Radar - Phase 1 Tests.

Tests for:
- Creation
- Persistence
- Status transitions
- Deny/snooze behavior
- Archive behavior
- Search/filter behavior (SQL LIKE)
"""

from __future__ import annotations

import sqlite3
import time
import unittest
from pathlib import Path

from .data_model import (
    CapabilitySuggestion,
    CapabilityType,
    SuggestionStatus,
    SourceProvenance,
)
from .api import (
    create_suggestion,
    list_suggestions,
    search_suggestions,
    deny_suggestion,
    accept_suggestion,
    archive_suggestion,
    update_status,
    get_suggestion,
    get_decisions,
    count_suggestions,
)


class TestCapabilitySuggestion(unittest.TestCase):
    """Tests for CapabilitySuggestion model."""
    
    def test_creation_with_defaults(self):
        """Test that suggestion creates with proper defaults."""
        s = CapabilitySuggestion(
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
        )
        
        self.assertIsNotNone(s.id)
        self.assertEqual(s.status, SuggestionStatus.NEW)
        self.assertIsNotNone(s.created_at)
        self.assertIsNotNone(s.last_seen_at)
        self.assertEqual(s.tags, [])
        self.assertEqual(s.mentions_count, 1)
    
    def test_creation_with_explicit_values(self):
        """Test that explicit values are preserved."""
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        s = CapabilitySuggestion(
            id="explicit-id",
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
            created_at=now,
            last_seen_at=now,
            confidence=0.8,
            rank_score=75.0,
            tags=["tag1", "tag2"],
        )
        
        self.assertEqual(s.id, "explicit-id")
        self.assertEqual(s.confidence, 0.8)
        self.assertEqual(s.rank_score, 75.0)
        self.assertEqual(s.tags, ["tag1", "tag2"])
    
    def test_to_dict_roundtrip(self):
        """Test that to_dict/from_dict roundtrip works."""
        s = CapabilitySuggestion(
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
            confidence=0.9,
            rank_score=80.0,
            tags=["test"],
        )
        
        d = s.to_dict()
        s2 = CapabilitySuggestion.from_dict(d)
        
        self.assertEqual(s.id, s2.id)
        self.assertEqual(s.title, s2.title)
        self.assertEqual(s.confidence, s2.confidence)
        self.assertEqual(s.rank_score, s2.rank_score)
    
    def test_transition_to(self):
        """Test status transitions."""
        s = CapabilitySuggestion(
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
        )
        
        original_status = s.status
        original_last_seen = s.last_seen_at
        
        s.transition_to(SuggestionStatus.SUGGESTED)
        
        self.assertEqual(s.status, SuggestionStatus.SUGGESTED)
        self.assertGreater(s.last_seen_at, original_last_seen)
    
    def test_deny(self):
        """Test deny behavior."""
        s = CapabilitySuggestion(
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
        )
        
        s.deny(hours=24)
        
        self.assertEqual(s.status, SuggestionStatus.DENIED)
        self.assertIsNotNone(s.denied_until)
        self.assertGreater(len(s.denied_until), 0)
    
    def test_snooze(self):
        """Test snooze behavior."""
        s = CapabilitySuggestion(
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
        )
        
        s.snooze(hours=4)
        
        self.assertEqual(s.status, SuggestionStatus.SNOOZED)
        self.assertIsNotNone(s.snoozed_until)
    
    def test_is_denied(self):
        """Test is_denied check."""
        s = CapabilitySuggestion(
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
        )
        
        # Not denied by default
        self.assertFalse(s.is_denied())
        
        # Deny and check
        s.deny(hours=1)  # 1 hour in past for quick test
        self.assertTrue(s.is_denied())
    
    def test_is_expired(self):
        """Test is_expired check."""
        s = CapabilitySuggestion(
            title="Test",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why",
            improvement_area="Area",
        )
        
        # Not expired by default
        self.assertFalse(s.is_expired())
        
        # Deny with 0 hours (immediate expiry)
        s.deny(hours=0)
        self.assertTrue(s.is_denied_expired())
        self.assertTrue(s.is_expired())


class TestCapabilityStore(unittest.TestCase):
    """Tests for CapabilityStore persistence."""
    
    def setUp(self):
        """Set up test store with in-memory DB."""
        from .store import CapabilityStore
        self.store = CapabilityStore()
        # Use in-memory database
        self.store.conn.close()
        self.store.conn = sqlite3.connect(":memory:")
        self.store.conn.row_factory = sqlite3.Row
        self.store._init_schema()
    
    def tearDown(self):
        """Clean up test store."""
        self.store.close()
    
    def _create_test_suggestion(self):
        """Helper to create a test suggestion."""
        return CapabilitySuggestion(
            title="Test Suggestion",
            capability_type=CapabilityType.REAL_TIME_COLLAB,
            summary="Summary",
            why_it_matters="Why it matters",
            improvement_area="Area",
            provenance=[
                SourceProvenance(
                    url="https://example.com",
                    title="Example",
                    snippet="Test snippet",
                    relevance_score=0.8,
                    signal_type="tool_mention",
                    timestamp="2026-04-05T21:00:00Z",
                )
            ],
            confidence=0.7,
            rank_score=75.0,
        )
    
    def test_create_suggestion(self):
        """Test creating a suggestion."""
        s = self._create_test_suggestion()
        result = self.store.create_suggestion(s)
        
        self.assertEqual(result.id, s.id)
        
        # Verify in DB
        fetched = self.store.get_suggestion(s.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, s.title)
    
    def test_get_suggestion(self):
        """Test getting a suggestion by ID."""
        s = self._create_test_suggestion()
        self.store.create_suggestion(s)
        
        fetched = self.store.get_suggestion(s.id)
        self.assertEqual(fetched.id, s.id)
        self.assertEqual(fetched.title, s.title)
        self.assertEqual(len(fetched.provenance), 1)
    
    def test_update_suggestion(self):
        """Test updating a suggestion."""
        s = self._create_test_suggestion()
        self.store.create_suggestion(s)
        
        # Update
        s.title = "Updated Title"
        s.confidence = 0.9
        s.transition_to(SuggestionStatus.SUGGESTED)
        self.store.update_suggestion(s)
        
        # Verify
        fetched = self.store.get_suggestion(s.id)
        self.assertEqual(fetched.title, "Updated Title")
        self.assertEqual(fetched.confidence, 0.9)
    
    def test_list_suggestions(self):
        """Test listing suggestions."""
        s1 = self._create_test_suggestion()
        s1.title = "Suggestion 1"
        self.store.create_suggestion(s1)
        
        s2 = self._create_test_suggestion()
        s2.title = "Suggestion 2"
        self.store.create_suggestion(s2)
        
        # List all
        results = self.store.list_suggestions()
        self.assertEqual(len(results), 2)
        
        # Filter by status
        results = self.store.list_suggestions(status=SuggestionStatus.NEW)
        self.assertEqual(len(results), 2)
    
    def test_search_suggestions(self):
        """Test FTS5 search."""
        s = self._create_test_suggestion()
        s.title = "Real-time collaboration editing"
        s.summary = "WESLR needs real-time collaborative editing"
        s.tags = ["collaboration", "real-time"]
        self.store.create_suggestion(s)
        
        # Search by title
        results = self.store.search_suggestions("collaboration")
        self.assertGreater(len(results), 0)
        
        # Search by summary
        results = self.store.search_suggestions("editing")
        self.assertGreater(len(results), 0)
    
    def test_count_suggestions(self):
        """Test counting suggestions."""
        s1 = self._create_test_suggestion()
        self.store.create_suggestion(s1)
        
        s2 = self._create_test_suggestion()
        self.store.create_suggestion(s2)
        
        count = self.store.count_suggestions()
        self.assertEqual(count, 2)
        
        count = self.store.count_suggestions(status=SuggestionStatus.NEW)
        self.assertEqual(count, 2)
    
    def test_delete_suggestion(self):
        """Test deleting a suggestion."""
        s = self._create_test_suggestion()
        self.store.create_suggestion(s)
        
        deleted = self.store.delete_suggestion(s.id)
        self.assertTrue(deleted)
        
        fetched = self.store.get_suggestion(s.id)
        self.assertIsNone(fetched)
    
    def test_record_and_get_decisions(self):
        """Test recording and retrieving decisions."""
        s = self._create_test_suggestion()
        self.store.create_suggestion(s)
        
        self.store.record_decision(s.id, "deny", "Not needed")
        
        decisions = self.store.get_decisions(s.id)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["action"], "deny")
    
    def test_suggestion_provenance_persistence(self):
        """Test that provenance sources are persisted correctly."""
        s = self._create_test_suggestion()
        self.store.create_suggestion(s)
        
        fetched = self.store.get_suggestion(s.id)
        self.assertEqual(len(fetched.provenance), 1)
        self.assertEqual(fetched.provenance[0].url, "https://example.com")
        self.assertEqual(fetched.provenance[0].signal_type, "tool_mention")


if __name__ == "__main__":
    unittest.main()
