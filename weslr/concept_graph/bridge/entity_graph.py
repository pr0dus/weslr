"""Entity Graph Bridge for Concept Graph

Maps existing entity_graph data into Concept Graph nodes and links.

Architecture:
  - EntityGraphBridge - Maps entities to concepts, relationships to links
  - Evidence mapping from entity provenance to Concept Evidence
  - Backward compatibility - does not modify existing entity_graph

Integration Points:
  1. Import entities → concepts
  2. Import relationships → typed links
  3. Map evidence sources (messages, sessions, etc.) to evidence categories
  4. Preserve ghost status (temporary concepts)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import existing entity_graph module (from workspace root)
import sys
import os
workspace_root = str(Path(__file__).resolve().parent.parent.parent)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from entity_graph import EntityGraph, Entity, Relationship, ENTITY_GRAPH_PATH


class EntityGraphBridge:
    """Bridge from entity_graph to concept_graph.
    
    Reads existing entity_graph data and maps it to Concept Graph structures.
    Does NOT modify the original entity_graph file.
    """
    
    # Entity type → concept type mapping
    ENTITY_TYPE_MAP = {
        "person": "concept",
        "organization": "concept",
        "concept": "concept",
        "event": "concept",
        "object": "entity",
        "location": "entity",
        "project": "concept",
        "principle": "concept",
        "question": "concept",
        "lesson": "concept",
        "semantic-memory": "concept",
        "research": "concept",
        "agent": "concept",
        "memory": "concept",
        "tool": "entity",
    }
    
    # Relationship type → link type mapping
    RELATIONSHIP_TYPE_MAP = {
        "related_to": "related_to",
        "works_with": "related_to",
        "mentions": "related_to",
        "affects": "causes",
        "causes": "causes",
        "depends_on": "depends_on",
        "similar_to": "similar_to",
        "opposes": "opposes",
        "part_of": "part_of",
        "has_part": "has_part",
        "collaboration": "related_to",
        "communication": "related_to",
        "exchange": "related_to",
    }
    
    def __init__(self, workspace_dir: str = None):
        """Initialize bridge with optional workspace directory."""
        self.workspace_dir = workspace_dir or str(
            Path(__file__).resolve().parent.parent
        )
        self.entity_graph_path = ENTITY_GRAPH_PATH
        self.bridge_metadata_path = Path(self.workspace_dir) / "weslr" / "concept_graph" / "bridge_metadata.json"
        
        # Track mapping for reversibility
        self.mapping: Dict[str, Dict[str, str]] = {
            "entity_id": {},  # entity_graph_id → concept_graph_id
            "rel_id": {},     # relationship_id → link_id
        }
    
    def _load_entity_graph(self) -> Optional[EntityGraph]:
        """Load entity graph from disk."""
        if not self.entity_graph_path.exists():
            return None
        return EntityGraph.load(self.entity_graph_path)
    
    def _map_entity_type(self, entity_type: str) -> str:
        """Map entity type to concept type."""
        return self.ENTITY_TYPE_MAP.get(entity_type, "concept")
    
    def _map_relationship_type(self, rel_type: str) -> str:
        """Map relationship type to link type."""
        return self.RELATIONSHIP_TYPE_MAP.get(rel_type, "related_to")
    
    def _build_evidence_from_provenance(
        self,
        provenance: Dict[str, Any],
        source_content: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Build evidence dict from entity provenance data."""
        if not provenance or not provenance.get("source"):
            return None
        
        source_id = provenance.get("source", "unknown")
        
        # Determine source type
        source_type = "message" if "message" in source_id.lower() else "entity_graph"
        if "session" in source_id.lower():
            source_type = "session"
        
        return {
            "source_id": source_id,
            "source_type": source_type,
            "content": source_content or str(provenance),
            "confidence": provenance.get("confidence", 0.5),
            "timestamp": provenance.get("timestamp", int(time.time())),
            "category": "source-backed" if provenance.get("traceable", False) else "inferred",
            "traceable": provenance.get("traceable", False),
            "source_file": "entity_graph.json",
        }
    
    def import_entities_to_concepts(self, store: "ConceptGraphStore") -> Dict[str, int]:
        """Import all entities from entity_graph to concept_graph.
        
        Args:
            store: ConceptGraphStore instance to save concepts to
        
        Returns:
            Import statistics (entities_imported, concepts_saved)
        """
        from ..models import Concept, Evidence
        
        entity_graph = self._load_entity_graph()
        if not entity_graph:
            return {"entities_found": 0, "concepts_imported": 0}
        
        imported = 0
        for entity in entity_graph.entities.values():
            concept = Concept(
                id=entity.id,
                name=entity.name,
                type=self._map_entity_type(entity.type),
                description=f"Entity graph entity: {entity.type}",
                aliases=entity.aliases or [],
                tags=[entity.type] if entity.type else [],
                confidence=entity.confidence,
                created_at=entity.created_at,
                last_updated=entity.last_seen,
                is_temporary=entity.is_ghost,
                is_ghost=entity.is_ghost,
                links=[],
                evidence=[],
                metadata=entity.metadata or {},
            )
            
            # Add evidence from entity provenance
            for ev in entity.evidence:
                evidence = Evidence(
                    source_id=ev.get("source", "unknown"),
                    source_type="message" if "message" in ev.get("source", "") else "entity_graph",
                    content=ev.get("content", ""),
                    confidence=min(1.0, entity.confidence + ev.get("confidence_boost", 0)),
                    timestamp=ev.get("timestamp", int(time.time())),
                    category="source-backed" if ev.get("traceable", False) else "inferred",
                    traceable=ev.get("traceable", True),
                )
                concept.add_evidence(evidence)
            
            store.save_concept(concept)
            imported += 1
            
            # Track mapping for reversibility
            self.mapping["entity_id"][entity.id] = concept.id
        
        # Save bridge metadata
        self._save_bridge_metadata()
        
        return {
            "entities_found": len(entity_graph.entities),
            "concepts_imported": imported,
        }
    
    def import_relationships_to_links(
        self,
        store: "ConceptGraphStore",
        entity_graph: EntityGraph = None,
    ) -> Dict[str, int]:
        """Import all relationships as typed links.
        
        Args:
            store: ConceptGraphStore instance to save links to
            entity_graph: Optional pre-loaded entity_graph
        
        Returns:
            Import statistics (relationships_imported, links_saved)
        """
        from ..models import Link, Evidence
        
        if entity_graph is None:
            entity_graph = self._load_entity_graph()
            if not entity_graph:
                return {"relationships_found": 0, "links_imported": 0}
        
        imported = 0
        for rel in entity_graph.relationships.values():
            # Build evidence from provenance
            evidence_data = self._build_evidence_from_provenance(
                rel.provenance,
                source_content=f"Relationship: {rel.type} between {rel.source_id} and {rel.target_id}",
            )
            
            evidence_list = []
            if evidence_data:
                evidence = Evidence(
                    source_id=evidence_data["source_id"],
                    source_type=evidence_data["source_type"],
                    content=evidence_data["content"],
                    confidence=evidence_data["confidence"],
                    timestamp=evidence_data["timestamp"],
                    category=evidence_data["category"],
                    traceable=evidence_data.get("traceable", True),
                )
                evidence_list = [evidence]
            
            link = Link(
                source_id=rel.source_id,
                target_id=rel.target_id,
                link_type=self._map_relationship_type(rel.type),
                confidence=rel.strength,
                reason=f"Entity relationship: {rel.type}",
                evidence=evidence_list,
                created_at=rel.created_at,
                updated_at=rel.updated_at,
                is_stale=False,
            )
            
            store.save_link(link)
            imported += 1
            
            # Track mapping for reversibility
            self.mapping["rel_id"][rel.id] = f"{link.source_id}-{link.target_id}-{link.link_type}"
        
        # Save bridge metadata
        self._save_bridge_metadata()
        
        return {
            "relationships_found": len(entity_graph.relationships),
            "links_imported": imported,
        }
    
    def import_all(self, store: "ConceptGraphStore") -> Dict[str, int]:
        """Import all entities and relationships.
        
        Args:
            store: ConceptGraphStore instance
        
        Returns:
            Combined statistics
        """
        entities_result = self.import_entities_to_concepts(store)
        relationships_result = self.import_relationships_to_links(store)
        
        return {
            "entities": entities_result,
            "relationships": relationships_result,
        }
    
    def _save_bridge_metadata(self) -> None:
        """Save bridge mapping metadata for reversibility."""
        metadata = {
            "last_run": int(time.time()),
            "entity_mapping": self.mapping["entity_id"],
            "rel_mapping": self.mapping["rel_id"],
        }
        self.bridge_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.bridge_metadata_path.write_text(json.dumps(metadata, indent=2))
    
    def get_import_mapping(self) -> Dict[str, Dict[str, str]]:
        """Get current mapping from entity_graph to concept_graph."""
        return self.mapping
    
    def clear_mapping(self) -> None:
        """Clear mapping (for fresh import)."""
        self.mapping = {
            "entity_id": {},
            "rel_id": {},
        }


def bridge_entity_graph_to_concepts(store: "ConceptGraphStore") -> Dict[str, int]:
    """Convenience function to bridge entity_graph to concept_graph.
    
    Args:
        store: ConceptGraphStore instance to save to
    
    Returns:
        Import statistics
    """
    bridge = EntityGraphBridge()
    return bridge.import_all(store)
