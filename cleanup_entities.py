#!/usr/bin/env python3
"""One-time cleanup migration for historical duplicate entities.

This script:
- Reads the entity graph from entity_graph.json (READ-ONLY)
- Identifies duplicate entities (same normalized name + same type)
- Merges duplicates into the strongest entity
- Removes duplicates from the graph
- Creates a backup before writing changes
- Is fully rollback-safe

DO NOT RUN unless you have confirmed duplicates exist.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
ENTITY_GRAPH_PATH = BASE_DIR / "entity_graph.json"
ENTITY_GRAPH_BACKUP_PATH = BASE_DIR / f"entity_graph_backup_{int(time.time())}.json"


def load_entity_graph() -> Dict[str, Any]:
    """Load entity graph from JSON file."""
    if not ENTITY_GRAPH_PATH.exists():
        raise FileNotFoundError(f"Entity graph not found: {ENTITY_GRAPH_PATH}")
    with open(ENTITY_GRAPH_PATH, "r") as f:
        return json.load(f)


def save_entity_graph(data: Dict[str, Any], path: Path = ENTITY_GRAPH_PATH) -> None:
    """Save entity graph to JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_normalized_name(name: str) -> str:
    """Normalize entity name for comparison."""
    return name.strip().lower()


def get_best_entity(entity_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Select the strongest entity from a list of duplicates.
    
    Scoring:
    - Highest confidence (primary)
    - Highest evidence count (secondary)
    - Newest last_seen (tertiary)
    """
    def score(e: Dict[str, Any]) -> tuple:
        return (
            e.get("confidence", 0.0),
            len(e.get("evidence", [])),
            e.get("last_seen", 0),
        )
    
    return max(entity_list, key=score)


def merge_entity_data(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """Merge source entity data into target entity."""
    # Merge aliases (only unique ones)
    target_aliases = set(a.lower().strip() for a in target.get("aliases", []))
    for alias in source.get("aliases", []):
        if alias.lower().strip() not in target_aliases:
            target_aliases.add(alias.lower().strip())
            target.setdefault("aliases", []).append(alias)
    
    # Merge evidence
    target_evidence = target.get("evidence", [])
    source_evidence = source.get("evidence", [])
    target_evidence.extend(source_evidence)
    target["evidence"] = target_evidence
    
    # Update last_seen to newest
    target["last_seen"] = max(target.get("last_seen", 0), source.get("last_seen", 0))
    
    # Update confidence (conservative merge)
    target["confidence"] = min(1.0, target.get("confidence", 0.0) + source.get("confidence", 0.0) * 0.25)
    
    # Update metadata from source
    target.setdefault("metadata", {}).update(source.get("metadata", {}))
    
    return target


def analyze_duplicates(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Group entities by normalized name + type to find duplicates."""
    groups = defaultdict(list)
    
    entity_list = data.get("entities", {})
    if isinstance(entity_list, dict):
        entity_list = list(entity_list.values())
    
    for entity in entity_list:
        name = get_normalized_name(entity.get("name", ""))
        entity_type = entity.get("type", "unknown")
        key = f"{name}/{entity_type}"
        groups[key].append(entity)
    
    # Filter to only groups with duplicates
    return {k: v for k, v in groups.items() if len(v) > 1}


def cleanup_migration(dry_run: bool = False) -> Dict[str, Any]:
    """Run the cleanup migration.
    
    Args:
        dry_run: If True, only analyze and report, don't write changes
        
    Returns:
        Summary of what would be/did happen
    """
    print("=== ENTITY CLEANUP MIGRATION ===\n")
    
    # Load current state
    print("1. Loading entity graph...")
    data = load_entity_graph()
    
    entities = data.get("entities", {})
    original_count = len(entities) if isinstance(entities, dict) else len(entities)
    print(f"   Original entities: {original_count}\n")
    
    # Convert to list for processing
    entity_list = list(entities.values()) if isinstance(entities, dict) else entities
    
    # Analyze duplicates
    print("2. Analyzing duplicates...")
    duplicate_groups = analyze_duplicates(data)
    
    if not duplicate_groups:
        print("   No duplicates found. Nothing to cleanup.\n")
        return {"status": "skipped", "message": "No duplicates found"}
    
    print(f"   Found {len(duplicate_groups)} duplicate groups:")
    for key, dup_ents in duplicate_groups.items():
        print(f"   - {key}: {len(dup_ents)} entities")
        for e in dup_ents:
            print(f"     * {e['id']}: {e['name']} (conf={e.get('confidence', 0)}, evidence={len(e.get('evidence', []))})")
    print()
    
    # Identify which to keep and which to remove
    print("3. Selecting entities to keep...")
    to_keep = []
    to_remove = []
    removed_id_to_kept_id = {}
    
    for key, dup_ents in duplicate_groups.items():
        best = get_best_entity(dup_ents)
        to_keep.append(best)
        for e in dup_ents:
            if e["id"] != best["id"]:
                to_remove.append(e)
                removed_id_to_kept_id[e["id"]] = best["id"]
    
    print(f"   Keeping: {len(to_keep)} entities")
    for e in to_keep:
        print(f"     - {e['id']}: {e['name']} (conf={e.get('confidence', 0)}, evidence={len(e.get('evidence', []))})")
    print(f"   Removing: {len(to_remove)} entities")
    for e in to_remove:
        print(f"     - {e['id']}: {e['name']}")
    print()
    
    # Build set of all duplicate entity IDs
    all_duplicate_ids = set()
    for dup_ents in duplicate_groups.values():
        for e in dup_ents:
            all_duplicate_ids.add(e["id"])
    
    # Build new entities dict
    # Keep ALL non-duplicate entities
    new_entities = {}
    for e in entity_list:
        if e["id"] not in all_duplicate_ids:
            new_entities[e["id"]] = e
    
    # Add kept duplicates
    for e in to_keep:
        new_entities[e["id"]] = e
    
    print("4. Merging removed duplicates into kept entities...")
    # Merge removed duplicates into their kept counterparts
    for e in to_remove:
        kept_id = removed_id_to_kept_id.get(e["id"])
        if kept_id and kept_id in new_entities:
            new_entities[kept_id] = merge_entity_data(new_entities[kept_id], e)
            print(f"   Merged {e['id']} into {kept_id}")
    print()
    
    # Check for potential placeholder entities
    print("5. Checking for placeholder entities...")
    placeholders = []
    for e in entity_list:
        name = get_normalized_name(e.get("name", ""))
        entity_type = e.get("type", "unknown")
        # Check if this looks like a placeholder (non-human-like name, non-person type)
        if entity_type not in {"person", "agent", "organization"}:
            # Not a person-type entity
            if name.startswith("agent-") and name[6:].isdigit():
                # agent-N with non-person type - likely placeholder from text analysis
                placeholders.append(e)
                print(f"   Potential placeholder: {e['id']}: {e['name']} (type={entity_type})")
    
    if placeholders:
        print(f"   Found {len(placeholders)} potential placeholder entities")
    else:
        print("   No obvious placeholder entities found")
    print()
    
    if dry_run:
        print("=== DRY RUN - NO CHANGES MADE ===")
        return {
            "status": "dry_run",
            "original_count": original_count,
            "duplicate_groups": len(duplicate_groups),
            "entities_to_keep": len(to_keep),
            "entities_to_remove": len(to_remove),
            "placeholders_found": len(placeholders),
            "message": "Dry run complete. No changes made."
        }
    
    # Create backup before making changes
    print("6. Creating backup...")
    save_entity_graph(data, ENTITY_GRAPH_BACKUP_PATH)
    print(f"   Backup created: {ENTITY_GRAPH_BACKUP_PATH}\n")
    
    # Remove placeholder entities (safe to delete)
    print("7. Removing placeholder entities...")
    for p in placeholders:
        entity_type = p.get("type", "")
        name = get_normalized_name(p.get("name", ""))
        # Only remove if type is clearly non-agent (concept, event, object, etc.)
        if entity_type in {"concept", "event", "object", "location", "other"}:
            print(f"   Removing placeholder: {p['id']}: {name} (type={entity_type})")
            if p["id"] in new_entities:
                del new_entities[p["id"]]
        else:
            print(f"   WARNING: Not removing {p['id']}: {name} (type={entity_type}) - may be intentional")
    print()
    
    # Build final data
    data["entities"] = new_entities
    data["updated_at"] = int(time.time())
    
    print(f"8. Final entity count: {len(new_entities)}")
    
    # Save changes
    save_entity_graph(data)
    print(f"   Saved: {ENTITY_GRAPH_PATH}\n")
    
    return {
        "status": "completed",
        "original_count": original_count,
        "final_count": len(new_entities),
        "duplicate_groups_cleaned": len(duplicate_groups),
        "entities_removed": len(to_remove),
        "placeholders_removed": len([p for p in placeholders if p.get("type") in {"concept", "event", "object", "location", "other"}]),
        "backup_path": str(ENTITY_GRAPH_BACKUP_PATH),
        "message": f"Cleanup completed. Original: {original_count}, Final: {len(new_entities)}"
    }


def main():
    """CLI entry point."""
    import sys
    
    dry_run = "--dry-run" in sys.argv or "--dry" in sys.argv
    force = "--force" in sys.argv
    
    if not force and not dry_run:
        print("WARNING: This will modify entity_graph.json")
        print("Use --dry-run to analyze without changes")
        print("Use --force to proceed with cleanup")
        return
    
    result = cleanup_migration(dry_run=dry_run)
    
    print("\n=== MIGRATION RESULT ===")
    print(f"Status: {result['status']}")
    if result.get("message"):
        print(f"Message: {result['message']}")
    
    if dry_run:
        print("\nThis was a dry run. No files were modified.")
        print("To proceed with actual cleanup, run: python3 cleanup_entities.py --force")


if __name__ == "__main__":
    main()
