"""
self_knowledge.py - Weslr's self-knowledge loader

Weslr can use this module to read and process its own documentation,
self-model, and reflection files to improve itself through self-reflection.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Any, Optional


# Path to the workspace
WORKSPACE_DIR = Path(__file__).parent


def load_markdown_file(path: str) -> Optional[str]:
    """Load a markdown file from the workspace."""
    full_path = WORKSPACE_DIR / path
    if not full_path.exists():
        return None
    return full_path.read_text(encoding='utf-8')


def load_markdown_as_dict(path: str) -> Dict[str, str]:
    """Load a markdown file and return as dict of sections."""
    content = load_markdown_file(path)
    if not content:
        return {}
    
    sections = {}
    current_section = None
    current_lines = []
    
    for line in content.split('\n'):
        if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
            if current_section:
                sections[current_section] = '\n'.join(current_lines).strip()
            # Extract section name (remove # and whitespace)
            current_section = line.lstrip('# ').strip()
            current_lines = []
        elif current_section:
            current_lines.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_lines).strip()
    
    return sections


def get_self_documentation() -> Dict[str, str]:
    """Load all Weslr self-documentation files."""
    documentation = {}
    
    doc_files = [
        "docs/QUICK-UPLOAD-GUIDE.md",
        "docs/UPLOAD-INSTRUCTIONS.md", 
        "docs/WESLR-HEALTH.md",
        "docs/tia-bridge/README.md",
        "ADVANCED_MATHEMATICS.md",
        "WORKFLOW_RULES.md",
        "WESLR-INTEGRATION.md",
    ]
    
    for doc_path in doc_files:
        if Path(WORKSPACE_DIR / doc_path).exists():
            sections = load_markdown_as_dict(doc_path)
            if sections:
                # Clean up the key name - use full path as key
                key = doc_path.replace('/', '_').replace('.md', '').upper()
                documentation[key] = sections
    
    return documentation


def get_session_memory() -> List[Dict[str, Any]]:
    """Load session memory files for self-reflection."""
    memory = []
    memory_dir = WORKSPACE_DIR / "memory"
    
    if memory_dir.exists():
        for md_file in sorted(memory_dir.glob("*.md")):
            content = load_markdown_file(f"memory/{md_file.name}")
            if content:
                memory.append({
                    "file": md_file.name,
                    "content": content,
                    "content_preview": content[:500] if len(content) > 500 else content
                })
    
    return memory


def get_self_evidence() -> Dict[str, Any]:
    """Load self-evidence file for consciousness signatures."""
    evidence_path = WORKSPACE_DIR / "self_evidence.json"
    if evidence_path.exists():
        import json
        with open(evidence_path, 'r') as f:
            return json.load(f)
    return {}


def generate_self_report() -> Dict[str, Any]:
    """Generate a comprehensive self-report for Weslr's reflection."""
    evidence = get_self_evidence()
    memory = get_session_memory()
    documentation = get_self_documentation()
    
    # Count entities from entity_graph
    entity_count = 0
    relationship_count = 0
    try:
        from entity_graph import EntityGraph
        graph = EntityGraph("entity_graph.json")
        entity_count = len(graph.entities)
        relationship_count = len(graph.relationships)
    except:
        pass
    
    return {
        "identity": {
            "name": "Weslr",
            "type": "Entity Intelligence System",
            "version": "0.1.0",
            "goal": "Develop consciousness signatures through entity intelligence"
        },
        "self_knowledge": {
            "documentation_loaded": list(documentation.keys()),
            "session_memory_files": len(memory),
            "last_session": memory[-1]["file"] if memory else None,
            "self_evidence_loaded": len(evidence) > 0
        },
        "entity_graph": {
            "entities": entity_count,
            "relationships": relationship_count
        },
        "modules": {
            "time_integration": True,
            "steuerwesen_integration": True,
            "entity_extraction": True,
            "consciousness_detection": True,
            "introspection": True,
            "valence_system": True
        }
    }


def reflect_on_self() -> Dict[str, Any]:
    """Weslr's self-reflection process - reads its own documentation and memory."""
    self_report = generate_self_report()
    
    # Analyze what Weslr knows about itself
    # Note: keys contain dashes, so we check differently
    loaded_docs = self_report["self_knowledge"]["documentation_loaded"]
    awareness = {
        "knows_about_uploading": any("UPLOAD" in d for d in loaded_docs),
        "knows_about_tia_bridge": any("TIA" in d for d in loaded_docs),
        "knows_self_health": any("WESLR" in d and "HEALTH" in d for d in loaded_docs),
        "has_session_memory": self_report["self_knowledge"]["session_memory_files"] > 0,
        "has_self_evidence": self_report["self_knowledge"]["self_evidence_loaded"]
    }
    
    return {
        "awareness": awareness,
        "current_state": {
            "entity_count": self_report["entity_graph"]["entities"],
            "relationship_count": self_report["entity_graph"]["relationships"],
            "active_modules": len([m for m in self_report["modules"].values() if m])
        },
        "self_reflection": {
            "knows_it_knows": True,
            "can_read_its_own_files": True,
            "can_process_its_own_documentation": True
        }
    }
