"""Capability Discovery Radar - Persistence Layer.

Uses SQLite with FTS5 for:
- Storing capability suggestions
- Full-text search
- Filtering by status, capability_type, tags
- 24h denial tracking
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .data_model import (
    CapabilitySuggestion,
    CapabilityType,
    SuggestionStatus,
    SourceProvenance,
)

# Database paths
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = WORKSPACE_DIR / "capability_discovery.db"


class CapabilityStore:
    """SQLite persistence layer for capability suggestions.
    
    Tables:
    - suggestions: Main suggestion data
    - sources: Provenance tracking
    - decisions: Operator actions (accept/deny/snooze)
    
    Indexes:
    - idx_status: status filtering
    - idx_capability_type: type filtering
    - idx_tags: tag search
    - idx_denied_until: expiration checking
    - idx_created_at: chronological sorting
    """
    
    def __init__(self, db_path: Path = None):
        """Initialize store with optional custom path."""
        self.db_path = db_path or DB_PATH
        self.db_dir = self.db_path.parent
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Create tables and indexes if they don't exist."""
        cursor = self.conn.cursor()
        
        # Suggestions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                capability_type TEXT NOT NULL,
                summary TEXT,
                why_it_matters TEXT,
                improvement_area TEXT,
                confidence REAL DEFAULT 0.5,
                rank_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'new',
                created_at TEXT,
                last_seen_at TEXT,
                last_ranked_at TEXT,
                denied_until TEXT,
                snoozed_until TEXT,
                tags TEXT,
                mentions_count INTEGER DEFAULT 1,
                growth_trend TEXT DEFAULT 'stable',
                source_diversity INTEGER DEFAULT 1,
                architectural_fit TEXT DEFAULT 'medium',
                first_seen_at TEXT,
                github_activity TEXT,
                science_relevance TEXT,
                extra_data TEXT
            )
        """)
        
        # Sources table (provenance tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                snippet TEXT,
                relevance_score REAL,
                signal_type TEXT,
                timestamp TEXT,
                FOREIGN KEY (suggestion_id) REFERENCES suggestions(id) ON DELETE CASCADE
            )
        """)
        
        # Decisions table (operator actions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT,
                notes TEXT,
                FOREIGN KEY (suggestion_id) REFERENCES suggestions(id) ON DELETE CASCADE
            )
        """)
        
        # Indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON suggestions(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_capability_type ON suggestions(capability_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at ON suggestions(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_denied_until ON suggestions(denied_until)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags ON suggestions(tags)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_title ON suggestions(title)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_summary ON suggestions(summary)
        """)
        
        self.conn.commit()
    
    def create_suggestion(self, suggestion: CapabilitySuggestion) -> CapabilitySuggestion:
        """Create a new suggestion."""
        cursor = self.conn.cursor()
        
        # Insert suggestion
        cursor.execute("""
            INSERT INTO suggestions (
                id, title, capability_type, summary, why_it_matters, improvement_area,
                confidence, rank_score, status, created_at, last_seen_at,
                tags, mentions_count, growth_trend, source_diversity,
                architectural_fit, first_seen_at, github_activity, science_relevance,
                extra_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            suggestion.id,
            suggestion.title,
            suggestion.capability_type.value,
            suggestion.summary,
            suggestion.why_it_matters,
            suggestion.improvement_area,
            suggestion.confidence,
            suggestion.rank_score,
            suggestion.status.value,
            suggestion.created_at,
            suggestion.last_seen_at,
            json.dumps(suggestion.tags),
            suggestion.mentions_count,
            suggestion.growth_trend,
            suggestion.source_diversity,
            suggestion.architectural_fit,
            suggestion.first_seen_at or suggestion.created_at,
            json.dumps(suggestion.github_activity) if suggestion.github_activity else None,
            suggestion.science_relevance,
            json.dumps({
                "denied_until": suggestion.denied_until,
                "snoozed_until": suggestion.snoozed_until,
            }),
        ))
        
        # Insert sources
        for source in suggestion.provenance:
            cursor.execute("""
                INSERT INTO sources (
                    suggestion_id, url, title, snippet, relevance_score, signal_type, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion.id,
                source.url,
                source.title,
                source.snippet,
                source.relevance_score,
                source.signal_type,
                source.timestamp,
            ))
        
        self.conn.commit()
        return suggestion
    
    def update_suggestion(self, suggestion: CapabilitySuggestion) -> CapabilitySuggestion:
        """Update an existing suggestion."""
        cursor = self.conn.cursor()
        
        # Update suggestion
        cursor.execute("""
            UPDATE suggestions SET
                title = ?,
                capability_type = ?,
                summary = ?,
                why_it_matters = ?,
                improvement_area = ?,
                confidence = ?,
                rank_score = ?,
                status = ?,
                last_seen_at = ?,
                last_ranked_at = ?,
                denied_until = ?,
                snoozed_until = ?,
                tags = ?,
                mentions_count = ?,
                growth_trend = ?,
                source_diversity = ?,
                architectural_fit = ?,
                first_seen_at = ?,
                github_activity = ?,
                science_relevance = ?,
                extra_data = ?
            WHERE id = ?
        """, (
            suggestion.title,
            suggestion.capability_type.value,
            suggestion.summary,
            suggestion.why_it_matters,
            suggestion.improvement_area,
            suggestion.confidence,
            suggestion.rank_score,
            suggestion.status.value,
            suggestion.last_seen_at,
            suggestion.last_ranked_at,
            suggestion.denied_until,
            suggestion.snoozed_until,
            json.dumps(suggestion.tags),
            suggestion.mentions_count,
            suggestion.growth_trend,
            suggestion.source_diversity,
            suggestion.architectural_fit,
            suggestion.first_seen_at,
            json.dumps(suggestion.github_activity) if suggestion.github_activity else None,
            suggestion.science_relevance,
            json.dumps({
                "denied_until": suggestion.denied_until,
                "snoozed_until": suggestion.snoozed_until,
            }),
            suggestion.id,
        ))
        
        self.conn.commit()
        return suggestion
    
    def get_suggestion(self, suggestion_id: str) -> Optional[CapabilitySuggestion]:
        """Get a suggestion by ID."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Get sources
        cursor.execute("SELECT * FROM sources WHERE suggestion_id = ?", (suggestion_id,))
        source_rows = cursor.fetchall()
        
        # Build suggestion
        data = dict(row)
        sources = [SourceProvenance(
            url=sr[2], title=sr[3], snippet=sr[4], relevance_score=sr[5],
            signal_type=sr[6], timestamp=sr[7]
        ) for sr in source_rows] if source_rows else []
        
        # Parse extra_data
        extra = json.loads(data.get("extra_data", "{}"))
        
        return CapabilitySuggestion(
            id=data["id"],
            title=data["title"],
            capability_type=CapabilityType(data["capability_type"]),
            summary=data["summary"],
            why_it_matters=data["why_it_matters"],
            improvement_area=data["improvement_area"],
            provenance=sources,
            confidence=data["confidence"] or 0.5,
            rank_score=data["rank_score"] or 0.0,
            status=SuggestionStatus(data["status"]),
            created_at=data["created_at"],
            last_seen_at=data["last_seen_at"],
            last_ranked_at=data["last_ranked_at"],
            denied_until=extra.get("denied_until"),
            snoozed_until=extra.get("snoozed_until"),
            tags=data["tags"] and json.loads(data["tags"]) or [],
            mentions_count=data["mentions_count"] or 1,
            growth_trend=data["growth_trend"] or "stable",
            source_diversity=data["source_diversity"] or 1,
            architectural_fit=data["architectural_fit"] or "medium",
            first_seen_at=data["first_seen_at"],
            github_activity=json.loads(data["github_activity"]) if data["github_activity"] else None,
            science_relevance=data["science_relevance"],
        )
    
    def list_suggestions(
        self,
        status: Optional[SuggestionStatus] = None,
        capability_type: Optional[CapabilityType] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "last_seen_at",
        sort_desc: bool = True,
    ) -> List[CapabilitySuggestion]:
        """List suggestions with optional filters."""
        cursor = self.conn.cursor()
        
        # Build query
        query = "SELECT * FROM suggestions"
        conditions = []
        params = []
        
        if status:
            conditions.append("status = ?")
            params.append(status.value)
        
        if capability_type:
            conditions.append("capability_type = ?")
            params.append(capability_type.value)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Sort
        order_clause = f"{sort_by} {'DESC' if sort_desc else 'ASC'}"
        query += f" ORDER BY {order_clause}"
        
        # Pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        suggestions = []
        for row in rows:
            suggestions.append(self._row_to_suggestion(row))
        
        return suggestions
    
    def _row_to_suggestion(self, row: sqlite3.Row) -> CapabilitySuggestion:
        """Convert a database row to a CapabilitySuggestion."""
        data = dict(row)
        
        # Get sources
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sources WHERE suggestion_id = ?", (data["id"],))
        source_rows = cursor.fetchall()
        
        sources = []
        for sr in source_rows:
            sources.append(SourceProvenance(
                url=sr["url"],
                title=sr["title"],
                snippet=sr["snippet"],
                relevance_score=sr["relevance_score"],
                signal_type=sr["signal_type"],
                timestamp=sr["timestamp"],
            ))
        
        # Parse extra_data
        extra = json.loads(data.get("extra_data", "{}"))
        
        return CapabilitySuggestion(
            id=data["id"],
            title=data["title"],
            capability_type=CapabilityType(data["capability_type"]),
            summary=data["summary"],
            why_it_matters=data["why_it_matters"],
            improvement_area=data["improvement_area"],
            provenance=sources,
            confidence=data["confidence"] or 0.5,
            rank_score=data["rank_score"] or 0.0,
            status=SuggestionStatus(data["status"]),
            created_at=data["created_at"],
            last_seen_at=data["last_seen_at"],
            last_ranked_at=data["last_ranked_at"],
            denied_until=extra.get("denied_until"),
            snoozed_until=extra.get("snoozed_until"),
            tags=data["tags"] and json.loads(data["tags"]) or [],
            mentions_count=data["mentions_count"] or 1,
            growth_trend=data["growth_trend"] or "stable",
            source_diversity=data["source_diversity"] or 1,
            architectural_fit=data["architectural_fit"] or "medium",
            first_seen_at=data["first_seen_at"],
            github_activity=json.loads(data["github_activity"]) if data["github_activity"] else None,
            science_relevance=data["science_relevance"],
        )
    
    def search_suggestions(self, query: str, limit: int = 50) -> List[CapabilitySuggestion]:
        """Search suggestions using LIKE pattern matching."""
        cursor = self.conn.cursor()
        
        # Search across title, summary, and tags using LIKE
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM suggestions
            WHERE title LIKE ? OR summary LIKE ? OR tags LIKE ?
            ORDER BY last_seen_at DESC
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, limit))
        
        rows = cursor.fetchall()
        return [self._row_to_suggestion(row) for row in rows]
    
    def count_suggestions(self, status: Optional[SuggestionStatus] = None) -> int:
        """Count suggestions with optional filter."""
        cursor = self.conn.cursor()
        
        query = "SELECT COUNT(*) FROM suggestions"
        if status:
            query += " WHERE status = ?"
        
        cursor.execute(query, (status.value,) if status else ())
        return cursor.fetchone()[0]
    
    def delete_suggestion(self, suggestion_id: str) -> bool:
        """Delete a suggestion by ID."""
        cursor = self.conn.cursor()
        
        cursor.execute("DELETE FROM sources WHERE suggestion_id = ?", (suggestion_id,))
        cursor.execute("DELETE FROM suggestions WHERE id = ?", (suggestion_id,))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def record_decision(self, suggestion_id: str, action: str, notes: str = "") -> None:
        """Record an operator decision."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO decisions (suggestion_id, action, timestamp, notes)
            VALUES (?, ?, ?, ?)
        """, (suggestion_id, action, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), notes))
        
        self.conn.commit()
    
    def get_decisions(self, suggestion_id: str) -> List[Dict[str, Any]]:
        """Get all decisions for a suggestion."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM decisions WHERE suggestion_id = ?
            ORDER BY timestamp DESC
        """, (suggestion_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()


# Global store instance
_store: Optional[CapabilityStore] = None


def get_store(db_path: Path = None) -> CapabilityStore:
    """Get or create the global store instance."""
    global _store
    
    if _store is None:
        _store = CapabilityStore(db_path)
    
    return _store
