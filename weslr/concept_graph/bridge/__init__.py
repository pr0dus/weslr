"""Concept Graph Bridge Module

Bridges from external data sources into the Concept Graph:
- entity_graph bridge: Maps entities to concepts, relationships to links
- Evidence bridge: Connects evidence-producing paths to graph nodes
- Runtime bridge: Writes runtime events to Concept Graph

All bridges are:
- Additive only (no destructive operations)
- Reversible (track mappings)
- Non-invasive (don't modify source data)
"""

from .entity_graph import EntityGraphBridge, bridge_entity_graph_to_concepts
from .evidence import EvidenceBridge, create_evidence_from_weather, create_evidence_from_message
from .runtime import (
    RuntimeWriteBridge,
    write_weather_result,
    write_time_result,
    write_unsupported_outcome,
    write_bounded_reflection,
)

__all__ = [
    "EntityGraphBridge",
    "bridge_entity_graph_to_concepts",
    "EvidenceBridge",
    "create_evidence_from_weather",
    "create_evidence_from_message",
    "RuntimeWriteBridge",
    "write_weather_result",
    "write_time_result",
    "write_unsupported_outcome",
    "write_bounded_reflection",
]
