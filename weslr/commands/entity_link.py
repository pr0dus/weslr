"""
Entity linking — same_as relationships between material names.
Operator-only commands: /entity link <source> <target> and /entity unlink <source> <target>
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from weslr.fact_extractor import append_enriched_fact


def link_entities(source: str, target: str, tenant_id: Optional[str] = None) -> dict:
    """Create a same_as link: source refers to the same material as target."""
    if not source or not target:
        return {"status": "error", "message": "Both source and target are required"}
    if source.lower() == target.lower():
        return {"status": "error", "message": "Source and target must be different"}

    # Normalize
    src_norm = source.strip().lower()
    tgt_norm = target.strip().lower()

    # Check if already linked
    from weslr.fact_extractor import load_facts
    existing = load_facts(predicate="same_as", tenant_id=tenant_id, limit=50)
    for e in existing:
        s = e.get("subject", "").lower()
        o = e.get("object", "").lower()
        if (s == src_norm and o == tgt_norm) or (s == tgt_norm and o == src_norm):
            return {"status": "already_linked", "message": f"{source} and {target} are already linked"}

    fact = {
        "subject": source.strip(),
        "predicate": "same_as",
        "object": target.strip(),
        "fact_data": {"link_type": "same_as", "source_name": source.strip(), "target_name": target.strip()},
        "confidence": 1.0,
        "trust_score": 1.0,
        "record_type": "fact_assertion_v1",
        "source_type": "manual_operator",
        "authority": "operator",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "publication_year": datetime.now(timezone.utc).year,
    }
    result = append_enriched_fact(fact, tenant_id=tenant_id)
    return {
        "status": "linked",
        "source": source,
        "target": target,
        "path": result["path"],
        "fact_id": result["fact_id"],
    }


def unlink_entities(source: str, target: str, tenant_id: Optional[str] = None) -> dict:
    """Archive a same_as link (append status:removed event — do NOT delete)."""
    from weslr.fact_extractor import load_facts
    existing = load_facts(predicate="same_as", tenant_id=tenant_id, limit=200)
    found = None
    src_norm = source.strip().lower()
    tgt_norm = target.strip().lower()

    for e in existing:
        s = e.get("subject", "").lower()
        o = e.get("object", "").lower()
        if (s == src_norm and o == tgt_norm) or (s == tgt_norm and o == src_norm):
            found = e
            break

    if not found:
        return {"status": "not_found", "message": f"No same_as link found between {source} and {target}"}

    # Append removal event
    removal = dict(found)
    removal["record_type"] = "fact_assertion_v1"
    removal["predicate"] = "same_as"
    removal["status"] = "removed"
    removal["removed_at"] = datetime.now(timezone.utc).isoformat()
    removal["removed_by"] = "operator"
    result = append_enriched_fact(removal, tenant_id=tenant_id)
    return {
        "status": "unlinked",
        "source": source,
        "target": target,
        "path": result["path"],
        "fact_id": result["fact_id"],
    }


def get_linked_entities(entity: str, tenant_id: Optional[str] = None) -> list:
    """Return all entities that are same_as linked to the given entity."""
    from weslr.fact_extractor import load_facts
    all_links = load_facts(predicate="same_as", tenant_id=tenant_id, limit=200)
    ent_norm = entity.strip().lower()

    # Build set of removed pairs (unordered) — check BOTH directions
    removed_pairs = set()
    for link in all_links:
        if link.get("status") == "removed":
            s = link.get("subject", "").lower()
            o = link.get("object", "").lower()
            # Store both orderings so we can check in either direction
            removed_pairs.add((s, o))
            removed_pairs.add((o, s))

    linked = []
    for link in all_links:
        s = link.get("subject", "").lower()
        o = link.get("object", "").lower()
        # Skip if link itself has status:removed OR if this pair has a removal record
        if link.get("status") == "removed":
            continue
        if (s, o) in removed_pairs:
            continue
        if s == ent_norm:
            linked.append(o)
        elif o == ent_norm:
            linked.append(s)
    return linked


def handle_entity_link_cmd(message: str, tenant_id: Optional[str] = None) -> str:
    """Parse and handle /entity link or /entity unlink command."""
    parts = message.strip().split()
    if len(parts) < 3:
        return "Usage: /entity link <source> <target>  or  /entity unlink <source> <target>"

    cmd = parts[0].lower()
    source = parts[1]
    target = parts[2]

    if "unlink" in cmd:
        result = unlink_entities(source, target, tenant_id=tenant_id)
    else:
        result = link_entities(source, target, tenant_id=tenant_id)

    if result.get("status") == "error":
        return f"Error: {result.get('message')}"
    elif result.get("status") == "already_linked":
        return f"Already linked: {result.get('message')}"
    elif result.get("status") == "not_found":
        return f"Not found: {result.get('message')}"
    elif result.get("status") == "linked":
        return f"✅ Linked: {source} ↔ {target} (same_as relationship created)"
    elif result.get("status") == "unlinked":
        return f"✅ Unlinked: {source} ↔ {target} (relationship archived)"
    return str(result)
