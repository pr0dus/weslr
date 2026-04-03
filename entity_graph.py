"""Entity graph storage layer for Weslr.

Implements entity intelligence: persistent entities with relationships, 
traceable provenance, ghost-to-authoritative promotion, and validation.

Features:
- Full type hints and validation
- Traceable provenance with source tracking
- Ghost entities that promote to authoritative
- JSON persistence with versioning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import uuid
import time


# Base directory for entity graph storage
BASE_DIR = Path(__file__).resolve().parent
ENTITY_GRAPH_PATH = BASE_DIR / "entity_graph.json"

# Entity type whitelist
VALID_ENTITY_TYPES = {
    "person", "organization", "concept", "event", "object", "location",
    "project", "principle", "question", "lesson", "semantic-memory",
    "research", "research_raw", "agent", "memory", "tool"
}


# ============================================================================
# Validation Functions
# ============================================================================

def validate_entity_id(entity_id: str) -> bool:
    """Validate entity ID format."""
    return isinstance(entity_id, str) and len(entity_id) >= 4 and len(entity_id) <= 16


def validate_entity_name(name: str) -> bool:
    """Validate entity name."""
    if not isinstance(name, str) or not name.strip():
        return False
    return len(name.strip()) >= 1 and len(name) <= 200


def validate_entity_type(entity_type: str) -> bool:
    """Validate entity type."""
    return entity_type in VALID_ENTITY_TYPES or entity_type in VALID_ENTITY_TYPES


def validate_confidence(confidence: float) -> bool:
    """Validate confidence score."""
    return isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0


def validate_relationship_type(rel_type: str) -> bool:
    """Validate relationship type."""
    valid_types = {
        "related_to", "works_with", "mentions", "affects", "causes",
        "depends_on", "similar_to", "opposes", "part_of", "has_part",
        "signal", "message", "collaboration", "communication", "exchange"
    }
    return rel_type in valid_types


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class Entity:
    """Represents an entity (person, concept, organization, event, etc.)."""
    id: str
    name: str
    aliases: List[str]
    type: str
    confidence: float
    created_at: int
    last_seen: int
    relationships: List[str]
    evidence: List[Dict[str, Any]]
    is_ghost: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate entity on creation."""
        self.validate()

    def validate(self) -> bool:
        """Validate entity data."""
        if not validate_entity_id(self.id):
            raise ValueError(f"Invalid entity ID: {self.id}")
        if not validate_entity_name(self.name):
            raise ValueError(f"Invalid entity name: {self.name}")
        if not validate_entity_type(self.type):
            raise ValueError(f"Invalid entity type: {self.type}")
        if not validate_confidence(self.confidence):
            raise ValueError(f"Invalid confidence: {self.confidence}")
        # Provenance validation: check evidence sources if evidence exists
        for ev in self.evidence:
            if not ev.get("source"):
                raise ValueError(f"Entity {self.id} evidence missing source")
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "aliases": self.aliases,
            "type": self.type,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "relationships": self.relationships,
            "evidence": self.evidence,
            "is_ghost": self.is_ghost,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Entity:
        return cls(
            id=data["id"],
            name=data["name"],
            aliases=data["aliases"],
            type=data["type"],
            confidence=data["confidence"],
            created_at=data["created_at"],
            last_seen=data["last_seen"],
            relationships=data["relationships"],
            evidence=data["evidence"],
            is_ghost=data["is_ghost"],
            metadata=data.get("metadata", {})
        )

    def update_last_seen(self):
        """Update last_seen timestamp."""
        self.last_seen = int(time.time())

    def add_evidence(self, source: str, content: str, confidence_boost: float = 0.0, traceable: bool = True):
        """Add evidence to entity's provenance trail.
        
        Args:
            source: Source identifier (message_id, thread_id, model_run_id)
            content: Supporting evidence content
            confidence_boost: Confidence increase (default 0.0, max 0.1)
            traceable: Whether this evidence is traceable to source
        """
        if not isinstance(content, str):
            content = str(content)
        
        # Validate source format
        if not isinstance(source, str) or not source.strip():
            raise ValueError("Evidence source must be a non-empty string")
        
        evidence_item = {
            "source": source,
            "content": content[:500],  # Truncate long content
            "timestamp": int(time.time()),
            "confidence_boost": min(0.1, max(0.0, confidence_boost)),
            "traceable": traceable
        }
        self.evidence.append(evidence_item)
        
        # Update confidence based on new evidence
        self.confidence = min(1.0, self.confidence + evidence_item["confidence_boost"])
        self.update_last_seen()

    def promote_from_ghost(self):
        """Promote from ghost entity to authoritative entity."""
        self.is_ghost = False
        self.metadata["promoted_at"] = int(time.time())
        self.metadata["promotion_source"] = "manual"  # or "automatic"

    def get_evidence_count(self) -> int:
        """Get total evidence count."""
        return len(self.evidence)

    def get_trust_score(self) -> float:
        """Calculate trust score based on evidence and confidence."""
        base = self.confidence
        evidence_boost = min(0.3, len(self.evidence) * 0.05)
        authoritative_bonus = 0.2 if not self.is_ghost else 0.0
        return min(1.0, base + evidence_boost + authoritative_bonus)


