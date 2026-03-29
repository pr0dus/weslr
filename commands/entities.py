"""Entity graph commands for Weslr.

Commands:
- entity-list [--limit N]
- entity-details <entity_id>
- entity-merge <id1> <id2>
- entity-promote <entity_id>
- entity-search <query>
- entity-stats
"""

from __future__ import annotations

import argparse
import json
import sys

import entity_graph as eg


def cmd_entity_list(args: argparse.Namespace):
    """List entities in the entity graph."""
    graph = eg.get_entity_graph()
    entities = graph.get_all_entities()

    limit = args.limit or 10
    for entity in entities[:limit]:
        ghost_marker = " (GHOST)" if entity.is_ghost else ""
        print(f"{entity.id}: {entity.name} ({entity.type}) - {entity.confidence:.2f}{ghost_marker}")


def cmd_entity_details(args: argparse.Namespace):
    """Show details for a specific entity."""
    graph = eg.get_entity_graph()
    entity = graph.get_entity(args.entity_id)

    if not entity:
        print(f"Entity {args.entity_id} not found")
        sys.exit(1)

    print(json.dumps(entity.to_dict(), indent=2))


def cmd_entity_merge(args: argparse.Namespace):
    """Merge two entities."""
    graph = eg.get_entity_graph()

    e1 = graph.get_entity(args.id1)
    e2 = graph.get_entity(args.id2)

    if not e1 or not e2:
        print("One or both entities not found")
        sys.exit(1)

    # Merge e2 into e1
    e1.aliases.extend(a for a in e2.aliases if a not in e1.aliases)
    e1.evidence.extend(e2.evidence)
    e1.confidence = min(1.0, e1.confidence + e2.confidence * 0.3)

    # Remove e2 and its relationships
    graph.delete_entity(args.id2)
    graph.update_entity(args.id1, aliases=e1.aliases, confidence=e1.confidence)

    print(f"Merged '{e2.name}' into '{e1.name}'")


def cmd_entity_promote(args: argparse.Namespace):
    """Promote ghost entity to authoritative."""
    graph = eg.get_entity_graph()
    entity = graph.promote_entity(args.entity_id)

    if entity:
        print(f"Promoted entity '{entity.name}' to authoritative")
    else:
        print(f"Could not promote entity {args.entity_id}")
        sys.exit(1)


def cmd_entity_search(args: argparse.Namespace):
    """Search entities by name or aliases."""
    graph = eg.get_entity_graph()
    entities = graph.search_entities(args.query)

    print(f"Found {len(entities)} entities matching '{args.query}':")
    for entity in entities:
        ghost_marker = " (GHOST)" if entity.is_ghost else ""
        print(f"  {entity.id}: {entity.name} ({entity.type}) - {entity.confidence:.2f}{ghost_marker}")


def cmd_entity_stats(args: argparse.Namespace):
    """Show entity graph statistics."""
    graph = eg.get_entity_graph()
    stats = graph.get_entity_stats()

    print(f"Total entities: {stats['total_entities']}")
    print(f"  Authoritative: {stats['authoritative_entities']}")
    print(f"  Ghost: {stats['ghost_entities']}")
    print(f"Total relationships: {stats['total_relationships']}")
    print(f"Entities by type:")
    for etype, count in stats['entities_by_type'].items():
        print(f"  {etype}: {count}")


def cmd_relationship_list(args: argparse.Namespace):
    """List relationships in the entity graph."""
    graph = eg.get_entity_graph()
    relationships = graph.get_all_relationships()

    limit = args.limit or 10
    for rel in relationships[:limit]:
        source = graph.get_entity(rel.source_id)
        target = graph.get_entity(rel.target_id)
        source_name = source.name if source else rel.source_id
        target_name = target.name if target else rel.target_id
        print(f"{rel.id}: {source_name} -> {target_name} ({rel.type}) - {rel.strength:.2f}")


def cmd_relationship_add(args: argparse.Namespace):
    """Add a relationship between entities."""
    graph = eg.get_entity_graph()

    source = graph.get_entity(args.source_id)
    target = graph.get_entity(args.target_id)

    if not source or not target:
        print("Source or target entity not found")
        sys.exit(1)

    strength = args.strength if args.strength else 0.5

    rel = graph.add_relationship(
        source_id=source.id,
        target_id=target.id,
        rel_type=args.rel_type or "related_to",
        strength=strength,
        provenance={"source": "cli", "timestamp": int(__import__('time').time())}
    )

    if rel:
        print(f"Added relationship: {rel.id}")
    else:
        print("Failed to add relationship")
        sys.exit(1)


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register entity-related subcommands."""
    # entity-list
    parser_list = subparsers.add_parser("entity-list", help="List entities")
    parser_list.add_argument("--limit", type=int, default=10, help="Maximum entities to show")
    parser_list.set_defaults(func=cmd_entity_list)

    # entity-details
    parser_details = subparsers.add_parser("entity-details", help="Show entity details")
    parser_details.add_argument("entity_id", help="Entity ID")
    parser_details.set_defaults(func=cmd_entity_details)

    # entity-merge
    parser_merge = subparsers.add_parser("entity-merge", help="Merge two entities")
    parser_merge.add_argument("id1", help="First entity ID")
    parser_merge.add_argument("id2", help="Second entity ID")
    parser_merge.set_defaults(func=cmd_entity_merge)

    # entity-promote
    parser_promote = subparsers.add_parser("entity-promote", help="Promote ghost entity")
    parser_promote.add_argument("entity_id", help="Entity ID")
    parser_promote.set_defaults(func=cmd_entity_promote)

    # entity-search
    parser_search = subparsers.add_parser("entity-search", help="Search entities")
    parser_search.add_argument("query", help="Search query")
    parser_search.set_defaults(func=cmd_entity_search)

    # entity-stats
    parser_stats = subparsers.add_parser("entity-stats", help="Show entity statistics")
    parser_stats.set_defaults(func=cmd_entity_stats)

    # relationship-list
    parser_rel_list = subparsers.add_parser("relationship-list", help="List relationships")
    parser_rel_list.add_argument("--limit", type=int, default=10, help="Maximum relationships to show")
    parser_rel_list.set_defaults(func=cmd_relationship_list)

    # relationship-add
    parser_rel_add = subparsers.add_parser("relationship-add", help="Add a relationship")
    parser_rel_add.add_argument("source_id", help="Source entity ID")
    parser_rel_add.add_argument("target_id", help="Target entity ID")
    parser_rel_add.add_argument("--rel-type", default="related_to", help="Relationship type")
    parser_rel_add.add_argument("--strength", type=float, default=0.5, help="Relationship strength")
    parser_rel_add.set_defaults(func=cmd_relationship_add)
