"""Capability Discovery Radar - Operator Review Loop.

Minimal operator-facing review path so we can:
- list latest ingested signals
- list top pending suggestions
- inspect provenance
- accept / deny / snooze from the existing suggestion system
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

try:
    from .data_model import CapabilitySuggestion, SuggestionStatus, SourceProvenance
    from .store import CapabilityStore, get_store
    from .api import (
        accept_suggestion,
        deny_suggestion,
        update_status,
        list_suggestions as api_list_suggestions,
    )
except ImportError:
    from data_model import CapabilitySuggestion, SuggestionStatus, SourceProvenance
    from store import CapabilityStore, get_store
    from api import (
        accept_suggestion,
        deny_suggestion,
        update_status,
        list_suggestions as api_list_suggestions,
    )


class OperatorReviewLoop:
    """Operator review loop for capability suggestions."""

    def __init__(self, store: Optional[CapabilityStore] = None):
        self.store = store or get_store()

    def list_latest_signals(self, limit: int = 10) -> List[CapabilitySuggestion]:
        """List latest ingested signals."""
        return self.store.list_suggestions(
            limit=limit,
            sort_by="created_at",
            sort_desc=True,
        )

    def list_pending(self, limit: int = 20) -> List[CapabilitySuggestion]:
        """List top pending suggestions (not denied/archived)."""
        return self.store.list_suggestions(
            status=SuggestionStatus.NEW,
            limit=limit,
            sort_by="rank_score",
            sort_desc=True,
        )

    def list_by_provenance(
        self,
        provenance_type: str,
        limit: int = 20,
    ) -> List[CapabilitySuggestion]:
        """List suggestions by provenance type."""
        # Filter by checking provenance.signal_type
        suggestions = self.store.list_suggestions(limit=100)
        result = []
        for s in suggestions:
            for p in s.provenance:
                if p.signal_type == provenance_type:
                    result.append(s)
                    break
        # Sort by rank_score
        result.sort(key=lambda x: x.rank_score, reverse=True)
        return result[:limit]

    def get_suggestion_with_provenance(self, suggestion_id: str) -> Optional[Dict[str, Any]]:
        """Get a suggestion with full provenance details."""
        suggestion = self.store.get_suggestion(suggestion_id)
        if not suggestion:
            return None

        return {
            "id": suggestion.id,
            "title": suggestion.title,
            "status": suggestion.status.value,
            "capability_type": suggestion.capability_type.value,
            "summary": suggestion.summary,
            "why_it_matters": suggestion.why_it_matters,
            "improvement_area": suggestion.improvement_area,
            "confidence": suggestion.confidence,
            "rank_score": suggestion.rank_score,
            "created_at": suggestion.created_at,
            "provenance": [
                {
                    "url": p.url,
                    "title": p.title,
                    "snippet": p.snippet,
                    "relevance_score": p.relevance_score,
                    "signal_type": p.signal_type,
                    "timestamp": p.timestamp,
                }
                for p in suggestion.provenance
            ],
            "tags": suggestion.tags,
        }

    def accept_suggestion(self, suggestion_id: str, notes: Optional[str] = None) -> CapabilitySuggestion:
        """Accept a suggestion."""
        return accept_suggestion(suggestion_id, store=self.store)

    def deny_suggestion(
        self,
        suggestion_id: str,
        reason: str = "",
        hours: int = 24,
    ) -> CapabilitySuggestion:
        """Deny a suggestion."""
        return deny_suggestion(suggestion_id, hours=hours, store=self.store)

    def snooze_suggestion(
        self,
        suggestion_id: str,
        reason: str = "",
        hours: int = 1,
    ) -> CapabilitySuggestion:
        """Snooze a suggestion."""
        return update_status(
            suggestion_id,
            SuggestionStatus.SNOOZED,
            store=self.store,
        )

    def archive_suggestion(
        self,
        suggestion_id: str,
        reason: str = "",
    ) -> CapabilitySuggestion:
        """Archive a suggestion."""
        return update_status(
            suggestion_id,
            SuggestionStatus.ARCHIVED,
            store=self.store,
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state."""
        suggestions = self.store.list_suggestions(limit=1000)

        total = len(suggestions)
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        by_provenance: Dict[str, int] = {}

        for s in suggestions:
            status = s.status.value
            by_status[status] = by_status.get(status, 0) + 1

            capability_type = s.capability_type.value
            by_type[capability_type] = by_type.get(capability_type, 0) + 1

            for p in s.provenance:
                provenance = p.signal_type
                by_provenance[provenance] = by_provenance.get(provenance, 0) + 1

        # Pending count
        pending = [s for s in suggestions if s.status in (SuggestionStatus.NEW, SuggestionStatus.SUGGESTED)]
        top_pending = None
        if pending:
            top_pending = max(pending, key=lambda s: s.rank_score)

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "by_provenance": by_provenance,
            "pending_count": len(pending),
            "top_pending": top_pending.to_dict() if top_pending else None,
        }


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI interface for operator review loop."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python capability_discovery/review.py <command> [args]")
        print("Commands:")
        print("  list-latest [n]        - List latest ingested signals (default: 10)")
        print("  list-pending [n]       - List pending suggestions (default: 20)")
        print("  by-provenance <type>   - List by provenance (reddit, github, manual)")
        print("  show <id>              - Show suggestion with provenance")
        print("  accept <id> [notes]    - Accept suggestion")
        print("  deny <id> [reason]     - Deny suggestion")
        print("  snooze <id> [reason]   - Snooze suggestion")
        print("  archive <id> [reason]  - Archive suggestion")
        print("  summary                - Show overall summary")
        sys.exit(1)

    command = sys.argv[1]
    review = OperatorReviewLoop()

    if command == "list-latest":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        suggestions = review.list_latest_signals(limit)
        print(f"Latest {len(suggestions)} signals:")
        for s in suggestions:
            print(f"  [{s.status.value}] {s.id}: {s.title[:50]}...")

    elif command == "list-pending":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        suggestions = review.list_pending(limit)
        print(f"Pending {len(suggestions)} suggestions:")
        for s in suggestions:
            print(f"  [{s.status.value}] {s.id}: {s.title[:50]}... (score={s.rank_score})")

    elif command == "by-provenance":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/review.py by-provenance <type>")
            sys.exit(1)
        provenance_type = sys.argv[2]
        suggestions = review.list_by_provenance(provenance_type)
        print(f"Suggestions from {provenance_type}:")
        for s in suggestions:
            print(f"  [{s.status.value}] {s.id}: {s.title[:50]}...")

    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/review.py show <id>")
            sys.exit(1)
        suggestion_id = sys.argv[2]
        details = review.get_suggestion_with_provenance(suggestion_id)
        if not details:
            print(f"Suggestion not found: {suggestion_id}")
            sys.exit(1)
        print(f"ID: {details['id']}")
        print(f"Title: {details['title']}")
        print(f"Status: {details['status']}")
        print(f"Type: {details['capability_type']}")
        print(f"Summary: {details['summary']}")
        print(f"Why it matters: {details['why_it_matters']}")
        print(f"Improvement area: {details['improvement_area']}")
        print(f"Confidence: {details['confidence']}")
        print(f"Rank score: {details['rank_score']}")
        print(f"Provenance: {len(details['provenance'])} source(s)")
        for p in details['provenance']:
            print(f"  - {p['signal_type']}: {p['title'][:40]}...")

    elif command == "accept":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/review.py accept <id> [notes]")
            sys.exit(1)
        suggestion_id = sys.argv[2]
        notes = sys.argv[3] if len(sys.argv) > 3 else None
        suggestion = review.accept_suggestion(suggestion_id, notes=notes)
        print(f"Accepted: {suggestion.id}")

    elif command == "deny":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/review.py deny <id> [reason]")
            sys.exit(1)
        suggestion_id = sys.argv[2]
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        suggestion = review.deny_suggestion(suggestion_id, reason=reason)
        print(f"Denied: {suggestion.id}")

    elif command == "snooze":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/review.py snooze <id> [reason]")
            sys.exit(1)
        suggestion_id = sys.argv[2]
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        suggestion = review.snooze_suggestion(suggestion_id, reason=reason)
        print(f"Snoozed: {suggestion.id}")

    elif command == "archive":
        if len(sys.argv) < 3:
            print("Usage: python capability_discovery/review.py archive <id> [reason]")
            sys.exit(1)
        suggestion_id = sys.argv[2]
        reason = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        suggestion = review.archive_suggestion(suggestion_id, reason=reason)
        print(f"Archived: {suggestion.id}")

    elif command == "summary":
        summary = review.get_summary()
        print(f"Total suggestions: {summary['total']}")
        print(f"By status: {summary['by_status']}")
        print(f"By type: {summary['by_type']}")
        print(f"By provenance: {summary['by_provenance']}")
        print(f"Pending count: {summary['pending_count']}")
        if summary['top_pending']:
            tp = summary['top_pending']
            print(f"Top pending: {tp['title'][:40]}... (score={tp['rank_score']})")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
