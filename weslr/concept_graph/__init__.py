"""Concept Graph Core (v1)

Weslr native graph layer for linked knowledge.

Architecture:
  graph model   — Concept, Link, Evidence classes
  graph store   — Persistence, indexing, session handling
  graph semantics — Link types, evidence categories, update rules
  graph query   — Traversal, path finding, centrality
  graph views   — Obsidian export, JSON export

Features:
  - Typed concept links with provenance
  - Backlinks derived (not primary stored)
  - Evidence categories: source-backed, inferred, model-asserted, cached, user-provided
  - Graph update policy: merge rules, contradiction handling, staleness
  - Obsidian export as view layer (not core storage)

This module is additive and reversible.
"""

__version__ = "1.0.0"

from .models import Concept, Link, Evidence, Backlink
from .semantics import EvidenceCategory, get_link_types, get_evidence_categories

__all__ = [
    "Concept",
    "Link",
    "Evidence",
    "Backlink",
    "EvidenceCategory",
    "get_link_types",
    "get_evidence_categories",
]