# ============================================================================
# Promotion Criteria Configuration
# ============================================================================

# Default promotion thresholds
DEFAULT_PROMOTION_MIN_EVIDENCE = 3      # Minimum independent evidence sources
DEFAULT_PROMOTION_MIN_CONFIDENCE = 0.8  # Minimum confidence score
DEFAULT_PROMOTION_MIN_DURATION = 48 * 3600  # Minimum time in seconds (48 hours)


def check_promotion_criteria(entity: Entity, 
                             min_evidence: int = DEFAULT_PROMOTION_MIN_EVIDENCE,
                             min_confidence: float = DEFAULT_PROMOTION_MIN_CONFIDENCE,
                             min_duration: int = DEFAULT_PROMOTION_MIN_DURATION) -> Dict[str, Any]:
    """Check if entity meets promotion criteria from ghost to authoritative.
    
    Args:
        entity: The entity to check
        min_evidence: Minimum number of independent evidence sources required
        min_confidence: Minimum confidence score required (0.0-1.0)
        min_duration: Minimum time in seconds entity must exist before promotion
        
    Returns:
        Dictionary with:
        - eligible: Whether entity meets all criteria
        - criteria: Current state for each criterion
        - missing: List of criteria not met
        - recommendations: Suggestions to meet criteria
    """
    now = int(time.time())
    age_seconds = now - entity.created_at
    
    # Count independent sources (unique source values in evidence)
    independent_sources = set()
    for ev in entity.evidence:
        source = ev.get("source", "")
        if source:
            independent_sources.add(source)
    
    num_sources = len(independent_sources)
    confidence_met = entity.confidence >= min_confidence
    duration_met = age_seconds >= min_duration
    evidence_met = num_sources >= min_evidence
    
    missing = []
    recommendations = []
    
    if not evidence_met:
        missing.append(f"evidence ({num_sources}/{min_evidence})")
        recommendations.append(f"Add {min_evidence - num_sources} more independent evidence sources")
    
    if not confidence_met:
        missing.append(f"confidence ({entity.confidence:.2f}/{min_confidence})")
        recommendations.append(f"Gain {min_confidence - entity.confidence:.2f} more confidence through evidence")
    
    if not duration_met:
        remaining_hours = (min_duration - age_seconds) / 3600
        missing.append(f"duration ({age_seconds/3600:.1f}h/{min_duration/3600}h)")
        recommendations.append(f"Wait {remaining_hours:.1f} more hours for minimum duration requirement")
    
    return {
        "eligible": len(missing) == 0,
        "criteria": {
            "independent_sources": num_sources,
            "min_independent_sources": min_evidence,
            "confidence": round(entity.confidence, 3),
            "min_confidence": min_confidence,
            "age_hours": round(age_seconds / 3600, 1),
            "min_age_hours": round(min_duration / 3600, 1)
        },
        "missing": missing,
        "recommendations": recommendations
    }

    def get_evidence_count(self) -> int:
        """Get total evidence count."""
        return len(self.evidence)

    def get_trust_score(self) -> float:
        """Calculate trust score based on evidence and confidence."""
        base = self.confidence
        evidence_boost = min(0.3, len(self.evidence) * 0.05)
        authoritative_bonus = 0.2 if not self.is_ghost else 0.0
        return min(1.0, base + evidence_boost + authoritative_bonus)


