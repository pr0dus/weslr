"""Concept Graph Query Engine

Query engine for concept graph:
- Path tracing between concepts
- Central concept detection
- Source attribution
- Recent concepts
- Graph statistics

Queries are built on the store and index primitives.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from .models import Concept, Link, Evidence, Backlink
from .semantics import check_staleness


class ConceptGraphQueryEngine:
    """Query engine for concept graph.
    
    Provides:
    - Path finding between concepts
    - Central concept detection (PageRank-like)
    - Source attribution (evidence chains)
    - Recent concepts
    - Graph statistics
    """
    
    def __init__(self, store: "ConceptGraphStore" = None):
        """Initialize with optional store."""
        self.store = store
    
    def trace_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 10,
    ) -> List[str]:
        """Trace path from one concept to another.
        
        Uses DFS to find path, returns list of concept IDs.
        Returns empty list if no path found.
        """
        if self.store is None:
            return []
        
        # Load graph data
        self.store.load()
        concepts = self.store._concept_cache
        links = self.store._link_cache.values()
        
        # Build adjacency list
        adj: Dict[str, List[str]] = {}
        for link in links:
            if link.source_id not in adj:
                adj[link.source_id] = []
            adj[link.source_id].append(link.target_id)
        
        # DFS path finding
        path = self._dfs_path(adj, from_id, to_id, max_depth, set())
        return path
    
    def _dfs_path(
        self,
        adj: Dict[str, List[str]],
        current: str,
        target: str,
        max_depth: int,
        visited: set,
    ) -> List[str]:
        """DFS helper for path finding."""
        if current == target:
            return [current]
        
        if len(visited) >= max_depth:
            return []
        
        if current in visited:
            return []
        
        visited.add(current)
        
        for neighbor in adj.get(current, []):
            path = self._dfs_path(adj, neighbor, target, max_depth, visited.copy())
            if path:
                return [current] + path
        
        return []
    
    def shortest_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 10,
    ) -> List[str]:
        """Find shortest path using BFS."""
        if self.store is None:
            return []
        
        self.store.load()
        concepts = self.store._concept_cache
        links = self.store._link_cache.values()
        
        # Build adjacency list
        adj: Dict[str, List[str]] = {}
        for link in links:
            if link.source_id not in adj:
                adj[link.source_id] = []
            adj[link.source_id].append(link.target_id)
        
        # BFS shortest path
        from collections import deque
        queue = deque([(from_id, [from_id])])
        visited = {from_id}
        
        while queue:
            current, path = queue.popleft()
            
            if current == to_id:
                return path
            
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def central_concepts(
        self,
        limit: int = 10,
        min_degree: int = 1,
    ) -> List[Tuple[str, int]]:
        """Find most central concepts by degree.
        
        Returns list of (concept_id, degree) sorted by degree descending.
        """
        if self.store is None:
            return []
        
        self.store.load()
        concepts = self.store._concept_cache
        links = self.store._link_cache.values()
        
        # Compute degree for each concept
        degree: Dict[str, int] = {}
        for concept_id in concepts:
            degree[concept_id] = 0
        
        for link in links:
            if link.source_id in degree:
                degree[link.source_id] += 1
            if link.target_id in degree:
                degree[link.target_id] += 1
        
        # Sort by degree and filter
        sorted_concepts = sorted(
            [(cid, d) for cid, d in degree.items() if d >= min_degree],
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_concepts[:limit]
    
    def sources_supporting(
        self,
        concept_id: str,
        min_confidence: float = 0.0,
    ) -> List[Evidence]:
        """Get all sources supporting a concept.
        
        Returns list of Evidence objects with confidence >= min_confidence.
        """
        if self.store is None:
            return []
        
        self.store.load()
        concept = self.store._concept_cache.get(concept_id)
        
        if not concept:
            return []
        
        # Filter evidence by confidence
        return [
            ev for ev in concept.evidence
            if ev.confidence >= min_confidence
        ]
    
    def evidence_chain(
        self,
        concept_id: str,
    ) -> List[Dict[str, Any]]:
        """Get full evidence chain for a concept.
        
        Returns list of evidence items with source info.
        """
        sources = self.sources_supporting(concept_id)
        return [
            {
                "source_id": ev.source_id,
                "source_type": ev.source_type,
                "content": ev.content,
                "confidence": ev.confidence,
                "timestamp": ev.timestamp,
                "category": ev.category,
            }
            for ev in sources
        ]
    
    def recent_concepts(
        self,
        days: int = 7,
    ) -> List[Concept]:
        """Get concepts updated in last N days."""
        if self.store is None:
            return []
        
        self.store.load()
        concepts = self.store._concept_cache
        
        cutoff = time.time() - (days * 24 * 60 * 60)
        
        return [
            c for c in concepts.values()
            if c.last_updated >= cutoff or c.created_at >= cutoff
        ]
    
    def staleness_report(
        self,
    ) -> Dict[str, Any]:
        """Generate staleness report.
        
        Returns stats about stale links and expired evidence.
        """
        if self.store is None:
            return {"links": {}, "evidence": {}}
        
        self.store.load()
        links = self.store._link_cache.values()
        
        stale_links = []
        expired_evidence = []
        
        for link in links:
            if check_staleness(link.created_at):
                stale_links.append({
                    "link_id": f"{link.source_id}-{link.target_id}-{link.link_type}",
                    "created_at": link.created_at,
                    "source": link.source_id,
                    "target": link.target_id,
                })
        
        for concept in self.store._concept_cache.values():
            for ev in concept.evidence:
                if ev.is_expired():
                    expired_evidence.append({
                        "concept_id": concept.id,
                        "source_id": ev.source_id,
                        "timestamp": ev.timestamp,
                    })
        
        return {
            "links": {
                "total": len(list(links)),
                "stale": len(stale_links),
            },
            "evidence": {
                "expired": len(expired_evidence),
            },
            "generated_at": int(time.time()),
        }
    
    def graph_statistics(
        self,
    ) -> Dict[str, Any]:
        """Get basic graph statistics."""
        if self.store is None:
            return {"concepts": 0, "links": 0}
        
        self.store.load()
        concepts = self.store._concept_cache
        links = self.store._link_cache.values()
        
        # Count by type
        type_counts: Dict[str, int] = {}
        for concept in concepts.values():
            type_counts[concept.type] = type_counts.get(concept.type, 0) + 1
        
        # Count by tag
        tag_counts: Dict[str, int] = {}
        for concept in concepts.values():
            for tag in concept.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            "concepts": len(concepts),
            "links": len(links),
            "by_type": type_counts,
            "by_tag": tag_counts,
            "generated_at": int(time.time()),
        }
