"""Capability Discovery Radar - Phase 1 Core, Phase 2 Ingestion.

Subsystems:
- data_model: CapabilitySuggestion type and validation
- store: Persistence layer (SQLite)
- api: CRUD operations and filtering
- ingestion: Signal ingestion + normalization pipeline (Reddit, GitHub, manual)
- seeds: Seeded source pack for controlled discovery
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
from .ingestion import (
    SourceSignal,
    SourceKind,
    SignalStatus,
    NormalizationPipeline,
    CapabilityIngestionPipeline,
)
from .seeds import (
    SeedSource,
    SeedKind,
    SeedStatus,
    get_seed_pack,
    get_enabled_seeds,
    get_seeds_by_kind,
    get_seeds_by_category,
)
from .seed_ingestion import (
    SeedIngestionPipeline,
)
from .review import (
    OperatorReviewLoop,
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
    "SourceSignal",
    "SourceKind",
    "SignalStatus",
    "NormalizationPipeline",
    "CapabilityIngestionPipeline",
    "SeedSource",
    "SeedKind",
    "SeedStatus",
    "get_seed_pack",
    "get_enabled_seeds",
    "get_seeds_by_kind",
    "get_seeds_by_category",
    "SeedIngestionPipeline",
    "OperatorReviewLoop",
]