@dataclass
class Relationship:
    """Represents a relationship between two entities."""
    id: str
    source_id: str
    target_id: str
    type: str
    strength: float
    provenance: Dict[str, Any]
    created_at: int
    updated_at: int

    def __post_init__(self):
        """Validate relationship on creation."""
        self.validate()

    def validate(self) -> bool:
        """Validate relationship data."""
        if not validate_entity_id(self.source_id):
            raise ValueError(f"Invalid source ID: {self.source_id}")
        if not validate_entity_id(self.target_id):
            raise ValueError(f"Invalid target ID: {self.target_id}")
        if not validate_relationship_type(self.type):
            raise ValueError(f"Invalid relationship type: {self.type}")
        if not validate_confidence(self.strength):
            raise ValueError(f"Invalid strength: {self.strength}")
        # Provenance validation: relationship must have traceable source
        if not self.provenance.get("source"):
            raise ValueError(f"Relationship {self.id} missing provenance source")
        if not self.provenance.get("traceable", False):
            raise ValueError(f"Relationship {self.id} must be traceable to source")
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "strength": self.strength,
            "provenance": self.provenance,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Relationship:
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            type=data["type"],
            strength=data["strength"],
            provenance=data["provenance"],
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )

    def update_strength(self, new_strength: float):
        """Update relationship strength."""
        new_strength = max(0.0, min(1.0, new_strength))
        self.strength = new_strength
        self.updated_at = int(time.time())

    def get_traceability(self) -> Dict[str, Any]:
        """Get traceability information."""
        return {
            "created_at": self.created_at,
            "source": self.provenance.get("source", "unknown"),
            "traceable": self.provenance.get("traceable", False)
        }


# ============================================================================
# Entity Graph Class
# ============================================================================

