"""Concept Graph Views

Export views for concept graph:
- Obsidian markdown export
- JSON export
- Audit trail

Views are READ-ONLY transformations.
They do NOT modify the graph store.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models import Concept, Link, Evidence, Backlink
from ..semantics import get_link_types


class ConceptGraphViews:
    """View layer for concept graph exports.
    
    All views are read-only.
    They transform graph data for export, not modify it.
    """
    
    def __init__(self, store: "ConceptGraphStore" = None):
        """Initialize with optional store."""
        self.store = store
    
    def export_obsidian(
        self,
        output_dir: Path,
        include_backlinks: bool = True,
        include_evidence: bool = True,
    ) -> Dict[str, int]:
        """Export graph to Obsidian-compatible format.
        
        Creates:
        - Concepts/ directory with .md files
        - [[links]] in Obsidian format
        - Backlinks section in each file
        - Evidence section if enabled
        
        Args:
            output_dir: Output directory for Obsidian vault
            include_backlinks: Include backlinks in each file
            include_evidence: Include evidence in each file
        
        Returns:
            Export statistics (files created, concepts, links)
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        concepts_dir = output_dir / "Concepts"
        concepts_dir.mkdir(exist_ok=True)
        
        stats = {
            "files_created": 0,
            "concepts_exported": 0,
            "links_exported": 0,
        }
        
        if self.store:
            self.store.load()
            concepts = self.store._concept_cache.values()
            
            for concept in concepts:
                md_content = self._concept_to_obsidian_md(
                    concept,
                    include_backlinks=include_backlinks,
                    include_evidence=include_evidence,
                )
                
                md_path = concepts_dir / f"{concept.name}.md"
                md_path.write_text(md_content)
                
                stats["files_created"] += 1
                stats["concepts_exported"] += 1
                stats["links_exported"] += len(concept.links)
        
        return stats
    
    def _concept_to_obsidian_md(
        self,
        concept: Concept,
        include_backlinks: bool = True,
        include_evidence: bool = True,
    ) -> str:
        """Convert concept to Obsidian markdown."""
        lines = []
        
        # Title
        lines.append(f"# {concept.name}")
        lines.append("")
        
        # Metadata
        lines.append(f"**Type:** {concept.type}")
        lines.append(f"**Confidence:** {concept.confidence:.2f}")
        lines.append(f"**Created:** {time.strftime('%Y-%m-%d', time.localtime(concept.created_at))}")
        lines.append("")
        
        # Description
        if concept.description:
            lines.append(concept.description)
            lines.append("")
        
        # Tags
        if concept.tags:
            lines.append(f"Tags: {', '.join(f'#{tag}' for tag in concept.tags)}")
            lines.append("")
        
        # Links
        if concept.links:
            lines.append("### Links")
            for link in concept.links:
                obsidian_link = f"[[{link.target_id}]]"
                lines.append(f"- {obsidian_link} ({link.link_type})")
            lines.append("")
        
        # Backlinks
        if include_backlinks:
            lines.append("### Backlinks")
            lines.append("These concepts link to this one:")
            # Backlinks would be computed from other concepts
            lines.append("(Computed from other concepts)")
            lines.append("")
        
        # Evidence
        if include_evidence and concept.evidence:
            lines.append("### Evidence")
            for ev in concept.evidence:
                lines.append(f"- **Source:** {ev.source_id}")
                lines.append(f"  - Type: {ev.source_type}")
                lines.append(f"  - Content: {ev.content[:100]}...")
            lines.append("")
        
        # Metadata details
        if concept.metadata:
            lines.append("### Metadata")
            lines.append(f"```json")
            lines.append(json.dumps(concept.metadata, indent=2))
            lines.append(f"```")
        
        return "\n".join(lines)
    
    def export_json(
        self,
        output_path: Path,
    ) -> Dict[str, int]:
        """Export graph to JSON format.
        
        Args:
            output_path: Output JSON file path
        
        Returns:
            Export statistics
        """
        if self.store is None:
            return {"concepts": 0, "links": 0}
        
        self.store.load()
        concepts = self.store._concept_cache
        links = self.store._link_cache
        
        data = {
            "version": "1.0",
            "exported_at": int(time.time()),
            "concepts": [c.to_dict() for c in concepts.values()],
            "links": [l.to_dict() for l in links.values()],
        }
        
        output_path.write_text(json.dumps(data, indent=2))
        
        return {
            "files_created": 1,
            "concepts": len(concepts),
            "links": len(links),
        }
    
    def export_audit_trail(
        self,
        output_path: Path,
    ) -> Dict[str, int]:
        """Export audit trail for graph changes.
        
        Records when concepts were created/updated.
        """
        if self.store is None:
            return {"events": 0}
        
        self.store.load()
        concepts = self.store._concept_cache
        
        events = []
        for concept in concepts.values():
            events.append({
                "event": "concept_created",
                "concept_id": concept.id,
                "concept_name": concept.name,
                "timestamp": concept.created_at,
                "type": concept.type,
            })
            
            if concept.created_at != concept.last_updated:
                events.append({
                    "event": "concept_updated",
                    "concept_id": concept.id,
                    "concept_name": concept.name,
                    "timestamp": concept.last_updated,
                })
        
        data = {
            "exported_at": int(time.time()),
            "events": events,
            "total_events": len(events),
        }
        
        output_path.write_text(json.dumps(data, indent=2))
        
        return {"events": len(events)}


def export_obsidian(
    store: "ConceptGraphStore",
    output_dir: Path,
) -> Dict[str, int]:
    """Convenience function for Obsidian export."""
    views = ConceptGraphViews(store)
    return views.export_obsidian(output_dir)
