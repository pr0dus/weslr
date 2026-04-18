"""Concept Graph Store

Persistence layer for concept graph:
- Saves/loads concepts and links
- Manages indices (by_name, by_type, by_tag, backlinks)
- Handles session concepts (temporary)
- Provides save/load/merge operations

Storage structure:
  concepts/       - Concept files (id.json)
  links/          - Link files (id.json with target in filename)
  index/          - Computed indices (backlinks, by_tag, etc.)
  metadata.json   - Graph metadata
  session.json    - Session state (temporary concepts)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import Concept, Link, Evidence, Backlink
from .semantics import check_staleness


# Base directory for concept graph storage
BASE_DIR = Path(__file__).resolve().parent
GRAPH_DIR = BASE_DIR / "concept_graph"
CONCEPTS_DIR = GRAPH_DIR / "concepts"
LINKS_DIR = GRAPH_DIR / "links"
EVIDENCE_DIR = GRAPH_DIR / "evidence"
INDEX_DIR = GRAPH_DIR / "index"

DEFAULT_GRAPH_PATH = GRAPH_DIR / "metadata.json"
SESSION_PATH = GRAPH_DIR / "session.json"


class ConceptGraphStore:
    """Persistence layer for concept graph.
    
    Manages:
    - Concept storage and retrieval
    - Link storage and retrieval
    - Index management (backlinks, by_name, by_type, by_tag)
    - Session concepts (temporary)
    - Graph metadata
    """
    
    def __init__(self, graph_dir: Path = None):
        """Initialize store with optional custom directory."""
        self.graph_dir = graph_dir or GRAPH_DIR
        self.concepts_dir = self.graph_dir / "concepts"
        self.links_dir = self.graph_dir / "links"
        self.evidence_dir = self.graph_dir / "evidence"
        self.index_dir = self.graph_dir / "index"
        
        self.session_path = self.graph_dir / "session.json"
        self.metadata_path = self.graph_dir / "metadata.json"
        
        # Create directories
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.links_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Load metadata
        self._metadata = self._load_metadata()
        
        # In-memory cache
        self._concept_cache: Dict[str, Concept] = {}
        self._link_cache: Dict[str, Link] = {}
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load or initialize graph metadata."""
        if self.metadata_path.exists():
            try:
                return json.loads(self.metadata_path.read_text())
            except Exception:
                pass
        return {
            "version": "1.0",
            "created_at": int(time.time()),
            "last_updated": int(time.time()),
            "concept_count": 0,
            "link_count": 0,
            "tag_index": {},
            "name_index": {},
        }
    
    def _save_metadata(self) -> None:
        """Save graph metadata."""
        self.metadata_path.write_text(json.dumps(self._metadata, indent=2))
    
    def save(self) -> None:
        """Save all concepts and links to disk."""
        # Save concepts
        for concept_id, concept in self._concept_cache.items():
            path = self.concepts_dir / f"{concept_id}.json"
            path.write_text(json.dumps(concept.to_dict(), indent=2))
        
        # Save links
        for link_id, link in self._link_cache.items():
            path = self.links_dir / f"{link_id}.json"
            path.write_text(json.dumps(link.to_dict(), indent=2))
        
        # Update metadata
        self._metadata["last_updated"] = int(time.time())
        self._metadata["concept_count"] = len(self._concept_cache)
        self._metadata["link_count"] = len(self._link_cache)
        self._save_metadata()
    
    def load(self) -> None:
        """Load concepts and links from disk."""
        # Load concepts
        for path in self.concepts_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                concept = Concept.from_dict(data)
                self._concept_cache[concept.id] = concept
            except Exception:
                pass
        
        # Load links
        for path in self.links_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                link = Link.from_dict(data)
                self._link_cache[f"{link.source_id}-{link.target_id}-{link.link_type}"] = link
            except Exception:
                pass
        
        # Load metadata
        self._metadata = self._load_metadata()
    
    def save_concept(self, concept: Concept) -> None:
        """Save a single concept."""
        path = self.concepts_dir / f"{concept.id}.json"
        path.write_text(json.dumps(concept.to_dict(), indent=2))
        self._concept_cache[concept.id] = concept
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def load_concept(self, concept_id: str) -> Optional[Concept]:
        """Load a single concept by ID."""
        path = self.concepts_dir / f"{concept_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return Concept.from_dict(data)
        return self._concept_cache.get(concept_id)
    
    def save_link(self, link: Link) -> None:
        """Save a single link."""
        link_id = f"{link.source_id}-{link.target_id}-{link.link_type}"
        path = self.links_dir / f"{link_id}.json"
        path.write_text(json.dumps(link.to_dict(), indent=2))
        self._link_cache[link_id] = link
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def load_link(self, source_id: str, target_id: str, link_type: str) -> Optional[Link]:
        """Load a single link by source, target, and type."""
        link_id = f"{source_id}-{target_id}-{link_type}"
        path = self.links_dir / f"{link_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return Link.from_dict(data)
        return self._link_cache.get(link_id)
    
    def list_concepts(self) -> List[Concept]:
        """List all concepts."""
        self.load()  # Reload from disk
        return list(self._concept_cache.values())
    
    def list_links(self) -> List[Link]:
        """List all links."""
        self.load()  # Reload from disk
        return list(self._link_cache.values())
    
    def delete_concept(self, concept_id: str) -> None:
        """Delete a concept by ID."""
        path = self.concepts_dir / f"{concept_id}.json"
        if path.exists():
            path.unlink()
        if concept_id in self._concept_cache:
            del self._concept_cache[concept_id]
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def delete_link(self, source_id: str, target_id: str, link_type: str) -> None:
        """Delete a link by source, target, and type."""
        link_id = f"{source_id}-{target_id}-{link_type}"
        path = self.links_dir / f"{link_id}.json"
        if path.exists():
            path.unlink()
        if link_id in self._link_cache:
            del self._link_cache[link_id]
        self._metadata["last_updated"] = int(time.time())
        self._save_metadata()
    
    def create_index(self) -> Dict[str, Any]:
        """Create indices for faster lookup."""
        self.load()
        
        index = {
            "by_name": {},
            "by_type": {},
            "by_tag": {},
            "backlinks": {},
        }
        
        for concept in self._concept_cache.values():
            # Index by name
            if concept.name not in index["by_name"]:
                index["by_name"][concept.name] = concept.id
            # Index by type
            if concept.type not in index["by_type"]:
                index["by_type"][concept.type] = []
            index["by_type"][concept.type].append(concept.id)
            # Index by tags
            for tag in concept.tags:
                if tag not in index["by_tag"]:
                    index["by_tag"][tag] = []
                index["by_tag"][tag].append(concept.id)
        
        # Compute backlinks from links
        for link in self._link_cache.values():
            if link.target_id not in index["backlinks"]:
                index["backlinks"][link.target_id] = []
            index["backlinks"][link.target_id].append({
                "source_id": link.source_id,
                "link_type": link.link_type,
                "confidence": link.confidence,
                "reason": link.reason,
                "created_at": link.created_at,
            })
        
        # Save index
        index_path = self.index_dir / "index.json"
        index_path.write_text(json.dumps(index, indent=2))
        
        return index
    
    def get_index(self) -> Dict[str, Any]:
        """Get existing index or create new one."""
        index_path = self.index_dir / "index.json"
        if index_path.exists():
            try:
                return json.loads(index_path.read_text())
            except Exception:
                pass
        return self.create_index()
    
    # Session operations (temporary concepts)
    
    def save_session_concept(self, concept: Concept) -> None:
        """Save a temporary session concept."""
        session = self._load_session()
        session["concepts"][concept.id] = concept.to_dict()
        session["last_updated"] = int(time.time())
        self.session_path.write_text(json.dumps(session, indent=2))
    
    def load_session_concepts(self) -> List[Concept]:
        """Load all session concepts."""
        session = self._load_session()
        return [Concept.from_dict(data) for data in session.get("concepts", {}).values()]
    
    def clear_session(self) -> None:
        """Clear all session concepts."""
        session = {"concepts": {}, "last_updated": int(time.time())}
        self.session_path.write_text(json.dumps(session, indent=2))
    
    def _load_session(self) -> Dict[str, Any]:
        """Load session state."""
        if self.session_path.exists():
            try:
                return json.loads(self.session_path.read_text())
            except Exception:
                pass
        return {"concepts": {}, "last_updated": int(time.time())}
    
    # Utility methods
    
    def get_concept_count(self) -> int:
        """Get number of concepts."""
        return len(self._concept_cache)
    
    def get_link_count(self) -> int:
        """Get number of links."""
        return len(self._link_cache)
    
    def is_stale_link(self, link: Link) -> bool:
        """Check if link is stale."""
        return check_staleness(link.created_at)