@dataclass
class EntityGraph:
    """Manages the full entity graph with persistence and validation."""
    entities: Dict[str, Entity] = field(default_factory=dict)
    relationships: Dict[str, Relationship] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(time.time()))
    updated_at: int = field(default_factory=lambda: int(time.time()))
    version: str = "1.0"
    _validation_enabled: bool = True

    def validate_graph(self) -> bool:
        """Validate entire graph consistency."""
        # Check for orphaned relationships
        for rel in self.relationships.values():
            if rel.source_id not in self.entities:
                raise ValueError(f"Orphaned relationship: {rel.id} references non-existent source")
            if rel.target_id not in self.entities:
                raise ValueError(f"Orphaned relationship: {rel.id} references non-existent target")
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "relationships": {k: v.to_dict() for k, v in self.relationships.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "validation_enabled": self._validation_enabled
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EntityGraph:
        graph = cls(
            created_at=data.get("created_at", int(time.time())),
            version=data.get("version", "1.0"),
            _validation_enabled=data.get("_validation_enabled", True)
        )
        graph.entities = {k: Entity.from_dict(v) for k, v in data.get("entities", {}).items()}
        graph.relationships = {k: Relationship.from_dict(v) for k, v in data.get("relationships", {}).items()}
        graph.updated_at = data.get("updated_at", int(time.time()))
        return graph

    @classmethod
    def load(cls, path: Path = ENTITY_GRAPH_PATH) -> EntityGraph:
        """Load entity graph from JSON file."""
        if not path.exists():
            return cls()
        with open(path, "r") as f:
            data = json.load(f)
        graph = cls.from_dict(data)
        if graph._validation_enabled:
            graph.validate_graph()
        return graph

    def save(self, path: Path = ENTITY_GRAPH_PATH):
        """Save entity graph to JSON file."""
        self.updated_at = int(time.time())
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    # --- Entity Management ---

    def add_entity(
        self,
        name: str,
        entity_type: str = "other",
        aliases: List[str] = None,
        confidence: float = 0.5,
        is_ghost: bool = True,
        metadata: Dict[str, Any] = None
    ) -> Entity:
        """Add a new entity to the graph.
        
        If an entity with the same normalized name and same type already exists,
        update it instead of creating a duplicate.
        
        Returns:
            Existing entity if found, otherwise newly created entity.
        """
        if self._validation_enabled:
            if not validate_entity_name(name):
                raise ValueError(f"Invalid entity name: {name}")
            if entity_type not in VALID_ENTITY_TYPES:
                raise ValueError(f"Invalid entity type: {entity_type}")
            if not validate_confidence(confidence):
                raise ValueError(f"Invalid confidence: {confidence}")

        # Check for existing entity with same normalized name and same type
        normalized_name = name.strip().lower()
        existing = self.get_entity_by_name(name)
        
        if existing and existing.type == entity_type:
            # Update existing entity instead of creating duplicate
            existing.update_last_seen()
            existing.confidence = min(1.0, existing.confidence + confidence * 0.25)
            
            # Merge aliases conservatively (only if not already present)
            for alias in aliases or []:
                if alias.lower().strip() not in [a.lower().strip() for a in existing.aliases]:
                    existing.aliases.append(alias)
            
            # Add evidence for traceability
            source = (metadata or {}).get("source", "unknown")
            existing.evidence.append({
                "source": source,
                "content": f"Name collision resolved: updated entity (type={entity_type})",
                "timestamp": int(time.time()),
                "confidence_boost": 0.0,
                "traceable": True
            })
            
            if self._validation_enabled:
                self.validate_graph()
            self.save()
            return existing

        # Create new entity (no existing match found)
        entity_id = str(uuid.uuid4())[:8]  # Short ID for readability
        aliases = aliases or []
        
        entity = Entity(
            id=entity_id,
            name=name,
            aliases=aliases,
            type=entity_type,
            confidence=confidence,
            created_at=int(time.time()),
            last_seen=int(time.time()),
            relationships=[],
            evidence=[],
            is_ghost=is_ghost,
            metadata=metadata or {}
        )
        
        self.entities[entity_id] = entity
        
        if self._validation_enabled:
            self.validate_graph()
            
        self.save()
        return entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get entity by name (exact match or alias)."""
        name_lower = name.lower().strip()
        for entity in self.entities.values():
            if entity.name.lower() == name_lower:
                return entity
            for alias in entity.aliases:
                if alias.lower() == name_lower:
                    return entity
        return None

    def update_entity(self, entity_id: str, **kwargs):
        """Update entity fields with validation."""
        entity = self.entities.get(entity_id)
        if not entity:
            return None

        # Validate kwargs before applying
        for key, value in kwargs.items():
            if key == "confidence" and not validate_confidence(value):
                raise ValueError(f"Invalid confidence: {value}")
            if key == "type" and value not in VALID_ENTITY_TYPES:
                raise ValueError(f"Invalid type: {value}")
            if key == "name" and not validate_entity_name(value):
                raise ValueError(f"Invalid name: {value}")

        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        entity.update_last_seen()
        
        if self._validation_enabled:
            self.validate_graph()
            
        self.save()
        return entity

    def promote_entity(self, entity_id: str, 
                       min_evidence: int = DEFAULT_PROMOTION_MIN_EVIDENCE,
                       min_confidence: float = DEFAULT_PROMOTION_MIN_CONFIDENCE,
                       min_duration: int = DEFAULT_PROMOTION_MIN_DURATION,
                       force: bool = False) -> Optional[Entity]:
        """Promote ghost entity to authoritative.
        
        Args:
            entity_id: Entity ID to promote
            min_evidence: Minimum independent evidence sources required
            min_confidence: Minimum confidence score required
            min_duration: Minimum time in seconds entity must exist
            force: Skip criteria check and promote regardless
            
        Returns:
            Entity if promoted, None if not a ghost entity or criteria not met
        """
        entity = self.entities.get(entity_id)
        if not entity or not entity.is_ghost:
            return None
        
        if not force:
            # Check promotion criteria
            criteria = check_promotion_criteria(
                entity, 
                min_evidence=min_evidence,
                min_confidence=min_confidence,
                min_duration=min_duration
            )
            
            if not criteria["eligible"]:
                raise ValueError(
                    f"Entity {entity_id} does not meet promotion criteria. "
                    f"Missing: {', '.join(criteria['missing'])}. "
                    f"Recommendations: {'; '.join(criteria['recommendations'])}"
                )
        
        entity.promote_from_ghost()
        
        if self._validation_enabled:
            self.validate_graph()
            
        self.save()
        return entity
    
    def get_promotion_candidates(self, 
                                  min_evidence: int = DEFAULT_PROMOTION_MIN_EVIDENCE,
                                  min_confidence: float = DEFAULT_PROMOTION_MIN_CONFIDENCE,
                                  min_duration: int = DEFAULT_PROMOTION_MIN_DURATION) -> List[Dict[str, Any]]:
        """Get list of ghost entities that meet promotion criteria.
        
        Returns:
            List of dictionaries with entity and criteria info
        """
        candidates = []
        for entity in self.get_ghost_entities():
            criteria = check_promotion_criteria(
                entity,
                min_evidence=min_evidence,
                min_confidence=min_confidence,
                min_duration=min_duration
            )
            if criteria["eligible"]:
                candidates.append({
                    "entity": entity,
                    "criteria": criteria["criteria"]
                })
        return candidates

    def delete_entity(self, entity_id: str) -> bool:
        """Delete entity and its relationships."""
        if entity_id not in self.entities:
            return False
        
        # Delete related relationships
        related_rels = [
            rel_id for rel_id, rel in self.relationships.items()
            if rel.source_id == entity_id or rel.target_id == entity_id
        ]
        for rel_id in related_rels:
            del self.relationships[rel_id]
        
        del self.entities[entity_id]
        
        if self._validation_enabled:
            self.validate_graph()
            
        self.save()
        return True

    # --- Relationship Management ---

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        strength: float = 0.5,
        provenance: Dict[str, Any] = None,
        source_ref: str = None
    ) -> Optional[Relationship]:
        """Add a new relationship between entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            rel_type: Relationship type
            strength: Relationship strength (0.0-1.0)
            provenance: Provenance metadata (must include source and traceable)
            source_ref: Specific source reference (message_id, thread_id, etc.)
        """
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        if self._validation_enabled:
            if not validate_relationship_type(rel_type):
                raise ValueError(f"Invalid relationship type: {rel_type}")
            if not validate_confidence(strength):
                raise ValueError(f"Invalid strength: {strength}")

        # Check if relationship already exists
        for rel in self.relationships.values():
            if (rel.source_id == source_id and rel.target_id == target_id and 
                rel.type == rel_type):
                rel.update_strength(strength)
                return rel
        
        rel_id = str(uuid.uuid4())[:8]
        
        # Build provenance with source reference
        base_provenance = {
            "source": source_ref or "manual",
            "timestamp": int(time.time()),
            "traceable": True
        }
        if provenance:
            base_provenance.update(provenance)
        
        relationship = Relationship(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            type=rel_type,
            strength=strength,
            provenance=base_provenance,
            created_at=int(time.time()),
            updated_at=int(time.time())
        )
        
        self.relationships[rel_id] = relationship
        self.entities[source_id].relationships.append(rel_id)
        self.entities[target_id].relationships.append(rel_id)
        
        if self._validation_enabled:
            self.validate_graph()
            
        self.save()
        return relationship

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """Get relationship by ID."""
        return self.relationships.get(rel_id)

    def get_relationships_for_entity(self, entity_id: str) -> List[Relationship]:
        """Get all relationships for an entity."""
        return [
            rel for rel in self.relationships.values()
            if rel.source_id == entity_id or rel.target_id == entity_id
        ]

    def update_relationship(self, rel_id: str, strength: float = None, **kwargs):
        """Update relationship fields with validation."""
        rel = self.relationships.get(rel_id)
        if not rel:
            return None

        if strength is not None:
            rel.update_strength(strength)
        
        for key, value in kwargs.items():
            if hasattr(rel, key) and key != "strength":
                setattr(rel, key, value)
        
        self.save()
        return rel

    def delete_relationship(self, rel_id: str) -> bool:
        """Delete a relationship."""
        if rel_id not in self.relationships:
            return False
        
        rel = self.relationships[rel_id]
        # Remove from entity relationship lists
        if rel.source_id in self.entities:
            self.entities[rel.source_id].relationships = [
                r for r in self.entities[rel.source_id].relationships if r != rel_id
            ]
        if rel.target_id in self.entities:
            self.entities[rel.target_id].relationships = [
                r for r in self.entities[rel.target_id].relationships if r != rel_id
            ]
        
        del self.relationships[rel_id]
        
        if self._validation_enabled:
            self.validate_graph()
            
        self.save()
        return True

    # --- Query Methods ---

    def get_all_entities(self) -> List[Entity]:
        """Get all entities."""
        return list(self.entities.values())

    def get_all_relationships(self) -> List[Relationship]:
        """Get all relationships."""
        return list(self.relationships.values())

    def get_ghost_entities(self) -> List[Entity]:
        """Get all ghost (unconfirmed) entities."""
        return [e for e in self.entities.values() if e.is_ghost]

    def get_authoritative_entities(self) -> List[Entity]:
        """Get all authoritative (confirmed) entities."""
        return [e for e in self.entities.values() if not e.is_ghost]

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get entities by type."""
        return [e for e in self.entities.values() if e.type == entity_type]

    def search_entities(self, query: str) -> List[Entity]:
        """Search entities by name or aliases."""
        query_lower = query.lower().strip()
        return [
            e for e in self.entities.values()
            if query_lower in e.name.lower() or 
               any(query_lower in alias.lower() for alias in e.aliases)
        ]

    def get_entity_stats(self) -> Dict[str, Any]:
        """Get entity graph statistics."""
        # Calculate provenance quality metrics
        entities_with_provenance = sum(1 for e in self.entities.values() if e.evidence)
        avg_evidence_per_entity = (
            sum(len(e.evidence) for e in self.entities.values()) / max(1, len(self.entities))
        )
        
        # Relationship provenance
        traceable_rels = sum(1 for r in self.relationships.values() 
                            if r.provenance.get("traceable", False))
        
        return {
            "total_entities": len(self.entities),
            "authoritative_entities": len(self.get_authoritative_entities()),
            "ghost_entities": len(self.get_ghost_entities()),
            "total_relationships": len(self.relationships),
            "entities_by_type": {
                et: len(self.get_entities_by_type(et))
                for et in set(e.type for e in self.entities.values())
            },
            "avg_confidence": round(
                sum(e.confidence for e in self.entities.values()) / max(1, len(self.entities)), 3
            ),
            "avg_trust_score": round(
                sum(e.get_trust_score() for e in self.entities.values()) / max(1, len(self.entities)), 3
            ),
            # Provenance metrics
            "entities_with_provenance": entities_with_provenance,
            "avg_evidence_per_entity": round(avg_evidence_per_entity, 2),
            "traceable_relationships": traceable_rels,
            "provenance_coverage": round(traceable_rels / max(1, len(self.relationships)), 3)
        }


# Global entity graph instance
_entity_graph: Optional[EntityGraph] = None


def get_entity_graph(path: Path = ENTITY_GRAPH_PATH) -> EntityGraph:
    """Get or create the global entity graph."""
    global _entity_graph
    if _entity_graph is None:
        _entity_graph = EntityGraph.load(path)
    return _entity_graph


def save_entity_graph(graph: EntityGraph = None, path: Path = ENTITY_GRAPH_PATH):
    """Save the entity graph to file."""
    if graph is None:
        global _entity_graph
        graph = _entity_graph
    if graph:
        graph.save(path)


# Initialize on module load
save_entity_graph(get_entity_graph())
