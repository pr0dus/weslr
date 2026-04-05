"""Capability Discovery Radar - Phase 1 Core.

Subsystems:
- data_model: CapabilitySuggestion type and validation
- store: Persistence layer (SQLite)
- api: CRUD operations and filtering
"""

from .data_model import (
    CapabilitySuggestion,
    CapabilityType,
    SuggestionStatus,
    SourceProvenance,
)
from .store import CapabilityStore, get_store
from .api import (
    create_suggestion,
    update_status,
    list_suggestions,
    search_suggestions,
    deny_suggestion,
    accept_suggestion,
    archive_suggestion,
)

__all__ = [
    "CapabilitySuggestion",
    "CapabilityType",
    "SuggestionStatus",
    "SourceProvenance",
    "CapabilityStore",
    "get_store",
    "create_suggestion",
    "update_status",
    "list_suggestions",
    "search_suggestions",
    "deny_suggestion",
    "accept_suggestion",
    "archive_suggestion",
]
