# capability_suggestion.py - Weslr Capability Discovery Radar
# Data model, store, and state machine for capability suggestions.
# Additive only, reversible (single file removal + storage revert).

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any


# ============================================================================
# ENUMS
# ============================================================================

class CapabilityType(str, Enum):
    """Types of capabilities that can be suggested."""
    INGESTION = "ingestion"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    STORAGE = "storage"
    SECURITY = "security"
    OTHER = "other"


class SuggestionStatus(str, Enum):
    """State transitions for capability suggestions."""
    NEW = "new"
    SUGGESTED = "suggested"
    ACCEPTED = "accepted"
    DENIED = "denied"
    SNOOZED = "snoozed"
    ARCHIVED = "archived"


class SourceProvenance(str, Enum):
    """Where a suggestion originated from."""
    INTERNAL_REVIEW = "internal_review"
    REDDIT = "reddit"
    GITHUB = "github"
    EMAIL = "email"
    DIRECT_SUBMISSION = "direct_submission"
    OTHER = "other"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CapabilitySuggestion:
    """A capability suggestion with full provenance tracking."""
    id: str
    title: str
    description: str
    capability_type: CapabilityType
    status: SuggestionStatus
    provenance: SourceProvenance
    created_at: str
    updated_at: str
    suggestion_text: Optional[str] = None
    context: Optional[str] = None
    tags: Optional[str] = None  # comma-separated list
    priority: int = 0  # higher = more urgent
    denial_count: int = 0
    last_denied_at: Optional[str] = None
    archived_at: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for JSON storage)."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilitySuggestion:
        """Deserialize from dict."""
        # Convert string enums back
        data["capability_type"] = CapabilityType(data.get("capability_type", "other"))
        data["status"] = SuggestionStatus(data.get("status", "new"))
        data["provenance"] = SourceProvenance(data.get("provenance", "other"))
        return cls(**data)


# ============================================================================
# STORE (SQLite)
# ============================================================================

