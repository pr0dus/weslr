"""Capability Discovery Radar - API Layer.

Provides CRUD operations and filtering:
- create_suggestion
- update_status
- list_suggestions
- search_suggestions
- deny_suggestion
- accept_suggestion
- archive_suggestion
"""

from __future__ import annotations

import time
from typing import List, Optional

from .data_model import (
    CapabilitySuggestion,
    CapabilityType,
    SuggestionStatus,
    SourceProvenance,
)
from .store import CapabilityStore, get_store


# ============== Creation ==============

def create_suggestion(
    title: str,
    capability_type: CapabilityType,
    summary: str,
    why_it_matters: str,
    improvement_area: str,
    provenance: List[SourceProvenance],
    confidence: float = 0.5,
    rank_score: float = 0.0,
    tags: List[str] = None,
    mentions_count: int = 1,
    growth_trend: str = "stable",
    source_diversity: int = 1,
    architectural_fit: str = "medium",
    github_activity: dict = None,
    science_relevance: str = None,
    store: CapabilityStore = None,
) -> CapabilitySuggestion:
    """Create a new capability suggestion."""
    store = store or get_store()
    
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    suggestion = CapabilitySuggestion(
        title=title,
        capability_type=capability_type,
        summary=summary,
        why_it_matters=why_it_matters,
        improvement_area=improvement_area,
        provenance=provenance or [],
        confidence=confidence,
        rank_score=rank_score,
        status=SuggestionStatus.SUGGESTED if confidence >= 0.6 else SuggestionStatus.NEW,
        created_at=now,
        last_seen_at=now,
        first_seen_at=now,
        tags=tags or [],
        mentions_count=mentions_count,
        growth_trend=growth_trend,
        source_diversity=source_diversity,
        architectural_fit=architectural_fit,
        github_activity=github_activity,
        science_relevance=science_relevance,
    )
    
    store.create_suggestion(suggestion)
    return suggestion


# ============== Status Updates ==============

def update_status(
    suggestion_id: str,
    new_status: SuggestionStatus,
    store: CapabilityStore = None,
) -> CapabilitySuggestion:
    """Update the status of a suggestion."""
    store = store or get_store()
    
    suggestion = store.get_suggestion(suggestion_id)
    if not suggestion:
        raise ValueError(f"Suggestion not found: {suggestion_id}")
    
    suggestion.transition_to(new_status)
    store.update_suggestion(suggestion)
    
    # Record decision
    store.record_decision(suggestion_id, f"status:{new_status.value}")
    
    return suggestion


def accept_suggestion(
    suggestion_id: str,
    store: CapabilityStore = None,
) -> CapabilitySuggestion:
    """Accept a suggestion for implementation."""
    return update_status(suggestion_id, SuggestionStatus.ACCEPTED, store)


def deny_suggestion(
    suggestion_id: str,
    hours: int = 24,
    store: CapabilityStore = None,
) -> CapabilitySuggestion:
    """Deny a suggestion for N hours (default 24h)."""
    store = store or get_store()
    
    suggestion = store.get_suggestion(suggestion_id)
    if not suggestion:
        raise ValueError(f"Suggestion not found: {suggestion_id}")
    
    # Calculate deny_until timestamp
    deny_until = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ",
        time.gmtime(time.time() + hours * 3600)
    )
    suggestion.denied_until = deny_until
    suggestion.transition_to(SuggestionStatus.DENIED)
    
    store.update_suggestion(suggestion)
    store.record_decision(suggestion_id, f"deny:{hours}h")
    
    return suggestion


def archive_suggestion(
    suggestion_id: str,
    store: CapabilityStore = None,
) -> CapabilitySuggestion:
    """Archive a suggestion (Irrelevant)."""
    return update_status(suggestion_id, SuggestionStatus.ARCHIVED, store)


# ============== List & Search ==============

def list_suggestions(
    status: SuggestionStatus = None,
    capability_type: CapabilityType = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "last_seen_at",
    sort_desc: bool = True,
    store: CapabilityStore = None,
) -> List[CapabilitySuggestion]:
    """List suggestions with optional filters."""
    store = store or get_store()
    return store.list_suggestions(
        status=status,
        capability_type=capability_type,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


def search_suggestions(
    query: str,
    limit: int = 50,
    store: CapabilityStore = None,
) -> List[CapabilitySuggestion]:
    """Search suggestions using FTS5."""
    store = store or get_store()
    return store.search_suggestions(query, limit)


def get_suggestion(
    suggestion_id: str,
    store: CapabilityStore = None,
) -> Optional[CapabilitySuggestion]:
    """Get a single suggestion by ID."""
    store = store or get_store()
    return store.get_suggestion(suggestion_id)


def count_suggestions(
    status: SuggestionStatus = None,
    store: CapabilityStore = None,
) -> int:
    """Count suggestions with optional status filter."""
    store = store or get_store()
    return store.count_suggestions(status)


def delete_suggestion(
    suggestion_id: str,
    store: CapabilityStore = None,
) -> bool:
    """Delete a suggestion (for cleanup)."""
    store = store or get_store()
    return store.delete_suggestion(suggestion_id)


def get_decisions(
    suggestion_id: str,
    store: CapabilityStore = None,
) -> List[dict]:
    """Get decision history for a suggestion."""
    store = store or get_store()
    return store.get_decisions(suggestion_id)
