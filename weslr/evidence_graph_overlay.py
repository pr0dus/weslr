"""
WESLR Evidence Graph Overlay V1 — Read-Only Overlay

Attaches evidence workspace references to graph context WITHOUT:
- Writing to any file
- Modifying graph state
- Promoting evidence to structured truth
- Creating proposals
- LLM usage
- Persistence

This is an overlay only — graph_context is passed through unchanged.

Verdict label: WESLR_EVIDENCE_GRAPH_OVERLAY_V1_DEFINED
"""

from __future__ import annotations

import os
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_LINKS_DEFAULT = 5

# Evidence source types
SOURCE_EXTERNAL = "external"
SOURCE_WORKSPACE = "workspace"

# Safety note embedded in every overlay entry
SAFETY_NOTE = "not part of structured truth"


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def attach_evidence_overlay(
    graph_context: dict,
    evidence_items: list[dict],
    max_links: int = MAX_LINKS_DEFAULT,
) -> dict:
    """
    Attach evidence workspace references to a graph context (overlay only).

    This function does NOT modify the graph_context in place — it returns
    a copy with the evidence_overlay added as a new key.

    Parameters
    ----------
    graph_context : dict
        The graph_context from a GraphContextBundle or context selector.
        Must contain a "root" key (dict with "id") and optionally "connections".
        Passed through unchanged if no matches found.
    evidence_items : list[dict]
        Evidence items from the Evidence Workspace.
        Each item should have: "entity_id", "summary", "confidence", "source"
    max_links : int
        Maximum number of overlay links to attach. Hard-capped at 5.

    Returns
    -------
    dict
        Copy of graph_context with "evidence_overlay" key added:
        {
            "graph_context": <original passed through>,
            "evidence_overlay": [
                {
                    "entity_id": str,
                    "evidence_summary": str,
                    "confidence": float,
                    "source_type": "external" | "workspace",
                    "note": "not part of structured truth"
                },
                ...
            ]
        }

    Matching rules:
    - entity_id exact match preferred
    - normalized topic match as fallback
    - max max_links entries returned
    - no matches → empty evidence_overlay list

    Safety rules enforced:
    - Every overlay entry includes SAFETY_NOTE
    - graph_context is never mutated
    - no writes, no persistence
    """
    # Hard cap on links
    max_links = min(max_links, MAX_LINKS_DEFAULT)

    # Normalize graph entity IDs
    graph_entity_ids = _extract_graph_entity_ids(graph_context)

    overlay_entries: list[dict] = []
    matched_ids: set[str] = set()

    for item in evidence_items:
        if len(overlay_entries) >= max_links:
            break

        if not isinstance(item, dict):
            continue

        entity_id = _normalize_id(item.get("entity_id", ""))
        if not entity_id:
            continue

        # Skip if already matched (no duplicates)
        if entity_id in matched_ids:
            continue

        # Check entity_id match
        if entity_id in graph_entity_ids:
            entry = _build_overlay_entry(item, entity_id)
            overlay_entries.append(entry)
            matched_ids.add(entity_id)
            continue

        # Check normalized topic match
        topic_match = _find_topic_match(item, graph_entity_ids, matched_ids)
        if topic_match:
            entry = _build_overlay_entry(item, topic_match)
            overlay_entries.append(entry)
            matched_ids.add(topic_match)
            continue

    # Build result — graph_context passed through unchanged
    result = {
        "graph_context": graph_context,   # passed through as-is
        "evidence_overlay": overlay_entries,
    }

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_graph_entity_ids(graph_context: dict) -> set[str]:
    """Extract all entity IDs from graph_context."""
    ids: set[str] = set()

    root = graph_context.get("root", {})
    if isinstance(root, dict) and root.get("id"):
        ids.add(_normalize_id(root["id"]))

    connections = graph_context.get("connections", [])
    if isinstance(connections, list):
        for conn in connections:
            if isinstance(conn, dict) and conn.get("id"):
                ids.add(_normalize_id(conn["id"]))

    return ids


def _normalize_id(value: Any) -> str:
    """Normalize an ID to lowercase string for comparison."""
    if value is None:
        return ""
    return str(value).strip().lower()


def _build_overlay_entry(item: dict, matched_entity_id: str) -> dict:
    """
    Build a single overlay entry from an evidence item.
    Every entry is guaranteed to include SAFETY_NOTE.
    """
    # Determine source_type
    source_raw = item.get("source", "")
    if source_raw == "external":
        source_type = SOURCE_EXTERNAL
    else:
        source_type = SOURCE_WORKSPACE

    # Build entry
    entry = {
        "entity_id": matched_entity_id,
        "evidence_summary": str(item.get("summary", item.get("evidence_summary", ""))),
        "confidence": _clamp_confidence(item.get("confidence", 0.0)),
        "source_type": source_type,
        "note": SAFETY_NOTE,
    }

    return entry


def _clamp_confidence(value: Any) -> float:
    """Ensure confidence is a float in [0.0, 1.0]."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        f = 0.0
    return max(0.0, min(1.0, f))


def _find_topic_match(
    item: dict,
    graph_entity_ids: set[str],
    already_matched: set[str],
) -> str | None:
    """
    Try to match an evidence item to a graph entity via normalized topic.
    Returns the matched entity_id or None.
    """
    item_topic = _normalize_topic(item)
    if not item_topic:
        return None

    for entity_id in graph_entity_ids:
        if entity_id in already_matched:
            continue
        if item_topic == entity_id or item_topic in entity_id or entity_id in item_topic:
            return entity_id

    return None


def _normalize_topic(item: dict) -> str:
    """Extract and normalize a topic string from an evidence item."""
    topic = item.get("topic", "")
    if not topic:
        summary = item.get("summary", item.get("evidence_summary", ""))
        # Use first significant word as topic approximation
        if summary:
            words = str(summary).split()
            topic = words[0] if words else ""
    return _normalize_id(topic)