class CapabilitySuggestionStore:
    """SQLite-backed persistence for capability suggestions."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("continuity/capability_suggestions.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS capability_suggestions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    capability_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    suggestion_text TEXT,
                    context TEXT,
                    tags TEXT,
                    priority INTEGER DEFAULT 0,
                    denial_count INTEGER DEFAULT 0,
                    last_denied_at TEXT,
                    archived_at TEXT,
                    assigned_to TEXT,
                    notes TEXT
                )
            """)
            # Index for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON capability_suggestions(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_capability_type ON capability_suggestions(capability_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_provenance ON capability_suggestions(provenance)
            """)
            conn.commit()

    def _now(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def create(self, suggestion: CapabilitySuggestion) -> CapabilitySuggestion:
        """Create a new suggestion. Returns the saved suggestion."""
        now = self._now()
        if suggestion.id is None or suggestion.id == "":
            suggestion.id = f"suggest-{uuid.uuid4().hex[:8]}"

        if suggestion.created_at is None or suggestion.created_at == "":
            suggestion.created_at = now

        suggestion.updated_at = now

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO capability_suggestions (
                    id, title, description, capability_type, status, provenance,
                    created_at, updated_at, suggestion_text, context, tags,
                    priority, denial_count, last_denied_at, archived_at,
                    assigned_to, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion.id,
                suggestion.title,
                suggestion.description,
                suggestion.capability_type.value,
                suggestion.status.value,
                suggestion.provenance.value,
                suggestion.created_at,
                suggestion.updated_at,
                suggestion.suggestion_text,
                suggestion.context,
                suggestion.tags,
                suggestion.priority,
                suggestion.denial_count,
                suggestion.last_denied_at,
                suggestion.archived_at,
                suggestion.assigned_to,
                suggestion.notes,
            ))
            conn.commit()

        return suggestion

    def update(self, suggestion: CapabilitySuggestion) -> CapabilitySuggestion:
        """Update an existing suggestion."""
        suggestion.updated_at = self._now()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE capability_suggestions SET
                    title = ?, description = ?, capability_type = ?, status = ?,
                    provenance = ?, updated_at = ?, suggestion_text = ?,
                    context = ?, tags = ?, priority = ?, denial_count = ?,
                    last_denied_at = ?, archived_at = ?, assigned_to = ?, notes = ?
                WHERE id = ?
            """, (
                suggestion.title,
                suggestion.description,
                suggestion.capability_type.value,
                suggestion.status.value,
                suggestion.provenance.value,
                suggestion.updated_at,
                suggestion.suggestion_text,
                suggestion.context,
                suggestion.tags,
                suggestion.priority,
                suggestion.denial_count,
                suggestion.last_denied_at,
                suggestion.archived_at,
                suggestion.assigned_to,
                suggestion.notes,
                suggestion.id,
            ))
            conn.commit()

        return suggestion

    def get(self, suggestion_id: str) -> Optional[CapabilitySuggestion]:
        """Get a suggestion by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM capability_suggestions WHERE id = ?",
                (suggestion_id,)
            )
            row = cursor.fetchone()
            if row:
                return CapabilitySuggestion.from_dict(dict(zip(
                    ["id", "title", "description", "capability_type", "status",
                     "provenance", "created_at", "updated_at", "suggestion_text",
                     "context", "tags", "priority", "denial_count", "last_denied_at",
                     "archived_at", "assigned_to", "notes"],
                    row
                )))
            return None

    def list_all(
        self,
        include_archived: bool = False,
        status: Optional[SuggestionStatus] = None,
        capability_type: Optional[CapabilityType] = None,
        provenance: Optional[SourceProvenance] = None,
    ) -> List[CapabilitySuggestion]:
        """List suggestions with optional filters."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query
            conditions = []
            params = []

            # Exclude archived unless requested
            if not include_archived:
                conditions.append("archived_at IS NULL")

            # Status filter
            if status:
                conditions.append("status = ?")
                params.append(status.value)

            # Capability type filter
            if capability_type:
                conditions.append("capability_type = ?")
                params.append(capability_type.value)

            # Provenance filter
            if provenance:
                conditions.append("provenance = ?")
                params.append(provenance.value)

            # Build final query
            query = "SELECT * FROM capability_suggestions"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY priority DESC, created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [CapabilitySuggestion.from_dict(dict(zip(
                ["id", "title", "description", "capability_type", "status",
                 "provenance", "created_at", "updated_at", "suggestion_text",
                 "context", "tags", "priority", "denial_count", "last_denied_at",
                 "archived_at", "assigned_to", "notes"],
                row
            ))) for row in rows]

    def search(
        self,
        query: str,
        include_archived: bool = False,
        status: Optional[SuggestionStatus] = None,
        capability_type: Optional[CapabilityType] = None,
    ) -> List[CapabilitySuggestion]:
        """Search suggestions by text in title or description."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build query with LIKE for search
            search_term = f"%{query}%"
            conditions = ["(title LIKE ? OR description LIKE ? OR suggestion_text LIKE ?)"]
            params = [search_term, search_term, search_term]

            # Exclude archived unless requested
            if not include_archived:
                conditions.append("archived_at IS NULL")

            # Status filter
            if status:
                conditions.append("status = ?")
                params.append(status.value)

            # Capability type filter
            if capability_type:
                conditions.append("capability_type = ?")
                params.append(capability_type.value)

            query_sql = "SELECT * FROM capability_suggestions WHERE " + " AND ".join(conditions)
            query_sql += " ORDER BY priority DESC, created_at DESC"

            cursor.execute(query_sql, params)
            rows = cursor.fetchall()

            return [CapabilitySuggestion.from_dict(dict(zip(
                ["id", "title", "description", "capability_type", "status",
                 "provenance", "created_at", "updated_at", "suggestion_text",
                 "context", "tags", "priority", "denial_count", "last_denied_at",
                 "archived_at", "assigned_to", "notes"],
                row
            ))) for row in rows]

    def delete(self, suggestion_id: str) -> bool:
        """Delete a suggestion (soft delete by archiving)."""
        suggestion = self.get(suggestion_id)
        if not suggestion:
            return False

        suggestion.status = SuggestionStatus.ARCHIVED
        suggestion.archived_at = self._now()
        self.update(suggestion)
        return True


# ============================================================================
# CAPABILITY DISCOVERY RADAR
# ============================================================================

class CapabilityDiscoveryRadar:
    """Capability Discovery Radar - manages the full suggestion lifecycle."""

    def __init__(self, store: Optional[CapabilitySuggestionStore] = None):
        self.store = store or CapabilitySuggestionStore()

    # --------------------------------------------------------------------------
    # STATE TRANSITIONS
    # --------------------------------------------------------------------------

    def create_suggestion(
        self,
        title: str,
        description: str,
        capability_type: CapabilityType,
        provenance: SourceProvenance = SourceProvenance.INTERNAL_REVIEW,
        suggestion_text: Optional[str] = None,
        context: Optional[str] = None,
        tags: Optional[str] = None,
        priority: int = 0,
        assigned_to: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CapabilitySuggestion:
        """Create a new suggestion with status 'new'."""
        now = self.store._now()

        suggestion = CapabilitySuggestion(
            id="",
            title=title,
            description=description,
            capability_type=capability_type,
            status=SuggestionStatus.NEW,
            provenance=provenance,
            created_at=now,
            updated_at=now,
            suggestion_text=suggestion_text,
            context=context,
            tags=tags,
            priority=priority,
            denial_count=0,
            last_denied_at=None,
            archived_at=None,
            assigned_to=assigned_to,
            notes=notes,
        )

        return self.store.create(suggestion)

    def suggest(self, suggestion_id: str) -> CapabilitySuggestion:
        """Move suggestion from 'new' to 'suggested'."""
        suggestion = self.store.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion not found: {suggestion_id}")
        if suggestion.status != SuggestionStatus.NEW:
            raise ValueError(f"Can only suggest from 'new' status, got: {suggestion.status}")

        suggestion.status = SuggestionStatus.SUGGESTED
        return self.store.update(suggestion)

    def accept(self, suggestion_id: str, notes: Optional[str] = None) -> CapabilitySuggestion:
        """Accept a suggestion."""
        suggestion = self.store.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion not found: {suggestion_id}")

        suggestion.status = SuggestionStatus.ACCEPTED
        suggestion.notes = notes or suggestion.notes
        return self.store.update(suggestion)

    def deny(self, suggestion_id: str, reason: str = "", suppress_24h: bool = True) -> CapabilitySuggestion:
        """Deny a suggestion, optionally suppressing for 24h."""
        suggestion = self.store.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion not found: {suggestion_id}")

        now = self.store._now()
        suggestion.status = SuggestionStatus.DENIED
        suggestion.denial_count += 1
        suggestion.last_denied_at = now
        suggestion.notes = f"Denied: {reason}\n{ suggestion.notes or '' }".strip()

        if suppress_24h:
            # In a real implementation, we'd store the suppression expiry
            # For now, we just track it in the status logic
            pass

        return self.store.update(suggestion)

    def snooze(self, suggestion_id: str, until: Optional[datetime] = None, reason: str = "") -> CapabilitySuggestion:
        """Snooze a suggestion (temporarily hide)."""
        suggestion = self.store.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion not found: {suggestion_id}")

        suggestion.status = SuggestionStatus.SNOOZED
        suggestion.notes = f"Snoozed: {reason}\n{ suggestion.notes or '' }".strip()
        return self.store.update(suggestion)

    def archive(self, suggestion_id: str, reason: str = "") -> CapabilitySuggestion:
        """Archive a suggestion (permanently hidden, but preserved)."""
        suggestion = self.store.get(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion not found: {suggestion_id}")

        suggestion.status = SuggestionStatus.ARCHIVED
        suggestion.archived_at = self.store._now()
        suggestion.notes = f"Archived: {reason}\n{ suggestion.notes or '' }".strip()
        return self.store.update(suggestion)

    # --------------------------------------------------------------------------
    # LISTING & SEARCH
    # --------------------------------------------------------------------------

    def list(
        self,
        include_archived: bool = False,
        status: Optional[SuggestionStatus] = None,
        capability_type: Optional[CapabilityType] = None,
        provenance: Optional[SourceProvenance] = None,
    ) -> List[CapabilitySuggestion]:
        """List suggestions with filters."""
        return self.store.list_all(
            include_archived=include_archived,
            status=status,
            capability_type=capability_type,
            provenance=provenance,
        )

    def search(self, query: str, include_archived: bool = False) -> List[CapabilitySuggestion]:
        """Search suggestions by text."""
        return self.store.search(query, include_archived=include_archived)

    # --------------------------------------------------------------------------
    # DIAGNOSTICS
    # --------------------------------------------------------------------------

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the capability queue for diagnostics."""
        all_suggestions = self.list(include_archived=True)

        total = len(all_suggestions)
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        by_provenance: Dict[str, int] = {}

        # Count by status
        for s in all_suggestions:
            status = s.status.value
            by_status[status] = by_status.get(status, 0) + 1

            capability_type = s.capability_type.value
            by_type[capability_type] = by_type.get(capability_type, 0) + 1

            provenance = s.provenance.value
            by_provenance[provenance] = by_provenance.get(provenance, 0) + 1

        # Find top ranked pending (not denied/archived)
        pending = [s for s in all_suggestions if s.status in (SuggestionStatus.NEW, SuggestionStatus.SUGGESTED)]
        top_pending = None
        if pending:
            top_pending = max(pending, key=lambda s: s.priority)

        # Count denied in last 24h (active suppression)
        now = datetime.utcnow()
        denied_active = 0
        for s in all_suggestions:
            if s.status == SuggestionStatus.DENIED and s.last_denied_at:
                last_denied = datetime.fromisoformat(s.last_denied_at.replace("Z", "+00:00"))
                # Simple check: if denied within last 24 hours
                if (now - last_denied.replace(tzinfo=None)).total_seconds() < 86400:
                    denied_active += 1

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "by_provenance": by_provenance,
            "pending_count": len(pending),
            "denied_active_count": denied_active,
            "top_pending_suggestion": top_pending.to_dict() if top_pending else None,
        }


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python capability_suggestion.py <command> [args]")
        print("Commands:")
        print("  create <title> <description> <type>")
        print("  suggest <id>")
        print("  accept <id> [notes]")
        print("  deny <id> [reason]")
        print("  snooze <id> [reason]")
        print("  archive <id> [reason]")
        print("  list [--include-archived] [--status <s>] [--type <t>]")
        print("  search <query>")
        print("  summary")
        print("  types")
        print("  provenances")
        print("  statuses")
        print("Types: ingestion, analysis, visualization, automation, integration, storage, security, other")
        print("Provenances: internal_review, reddit, github, email, direct_submission, other")
        print("Statuses: new, suggested, accepted, denied, snoozed, archived")
        sys.exit(1)

    command = sys.argv[1]
    radar = CapabilityDiscoveryRadar()

    if command == "create":
        # Simple CLI create - needs at least title, description, type
        print("Create command requires arguments: --title, --description, --type")
        print("Usage: python capability_suggestion.py create <title> <description> <type>")
        print("  Types: ingestion, analysis, visualization, automation, integration, storage, security, other")
        sys.exit(1)

    elif command == "suggest":
        if len(sys.argv) < 3:
            print("Usage: python capability_suggestion.py suggest <id>")
            sys.exit(1)
        suggestion = radar.suggest(sys.argv[2])
        print(json.dumps(suggestion.to_dict(), indent=2))

    elif command == "accept":
        if len(sys.argv) < 3:
            print("Usage: python capability_suggestion.py accept <id> [notes]")
            sys.exit(1)
        notes = sys.argv[3] if len(sys.argv) > 3 else None
        suggestion = radar.accept(sys.argv[2], notes=notes)
        print(json.dumps(suggestion.to_dict(), indent=2))

    elif command == "deny":
        if len(sys.argv) < 3:
            print("Usage: python capability_suggestion.py deny <id> [reason]")
            sys.exit(1)
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        suggestion = radar.deny(sys.argv[2], reason=reason)
        print(json.dumps(suggestion.to_dict(), indent=2))

    elif command == "snooze":
        if len(sys.argv) < 3:
            print("Usage: python capability_suggestion.py snooze <id> [reason]")
            sys.exit(1)
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        suggestion = radar.snooze(sys.argv[2], reason=reason)
        print(json.dumps(suggestion.to_dict(), indent=2))

    elif command == "archive":
        if len(sys.argv) < 3:
            print("Usage: python capability_suggestion.py archive <id> [reason]")
            sys.exit(1)
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        suggestion = radar.archive(sys.argv[2], reason=reason)
        print(json.dumps(suggestion.to_dict(), indent=2))

    elif command == "list":
        include_archived = "--include-archived" in sys.argv
        status = None
        capability_type = None

        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--status" and i + 1 < len(args):
                status = SuggestionStatus(args[i + 1])
                i += 2
            elif args[i] == "--type" and i + 1 < len(args):
                capability_type = CapabilityType(args[i + 1])
                i += 2
            else:
                i += 1

        suggestions = radar.list(
            include_archived=include_archived,
            status=status,
            capability_type=capability_type,
        )
        print(json.dumps([s.to_dict() for s in suggestions], indent=2))

    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python capability_suggestion.py search <query>")
            sys.exit(1)
        query = sys.argv[2]
        suggestions = radar.search(query, include_archived=False)
        print(json.dumps([s.to_dict() for s in suggestions], indent=2))

    elif command == "summary":
        summary = radar.get_summary()
        print(json.dumps(summary, indent=2))

    elif command == "types":
        print(json.dumps([t.value for t in CapabilityType], indent=2))

    elif command == "provenances":
        print(json.dumps([p.value for p in SourceProvenance], indent=2))

    elif command == "statuses":
        print(json.dumps([s.value for s in SuggestionStatus], indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
