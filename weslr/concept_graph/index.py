"""Concept Graph Index

Index management for concept graph:
- Backlinks computation (derived from links)
- By-name, by-type, by-tag indices
- Fast lookup operations
- Index regeneration

Indices are DERIVED from links and concepts.
They are NOT primary stored truth.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Concept, Link, Evidence, Backlink


class ConceptGraphIndex:
    """Index management for concept graph.
    
    Derives indices from links and concepts:
    - backlinks: computed from Link objects (NOT stored directly)
    - by_name: maps names to concept IDs
    - by_type: maps types to concept IDs
    - by_tag: maps tags to concept IDs
    """
    
    def __init__(self, index_dir: Path = None):
        """Initialize index with optional custom directory."""
        self.index_dir = index_dir or Path(__file__).resolve().parent / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "index.json"
    
    def compute_backlinks(self, links: List[Link]) -> Dict[str, List[Dict[str, Any]]]:
        """Compute backlinks from links.
        
        This is the DERIVED data - backlinks are NOT stored directly.
        They are computed on-demand from Link objects.
        """
        backlinks: Dict[str, List[Dict[str, Any]]] = {}
        
        for link in links:
            if link.target_id not in backlinks:
                backlinks[link.target_id] = []
            backlinks[link.target_id].append({
                "source_id": link.source_id,
                "link_type": link.link_type,
                "confidence": link.confidence,
                "reason": link.reason,
                "created_at": link.created_at,
            })
        
        return backlinks
    
    def compute_by_name(self, concepts: List[Concept]) -> Dict[str, str]:
        """Compute name index.
        
        Maps concept names to concept IDs.
        Returns first match for duplicate names.
        """
        by_name: Dict[str, str] = {}
        for concept in concepts:
            if concept.name not in by_name:
                by_name[concept.name] = concept.id
        return by_name
    
    def compute_by_type(self, concepts: List[Concept]) -> Dict[str, List[str]]:
        """Compute type index.
        
        Maps concept types to concept IDs.
        """
        by_type: Dict[str, List[str]] = {}
        for concept in concepts:
            if concept.type not in by_type:
                by_type[concept.type] = []
            by_type[concept.type].append(concept.id)
        return by_type
    
    def compute_by_tag(self, concepts: List[Concept]) -> Dict[str, List[str]]:
        """Compute tag index.
        
        Maps tags to concept IDs.
        """
        by_tag: Dict[str, List[str]] = {}
        for concept in concepts:
            for tag in concept.tags:
                if tag not in by_tag:
                    by_tag[tag] = []
                by_tag[tag].append(concept.id)
        return by_tag
    
    def build_full_index(
        self,
        concepts: List[Concept],
        links: List[Link],
    ) -> Dict[str, Any]:
        """Build full index from concepts and links.
        
        Returns complete index dict with all derived indices.
        """
        return {
            "by_name": self.compute_by_name(concepts),
            "by_type": self.compute_by_type(concepts),
            "by_tag": self.compute_by_tag(concepts),
            "backlinks": self.compute_backlinks(links),
            "last_updated": int(time.time()),
        }
    
    def save_index(self, index: Dict[str, Any]) -> None:
        """Save index to disk."""
        self.index_path.write_text(json.dumps(index, indent=2))
    
    def load_index(self) -> Optional[Dict[str, Any]]:
        """Load index from disk."""
        if self.index_path.exists():
            try:
                return json.loads(self.index_path.read_text())
            except Exception:
                pass
        return None
    
    def get_backlinks_for(self, concept_id: str, index: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get backlinks for a concept.
        
        Returns list of backlink objects pointing TO this concept.
        """
        return index.get("backlinks", {}).get(concept_id, [])
    
    def get_concept_by_name(self, name: str, index: Dict[str, Any]) -> Optional[str]:
        """Get concept ID by name.
        
        Returns first match for duplicate names.
        """
        return index.get("by_name", {}).get(name)
    
    def get_concepts_by_type(self, concept_type: str, index: Dict[str, Any]) -> List[str]:
        """Get concept IDs by type."""
        return index.get("by_type", {}).get(concept_type, [])
    
    def get_concepts_by_tag(self, tag: str, index: Dict[str, Any]) -> List[str]:
        """Get concept IDs by tag."""
        return index.get("by_tag", {}).get(tag, [])
    
    def regenerate_index(
        self,
        concepts: List[Concept],
        links: List[Link],
    ) -> Dict[str, Any]:
        """Regenerate index from scratch."""
        index = self.build_full_index(concepts, links)
        self.save_index(index)
        return index
