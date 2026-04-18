"""Concept Graph JSON Export Views

JSON export for concept graph.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from ..models import Concept, Link


def export_concepts_json(
    concepts: List[Concept],
    output_path: Path,
) -> Dict[str, Any]:
    """Export concepts to JSON format."""
    data = {
        "version": "1.0",
        "exported_at": int(time.time()),
        "concepts": [c.to_dict() for c in concepts],
    }
    
    output_path.write_text(json.dumps(data, indent=2))
    
    return {
        "files_created": 1,
        "concepts": len(concepts),
        "exported_at": data["exported_at"],
    }


def export_links_json(
    links: List[Link],
    output_path: Path,
) -> Dict[str, Any]:
    """Export links to JSON format."""
    data = {
        "version": "1.0",
        "exported_at": int(time.time()),
        "links": [l.to_dict() for l in links],
    }
    
    output_path.write_text(json.dumps(data, indent=2))
    
    return {
        "files_created": 1,
        "links": len(links),
        "exported_at": data["exported_at"],
    }


def export_full_graph_json(
    concepts: List[Concept],
    links: List[Link],
    output_path: Path,
) -> Dict[str, Any]:
    """Export full graph (concepts + links) to JSON."""
    data = {
        "version": "1.0",
        "exported_at": int(time.time()),
        "concepts": [c.to_dict() for c in concepts],
        "links": [l.to_dict() for l in links],
    }
    
    output_path.write_text(json.dumps(data, indent=2))
    
    return {
        "files_created": 1,
        "concepts": len(concepts),
        "links": len(links),
        "exported_at": data["exported_at"],
    }
