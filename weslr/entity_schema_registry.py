"""
Entity Schema Registry — Phase 4.3

Loads domain-specific entity schemas from weslr/schemas/<domain>.json.
Entities are NOT stored separately — they are derived at query time from
fact_assertions.jsonl by scanning subject, object, and fact_data fields.

Authority: read-only. No writes, no hidden learning.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# In-memory cache: domain → schema dict
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}

# Active domain (V1: hardcoded to cancer_research; multi-tenant later)
DEFAULT_DOMAIN = "cancer_research"


def load_schema(domain: str = DEFAULT_DOMAIN) -> Dict[str, Any]:
    """Load schema from weslr/schemas/<domain>.json.

    Caches after first load. Falls back to base.json if domain not found.

    Returns:
        dict with keys: domain, version, entity_types, relationship_types
    """
    if domain in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[domain]

    schema_path = Path(__file__).parent / "schemas" / f"{domain}.json"
    fallback_path = Path(__file__).parent / "schemas" / "base.json"

    if schema_path.exists():
        target = schema_path
    elif fallback_path.exists():
        target = fallback_path
    else:
        # Hard fallback — return minimal inline schema
        return {
            "domain": domain,
            "version": "1.0",
            "entity_types": {},
            "relationship_types": [],
        }

    with open(target, encoding="utf-8") as f:
        schema = json.load(f)

    _SCHEMA_CACHE[domain] = schema
    return schema


def get_entity_schema(
    entity_type: str, domain: str = DEFAULT_DOMAIN
) -> Dict[str, Any]:
    """Return schema for a specific entity type.

    Returns:
        dict with keys: extends, required, attributes, relationships
        Empty dict if entity_type not defined.
    """
    schema = load_schema(domain)
    return schema.get("entity_types", {}).get(entity_type, {})


def list_entity_types(domain: str = DEFAULT_DOMAIN) -> List[str]:
    """Return sorted list of entity type names defined in the schema."""
    schema = load_schema(domain)
    return sorted(schema.get("entity_types", {}).keys())


def list_relationship_types(domain: str = DEFAULT_DOMAIN) -> List[str]:
    """Return sorted list of relationship type names."""
    schema = load_schema(domain)
    return sorted(schema.get("relationship_types", []))


def get_schema_summary(domain: str = DEFAULT_DOMAIN) -> str:
    """Return a human-readable summary of the active schema.

    Lists entity types, their attributes, and relationship types.
    """
    schema = load_schema(domain)
    lines = [
        f"Schema: {schema.get('domain', domain)} (v{schema.get('version', '1.0')})",
        "",
    ]

    entity_types = schema.get("entity_types", {})
    for et_name, et_def in entity_types.items():
        lines.append(f"  [{et_name}]")
        attrs = et_def.get("attributes", [])
        if attrs:
            lines.append(f"    attributes : {', '.join(attrs)}")
        rels = et_def.get("relationships", [])
        if rels:
            lines.append(f"    relationships: {', '.join(rels)}")
        lines.append("")

    rel_types = schema.get("relationship_types", [])
    if rel_types:
        lines.append(f"Relationship types: {', '.join(rel_types)}")

    return "\n".join(lines)